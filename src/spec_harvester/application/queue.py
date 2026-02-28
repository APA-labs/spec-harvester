from __future__ import annotations

import json
from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import time
from typing import Callable

from spec_harvester.domain.hashing import sha256_hexdigest
from spec_harvester.domain.policy import Policy
from spec_harvester.domain.url import normalize_url
from spec_harvester.infrastructure.http.http_client import FetchError, ResponseData, fetch
from spec_harvester.infrastructure.http.robots import RobotsChecker
from spec_harvester.infrastructure.logging.jsonl import (
    EVENT_DEDUP_HIT,
    EVENT_FETCH_ERROR,
    EVENT_FETCH_SUCCESS,
    EVENT_RUN_FINISHED,
    EVENT_RUN_STARTED,
    EVENT_SAVED,
    JsonlEventLogger,
)
from spec_harvester.infrastructure.parsers.links import extract_links
from spec_harvester.infrastructure.storage.manifest import should_save
from spec_harvester.infrastructure.storage.writer import write_document


@dataclass(frozen=True)
class CrawlRunResult:
    command_id: str
    fetched: int
    no_change: int
    errors: int
    visited: int
    manifest_path: Path
    log_path: Path


def run_crawl(
    *,
    policy: Policy,
    max_pages: int | None = None,
    raw_root: str | Path = "storage/raw",
    manifest_root: str | Path = "storage/manifests",
    log_root: str | Path = "logs",
    fetch_fn: Callable[[str], ResponseData] | None = None,
    robots_checker: RobotsChecker | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> CrawlRunResult:
    effective_max_pages = max_pages if max_pages is not None else policy.max_pages
    if effective_max_pages <= 0:
        raise ValueError("max_pages must be > 0")

    # Include microseconds to avoid path collisions for back-to-back runs.
    command_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    log_path = Path(log_root) / f"run-{command_id}.jsonl"
    logger = JsonlEventLogger(log_path, base_fields={"command_id": command_id})

    manifest_dir = Path(manifest_root)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    run_manifest_path = manifest_dir / f"run-{command_id}.json"
    url_index_path = manifest_dir / "url_index.json"

    logger.emit(
        EVENT_RUN_STARTED,
        policy_domain=policy.domain,
        max_pages=effective_max_pages,
    )

    queue: deque[tuple[str, int]] = deque((url, 0) for url in policy.seed_urls)
    visited: set[str] = set()
    results: list[dict[str, object]] = []

    fetched = 0
    no_change = 0
    errors = 0

    do_fetch = fetch_fn or (lambda url: fetch(url))
    robots = robots_checker or RobotsChecker()

    while queue and (fetched + no_change + errors) < effective_max_pages:
        current_url, depth = queue.popleft()

        if depth > policy.max_depth:
            continue

        normalized_url = normalize_url(current_url)
        if normalized_url in visited:
            continue
        visited.add(normalized_url)

        if policy.respect_robots and not robots.is_allowed(policy.user_agent, normalized_url):
            logger.emit("robots_blocked", url=normalized_url, depth=depth)
            results.append(
                {
                    "url": normalized_url,
                    "depth": depth,
                    "result": "blocked",
                    "reason": "robots",
                }
            )
            continue

        if policy.rate_limit_ms > 0:
            sleeper(policy.rate_limit_ms / 1000)

        try:
            response = do_fetch(normalized_url)
        except FetchError as exc:
            errors += 1
            logger.emit(
                EVENT_FETCH_ERROR,
                url=normalized_url,
                depth=depth,
                reason=exc.reason,
                duration_ms=exc.duration_ms,
                status=exc.status_code,
            )
            results.append(
                {
                    "url": normalized_url,
                    "depth": depth,
                    "result": "error",
                    "reason": exc.reason,
                    "status": exc.status_code,
                    "duration_ms": exc.duration_ms,
                }
            )
            continue
        except Exception as exc:
            errors += 1
            logger.emit(
                EVENT_FETCH_ERROR,
                url=normalized_url,
                depth=depth,
                reason=f"unexpected_error: {exc}",
                duration_ms=0,
                status=None,
            )
            results.append(
                {
                    "url": normalized_url,
                    "depth": depth,
                    "result": "error",
                    "reason": f"unexpected_error: {exc}",
                    "status": None,
                    "duration_ms": 0,
                }
            )
            continue

        logger.emit(
            EVENT_FETCH_SUCCESS,
            url=normalized_url,
            depth=depth,
            status=response.status,
            duration_ms=response.duration_ms,
            content_type=response.content_type,
            final_url=response.final_url,
        )

        sha256 = sha256_hexdigest(response.body)
        decision = should_save(
            normalized_url,
            response.headers,
            sha256,
            manifest_path=url_index_path,
        )

        if decision == "no_change":
            no_change += 1
            logger.emit(EVENT_DEDUP_HIT, url=normalized_url, depth=depth, sha256=sha256)
            results.append(
                {
                    "url": normalized_url,
                    "depth": depth,
                    "result": "no_change",
                    "status": response.status,
                    "content_type": response.content_type,
                    "final_url": response.final_url,
                }
            )
        else:
            fetched += 1
            saved = write_document(url=normalized_url, response=response, raw_root=raw_root)
            logger.emit(
                EVENT_SAVED,
                url=normalized_url,
                depth=depth,
                raw_path=str(saved.raw_path),
                meta_path=str(saved.meta_path),
                sha256=saved.meta.sha256,
                content_type=saved.meta.content_type,
            )
            results.append(
                {
                    "url": normalized_url,
                    "depth": depth,
                    "result": "fetched",
                    "status": response.status,
                    "content_type": response.content_type,
                    "final_url": response.final_url,
                    "raw_path": str(saved.raw_path),
                    "meta_path": str(saved.meta_path),
                    "sha256": saved.meta.sha256,
                }
            )

        content_type = response.content_type.lower().split(";", 1)[0]
        if content_type in {"text/html", "application/xhtml+xml"} and depth < policy.max_depth:
            html = response.body.decode("utf-8", errors="ignore")
            links = extract_links(
                html,
                response.final_url or normalized_url,
                allowed_domains=[policy.domain],
                allowed_paths_prefix=policy.allowed_paths_prefix,
                disallowed_paths_prefix=policy.disallowed_paths_prefix,
            )
            for link in links:
                if link not in visited:
                    queue.append((link, depth + 1))

    summary = {
        "command_id": command_id,
        "policy_domain": policy.domain,
        "max_pages": effective_max_pages,
        "fetched": fetched,
        "no_change": no_change,
        "errors": errors,
        "visited": len(visited),
    }
    run_manifest_path.write_text(
        json.dumps({"summary": summary, "results": results}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )

    logger.emit(
        EVENT_RUN_FINISHED,
        fetched=fetched,
        no_change=no_change,
        errors=errors,
        visited=len(visited),
        manifest_path=str(run_manifest_path),
    )

    return CrawlRunResult(
        command_id=command_id,
        fetched=fetched,
        no_change=no_change,
        errors=errors,
        visited=len(visited),
        manifest_path=run_manifest_path,
        log_path=log_path,
    )

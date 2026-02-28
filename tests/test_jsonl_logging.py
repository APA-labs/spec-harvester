from __future__ import annotations

import json
import re

from spec_harvester.application.queue import run_crawl
from spec_harvester.domain.policy import Policy
from spec_harvester.infrastructure.http.http_client import FetchError, ResponseData
from spec_harvester.infrastructure.logging.jsonl import (
    EVENT_DEDUP_HIT,
    EVENT_FETCH_ERROR,
    EVENT_FETCH_SUCCESS,
    EVENT_RUN_FINISHED,
    EVENT_RUN_STARTED,
    EVENT_SAVED,
)


class _AllowAllRobots:
    def is_allowed(self, user_agent: str, url: str) -> bool:
        return True


def test_jsonl_logging_includes_required_events(tmp_path) -> None:
    policy = Policy(
        domain="www.w3.org",
        seed_urls=["https://www.w3.org/TR/a", "https://www.w3.org/TR/b"],
        allowed_paths_prefix=["/TR/"],
        disallowed_paths_prefix=[],
        max_depth=1,
        max_pages=10,
        rate_limit_ms=0,
        user_agent="SpecHarvesterCrawler/0.1",
        respect_robots=True,
    )

    success_response = ResponseData(
        status=200,
        headers={"content-type": "text/html", "etag": '"v1"'},
        body=b"<html>ok</html>",
        final_url="https://www.w3.org/TR/a",
        content_type="text/html",
        duration_ms=5,
    )

    def fetch_first_run(url: str) -> ResponseData:
        if url.endswith("/a"):
            return success_response
        raise FetchError(url=url, reason="network_error: boom", attempts=1, duration_ms=7)

    run1 = run_crawl(
        policy=policy,
        raw_root=tmp_path / "storage" / "raw",
        manifest_root=tmp_path / "storage" / "manifests",
        log_root=tmp_path / "logs",
        fetch_fn=fetch_first_run,
        robots_checker=_AllowAllRobots(),
        sleeper=lambda _: None,
    )

    def fetch_second_run(url: str) -> ResponseData:
        if url.endswith("/a"):
            return success_response
        raise FetchError(url=url, reason="network_error: boom", attempts=1, duration_ms=7)

    run2 = run_crawl(
        policy=policy,
        raw_root=tmp_path / "storage" / "raw",
        manifest_root=tmp_path / "storage" / "manifests",
        log_root=tmp_path / "logs",
        fetch_fn=fetch_second_run,
        robots_checker=_AllowAllRobots(),
        sleeper=lambda _: None,
    )

    log1_events = [json.loads(line)["event"] for line in run1.log_path.read_text(encoding="utf-8").splitlines()]
    log2_events = [json.loads(line)["event"] for line in run2.log_path.read_text(encoding="utf-8").splitlines()]

    all_events = set(log1_events + log2_events)
    required = {
        EVENT_RUN_STARTED,
        EVENT_FETCH_SUCCESS,
        EVENT_FETCH_ERROR,
        EVENT_SAVED,
        EVENT_DEDUP_HIT,
        EVENT_RUN_FINISHED,
    }
    assert required.issubset(all_events)

    assert re.search(r"run-\d{8}T\d{6}\d{6}Z\.jsonl$", run1.log_path.name)
    assert run1.log_path != run2.log_path

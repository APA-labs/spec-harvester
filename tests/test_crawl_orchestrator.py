from __future__ import annotations

import json

from spec_crawler.application.queue import run_crawl
from spec_crawler.domain.policy import Policy
from spec_crawler.infrastructure.http.http_client import ResponseData


class _AllowAllRobots:
    def is_allowed(self, user_agent: str, url: str) -> bool:
        return True


def test_run_crawl_creates_raw_manifest_and_logs(tmp_path) -> None:
    policy = Policy(
        domain="www.w3.org",
        seed_urls=["https://www.w3.org/TR/"],
        allowed_paths_prefix=["/TR/"],
        disallowed_paths_prefix=["/blog/"],
        max_depth=3,
        max_pages=50,
        rate_limit_ms=0,
        user_agent="SpecHarvesterCrawler/0.1",
        respect_robots=True,
    )

    pages = {
        "https://www.w3.org/TR": ResponseData(
            status=200,
            headers={"content-type": "text/html"},
            body=(
                b'<a href="/TR/wai-aria/">a</a>'
                b'<a href="/TR/html-aam-1.0/">b</a>'
                b'<a href="/blog/post">blog</a>'
            ),
            final_url="https://www.w3.org/TR/",
            content_type="text/html",
            duration_ms=10,
        ),
        "https://www.w3.org/TR/wai-aria": ResponseData(
            status=200,
            headers={"content-type": "text/html"},
            body=b"<html>wai-aria</html>",
            final_url="https://www.w3.org/TR/wai-aria/",
            content_type="text/html",
            duration_ms=12,
        ),
        "https://www.w3.org/TR/html-aam-1.0": ResponseData(
            status=200,
            headers={"content-type": "application/pdf"},
            body=b"%PDF-1.7 mock",
            final_url="https://www.w3.org/TR/html-aam-1.0/",
            content_type="application/pdf",
            duration_ms=15,
        ),
    }

    def fake_fetch(url: str) -> ResponseData:
        return pages[url]

    result = run_crawl(
        policy=policy,
        max_pages=50,
        raw_root=tmp_path / "storage" / "raw",
        manifest_root=tmp_path / "storage" / "manifests",
        log_root=tmp_path / "logs",
        fetch_fn=fake_fetch,
        robots_checker=_AllowAllRobots(),
        sleeper=lambda _: None,
    )

    assert result.fetched == 3
    assert result.no_change == 0
    assert result.errors == 0
    assert result.manifest_path.exists()
    assert result.log_path.exists()

    raw_files = sorted((tmp_path / "storage" / "raw").rglob("*.*"))
    assert any(path.suffix == ".html" for path in raw_files)
    assert any(path.suffix == ".pdf" for path in raw_files)
    assert any(path.name.endswith(".meta.json") for path in raw_files)

    run_manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert run_manifest["summary"]["fetched"] == 3
    assert len(run_manifest["results"]) == 3

    events = [json.loads(line)["event"] for line in result.log_path.read_text(encoding="utf-8").splitlines()]
    assert "run_started" in events
    assert "fetch_success" in events
    assert "saved" in events
    assert "run_finished" in events

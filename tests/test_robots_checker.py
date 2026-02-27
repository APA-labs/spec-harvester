from __future__ import annotations

import logging

from spec_harvester.infrastructure.http.robots import RobotsChecker


def test_robots_deny_and_cache_once() -> None:
    calls = {"count": 0}

    def fetcher(_: str) -> str:
        calls["count"] += 1
        return "User-agent: *\nDisallow: /private"

    checker = RobotsChecker(fetcher=fetcher)

    assert checker.is_allowed("SpecHarvesterCrawler", "https://example.com/public") is True
    assert checker.is_allowed("SpecHarvesterCrawler", "https://example.com/private/page") is False
    assert checker.is_allowed("SpecHarvesterCrawler", "https://example.com/private/other") is False
    assert calls["count"] == 1


def test_robots_fetch_failure_allows_and_logs(caplog) -> None:
    def fetcher(_: str) -> str:
        raise RuntimeError("network down")

    checker = RobotsChecker(fetcher=fetcher)

    with caplog.at_level(logging.WARNING):
        allowed = checker.is_allowed("SpecHarvesterCrawler", "https://example.com/private")

    assert allowed is True
    assert "robots fetch failed" in caplog.text

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

LOGGER = logging.getLogger(__name__)


@dataclass
class _RobotsPolicy:
    allow_all: bool
    parser: RobotFileParser | None = None


class RobotsChecker:
    """Check robots.txt rules with per-origin caching."""

    def __init__(
        self,
        fetcher: Callable[[str], str] | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._fetcher = fetcher or _default_fetch_robots_txt
        self._logger = logger or LOGGER
        self._cache: dict[str, _RobotsPolicy] = {}

    def is_allowed(self, user_agent: str, url: str) -> bool:
        split = urlsplit(url)
        if not split.scheme or not split.netloc:
            raise ValueError(f"invalid absolute URL: {url}")

        origin = f"{split.scheme.lower()}://{split.netloc.lower()}"
        policy = self._cache.get(origin)
        if policy is None:
            policy = self._load_policy(origin)
            self._cache[origin] = policy

        if policy.allow_all:
            return True

        assert policy.parser is not None
        return policy.parser.can_fetch(user_agent, url)

    def _load_policy(self, origin: str) -> _RobotsPolicy:
        robots_url = f"{origin}/robots.txt"
        try:
            robots_txt = self._fetcher(robots_url)
        except Exception as exc:  # pragma: no cover - exercised in tests via fetcher
            self._logger.warning(
                "robots fetch failed for %s; allowing crawl by fallback: %s",
                robots_url,
                exc,
            )
            return _RobotsPolicy(allow_all=True)

        parser = RobotFileParser()
        parser.set_url(robots_url)
        parser.parse(robots_txt.splitlines())
        return _RobotsPolicy(allow_all=False, parser=parser)


def _default_fetch_robots_txt(robots_url: str) -> str:
    import httpx

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        response = client.get(robots_url)

    if response.status_code == 404:
        return ""

    response.raise_for_status()
    return response.text


_DEFAULT_CHECKER = RobotsChecker()


def is_allowed(user_agent: str, url: str) -> bool:
    return _DEFAULT_CHECKER.is_allowed(user_agent=user_agent, url=url)

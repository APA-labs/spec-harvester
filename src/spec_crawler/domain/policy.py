from __future__ import annotations

from dataclasses import dataclass


class PolicyError(ValueError):
    """Raised when policy files are invalid or cannot be loaded."""


@dataclass(frozen=True)
class Policy:
    domain: str
    seed_urls: list[str]
    allowed_paths_prefix: list[str]
    disallowed_paths_prefix: list[str]
    max_depth: int
    max_pages: int
    rate_limit_ms: int
    user_agent: str
    respect_robots: bool

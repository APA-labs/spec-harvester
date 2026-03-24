from __future__ import annotations

import json
from pathlib import Path

from spec_harvester.domain.policy import Policy, PolicyError


POLICY_DIR = Path(__file__).resolve().parent / "policies"


def _validate_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PolicyError(f"{field_name} must be a non-empty string")
    return value.strip()


def _validate_string_list(value: object, field_name: str, *, allow_empty: bool) -> list[str]:
    if value is None:
        return [] if allow_empty else []
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise PolicyError(f"{field_name} must be a list of strings")
    cleaned = [item.strip() for item in value if item.strip()]
    if not allow_empty and not cleaned:
        raise PolicyError(f"{field_name} must not be empty")
    return cleaned


def _validate_positive_int(value: object, field_name: str, *, minimum: int = 1) -> int:
    if not isinstance(value, int) or value < minimum:
        raise PolicyError(f"{field_name} must be an integer >= {minimum}")
    return value


def _from_dict(data: dict[str, object]) -> Policy:
    domain = _validate_non_empty_string(data.get("domain"), "domain")
    seed_urls = _validate_string_list(data.get("seed_urls"), "seed_urls", allow_empty=False)
    allowed_paths_prefix = _validate_string_list(
        data.get("allowed_paths_prefix", []),
        "allowed_paths_prefix",
        allow_empty=True,
    )
    disallowed_paths_prefix = _validate_string_list(
        data.get("disallowed_paths_prefix", []),
        "disallowed_paths_prefix",
        allow_empty=True,
    )
    max_depth = _validate_positive_int(data.get("max_depth", 3), "max_depth")
    max_pages = _validate_positive_int(data.get("max_pages", 200), "max_pages")
    rate_limit_ms = _validate_positive_int(data.get("rate_limit_ms", 700), "rate_limit_ms", minimum=0)
    user_agent = _validate_non_empty_string(
        data.get("user_agent", "SpecHarvesterCrawler/0.1"),
        "user_agent",
    )

    respect_robots_raw = data.get("respect_robots", True)
    if not isinstance(respect_robots_raw, bool):
        raise PolicyError("respect_robots must be a boolean")

    return Policy(
        domain=domain,
        seed_urls=seed_urls,
        allowed_paths_prefix=allowed_paths_prefix,
        disallowed_paths_prefix=disallowed_paths_prefix,
        max_depth=max_depth,
        max_pages=max_pages,
        rate_limit_ms=rate_limit_ms,
        user_agent=user_agent,
        respect_robots=respect_robots_raw,
    )


def load_all_policies() -> list[Policy]:
    return [load_policy(p.stem) for p in sorted(POLICY_DIR.glob("*.json"))]


def load_policy(name: str) -> Policy:
    policy_name = _validate_non_empty_string(name, "name")
    policy_path = POLICY_DIR / f"{policy_name}.json"

    if not policy_path.exists():
        raise PolicyError(f"policy file not found: {policy_path}")

    try:
        data = json.loads(policy_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PolicyError(f"invalid policy json: {policy_path}") from exc

    if not isinstance(data, dict):
        raise PolicyError("policy json must be an object")

    return _from_dict(data)

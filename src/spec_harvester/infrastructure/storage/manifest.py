from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from spec_harvester.domain.url import normalize_url

ChangeDecision = Literal["fetched", "no_change"]


def should_save(
    url: str,
    headers: dict[str, str] | None,
    sha256: str,
    *,
    manifest_path: str | Path = "storage/manifests/url_index.json",
) -> ChangeDecision:
    normalized_url = normalize_url(url)
    path = Path(manifest_path)
    index = _load_index(path)

    previous = index.get(normalized_url, {})
    current_headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}

    etag = _clean_value(current_headers.get("etag"))
    last_modified = _clean_value(current_headers.get("last-modified"))

    previous_etag = _clean_value(previous.get("etag"))
    previous_last_modified = _clean_value(previous.get("last_modified"))
    previous_sha = _clean_value(previous.get("sha256"))

    if etag and previous_etag and etag == previous_etag:
        return "no_change"

    if last_modified and previous_last_modified and last_modified == previous_last_modified:
        return "no_change"

    if not etag and not last_modified and previous_sha and previous_sha == sha256:
        return "no_change"

    index[normalized_url] = {
        "etag": etag,
        "last_modified": last_modified,
        "sha256": sha256,
        "updated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_index(path, index)
    return "fetched"


def _clean_value(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    cleaned = value.strip()
    return cleaned or None


def _load_index(path: Path) -> dict[str, dict[str, str | None]]:
    if not path.exists():
        return {}

    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"manifest index must be a JSON object: {path}")

    return raw  # type: ignore[return-value]


def _write_index(path: Path, index: dict[str, dict[str, str | None]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, ensure_ascii=True, indent=2, sort_keys=True), encoding="utf-8")

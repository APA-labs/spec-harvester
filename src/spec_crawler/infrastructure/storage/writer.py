from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from spec_crawler.domain.hashing import sha256_hexdigest
from spec_crawler.domain.meta import DocumentMeta
from spec_crawler.infrastructure.http.http_client import ResponseData


@dataclass(frozen=True)
class SavedDocument:
    raw_path: Path
    meta_path: Path
    meta: DocumentMeta


def write_document(
    *,
    url: str,
    response: ResponseData,
    raw_root: str | Path = "storage/raw",
    fetched_at: datetime | None = None,
) -> SavedDocument:
    if fetched_at is None:
        fetched_at = datetime.now(timezone.utc)
    elif fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)

    fetched_at_utc = fetched_at.astimezone(timezone.utc)
    day_dir = Path(raw_root) / fetched_at_utc.date().isoformat()
    day_dir.mkdir(parents=True, exist_ok=True)

    sha256 = sha256_hexdigest(response.body)
    extension = _extension_for_content_type(response.content_type)

    raw_path = day_dir / f"{sha256}.{extension}"
    raw_path.write_bytes(response.body)

    meta = DocumentMeta(
        url=url,
        fetched_at=fetched_at_utc.isoformat().replace("+00:00", "Z"),
        status=response.status,
        content_type=response.content_type,
        sha256=sha256,
        bytes=len(response.body),
        headers={
            "etag": response.headers.get("etag"),
            "last-modified": response.headers.get("last-modified"),
        },
        final_url=response.final_url,
    )

    meta_path = day_dir / f"{sha256}.meta.json"
    meta_path.write_text(json.dumps(meta.to_dict(), ensure_ascii=True, indent=2), encoding="utf-8")

    return SavedDocument(raw_path=raw_path, meta_path=meta_path, meta=meta)


def _extension_for_content_type(content_type: str) -> str:
    normalized = content_type.lower().split(";", 1)[0].strip()
    if normalized == "text/html" or normalized == "application/xhtml+xml":
        return "html"
    if normalized == "application/pdf":
        return "pdf"
    return "bin"

from __future__ import annotations

import json
from datetime import datetime, timezone

from spec_harvester.domain.hashing import sha256_hexdigest
from spec_harvester.infrastructure.http.http_client import ResponseData
from spec_harvester.infrastructure.storage.writer import write_document


def test_write_document_saves_raw_and_meta_with_sha_match(tmp_path) -> None:
    body = b"<html><body>w3c sample</body></html>"
    response = ResponseData(
        status=200,
        headers={"etag": "abc123", "last-modified": "Tue, 27 Feb 2026 00:00:00 GMT"},
        body=body,
        final_url="https://www.w3.org/TR/",
        content_type="text/html; charset=UTF-8",
        duration_ms=42,
    )

    saved = write_document(
        url="https://www.w3.org/TR/",
        response=response,
        raw_root=tmp_path / "raw",
        fetched_at=datetime(2026, 2, 27, 12, 30, tzinfo=timezone.utc),
    )

    assert saved.raw_path.exists()
    assert saved.meta_path.exists()

    expected_sha = sha256_hexdigest(body)
    assert saved.raw_path.name == f"{expected_sha}.html"
    assert saved.meta_path.name == f"{expected_sha}.meta.json"
    assert saved.raw_path.read_bytes() == body

    meta = json.loads(saved.meta_path.read_text(encoding="utf-8"))
    assert meta["sha256"] == expected_sha
    assert meta["bytes"] == len(body)
    assert meta["url"] == "https://www.w3.org/TR/"
    assert meta["final_url"] == "https://www.w3.org/TR/"
    assert meta["headers"]["etag"] == "abc123"
    assert meta["headers"]["last-modified"] == "Tue, 27 Feb 2026 00:00:00 GMT"


def test_write_document_pdf_extension(tmp_path) -> None:
    response = ResponseData(
        status=200,
        headers={},
        body=b"%PDF-1.7",
        final_url="https://www.w3.org/TR/pdf-sample",
        content_type="application/pdf",
        duration_ms=21,
    )

    saved = write_document(
        url="https://www.w3.org/TR/pdf-sample",
        response=response,
        raw_root=tmp_path / "raw",
        fetched_at=datetime(2026, 2, 27, 12, 30, tzinfo=timezone.utc),
    )

    assert saved.raw_path.suffix == ".pdf"
    assert saved.meta_path.exists()

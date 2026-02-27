from __future__ import annotations

from spec_harvester.infrastructure.storage.manifest import should_save


def test_should_save_second_run_is_no_change_by_etag(tmp_path) -> None:
    manifest = tmp_path / "manifests" / "url_index.json"

    first = should_save(
        "https://www.w3.org/TR/",
        {"etag": '"v1"'},
        "sha-a",
        manifest_path=manifest,
    )
    second = should_save(
        "https://www.w3.org/TR/#section",
        {"etag": '"v1"'},
        "sha-b",
        manifest_path=manifest,
    )

    assert first == "fetched"
    assert second == "no_change"


def test_should_save_no_change_by_last_modified(tmp_path) -> None:
    manifest = tmp_path / "manifests" / "url_index.json"

    should_save(
        "https://www.w3.org/TR/spec",
        {"last-modified": "Tue, 27 Feb 2026 00:00:00 GMT"},
        "sha-a",
        manifest_path=manifest,
    )

    decision = should_save(
        "https://www.w3.org/TR/spec",
        {"last-modified": "Tue, 27 Feb 2026 00:00:00 GMT"},
        "sha-b",
        manifest_path=manifest,
    )

    assert decision == "no_change"


def test_should_save_no_change_by_sha_when_cache_headers_missing(tmp_path) -> None:
    manifest = tmp_path / "manifests" / "url_index.json"

    first = should_save("https://www.w3.org/TR/html", {}, "sha-same", manifest_path=manifest)
    second = should_save("https://www.w3.org/TR/html", {}, "sha-same", manifest_path=manifest)
    third = should_save("https://www.w3.org/TR/html", {}, "sha-new", manifest_path=manifest)

    assert first == "fetched"
    assert second == "no_change"
    assert third == "fetched"

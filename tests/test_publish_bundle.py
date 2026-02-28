from __future__ import annotations

import json
from pathlib import Path
import tarfile

from spec_harvester.application.publish import build_publish_bundle


def test_build_publish_bundle_for_specific_run(tmp_path: Path) -> None:
    raw = tmp_path / "storage" / "raw" / "2026-02-28"
    manifests = tmp_path / "storage" / "manifests"
    logs = tmp_path / "logs"

    raw.mkdir(parents=True)
    manifests.mkdir(parents=True)
    logs.mkdir(parents=True)

    raw_file = raw / "abc.html"
    meta_file = raw / "abc.meta.json"
    raw_file.write_text("<html/>", encoding="utf-8")
    meta_file.write_text("{}", encoding="utf-8")

    run_id = "20260228T999999999999Z"
    run_manifest = manifests / f"run-{run_id}.json"
    run_manifest.write_text(
        json.dumps(
            {
                "summary": {},
                "results": [
                    {
                        "result": "fetched",
                        "raw_path": "storage/raw/2026-02-28/abc.html",
                        "meta_path": "storage/raw/2026-02-28/abc.meta.json",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    (manifests / "url_index.json").write_text("{}", encoding="utf-8")
    (logs / f"run-{run_id}.jsonl").write_text('{"event":"run_finished"}\n', encoding="utf-8")

    result = build_publish_bundle(
        run_id=run_id,
        manifest_root=manifests,
        log_root=logs,
        output_dir=tmp_path / "exports",
        repo_root=tmp_path,
    )

    assert result.run_id == run_id
    assert result.bundle_path.exists()
    assert not result.missing_files

    with tarfile.open(result.bundle_path, "r:gz") as tar:
        names = sorted(tar.getnames())

    assert f"storage/manifests/run-{run_id}.json" in names
    assert "storage/manifests/url_index.json" in names
    assert f"logs/run-{run_id}.jsonl" in names
    assert "storage/raw/2026-02-28/abc.html" in names
    assert "storage/raw/2026-02-28/abc.meta.json" in names


def test_build_publish_bundle_uses_latest_when_run_id_missing(tmp_path: Path) -> None:
    manifests = tmp_path / "storage" / "manifests"
    logs = tmp_path / "logs"
    manifests.mkdir(parents=True)
    logs.mkdir(parents=True)

    older_id = "20260227T010101010101Z"
    newer_id = "20260228T020202020202Z"

    (manifests / f"run-{older_id}.json").write_text('{"results": []}', encoding="utf-8")
    (manifests / f"run-{newer_id}.json").write_text('{"results": []}', encoding="utf-8")
    (manifests / "url_index.json").write_text("{}", encoding="utf-8")

    result = build_publish_bundle(
        manifest_root=manifests,
        log_root=logs,
        output_dir=tmp_path / "exports",
        repo_root=tmp_path,
    )

    assert result.run_id == newer_id
    assert any(path.endswith(f"logs/run-{newer_id}.jsonl") for path in result.missing_files)

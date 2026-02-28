from __future__ import annotations

import json

from spec_harvester.application.audit import render_audit_report, run_audit


def test_run_audit_summarizes_ratios_and_content_types(tmp_path) -> None:
    manifests = tmp_path / "manifests"
    manifests.mkdir()

    (manifests / "run-1.json").write_text(
        json.dumps(
            {
                "summary": {},
                "results": [
                    {"result": "fetched", "content_type": "text/html"},
                    {"result": "no_change", "content_type": "text/html"},
                    {"result": "error"},
                ],
            }
        ),
        encoding="utf-8",
    )
    (manifests / "run-2.json").write_text(
        json.dumps(
            {
                "summary": {},
                "results": [
                    {"result": "fetched", "content_type": "application/pdf"},
                    {"result": "no_change", "content_type": "application/pdf"},
                    {"result": "error"},
                ],
            }
        ),
        encoding="utf-8",
    )
    # Should be ignored by run_audit (not matching run-*.json)
    (manifests / "url_index.json").write_text("{}", encoding="utf-8")

    report = run_audit(manifest_root=manifests)

    assert report.manifests_scanned == 2
    assert report.fetched == 2
    assert report.no_change == 2
    assert report.errors == 2
    assert report.content_type_counts == {"application/pdf": 2, "text/html": 2}

    output = render_audit_report(report)
    assert "fetched: 2 (33.3%)" in output
    assert "no_change: 2 (33.3%)" in output
    assert "error: 2 (33.3%)" in output
    assert "text/html: 2 (50.0%)" in output


def test_run_audit_handles_missing_manifest_dir(tmp_path) -> None:
    report = run_audit(manifest_root=tmp_path / "missing")
    assert report.manifests_scanned == 0
    assert report.total == 0

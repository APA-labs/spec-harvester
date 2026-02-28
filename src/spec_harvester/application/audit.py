from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AuditReport:
    manifests_scanned: int
    fetched: int
    no_change: int
    errors: int
    content_type_counts: dict[str, int]

    @property
    def total(self) -> int:
        return self.fetched + self.no_change + self.errors


def run_audit(manifest_root: str | Path = "storage/manifests") -> AuditReport:
    root = Path(manifest_root)
    if not root.exists():
        return AuditReport(0, 0, 0, 0, {})

    fetched = 0
    no_change = 0
    errors = 0
    content_type_counts: dict[str, int] = {}

    run_files = sorted(p for p in root.glob("run-*.json") if p.is_file())

    for run_file in run_files:
        payload = json.loads(run_file.read_text(encoding="utf-8"))
        results = payload.get("results", [])
        if not isinstance(results, list):
            continue

        for row in results:
            if not isinstance(row, dict):
                continue

            result = str(row.get("result", "")).strip().lower()
            if result == "fetched":
                fetched += 1
            elif result == "no_change":
                no_change += 1
            elif result == "error":
                errors += 1

            content_type = str(row.get("content_type", "")).strip().lower()
            if content_type:
                content_type_counts[content_type] = content_type_counts.get(content_type, 0) + 1

    return AuditReport(
        manifests_scanned=len(run_files),
        fetched=fetched,
        no_change=no_change,
        errors=errors,
        content_type_counts=dict(sorted(content_type_counts.items())),
    )


def render_audit_report(report: AuditReport) -> str:
    total = report.total

    def ratio(count: int) -> float:
        return (count / total * 100.0) if total else 0.0

    lines = [
        "Audit Report",
        f"- manifests_scanned: {report.manifests_scanned}",
        f"- total_results: {total}",
        f"- fetched: {report.fetched} ({ratio(report.fetched):.1f}%)",
        f"- no_change: {report.no_change} ({ratio(report.no_change):.1f}%)",
        f"- error: {report.errors} ({ratio(report.errors):.1f}%)",
        "- content_type_distribution:",
    ]

    if not report.content_type_counts:
        lines.append("  (none)")
    else:
        typed_total = sum(report.content_type_counts.values())
        for content_type, count in report.content_type_counts.items():
            pct = (count / typed_total * 100.0) if typed_total else 0.0
            lines.append(f"  {content_type}: {count} ({pct:.1f}%)")

    return "\n".join(lines)

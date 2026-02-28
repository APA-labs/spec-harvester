from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
import tarfile


@dataclass(frozen=True)
class PublishBundleResult:
    run_id: str
    bundle_path: Path
    included_files: list[str]
    missing_files: list[str]


def build_publish_bundle(
    *,
    run_id: str | None = None,
    manifest_root: str | Path = "storage/manifests",
    log_root: str | Path = "logs",
    output_dir: str | Path = "exports",
    repo_root: str | Path = ".",
) -> PublishBundleResult:
    root = Path(repo_root).resolve()
    manifests = (root / Path(manifest_root)).resolve()
    logs = (root / Path(log_root)).resolve()

    manifest_path = _resolve_run_manifest(manifests, run_id)
    selected_run_id = _extract_run_id(manifest_path)

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = payload.get("results", []) if isinstance(payload, dict) else []

    candidates: set[Path] = set()
    candidates.add(manifest_path)

    url_index = manifests / "url_index.json"
    candidates.add(url_index)

    log_file = logs / f"run-{selected_run_id}.jsonl"
    candidates.add(log_file)

    if isinstance(results, list):
        for row in results:
            if not isinstance(row, dict):
                continue
            for key in ("raw_path", "meta_path"):
                val = row.get(key)
                if isinstance(val, str) and val.strip():
                    p = Path(val.strip())
                    resolved = p.resolve() if p.is_absolute() else (root / p).resolve()
                    candidates.add(resolved)

    included: list[str] = []
    missing: list[str] = []

    out_dir = (root / Path(output_dir)).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = out_dir / f"spec-harvester-run-{selected_run_id}.tar.gz"

    with tarfile.open(bundle_path, "w:gz") as tar:
        for p in sorted(candidates):
            if p.exists() and p.is_file():
                arcname = _to_arcname(p, root)
                tar.add(p, arcname=arcname)
                included.append(arcname)
            else:
                missing.append(_to_arcname(p, root))

    return PublishBundleResult(
        run_id=selected_run_id,
        bundle_path=bundle_path,
        included_files=included,
        missing_files=missing,
    )


def _resolve_run_manifest(manifest_root: Path, run_id: str | None) -> Path:
    if not manifest_root.exists():
        raise FileNotFoundError(f"manifest directory not found: {manifest_root}")

    if run_id:
        path = manifest_root / f"run-{run_id}.json"
        if not path.exists():
            raise FileNotFoundError(f"run manifest not found: {path}")
        return path

    run_files = sorted(p for p in manifest_root.glob("run-*.json") if p.is_file())
    if not run_files:
        raise FileNotFoundError(f"no run manifests found in: {manifest_root}")

    return run_files[-1]


def _extract_run_id(manifest_path: Path) -> str:
    name = manifest_path.name
    if not name.startswith("run-") or not name.endswith(".json"):
        raise ValueError(f"invalid run manifest filename: {name}")
    return name[len("run-") : -len(".json")]


def _to_arcname(path: Path, repo_root: Path) -> str:
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return path.name

from __future__ import annotations

from pathlib import Path

import pytest

from spec_crawler.config.policy import PolicyError, load_policy


def test_load_policy_success() -> None:
    policy = load_policy("w3c")
    assert policy.domain == "www.w3.org"
    assert policy.seed_urls == ["https://www.w3.org/TR/"]
    assert policy.max_depth == 3
    assert policy.respect_robots is True


def test_load_policy_validation_error(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()
    (policies_dir / "invalid.json").write_text(
        '{"domain": "", "seed_urls": []}',
        encoding="utf-8",
    )

    monkeypatch.setattr("spec_crawler.config.policy.POLICY_DIR", policies_dir)

    with pytest.raises(PolicyError):
        load_policy("invalid")


def test_load_policy_invalid_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    policies_dir = tmp_path / "policies"
    policies_dir.mkdir()
    (policies_dir / "broken.json").write_text("{not-json", encoding="utf-8")

    monkeypatch.setattr("spec_crawler.config.policy.POLICY_DIR", policies_dir)

    with pytest.raises(PolicyError):
        load_policy("broken")

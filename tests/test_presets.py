from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from agentkit.commands import init_repo
from agentkit.config import parse_config


def test_recommended_v1_is_materialized_with_provenance_and_rules(tmp_path: Path) -> None:
    init_repo(tmp_path, preset="recommended-v1")

    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    assert raw["preset"] == {"source": "agentkit", "name": "recommended-v1", "version": 1}
    assert raw["rules"]["working_tree_clean"] == {"enabled": True, "severity": "error"}
    assert raw["rules"]["check_receipt_current"] == {"enabled": True, "severity": "error"}
    assert raw["rules"]["review_addressed"] == {
        "enabled": True,
        "severity": "error",
        "allow_skip": True,
    }
    assert raw["rules"]["blocked_question_recorded"] == {"enabled": True, "severity": "error"}
    assert raw["reminders"] == {
        "open_task": True,
        "ready_to_close": True,
        "stale_terminal": True,
    }


def test_plain_init_remains_backward_compatible_without_preset_metadata(tmp_path: Path) -> None:
    init_repo(tmp_path)

    raw = yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))
    assert "preset" not in raw
    assert "rules" not in raw
    assert "reminders" not in raw


def test_reapplying_preset_is_idempotent_and_preserves_supported_override(tmp_path: Path) -> None:
    init_repo(tmp_path, preset="recommended-v1")
    path = tmp_path / "agentkit.yml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    raw["rules"]["working_tree_clean"]["severity"] = "warning"
    overridden = "# repository policy comment\n" + yaml.safe_dump(raw, sort_keys=False)
    path.write_text(overridden, encoding="utf-8")

    init_repo(tmp_path, preset="recommended-v1")

    reapplied = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert reapplied["rules"]["working_tree_clean"]["severity"] == "warning"
    assert path.read_text(encoding="utf-8") == overridden


def test_applying_preset_to_existing_config_preserves_comments_and_unrelated_text(tmp_path: Path) -> None:
    init_repo(tmp_path)
    path = tmp_path / "agentkit.yml"
    existing = path.read_text(encoding="utf-8") + "\n# keep this repository comment\ncustom_policy: keep-me\n"
    path.write_text(existing, encoding="utf-8")

    init_repo(tmp_path, preset="recommended-v1")

    materialized = path.read_text(encoding="utf-8")
    assert materialized.startswith(existing.rstrip() + "\n\n")
    assert "# keep this repository comment" in materialized
    assert yaml.safe_load(materialized)["custom_policy"] == "keep-me"


def test_existing_partial_policy_is_rejected_without_rewriting_text(tmp_path: Path) -> None:
    init_repo(tmp_path)
    path = tmp_path / "agentkit.yml"
    existing = path.read_text(encoding="utf-8") + "\n# custom partial policy\nrules: {}\n"
    path.write_text(existing, encoding="utf-8")

    with pytest.raises(ValueError, match="Refusing to rewrite existing AgentKit policy text"):
        init_repo(tmp_path, preset="recommended-v1")

    assert path.read_text(encoding="utf-8") == existing


def test_matching_provenance_with_incomplete_materialization_is_rejected(tmp_path: Path) -> None:
    init_repo(tmp_path)
    path = tmp_path / "agentkit.yml"
    existing = path.read_text(encoding="utf-8") + """
preset:
  source: agentkit
  name: recommended-v1
  version: 1
rules:
  working_tree_clean:
    enabled: true
reminders: {}
"""
    path.write_text(existing, encoding="utf-8")

    with pytest.raises(ValueError, match="Materialized preset `recommended-v1` is incomplete"):
        init_repo(tmp_path, preset="recommended-v1")

    assert path.read_text(encoding="utf-8") == existing


def test_unknown_preset_and_rule_fail_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="Unknown AgentKit preset: future-v9"):
        init_repo(tmp_path, preset="future-v9")
    assert not (tmp_path / "AGENTS.md").exists()

    with pytest.raises(ValueError, match="Unknown lifecycle rule: made_up"):
        parse_config({"rules": {"made_up": {"enabled": True}}})


def test_invalid_rule_option_fails_clearly() -> None:
    with pytest.raises(ValueError, match="working_tree_clean.*allow_skip"):
        parse_config({"rules": {"working_tree_clean": {"allow_skip": True}}})

    with pytest.raises(ValueError, match="severity"):
        parse_config({"rules": {"working_tree_clean": {"severity": "sometimes"}}})

    with pytest.raises(ValueError, match="field `rules` must be a mapping"):
        parse_config({"rules": []})

    with pytest.raises(ValueError, match="field `reminders` must be a mapping"):
        parse_config({"reminders": []})

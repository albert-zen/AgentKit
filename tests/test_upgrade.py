from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

import agentkit
from agentkit.cli import main
from agentkit.commands import doctor, init_repo, upgrade_repo
from agentkit.migrations import (
    AGENTS_BLOCK_END,
    AGENTS_BLOCK_START,
    LEGACY_AGENT_SECTIONS,
    apply_migration_plan,
    plan_repository_upgrade,
)
from agentkit.versions import (
    AGENTS_MANAGED_ARTIFACT_VERSION,
    LATEST_REPOSITORY_FORMAT,
    PACKAGE_VERSION,
    RECOMMENDED_PRESET_VERSION,
    TASK_STATE_SCHEMA_VERSION,
)


def test_package_version_domains_are_explicit_and_synchronized() -> None:
    pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(encoding="utf-8")
    assert agentkit.__version__ == PACKAGE_VERSION == "0.2.0"
    assert 'version = "0.2.0"' in pyproject
    assert LATEST_REPOSITORY_FORMAT == 2
    assert RECOMMENDED_PRESET_VERSION == 1
    assert TASK_STATE_SCHEMA_VERSION == 1
    assert AGENTS_MANAGED_ARTIFACT_VERSION == 2


def _write_v1_repo(repo: Path, *, agents_prefix: str = "", agents_suffix: str = "") -> None:
    repo.mkdir(parents=True, exist_ok=True)
    (repo / "agentkit.yml").write_text(
        """# repository policy
version: 1 # format marker

docs:
  root: docs
  design: docs/design.md
  workflow: null
  decisions: docs/decisions

components:
  bespoke:
    description: 'Keep this quoting'
    code: [src/**]
    docs: [docs/design.md]
    required_docs: [design]
    unknown_component_field: keep

layers:
  domain:
    paths: [src/domain/**]
    may_import: []

review:
  require_for: [architecture]
  default: custom

skills:
  source: custom/SKILL.md
  output: custom/SKILL.md

maintainability:
  budgets:
    - name: custom-budget
      paths: [src/**]
      max_lines: 77
      mode: warn

preset:
  source: agentkit
  name: recommended-v1
  version: 1

rules:
  working_tree_clean: {enabled: false, severity: warning}
  check_receipt_current: {enabled: true, severity: error}
  review_addressed: {enabled: true, severity: warning, allow_skip: false}
  blocked_question_recorded: {enabled: true, severity: error}

reminders: {open_task: false, ready_to_close: true, stale_terminal: false}

x-project-policy:
  preserve: "exactly"
""",
        encoding="utf-8",
    )
    (repo / "AGENTS.md").write_text(
        agents_prefix + LEGACY_AGENT_SECTIONS[0] + agents_suffix,
        encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "design.md").write_text("# Design\n", encoding="utf-8")
    (repo / "src" / "domain").mkdir(parents=True)
    (repo / "src" / "domain" / "model.py").write_text("VALUE = 1\n", encoding="utf-8")
    (repo / "custom").mkdir()
    (repo / "custom" / "SKILL.md").write_text("# Local skill\n", encoding="utf-8")
    (repo / "plugins" / "agentkit" / ".codex-plugin").mkdir(parents=True)
    (repo / "plugins" / "agentkit" / ".codex-plugin" / "plugin.json").write_text(
        '{"name": "agentkit"}\n', encoding="utf-8"
    )
    (repo / ".agents" / "plugins").mkdir(parents=True)
    (repo / ".agents" / "plugins" / "marketplace.json").write_text(
        json.dumps(
            {
                "plugins": [
                    {
                        "name": "agentkit",
                        "source": {"source": "local", "path": "./plugins/agentkit"},
                        "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        "category": "Productivity",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _snapshot(repo: Path) -> dict[str, bytes]:
    return {path.relative_to(repo).as_posix(): path.read_bytes() for path in repo.rglob("*") if path.is_file()}


def test_v1_dry_run_is_complete_and_byte_read_only(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path, dry_run=True)

    assert code == 0
    assert _snapshot(tmp_path) == before
    assert "source repository format: 1" in output
    assert "target repository format: 2" in output
    assert "repository-format-1-to-2" in output
    assert "agentkit.yml" in output and "AGENTS.md" in output
    assert "components, docs, layers, review, maintainability" in output
    assert "dry-run; no files written" in output


def test_v1_apply_changes_only_format_marker_and_known_agents_section(tmp_path: Path) -> None:
    prefix = "# Local instructions\n\n"
    suffix = "\n## Team policy\nDo not rewrite this.\n"
    _write_v1_repo(tmp_path, agents_prefix=prefix, agents_suffix=suffix)
    yaml_before = (tmp_path / "agentkit.yml").read_bytes()

    code, output = upgrade_repo(tmp_path)

    assert code == 0
    yaml_after = (tmp_path / "agentkit.yml").read_bytes()
    assert yaml_after == yaml_before.replace(b"version: 1 # format marker", b"version: 2 # format marker", 1)
    raw = yaml.safe_load(yaml_after)
    assert raw["components"]["bespoke"]["unknown_component_field"] == "keep"
    assert raw["rules"]["working_tree_clean"]["enabled"] is False
    assert raw["reminders"]["open_task"] is False
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert agents.startswith(prefix)
    assert agents.endswith(suffix)
    assert AGENTS_BLOCK_START in agents and AGENTS_BLOCK_END in agents
    assert "changed files" in output.lower()


def test_customized_legacy_agents_section_conflicts_with_zero_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    path = tmp_path / "AGENTS.md"
    path.write_text(path.read_text(encoding="utf-8").replace("durable intent", "custom policy"), encoding="utf-8")
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)

    assert code == 1
    assert "conflict" in output.lower()
    assert "customized" in output.lower()
    assert _snapshot(tmp_path) == before


def test_ambiguous_legacy_agents_markers_conflict_with_zero_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    path = tmp_path / "AGENTS.md"
    path.write_text(path.read_text(encoding="utf-8") + "\n<!-- agentkit:agents-section -->\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    plan = plan_repository_upgrade(tmp_path)

    assert plan.conflicts
    with pytest.raises(ValueError, match="conflicts"):
        apply_migration_plan(plan)
    assert _snapshot(tmp_path) == before


def test_bounded_block_plus_legacy_marker_is_an_ambiguous_conflict(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    bounded = (
        f"### AgentKit\n\n{AGENTS_BLOCK_START}\nmanaged\n{AGENTS_BLOCK_END}\n"
        f"{LEGACY_AGENT_SECTIONS[0]}"
    )
    agents.write_text(bounded, encoding="utf-8")
    before = _snapshot(tmp_path)

    plan = plan_repository_upgrade(tmp_path)

    assert plan.conflicts
    assert "ambiguous" in plan.conflicts[0].reason
    assert _snapshot(tmp_path) == before


def test_dual_agents_filenames_conflict_with_zero_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    (tmp_path / "agents.md").write_text(LEGACY_AGENT_SECTIONS[0], encoding="utf-8")
    if (tmp_path / "AGENTS.md").samefile(tmp_path / "agents.md"):
        pytest.skip("filesystem is case-insensitive")
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)

    assert code == 1
    assert "both AGENTS.md and agents.md" in output
    assert _snapshot(tmp_path) == before


def test_duplicate_quoted_top_level_version_key_conflicts(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    config = tmp_path / "agentkit.yml"
    config.write_text('"version": 99\n' + config.read_text(encoding="utf-8"), encoding="utf-8")
    before = _snapshot(tmp_path)

    plan = plan_repository_upgrade(tmp_path)

    assert plan.conflicts
    assert "exactly one" in plan.conflicts[0].reason
    assert _snapshot(tmp_path) == before


def test_apply_failure_rolls_back_every_planned_file(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    plan = plan_repository_upgrade(tmp_path)
    before = _snapshot(tmp_path)
    calls = 0

    def fail_second(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated replace failure")
        path.write_bytes(content)

    with pytest.raises(OSError, match="simulated"):
        apply_migration_plan(plan, replace_file=fail_second)

    assert _snapshot(tmp_path) == before


def test_apply_refuses_a_stale_plan_before_any_write(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    plan = plan_repository_upgrade(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_text(agents.read_text(encoding="utf-8") + "# concurrent edit\n", encoding="utf-8")
    before_apply = _snapshot(tmp_path)

    with pytest.raises(ValueError, match="changed after planning"):
        apply_migration_plan(plan)

    assert _snapshot(tmp_path) == before_apply


def test_second_file_change_after_first_write_rolls_back_without_overwriting_external_edit(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    plan = plan_repository_upgrade(tmp_path)
    config = tmp_path / "agentkit.yml"
    agents = tmp_path / "AGENTS.md"
    config_before = config.read_bytes()
    external_agents = agents.read_bytes() + b"# concurrent external edit\n"
    injected = False

    def write_and_inject(path: Path, content: bytes) -> None:
        nonlocal injected
        path.write_bytes(content)
        if not injected:
            injected = True
            agents.write_bytes(external_agents)

    with pytest.raises(ValueError, match="immediately before write"):
        apply_migration_plan(plan, replace_file=write_and_inject)

    assert config.read_bytes() == config_before
    assert agents.read_bytes() == external_agents


def test_rollback_preserves_concurrent_edit_to_already_written_file(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    plan = plan_repository_upgrade(tmp_path)
    config = tmp_path / "agentkit.yml"
    agents = tmp_path / "AGENTS.md"
    agents_before = agents.read_bytes()
    concurrent_config = config.read_bytes() + b"# concurrent edit after replacement\n"
    calls = 0

    def fail_after_concurrent_edit(path: Path, content: bytes) -> None:
        nonlocal calls
        calls += 1
        if calls == 2:
            config.write_bytes(concurrent_config)
            raise OSError("second write failed")
        path.write_bytes(content)

    with pytest.raises(RuntimeError, match="preserved concurrent edits"):
        apply_migration_plan(plan, replace_file=fail_after_concurrent_edit)

    assert config.read_bytes() == concurrent_config
    assert agents.read_bytes() == agents_before


@pytest.mark.parametrize("linked_name", ["agentkit.yml", "AGENTS.md"])
def test_symlink_mixed_surface_conflicts_without_changing_link_or_target(
    tmp_path: Path, linked_name: str
) -> None:
    _write_v1_repo(tmp_path)
    linked = tmp_path / linked_name
    target = tmp_path / f"{linked_name}.target"
    target.write_bytes(linked.read_bytes())
    linked.unlink()
    linked.symlink_to(target.name)
    target_before = target.read_bytes()

    code, output = upgrade_repo(tmp_path)

    assert code == 1
    assert "symbolic link" in output
    assert linked.is_symlink()
    assert linked.readlink() == Path(target.name)
    assert target.read_bytes() == target_before


def test_repeat_upgrade_is_successful_noop(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    assert upgrade_repo(tmp_path)[0] == 0
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)

    assert code == 0
    assert "already up to date" in output.lower()
    assert "No files changed" in output
    assert _snapshot(tmp_path) == before


def test_current_v2_upgrade_is_noop_even_when_unrelated_checks_fail(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    assert upgrade_repo(tmp_path)[0] == 0
    (tmp_path / "docs" / "design.md").unlink()
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)

    assert code == 0
    assert "already up to date" in output.lower()
    assert _snapshot(tmp_path) == before


def test_deterministic_check_failure_blocks_upgrade_without_receipt_or_repo_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    (tmp_path / "docs" / "design.md").unlink()
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)

    assert code == 1
    assert "manifest" in output
    assert "zero files written" in output
    assert _snapshot(tmp_path) == before
    assert not (tmp_path / ".agentkit").exists()


def test_doctor_and_dry_run_agree_when_deterministic_validation_blocks(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    (tmp_path / "docs" / "design.md").unlink()

    doctor_code, doctor_output = doctor(tmp_path)
    upgrade_code, upgrade_output = upgrade_repo(tmp_path, dry_run=True)

    assert doctor_code == upgrade_code == 1
    assert "repository format status: blocked" in doctor_output
    assert "blocked; zero files written" in upgrade_output


def test_non_utf8_agents_bytes_render_a_conflict_without_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    agents = tmp_path / "AGENTS.md"
    agents.write_bytes(b"\xff" + agents.read_bytes())
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path, dry_run=True)

    assert code == 1
    assert "not valid UTF-8" in output
    assert "Conflicts" in output
    assert _snapshot(tmp_path) == before

    doctor_code, doctor_output = doctor(tmp_path)
    assert doctor_code == 1
    assert "repository format status: blocked" in doctor_output
    assert "Unable to read AGENTS.md as UTF-8" in doctor_output


def test_non_utf8_config_bytes_render_unknown_source_conflict_without_writes(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    config = tmp_path / "agentkit.yml"
    config.write_bytes(b"\xff" + config.read_bytes())
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path, dry_run=True)
    doctor_code, doctor_output = doctor(tmp_path)

    assert code == doctor_code == 1
    assert "source repository format: unknown" in output
    assert "repository format cannot be read safely" in output
    assert "repository format status: blocked" in doctor_output
    assert _snapshot(tmp_path) == before


def test_apply_preserves_file_permissions(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    config = tmp_path / "agentkit.yml"
    agents = tmp_path / "AGENTS.md"
    config.chmod(0o640)
    agents.chmod(0o644)

    assert upgrade_repo(tmp_path)[0] == 0

    assert config.stat().st_mode & 0o777 == 0o640
    assert agents.stat().st_mode & 0o777 == 0o644


def test_new_init_creates_v2_and_bounded_agents_block(tmp_path: Path) -> None:
    init_repo(tmp_path)

    assert yaml.safe_load((tmp_path / "agentkit.yml").read_text(encoding="utf-8"))["version"] == 2
    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert AGENTS_BLOCK_START in agents
    assert AGENTS_BLOCK_END in agents
    assert "<!-- agentkit:agents-section -->" not in agents


def test_doctor_reports_format_status_for_v1_v2_and_conflict(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    code, output = doctor(tmp_path)
    assert code == 0
    assert "current repository format: 1" in output
    assert "latest supported format: 2" in output
    assert "upgrade_available" in output

    (tmp_path / "AGENTS.md").write_text("<!-- agentkit:agents-section -->\ncustom\n", encoding="utf-8")
    code, output = doctor(tmp_path)
    assert code == 1
    assert "blocked" in output


def test_unknown_future_format_is_rejected_by_upgrade_and_doctor(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    config = tmp_path / "agentkit.yml"
    config.write_text(config.read_text(encoding="utf-8").replace("version: 1", "version: 99", 1), encoding="utf-8")
    before = _snapshot(tmp_path)

    code, output = upgrade_repo(tmp_path)
    doctor_code, doctor_output = doctor(tmp_path)

    assert code == 1 and doctor_code == 1
    assert "future repository format 99" in output
    assert "incompatible" in doctor_output
    assert _snapshot(tmp_path) == before


def test_task_state_and_receipts_remain_byte_identical(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    task = tmp_path / ".agentkit" / "tasks" / "current.json"
    receipt = tmp_path / ".agentkit" / "receipts" / "checks.json"
    task.parent.mkdir(parents=True)
    receipt.parent.mkdir(parents=True)
    task.write_text(json.dumps({"task_id": "current", "task": "active", "status": "open"}), encoding="utf-8")
    receipt.write_text('{"legacy": true}\n', encoding="utf-8")
    before = {task: task.read_bytes(), receipt: receipt.read_bytes()}

    assert upgrade_repo(tmp_path)[0] == 0

    assert {path: path.read_bytes() for path in before} == before


def test_cli_upgrade_dry_run_routes_and_exits_successfully(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_v1_repo(tmp_path)
    before = _snapshot(tmp_path)

    main(["--repo", str(tmp_path), "upgrade", "--dry-run"])

    assert "Repository Upgrade Plan" in capsys.readouterr().out
    assert _snapshot(tmp_path) == before


def test_cli_upgrade_conflict_exits_nonzero(tmp_path: Path) -> None:
    _write_v1_repo(tmp_path)
    (tmp_path / "AGENTS.md").write_text("<!-- agentkit:agents-section -->\ncustom\n", encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        main(["--repo", str(tmp_path), "upgrade"])

    assert exc.value.code == 1

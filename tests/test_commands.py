from pathlib import Path

from agentkit.commands import (
    close_task,
    check,
    docs_impact,
    doctor,
    generate_skill,
    init_repo,
    install_hooks,
    lint_architecture,
    orient,
    remind_task,
    review_guidance,
    start_task,
    status_task,
)
from agentkit.cli import _normalize_global_repo_arg
from agentkit.git import changed_paths, diff_fingerprint, git_path
from agentkit.watch import watch_task


def test_init_and_orient(tmp_path: Path) -> None:
    init_repo(tmp_path)
    output = orient(tmp_path, component_names=["core"], paths=[], task="")

    assert "Affected Components" in output
    assert "docs/design.md" in output


def test_init_creates_small_agentkit_agents_section(tmp_path: Path) -> None:
    init_repo(tmp_path)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "### AgentKit" in agents
    assert "keep agent-led changes tied to durable intent" in agents
    assert "agentkit start --task" in agents
    assert "Before changing code" not in agents


def test_init_appends_agentkit_section_to_existing_agents(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Existing\n\nKeep local conventions.\n", encoding="utf-8")

    init_repo(tmp_path)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Existing" in agents
    assert "### AgentKit" in agents
    assert agents.index("# Existing") < agents.index("### AgentKit")


def test_init_force_preserves_existing_agents_file(tmp_path: Path) -> None:
    (tmp_path / "AGENTS.md").write_text("# Existing\n\nKeep local conventions.\n", encoding="utf-8")

    init_repo(tmp_path, force=True)

    agents = (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert "# Existing" in agents
    assert "Keep local conventions." in agents
    assert "### AgentKit" in agents


def test_init_updates_existing_lowercase_agents_file(tmp_path: Path) -> None:
    (tmp_path / "agents.md").write_text("Existing notes.\n", encoding="utf-8")

    init_repo(tmp_path)

    agents = (tmp_path / "agents.md").read_text(encoding="utf-8")
    assert "Existing notes." in agents
    assert "### AgentKit" in agents


def test_doctor_reports_missing_readiness_items(tmp_path: Path) -> None:
    code, output = doctor(tmp_path)

    assert code == 1
    assert "needs_attention" in output
    assert "Missing AGENTS.md" in output
    assert "Missing agentkit.yml" in output


def test_doctor_reports_ready_initialized_repo(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    generate_skill(tmp_path)

    code, output = doctor(tmp_path)

    assert code == 0
    assert "ready" in output
    assert "AGENTS.md contains AgentKit entry guidance" in output


def test_doctor_respects_configured_doc_paths(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "product.md").write_text("# Product\n", encoding="utf-8")
    (tmp_path / "docs" / "process.md").write_text("# Process\n", encoding="utf-8")
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  root: docs
  design: docs/product.md
  workflow: docs/process.md
components:
  core:
    code:
      - src/**
    docs:
      - docs/product.md
layers: {}
skills:
  output: .codex/skills/agentkit/SKILL.md
""",
        encoding="utf-8",
    )
    generate_skill(tmp_path)

    code, output = doctor(tmp_path)

    assert code == 0
    assert "docs/product.md exists" in output
    assert "docs/process.md exists" in output


def test_start_task_writes_state_with_durable_sources(tmp_path: Path) -> None:
    init_repo(tmp_path)

    output = start_task(tmp_path, component_names=["core"], task="implement core flow")

    assert "Task Started" in output
    assert "Durable Intent Sources" in output
    assert "docs/design.md" in output
    state = tmp_path / ".agentkit" / "tasks" / "current.json"
    assert state.exists()
    assert '"status": "open"' in state.read_text(encoding="utf-8")


def test_start_task_records_focus_context(tmp_path: Path) -> None:
    import json

    init_repo(tmp_path)

    output = start_task(
        tmp_path,
        component_names=["core"],
        task="implement core flow",
        focus_notes=["Preserve the existing CLI flow"],
        focus_docs=["docs/workflow.md"],
    )

    state = json.loads((tmp_path / ".agentkit" / "tasks" / "current.json").read_text(encoding="utf-8"))
    assert "Focus Notes" in output
    assert "Preserve the existing CLI flow" in output
    assert state["focus_notes"] == ["Preserve the existing CLI flow"]
    assert state["focus_docs"] == ["docs/workflow.md"]


def test_start_task_uses_focus_doc_for_component_discovery(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "docs" / "components" / "cli").mkdir(parents=True)
    (tmp_path / "docs" / "components" / "cli" / "design.md").write_text("# CLI\n", encoding="utf-8")
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
  workflow: docs/workflow.md
components:
  cli:
    description: Command routing.
    code:
      - src/agentkit/cli.py
    docs:
      - docs/components/cli/design.md
layers: {}
review:
  require_for:
    - cli
""",
        encoding="utf-8",
    )

    output = start_task(
        tmp_path,
        task="refine wording",
        focus_docs=["docs/components/cli/design.md"],
    )

    assert "cli: Command routing." in output
    assert "Review Expected\nyes" in output


def test_close_task_reports_needs_work_for_open_changes(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")

    code, output = close_task(tmp_path)

    assert code == 1
    assert "needs_work" in output
    assert "Open Changes" in output


def test_close_task_allows_blocked_question(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])

    code, output = close_task(tmp_path, blocked_question="Which API shape should this use?")

    assert code == 0
    assert "blocked" in output
    assert "Which API shape" in output


def test_blocked_close_records_open_changes(tmp_path: Path) -> None:
    import json
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "notes.md").write_text("blocked detail\n", encoding="utf-8")

    code, output = close_task(tmp_path, blocked_question="Need product decision")

    state = json.loads((tmp_path / ".agentkit" / "tasks" / "current.json").read_text(encoding="utf-8"))
    assert code == 0
    assert "blocked" in output
    assert "notes.md" in state["open_changes"]


def test_close_task_requires_started_task_for_blocked_question(tmp_path: Path) -> None:
    code, output = close_task(tmp_path, blocked_question="Need human input")

    assert code == 1
    assert "Missing Task State" in output


def test_close_task_requires_started_task(tmp_path: Path) -> None:
    code, output = close_task(tmp_path)

    assert code == 1
    assert "Missing Task State" in output


def test_close_task_requires_check_receipt(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])

    code, output = close_task(tmp_path, skip_review_reason="low risk")

    assert code == 1
    assert "Missing Check Receipt" in output


def test_status_reports_missing_lifecycle_gates(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(
        tmp_path,
        component_names=["core"],
        task="implement core flow",
        focus_notes=["Keep CLI reminders concise"],
        focus_docs=["docs/workflow.md"],
    )

    output = status_task(tmp_path)

    assert "Lifecycle Status" in output
    assert "needs_work" in output
    assert "docs/workflow.md" in output
    assert "Keep CLI reminders concise" in output
    assert "Missing Gates" in output
    assert "Run `agentkit check`" in output


def test_remind_reports_next_action_from_lifecycle_state(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"], task="implement core flow")

    output = remind_task(tmp_path)

    assert "AgentKit Reminder" in output
    assert "Run `agentkit check`" in output
    assert "Run the review loop" in output


def test_check_includes_lifecycle_reminder_and_writes_receipt(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    start_task(tmp_path, component_names=["core"], task="implement core flow")

    code, output = check(tmp_path)

    assert code == 0
    assert "Lifecycle Reminder" in output
    assert "Run the review loop" in output
    assert "missing check receipt" not in output
    receipt = tmp_path / ".agentkit" / "receipts" / "checks" / f"{diff_fingerprint(tmp_path)}.json"
    assert receipt.exists()


def test_remind_stops_for_blocked_task(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    close_task(tmp_path, blocked_question="Need product decision")

    output = remind_task(tmp_path)

    assert "Task Blocked" in output
    assert "Need product decision" in output
    assert "No reminder will repeat" in output


def test_watch_once_reuses_reminder_output(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    outputs: list[str] = []

    code = watch_task(tmp_path, once=True, output=outputs.append)

    assert code == 0
    assert len(outputs) == 1
    assert "AgentKit Reminder" in outputs[0]


def test_watch_stops_for_blocked_task(tmp_path: Path) -> None:
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    close_task(tmp_path, blocked_question="Need product decision")
    outputs: list[str] = []

    code = watch_task(tmp_path, output=outputs.append)

    assert code == 0
    assert len(outputs) == 1
    assert "Task Blocked" in outputs[0]


def test_remind_is_quiet_without_open_task(tmp_path: Path) -> None:
    init_repo(tmp_path)

    output = remind_task(tmp_path)

    assert "No reminder needed" in output
    assert "No AgentKit task is open" in output


def test_watch_exits_without_open_task(tmp_path: Path) -> None:
    init_repo(tmp_path)
    outputs: list[str] = []

    code = watch_task(tmp_path, output=outputs.append)

    assert code == 0
    assert len(outputs) == 1
    assert "No AgentKit task is open" in outputs[0]


def test_blocked_task_reminds_when_diff_changes(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    init_repo(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "notes.md").write_text("first\n", encoding="utf-8")
    close_task(tmp_path, blocked_question="Need product decision")
    (tmp_path / "notes.md").write_text("second\n", encoding="utf-8")

    output = remind_task(tmp_path)

    assert "stale" in output
    assert "changed after it was blocked" in output


def test_close_task_requires_review_or_skip_for_review_expected(tmp_path: Path) -> None:
    from agentkit.commands import check

    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    start_task(tmp_path, component_names=["core"])
    check(tmp_path)

    code, output = close_task(tmp_path)

    assert code == 1
    assert "Missing Review Receipt" in output


def test_close_task_rejects_skip_reason_for_required_review(tmp_path: Path) -> None:
    from agentkit.commands import check

    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    start_task(tmp_path, component_names=["core"])
    check(tmp_path)

    code, output = close_task(tmp_path, skip_review_reason="low risk")

    assert code == 1
    assert "Missing Review Receipt" in output


def test_close_task_completes_after_check_and_review(tmp_path: Path) -> None:
    from agentkit.commands import check

    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    start_task(tmp_path, component_names=["core"])
    check(tmp_path)

    code, output = close_task(tmp_path, review_complete=True)

    assert code == 0
    assert "completed" in output


def test_close_task_rejects_clean_tree_receipt_from_previous_head(tmp_path: Path) -> None:
    import subprocess
    from agentkit.commands import check

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agentkit@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "AgentKit"], cwd=tmp_path, check=True)
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    check(tmp_path)
    start_task(tmp_path, component_names=["core"])
    (tmp_path / "src" / "example.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=tmp_path, check=True, capture_output=True)

    code, output = close_task(tmp_path, review_complete=True)

    assert code == 1
    assert "Missing Check Receipt" in output


def test_close_task_rejects_review_receipt_from_previous_head(tmp_path: Path) -> None:
    import subprocess
    from agentkit.commands import check

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agentkit@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "AgentKit"], cwd=tmp_path, check=True)
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=tmp_path, check=True, capture_output=True)
    start_task(tmp_path, component_names=["core"])
    check(tmp_path)
    close_task(tmp_path, review_complete=True)
    (tmp_path / "src" / "example.py").write_text("VALUE = 2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "change"], cwd=tmp_path, check=True, capture_output=True)
    check(tmp_path)

    code, output = close_task(tmp_path)

    assert code == 1
    assert "Missing Review Receipt" in output


def test_install_hooks_writes_git_pre_commit(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)

    output = install_hooks(tmp_path)

    hook = tmp_path / ".git" / "hooks" / "pre-commit"
    assert "Hooks Installed" in output
    assert hook.exists()
    assert "agentkit check" in hook.read_text(encoding="utf-8")


def test_install_hooks_uses_git_path_for_worktree(tmp_path: Path) -> None:
    import subprocess

    repo = tmp_path / "repo"
    worktree = tmp_path / "linked"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "agentkit@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "AgentKit"], cwd=repo, check=True)
    (repo / "README.md").write_text("# Repo\n", encoding="utf-8")
    subprocess.run(["git", "add", "README.md"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", "initial"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "worktree", "add", str(worktree)], cwd=repo, check=True, capture_output=True)

    install_hooks(worktree)

    hook = git_path(worktree, "hooks/pre-commit")
    assert hook.exists()
    assert "agentkit check" in hook.read_text(encoding="utf-8")


def test_generate_skill_includes_lifecycle_commands(tmp_path: Path) -> None:
    init_repo(tmp_path)

    generate_skill(tmp_path)

    skill = (tmp_path / ".codex" / "skills" / "agentkit" / "SKILL.md").read_text(encoding="utf-8")
    assert "Normal Operating Loop" in skill
    assert "ask the human" in skill
    assert "start` writes repository-local task state" in skill
    assert "architecture`, `data_model`, `public_api`" in skill
    assert "docs-only wording tasks" in skill
    assert "agentkit start" in skill
    assert "agentkit status" in skill
    assert "agentkit remind" in skill
    assert "review loop was completed" in skill
    assert "agentkit close" in skill


def test_orient_task_matching_ignores_common_words(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components:
  cli:
    description: command line interface and routing.
    code:
      - src/cli.py
    docs:
      - docs/components/cli/design.md
    keywords:
      - cli
  config:
    description: yaml configuration and schema.
    code:
      - src/config.py
    docs:
      - docs/components/config/design.md
    keywords:
      - config
layers: {}
""",
        encoding="utf-8",
    )

    output = orient(tmp_path, task="rename variable and update formatting")

    assert "Affected Components\n- none" in output


def test_docs_impact_uses_component_mapping(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")

    output = docs_impact(tmp_path, paths=["src/example.py"])

    assert "docs/design.md" in output
    assert "Unmapped Changed Paths" in output


def test_docs_impact_counts_related_docs_outside_docs_root(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "web").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "example.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "web" / "design.md").write_text("# Web\n", encoding="utf-8")
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  root: docs
  design: docs/design.md
components:
  frontend:
    code:
      - src/example.py
    docs:
      - web/design.md
layers: {}
""",
        encoding="utf-8",
    )

    output = docs_impact(tmp_path, paths=["src/example.py", "web/design.md"])

    assert "Docs Impact Assessment Needed\nNo related docs" in output


def test_lint_architecture_detects_reverse_import(tmp_path: Path) -> None:
    (tmp_path / "src" / "app" / "api").mkdir(parents=True)
    (tmp_path / "src" / "app" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "routes.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "model.py").write_text(
        "from app.api import routes\n",
        encoding="utf-8",
    )
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components: {}
layers:
  domain:
    paths:
      - src/app/domain/**
    may_import: []
  api:
    paths:
      - src/app/api/**
    may_import:
      - domain
""",
        encoding="utf-8",
    )

    code, output = lint_architecture(tmp_path)

    assert code == 1
    assert "domain" in output


def test_lint_architecture_detects_relative_reverse_import(tmp_path: Path) -> None:
    (tmp_path / "src" / "app" / "api").mkdir(parents=True)
    (tmp_path / "src" / "app" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "routes.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "model.py").write_text(
        "from ..api import routes\n",
        encoding="utf-8",
    )
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components: {}
layers:
  domain:
    paths:
      - src/app/domain/**
    may_import: []
  api:
    paths:
      - src/app/api/**
    may_import:
      - domain
""",
        encoding="utf-8",
    )

    code, output = lint_architecture(tmp_path)

    assert code == 1
    assert "app.api" in output


def test_lint_architecture_detects_package_alias_import(tmp_path: Path) -> None:
    (tmp_path / "src" / "app" / "api").mkdir(parents=True)
    (tmp_path / "src" / "app" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "app" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "src" / "app" / "api" / "routes.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "model.py").write_text(
        "from app import api\n",
        encoding="utf-8",
    )
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components: {}
layers:
  domain:
    paths:
      - src/app/domain/**
    may_import: []
  api:
    paths:
      - src/app/api/**
    may_import:
      - domain
""",
        encoding="utf-8",
    )

    code, output = lint_architecture(tmp_path)

    assert code == 1
    assert "app.api" in output


def test_lint_architecture_detects_namespace_package_alias_import(tmp_path: Path) -> None:
    (tmp_path / "src" / "app" / "api").mkdir(parents=True)
    (tmp_path / "src" / "app" / "domain").mkdir(parents=True)
    (tmp_path / "src" / "app" / "api" / "routes.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "src" / "app" / "domain" / "model.py").write_text(
        "from app import api\n",
        encoding="utf-8",
    )
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components: {}
layers:
  domain:
    paths:
      - src/app/domain/**
    may_import: []
  api:
    paths:
      - src/app/api/**
    may_import:
      - domain
""",
        encoding="utf-8",
    )

    code, output = lint_architecture(tmp_path)

    assert code == 1
    assert "app.api" in output or "app" in output


def test_review_guidance_uses_git_changed_paths(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "src").mkdir()
    (tmp_path / "docs" / "components" / "core").mkdir(parents=True)
    (tmp_path / "src" / "feature.py").write_text("VALUE = 1\n", encoding="utf-8")
    (tmp_path / "docs" / "design.md").write_text("# Design\n", encoding="utf-8")
    (tmp_path / "docs" / "components" / "core" / "design.md").write_text("# Core\n", encoding="utf-8")
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
components:
  core:
    description: Core behavior.
    code:
      - src/**
    docs:
      - docs/components/core/design.md
layers: {}
review:
  require_for:
    - core
""",
        encoding="utf-8",
    )

    output = review_guidance(tmp_path)

    assert "Review Expected\nyes" in output
    assert "docs/components/core/design.md" in output


def test_review_guidance_prefers_durable_intent_sources(tmp_path: Path) -> None:
    init_repo(tmp_path)
    (tmp_path / "docs" / "components" / "core").mkdir(parents=True)
    (tmp_path / "docs" / "components" / "core" / "design.md").write_text("# Core\n", encoding="utf-8")
    (tmp_path / "agentkit.yml").write_text(
        """
version: 1
docs:
  design: docs/design.md
  workflow: docs/workflow.md
components:
  core:
    description: Core behavior.
    code:
      - src/**
    docs:
      - docs/components/core/design.md
layers: {}
review:
  require_for:
    - core
""",
        encoding="utf-8",
    )

    output = review_guidance(tmp_path, component_names=["core"])

    assert "Durable Intent Sources" in output
    assert "docs/design.md" in output
    assert "docs/components/core/design.md" in output
    assert "Do not make an inline summary the source of truth" in output
    assert output.index("## Durable Intent Sources") < output.index("## Instruction For Implementing Agent")
    assert output.index("## Durable Intent Sources") < output.index("Do not make an inline summary")


def test_changed_paths_includes_untracked_files(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "new.md").write_text("# New\n", encoding="utf-8")

    assert "docs/new.md" in changed_paths(tmp_path)


def test_changed_paths_excludes_agentkit_runtime_state(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    (tmp_path / ".agentkit" / "tasks").mkdir(parents=True)
    (tmp_path / ".agentkit" / "tasks" / "current.json").write_text("{}", encoding="utf-8")

    assert changed_paths(tmp_path) == []


def test_diff_fingerprint_includes_untracked_file_content(tmp_path: Path) -> None:
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    file_path = tmp_path / "notes.md"
    file_path.write_text("one\n", encoding="utf-8")
    first = diff_fingerprint(tmp_path)
    file_path.write_text("two\n", encoding="utf-8")
    second = diff_fingerprint(tmp_path)

    assert first != second


def test_repo_arg_can_appear_after_subcommand() -> None:
    assert _normalize_global_repo_arg(["review-guidance", "--repo", "D:/repo"]) == [
        "--repo",
        "D:/repo",
        "review-guidance",
    ]

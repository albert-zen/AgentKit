from pathlib import Path

from agentkit.commands import docs_impact, init_repo, lint_architecture, orient, review_guidance
from agentkit.cli import _normalize_global_repo_arg
from agentkit.git import changed_paths


def test_init_and_orient(tmp_path: Path) -> None:
    init_repo(tmp_path)
    output = orient(tmp_path, component_names=["core"], paths=[], task="")

    assert "Affected Components" in output
    assert "docs/design.md" in output


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


def test_repo_arg_can_appear_after_subcommand() -> None:
    assert _normalize_global_repo_arg(["review-guidance", "--repo", "D:/repo"]) == [
        "--repo",
        "D:/repo",
        "review-guidance",
    ]

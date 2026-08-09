from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable

import yaml

from agentkit.artifacts import AGENTS_BLOCK_END, AGENTS_BLOCK_START
from agentkit.config import parse_config
from agentkit.fs import replace_bytes_atomic_preserving_mode
from agentkit.versions import LATEST_REPOSITORY_FORMAT


LEGACY_AGENT_MARKER = "<!-- agentkit:agents-section -->"

# Every entry is a byte-exact section shipped by an earlier AgentKit version.
# Recognition is content-based: location alone is never treated as ownership.
LEGACY_AGENT_SECTIONS = (
    """### AgentKit

<!-- agentkit:agents-section -->
This repository uses AgentKit to keep agent-led changes tied to durable intent, checks, review, and closeout. For implementation, documentation edits, hook/plugin updates, or any repository-changing task, start with `agentkit start --task "..."`, use `agentkit check` plus `agentkit status` or `agentkit remind` while working, and finish with `agentkit close`. For read-only exploration, codebase orientation, or answering questions without edits, do not create an AgentKit task unless the work becomes long-running or the human asks for lifecycle tracking. For the full operating guide, read the AgentKit plugin skill.
""",
    """### AgentKit

<!-- agentkit:agents-section -->
This repository uses AgentKit to keep substantial agent-led changes tied to durable intent, checks, review, and closeout. Use the full lifecycle for changes that affect architecture, public behavior, state or data models, security boundaries, cross-component workflows, hooks or plugins, or otherwise need durable design and review context. Small, self-contained, low-risk edits may skip the lifecycle when ownership is obvious and verification is focused; read-only work does not need a lifecycle task. If initially small work expands, run `agentkit start --task "..."` or resume the task before continuing. A repository may require a stricter policy. For the full operating guide, read the AgentKit plugin skill.
""",
)

PRESERVED_POLICY = (
    "components, docs, layers, review, maintainability",
    "rules, reminders, preset provenance, unknown fields, comments, ordering, and formatting",
    "task-state schema, active task context, and runtime receipts",
    "skill, plugin, hook, and non-managed repository content",
)


@dataclass(frozen=True)
class PlannedChange:
    path: Path
    original_bytes: bytes
    final_bytes: bytes
    ownership: str
    description: str


@dataclass(frozen=True)
class Conflict:
    path: Path
    reason: str
    next_action: str


@dataclass(frozen=True)
class MigrationPlan:
    repo: Path
    source_version: int | None
    target_version: int
    migration_ids: tuple[str, ...]
    changes: tuple[PlannedChange, ...]
    preserved_policy: tuple[str, ...]
    conflicts: tuple[Conflict, ...]
    validation: tuple[str, ...]
    next_action: str


def read_repository_format(repo: Path) -> int:
    path = repo / "agentkit.yml"
    if not path.exists():
        raise FileNotFoundError(f"AgentKit config not found: {path}")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"AgentKit config must be a mapping: {path}")
    version = raw.get("version", 1)
    if type(version) is not int or version < 1:
        raise ValueError("AgentKit repository format `version` must be a positive integer")
    return version


def plan_repository_upgrade(repo: Path) -> MigrationPlan:
    repo = repo.resolve()
    target = LATEST_REPOSITORY_FORMAT
    try:
        source = read_repository_format(repo)
    except Exception as exc:
        return _plan(
            repo,
            None,
            target,
            conflicts=(
                Conflict(
                    repo / "agentkit.yml",
                    f"repository format cannot be read safely: {exc}",
                    "Repair the configuration encoding and YAML syntax without changing policy, then retry dry-run.",
                ),
            ),
        )
    if source > target:
        return _plan(
            repo,
            source,
            target,
            conflicts=(
                Conflict(
                    repo / "agentkit.yml",
                    f"future repository format {source} is incompatible with this AgentKit installation",
                    "Install an AgentKit version that supports this repository format; do not downgrade it.",
                ),
            ),
        )
    config_path = repo / "agentkit.yml"
    config_conflicts = (
        (
            Conflict(
                config_path,
                "agentkit.yml is a symbolic link, so mixed-surface ownership cannot be proven",
                "Replace the link with a reviewed regular repository file before upgrading.",
            ),
        )
        if config_path.is_symlink()
        else ()
    )
    if source == target:
        artifact_conflicts = _validate_v2_agents_artifact(repo)
        return _plan(repo, source, target, conflicts=(*config_conflicts, *artifact_conflicts))
    if source != 1:
        return _plan(
            repo,
            source,
            target,
            conflicts=(
                Conflict(
                    repo / "agentkit.yml",
                    f"no sequential migration is installed for repository format {source}",
                    "Install a version of AgentKit containing the missing sequential migration.",
                ),
            ),
        )

    changes: list[PlannedChange] = []
    conflicts: list[Conflict] = list(config_conflicts)
    if not config_conflicts:
        config_change, planned_config_conflicts = _plan_config_v1_to_v2(repo / "agentkit.yml")
        if config_change:
            changes.append(config_change)
        conflicts.extend(planned_config_conflicts)
    agents_paths = _existing_agents_paths(repo)
    if len(agents_paths) > 1:
        conflicts.append(
            Conflict(
                repo,
                "both AGENTS.md and agents.md exist, so AgentKit instruction ownership is ambiguous",
                "Consolidate the repository's agent instructions into one reviewed file, then retry dry-run.",
            )
        )
    else:
        agents_change, agents_conflicts = _plan_agents_v1_to_v2(
            agents_paths[0] if agents_paths else repo / "AGENTS.md"
        )
        if agents_change:
            changes.append(agents_change)
        conflicts.extend(agents_conflicts)
    return _plan(
        repo,
        source,
        target,
        migration_ids=("repository-format-1-to-2",),
        changes=tuple(changes),
        conflicts=tuple(conflicts),
    )


def apply_migration_plan(
    plan: MigrationPlan,
    *,
    replace_file: Callable[[Path, bytes], None] | None = None,
    validate_repository: Callable[[Path], None] | None = None,
) -> tuple[str, ...]:
    if plan.conflicts:
        raise ValueError("Migration plan has conflicts; refusing all writes")
    if not plan.changes:
        return ()
    writer = replace_file or replace_bytes_atomic_preserving_mode
    attempted: list[PlannedChange] = []
    try:
        for change in plan.changes:
            if (
                change.path.is_symlink()
                or not change.path.exists()
                or change.path.read_bytes() != change.original_bytes
            ):
                raise ValueError(
                    f"Planned source changed after planning: {change.path}; refusing all writes"
                )
        for change in plan.changes:
            if (
                change.path.is_symlink()
                or not change.path.exists()
                or change.path.read_bytes() != change.original_bytes
            ):
                raise ValueError(
                    f"Planned source changed immediately before write: {change.path}; refusing to overwrite it"
                )
            attempted.append(change)
            writer(change.path, change.final_bytes)
        config_raw = yaml.safe_load((plan.repo / "agentkit.yml").read_text(encoding="utf-8")) or {}
        if not isinstance(config_raw, dict) or parse_config(config_raw).version != plan.target_version:
            raise ValueError("Post-write validation did not observe the target repository format")
        if _validate_v2_agents_artifact(plan.repo):
            raise ValueError("Post-write validation did not observe a valid managed agents block")
        if validate_repository is not None:
            validate_repository(plan.repo)
    except Exception as failure:
        rollback_errors: list[Exception] = []
        concurrent_paths: list[Path] = []
        for change in reversed(attempted):
            try:
                if change.path.is_symlink() or not change.path.exists():
                    concurrent_paths.append(change.path)
                    continue
                current = change.path.read_bytes()
                if current == change.original_bytes:
                    continue
                if current != change.final_bytes:
                    concurrent_paths.append(change.path)
                    continue
                writer(change.path, change.original_bytes)
            except Exception as exc:  # pragma: no cover - catastrophic storage failure
                rollback_errors.append(exc)
        if rollback_errors:
            raise RuntimeError("Migration failed and rollback could not restore every original file") from rollback_errors[0]
        if concurrent_paths:
            names = ", ".join(str(path) for path in concurrent_paths)
            raise RuntimeError(
                f"Migration failed; rollback preserved concurrent edits instead of overwriting them: {names}"
            ) from failure
        raise
    return tuple(change.path.relative_to(plan.repo).as_posix() for change in plan.changes)


def _plan(
    repo: Path,
    source: int | None,
    target: int,
    *,
    migration_ids: tuple[str, ...] = (),
    changes: tuple[PlannedChange, ...] = (),
    conflicts: tuple[Conflict, ...] = (),
) -> MigrationPlan:
    next_action = (
        "Resolve every conflict and run `agentkit upgrade --dry-run` again."
        if conflicts
        else "Run `agentkit upgrade` to apply this plan."
        if changes
        else "No upgrade action is required."
    )
    return MigrationPlan(
        repo=repo,
        source_version=source,
        target_version=target,
        migration_ids=migration_ids,
        changes=changes,
        preserved_policy=PRESERVED_POLICY,
        conflicts=conflicts,
        validation=(
            "proposed agentkit.yml parses as repository format 2",
            "AgentKit agents block is bounded and managed-artifact version 2",
            "planned bytes preserve every non-owned byte",
            "task state and receipts are outside this migration",
            "manifest, architecture, and failing maintainability checks run without receipts before and after apply",
        ),
        next_action=next_action,
    )


def _plan_config_v1_to_v2(path: Path) -> tuple[PlannedChange | None, tuple[Conflict, ...]]:
    if path.is_symlink():
        return None, (
            Conflict(path, "agentkit.yml is a symbolic link, so mixed-surface ownership cannot be proven", "Replace the link with a reviewed regular repository file before upgrading."),
        )
    original = path.read_bytes()
    try:
        source_text = original.decode("utf-8")
        node = yaml.compose(source_text)
        version_keys = (
            [key for key, _ in node.value if getattr(key, "value", None) == "version"]
            if isinstance(node, yaml.MappingNode)
            else []
        )
    except Exception as exc:
        return None, (
            Conflict(path, f"cannot inspect top-level YAML keys safely: {exc}", "Repair the v1 YAML syntax, then retry dry-run."),
        )
    if len(version_keys) != 1:
        return None, (
            Conflict(
                path,
                "cannot prove ownership because the YAML does not contain exactly one top-level `version` key",
                "Remove duplicate format keys without changing repository policy, then retry dry-run.",
            ),
        )
    matches = list(re.finditer(rb"(?m)^version(?P<space>[ \t]*):(?P<value_space>[ \t]*)1(?P<suffix>[ \t]*(?:#.*)?(?:\r?\n|$))", original))
    if len(matches) != 1:
        return None, (
            Conflict(
                path,
                "cannot identify exactly one plain top-level `version: 1` format marker without rewriting YAML",
                "Normalize only the top-level format marker to a plain `version: 1` scalar, preserving all policy content.",
            ),
        )
    match = matches[0]
    value_start = match.start() + match.group(0).find(b"1")
    final = original[:value_start] + b"2" + original[value_start + 1 :]
    try:
        raw = yaml.safe_load(final.decode("utf-8")) or {}
        if not isinstance(raw, dict):
            raise ValueError("configuration is not a mapping")
        parsed = parse_config(raw)
        if parsed.version != 2:
            raise ValueError("proposed configuration is not format 2")
    except Exception as exc:
        return None, (
            Conflict(
                path,
                f"proposed format marker edit does not produce a valid AgentKit config: {exc}",
                "Repair the existing v1 configuration without changing its policy, then retry dry-run.",
            ),
        )
    return (
        PlannedChange(path, original, final, "mixed: managed format marker", "advance repository format marker 1 -> 2"),
        (),
    )


def _plan_agents_v1_to_v2(path: Path) -> tuple[PlannedChange | None, tuple[Conflict, ...]]:
    if path.is_symlink():
        return None, (
            Conflict(path, "the AgentKit agents instruction file is a symbolic link, so mixed-surface ownership cannot be proven", "Replace the link with one reviewed regular instruction file before upgrading."),
        )
    if not path.exists():
        return None, (
            Conflict(path, "no AgentKit agents instruction file exists", "Restore the known v1 AgentKit section or adopt a reviewed bounded v2 block manually."),
        )
    original = path.read_bytes()
    try:
        text = original.decode("utf-8")
    except UnicodeDecodeError as exc:
        return None, (
            Conflict(path, f"agents instruction bytes are not valid UTF-8: {exc}", "Convert the file to reviewed UTF-8 text without changing its policy, then retry dry-run."),
        )
    managed_start_count = text.count("<!-- agentkit:agents-section")
    if (
        managed_start_count == 1
        and text.count(AGENTS_BLOCK_START) == 1
        and text.count(AGENTS_BLOCK_END) == 1
        and LEGACY_AGENT_MARKER not in text
    ):
        if text.index(AGENTS_BLOCK_START) < text.index(AGENTS_BLOCK_END):
            return None, ()
    if managed_start_count != 1:
        return None, (
            Conflict(path, "legacy AgentKit agents section boundary is ambiguous", "Keep one byte-exact shipped legacy section or migrate the customized section manually."),
        )
    marker_count = text.count(LEGACY_AGENT_MARKER)
    if marker_count != 1:
        return None, (
            Conflict(path, "legacy AgentKit agents section boundary is ambiguous", "Keep one byte-exact shipped legacy section or migrate the customized section manually."),
        )
    matches = [section for section in LEGACY_AGENT_SECTIONS if text.count(section) == 1]
    if len(matches) != 1:
        return None, (
            Conflict(path, "legacy AgentKit agents section is customized and ownership cannot be proven", "Review the local policy and replace it manually with a bounded version-2 AgentKit block."),
        )
    legacy = matches[0]
    bounded = legacy.replace(LEGACY_AGENT_MARKER, AGENTS_BLOCK_START, 1).rstrip("\n") + f"\n{AGENTS_BLOCK_END}\n"
    final_text = text.replace(legacy, bounded, 1)
    final = final_text.encode("utf-8")
    return PlannedChange(path, original, final, "mixed: known managed block", "bound and version the known legacy AgentKit agents section"), ()


def _validate_v2_agents_artifact(repo: Path) -> tuple[Conflict, ...]:
    paths = _existing_agents_paths(repo)
    if len(paths) > 1:
        return (
            Conflict(
                repo,
                "both AGENTS.md and agents.md exist, so AgentKit instruction ownership is ambiguous",
                "Consolidate the repository's agent instructions into one reviewed file.",
            ),
        )
    path = paths[0] if paths else repo / "AGENTS.md"
    if path.is_symlink():
        return (Conflict(path, "the AgentKit agents instruction file is a symbolic link, so mixed-surface ownership cannot be proven", "Replace the link with one reviewed regular instruction file."),)
    if not path.exists():
        return (Conflict(path, "format 2 requires a bounded AgentKit agents block", "Run `agentkit init` only after reviewing why the managed block is missing."),)
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        return (Conflict(path, f"agents instruction bytes are not valid UTF-8: {exc}", "Convert the file to reviewed UTF-8 text without changing its policy."),)
    if (
        text.count("<!-- agentkit:agents-section") != 1
        or text.count(AGENTS_BLOCK_START) != 1
        or text.count(AGENTS_BLOCK_END) != 1
        or LEGACY_AGENT_MARKER in text
    ):
        return (Conflict(path, "format 2 AgentKit agents block is missing or ambiguous", "Restore exactly one bounded managed-artifact version-2 block."),)
    if text.index(AGENTS_BLOCK_START) > text.index(AGENTS_BLOCK_END):
        return (Conflict(path, "format 2 AgentKit agents block markers are reversed", "Repair the managed block boundaries manually."),)
    return ()


def _existing_agents_paths(repo: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for name in ("AGENTS.md", "agents.md"):
        candidate = repo / name
        if candidate.exists() and not any(candidate.samefile(existing) for existing in paths):
            paths.append(candidate)
    return tuple(paths)

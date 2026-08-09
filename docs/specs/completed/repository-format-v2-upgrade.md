# Repository Format v2 Upgrade Implementation

Status: Completed

Authority: [ADR 0002](../../decisions/0002-repository-upgrade-preserves-user-intent.md),
[ADR 0001](../../decisions/0001-association-state-rule-core.md), and the
[core model](../../architecture/core-model.md).

## Intent And Invariant

Repository format v2 introduces an explicit bounded/versioned AgentKit block
in `AGENTS.md`. The migration changes only AgentKit-managed envelope structure:

```text
v1 managed envelope + repository-owned intent
  -> v2 managed envelope + byte-identical repository-owned intent
```

If ownership or losslessness cannot be proven, planning returns a conflict and
application performs zero writes.

## Independent Version Domains

- Package version: the installed Python distribution and CLI implementation.
- Repository format: top-level `agentkit.yml` `version`; latest supported is 2.
- Preset version: provenance for materialized policy such as `recommended-v1`.
- Task-state schema: `.agentkit/tasks/*.json`; remains schema v1.
- Managed-artifact version: bounded generated blocks; the AgentKit agents block
  introduced here is version 2.

Advancing one domain does not imply advancing another. In particular, format
v2 does not rewrite preset policy or task/evidence state.

## Migration 1 To 2

The ordered migration id is `repository-format-1-to-2`.

Planning reads all affected bytes before producing changes. It:

1. Locates exactly one top-level YAML `version: 1` scalar and changes only its
   scalar token to `2`.
2. Parses the proposed YAML with AgentKit to prove it remains a supported
   configuration. Comments, unknown fields, ordering, quoting, whitespace, and
   all policy values outside the scalar token remain byte-identical.
3. Locates `AGENTS.md` or `agents.md` and recognizes a shipped, byte-exact
   legacy AgentKit section. It replaces only that known byte sequence with the
   bounded version-2 block. Bytes before and after the recognized sequence are
   unchanged.
4. Conflicts on a customized legacy marker, ambiguous/multiple markers, a
   missing recognizable boundary, an already-bounded unsupported block, or
   distinct simultaneous `AGENTS.md` and `agents.md` instruction files.
5. Conflicts on a symlinked `agentkit.yml` or agents instruction file. The
   first migration does not replace a link or follow it to mutate a target.

New init preflights an existing marked agents file. It creates format 2 only
when it can create or preserve one complete bounded v2 block; legacy,
incomplete, or ambiguous markers stop init before any scaffold write.

No skill, plugin, hook, task-state, or receipt migration is required by format
v2. Their paths alone do not establish AgentKit ownership.

## Planning And Application

`MigrationPlan` contains source/target format, ordered migration ids,
`PlannedChange` final bytes, preserved policy categories, conflicts, and
validation/next-action text. Dry-run renders this plan and never invokes the
writer or repository checks that create receipts.

Application refuses any plan with conflicts. It verifies every source during
preflight and again immediately before that file's write. If a later file
changes after an earlier write, AgentKit restores only files it already wrote
and leaves the concurrent edit untouched. Each planned file is written to a
same-directory temporary file, fsynced, and atomically replaced. Original bytes
remain in memory until every replacement and post-write format validation has
succeeded. Any write or validation failure restores every file that AgentKit
attempted to change.

The replacement also preserves the original file mode. Before any write,
AgentKit runs manifest, architecture, and failing maintainability checks without
creating a lifecycle receipt. It repeats those deterministic checks after the
write as part of success validation; a failure rolls back the migration.

Already-current repositories return a successful empty plan. Unknown future
formats are incompatible and never downgraded.

## Command Behavior

- `agentkit init` creates format v2 and a bounded agents block directly.
- `agentkit init --preset ...` selects/materializes policy; it is not upgrade.
- `agentkit upgrade --dry-run` plans the latest supported repository format
  without writes.
- `agentkit upgrade` applies the same deterministic plan.
- `agentkit doctor` reports current/latest format and one of `up_to_date`,
  `upgrade_available`, or `blocked`.

Upgrade output names the source/target, migration ids, planned or changed
files, preserved policy, conflicts, validation, and next action.

## Validation Matrix

- pristine v1 init fixture: dry-run, apply, and idempotent repeat;
- custom YAML policy, budgets, unknown fields, comments, and formatting;
- known legacy agents section with byte-identical prefix/suffix;
- customized and ambiguous agents sections conflict with zero writes;
- simulated later-file I/O failure restores earlier writes;
- v2 init and doctor status;
- future format rejection;
- active/unversioned task state and receipts remain byte-identical;
- CLI argument routing/output and existing behavior regression.

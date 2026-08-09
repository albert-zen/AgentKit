# AgentKit Core Model

Status: Accepted implementation design

This document applies the decision in
[ADR 0001](../decisions/0001-association-state-rule-core.md) to the current
file-based Python implementation. The ADR is authoritative if this document
and the decision ever diverge.

## Evaluation Boundary

AgentKit evaluates repository work with one model:

```text
Evaluation = Rules(Associations, State)
```

- Associations select relevant repository knowledge: path-to-component,
  component-to-document, file-to-layer, and change-to-review relationships.
- State supplies persisted task facts, observed Git facts, asserted lifecycle
  facts, and version-bound evidence.
- Rules consume those inputs and return stable identifiers, outcomes, reasons,
  and next actions.

Commands may request an evaluation for a proposed transition, such as normal
completion or blocked handoff. They do not reproduce the transition policy.
Status and reminder rendering consume the same evaluation that close uses.

## Fixed System Invariants

The following behavior is owned by AgentKit and cannot be weakened by
repository configuration:

- evaluation is deterministic for the same associations and state;
- code-related evidence is bound to the current diff fingerprint;
- evidence for an older HEAD or diff never satisfies a current rule;
- persisted source facts and recomputable lifecycle status remain separate;
- task-context updates cannot write validation evidence or derived status;
- unknown presets, named rules, unsupported schema versions, and invalid rule
  options fail with an actionable error;
- completion and blocked handoff are explainable through named rule results;
- CLI, watcher, Git/Codex hooks, and future adapters do not own policy copies.

Task files retain a persisted transition marker for compatibility (`open`,
`completed`, or `blocked`). Readiness such as `needs_work` and
`ready_to_close` is always derived from the current facts and rule results.

## Repository-Configurable Policy

Within those invariants, a repository may configure:

- components, documents, code paths, layers, and other associations;
- whether a supported named rule is enabled and whether a supported failure is
  blocking or advisory;
- which configured components or change categories require review;
- whether an explicit low-risk review skip is permitted;
- which supported lifecycle nodes emit reminders;
- maintainability thresholds and other existing repository-owned checks;
- provenance for the versioned preset that materialized the policy.

Configuration is data, not executable rule code. The first implementation does
not accept arbitrary expressions, JSON patch, event sourcing, user Python, or a
workflow DSL.

## State Model

`.agentkit/tasks/current.json` stores a schema-versioned `TaskState`. Schema v1
contains task identity and transition facts, human-approved context, derived
association snapshots, and review acknowledgement fields. Existing unversioned
task JSON is interpreted as schema v1 and is written with `schema_version: 1`
the next time AgentKit changes it.

Task state and receipt writes use unique same-directory temporary files followed
by atomic replacement, so concurrent adapters cannot share or move each
other's temporary payload.

`agentkit start` keeps its compatibility behavior: it creates or resumes the
current lifecycle record from a fresh orientation. `agentkit update` is the
normal command for later context changes. It has domain operations only:

- set replaces `task` or `plan`;
- add inserts a focus note, focus document, or component without duplication;
- remove deletes the requested list value and succeeds when already absent.

Update changes only requested context fields. It does not reopen terminal
tasks, reset unrelated context, alter fingerprints, or create check/review
evidence.

Observed Git state is sampled at evaluation time. Check receipts and review
acknowledgements only apply when their fingerprint equals the current diff
fingerprint. This includes clean trees: a receipt from an earlier HEAD is stale.

## Initial Named Lifecycle Rules

The compatibility baseline is expressed with these finite rules:

- `working_tree_clean`: normal completion requires no open changed paths;
- `check_receipt_current`: normal completion requires a successful check
  receipt for the current diff fingerprint;
- `review_addressed`: when review applies, the current diff requires either a
  review acknowledgement or an explicitly permitted low-risk skip;
- `blocked_question_recorded`: blocked handoff requires a non-empty human
  question.

Each evaluation returns a `RuleResult` with a stable rule id, an outcome
(`pass`, `fail`, or `not_applicable`), a reason, an optional next action, and
whether failure blocks the requested transition. Additional compatibility
facts, such as a terminal task becoming stale after the diff changes, remain
derived lifecycle facts and are rendered beside rule results.

Docs impact is not modeled as an independently satisfied receipt in this
version. `agentkit check` reports docs impact, but the current implementation
does not have reliable state proving that a human or agent made and recorded a
semantic persistence decision. AgentKit must not claim that guarantee until a
future, separately designed evidence source exists.

## Recommended Preset

`agentkit init --preset recommended-v1` materializes the supported rule and
reminder configuration into `agentkit.yml` and records preset name/version
provenance. Runtime evaluation uses those checked-in values; upgrading the
AgentKit package does not replace them.

`agentkit init` without `--preset` remains compatible with the existing
unmaterialized configuration. When a rules section is absent, AgentKit applies
the existing lifecycle baseline in memory. A repository can later choose the
explicit preset through a reviewable configuration change.

Direct edits to materialized configuration are repository policy. Re-running
the same preset is idempotent and preserves explicit supported overrides.
Selecting an unknown preset or rule fails instead of silently falling back.
When preset provenance is present, every supported rule and reminder value must
be explicit; incomplete materialization is a configuration error.

Materialization preserves existing YAML text. A repository with no policy
sections receives one appended recommended block, leaving comments and
unrelated configuration byte-for-byte intact. Reapplying matching provenance
does not rewrite the file. Existing partial or conflicting policy sections are
rejected with a manual migration instruction instead of being parsed and
re-serialized destructively.

## Adapter Boundary

- `cli.py` parses and renders command results.
- `commands.py` coordinates repository reads/writes and invokes evaluation.
- `watch.py`, `codex.py`, and Git hooks sample or deliver evaluation output.
- task-state and receipt modules persist source facts/evidence.
- lifecycle rules evaluate associations and state once for all adapters.

Adapters may decide when and where to show an evaluation. They may not decide
which gates pass, reinterpret stale evidence, or persist a second lifecycle
conclusion.

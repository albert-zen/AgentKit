from __future__ import annotations

import yaml

from agentkit.policy import SUPPORTED_PRESETS


RECOMMENDED_V1 = "recommended-v1"
RECOMMENDED_V1_PROVENANCE = {
    "source": "agentkit",
    "name": RECOMMENDED_V1,
    "version": 1,
}
RECOMMENDED_V1_BLOCK = """preset:
  source: agentkit
  name: recommended-v1
  version: 1

rules:
  working_tree_clean:
    enabled: true
    severity: error
  check_receipt_current:
    enabled: true
    severity: error
  review_addressed:
    enabled: true
    severity: error
    allow_skip: true
  blocked_question_recorded:
    enabled: true
    severity: error

reminders:
  open_task: true
  ready_to_close: true
  stale_terminal: true
"""


def materialize_preset_text(existing_text: str, preset_name: str) -> str:
    if preset_name not in SUPPORTED_PRESETS:
        raise ValueError(f"Unknown AgentKit preset: {preset_name}")
    if preset_name != RECOMMENDED_V1:  # Defensive until another finite preset is added.
        raise ValueError(f"Unknown AgentKit preset: {preset_name}")

    raw = yaml.safe_load(existing_text) or {}
    if not isinstance(raw, dict):
        raise ValueError("AgentKit config must be a mapping before applying a preset")
    policy_keys = {"preset", "rules", "reminders"}
    present_policy_keys = policy_keys.intersection(raw)
    if not present_policy_keys:
        prefix = existing_text.rstrip()
        return f"{prefix}\n\n{RECOMMENDED_V1_BLOCK}" if prefix else RECOMMENDED_V1_BLOCK

    if raw.get("preset") == RECOMMENDED_V1_PROVENANCE:
        return existing_text

    present = ", ".join(sorted(present_policy_keys))
    raise ValueError(
        "Refusing to rewrite existing AgentKit policy text while applying recommended-v1: "
        f"found {present}. Preserve comments and repo-owned overrides by editing the preset/rules/reminders "
        "block explicitly, or remove those partial sections and rerun `agentkit init --preset recommended-v1`."
    )

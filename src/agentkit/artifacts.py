"""Stable contracts for versioned AgentKit-managed repository artifacts."""

from agentkit.versions import AGENTS_MANAGED_ARTIFACT_VERSION


AGENTS_BLOCK_START = (
    f"<!-- agentkit:agents-section version={AGENTS_MANAGED_ARTIFACT_VERSION} -->"
)
AGENTS_BLOCK_END = "<!-- /agentkit:agents-section -->"


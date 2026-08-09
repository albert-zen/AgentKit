from __future__ import annotations

import json
from pathlib import Path

from agentkit.fs import write_json_atomic


def receipt_path(repo: Path, kind: str, fingerprint: str) -> Path:
    return repo / ".agentkit" / "receipts" / kind / f"{fingerprint}.json"


def has_receipt(repo: Path, kind: str, fingerprint: str) -> bool:
    path = receipt_path(repo, kind, fingerprint)
    if not path.exists():
        return False
    try:
        content = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return bool(
        isinstance(content, dict)
        and content.get("fingerprint") == fingerprint
        and content.get("status") == "passed"
    )


def write_receipt(repo: Path, kind: str, fingerprint: str, payload: dict[str, str]) -> None:
    path = receipt_path(repo, kind, fingerprint)
    content = {**payload, "fingerprint": fingerprint}
    write_json_atomic(path, content)

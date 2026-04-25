from __future__ import annotations

import json
from pathlib import Path


def receipt_path(repo: Path, kind: str, fingerprint: str) -> Path:
    return repo / ".agentkit" / "receipts" / kind / f"{fingerprint}.json"


def has_receipt(repo: Path, kind: str, fingerprint: str) -> bool:
    return receipt_path(repo, kind, fingerprint).exists()


def write_receipt(repo: Path, kind: str, fingerprint: str, payload: dict[str, str]) -> None:
    path = receipt_path(repo, kind, fingerprint)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = {"fingerprint": fingerprint, **payload}
    path.write_text(json.dumps(content, indent=2), encoding="utf-8")

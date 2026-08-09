from __future__ import annotations

import json
import os
import tempfile
from fnmatch import fnmatch
from pathlib import Path
from typing import Any


def relpath(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def matches_any(path: str, patterns: tuple[str, ...] | list[str]) -> bool:
    normalized = path.replace("\\", "/")
    return any(_matches(normalized, pattern.replace("\\", "/")) for pattern in patterns)


def expand_patterns(repo: Path, patterns: tuple[str, ...] | list[str]) -> list[Path]:
    paths: list[Path] = []
    for pattern in patterns:
        normalized = pattern.replace("\\", "/")
        if any(char in normalized for char in "*?["):
            paths.extend(path for path in repo.glob(normalized) if path.is_file())
        else:
            path = repo / normalized
            if path.is_file():
                paths.append(path)
            elif path.is_dir():
                paths.extend(child for child in path.rglob("*") if child.is_file())
    return sorted(set(paths))


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            json.dump(payload, handle, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def replace_bytes_atomic_preserving_mode(path: Path, content: bytes) -> None:
    """Atomically replace an existing file without changing its permission mode."""
    if path.is_symlink():
        raise ValueError(f"Refusing to atomically replace symbolic link: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    original_mode = path.stat().st_mode & 0o7777
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary_path = Path(handle.name)
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary_path, original_mode)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _matches(path: str, pattern: str) -> bool:
    if fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    if "/**/" in pattern:
        prefix, suffix = pattern.split("/**/", 1)
        return path.startswith(prefix) and path.endswith(suffix)
    return False

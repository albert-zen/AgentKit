from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path


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


def _matches(path: str, pattern: str) -> bool:
    if fnmatch(path, pattern):
        return True
    if pattern.endswith("/**"):
        return path.startswith(pattern[:-3])
    if "/**/" in pattern:
        prefix, suffix = pattern.split("/**/", 1)
        return path.startswith(prefix) and path.endswith(suffix)
    return False

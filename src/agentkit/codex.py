from __future__ import annotations

import json
import os
import re
from pathlib import Path

from agentkit.lifecycle import render_reminder, sample_lifecycle
from agentkit.render import bullet, section


def install_codex_watchdog(
    repo: Path,
    *,
    scope: str = "repo",
    force: bool = False,
    log_path: str = ".agentkit/codex-stop-hook.log",
    codex_home: Path | None = None,
) -> str:
    if scope not in {"repo", "user"}:
        raise ValueError("scope must be 'repo' or 'user'")
    target_root = repo / ".codex" if scope == "repo" else _codex_home(codex_home)
    hooks_path = target_root / "hooks.json"
    config_path = target_root / "config.toml"
    target_root.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    command = codex_watchdog_command(log_path)
    _ensure_codex_watchdog_hook(hooks_path, command, force, created)
    _ensure_codex_hooks_feature(config_path, created)
    return "\n\n".join(
        [
            section("Codex Watchdog Installed", [scope]),
            section("Files", bullet(created or [str(hooks_path), str(config_path)])),
            section(
                "Next Verification",
                [
                    "Start a new Codex session in this repo, leave an AgentKit task open, and confirm the Stop hook writes the diagnostic log or continues the turn.",
                ],
            ),
        ]
    )


def codex_stop_hook(repo: Path, payload_text: str, log_path: str | None = None) -> tuple[int, str]:
    payload: dict[str, object] = {}
    if payload_text.strip():
        loaded = json.loads(payload_text)
        if isinstance(loaded, dict):
            payload = loaded
    hook_repo = repo_from_hook_payload(repo, payload)
    sample = sample_lifecycle(hook_repo)
    if log_path:
        append_codex_stop_log(hook_repo, log_path, sample.state)
    if sample.state not in {"needs_work", "ready_to_close"}:
        return (0, "")
    reminder = render_reminder(sample)
    reason = (
        f"{reminder}\n\n"
        "AgentKit has not reached a valid closeout state. Continue the task, complete the missing gates, "
        "or run `agentkit close --blocked-question \"...\"` if human input is required."
    )
    return (0, json.dumps({"decision": "block", "reason": reason}))


def has_codex_watchdog_hook(path: Path, expected_command: str | None = None) -> bool:
    if not path.exists():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    except json.JSONDecodeError:
        return False
    if not isinstance(data, dict):
        return False
    hooks = data.get("hooks")
    if not isinstance(hooks, dict):
        return False
    stop_hooks = hooks.get("Stop")
    if not isinstance(stop_hooks, list):
        return False
    if expected_command:
        return any(_is_expected_agentkit_codex_stop_group(group, expected_command) for group in stop_hooks)
    return any(_is_agentkit_codex_stop_group(group) for group in stop_hooks)


def codex_hooks_feature_enabled(path: Path) -> bool:
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    return bool(
        _features_section_has_codex_hooks(text, "true")
        or re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*true\s*$", text)
        or re.search(r"(?m)^\s*features\s*=\s*\{[^}\n]*\bcodex_hooks\s*=\s*true\b[^}\n]*\}\s*$", text)
    )


def codex_watchdog_command(log_path: str) -> str:
    return f'agentkit codex-stop-hook --log "{log_path}"'


def append_codex_stop_log(repo: Path, log_path: str, state: str) -> None:
    path = Path(log_path)
    if not path.is_absolute():
        path = repo / path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8") if not path.exists() else None
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"event": "Stop", "state": state}) + "\n")


def repo_from_hook_payload(default_repo: Path, payload: dict[str, object]) -> Path:
    cwd = payload.get("cwd")
    start = Path(str(cwd)).resolve() if cwd else default_repo
    for candidate in [start, *start.parents]:
        if (candidate / "agentkit.yml").exists():
            return candidate
    return default_repo


def _ensure_codex_watchdog_hook(path: Path, command: str, force: bool, created: list[str]) -> None:
    agentkit_group = {
        "hooks": [
            {
                "type": "command",
                "command": command,
                "timeout": 30,
                "statusMessage": "Checking AgentKit task closeout",
            }
        ]
    }
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8") or "{}")
    else:
        data = {}
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    hooks = data.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError(f"{path} hooks field must be a JSON object")
    stop_hooks = hooks.setdefault("Stop", [])
    if not isinstance(stop_hooks, list):
        raise ValueError(f"{path} hooks.Stop field must be a list")
    for index, group in enumerate(stop_hooks):
        if _is_agentkit_codex_stop_group(group):
            if force or not _is_expected_agentkit_codex_stop_group(group, command):
                stop_hooks[index] = agentkit_group
                path.write_text(json.dumps(data, indent=2), encoding="utf-8")
                created.append(path.as_posix())
            return
    stop_hooks.append(agentkit_group)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    created.append(path.as_posix())


def _ensure_codex_hooks_feature(path: Path, created: list[str]) -> None:
    if not path.exists():
        path.write_text("[features]\ncodex_hooks = true\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    text = path.read_text(encoding="utf-8")
    if _features_section_has_codex_hooks(text, "true") or re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*true\s*$", text):
        return
    if re.search(r"(?m)^\s*features\.codex_hooks\s*=\s*false\s*$", text):
        updated = re.sub(r"(?m)^(\s*features\.codex_hooks\s*=\s*)false\s*$", r"\1true", text, count=1)
        path.write_text(updated, encoding="utf-8")
        created.append(path.as_posix())
        return
    inline_features = re.search(r"(?m)^(\s*features\s*=\s*\{)([^}\n]*)(\}\s*)$", text)
    if inline_features:
        body = inline_features.group(2)
        if re.search(r"\bcodex_hooks\s*=\s*true\b", body):
            return
        if re.search(r"\bcodex_hooks\s*=\s*false\b", body):
            new_body = re.sub(r"\bcodex_hooks\s*=\s*false\b", "codex_hooks = true", body, count=1)
        else:
            prefix = f"{body.rstrip()}, " if body.strip() else ""
            new_body = f"{prefix}codex_hooks = true "
        updated = text[: inline_features.start(2)] + new_body + text[inline_features.end(2) :]
        path.write_text(updated, encoding="utf-8")
        created.append(path.as_posix())
        return
    lines = text.splitlines()
    bounds = _features_section_bounds(lines)
    if bounds:
        start, end = bounds
        for index in range(start, end):
            if re.match(r"^\s*codex_hooks\s*=\s*false\s*$", lines[index]):
                lines[index] = re.sub(r"^(\s*codex_hooks\s*=\s*)false\s*$", r"\1true", lines[index])
                path.write_text("\n".join(lines) + "\n", encoding="utf-8")
                created.append(path.as_posix())
                return
        lines.insert(start, "codex_hooks = true")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    if re.search(r"(?m)^\s*features\.", text):
        separator = "" if text.endswith("\n") or not text else "\n"
        path.write_text(f"{text}{separator}features.codex_hooks = true\n", encoding="utf-8")
        created.append(path.as_posix())
        return
    separator = "" if text.endswith("\n") or not text else "\n"
    path.write_text(f"{text}{separator}\n[features]\ncodex_hooks = true\n", encoding="utf-8")
    created.append(path.as_posix())


def _is_agentkit_codex_stop_group(group: object) -> bool:
    return isinstance(group, dict) and any(
        isinstance(item, dict) and str(item.get("command", "")).startswith("agentkit codex-stop-hook")
        for item in group.get("hooks", [])
    )


def _is_expected_agentkit_codex_stop_group(group: object, expected_command: str) -> bool:
    return isinstance(group, dict) and any(
        isinstance(item, dict) and item.get("command") == expected_command for item in group.get("hooks", [])
    )


def _features_section_has_codex_hooks(text: str, value: str) -> bool:
    lines = text.splitlines()
    bounds = _features_section_bounds(lines)
    if not bounds:
        return False
    start, end = bounds
    return any(re.match(rf"^\s*codex_hooks\s*=\s*{value}\s*$", line) for line in lines[start:end])


def _features_section_bounds(lines: list[str]) -> tuple[int, int] | None:
    start: int | None = None
    for index, line in enumerate(lines):
        if re.match(r"^\s*\[features]\s*$", line):
            start = index + 1
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start, len(lines)):
        if re.match(r"^\s*\[[^\]]+]\s*$", lines[index]):
            end = index
            break
    return start, end


def _codex_home(override: Path | None = None) -> Path:
    if override:
        return override
    env_home = os.environ.get("CODEX_HOME")
    if env_home:
        return Path(env_home)
    return Path.home() / ".codex"

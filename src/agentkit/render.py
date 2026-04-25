from __future__ import annotations


def section(title: str, lines: list[str] | tuple[str, ...]) -> str:
    body = "\n".join(lines) if lines else "(none)"
    return f"## {title}\n{body}"


def bullet(items: list[str] | tuple[str, ...]) -> list[str]:
    if not items:
        return ["- none"]
    return [f"- {item}" for item in items]


def code_block(text: str) -> str:
    return f"```text\n{text.rstrip()}\n```"

from __future__ import annotations

import ast
from pathlib import Path

from agentkit.config import MaintainabilityBudgetConfig, load_config
from agentkit.fs import expand_patterns, relpath
from agentkit.render import bullet, section


def lint_maintainability(repo: Path, *, verbose: bool = True) -> tuple[int, str]:
    config = load_config(repo)
    if not config.maintainability.budgets:
        if verbose:
            return (0, section("Maintainability Budgets", ["No budgets configured"]))
        return (0, "")

    findings: list[str] = []
    failures: list[str] = []
    ok: list[str] = []
    for budget in config.maintainability.budgets:
        files = expand_patterns(repo, budget.paths)
        if not files:
            message = f"{budget.name}: no files matched {list(budget.paths)}"
            findings.append(message)
            failures.append(message)
            continue
        for path in files:
            file_findings = _findings_for_file(path, repo, budget)
            if file_findings:
                findings.extend(file_findings)
                if budget.mode == "fail":
                    failures.extend(file_findings)
            else:
                ok.append(f"{relpath(path, repo)} within {budget.name}")

    if verbose:
        lines: list[str] = []
    elif findings:
        lines = [f"OK: {len(ok)} files within configured budgets"] if ok else []
    else:
        lines = [f"OK: {len(ok)} files within configured budgets"]

    if verbose and ok:
        lines.extend(bullet(ok))
    if findings:
        lines.extend(bullet(findings))
    return (1 if failures else 0, section("Maintainability Budgets", lines or ["OK"]))


def _findings_for_file(path: Path, repo: Path, budget: MaintainabilityBudgetConfig) -> list[str]:
    stats = _python_file_stats(path) if path.suffix == ".py" else _text_file_stats(path)
    label = relpath(path, repo)
    findings: list[str] = []
    checks = [
        ("lines", budget.max_lines),
        ("functions", budget.max_functions),
        ("classes", budget.max_classes),
    ]
    for name, limit in checks:
        if limit is None:
            continue
        actual = stats[name]
        if actual > limit:
            prefix = "FAIL" if budget.mode == "fail" else "WARN"
            message = f"{prefix} {label} has {actual} {name}; budget {budget.name} allows {limit}"
            if budget.guidance:
                message = f"{message}. {budget.guidance}"
            findings.append(message)
    return findings


def _text_file_stats(path: Path) -> dict[str, int]:
    return {"lines": len(path.read_text(encoding="utf-8").splitlines()), "functions": 0, "classes": 0}


def _python_file_stats(path: Path) -> dict[str, int]:
    text = path.read_text(encoding="utf-8")
    stats = {"lines": len(text.splitlines()), "functions": 0, "classes": 0}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return stats
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            stats["functions"] += 1
        elif isinstance(node, ast.ClassDef):
            stats["classes"] += 1
    return stats

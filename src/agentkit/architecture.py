from __future__ import annotations

import ast
from pathlib import Path

from agentkit.config import load_config
from agentkit.fs import expand_patterns, relpath
from agentkit.render import bullet, section


def lint_architecture(repo: Path) -> tuple[int, str]:
    config = load_config(repo)
    if not config.layers:
        return (0, section("Architecture Lint", ["No layers configured"]))

    files_by_layer: dict[str, list[Path]] = {
        name: [path for path in expand_patterns(repo, layer.paths) if path.suffix == ".py"]
        for name, layer in config.layers.items()
    }
    path_to_layer: dict[str, str] = {}
    for name, files in files_by_layer.items():
        for path in files:
            path_to_layer[relpath(path, repo)] = name

    module_to_layer = _python_module_index(path_to_layer)
    violations: list[str] = []
    for layer_name, files in files_by_layer.items():
        layer = config.layers[layer_name]
        allowed = set(layer.may_import) | {layer_name}
        for file_path in files:
            for imported in _imports_from(file_path, repo, module_to_layer):
                imported_layer = _resolve_imported_layer(imported, module_to_layer)
                if imported_layer and imported_layer not in allowed:
                    violations.append(
                        f"{relpath(file_path, repo)} ({layer_name}) imports {imported} ({imported_layer}), allowed: {sorted(allowed)}"
                    )
    return (1 if violations else 0, section("Architecture Lint", bullet(violations) if violations else ["OK"]))


def _imports_from(path: Path, repo: Path, module_to_layer: dict[str, str]) -> list[str]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            resolved = _resolve_import_from(path, repo, node.module, node.level)
            if resolved:
                imports.append(resolved)
                imports.extend(
                    f"{resolved}.{alias.name}"
                    for alias in node.names
                    if _resolve_imported_layer(f"{resolved}.{alias.name}", module_to_layer)
                )
    return imports


def _resolve_import_from(path: Path, repo: Path, module: str | None, level: int) -> str | None:
    if level == 0:
        return module
    current = _module_name_for_path(path, repo)
    if not current:
        return module
    package_parts = current.split(".")[:-1]
    if level > 1:
        package_parts = package_parts[: -(level - 1)]
    if module:
        package_parts.extend(module.split("."))
    return ".".join(part for part in package_parts if part)


def _python_module_index(path_to_layer: dict[str, str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for path, layer in path_to_layer.items():
        if not path.endswith(".py"):
            continue
        module_name = _module_name_for_relpath(path)
        if module_name:
            index[module_name] = layer
    return index


def _module_name_for_path(path: Path, repo: Path) -> str | None:
    return _module_name_for_relpath(relpath(path, repo))


def _module_name_for_relpath(path: str) -> str | None:
    if not path.endswith(".py"):
        return None
    without_suffix = path[:-3]
    parts = without_suffix.split("/")
    if "src" in parts:
        parts = parts[parts.index("src") + 1 :]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts) if parts else None


def _resolve_imported_layer(imported: str, module_to_layer: dict[str, str]) -> str | None:
    parts = imported.split(".")
    for end in range(len(parts), 0, -1):
        candidate = ".".join(parts[:end])
        if candidate in module_to_layer:
            return module_to_layer[candidate]
        dotted_prefix = f"{candidate}."
        descendant_layers = {
            layer
            for module, layer in module_to_layer.items()
            if module.startswith(dotted_prefix)
        }
        if len(descendant_layers) == 1:
            return next(iter(descendant_layers))
    return None

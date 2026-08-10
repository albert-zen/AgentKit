from pathlib import Path

from agentkit.fs import expand_patterns


def test_expand_patterns_trailing_double_star_recursively_includes_files(tmp_path: Path) -> None:
    source = tmp_path / "src"
    nested = source / "package"
    nested.mkdir(parents=True)
    top_level_file = source / "top.py"
    nested_file = nested / "module.py"
    top_level_file.write_text("", encoding="utf-8")
    nested_file.write_text("", encoding="utf-8")

    paths = expand_patterns(tmp_path, ["src/**"])

    assert paths == [nested_file, top_level_file]
    assert source not in paths
    assert nested not in paths


def test_expand_patterns_preserves_other_pattern_types(tmp_path: Path) -> None:
    source = tmp_path / "src"
    nested = source / "package"
    nested.mkdir(parents=True)
    top_level_file = source / "top.py"
    nested_file = nested / "module.py"
    ignored_file = nested / "notes.txt"
    top_level_file.write_text("", encoding="utf-8")
    nested_file.write_text("", encoding="utf-8")
    ignored_file.write_text("", encoding="utf-8")

    assert expand_patterns(tmp_path, ["src/*.py"]) == [top_level_file]
    assert expand_patterns(tmp_path, ["src/*/**"]) == [nested_file, ignored_file]
    assert expand_patterns(tmp_path, ["src/top.py"]) == [top_level_file]
    assert expand_patterns(tmp_path, ["src/package"]) == [nested_file, ignored_file]

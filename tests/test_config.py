from agentkit.config import parse_config


def test_parse_config_components_and_layers() -> None:
    config = parse_config(
        {
            "components": {
                "orchestration": {
                    "description": "Agent runs",
                    "code": ["src/example.py"],
                    "docs": ["docs/components/orchestration/design.md"],
                    "keywords": ["symphony"],
                }
            },
            "layers": {
                "api": {
                    "paths": ["src/api/**"],
                    "may_import": ["services"],
                }
            },
        }
    )

    assert config.components["orchestration"].keywords == ("symphony",)
    assert config.layers["api"].may_import == ("services",)


def test_parse_config_maintainability_budgets() -> None:
    config = parse_config(
        {
            "maintainability": {
                "budgets": [
                    {
                        "name": "commands",
                        "paths": ["src/agentkit/commands.py"],
                        "max_lines": 800,
                        "max_functions": 40,
                        "max_classes": 0,
                        "mode": "warn",
                        "guidance": "Split large command modules.",
                    }
                ]
            }
        }
    )

    budget = config.maintainability.budgets[0]
    assert budget.name == "commands"
    assert budget.paths == ("src/agentkit/commands.py",)
    assert budget.max_lines == 800
    assert budget.max_functions == 40
    assert budget.max_classes == 0
    assert budget.mode == "warn"
    assert budget.guidance == "Split large command modules."

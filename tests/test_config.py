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

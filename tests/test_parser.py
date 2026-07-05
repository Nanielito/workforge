from pathlib import Path

from workforge.config import load_workspace_config
from workforge.core.parser import parse_markdown_requirements


def test_parse_markdown_requirements() -> None:
    workspace = Path("workspaces/example")
    config = load_workspace_config(workspace)
    content = Path("workspaces/example/inbox/sample-requirements.md").read_text()

    requirements = parse_markdown_requirements(content, config)

    assert len(requirements) == 2
    assert requirements[0].title == "Clarify customer data collection"
    assert requirements[0].source == "shopify_review"
    assert requirements[0].priority == "high"
    assert requirements[0].labels == ["compliance", "required"]
    assert len(requirements[0].tasks) == 3

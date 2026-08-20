from workforge.config import WorkspaceConfig
from workforge.core.parser import parse_markdown_requirements


def test_parse_markdown_requirements() -> None:
    config = WorkspaceConfig(
        name="parser-test",
        default_provider="irrelevant-to-parser",
        defaults={
            "source": "manual",
            "namespace": "tests/parser",
        },
    )
    content = """\
# Requirements

## Add audit history

Source: product_review
Priority: high
Milestone: release-2
Labels: reporting, required

Record important changes so operators can review them later.

- Define the events to record
- Add the history view
- Validate retention behavior

## Use workspace defaults

This requirement intentionally omits metadata.
"""

    requirements = parse_markdown_requirements(content, config)

    assert len(requirements) == 2
    assert requirements[0].title == "Add audit history"
    assert requirements[0].source == "product_review"
    assert requirements[0].priority == "high"
    assert requirements[0].milestone == "release-2"
    assert requirements[0].labels == ["reporting", "required"]
    assert len(requirements[0].tasks) == 3
    assert requirements[1].source == "manual"
    assert requirements[1].namespace == "tests/parser"

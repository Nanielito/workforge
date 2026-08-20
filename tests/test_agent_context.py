from pathlib import Path

import pytest

from workforge.cli import (
    _build_agent_context,
    _build_item_context,
    _find_item_status,
    _find_created_item,
    _load_created_items,
    _item_context_path,
    _slugify,
)
from workforge.models import CreatedItem, ItemStatus, TaskStatus


def test_load_created_items_filters_by_provider(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    output_dir = workspace / "output" / "requirements"
    output_dir.mkdir(parents=True)
    (output_dir / "items.json").write_text(
        """
[
  {
    "provider": "provider-a",
    "id": "item-1",
    "url": "https://provider-a.example/items/1",
    "title": "Fix UI"
  },
  {
    "provider": "provider-b",
    "id": "item-2",
    "url": "https://provider-b.example/items/2",
    "title": "Fix UI"
  }
]
"""
    )

    items = _load_created_items(workspace, workspace / "inbox" / "requirements.md", "provider-a")

    assert len(items) == 1
    assert items[0].id == "item-1"
    assert items[0].title == "Fix UI"


def test_build_agent_context_groups_pending_and_completed_tasks() -> None:
    context = _build_agent_context(
        [
            ItemStatus(
                provider="test-provider",
                id="item-1",
                url="https://provider.example/items/1",
                title="Fix UI",
                tasks=[
                    TaskStatus(title="Add status panel", done=False),
                    TaskStatus(title="Remove empty template", done=True),
                ],
            )
        ]
    )

    assert "# WorkForge Agent Context" in context
    assert "## Fix UI" in context
    assert "Progress: 1/2 tasks complete" in context
    assert "### Pending Tasks\n\n- Add status panel" in context
    assert "### Completed Tasks\n\n- Remove empty template" in context


def test_find_created_item_matches_by_id_exact_title_or_unique_partial() -> None:
    items = [
        CreatedItem(provider="test-provider", id="item-1", title="Fix UI"),
        CreatedItem(provider="test-provider", id="item-2", title="Deploy app"),
    ]

    assert _find_created_item(items, "item-1").title == "Fix UI"
    assert _find_created_item(items, "Fix UI").id == "item-1"
    assert _find_created_item(items, "Deploy").id == "item-2"


def test_find_created_item_rejects_ambiguous_partial_matches() -> None:
    items = [
        CreatedItem(provider="test-provider", id="item-1", title="Fix UI"),
        CreatedItem(provider="test-provider", id="item-2", title="Fix template"),
    ]

    with pytest.raises(ValueError, match="Multiple items matched"):
        _find_created_item(items, "Fix")


def test_find_item_status_matches_by_id_exact_title_or_unique_partial() -> None:
    statuses = [
        ItemStatus(provider="test-provider", id="item-1", title="Fix UI"),
        ItemStatus(provider="test-provider", id="item-2", title="Deploy app"),
    ]

    assert _find_item_status(statuses, "item-1").title == "Fix UI"
    assert _find_item_status(statuses, "Fix UI").id == "item-1"
    assert _find_item_status(statuses, "Deploy").id == "item-2"


def test_build_item_context_focuses_on_one_item() -> None:
    context = _build_item_context(
        ItemStatus(
            provider="test-provider",
            id="item-1",
            url="https://provider.example/items/1",
            title="Fix UI",
            tasks=[
                TaskStatus(id="task-1", title="Add status panel", done=False),
                TaskStatus(id="task-2", title="Remove empty template", done=True),
            ],
        )
    )

    assert context.startswith("# Fix UI")
    assert "Progress: 1/2 tasks complete" in context
    assert "## Implementation Focus" in context
    assert "- Add status panel (`task-1`)" in context
    assert "- Remove empty template (`task-2`)" in context
    assert '--item "item-1"' in context


def test_slugify_and_item_context_path() -> None:
    status = ItemStatus(provider="test-provider", id="item-1", title="Improve post-install UI")

    assert _slugify(status.title) == "improve-post-install-ui"
    assert _item_context_path(Path("workspace"), Path("inbox/product-review.md"), status) == Path(
        "workspace/output/product-review/items/improve-post-install-ui.md"
    )

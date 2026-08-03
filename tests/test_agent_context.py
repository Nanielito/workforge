from pathlib import Path

import pytest

from workforge.cli import (
    _build_agent_context,
    _build_card_context,
    _card_context_path,
    _find_card_status,
    _find_created_item,
    _load_created_items,
    _slugify,
)
from workforge.models import CardStatus, CreatedItem, TaskStatus
from workforge.providers.trello import _find_task


def test_load_created_items_filters_by_provider(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    output_dir = workspace / "output" / "requirements"
    output_dir.mkdir(parents=True)
    (output_dir / "cards.json").write_text(
        """
[
  {
    "provider": "trello",
    "id": "card-1",
    "url": "https://trello.com/c/card-1",
    "title": "Fix UI"
  },
  {
    "provider": "github",
    "id": "issue-1",
    "url": "https://github.com/example/issues/1",
    "title": "Fix UI"
  }
]
"""
    )

    items = _load_created_items(workspace, workspace / "inbox" / "requirements.md", "trello")

    assert len(items) == 1
    assert items[0].id == "card-1"
    assert items[0].title == "Fix UI"


def test_build_agent_context_groups_pending_and_completed_tasks() -> None:
    context = _build_agent_context(
        [
            CardStatus(
                provider="trello",
                id="card-1",
                url="https://trello.com/c/card-1",
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
        CreatedItem(provider="trello", id="card-1", title="Fix UI"),
        CreatedItem(provider="trello", id="card-2", title="Deploy app"),
    ]

    assert _find_created_item(items, "card-1").title == "Fix UI"
    assert _find_created_item(items, "Fix UI").id == "card-1"
    assert _find_created_item(items, "Deploy").id == "card-2"


def test_find_created_item_rejects_ambiguous_partial_matches() -> None:
    items = [
        CreatedItem(provider="trello", id="card-1", title="Fix UI"),
        CreatedItem(provider="trello", id="card-2", title="Fix template"),
    ]

    with pytest.raises(ValueError, match="Multiple cards matched"):
        _find_created_item(items, "Fix")


def test_find_card_status_matches_by_id_exact_title_or_unique_partial() -> None:
    statuses = [
        CardStatus(provider="trello", id="card-1", title="Fix UI"),
        CardStatus(provider="trello", id="card-2", title="Deploy app"),
    ]

    assert _find_card_status(statuses, "card-1").title == "Fix UI"
    assert _find_card_status(statuses, "Fix UI").id == "card-1"
    assert _find_card_status(statuses, "Deploy").id == "card-2"


def test_build_card_context_focuses_on_one_card() -> None:
    context = _build_card_context(
        CardStatus(
            provider="trello",
            id="card-1",
            url="https://trello.com/c/card-1",
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
    assert '--card "card-1"' in context


def test_slugify_and_card_context_path() -> None:
    status = CardStatus(provider="trello", id="card-1", title="Fix UI operativa post-instalación")

    assert _slugify(status.title) == "fix-ui-operativa-post-instalacion"
    assert _card_context_path(Path("workspace"), Path("inbox/shopify-review.md"), status) == Path(
        "workspace/output/shopify-review/cards/fix-ui-operativa-post-instalacion.md"
    )


def test_find_task_matches_by_id_exact_title_or_unique_partial() -> None:
    checklists = [
        {
            "checkItems": [
                {"id": "task-1", "name": "Add status panel", "state": "incomplete"},
                {"id": "task-2", "name": "Remove empty template", "state": "complete"},
            ]
        }
    ]

    assert _find_task(checklists, "task-1")["name"] == "Add status panel"
    assert _find_task(checklists, "Remove empty template")["id"] == "task-2"
    assert _find_task(checklists, "status panel")["id"] == "task-1"

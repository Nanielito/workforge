from workforge.models import Requirement
from workforge.providers.trello import (
    TrelloProvider,
    _build_description,
    _card_matches_label,
    _find_task,
    _task_statuses_from_checklists,
)


def test_build_description_excludes_internal_metadata() -> None:
    requirement = Requirement(
        title="Fix UI",
        description="Create an operative post-install experience.",
        source="external_review",
        namespace="examples/sample",
        priority="high",
        labels=["product-review", "required"],
    )

    description = _build_description(requirement)

    assert description == "Create an operative post-install experience."
    assert "Source:" not in description
    assert "Namespace:" not in description
    assert "Priority:" not in description
    assert "Labels:" not in description


def test_label_ids_for_maps_requirement_labels_to_trello_label_ids() -> None:
    provider = TrelloProvider(
        config={
            "list_id": "list-123",
            "labels": {
                "product-review": "label-review",
                "required": "label-required",
            },
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
    )

    label_ids = provider._label_ids_for(["product-review", "missing", "required"])

    assert label_ids == ["label-review", "label-required"]


def test_configured_label_id_resolves_logical_label_names() -> None:
    provider = TrelloProvider(
        config={
            "list_id": "list-123",
            "labels": {
                "product": "label-product",
            },
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
    )

    assert provider._configured_label_id("product") == "label-product"
    assert provider._configured_label_id("missing") is None


def test_configured_list_id_resolves_logical_list_names() -> None:
    provider = TrelloProvider(
        config={
            "list_id": "list-todo",
            "lists": {
                "todo": "list-todo",
                "doing": "list-doing",
            },
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
    )

    assert provider._configured_list_id("doing") == "list-doing"
    assert provider._configured_list_id("missing") is None


def test_card_matches_label_by_id_labels_or_embedded_labels() -> None:
    assert _card_matches_label({"idLabels": ["label-product"]}, "label-product") is True
    assert _card_matches_label({"labels": [{"id": "label-product"}]}, "label-product") is True
    assert _card_matches_label({"idLabels": ["label-other"]}, "label-product") is False
    assert _card_matches_label({"idLabels": []}, None) is True


def test_task_statuses_from_checklists_preserves_check_item_ids() -> None:
    statuses = _task_statuses_from_checklists(
        [
            {
                "checkItems": [
                    {"id": "task-1", "name": "Add status panel", "state": "complete"},
                    {"id": "task-2", "name": "Remove empty template", "state": "incomplete"},
                ]
            }
        ]
    )

    assert statuses[0].id == "task-1"
    assert statuses[0].done is True
    assert statuses[1].id == "task-2"
    assert statuses[1].done is False


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

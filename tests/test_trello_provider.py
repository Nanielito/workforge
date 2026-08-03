from workforge.models import Requirement
from workforge.providers.trello import TrelloProvider, _build_description, _card_matches_label, _task_statuses_from_checklists


def test_build_description_excludes_internal_metadata() -> None:
    requirement = Requirement(
        title="Fix UI",
        description="Create an operative post-install experience.",
        source="shopify_app_review",
        namespace="linkealo/shopify",
        priority="high",
        labels=["shopify-review", "compliance"],
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
                "shopify-review": "label-shopify",
                "compliance": "label-compliance",
            },
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
    )

    label_ids = provider._label_ids_for(["shopify-review", "missing", "compliance"])

    assert label_ids == ["label-shopify", "label-compliance"]


def test_configured_label_id_resolves_logical_label_names() -> None:
    provider = TrelloProvider(
        config={
            "list_id": "list-123",
            "labels": {
                "shopify": "label-shopify",
            },
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
    )

    assert provider._configured_label_id("shopify") == "label-shopify"
    assert provider._configured_label_id("missing") is None


def test_card_matches_label_by_id_labels_or_embedded_labels() -> None:
    assert _card_matches_label({"idLabels": ["label-shopify"]}, "label-shopify") is True
    assert _card_matches_label({"labels": [{"id": "label-shopify"}]}, "label-shopify") is True
    assert _card_matches_label({"idLabels": ["label-other"]}, "label-shopify") is False
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

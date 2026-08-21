import asyncio
import json

import httpx

from workforge.models import CreatedItem, Requirement, WorkTask
from workforge.providers.trello import (
    TrelloProvider,
    _build_description,
    _card_matches_label,
    _card_matches_member,
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


def test_card_matches_member() -> None:
    assert _card_matches_member({"idMembers": ["member-1"]}, "member-1") is True
    assert _card_matches_member({"idMembers": ["member-2"]}, "member-1") is False
    assert _card_matches_member({}, None) is True


def test_update_requirement_tasks_replaces_managed_checklist_and_preserves_completion() -> None:
    checklists = [
        {
            "id": "tasks-old",
            "name": "Tasks",
            "checkItems": [
                {"id": "task-old", "name": "Existing", "state": "complete"},
                {"id": "task-removed", "name": "Removed", "state": "incomplete"},
            ],
        },
        {"id": "manual", "name": "Manual", "checkItems": []},
    ]
    created: list[dict[str, str]] = []

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET" and request.url.path == "/1/cards/card-1":
            return httpx.Response(200, json={"id": "card-1", "name": "Item", "closed": False})
        if request.method == "GET" and request.url.path == "/1/cards/card-1/checklists":
            if created:
                return httpx.Response(200, json=[checklists[1], {"id": "tasks-new", "name": "Tasks", "checkItems": created}])
            return httpx.Response(200, json=checklists)
        if request.method == "DELETE":
            assert request.url.path == "/1/checklists/tasks-old"
            return httpx.Response(200, json={})
        if request.url.path == "/1/cards/card-1/checklists":
            return httpx.Response(200, json={"id": "tasks-new"})
        if request.url.path == "/1/checklists/tasks-new/checkItems":
            name = json.loads(request.content)["name"]
            task = {"id": f"new-{len(created)}", "name": name, "state": "incomplete"}
            created.append(task)
            return httpx.Response(200, json=task)
        assert request.url.path == "/1/cards/card-1/checkItem/new-0"
        created[0]["state"] = "complete"
        return httpx.Response(200, json=created[0])

    provider = TrelloProvider(
        {"list_id": "list-1"},
        {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.update_requirement_tasks(
            CreatedItem(provider="trello", id="card-1", title="Item"),
            Requirement(title="Item", tasks=[WorkTask(title="Existing"), WorkTask(title="Added")]),
        )
    )

    assert [(task.title, task.done) for task in status.tasks] == [("Existing", True), ("Added", False)]


def test_discover_items_filters_member_list_and_label() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/1/lists/list-todo":
            return httpx.Response(200, json={"idBoard": "board-1"})
        if request.url.path == "/1/boards/board-1/members":
            return httpx.Response(
                200,
                json=[
                    {"id": "member-1", "username": "nanielito", "fullName": "Daniel Ramirez"},
                    {"id": "member-2", "username": "other", "fullName": "Other User"},
                ],
            )
        assert request.url.path == "/1/boards/board-1/cards"
        return httpx.Response(
            200,
            json=[
                {
                    "id": "card-1",
                    "name": "Matching card",
                    "closed": False,
                    "idLabels": ["label-feature"],
                    "idMembers": ["member-1"],
                    "idList": "list-doing",
                },
                {
                    "id": "card-2",
                    "name": "Other member",
                    "closed": False,
                    "idLabels": ["label-feature"],
                    "idMembers": ["member-2"],
                    "idList": "list-doing",
                },
                {
                    "id": "card-3",
                    "name": "Other list",
                    "closed": False,
                    "idLabels": ["label-feature"],
                    "idMembers": ["member-1"],
                    "idList": "list-todo",
                },
            ],
        )

    provider = TrelloProvider(
        config={
            "list_id": "list-todo",
            "lists": {"doing": "list-doing"},
            "labels": {"feature": "label-feature"},
        },
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    items = asyncio.run(provider.discover_items("feature", "@nanielito", "doing"))

    assert [item.id for item in items] == ["card-1"]


def test_claim_item_assigns_authenticated_member() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/1/lists/list-1":
            return httpx.Response(200, json={"idBoard": "board-1"})
        if request.url.path == "/1/members/me":
            return httpx.Response(200, json={"id": "member-1"})
        if request.url.path == "/1/cards/card-1/idMembers":
            assert request.url.params["value"] == "member-1"
            return httpx.Response(200, json={})
        if request.url.path == "/1/cards/card-1/checklists":
            return httpx.Response(200, json=[])
        return httpx.Response(200, json={"id": "card-1", "name": "Claim me", "closed": False})

    provider = TrelloProvider(
        {"list_id": "list-1"},
        {"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(provider.claim_item(CreatedItem(provider="trello", id="card-1", title="Claim me")))

    assert status.id == "card-1"


def test_discover_items_resolves_me() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/1/lists/list-todo":
            return httpx.Response(200, json={"idBoard": "board-1"})
        if request.url.path == "/1/members/me":
            return httpx.Response(200, json={"id": "member-1"})
        return httpx.Response(
            200,
            json=[
                {
                    "id": "card-1",
                    "name": "My card",
                    "closed": False,
                    "idMembers": ["member-1"],
                    "idList": "list-todo",
                }
            ],
        )

    provider = TrelloProvider(
        config={"list_id": "list-todo"},
        env={"TRELLO_API_KEY": "key", "TRELLO_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    items = asyncio.run(provider.discover_items(assignee_ref="@me"))

    assert [item.id for item in items] == ["card-1"]


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

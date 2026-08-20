import asyncio
import json

import httpx
import pytest

from workforge.models import CreatedItem, Requirement, WorkTask
from workforge.providers.github import GitHubProvider
from workforge.providers.registry import build_provider


def test_check_rejects_missing_configuration() -> None:
    result = asyncio.run(GitHubProvider({}, {}).check())

    assert result.ok is False
    assert "GITHUB_TOKEN" in result.message
    assert "providers.github.project_number" in result.message


def test_check_verifies_personal_repository_and_project() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer token"
        return httpx.Response(
            200,
            json={
                "data": {
                    "viewer": {"login": "owner"},
                    "user": {
                        "repository": {"nameWithOwner": "owner/workforge"},
                        "projectV2": {"title": "Workforge"},
                    },
                }
            },
        )

    provider = GitHubProvider(
        {"owner": "owner", "repository": "workforge", "project_number": 1},
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    result = asyncio.run(provider.check())

    assert result.ok is True
    assert result.message == "GitHub access verified for owner/workforge and project Workforge."


def test_registry_builds_github_provider() -> None:
    assert isinstance(build_provider("github", {}, {}), GitHubProvider)


def test_create_requirement_creates_issue_with_tasks_and_mapped_labels() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if request.url.path == "/repos/owner/workforge/issues":
            assert payload == {
                "title": "Add status view",
                "body": "Show current progress.\n\n## Tasks\n\n- [ ] Build view\n- [x] Add tests",
                "labels": ["enhancement"],
            }
            return httpx.Response(
                201,
                json={
                    "number": 12,
                    "node_id": "issue-node",
                    "html_url": "https://github.com/owner/workforge/issues/12",
                    "title": "Add status view",
                },
            )

        assert request.url.path == "/graphql"
        if "addProjectV2ItemById" in payload["query"]:
            assert payload["variables"] == {"project": "project-node", "content": "issue-node"}
            return httpx.Response(200, json={"data": {"addProjectV2ItemById": {"item": {"id": "item-node"}}}})

        assert payload["variables"] == {"owner": "owner", "project": 1}
        return httpx.Response(200, json={"data": {"user": {"projectV2": {"id": "project-node"}}}})

    provider = GitHubProvider(
        {
            "owner": "owner",
            "repository": "workforge",
            "project_number": 1,
            "labels": {"feature": "enhancement"},
        },
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )
    requirement = Requirement(
        title="Add status view",
        description="Show current progress.",
        labels=["feature", "unmapped"],
        tasks=[WorkTask(title="Build view"), WorkTask(title="Add tests", done=True)],
    )

    item = asyncio.run(provider.create_requirement(requirement))

    assert item.id == "12"
    assert item.url == "https://github.com/owner/workforge/issues/12"


def test_create_requirement_reports_issue_when_project_insertion_fails() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content)
        if request.url.path == "/repos/owner/workforge/issues":
            return httpx.Response(
                201,
                json={
                    "number": 12,
                    "node_id": "issue-node",
                    "html_url": "https://github.com/owner/workforge/issues/12",
                    "title": "Add status view",
                },
            )
        if "addProjectV2ItemById" in payload["query"]:
            return httpx.Response(200, json={"errors": [{"message": "Project write denied"}]})
        return httpx.Response(200, json={"data": {"user": {"projectV2": {"id": "project-node"}}}})

    provider = GitHubProvider(
        {"owner": "owner", "repository": "workforge", "project_number": 1},
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    with pytest.raises(RuntimeError, match=r"Issue created at https://github.com/owner/workforge/issues/12"):
        asyncio.run(provider.create_requirement(Requirement(title="Add status view")))


def test_get_item_status_reads_issue_and_managed_tasks() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/workforge/issues/12"
        return httpx.Response(
            200,
            json={
                "number": 12,
                "html_url": "https://github.com/owner/workforge/issues/12",
                "title": "Add status view",
                "state": "closed",
                "body": (
                    "- [x] Unrelated checkbox\n\n"
                    "## Tasks\n\n"
                    "- [ ] Build view\n"
                    "- [x] Add tests\n\n"
                    "## Notes\n\n"
                    "- [ ] Another unrelated checkbox"
                ),
            },
        )

    provider = GitHubProvider(
        {"owner": "owner", "repository": "workforge", "project_number": 1},
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.get_item_status(CreatedItem(provider="github", id="12", title="Fallback title"))
    )

    assert status.closed is True
    assert [(task.id, task.title, task.done) for task in status.tasks] == [
        ("task-1", "Build view", False),
        ("task-2", "Add tests", True),
    ]


def test_complete_task_updates_only_the_selected_managed_checkbox() -> None:
    original_body = "- [ ] Unrelated\n\n## Tasks\n\n- [ ] Build view\n- [ ] Add tests\n"
    updated_body = "- [ ] Unrelated\n\n## Tasks\n\n- [x] Build view\n- [ ] Add tests\n"

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/owner/workforge/issues/12"
        if request.method == "PATCH":
            assert json.loads(request.content) == {"body": updated_body}
            body = updated_body
        else:
            body = original_body
        return httpx.Response(
            200,
            json={
                "number": 12,
                "html_url": "https://github.com/owner/workforge/issues/12",
                "title": "Add status view",
                "state": "open",
                "body": body,
            },
        )

    provider = GitHubProvider(
        {"owner": "owner", "repository": "workforge", "project_number": 1},
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.complete_task(
            CreatedItem(provider="github", id="12", title="Add status view"),
            "task-1",
        )
    )

    assert [task.done for task in status.tasks] == [True, False]


def test_move_item_updates_project_status_from_configured_alias() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "number": 12,
                    "html_url": "https://github.com/owner/workforge/issues/12",
                    "title": "Add status view",
                    "state": "open",
                    "body": "",
                },
            )

        payload = json.loads(request.content)
        if "updateProjectV2ItemFieldValue" in payload["query"]:
            assert payload["variables"] == {
                "project": "project-node",
                "item": "project-item-node",
                "field": "status-field-node",
                "option": "done-option",
            }
            return httpx.Response(200, json={"data": {"updateProjectV2ItemFieldValue": {"projectV2Item": {"id": "project-item-node"}}}})

        assert payload["variables"] == {
            "owner": "owner",
            "repository": "workforge",
            "project": 1,
            "issue": 12,
        }
        return httpx.Response(
            200,
            json={
                "data": {
                    "user": {
                        "projectV2": {
                            "id": "project-node",
                            "fields": {
                                "nodes": [
                                    {
                                        "id": "status-field-node",
                                        "name": "Status",
                                        "options": [
                                            {"id": "todo-option", "name": "Todo"},
                                            {"id": "done-option", "name": "Done"},
                                        ],
                                    }
                                ]
                            },
                        }
                    },
                    "repository": {
                        "issue": {
                            "projectItems": {
                                "nodes": [
                                    {"id": "project-item-node", "project": {"id": "project-node"}}
                                ]
                            }
                        }
                    },
                }
            },
        )

    provider = GitHubProvider(
        {
            "owner": "owner",
            "repository": "workforge",
            "project_number": 1,
            "status": {"field": "Status", "values": {"done": "Done"}},
        },
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.move_item(CreatedItem(provider="github", id="12", title="Add status view"), "done")
    )

    assert status.id == "12"


def test_discover_items_paginates_and_filters_repository_state_and_label() -> None:
    def issue(number: int, repository: str = "owner/workforge", state: str = "OPEN") -> dict[str, object]:
        return {
            "content": {
                "number": number,
                "title": f"Issue {number}",
                "url": f"https://github.com/{repository}/issues/{number}",
                "state": state,
                "repository": {"nameWithOwner": repository},
                "labels": {"nodes": [{"id": "label-node", "name": "enhancement"}]},
            }
        }

    def respond(request: httpx.Request) -> httpx.Response:
        variables = json.loads(request.content)["variables"]
        if variables["cursor"] is None:
            nodes = [issue(1), issue(2, repository="owner/other")]
            page_info = {"hasNextPage": True, "endCursor": "next-page"}
        else:
            assert variables["cursor"] == "next-page"
            nodes = [issue(3), issue(4, state="CLOSED")]
            page_info = {"hasNextPage": False, "endCursor": None}
        return httpx.Response(
            200,
            json={
                "data": {
                    "user": {
                        "projectV2": {
                            "items": {"nodes": nodes, "pageInfo": page_info}
                        }
                    }
                }
            },
        )

    provider = GitHubProvider(
        {
            "owner": "owner",
            "repository": "workforge",
            "project_number": 1,
            "labels": {"feature": "enhancement"},
        },
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    items = asyncio.run(provider.discover_items("feature"))

    assert [item.id for item in items] == ["1", "3"]


def test_comment_item_adds_issue_comment_and_returns_status() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            assert request.url.path == "/repos/owner/workforge/issues/12/comments"
            assert json.loads(request.content) == {"body": "Implementation complete."}
            return httpx.Response(201, json={"id": 1})
        return httpx.Response(
            200,
            json={
                "number": 12,
                "html_url": "https://github.com/owner/workforge/issues/12",
                "title": "Add status view",
                "state": "open",
                "body": "",
            },
        )

    provider = GitHubProvider(
        {"owner": "owner", "repository": "workforge", "project_number": 1},
        {"GITHUB_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.comment_item(
            CreatedItem(provider="github", id="12", title="Add status view"),
            "Implementation complete.",
        )
    )

    assert status.id == "12"

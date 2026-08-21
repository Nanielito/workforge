import asyncio
import json

import httpx
import pytest

from workforge.models import CreatedItem, Requirement, WorkTask
from workforge.providers.jira import JiraProvider, _find_adf_task, _sync_adf_tasks, _task_statuses_from_adf
from workforge.providers.registry import build_provider


def test_check_rejects_missing_or_invalid_configuration() -> None:
    missing = asyncio.run(JiraProvider({}, {}).check())
    invalid_url = asyncio.run(
        JiraProvider(
            {"site_url": "http://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
            {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        ).check()
    )

    assert missing.ok is False
    assert "JIRA_EMAIL" in missing.message
    assert "providers.jira.issue_type" in missing.message
    assert invalid_url.message == "providers.jira.site_url must be an HTTPS URL."


def test_check_verifies_user_and_project() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"].startswith("Basic ")
        if request.url.path == "/rest/api/3/myself":
            return httpx.Response(200, json={"displayName": "Daniel"})
        assert request.url.path == "/rest/api/3/project/WF"
        return httpx.Response(200, json={"key": "WF"})

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    result = asyncio.run(provider.check())

    assert result.ok is True
    assert result.message == "Jira access verified for Daniel and project WF."


def test_check_redacts_credentials_from_errors() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("token for user@example.com failed", request=request)

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    result = asyncio.run(provider.check())

    assert result.ok is False
    assert result.message == "Jira request failed: [REDACTED] for [REDACTED] failed"


def test_check_includes_jira_error_details_and_redacts_credentials() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            401,
            json={"errorMessages": ["Token token rejected"], "errors": {"email": "user@example.com denied"}},
        )

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    result = asyncio.run(provider.check())

    assert result.ok is False
    assert "Token [REDACTED] rejected" in result.message
    assert "[REDACTED] denied" in result.message


def test_registry_builds_jira_provider() -> None:
    assert isinstance(build_provider("jira", {}, {}), JiraProvider)


def test_sync_adf_tasks_preserves_completion_and_unmanaged_content() -> None:
    description = {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Keep this."}]},
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Tasks"}]},
            {
                "type": "taskList",
                "attrs": {"localId": "workforge-tasks"},
                "content": [
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "old-1", "state": "DONE"},
                        "content": [{"type": "text", "text": "Existing"}],
                    }
                ],
            },
        ],
    }

    updated = _sync_adf_tasks(
        description,
        Requirement(title="Item", tasks=[WorkTask(title="Existing"), WorkTask(title="Added")]),
    )

    assert updated["content"][0] == description["content"][0]
    assert [task.model_dump() for task in _task_statuses_from_adf(updated)] == [
        {"id": "workforge-task-1", "title": "Existing", "done": True},
        {"id": "workforge-task-2", "title": "Added", "done": False},
    ]


def test_create_requirement_creates_issue_with_adf_and_mappings() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/api/3/issue"
        fields = json.loads(request.content)["fields"]
        assert fields["project"] == {"key": "WF"}
        assert fields["issuetype"] == {"name": "Task"}
        assert fields["summary"] == "Add Jira support"
        assert fields["labels"] == ["enhancement"]
        assert fields["fixVersions"] == [{"id": "10001"}]
        assert fields["description"]["content"] == [
            {"type": "paragraph", "content": [{"type": "text", "text": "Create issues."}]},
            {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Tasks"}]},
            {
                "type": "taskList",
                "attrs": {"localId": "workforge-tasks"},
                "content": [
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "workforge-task-1", "state": "TODO"},
                        "content": [{"type": "text", "text": "Send request"}],
                    },
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "workforge-task-2", "state": "DONE"},
                        "content": [{"type": "text", "text": "Add test"}],
                    },
                ],
            },
        ]
        return httpx.Response(201, json={"key": "WF-12"})

    provider = JiraProvider(
        {
            "site_url": "https://example.atlassian.net",
            "project_key": "WF",
            "issue_type": "Task",
            "labels": {"feature": "enhancement"},
            "versions": {"v2": "10001"},
        },
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )
    requirement = Requirement(
        title="Add Jira support",
        description="Create issues.",
        labels=["feature", "missing"],
        milestone="v2",
        tasks=[WorkTask(title="Send request"), WorkTask(title="Add test", done=True)],
    )

    created = asyncio.run(provider.create_requirement(requirement))

    assert created.id == "WF-12"
    assert created.url == "https://example.atlassian.net/browse/WF-12"


def test_create_requirement_rejects_unconfigured_version() -> None:
    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
    )

    with pytest.raises(ValueError, match="Jira version is not configured: missing"):
        asyncio.run(provider.create_requirement(Requirement(title="Test", milestone="missing")))


def _issue_description() -> dict:
    return {
        "type": "doc",
        "version": 1,
        "content": [
            {"type": "paragraph", "content": [{"type": "text", "text": "Keep this."}]},
            {
                "type": "taskList",
                "attrs": {"localId": "other-tasks"},
                "content": [
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "other-1", "state": "TODO"},
                        "content": [{"type": "text", "text": "Ignore this"}],
                    }
                ],
            },
            {
                "type": "taskList",
                "attrs": {"localId": "workforge-tasks"},
                "content": [
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "workforge-task-1", "state": "TODO"},
                        "content": [{"type": "text", "text": "Build parser"}],
                    },
                    {
                        "type": "taskItem",
                        "attrs": {"localId": "workforge-task-2", "state": "DONE"},
                        "content": [{"type": "text", "text": "Add tests"}],
                    },
                ],
            },
        ],
    }


def test_task_statuses_only_read_managed_adf_tasks() -> None:
    tasks = _task_statuses_from_adf(_issue_description())

    assert [(task.id, task.title, task.done) for task in tasks] == [
        ("workforge-task-1", "Build parser", False),
        ("workforge-task-2", "Add tests", True),
    ]


def test_find_adf_task_supports_id_exact_title_and_unique_substring() -> None:
    description = _issue_description()

    assert _find_adf_task(description, "workforge-task-1")["attrs"]["localId"] == "workforge-task-1"
    assert _find_adf_task(description, "Add tests")["attrs"]["localId"] == "workforge-task-2"
    assert _find_adf_task(description, "parser")["attrs"]["localId"] == "workforge-task-1"
    with pytest.raises(ValueError, match="Multiple tasks matched"):
        _find_adf_task(description, "a")
    with pytest.raises(ValueError, match="Task not found"):
        _find_adf_task({"type": "doc", "version": 1, "content": []}, "missing")


def test_get_item_status_reads_jira_status_and_tasks() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rest/api/3/issue/WF-12"
        assert request.url.params["fields"] == "summary,status,description"
        return httpx.Response(
            200,
            json={
                "key": "WF-12",
                "fields": {
                    "summary": "Jira item",
                    "status": {"statusCategory": {"key": "done"}},
                    "description": _issue_description(),
                },
            },
        )

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(provider.get_item_status(CreatedItem(provider="jira", id="WF-12", title="Fallback")))

    assert status.title == "Jira item"
    assert status.closed is True
    assert status.completed_tasks == 1


def test_complete_task_updates_only_selected_managed_task() -> None:
    original = _issue_description()

    def respond(request: httpx.Request) -> httpx.Response:
        if request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "key": "WF-12",
                    "fields": {
                        "summary": "Jira item",
                        "status": {"statusCategory": {"key": "indeterminate"}},
                        "description": original,
                    },
                },
            )
        updated = json.loads(request.content)["fields"]["description"]
        assert updated["content"][0]["content"][0]["text"] == "Keep this."
        assert updated["content"][1]["content"][0]["attrs"]["state"] == "TODO"
        assert updated["content"][2]["content"][0]["attrs"]["state"] == "DONE"
        assert updated["content"][2]["content"][1]["attrs"]["state"] == "DONE"
        return httpx.Response(204)

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.complete_task(CreatedItem(provider="jira", id="WF-12", title="Fallback"), "parser")
    )

    assert status.completed_tasks == 2


def _jira_issue(status_key: str = "indeterminate") -> dict:
    return {
        "key": "WF-12",
        "fields": {
            "summary": "Jira item",
            "status": {"statusCategory": {"key": status_key}},
            "description": _issue_description(),
        },
    }


def test_comment_item_adds_adf_comment() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/comment"):
            assert json.loads(request.content) == {
                "body": {
                    "type": "doc",
                    "version": 1,
                    "content": [{"type": "paragraph", "content": [{"type": "text", "text": "Ready for review"}]}],
                }
            }
            return httpx.Response(201, json={"id": "10001"})
        return httpx.Response(200, json=_jira_issue())

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(
        provider.comment_item(CreatedItem(provider="jira", id="WF-12", title="Fallback"), "Ready for review")
    )

    assert status.id == "WF-12"
    with pytest.raises(ValueError, match="Comment text cannot be empty"):
        asyncio.run(provider.comment_item(CreatedItem(provider="jira", id="WF-12", title="Fallback"), " "))


def test_move_item_resolves_alias_to_transition_destination() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/transitions") and request.method == "GET":
            return httpx.Response(
                200,
                json={
                    "transitions": [
                        {"id": "21", "name": "Start Progress", "to": {"name": "In Progress"}},
                        {"id": "31", "name": "Finish", "to": {"name": "Done"}},
                    ]
                },
            )
        if request.url.path.endswith("/transitions"):
            assert json.loads(request.content) == {"transition": {"id": "21"}}
            return httpx.Response(204)
        return httpx.Response(200, json=_jira_issue())

    provider = JiraProvider(
        {
            "site_url": "https://example.atlassian.net",
            "project_key": "WF",
            "issue_type": "Task",
            "status": {"values": {"doing": "In Progress"}},
        },
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(provider.move_item(CreatedItem(provider="jira", id="WF-12", title="Fallback"), "doing"))

    assert status.id == "WF-12"


def test_claim_item_assigns_authenticated_user() -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/api/3/myself":
            return httpx.Response(200, json={"accountId": "account-1"})
        if request.url.path.endswith("/assignee"):
            assert json.loads(request.content) == {"accountId": "account-1"}
            return httpx.Response(204)
        return httpx.Response(200, json=_jira_issue())

    provider = JiraProvider(
        {"site_url": "https://example.atlassian.net", "project_key": "WF", "issue_type": "Task"},
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    status = asyncio.run(provider.claim_item(CreatedItem(provider="jira", id="WF-12", title="Claim me")))

    assert status.id == "WF-12"


def test_resolve_transition_reports_available_options() -> None:
    provider = JiraProvider({"status": {"values": {"review": "In Review"}}}, {})

    with pytest.raises(ValueError, match=r"not available.*21 \(Start Progress → In Progress\)"):
        provider._resolve_transition(
            [{"id": "21", "name": "Start Progress", "to": {"name": "In Progress"}}],
            "review",
        )


def test_discover_items_paginates_and_combines_filters() -> None:
    requests: list[dict] = []

    def respond(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        requests.append(body)
        if "nextPageToken" not in body:
            return httpx.Response(
                200,
                json={
                    "issues": [{"key": "WF-1", "fields": {"summary": "First"}}],
                    "nextPageToken": "next-token",
                },
            )
        return httpx.Response(200, json={"issues": [{"key": "WF-2", "fields": {"summary": "Second"}}]})

    provider = JiraProvider(
        {
            "site_url": "https://example.atlassian.net",
            "project_key": "WF",
            "issue_type": "Task",
            "labels": {"feature": "enhancement"},
            "status": {"values": {"doing": "In Progress"}},
        },
        {"JIRA_EMAIL": "user@example.com", "JIRA_API_TOKEN": "token"},
        transport=httpx.MockTransport(respond),
    )

    items = asyncio.run(provider.discover_items("feature", "@me", "doing"))

    assert [item.id for item in items] == ["WF-1", "WF-2"]
    assert requests == [
        {
            "jql": 'project = "WF" AND statusCategory != "Done" AND labels = "enhancement" AND assignee = currentUser() AND status = "In Progress" ORDER BY created ASC',
            "fields": ["summary"],
            "maxResults": 100,
        },
        {
            "jql": 'project = "WF" AND statusCategory != "Done" AND labels = "enhancement" AND assignee = currentUser() AND status = "In Progress" ORDER BY created ASC',
            "fields": ["summary"],
            "maxResults": 100,
            "nextPageToken": "next-token",
        },
    ]


def test_discovery_jql_preserves_unfiltered_search_and_escapes_account_id() -> None:
    provider = JiraProvider(
        {"project_key": 'W"F'},
        {},
    )

    assert provider._discovery_jql(None, None, None) == 'project = "W\\"F" AND statusCategory != "Done" ORDER BY created ASC'
    assert 'assignee = "account\\"id"' in provider._discovery_jql(None, 'account"id', None)

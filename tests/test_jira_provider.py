import asyncio
import json

import httpx
import pytest

from workforge.models import Requirement, WorkTask
from workforge.providers.jira import JiraProvider
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


def test_registry_builds_jira_provider() -> None:
    assert isinstance(build_provider("jira", {}, {}), JiraProvider)


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

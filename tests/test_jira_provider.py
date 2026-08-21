import asyncio

import httpx

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

import asyncio

import httpx

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

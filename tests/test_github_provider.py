import asyncio
import json

import httpx

from workforge.models import Requirement, WorkTask
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
        assert request.url.path == "/repos/owner/workforge/issues"
        assert json.loads(request.content) == {
            "title": "Add status view",
            "body": "Show current progress.\n\n## Tasks\n\n- [ ] Build view\n- [x] Add tests",
            "labels": ["enhancement"],
        }
        return httpx.Response(
            201,
            json={
                "number": 12,
                "html_url": "https://github.com/owner/workforge/issues/12",
                "title": "Add status view",
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
    requirement = Requirement(
        title="Add status view",
        description="Show current progress.",
        labels=["feature", "unmapped"],
        tasks=[WorkTask(title="Build view"), WorkTask(title="Add tests", done=True)],
    )

    item = asyncio.run(provider.create_requirement(requirement))

    assert item.id == "12"
    assert item.url == "https://github.com/owner/workforge/issues/12"

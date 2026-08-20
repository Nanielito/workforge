from typing import Any

import httpx

from workforge.models import CardStatus, CreatedItem, ProviderCheck, Requirement
from workforge.providers.base import PlanningProvider


_CHECK_QUERY = """
query($owner: String!, $repository: String!, $project: Int!) {
  viewer { login }
  user(login: $owner) {
    repository(name: $repository) { nameWithOwner }
    projectV2(number: $project) { title }
  }
}
"""


class GitHubProvider(PlanningProvider):
    name = "github"

    def __init__(
        self,
        config: dict[str, Any],
        env: dict[str, str],
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.token = env.get("GITHUB_TOKEN", "")
        self.owner = config.get("owner", "")
        self.repository = config.get("repository", "")
        self.project_number = config.get("project_number")
        self.labels = config.get("labels", {})
        self.transport = transport

    async def check(self) -> ProviderCheck:
        missing = self._missing_configuration()
        if missing:
            return ProviderCheck(
                provider=self.name,
                ok=False,
                message=f"Missing configuration: {', '.join(missing)}",
            )
        if isinstance(self.project_number, bool) or not isinstance(self.project_number, int):
            return ProviderCheck(
                provider=self.name,
                ok=False,
                message="providers.github.project_number must be an integer.",
            )

        try:
            async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
                response = await client.post(
                    "https://api.github.com/graphql",
                    headers={"Authorization": f"Bearer {self.token}"},
                    json={
                        "query": _CHECK_QUERY,
                        "variables": {
                            "owner": self.owner,
                            "repository": self.repository,
                            "project": self.project_number,
                        },
                    },
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            return ProviderCheck(provider=self.name, ok=False, message=f"GitHub request failed: {error}")

        if errors := payload.get("errors"):
            return ProviderCheck(provider=self.name, ok=False, message=errors[0].get("message", "GitHub GraphQL error."))

        owner = payload.get("data", {}).get("user")
        if not owner:
            return ProviderCheck(provider=self.name, ok=False, message=f"GitHub user not found or inaccessible: {self.owner}")
        if not owner.get("repository"):
            return ProviderCheck(provider=self.name, ok=False, message=f"GitHub repository not found or inaccessible: {self.owner}/{self.repository}")
        if not owner.get("projectV2"):
            return ProviderCheck(provider=self.name, ok=False, message=f"GitHub Project v2 not found or inaccessible: {self.project_number}")

        return ProviderCheck(
            provider=self.name,
            ok=True,
            message=f"GitHub access verified for {owner['repository']['nameWithOwner']} and project {owner['projectV2']['title']}.",
        )

    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        if missing := self._missing_configuration():
            raise RuntimeError(f"Missing configuration: {', '.join(missing)}")

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            response = await client.post(
                f"https://api.github.com/repos/{self.owner}/{self.repository}/issues",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                json={
                    "title": requirement.title,
                    "body": _build_issue_body(requirement),
                    "labels": self._label_names_for(requirement.labels),
                },
            )
            response.raise_for_status()
            issue = response.json()

        return CreatedItem(
            provider=self.name,
            id=str(issue["number"]),
            url=issue.get("html_url"),
            title=issue.get("title") or requirement.title,
        )

    def _missing_configuration(self) -> list[str]:
        return [
            name
            for name, value in {
                "GITHUB_TOKEN": self.token,
                "providers.github.owner": self.owner,
                "providers.github.repository": self.repository,
                "providers.github.project_number": self.project_number,
            }.items()
            if value in (None, "")
        ]

    def _label_names_for(self, logical_names: list[str]) -> list[str]:
        if not isinstance(self.labels, dict):
            return []
        return [label for name in logical_names if isinstance(label := self.labels.get(name), str) and label]

    async def get_card_status(self, item: CreatedItem) -> CardStatus:
        raise NotImplementedError

    async def complete_task(self, item: CreatedItem, task_ref: str) -> CardStatus:
        raise NotImplementedError

    async def comment_card(self, item: CreatedItem, text: str) -> CardStatus:
        raise NotImplementedError

    async def move_card(self, item: CreatedItem, list_ref: str) -> CardStatus:
        raise NotImplementedError

    async def discover_cards(self, label_ref: str | None = None) -> list[CreatedItem]:
        raise NotImplementedError


def _build_issue_body(requirement: Requirement) -> str:
    parts = [requirement.description] if requirement.description else []
    if requirement.tasks:
        tasks = "\n".join(f"- [{'x' if task.done else ' '}] {task.title}" for task in requirement.tasks)
        parts.append(f"## Tasks\n\n{tasks}")
    return "\n\n".join(parts)

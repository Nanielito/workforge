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
        self.transport = transport

    async def check(self) -> ProviderCheck:
        missing = [
            name
            for name, value in {
                "GITHUB_TOKEN": self.token,
                "providers.github.owner": self.owner,
                "providers.github.repository": self.repository,
                "providers.github.project_number": self.project_number,
            }.items()
            if value in (None, "")
        ]
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
        raise NotImplementedError

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

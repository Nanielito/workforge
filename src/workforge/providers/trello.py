import os
from typing import Any

import httpx

from workforge.models import CreatedItem, ProviderCheck, Requirement
from workforge.providers.base import PlanningProvider


class TrelloProvider(PlanningProvider):
    name = "trello"

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.api_key = os.getenv("TRELLO_API_KEY", "")
        self.api_token = os.getenv("TRELLO_API_TOKEN", "")
        self.list_id = config.get("list_id", "")
        self.base_url = "https://api.trello.com/1"

    async def check(self) -> ProviderCheck:
        missing = [
            name
            for name, value in {
                "TRELLO_API_KEY": self.api_key,
                "TRELLO_API_TOKEN": self.api_token,
                "providers.trello.list_id": self.list_id,
            }.items()
            if not value
        ]

        if missing:
            return ProviderCheck(
                provider=self.name,
                ok=False,
                message=f"Missing configuration: {', '.join(missing)}",
            )

        return ProviderCheck(provider=self.name, ok=True, message="Trello configuration is present.")

    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        check = await self.check()
        if not check.ok:
            raise RuntimeError(check.message)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=20) as client:
            card = await self._create_card(client, requirement)
            if requirement.tasks:
                checklist = await self._create_checklist(client, card["id"])
                for task in requirement.tasks:
                    await self._create_check_item(client, checklist["id"], task.title)

        return CreatedItem(
            provider=self.name,
            id=card["id"],
            url=card.get("shortUrl") or card.get("url"),
            title=requirement.title,
        )

    def _auth_params(self) -> dict[str, str]:
        return {"key": self.api_key, "token": self.api_token}

    async def _create_card(self, client: httpx.AsyncClient, requirement: Requirement) -> dict[str, Any]:
        description = _build_description(requirement)
        response = await client.post(
            "/cards",
            params=self._auth_params(),
            json={
                "idList": self.list_id,
                "name": requirement.title,
                "desc": description,
            },
        )
        response.raise_for_status()
        return response.json()

    async def _create_checklist(self, client: httpx.AsyncClient, card_id: str) -> dict[str, Any]:
        response = await client.post(
            f"/cards/{card_id}/checklists",
            params=self._auth_params(),
            json={"name": "Tasks"},
        )
        response.raise_for_status()
        return response.json()

    async def _create_check_item(self, client: httpx.AsyncClient, checklist_id: str, name: str) -> dict[str, Any]:
        response = await client.post(
            f"/checklists/{checklist_id}/checkItems",
            params=self._auth_params(),
            json={"name": name},
        )
        response.raise_for_status()
        return response.json()


def _build_description(requirement: Requirement) -> str:
    parts = [
        requirement.description,
        "",
        f"Source: {requirement.source}",
        f"Namespace: {requirement.namespace}",
        f"Priority: {requirement.priority}",
    ]
    if requirement.labels:
        parts.append(f"Labels: {', '.join(requirement.labels)}")
    return "\n".join(part for part in parts if part is not None)

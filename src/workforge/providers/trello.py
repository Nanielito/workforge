from typing import Any

import httpx

from workforge.models import CardStatus, CreatedItem, ProviderCheck, Requirement, TaskStatus
from workforge.providers.base import PlanningProvider


class TrelloProvider(PlanningProvider):
    name = "trello"

    def __init__(self, config: dict[str, Any], env: dict[str, str]):
        self.config = config
        self.env = env
        self.api_key = env.get("TRELLO_API_KEY", "")
        self.api_token = env.get("TRELLO_API_TOKEN", "")
        self.list_id = config.get("list_id", "")
        self.labels = config.get("labels", {})
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

    async def get_card_status(self, item: CreatedItem) -> CardStatus:
        check = await self.check()
        if not check.ok:
            raise RuntimeError(check.message)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=20) as client:
            card = await self._get_card(client, item.id)
            checklists = await self._get_card_checklists(client, item.id)

        tasks = _task_statuses_from_checklists(checklists)

        return CardStatus(
            provider=self.name,
            id=card["id"],
            url=card.get("shortUrl") or card.get("url") or item.url,
            title=card.get("name") or item.title,
            closed=bool(card.get("closed")),
            tasks=tasks,
        )

    async def complete_task(self, item: CreatedItem, task_ref: str) -> CardStatus:
        check = await self.check()
        if not check.ok:
            raise RuntimeError(check.message)

        async with httpx.AsyncClient(base_url=self.base_url, timeout=20) as client:
            card = await self._get_card(client, item.id)
            checklists = await self._get_card_checklists(client, item.id)
            task = _find_task(checklists, task_ref)
            await self._update_check_item_state(client, item.id, task["id"], "complete")
            updated_checklists = await self._get_card_checklists(client, item.id)

        return CardStatus(
            provider=self.name,
            id=card["id"],
            url=card.get("shortUrl") or card.get("url") or item.url,
            title=card.get("name") or item.title,
            closed=bool(card.get("closed")),
            tasks=_task_statuses_from_checklists(updated_checklists),
        )

    def _auth_params(self) -> dict[str, str]:
        return {"key": self.api_key, "token": self.api_token}

    async def _create_card(self, client: httpx.AsyncClient, requirement: Requirement) -> dict[str, Any]:
        description = _build_description(requirement)
        label_ids = self._label_ids_for(requirement.labels)
        response = await client.post(
            "/cards",
            params=self._auth_params(),
            json={
                "idList": self.list_id,
                "name": requirement.title,
                "desc": description,
                "idLabels": label_ids,
            },
        )
        response.raise_for_status()
        return response.json()

    def _label_ids_for(self, label_names: list[str]) -> list[str]:
        if not isinstance(self.labels, dict):
            return []

        return [
            label_id
            for label_name in label_names
            if isinstance(label_id := self.labels.get(label_name), str) and label_id
        ]

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

    async def _get_card(self, client: httpx.AsyncClient, card_id: str) -> dict[str, Any]:
        response = await client.get(
            f"/cards/{card_id}",
            params={**self._auth_params(), "fields": "id,name,closed,shortUrl,url"},
        )
        response.raise_for_status()
        return response.json()

    async def _get_card_checklists(self, client: httpx.AsyncClient, card_id: str) -> list[dict[str, Any]]:
        response = await client.get(
            f"/cards/{card_id}/checklists",
            params={**self._auth_params(), "checkItems": "all"},
        )
        response.raise_for_status()
        return response.json()

    async def _update_check_item_state(
        self,
        client: httpx.AsyncClient,
        card_id: str,
        check_item_id: str,
        state: str,
    ) -> dict[str, Any]:
        response = await client.put(
            f"/cards/{card_id}/checkItem/{check_item_id}",
            params=self._auth_params(),
            json={"state": state},
        )
        response.raise_for_status()
        return response.json()


def _task_statuses_from_checklists(checklists: list[dict[str, Any]]) -> list[TaskStatus]:
    return [
        TaskStatus(
            id=check_item.get("id"),
            title=check_item["name"],
            done=check_item.get("state") == "complete",
        )
        for checklist in checklists
        for check_item in checklist.get("checkItems", [])
    ]


def _find_task(checklists: list[dict[str, Any]], task_ref: str) -> dict[str, Any]:
    tasks = [
        check_item
        for checklist in checklists
        for check_item in checklist.get("checkItems", [])
    ]

    exact_matches = [
        task
        for task in tasks
        if task.get("id") == task_ref or task.get("name", "").casefold() == task_ref.casefold()
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple tasks matched exactly: {task_ref}")

    partial_matches = [
        task
        for task in tasks
        if task_ref.casefold() in task.get("name", "").casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        titles = ", ".join(task.get("name", "") for task in partial_matches)
        raise ValueError(f"Multiple tasks matched '{task_ref}': {titles}")

    raise ValueError(f"Task not found: {task_ref}")


def _build_description(requirement: Requirement) -> str:
    parts = [
        requirement.description,
    ]
    return "\n".join(part for part in parts if part)

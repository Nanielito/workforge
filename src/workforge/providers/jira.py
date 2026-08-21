from typing import Any
from urllib.parse import urlparse

import httpx

from workforge.models import CreatedItem, ItemStatus, ProviderCheck, Requirement
from workforge.providers.base import PlanningProvider


class JiraProvider(PlanningProvider):
    name = "jira"

    def __init__(
        self,
        config: dict[str, Any],
        env: dict[str, str],
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        self.site_url = config.get("site_url", "").rstrip("/")
        self.project_key = config.get("project_key", "")
        self.issue_type = config.get("issue_type", "")
        self.labels = config.get("labels", {})
        self.versions = config.get("versions", {})
        self.email = env.get("JIRA_EMAIL", "")
        self.api_token = env.get("JIRA_API_TOKEN", "")
        self.transport = transport

    async def check(self) -> ProviderCheck:
        if error := self._configuration_error():
            return ProviderCheck(provider=self.name, ok=False, message=error)

        try:
            async with httpx.AsyncClient(
                base_url=self.site_url,
                auth=(self.email, self.api_token),
                timeout=20,
                transport=self.transport,
            ) as client:
                user_response = await client.get("/rest/api/3/myself")
                user_response.raise_for_status()
                project_response = await client.get(f"/rest/api/3/project/{self.project_key}")
                project_response.raise_for_status()
                user = user_response.json()
                project = project_response.json()
        except (httpx.HTTPError, ValueError) as error:
            return ProviderCheck(provider=self.name, ok=False, message=f"Jira request failed: {self._safe_message(error)}")

        return ProviderCheck(
            provider=self.name,
            ok=True,
            message=f"Jira access verified for {user.get('displayName', self.email)} and project {project.get('key', self.project_key)}.",
        )

    def _configuration_error(self) -> str | None:
        missing = [
            name
            for name, value in {
                "JIRA_EMAIL": self.email,
                "JIRA_API_TOKEN": self.api_token,
                "providers.jira.site_url": self.site_url,
                "providers.jira.project_key": self.project_key,
                "providers.jira.issue_type": self.issue_type,
            }.items()
            if not value
        ]
        if missing:
            return f"Missing configuration: {', '.join(missing)}"

        parsed_url = urlparse(self.site_url)
        if parsed_url.scheme != "https" or not parsed_url.netloc:
            return "providers.jira.site_url must be an HTTPS URL."
        return None

    def _safe_message(self, error: object) -> str:
        message = str(error)
        for secret in (self.api_token, self.email):
            if secret:
                message = message.replace(secret, "[REDACTED]")
        return message

    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        if error := self._configuration_error():
            raise RuntimeError(error)

        fields: dict[str, Any] = {
            "project": {"key": self.project_key},
            "issuetype": {"name": self.issue_type},
            "summary": requirement.title,
            "description": _adf_document(requirement),
            "labels": self._label_names_for(requirement.labels),
        }
        if requirement.milestone:
            fields["fixVersions"] = [{"id": self._version_id_for(requirement.milestone)}]

        try:
            async with httpx.AsyncClient(
                base_url=self.site_url,
                auth=(self.email, self.api_token),
                timeout=20,
                transport=self.transport,
            ) as client:
                response = await client.post("/rest/api/3/issue", json={"fields": fields})
                response.raise_for_status()
                issue = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise RuntimeError(f"Jira request failed: {self._safe_message(error)}") from error

        return CreatedItem(
            provider=self.name,
            id=issue["key"],
            url=f"{self.site_url}/browse/{issue['key']}",
            title=requirement.title,
        )

    def _label_names_for(self, logical_names: list[str]) -> list[str]:
        if not isinstance(self.labels, dict):
            return []
        return [label for name in logical_names if isinstance(label := self.labels.get(name), str) and label]

    def _version_id_for(self, logical_name: str) -> str:
        version_id = self.versions.get(logical_name) if isinstance(self.versions, dict) else None
        if isinstance(version_id, bool) or not isinstance(version_id, (str, int)) or not str(version_id):
            raise ValueError(f"Jira version is not configured: {logical_name}")
        return str(version_id)

    async def get_item_status(self, item: CreatedItem) -> ItemStatus:
        raise NotImplementedError("Jira status reading is not implemented yet.")

    async def complete_task(self, item: CreatedItem, task_ref: str) -> ItemStatus:
        raise NotImplementedError("Jira task completion is not implemented yet.")

    async def comment_item(self, item: CreatedItem, text: str) -> ItemStatus:
        raise NotImplementedError("Jira comments are not implemented yet.")

    async def move_item(self, item: CreatedItem, status_ref: str) -> ItemStatus:
        raise NotImplementedError("Jira transitions are not implemented yet.")

    async def discover_items(
        self,
        label_ref: str | None = None,
        assignee_ref: str | None = None,
        status_ref: str | None = None,
    ) -> list[CreatedItem]:
        raise NotImplementedError("Jira discovery is not implemented yet.")


def _adf_document(requirement: Requirement) -> dict[str, Any]:
    content: list[dict[str, Any]] = []
    if requirement.description:
        content.append({"type": "paragraph", "content": [{"type": "text", "text": requirement.description}]})
    if requirement.tasks:
        content.extend(
            [
                {"type": "heading", "attrs": {"level": 2}, "content": [{"type": "text", "text": "Tasks"}]},
                {
                    "type": "taskList",
                    "attrs": {"localId": "workforge-tasks"},
                    "content": [
                        {
                            "type": "taskItem",
                            "attrs": {
                                "localId": f"workforge-task-{index}",
                                "state": "DONE" if task.done else "TODO",
                            },
                            "content": [{"type": "text", "text": task.title}],
                        }
                        for index, task in enumerate(requirement.tasks, start=1)
                    ],
                },
            ]
        )
    return {"type": "doc", "version": 1, "content": content}

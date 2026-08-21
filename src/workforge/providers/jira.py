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
        raise NotImplementedError("Jira issue creation is not implemented yet.")

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

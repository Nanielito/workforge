import re
from typing import Any

import httpx

from workforge.models import CreatedItem, ItemStatus, ProviderCheck, Requirement, TaskStatus
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

_PROJECT_QUERY = """
query($owner: String!, $project: Int!) {
  user(login: $owner) { projectV2(number: $project) { id } }
}
"""

_ADD_PROJECT_ITEM_MUTATION = """
mutation($project: ID!, $content: ID!) {
  addProjectV2ItemById(input: {projectId: $project, contentId: $content}) { item { id } }
}
"""

_STATUS_CONTEXT_QUERY = """
query($owner: String!, $repository: String!, $project: Int!, $issue: Int!) {
  user(login: $owner) {
    projectV2(number: $project) {
      id
      fields(first: 50) {
        nodes {
          ... on ProjectV2SingleSelectField { id name options { id name } }
        }
      }
    }
  }
  repository(owner: $owner, name: $repository) {
    issue(number: $issue) {
      projectItems(first: 20) { nodes { id project { id } } }
    }
  }
}
"""

_UPDATE_STATUS_MUTATION = """
mutation($project: ID!, $item: ID!, $field: ID!, $option: String!) {
  updateProjectV2ItemFieldValue(
    input: {
      projectId: $project
      itemId: $item
      fieldId: $field
      value: {singleSelectOptionId: $option}
    }
  ) { projectV2Item { id } }
}
"""

_PROJECT_ITEMS_QUERY = """
query($owner: String!, $project: Int!, $cursor: String) {
  user(login: $owner) {
    projectV2(number: $project) {
      items(first: 100, after: $cursor) {
        nodes {
          content {
            ... on Issue {
              number
              title
              url
              state
              repository { nameWithOwner }
              labels(first: 100) { nodes { id name } }
            }
          }
        }
        pageInfo { hasNextPage endCursor }
      }
    }
  }
}
"""

_TASK_PATTERN = re.compile(r"^- \[([ xX])\] (.+)$")


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
        self.milestones = config.get("milestones", {})
        self.status = config.get("status", {})
        self.transport = transport

    async def check(self) -> ProviderCheck:
        if error := self._configuration_error():
            return ProviderCheck(provider=self.name, ok=False, message=error)

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
            return ProviderCheck(provider=self.name, ok=False, message=f"GitHub request failed: {self._safe_message(error)}")

        if errors := payload.get("errors"):
            return ProviderCheck(provider=self.name, ok=False, message=self._safe_message(errors[0].get("message", "GitHub GraphQL error.")))

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
        self._require_configuration()

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            project_id = await self._get_project_id(client)
            payload: dict[str, Any] = {
                "title": requirement.title,
                "body": _build_issue_body(requirement),
                "labels": self._label_names_for(requirement.labels),
            }
            if requirement.milestone:
                payload["milestone"] = self._milestone_number_for(requirement.milestone)

            response = await client.post(
                f"https://api.github.com/repos/{self.owner}/{self.repository}/issues",
                headers=self._rest_headers(),
                json=payload,
            )
            response.raise_for_status()
            issue = response.json()
            try:
                await self._add_issue_to_project(client, project_id, issue["node_id"])
            except (httpx.HTTPError, RuntimeError, ValueError) as error:
                raise RuntimeError(
                    f"Issue created at {issue.get('html_url', '')}, but adding it to GitHub Project v2 failed: {error}"
                ) from error

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

    def _configuration_error(self) -> str | None:
        if missing := self._missing_configuration():
            return f"Missing configuration: {', '.join(missing)}"
        if isinstance(self.project_number, bool) or not isinstance(self.project_number, int) or self.project_number < 1:
            return "providers.github.project_number must be a positive integer."
        return None

    def _require_configuration(self) -> None:
        if error := self._configuration_error():
            raise RuntimeError(error)

    def _safe_message(self, error: object) -> str:
        message = str(error)
        return message.replace(self.token, "[REDACTED]") if self.token else message

    def _label_names_for(self, logical_names: list[str]) -> list[str]:
        if not isinstance(self.labels, dict):
            return []
        return [label for name in logical_names if isinstance(label := self.labels.get(name), str) and label]

    def _milestone_number_for(self, logical_name: str) -> int:
        number = self.milestones.get(logical_name) if isinstance(self.milestones, dict) else None
        if isinstance(number, bool) or not isinstance(number, int) or number < 1:
            raise ValueError(f"GitHub milestone is not configured: {logical_name}")
        return number

    async def _get_project_id(self, client: httpx.AsyncClient) -> str:
        payload = await self._graphql(
            client,
            _PROJECT_QUERY,
            {"owner": self.owner, "project": self.project_number},
        )
        owner = payload.get("data", {}).get("user") or {}
        project = owner.get("projectV2")
        if not project:
            raise RuntimeError(f"GitHub Project v2 not found or inaccessible: {self.project_number}")
        return project["id"]

    async def _add_issue_to_project(self, client: httpx.AsyncClient, project_id: str, issue_id: str) -> None:
        await self._graphql(
            client,
            _ADD_PROJECT_ITEM_MUTATION,
            {"project": project_id, "content": issue_id},
        )

    async def _graphql(self, client: httpx.AsyncClient, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = await client.post(
            "https://api.github.com/graphql",
            headers={"Authorization": f"Bearer {self.token}"},
            json={"query": query, "variables": variables},
        )
        response.raise_for_status()
        payload = response.json()
        if errors := payload.get("errors"):
            raise RuntimeError(self._safe_message(errors[0].get("message", "GitHub GraphQL error.")))
        return payload

    async def get_item_status(self, item: CreatedItem) -> ItemStatus:
        self._require_configuration()

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            issue = await self._get_issue(client, item.id)

        return self._item_status_from_issue(issue, item)

    async def complete_task(self, item: CreatedItem, task_ref: str) -> ItemStatus:
        self._require_configuration()

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            issue = await self._get_issue(client, item.id)
            body = issue.get("body") or ""
            updated_body = _complete_task_in_issue_body(body, task_ref)
            if updated_body != body:
                issue = await self._update_issue_body(client, item.id, updated_body)

        return self._item_status_from_issue(issue, item)

    async def comment_item(self, item: CreatedItem, text: str) -> ItemStatus:
        self._require_configuration()
        if not text.strip():
            raise ValueError("Comment text cannot be empty.")

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            await self._comment_issue(client, item.id, text)

        return await self.get_item_status(item)

    async def move_item(self, item: CreatedItem, status_ref: str) -> ItemStatus:
        self._require_configuration()
        if not isinstance(self.status, dict) or not self.status.get("field"):
            raise RuntimeError("Missing configuration: providers.github.status.field")

        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            context = await self._get_status_context(client, item, status_ref)
            await self._graphql(
                client,
                _UPDATE_STATUS_MUTATION,
                {
                    "project": context["project_id"],
                    "item": context["item_id"],
                    "field": context["field_id"],
                    "option": context["option_id"],
                },
            )

        return await self.get_item_status(item)

    async def discover_items(self, label_ref: str | None = None) -> list[CreatedItem]:
        self._require_configuration()

        discovered: list[CreatedItem] = []
        cursor: str | None = None
        async with httpx.AsyncClient(timeout=20, transport=self.transport) as client:
            while True:
                payload = await self._graphql(
                    client,
                    _PROJECT_ITEMS_QUERY,
                    {"owner": self.owner, "project": self.project_number, "cursor": cursor},
                )
                project = (payload.get("data", {}).get("user") or {}).get("projectV2") or {}
                items = project.get("items")
                if not items:
                    raise ValueError(f"GitHub Project v2 not found: {self.project_number}")

                for node in items.get("nodes", []):
                    issue = (node or {}).get("content") or {}
                    if self._is_discoverable_issue(issue, label_ref):
                        discovered.append(
                            CreatedItem(
                                provider=self.name,
                                id=str(issue["number"]),
                                url=issue.get("url"),
                                title=issue["title"],
                            )
                        )

                page_info = items.get("pageInfo", {})
                if not page_info.get("hasNextPage"):
                    break
                cursor = page_info.get("endCursor")

        return discovered

    def _is_discoverable_issue(self, issue: dict[str, Any], label_ref: str | None) -> bool:
        if issue.get("state") != "OPEN":
            return False
        repository = issue.get("repository", {}).get("nameWithOwner", "")
        if repository.casefold() != f"{self.owner}/{self.repository}".casefold():
            return False
        if not label_ref:
            return True

        configured_name = self.labels.get(label_ref) if isinstance(self.labels, dict) else None
        expected = configured_name or label_ref
        return any(
            label.get("id") == expected or label.get("name", "").casefold() == expected.casefold()
            for label in issue.get("labels", {}).get("nodes", [])
        )

    async def _get_issue(self, client: httpx.AsyncClient, issue_number: str) -> dict[str, Any]:
        response = await client.get(
            f"https://api.github.com/repos/{self.owner}/{self.repository}/issues/{issue_number}",
            headers=self._rest_headers(),
        )
        response.raise_for_status()
        return response.json()

    async def _get_status_context(
        self,
        client: httpx.AsyncClient,
        item: CreatedItem,
        status_ref: str,
    ) -> dict[str, str]:
        payload = await self._graphql(
            client,
            _STATUS_CONTEXT_QUERY,
            {
                "owner": self.owner,
                "repository": self.repository,
                "project": self.project_number,
                "issue": int(item.id),
            },
        )
        project = (payload.get("data", {}).get("user") or {}).get("projectV2") or {}
        project_id = project.get("id")
        if not project_id:
            raise ValueError(f"GitHub Project v2 not found: {self.project_number}")

        field_name = str(self.status["field"])
        fields = [field for field in project.get("fields", {}).get("nodes", []) if field]
        field = next((field for field in fields if field.get("name", "").casefold() == field_name.casefold()), None)
        if not field:
            raise ValueError(f"GitHub Project status field not found: {field_name}")

        values = self.status.get("values", {})
        option_name = values.get(status_ref, status_ref) if isinstance(values, dict) else status_ref
        option = next(
            (option for option in field.get("options", []) if option.get("name", "").casefold() == option_name.casefold()),
            None,
        )
        if not option:
            raise ValueError(f"GitHub Project status option not found: {option_name}")

        issue = (payload.get("data", {}).get("repository") or {}).get("issue") or {}
        project_items = issue.get("projectItems", {}).get("nodes", [])
        project_item = next(
            (project_item for project_item in project_items if project_item.get("project", {}).get("id") == project_id),
            None,
        )
        if not project_item:
            raise ValueError(f"Issue is not attached to GitHub Project v2: {item.id}")

        return {
            "project_id": project_id,
            "item_id": project_item["id"],
            "field_id": field["id"],
            "option_id": option["id"],
        }

    async def _update_issue_body(
        self,
        client: httpx.AsyncClient,
        issue_number: str,
        body: str,
    ) -> dict[str, Any]:
        response = await client.patch(
            f"https://api.github.com/repos/{self.owner}/{self.repository}/issues/{issue_number}",
            headers=self._rest_headers(),
            json={"body": body},
        )
        response.raise_for_status()
        return response.json()

    async def _comment_issue(self, client: httpx.AsyncClient, issue_number: str, text: str) -> None:
        response = await client.post(
            f"https://api.github.com/repos/{self.owner}/{self.repository}/issues/{issue_number}/comments",
            headers=self._rest_headers(),
            json={"body": text},
        )
        response.raise_for_status()

    def _item_status_from_issue(self, issue: dict[str, Any], item: CreatedItem) -> ItemStatus:
        return ItemStatus(
            provider=self.name,
            id=str(issue["number"]),
            url=issue.get("html_url") or item.url,
            title=issue.get("title") or item.title,
            closed=issue.get("state") == "closed",
            tasks=_task_statuses_from_issue_body(issue.get("body") or ""),
        )

    def _rest_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }


def _build_issue_body(requirement: Requirement) -> str:
    parts = [requirement.description] if requirement.description else []
    if requirement.tasks:
        tasks = "\n".join(f"- [{'x' if task.done else ' '}] {task.title}" for task in requirement.tasks)
        parts.append(f"## Tasks\n\n{tasks}")
    return "\n\n".join(parts)


def _task_statuses_from_issue_body(body: str) -> list[TaskStatus]:
    return [TaskStatus(id=task_id, title=title, done=done) for task_id, title, done, _ in _task_entries(body)]


def _task_entries(body: str) -> list[tuple[str, str, bool, int]]:
    tasks: list[tuple[str, str, bool, int]] = []
    in_tasks = False
    for line_index, line in enumerate(body.splitlines()):
        if line.strip() == "## Tasks":
            in_tasks = True
            continue
        if in_tasks and line.startswith("## "):
            break
        if in_tasks and (match := _TASK_PATTERN.fullmatch(line)):
            tasks.append(
                (
                    f"task-{len(tasks) + 1}",
                    match.group(2).strip(),
                    match.group(1).casefold() == "x",
                    line_index,
                )
            )
    return tasks


def _complete_task_in_issue_body(body: str, task_ref: str) -> str:
    tasks = _task_entries(body)
    exact_matches = [task for task in tasks if task[0] == task_ref or task[1].casefold() == task_ref.casefold()]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple tasks matched exactly: {task_ref}")

    matches = exact_matches or [task for task in tasks if task_ref.casefold() in task[1].casefold()]
    if len(matches) > 1:
        raise ValueError(f"Multiple tasks matched '{task_ref}': {', '.join(task[1] for task in matches)}")
    if not matches:
        raise ValueError(f"Task not found: {task_ref}")

    _, _, done, line_index = matches[0]
    if done:
        return body

    lines = body.splitlines(keepends=True)
    lines[line_index] = lines[line_index].replace("- [ ]", "- [x]", 1)
    return "".join(lines)

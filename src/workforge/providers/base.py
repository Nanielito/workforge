from abc import ABC, abstractmethod

from workforge.models import CreatedItem, ItemStatus, ProviderCheck, Requirement


class PlanningProvider(ABC):
    name: str

    @abstractmethod
    async def check(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        raise NotImplementedError

    @abstractmethod
    async def update_requirement_tasks(self, item: CreatedItem, requirement: Requirement) -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def get_item_status(self, item: CreatedItem) -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def complete_task(self, item: CreatedItem, task_ref: str) -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def comment_item(self, item: CreatedItem, text: str) -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def move_item(self, item: CreatedItem, status_ref: str) -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def claim_item(self, item: CreatedItem, assignee_ref: str = "@me") -> ItemStatus:
        raise NotImplementedError

    @abstractmethod
    async def discover_items(
        self,
        label_ref: str | None = None,
        assignee_ref: str | None = None,
        status_ref: str | None = None,
    ) -> list[CreatedItem]:
        raise NotImplementedError

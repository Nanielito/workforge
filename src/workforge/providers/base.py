from abc import ABC, abstractmethod

from workforge.models import CardStatus, CreatedItem, ProviderCheck, Requirement


class PlanningProvider(ABC):
    name: str

    @abstractmethod
    async def check(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        raise NotImplementedError

    @abstractmethod
    async def get_card_status(self, item: CreatedItem) -> CardStatus:
        raise NotImplementedError

    @abstractmethod
    async def complete_task(self, item: CreatedItem, task_ref: str) -> CardStatus:
        raise NotImplementedError

    @abstractmethod
    async def discover_cards(self, label_ref: str | None = None) -> list[CreatedItem]:
        raise NotImplementedError

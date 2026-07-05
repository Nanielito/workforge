from abc import ABC, abstractmethod

from workforge.models import CreatedItem, ProviderCheck, Requirement


class PlanningProvider(ABC):
    name: str

    @abstractmethod
    async def check(self) -> ProviderCheck:
        raise NotImplementedError

    @abstractmethod
    async def create_requirement(self, requirement: Requirement) -> CreatedItem:
        raise NotImplementedError

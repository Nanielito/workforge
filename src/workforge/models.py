from typing import Literal

from pydantic import BaseModel, Field


Priority = Literal["low", "medium", "high", "urgent"]


class WorkTask(BaseModel):
    title: str
    done: bool = False


class Requirement(BaseModel):
    title: str
    description: str = ""
    source: str = "manual"
    namespace: str = "default"
    priority: Priority = "medium"
    milestone: str | None = None
    labels: list[str] = Field(default_factory=list)
    tasks: list[WorkTask] = Field(default_factory=list)


class CreatedItem(BaseModel):
    provider: str
    id: str
    url: str | None = None
    title: str


class TaskStatus(BaseModel):
    id: str | None = None
    title: str
    done: bool = False


class ItemStatus(BaseModel):
    provider: str
    id: str
    url: str | None = None
    title: str
    closed: bool = False
    tasks: list[TaskStatus] = Field(default_factory=list)

    @property
    def completed_tasks(self) -> int:
        return sum(1 for task in self.tasks if task.done)


class ProviderCheck(BaseModel):
    provider: str
    ok: bool
    message: str

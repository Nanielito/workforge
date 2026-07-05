from typing import Any

from workforge.providers.base import PlanningProvider
from workforge.providers.trello import TrelloProvider


def build_provider(name: str, config: dict[str, Any]) -> PlanningProvider:
    if name == "trello":
        return TrelloProvider(config)

    raise ValueError(f"Unknown provider: {name}")

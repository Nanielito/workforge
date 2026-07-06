from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field


class WorkspaceDefaults(BaseModel):
    source: str = "manual"
    namespace: str = "default"
    dry_run: bool = True


class WorkspaceConfig(BaseModel):
    name: str
    default_provider: str = "trello"
    providers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    defaults: WorkspaceDefaults = Field(default_factory=WorkspaceDefaults)


def load_workspace_config(workspace_path: Path) -> WorkspaceConfig:
    config_path = workspace_path / "workforge.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Workspace config not found: {config_path}")

    env_path = workspace_path / ".env"
    if env_path.exists():
        load_dotenv(env_path)

    raw_config = yaml.safe_load(config_path.read_text()) or {}
    return WorkspaceConfig.model_validate(raw_config)

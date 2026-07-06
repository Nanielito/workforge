from pathlib import Path
from typing import Any

import yaml
from dotenv import dotenv_values
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


class WorkspaceRuntime(BaseModel):
    path: Path
    config: WorkspaceConfig
    env: dict[str, str] = Field(default_factory=dict)


def load_workspace_config(workspace_path: Path) -> WorkspaceConfig:
    return load_workspace(workspace_path).config


def load_workspace(workspace_path: Path) -> WorkspaceRuntime:
    config_path = workspace_path / "workforge.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"Workspace config not found: {config_path}")

    env_path = workspace_path / ".env"
    env: dict[str, str] = {}
    if env_path.exists():
        env = {key: value for key, value in dotenv_values(env_path).items() if value is not None}

    raw_config = yaml.safe_load(config_path.read_text()) or {}
    return WorkspaceRuntime(
        path=workspace_path,
        config=WorkspaceConfig.model_validate(raw_config),
        env=env,
    )

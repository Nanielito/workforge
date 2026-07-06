import os
from pathlib import Path

from workforge.config import load_workspace


def test_load_workspace_reads_env_without_global_side_effects(tmp_path: Path) -> None:
    workspace = tmp_path / "example"
    workspace.mkdir()
    (workspace / "workforge.yaml").write_text(
        """
name: example
default_provider: trello
providers:
  trello:
    list_id: list-123
"""
    )
    (workspace / ".env").write_text("TRELLO_API_KEY=workspace-key\nTRELLO_API_TOKEN=workspace-token\n")

    previous_api_key = os.environ.get("TRELLO_API_KEY")
    os.environ.pop("TRELLO_API_KEY", None)

    try:
        runtime = load_workspace(workspace)

        assert runtime.config.name == "example"
        assert runtime.env["TRELLO_API_KEY"] == "workspace-key"
        assert runtime.env["TRELLO_API_TOKEN"] == "workspace-token"
        assert "TRELLO_API_KEY" not in os.environ
    finally:
        if previous_api_key is not None:
            os.environ["TRELLO_API_KEY"] = previous_api_key

import os
from pathlib import Path

from workforge.config import load_workspace


def test_load_workspace_reads_env_without_global_side_effects(tmp_path: Path) -> None:
    workspace = tmp_path / "sample-workspace"
    workspace.mkdir()
    (workspace / "workforge.yaml").write_text(
        """
name: sample-workspace
default_provider: test-provider
providers:
  test-provider:
    resource_id: resource-123
"""
    )
    (workspace / ".env").write_text(
        "WORKFORGE_TEST_TOKEN=workspace-token\nWORKFORGE_TEST_SECRET=workspace-secret\n"
    )

    variable_name = "WORKFORGE_TEST_TOKEN"
    previous_value = os.environ.get(variable_name)
    os.environ.pop(variable_name, None)

    try:
        runtime = load_workspace(workspace)

        assert runtime.config.name == "sample-workspace"
        assert runtime.config.default_provider == "test-provider"
        assert runtime.env["WORKFORGE_TEST_TOKEN"] == "workspace-token"
        assert runtime.env["WORKFORGE_TEST_SECRET"] == "workspace-secret"
        assert variable_name not in os.environ
    finally:
        if previous_value is not None:
            os.environ[variable_name] = previous_value

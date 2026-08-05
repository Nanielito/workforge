from pathlib import Path

import yaml

from workforge.cli import (
    _env_example_template,
    _init_workspace,
    _project_workspace_gitignore_block,
    _workspace_config_template,
)


def test_workspace_config_template_for_trello() -> None:
    config = yaml.safe_load(_workspace_config_template("sample-project", "trello", "examples/sample"))

    assert config == {
        "name": "sample-project",
        "default_provider": "trello",
        "providers": {
            "trello": {
                "list_id": "replace-with-trello-list-id",
                "lists": {
                    "todo": "replace-with-trello-todo-list-id",
                    "doing": "replace-with-trello-doing-list-id",
                    "done": "replace-with-trello-done-list-id",
                },
                "labels": {},
            }
        },
        "defaults": {
            "source": "manual",
            "namespace": "examples/sample",
            "dry_run": True,
        },
    }


def test_init_workspace_creates_project_local_scaffold(tmp_path: Path) -> None:
    workspace = tmp_path / ".workforge"

    created = _init_workspace(
        workspace_path=workspace,
        name="sample-project",
        provider="test-provider",
        namespace="examples/sample",
        force=False,
    )

    assert created == [
        workspace / "workforge.yaml",
        workspace / ".env.example",
        workspace / "output" / ".gitkeep",
    ]
    assert (workspace / "inbox").is_dir()
    assert (workspace / "output").is_dir()
    assert (workspace / ".env.example").read_text() == ""
    assert "default_provider: test-provider" in (workspace / "workforge.yaml").read_text()


def test_init_workspace_does_not_overwrite_existing_files_without_force(tmp_path: Path) -> None:
    workspace = tmp_path / ".workforge"
    workspace.mkdir()
    config_path = workspace / "workforge.yaml"
    config_path.write_text("custom: true\n")

    _init_workspace(
        workspace_path=workspace,
        name="sample-project",
        provider="test-provider",
        namespace=None,
        force=False,
    )

    assert config_path.read_text() == "custom: true\n"


def test_init_workspace_overwrites_existing_files_with_force(tmp_path: Path) -> None:
    workspace = tmp_path / ".workforge"
    workspace.mkdir()
    config_path = workspace / "workforge.yaml"
    config_path.write_text("custom: true\n")

    _init_workspace(
        workspace_path=workspace,
        name="sample-project",
        provider="test-provider",
        namespace=None,
        force=True,
    )

    assert "default_provider: test-provider" in config_path.read_text()


def test_env_example_template_uses_provider_credentials() -> None:
    assert _env_example_template("trello") == "TRELLO_API_KEY=\nTRELLO_API_TOKEN=\n"
    assert _env_example_template("unknown") == ""


def test_project_workspace_gitignore_block() -> None:
    assert _project_workspace_gitignore_block(Path(".workforge")) == ".workforge/.env\n.workforge/output/\n"
    assert _project_workspace_gitignore_block(Path("/tmp/project/.workforge")) == ".workforge/.env\n.workforge/output/\n"

import asyncio
import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import typer
import yaml

from workforge.config import WorkspaceRuntime, load_workspace
from workforge.core.parser import parse_markdown_requirements
from workforge.models import CreatedItem, ItemStatus
from workforge.providers.registry import build_provider

app = typer.Typer(no_args_is_help=True)
providers_app = typer.Typer(no_args_is_help=True)
app.add_typer(providers_app, name="providers")


@app.command()
def init(
    workspace: Path = typer.Argument(Path(".workforge"), help="Workspace directory to create."),
    name: str | None = typer.Option(None, "--name", "-n", help="Workspace name. Defaults to the directory name."),
    provider: str = typer.Option("trello", "--provider", "-p", help="Default planning provider."),
    namespace: str | None = typer.Option(None, "--namespace", help="Default requirement namespace."),
    force: bool = typer.Option(False, "--force", help="Overwrite existing WorkForge scaffold files."),
    print_gitignore: bool = typer.Option(
        True,
        "--print-gitignore/--no-print-gitignore",
        help="Print recommended .gitignore entries for project-local workspaces.",
    ),
) -> None:
    created = _init_workspace(workspace, name, provider, namespace, force)
    for path in created:
        typer.echo(f"Created {path}")

    if print_gitignore:
        typer.echo("")
        typer.echo("Recommended .gitignore entries:")
        typer.echo(_project_workspace_gitignore_block(workspace))


@app.command()
def preview(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    save: bool = typer.Option(False, "--save", help="Save preview output under workspace output/<input-name>/preview.json."),
) -> None:
    runtime = load_workspace(workspace)
    requirements = parse_markdown_requirements(input_file.read_text(), runtime.config)
    output = [item.model_dump() for item in requirements]
    _echo_json(output)
    if save:
        _save_output(runtime.path, input_file, "preview.json", output)


@app.command()
def create(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    execute: bool = typer.Option(False, "--execute", help="Create external provider items even when workspace dry_run is true."),
    save: bool = typer.Option(False, "--save", help="Save output under workspace output/<input-name>/."),
) -> None:
    asyncio.run(_create(input_file, workspace, provider, dry_run, execute, save))


@app.command()
def discover(
    input_file: Path | None = typer.Argument(
        None,
        help="Optional input file used to choose output/<input-name>/items.json.",
    ),
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    label: str | None = typer.Option(None, "--label", "-l", help="Provider label name or ID used to filter items."),
    assignee: str | None = typer.Option(None, "--assignee", "-a", help="Provider username or @me used to filter items."),
    status: str | None = typer.Option(None, "--status", "-s", help="Provider status name or configured alias used to filter items."),
    output_name: str = typer.Option(
        "discovered",
        "--output-name",
        help="Output directory name when INPUT_FILE is omitted.",
    ),
    save: bool = typer.Option(False, "--save", help="Save discovered items as items.json."),
) -> None:
    asyncio.run(_discover(input_file, workspace, provider, label, assignee, status, output_name, save))


@app.command()
def status(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(False, "--save", help="Save status output under workspace output/<input-name>/status.json."),
) -> None:
    asyncio.run(_status(input_file, workspace, provider, save))


@app.command("agent-context")
def agent_context(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(False, "--save", help="Save agent context under workspace output/<input-name>/agent-context.md."),
) -> None:
    asyncio.run(_agent_context(input_file, workspace, provider, save))


@app.command("item-context")
def item_context(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    item: str = typer.Option(..., "--item", "-i", help="Item title, item ID, or unique title substring."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(False, "--save", help="Save focused item context under workspace output/<input-name>/items/."),
) -> None:
    asyncio.run(_item_context(input_file, workspace, item, provider, save))


@app.command("complete-task")
def complete_task(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    item: str = typer.Option(..., "--item", "-i", help="Item title, item ID, or unique title substring."),
    task: str = typer.Option(..., "--task", "-t", help="Task title, task ID, or unique title substring."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(True, "--save/--no-save", help="Refresh status.json and agent-context.md after completion."),
) -> None:
    asyncio.run(_complete_task(input_file, workspace, item, task, provider, save))


@app.command("comment-item")
def comment_item(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    item: str = typer.Option(..., "--item", "-i", help="Item title, item ID, or unique title substring."),
    text: str = typer.Option(..., "--text", "-t", help="Comment text to add to the item."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(True, "--save/--no-save", help="Refresh status.json and agent-context.md after commenting."),
) -> None:
    asyncio.run(_comment_item(input_file, workspace, item, text, provider, save))


@app.command("move-item")
def move_item(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    item: str = typer.Option(..., "--item", "-i", help="Item title, item ID, or unique title substring."),
    status: str = typer.Option(..., "--status", "-s", help="Destination status name or configured alias."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(True, "--save/--no-save", help="Refresh status.json and agent-context.md after moving."),
) -> None:
    asyncio.run(_move_item(input_file, workspace, item, status, provider, save))


@app.command("claim-item")
def claim_item(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    item: str = typer.Option(..., "--item", "-i", help="Item title, item ID, or unique title substring."),
    assignee: str = typer.Option("@me", "--assignee", "-a", help="Provider username or @me."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(True, "--save/--no-save", help="Refresh status.json and agent-context.md after assignment."),
) -> None:
    asyncio.run(_claim_item(input_file, workspace, item, assignee, provider, save))


@providers_app.command("test")
def test_provider(
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
) -> None:
    asyncio.run(_test_provider(workspace, provider))


async def _create(
    input_file: Path,
    workspace: Path,
    provider_name: str | None,
    dry_run: bool,
    execute: bool,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    config = runtime.config
    requirements = parse_markdown_requirements(input_file.read_text(), config)

    if dry_run or (config.defaults.dry_run and not execute):
        output = [item.model_dump() for item in requirements]
        _echo_json(output)
        if save:
            _save_output(runtime.path, input_file, "preview.json", output)
        return

    selected_provider = provider_name or config.default_provider
    provider_config = config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)

    created = []
    for requirement in requirements:
        created.append((await provider.create_requirement(requirement)).model_dump())

    _echo_json(created)
    if save:
        _save_output(runtime.path, input_file, "items.json", created)


async def _test_provider(workspace: Path, provider_name: str | None) -> None:
    runtime = load_workspace(workspace)
    config = runtime.config
    selected_provider = provider_name or config.default_provider
    provider_config = config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    result = await provider.check()
    typer.echo(result.model_dump_json(indent=2))


async def _discover(
    input_file: Path | None,
    workspace: Path,
    provider_name: str | None,
    label: str | None,
    assignee: str | None,
    status: str | None,
    output_name: str,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    discovered = [item.model_dump() for item in await provider.discover_items(label, assignee, status)]
    _echo_json(discovered)

    if save:
        _save_output(runtime.path, _output_ref_for(input_file, output_name), "items.json", discovered)


async def _status(input_file: Path, workspace: Path, provider_name: str | None, save: bool) -> None:
    runtime = load_workspace(workspace)
    statuses = await _load_item_statuses(runtime, input_file, provider_name)
    output = [status.model_dump() for status in statuses]
    _echo_json(output)
    if save:
        _save_output(runtime.path, input_file, "status.json", output)


async def _agent_context(input_file: Path, workspace: Path, provider_name: str | None, save: bool) -> None:
    runtime = load_workspace(workspace)
    statuses = await _load_item_statuses(runtime, input_file, provider_name)
    output = _build_agent_context(statuses)
    typer.echo(output)
    if save:
        _save_text_output(runtime.path, input_file, "agent-context.md", output)


async def _item_context(
    input_file: Path,
    workspace: Path,
    item_ref: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    statuses = await _load_item_statuses(runtime, input_file, provider_name)
    status = _find_item_status(statuses, item_ref)
    output = _build_item_context(status)
    typer.echo(output)
    if save:
        output_path = _item_context_path(runtime.path, input_file, status)
        _save_text_path(output_path, output)


async def _complete_task(
    input_file: Path,
    workspace: Path,
    item_ref: str,
    task_ref: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    item = _find_created_item(created_items, item_ref)
    updated_status = await provider.complete_task(item, task_ref)

    _echo_json(updated_status.model_dump())

    if save:
        statuses = await _load_item_statuses(runtime, input_file, provider_name)
        status_output = [status.model_dump() for status in statuses]
        _save_output(runtime.path, input_file, "status.json", status_output)
        _save_text_output(runtime.path, input_file, "agent-context.md", _build_agent_context(statuses))


async def _comment_item(
    input_file: Path,
    workspace: Path,
    item_ref: str,
    text: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    item = _find_created_item(created_items, item_ref)
    updated_status = await provider.comment_item(item, text)

    _echo_json(updated_status.model_dump())

    if save:
        await _refresh_saved_context(runtime, input_file, provider_name)


async def _move_item(
    input_file: Path,
    workspace: Path,
    item_ref: str,
    status_ref: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    item = _find_created_item(created_items, item_ref)
    updated_status = await provider.move_item(item, status_ref)

    _echo_json(updated_status.model_dump())

    if save:
        await _refresh_saved_context(runtime, input_file, provider_name)


async def _claim_item(
    input_file: Path,
    workspace: Path,
    item_ref: str,
    assignee_ref: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    item = _find_created_item(_load_created_items(runtime.path, input_file, selected_provider), item_ref)
    updated_status = await provider.claim_item(item, assignee_ref)

    _echo_json(updated_status.model_dump())
    if save:
        await _refresh_saved_context(runtime, input_file, provider_name)


async def _refresh_saved_context(
    runtime: WorkspaceRuntime,
    input_file: Path,
    provider_name: str | None,
) -> None:
    statuses = await _load_item_statuses(runtime, input_file, provider_name)
    status_output = [status.model_dump() for status in statuses]
    _save_output(runtime.path, input_file, "status.json", status_output)
    _save_text_output(runtime.path, input_file, "agent-context.md", _build_agent_context(statuses))


async def _load_item_statuses(
    runtime: WorkspaceRuntime,
    input_file: Path,
    provider_name: str | None,
) -> list[ItemStatus]:
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    return [await provider.get_item_status(item) for item in created_items]


def _load_created_items(workspace_path: Path, input_file: Path, provider_name: str) -> list[CreatedItem]:
    items_path = _output_dir_for(workspace_path, input_file) / "items.json"
    if not items_path.exists():
        raise FileNotFoundError(f"Created items output not found: {items_path}")

    raw_items = json.loads(items_path.read_text())
    return [
        CreatedItem.model_validate(item)
        for item in raw_items
        if item.get("provider") == provider_name
    ]


def _find_created_item(items: list[CreatedItem], item_ref: str) -> CreatedItem:
    exact_matches = [
        item
        for item in items
        if item.id == item_ref or item.title.casefold() == item_ref.casefold()
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple items matched exactly: {item_ref}")

    partial_matches = [
        item
        for item in items
        if item_ref.casefold() in item.title.casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        titles = ", ".join(item.title for item in partial_matches)
        raise ValueError(f"Multiple items matched '{item_ref}': {titles}")

    raise ValueError(f"Item not found: {item_ref}")


def _find_item_status(statuses: list[ItemStatus], item_ref: str) -> ItemStatus:
    exact_matches = [
        status
        for status in statuses
        if status.id == item_ref or status.title.casefold() == item_ref.casefold()
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple items matched exactly: {item_ref}")

    partial_matches = [
        status
        for status in statuses
        if item_ref.casefold() in status.title.casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        titles = ", ".join(status.title for status in partial_matches)
        raise ValueError(f"Multiple items matched '{item_ref}': {titles}")

    raise ValueError(f"Item not found: {item_ref}")


def _build_agent_context(statuses: list[ItemStatus]) -> str:
    lines = ["# WorkForge Agent Context", ""]

    for status in statuses:
        total_tasks = len(status.tasks)
        pending_tasks = [task for task in status.tasks if not task.done]
        completed_tasks = [task for task in status.tasks if task.done]
        lines.extend(
            [
                f"## {status.title}",
                "",
                f"Provider: {status.provider}",
                f"Item ID: {status.id}",
                f"URL: {status.url or ''}",
                f"Item closed: {status.closed}",
                f"Progress: {len(completed_tasks)}/{total_tasks} tasks complete",
                "",
                "### Pending Tasks",
                "",
            ]
        )

        if pending_tasks:
            lines.extend(f"- {task.title}" for task in pending_tasks)
        else:
            lines.append("- None")

        lines.extend(["", "### Completed Tasks", ""])
        if completed_tasks:
            lines.extend(f"- {task.title}" for task in completed_tasks)
        else:
            lines.append("- None")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_item_context(status: ItemStatus) -> str:
    total_tasks = len(status.tasks)
    pending_tasks = [task for task in status.tasks if not task.done]
    completed_tasks = [task for task in status.tasks if task.done]
    lines = [
        f"# {status.title}",
        "",
        f"Provider: {status.provider}",
        f"Item ID: {status.id}",
        f"URL: {status.url or ''}",
        f"Item closed: {status.closed}",
        f"Progress: {len(completed_tasks)}/{total_tasks} tasks complete",
        "",
        "## Implementation Focus",
        "",
        "Work only on this item unless the implementation requires a small supporting change.",
        "Prefer completing one pending task at a time, then run the relevant checks before marking it done.",
        "",
        "## Pending Tasks",
        "",
    ]

    if pending_tasks:
        lines.extend(_format_task_line(task) for task in pending_tasks)
    else:
        lines.append("- None")

    lines.extend(["", "## Completed Tasks", ""])
    if completed_tasks:
        lines.extend(_format_task_line(task) for task in completed_tasks)
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Completion Command",
            "",
            "After implementing and verifying a task, mark it complete with:",
            "",
            "```bash",
            "workforge complete-task <input-file> --workspace <workspace> "
            f"--item \"{status.id}\" --task \"<task-id-or-title>\"",
            "```",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _format_task_line(task: Any) -> str:
    suffix = f" (`{task.id}`)" if task.id else ""
    return f"- {task.title}{suffix}"


def _output_dir_for(workspace_path: Path, input_file: Path) -> Path:
    return workspace_path / "output" / input_file.stem


def _item_context_path(workspace_path: Path, input_file: Path, status: ItemStatus) -> Path:
    return _output_dir_for(workspace_path, input_file) / "items" / f"{_slugify(status.title)}.md"


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    normalized = "".join(character for character in normalized if not unicodedata.combining(character))
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = normalized.strip("-")
    return normalized or "item"


def _output_ref_for(input_file: Path | None, output_name: str) -> Path:
    return input_file or Path(output_name)


def _init_workspace(
    workspace_path: Path,
    name: str | None,
    provider: str,
    namespace: str | None,
    force: bool,
) -> list[Path]:
    workspace_name = name or workspace_path.name.removeprefix(".") or "workspace"
    default_namespace = namespace or workspace_name
    created: list[Path] = []

    for directory in [workspace_path, workspace_path / "inbox", workspace_path / "output"]:
        directory.mkdir(parents=True, exist_ok=True)

    files = {
        workspace_path / "workforge.yaml": _workspace_config_template(workspace_name, provider, default_namespace),
        workspace_path / ".env.example": _env_example_template(provider),
        workspace_path / "output" / ".gitkeep": "",
    }

    for path, content in files.items():
        if path.exists() and not force:
            continue

        path.write_text(content)
        created.append(path)

    return created


def _workspace_config_template(name: str, provider: str, namespace: str) -> str:
    provider_config: dict[str, Any]
    if provider == "trello":
        provider_config = {
            "list_id": "replace-with-trello-list-id",
            "lists": {
                "todo": "replace-with-trello-todo-list-id",
                "doing": "replace-with-trello-doing-list-id",
                "done": "replace-with-trello-done-list-id",
            },
            "labels": {},
        }
    elif provider == "github":
        provider_config = {
            "owner": "replace-with-github-owner",
            "repository": "replace-with-repository",
            "project_number": 1,
            "labels": {},
            "milestones": {},
            "status": {
                "field": "Status",
                "values": {
                    "todo": "Todo",
                    "doing": "In Progress",
                    "done": "Done",
                },
            },
        }
    else:
        provider_config = {}

    payload = {
        "name": name,
        "default_provider": provider,
        "providers": {
            provider: provider_config,
        },
        "defaults": {
            "source": "manual",
            "namespace": namespace,
            "dry_run": True,
        },
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _env_example_template(provider: str) -> str:
    if provider == "trello":
        return "TRELLO_API_KEY=\nTRELLO_API_TOKEN=\n"
    if provider == "github":
        return "GITHUB_TOKEN=\n"

    return ""


def _project_workspace_gitignore_block(workspace_path: Path) -> str:
    workspace_ref = workspace_path.name if workspace_path.is_absolute() else workspace_path.as_posix().rstrip("/")
    return f"{workspace_ref}/.env\n{workspace_ref}/output/\n"


def _save_output(workspace_path: Path, input_file: Path, filename: str, payload: Any) -> Path:
    output_dir = _output_dir_for(workspace_path, input_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(json.dumps(payload, indent=2) + "\n")
    typer.echo(f"Saved {output_path}")
    return output_path


def _save_text_output(workspace_path: Path, input_file: Path, filename: str, payload: str) -> Path:
    output_dir = _output_dir_for(workspace_path, input_file)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename
    output_path.write_text(payload)
    typer.echo(f"Saved {output_path}")
    return output_path


def _save_text_path(output_path: Path, payload: str) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(payload)
    typer.echo(f"Saved {output_path}")
    return output_path


def _echo_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2))

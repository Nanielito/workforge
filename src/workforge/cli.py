import asyncio
import json
from pathlib import Path
from typing import Any

import typer

from workforge.config import WorkspaceRuntime, load_workspace
from workforge.core.parser import parse_markdown_requirements
from workforge.models import CardStatus, CreatedItem
from workforge.providers.registry import build_provider

app = typer.Typer(no_args_is_help=True)
providers_app = typer.Typer(no_args_is_help=True)
app.add_typer(providers_app, name="providers")


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


@app.command("complete-task")
def complete_task(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    card: str = typer.Option(..., "--card", "-c", help="Card title, card ID, or unique title substring."),
    task: str = typer.Option(..., "--task", "-t", help="Task title, task ID, or unique title substring."),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    save: bool = typer.Option(True, "--save/--no-save", help="Refresh status.json and agent-context.md after completion."),
) -> None:
    asyncio.run(_complete_task(input_file, workspace, card, task, provider, save))


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
        _save_output(runtime.path, input_file, "cards.json", created)


async def _test_provider(workspace: Path, provider_name: str | None) -> None:
    runtime = load_workspace(workspace)
    config = runtime.config
    selected_provider = provider_name or config.default_provider
    provider_config = config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    result = await provider.check()
    typer.echo(result.model_dump_json(indent=2))


async def _status(input_file: Path, workspace: Path, provider_name: str | None, save: bool) -> None:
    runtime = load_workspace(workspace)
    statuses = await _load_card_statuses(runtime, input_file, provider_name)
    output = [status.model_dump() for status in statuses]
    _echo_json(output)
    if save:
        _save_output(runtime.path, input_file, "status.json", output)


async def _agent_context(input_file: Path, workspace: Path, provider_name: str | None, save: bool) -> None:
    runtime = load_workspace(workspace)
    statuses = await _load_card_statuses(runtime, input_file, provider_name)
    output = _build_agent_context(statuses)
    typer.echo(output)
    if save:
        _save_text_output(runtime.path, input_file, "agent-context.md", output)


async def _complete_task(
    input_file: Path,
    workspace: Path,
    card_ref: str,
    task_ref: str,
    provider_name: str | None,
    save: bool,
) -> None:
    runtime = load_workspace(workspace)
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    item = _find_created_item(created_items, card_ref)
    updated_status = await provider.complete_task(item, task_ref)

    _echo_json(updated_status.model_dump())

    if save:
        statuses = await _load_card_statuses(runtime, input_file, provider_name)
        status_output = [status.model_dump() for status in statuses]
        _save_output(runtime.path, input_file, "status.json", status_output)
        _save_text_output(runtime.path, input_file, "agent-context.md", _build_agent_context(statuses))


async def _load_card_statuses(
    runtime: WorkspaceRuntime,
    input_file: Path,
    provider_name: str | None,
) -> list[CardStatus]:
    selected_provider = provider_name or runtime.config.default_provider
    provider_config = runtime.config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config, runtime.env)
    created_items = _load_created_items(runtime.path, input_file, selected_provider)
    return [await provider.get_card_status(item) for item in created_items]


def _load_created_items(workspace_path: Path, input_file: Path, provider_name: str) -> list[CreatedItem]:
    cards_path = _output_dir_for(workspace_path, input_file) / "cards.json"
    if not cards_path.exists():
        raise FileNotFoundError(f"Created cards output not found: {cards_path}")

    raw_items = json.loads(cards_path.read_text())
    return [
        CreatedItem.model_validate(item)
        for item in raw_items
        if item.get("provider") == provider_name
    ]


def _find_created_item(items: list[CreatedItem], card_ref: str) -> CreatedItem:
    exact_matches = [
        item
        for item in items
        if item.id == card_ref or item.title.casefold() == card_ref.casefold()
    ]
    if len(exact_matches) == 1:
        return exact_matches[0]
    if len(exact_matches) > 1:
        raise ValueError(f"Multiple cards matched exactly: {card_ref}")

    partial_matches = [
        item
        for item in items
        if card_ref.casefold() in item.title.casefold()
    ]
    if len(partial_matches) == 1:
        return partial_matches[0]
    if len(partial_matches) > 1:
        titles = ", ".join(item.title for item in partial_matches)
        raise ValueError(f"Multiple cards matched '{card_ref}': {titles}")

    raise ValueError(f"Card not found: {card_ref}")


def _build_agent_context(statuses: list[CardStatus]) -> str:
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
                f"Card ID: {status.id}",
                f"URL: {status.url or ''}",
                f"Card closed: {status.closed}",
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


def _output_dir_for(workspace_path: Path, input_file: Path) -> Path:
    return workspace_path / "output" / input_file.stem


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


def _echo_json(payload: Any) -> None:
    typer.echo(json.dumps(payload, indent=2))

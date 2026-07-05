import asyncio
import json
from pathlib import Path

import typer

from workforge.config import load_workspace_config
from workforge.core.parser import parse_markdown_requirements
from workforge.providers.registry import build_provider

app = typer.Typer(no_args_is_help=True)
providers_app = typer.Typer(no_args_is_help=True)
app.add_typer(providers_app, name="providers")


@app.command()
def preview(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
) -> None:
    config = load_workspace_config(workspace)
    requirements = parse_markdown_requirements(input_file.read_text(), config)
    typer.echo(json.dumps([item.model_dump() for item in requirements], indent=2))


@app.command()
def create(
    input_file: Path,
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    execute: bool = typer.Option(False, "--execute", help="Create external provider items even when workspace dry_run is true."),
) -> None:
    asyncio.run(_create(input_file, workspace, provider, dry_run, execute))


@providers_app.command("test")
def test_provider(
    workspace: Path = typer.Option(..., "--workspace", "-w"),
    provider: str | None = typer.Option(None, "--provider", "-p"),
) -> None:
    asyncio.run(_test_provider(workspace, provider))


async def _create(input_file: Path, workspace: Path, provider_name: str | None, dry_run: bool, execute: bool) -> None:
    config = load_workspace_config(workspace)
    requirements = parse_markdown_requirements(input_file.read_text(), config)

    if dry_run or (config.defaults.dry_run and not execute):
        typer.echo(json.dumps([item.model_dump() for item in requirements], indent=2))
        return

    selected_provider = provider_name or config.default_provider
    provider_config = config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config)

    created = []
    for requirement in requirements:
        created.append((await provider.create_requirement(requirement)).model_dump())

    typer.echo(json.dumps(created, indent=2))


async def _test_provider(workspace: Path, provider_name: str | None) -> None:
    config = load_workspace_config(workspace)
    selected_provider = provider_name or config.default_provider
    provider_config = config.providers.get(selected_provider, {})
    provider = build_provider(selected_provider, provider_config)
    result = await provider.check()
    typer.echo(result.model_dump_json(indent=2))

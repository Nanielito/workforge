# WorkForge Agent Guide

## Project overview

WorkForge is a Python CLI that parses Markdown requirements into provider-neutral planning items and synchronizes them with planning systems such as Trello, GitHub Projects, and Jira.

The project prioritizes:

- provider-neutral domain models;
- isolated, project-specific workspace configuration and credentials;
- safe previews before external writes;
- small provider adapters with consistent behavior;
- backward-compatible CLI and saved-output contracts within a major version.

Python 3.11 is the minimum supported version. The package uses Typer for the CLI, Pydantic for models and configuration, HTTPX for provider requests, PyYAML for workspace files, and pytest for tests.

## Repository map

- `src/workforge/cli.py`: Typer commands and application orchestration.
- `src/workforge/models.py`: provider-neutral domain and status models.
- `src/workforge/config.py`: workspace configuration and isolated `.env` loading.
- `src/workforge/core/parser.py`: Markdown-to-requirement parsing.
- `src/workforge/providers/base.py`: provider contract.
- `src/workforge/providers/registry.py`: provider construction.
- `src/workforge/providers/{trello,github,jira}.py`: provider-specific API logic.
- `tests/`: behavior-focused unit tests, including mocked HTTP provider tests.
- `workspaces/*-example/`: committed examples only; generated output and real credentials remain local.
- `docs/`: provider designs and other decisions that need more detail than the README.
- `.github/workflows/`: CI and manual SemVer release automation.

The main flow is:

1. `load_workspace` reads `workforge.yaml` and a workspace-local `.env` without mutating the process environment.
2. `parse_markdown_requirements` produces provider-neutral `Requirement` models.
3. `build_provider` selects a `PlanningProvider` adapter.
4. CLI orchestration calls the adapter and optionally saves provider-neutral JSON or Markdown context under the workspace output directory.

## Working rules

- Read the relevant implementation, callers, tests, and local diff before editing.
- Preserve unrelated and pre-existing working-tree changes. Never discard, overwrite, stage, or commit them.
- Make the smallest complete change. Reuse existing patterns and dependencies; do not add speculative abstractions or dependencies.
- Keep provider-specific concepts inside provider modules. Shared models, parser output, CLI terminology, and saved formats must remain provider-neutral.
- Extend `PlanningProvider` and `build_provider` together when adding a provider capability, then cover every concrete provider as required by the contract.
- Keep CLI commands thin: parsing/configuration, provider selection, orchestration, output, and persistence belong there; provider API details do not.
- Preserve async provider methods and inject `httpx.MockTransport` in tests. Tests must not call live external services.
- Validate configuration before network requests and turn provider failures into useful, secret-safe errors.
- Never expose tokens, credentials, authorization headers, or `.env` contents in output, exceptions, fixtures, logs, or commits.
- Do not mutate external planning systems unless the user explicitly authorizes it. Prefer preview, provider checks, and mocked tests while developing.
- WorkForge dogfoods its GitHub provider: create this repository's tracking issues through the `workspaces/workforge` workspace and WorkForge CLI, previewing first and using `--execute` only when the user explicitly authorizes the external write. Use `gh` or the GitHub UI only when that workflow cannot perform the requested operation.
- Keep workspace secrets in `.env`, commit only `.env.example`, and preserve workspace isolation by passing the runtime environment explicitly.
- Treat CLI names, options, JSON fields, output paths, provider contracts, and workspace configuration as public interfaces. Breaking changes require explicit approval and a major release plan.
- Update README examples or design docs when user-facing commands, configuration, provider behavior, or output contracts change.
- Do not manually edit release versions or generated changelog entries as part of ordinary feature work; the release workflow owns them.

## Tests and verification

Install the development environment with:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

For a focused change, run the smallest relevant test first:

```bash
python -m pytest tests/test_<area>.py
```

Before handing off a completed code change, run the full local CI equivalent:

```bash
python -m pytest
python -m build
```

Add or update tests for every behavior change and regression fix. Prefer observable behavior over implementation-detail assertions. Provider tests should assert request paths and payloads, success mapping, configuration validation, error handling, and secret redaction where relevant.

If a required check cannot run, state exactly which check was skipped and why. Do not claim verification that was not performed.

## Git and commits

- Use Conventional Commits: `<type>(<optional-scope>): <imperative summary>`.
- Allowed common types are `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `build`, `ci`, and `perf`.
- Keep the subject concise, lowercase after the colon, and free of a trailing period.
- Use a scope when it adds useful precision, such as `github`, `trello`, `jira`, `cli`, `parser`, or `workspace`.
- Mark breaking changes with `!` and explain them in a `BREAKING CHANGE:` footer.
- Keep commits atomic: one coherent change plus its tests and documentation.
- Do not create a commit, push, or open a PR unless the user asks. Before committing, inspect the staged diff and ensure it contains only intended files.

Examples:

```text
feat(jira): create issues from requirements
fix(cli): preserve workspace output on provider failure
docs: document provider configuration
feat(cli)!: rename card commands to item commands
```

## Pull request handoff

Always provide a ready-to-paste PR title and summary when handing off a completed change, even if no PR is created.

Use a Conventional Commit-style PR title and this body:

```markdown
## Summary

- <what changed>
- <why it changed>

## Verification

- `<command>`
- <manual check, or `Not run (reason)`>

## Risks

- <compatibility, migration, external side-effect, or operational risk>
- None identified
```

Mention user-visible CLI/configuration/output changes, deferred work, and breaking or migration implications. Keep the summary factual; never claim tests passed unless they were run successfully.

## Definition of done

A change is complete only when the requested behavior is implemented, relevant tests cover it, applicable tests pass, documentation is updated when needed, no secrets or unrelated changes are included, and the handoff contains the changed files, verification results, and PR-ready summary.

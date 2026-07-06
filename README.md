# WorkForge

WorkForge turns raw work inputs into structured planning items, then sends them
to planning providers such as Trello, Jira, GitHub Issues, or Linear.

The first provider is Trello. The core model is provider-neutral so future
integrations can translate the same requirements into issues, cards, tickets, or
tasks.

## Goals

- Keep planning automation outside product repositories.
- Support multiple workspaces with their own configuration and environment.
- Preview generated requirements before creating external items.
- Add providers through a small adapter interface.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Preview requirements from a workspace inbox file:

```bash
workforge preview workspaces/example/inbox/sample-requirements.md --workspace workspaces/example
```

Create provider items:

```bash
workforge create workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --provider trello --execute
```

Check provider credentials and workspace configuration:

```bash
workforge providers test --workspace workspaces/example --provider trello
```

## Workspace Layout

```txt
workspaces/<name>/
  workforge.yaml
  .env.example
  inbox/
  output/
```

Workspace `.env` files are intentionally local-only. Commit `.env.example`, not
`.env`.

Environment variables are scoped to the selected workspace at runtime. WorkForge
reads `workspaces/<name>/.env` into an in-memory runtime object and passes those
values to the selected provider. It does not load workspace credentials into the
global process environment, which keeps simultaneous workspace runs isolated.

## Input Format

The initial parser accepts Markdown sections with optional tasks:

```md
## Clarify customer data collection

Source: shopify_review
Priority: high
Labels: compliance, required

Shopify asked us to explain what customer data is collected and why.

- Review current privacy copy
- Add explicit customer data disclosure
- Validate wording against Shopify review requirements
```

Each `##` section becomes one provider-neutral requirement.

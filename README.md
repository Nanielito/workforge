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

## Versioning

WorkForge uses semantic versioning.

- Patch releases fix bugs without changing commands or output contracts.
- Minor releases add backward-compatible commands, providers, or output files.
- Major releases may change CLI behavior, provider contracts, or saved output
  formats.

The first stable Trello workflow release should be tagged as `v1.0.0` once the
Trello create/status/agent-context/complete-task flow is merged and CI is green.

## CI

GitHub Actions runs on pull requests and pushes to `main`.

- Tests run on Python 3.11, 3.12, and 3.13.
- The package build is validated with `python -m build`.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

Create a project-local workspace:

```bash
workforge init .workforge --name linkealo --provider trello --namespace linkealo/shopify
```

Then add the printed entries to the host project's `.gitignore`:

```gitignore
.workforge/.env
.workforge/output/
```

Preview requirements from a workspace inbox file:

```bash
workforge preview workspaces/example/inbox/sample-requirements.md --workspace workspaces/example
```

Save preview output next to the workspace:

```bash
workforge preview workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --save
```

Create provider items:

```bash
workforge create workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --provider trello --execute
```

Save created provider items:

```bash
workforge create workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --provider trello --execute --save
```

Check provider card status from saved `cards.json`:

```bash
workforge status workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --save
```

Generate implementation context for an agent:

```bash
workforge agent-context workspaces/example/inbox/sample-requirements.md --workspace workspaces/example --save
```

Mark a provider checklist task as complete:

```bash
workforge complete-task workspaces/example/inbox/sample-requirements.md \
  --workspace workspaces/example \
  --card "Fix UI" \
  --task "Add explicit customer data disclosure"
```

`--card` accepts a card ID, exact title, or unique title substring. `--task`
accepts a checklist item ID, exact title, or unique title substring. By default,
WorkForge refreshes `status.json` and `agent-context.md` after completing the
task.

Check provider credentials and workspace configuration:

```bash
workforge providers test --workspace workspaces/example --provider trello
```

## Workspace Layout

```txt
<workspace>/
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

## Workspace Modes

WorkForge supports two workspace styles.

Central workspaces live inside this repository:

```txt
workspaces/example/
```

Project-local workspaces live inside the repository that the agent will modify:

```txt
some-project/
  .workforge/
    workforge.yaml
    .env.example
    inbox/
    output/
```

Project-local workspaces are recommended when generating agent context for an
implementation task because `agent-context.md`, `status.json`, and `cards.json`
stay close to the code being changed.

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

## Output Files

Saved output is grouped by input filename under the selected workspace:

```txt
workspaces/<name>/
  inbox/
    shopify-feedback-app-review.md
  output/
    shopify-feedback-app-review/
      preview.json
      cards.json
      status.json
      agent-context.md
```

`preview.json` contains the provider-neutral requirements parsed from the input.
`cards.json` contains the items created by the selected provider, including IDs
and URLs when the provider returns them.
`status.json` contains the live provider status for saved cards and checklists.
`agent-context.md` turns that status into implementation-ready context with
pending and completed tasks.

## Trello Labels

Labels in Markdown are logical names. To attach real Trello labels to cards,
map those logical names to Trello label IDs in the workspace config:

```yaml
providers:
  trello:
    list_id: "trello-list-id"
    labels:
      shopify-review: "trello-label-id"
      compliance: "trello-label-id"
```

WorkForge sends mapped labels as `idLabels` when creating Trello cards. Unmapped
labels are ignored by the Trello provider.

WorkForge does not create Trello labels yet. Create or rename labels in Trello
first, then paste their IDs into `workforge.yaml`.

To create a label through the Trello API:

```bash
curl --request POST \
  --url "https://api.trello.com/1/labels?name=shopify-review&color=blue&idBoard=TRELLO_BOARD_ID&key=$TRELLO_API_KEY&token=$TRELLO_API_TOKEN"
```

To rename an existing label:

```bash
curl --request PUT \
  --url "https://api.trello.com/1/labels/TRELLO_LABEL_ID?name=shopify-review&key=$TRELLO_API_KEY&token=$TRELLO_API_TOKEN"
```

To list labels for a board:

```bash
curl "https://api.trello.com/1/boards/TRELLO_BOARD_ID/labels?fields=id,name,color&key=$TRELLO_API_KEY&token=$TRELLO_API_TOKEN"
```

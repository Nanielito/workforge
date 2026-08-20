# WorkForge

WorkForge turns raw work inputs into structured planning items, then sends them
to planning providers such as Trello and GitHub Projects.

The core model is provider-neutral so the same requirements can become Trello
cards or GitHub Issues attached to a Project v2.

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

`v1.0.0` is the stable Trello workflow release. The provider-neutral item
terminology and GitHub Projects provider require a major release because they
change saved output and CLI command names.

Releases are created manually from the `Release` GitHub Actions workflow on
`main`. The workflow updates the version and changelog, runs the test suite,
builds and validates the wheel and source distribution, creates the Git tag,
and attaches both distributions to a GitHub Release. To create the first stable
release from `0.1.0`, run it with the `major` bump.

GitHub Packages does not provide a Python package index. The GitHub Release is
therefore the initial distribution channel; publishing to PyPI or a private
Python index can be added later if installation through `pip` is required.

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
workforge preview workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example
```

Save preview output next to the workspace:

```bash
workforge preview workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --save
```

Create provider items:

```bash
workforge create workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --provider trello --execute
```

Save created provider items:

```bash
workforge create workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --provider trello --execute --save
```

Discover existing provider items by label and rebuild `items.json`:

```bash
workforge discover workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --provider trello --label shopify --save
```

Check provider item status from saved `items.json`:

```bash
workforge status workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --save
```

Generate implementation context for an agent:

```bash
workforge agent-context workspaces/trello-example/inbox/sample-requirements.md --workspace workspaces/trello-example --save
```

Generate implementation context for one item:

```bash
workforge item-context workspaces/trello-example/inbox/sample-requirements.md \
  --workspace workspaces/trello-example \
  --item "Fix UI" \
  --save
```

Mark a provider checklist task as complete:

```bash
workforge complete-task workspaces/trello-example/inbox/sample-requirements.md \
  --workspace workspaces/trello-example \
  --item "Fix UI" \
  --task "Add explicit customer data disclosure"
```

`--item` accepts an item ID, exact title, or unique title substring. `--task`
accepts a checklist item ID, exact title, or unique title substring. By default,
WorkForge refreshes `status.json` and `agent-context.md` after completing the
task.

Add an implementation comment to a provider item:

```bash
workforge comment-item workspaces/trello-example/inbox/sample-requirements.md \
  --workspace workspaces/trello-example \
  --item "Fix UI" \
  --text "Started implementation from WorkForge agent context."
```

Move a provider item to another list or workflow column:

```bash
workforge move-item workspaces/trello-example/inbox/sample-requirements.md \
  --workspace workspaces/trello-example \
  --item "Fix UI" \
  --status doing
```

For Trello, `--status` accepts a Trello list ID or a configured logical list name.
By default, WorkForge refreshes `status.json` and `agent-context.md` after
commenting or moving an item.

Check provider credentials and workspace configuration:

```bash
workforge providers test --workspace workspaces/trello-example --provider trello
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

Shared example workspaces live inside this repository:

```txt
workspaces/trello-example/
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
implementation task because `agent-context.md`, `status.json`, and `items.json`
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
      items.json
      status.json
      agent-context.md
      items/
        fix-ui-operativa-post-instalacion.md
```

`preview.json` contains the provider-neutral requirements parsed from the input.
`items.json` contains the items created by the selected provider, including IDs
and URLs when the provider returns them.
`status.json` contains the live provider status for saved items and tasks.
`agent-context.md` turns that status into implementation-ready context with
pending and completed tasks.
`items/*.md` contains focused implementation context for a single provider item.

## Discovering Existing Items

Project-local workspaces can stay ignored by Git. To rebuild local tracking
files after cloning a project, discover items from the planning provider:

```bash
workforge discover .workforge/inbox/shopify-feedback-app-review.md \
  --workspace .workforge \
  --provider trello \
  --label shopify \
  --save
```

This writes:

```txt
.workforge/output/shopify-feedback-app-review/items.json
```

Then refresh status and agent context:

```bash
workforge status .workforge/inbox/shopify-feedback-app-review.md --workspace .workforge --save
workforge agent-context .workforge/inbox/shopify-feedback-app-review.md --workspace .workforge --save
workforge item-context .workforge/inbox/shopify-feedback-app-review.md --workspace .workforge --item "Fix UI" --save
```

For Trello, `--label` accepts a configured logical label name, a Trello label
ID, or a Trello label name. Logical labels are read from `workforge.yaml`:

```yaml
providers:
  trello:
    list_id: "trello-list-id"
    lists:
      todo: "trello-todo-list-id"
      doing: "trello-doing-list-id"
      done: "trello-done-list-id"
    labels:
      shopify: "trello-label-id"
```

## GitHub Projects

The GitHub provider supports Projects v2 owned by a personal account. It creates
repository Issues, renders requirement tasks as GitHub checkboxes, and adds each
Issue to the configured Project.

```yaml
providers:
  github:
    owner: github-user
    repository: repository-name
    project_number: 1
    labels:
      feature: enhancement
    status:
      field: Status
      values:
        todo: Todo
        doing: In Progress
        done: Done
```

Store a token with Issues and Projects read/write access in the workspace `.env`:

```dotenv
GITHUB_TOKEN=
```

Verify access without modifying GitHub:

```bash
workforge providers test --workspace .workforge --provider github
```

GitHub labels and Status options must already exist. Logical labels and status
aliases map to their GitHub names through `workforge.yaml`; unmapped requirement
labels are ignored. Project workflows may independently close an Issue when its
Status moves to `Done`.

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

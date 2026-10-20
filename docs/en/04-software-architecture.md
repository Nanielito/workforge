# DOC-04 — Software architecture

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Drivers

- One workflow across different planning providers.
- Safe inspection before external mutations.
- Credentials isolated by project workspace.
- Stable CLI and saved-output contracts.
- Small adapters that can be tested without external services.
- Useful context for human contributors and automation agents.

## 2. Structural decision

WorkForge is one Python package with four responsibility areas:

```text
Markdown input
    │
    ▼
parser ──► provider-neutral models
               │
workspace ─────┤
               ▼
          CLI orchestration ──► provider adapter ──► remote planning API
               │
               └───────────────────────────────► local output artifacts
```

| Component | Responsibility |
| --- | --- |
| `config.py` | Load and validate one workspace plus its isolated environment |
| `core/parser.py` | Convert Markdown sections into `Requirement` models |
| `models.py` | Define provider-neutral input, output, and status contracts |
| `cli.py` | Orchestrate commands, effects, matching, output, and persistence |
| `providers/base.py` | Define the complete provider behavior contract |
| `providers/registry.py` | Select a concrete provider by configured name |
| `providers/*.py` | Translate neutral operations to one remote API |

The CLI depends on the neutral contract. Provider modules depend on neutral
models. Shared models and parser code do not depend on provider payloads.

## 3. Primary flows

### Requirement-first

```text
load workspace → parse Markdown → preview → explicit create → save items
```

### Provider-first

```text
load workspace → discover remote items → save items → read/mutate live state
```

### Task synchronization

```text
parse Markdown → exact-title match → preview task set → explicit provider update
```

`items.json` is the local index joining later commands to remote items. It is
not a cache of all provider state; status and tasks are fetched live.

## 4. Effect boundaries

| Operation | Local reads | Local writes | Remote reads | Remote writes |
| --- | ---: | ---: | ---: | ---: |
| `init` | Optional existing scaffold | Yes | No | No |
| `preview` | Yes | Optional | No | No |
| dry-run `create` | Yes | Optional | No | No |
| executed `create` | Yes | Optional | Yes | Yes |
| `providers test` | Yes | No | Yes | No |
| `discover` | Yes | Optional | Yes | No |
| `status` / context | Yes | Optional | Yes | No |
| preview `update` | Yes | No | No | No |
| executed mutations | Yes | Usually | Yes | Yes |

External authorization is a caller responsibility. WorkForge supplies dry-run
and preview boundaries but cannot infer organizational approval.

## 5. Trust boundaries

The following inputs are untrusted:

- Markdown requirements and workspace YAML;
- workspace `.env` values;
- saved JSON edited outside WorkForge;
- CLI references and comment text;
- every remote API response and error;
- provider titles and task text rendered into Markdown context.

Pydantic validates shared models. Provider adapters validate required
configuration, use bounded HTTP clients, and translate errors where necessary.
No credential is copied into the process-wide environment.

## 6. Managed content and ownership

WorkForge owns only the task representation defined by each provider design:
GitHub's `## Tasks` section, Jira's identified ADF task list, and Trello
checklists named `Tasks`. Synchronization may replace that managed area while
preserving unrelated descriptions, comments, fields, and checklists.

The planning provider remains authoritative for item state. Generated local
artifacts are disposable except when a user intentionally treats a requirement
document as versioned planning input.

## 7. Consistency and failure model

- Commands operate sequentially; there is no cross-item transaction.
- Multi-request creation may succeed partially.
- Retries are not universally idempotent and may create duplicates.
- Saved output is written only after the corresponding command reaches its save step.
- Item and task substring matching succeeds only when unique.
- Discovery is the recovery path when local item tracking is missing.

Provider-specific recovery details belong in each provider design.

## 8. Security

- Secrets live in workspace `.env`, not YAML or committed examples.
- Environment loading is local and does not mutate `os.environ`.
- Errors, tests, fixtures, and output must avoid tokens and authorization headers.
- Tests use mocked transports; live provider credentials are not test inputs.
- Preview and provider checks do not mutate remote planning systems.

## 9. Evolution rules

- A new provider implements the full contract and registry entry together.
- A new shared capability must be expressed provider-neutrally and implemented by every provider.
- A saved-format or CLI breaking change requires a major release and migration plan.
- Continuous synchronization, a database, or concurrent writes require a new architectural decision.

## 10. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial architecture reconstructed from WorkForge 2.5.x |


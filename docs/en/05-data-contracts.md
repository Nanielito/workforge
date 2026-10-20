# DOC-05 — Data contracts

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Conventions

- Public CLI names, options, workspace fields, and saved artifact fields are contracts.
- Omitted Pydantic fields use their documented defaults.
- Provider-specific configuration remains an open mapping validated by its adapter.
- JSON artifacts use model field names and UTF-8 text.
- Generated output is grouped by the stem of an input reference.

## 2. DAT-001 — Markdown requirement document

Each line beginning exactly with `## ` starts one requirement. Content before
the first requirement is ignored. Within a requirement, blank lines are
ignored and recognized metadata uses `Key: value` syntax.

| Input | Cardinality | Mapping |
| --- | --- | --- |
| `## Title` | Exactly one per section | `Requirement.title` |
| `Source:` | Zero or one effective value | `source`; workspace default when omitted |
| `Namespace:` | Zero or one effective value | `namespace`; workspace default when omitted |
| `Priority:` | Zero or one effective value | low, medium, high, urgent; otherwise medium |
| `Milestone:` | Zero or one effective value | provider-neutral logical milestone |
| `Labels:` | Zero or one effective value | comma-separated logical labels |
| `- Task` | Zero or more | ordered `WorkTask` entries |
| Other non-empty line | Zero or more | description joined with newlines |

Later occurrences of the same metadata key replace earlier ones. Markdown
checkbox syntax has no special parser meaning; tasks should use plain `- ` lines.

## 3. DAT-002 — Requirement and WorkTask

| Field | Type | Required | Default/rule |
| --- | --- | ---: | --- |
| `Requirement.title` | string | Yes | Section heading |
| `description` | string | No | Empty string |
| `source` | string | No | `manual` or workspace default |
| `namespace` | string | No | `default` or workspace default |
| `priority` | enum | No | `medium` |
| `milestone` | string/null | No | null |
| `labels` | list[string] | No | Empty list |
| `tasks` | list[WorkTask] | No | Empty list |
| `WorkTask.title` | string | Yes | Task text |
| `WorkTask.done` | boolean | No | false |

Source, namespace, and priority are planning metadata. Providers decide which
other fields have a remote representation.

## 4. DAT-003 — Workspace configuration

```yaml
name: my-project
default_provider: github
providers:
  github: {}
defaults:
  source: manual
  namespace: organization/repository
  dry_run: true
```

| Field | Type | Required | Default/rule |
| --- | --- | ---: | --- |
| `name` | string | Yes | Workspace identity |
| `default_provider` | string | No | `trello` |
| `providers` | map[string,map] | No | Empty map |
| `defaults.source` | string | No | `manual` |
| `defaults.namespace` | string | No | `default` |
| `defaults.dry_run` | boolean | No | true |

The adjacent `.env` is parsed into an in-memory string map and passed only to
the selected provider. `.env.example` documents keys without real values.

## 5. DAT-004 — CreatedItem

| Field | Type | Required | Description |
| --- | --- | ---: | --- |
| `provider` | string | Yes | Adapter name |
| `id` | string | Yes | Provider item identifier used by later operations |
| `url` | string/null | No | Human-facing provider URL |
| `title` | string | Yes | Item title used for display and exact matching |

`items.json` is a JSON array of `CreatedItem`. Loading filters entries to the
currently selected provider.

## 6. DAT-005 — ItemStatus and TaskStatus

| Field | Type | Required | Description |
| --- | --- | ---: | --- |
| `ItemStatus.provider` | string | Yes | Adapter name |
| `id` | string | Yes | Provider item identifier |
| `url` | string/null | No | Human-facing URL |
| `title` | string | Yes | Live or fallback title |
| `closed` | boolean | No | false when not reported closed |
| `tasks` | list[TaskStatus] | No | Managed task state |
| `TaskStatus.id` | string/null | No | Provider or deterministic task reference |
| `TaskStatus.title` | string | Yes | Task text |
| `TaskStatus.done` | boolean | No | false |

`completed_tasks` is a derived runtime count and is not serialized as a model field.

## 7. DAT-006 — Saved artifacts

For input reference `inbox/release.md`, artifacts live under
`output/release/`. Discovery without an input uses `--output-name`, defaulting
to `discovered`.

| Artifact | Producer | Contract |
| --- | --- | --- |
| `preview.json` | preview or dry-run create with `--save` | Array of Requirement objects |
| `items.json` | executed create or discovery with `--save` | Array of CreatedItem objects |
| `status.json` | status or refreshed mutation context | Array of live ItemStatus objects |
| `agent-context.md` | agent-context or refreshed mutation context | All items grouped by pending/completed tasks |
| `items/<slug>.md` | item-context | One item's focused implementation context |

Slugs are lowercase ASCII-like text derived from the title, with non-alphanumeric
runs replaced by `-`; an empty result becomes `item`.

## 8. Reference matching

| Target | Accepted matching |
| --- | --- |
| General item operations | ID, case-insensitive exact title, unique case-insensitive title substring |
| Requirement-to-item update | Case-insensitive exact title only |
| Managed task | Provider task ID, exact title, or unique substring |

Zero matches fail. Multiple exact or partial matches fail rather than selecting
an arbitrary item or task.

## 9. Compatibility

Within major version 2, existing fields and meanings must remain readable.
Additive optional fields may be introduced in a minor release. Renames,
removals, changed defaults, directory changes, or altered matching semantics
require explicit compatibility review and may require a major release.

## 10. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial input, model, workspace, and artifact contracts |


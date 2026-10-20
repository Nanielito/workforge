# DOC-03 — Use cases

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Actors

- **Maintainer:** configures a workspace and authorizes provider writes.
- **Contributor:** claims and progresses an existing planning item.
- **Automation agent:** consumes saved context and performs scoped work.
- **Planning provider:** stores remote items and is an untrusted external system.
- **Filesystem:** stores versioned requirements, local secrets, and generated artifacts.

## 2. Catalog

| ID | Use case | Requirements |
| --- | --- | --- |
| CU-001 | Initialize and validate a workspace | RF-001–003, RF-024, RF-042 |
| CU-002 | Preview and create items | RF-010–012, RF-020–024, RF-045 |
| CU-003 | Discover and continue existing items | RF-030–034, RNF-004 |
| CU-004 | Synchronize requirement tasks | RF-035–036 |
| CU-005 | Progress one tracked item | RF-032–034, RF-037–038 |
| CU-006 | Generate agent context | RF-032–034 |
| CU-007 | Diagnose configuration or provider failure | RF-023–024, RF-042–045, RNF-007 |

## 3. CU-001 — Initialize and validate a workspace

1. The maintainer runs `workforge init` with a provider and namespace.
2. WorkForge creates only missing scaffold files unless `--force` is used.
3. The maintainer copies `.env.example` to `.env` and supplies credentials.
4. `providers test` loads only that workspace and validates configuration and,
   where supported, remote access without mutation.

**Alternative:** invalid or missing configuration returns a useful failure; no planning item is changed.

## 4. CU-002 — Preview and create items

1. The maintainer writes one or more Markdown requirement sections.
2. `preview`, or dry-run `create`, emits provider-neutral requirements.
3. The maintainer reviews the title, metadata, description, and tasks.
4. An explicitly executed `create` sends each requirement to the selected provider.
5. With `--save`, WorkForge writes returned item IDs, titles, URLs, and provider names.

**Alternatives:** workspace dry-run prevents mutation; a provider failure stops the command. Multi-step provider creation may leave a recoverable partial remote item.

## 5. CU-003 — Discover and continue existing items

1. The contributor runs `discover` with optional label, assignee, or status filters.
2. The provider returns open items in its configured planning scope.
3. With `--save`, WorkForge creates `items.json` under the selected output name.
4. The contributor uses that output reference with status and mutation commands.

**Alternative:** discovery may be run again to rebuild local tracking; it does not recreate remote items.

## 6. CU-004 — Synchronize requirement tasks

1. The maintainer edits tasks in the requirement document.
2. `update` matches each requirement to one saved item by exact title.
3. Without `--execute`, WorkForge prints the proposed task list.
4. With `--execute`, the provider replaces only its managed task content.
5. Completion is retained for unchanged titles when the provider supports synchronization.

**Alternatives:** missing or duplicate exact titles fail before mutation; unmanaged provider content remains outside WorkForge ownership.

## 7. CU-005 — Progress one tracked item

1. The contributor selects an item by ID, exact title, or unique substring.
2. `claim-item` assigns it, commonly to `@me`.
3. `move-item` changes its provider status or list.
4. `comment-item` records an implementation note when needed.
5. After implementing and verifying one task, `complete-task` marks it done.
6. WorkForge refreshes saved status and agent context by default.

**Alternatives:** ambiguous item or task references fail without choosing one arbitrarily; provider workflows may reject unavailable transitions.

## 8. CU-006 — Generate agent context

1. WorkForge reads saved items and fetches their live provider status.
2. `agent-context` groups every item's pending and completed tasks.
3. `item-context` selects one item and emits focused implementation guidance.
4. With `--save`, the Markdown stays beside the related tracking artifacts.

## 9. CU-007 — Diagnose a failure

1. WorkForge validates workspace and provider inputs as early as the operation permits.
2. It reports the resource, field, or provider operation that failed.
3. It omits credentials and authorization material.
4. If a partial remote item exists, the error identifies a safe recovery target when available.

## 10. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial use cases for WorkForge 2.5.x |

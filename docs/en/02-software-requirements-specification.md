# DOC-02 — Software requirements specification

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Conventions

**MUST**, **MUST NOT**, **SHOULD**, and **MAY** express requirement strength.
IDs are stable. Provider-specific realizations are documented in the provider
designs rather than repeated here.

## 2. Workspace and parsing requirements

| ID | Requirement | Verification |
| --- | --- | --- |
| RF-001 | `init` MUST create a workspace configuration, credential template, contributor README, inbox, and output directory without overwriting existing files unless `--force` is set. | Unit |
| RF-002 | A workspace MUST load `workforge.yaml` and its local `.env` without mutating the process environment. | Unit |
| RF-003 | The selected provider MUST default to `default_provider` and MAY be overridden by the command. | Unit/integration |
| RF-010 | The parser MUST convert each `##` section into one `Requirement`. | Unit |
| RF-011 | It MUST recognize Source, Namespace, Priority, Milestone, Labels, description text, and `- Task` lines. | Unit |
| RF-012 | Missing source and namespace MUST use workspace defaults; unsupported priority values MUST normalize to `medium`. | Unit |

## 3. Safe execution requirements

| ID | Requirement | Verification |
| --- | --- | --- |
| RF-020 | `preview` MUST parse and print requirements without contacting a provider. | Unit/manual |
| RF-021 | `create` MUST avoid external writes when `--dry-run` is set or workspace `dry_run` is true without `--execute`. | Unit/integration |
| RF-022 | Executed creation MUST return provider-neutral `CreatedItem` values and MAY save them as `items.json`. | Provider tests |
| RF-023 | Provider configuration MUST be validated before the first mutation whenever the provider can validate it locally. | Provider tests |
| RF-024 | Credentials and authorization material MUST NOT appear in WorkForge-generated output, artifacts, fixtures, or translated errors. | Security tests/review |

## 4. Tracking and synchronization requirements

| ID | Requirement | Verification |
| --- | --- | --- |
| RF-030 | `discover` MUST return open provider items and MAY filter them by label, assignee, and status. | Provider tests |
| RF-031 | Saved discovery MUST create an `items.json` usable by status and mutation commands. | Unit/provider tests |
| RF-032 | `status` MUST map live provider state and managed tasks to provider-neutral `ItemStatus` values. | Provider tests |
| RF-033 | `agent-context` and `item-context` MUST distinguish pending and completed tasks. | Unit |
| RF-034 | Item references MUST accept an ID, exact title, or unique title substring and MUST reject ambiguous references. | Unit |
| RF-035 | `update` MUST match requirements to saved items by exact title and preview before mutation unless `--execute` is supplied. | Unit/provider tests |
| RF-036 | Task synchronization SHOULD retain completion for unchanged task titles and preserve unmanaged provider content. | Provider tests |
| RF-037 | `complete-task` MUST accept the provider task ID, exact title, or unique substring and MUST reject ambiguous references. | Provider tests |
| RF-038 | Successful item mutations SHOULD refresh saved status and agent context by default. | Unit/provider tests |

## 5. Provider requirements

| ID | Requirement | Verification |
| --- | --- | --- |
| RF-040 | Every provider MUST implement the complete `PlanningProvider` contract. | Type/registry review |
| RF-041 | Provider-specific identifiers and payloads MUST remain inside provider modules and configuration. | Architecture review |
| RF-042 | `check` MUST be read-only and return a provider-neutral result. | Provider tests |
| RF-043 | Network methods MUST use bounded timeouts. | Provider review/tests |
| RF-044 | Tests MUST inject `httpx.MockTransport` and MUST NOT call live services. | Test review |
| RF-045 | Partial creation failures MUST report enough non-secret information for recovery and MUST NOT silently claim success. | Provider tests |

## 6. Non-functional requirements

| ID | Category | Requirement | Verification |
| --- | --- | --- | --- |
| RNF-001 | Compatibility | CLI names, options, workspace fields, provider contracts, and saved artifacts MUST remain backward-compatible within major version 2. | Release review |
| RNF-002 | Portability | The package MUST support Python 3.11, 3.12, and 3.13. | CI |
| RNF-003 | Security | Workspace credentials MUST remain local and secret-safe. | Unit/provider tests |
| RNF-004 | Recoverability | Generated tracking artifacts SHOULD be rebuildable through discovery and live status. | Use-case review |
| RNF-005 | Maintainability | Shared code MUST remain provider-neutral and providers MUST use the common contract. | Architecture review |
| RNF-006 | Distribution | Releases MUST build valid wheel and source distributions before publication. | Release workflow |
| RNF-007 | Observability | Errors SHOULD identify the failing configuration or provider operation without revealing secrets. | Provider tests |

## 7. Draft conformance notes

The 2.5.x implementation has known gaps against this draft baseline:

- `init --provider jira` does not yet emit Jira-specific configuration or credential keys.
- Trello `providers test` validates required local values but does not verify remote access.
- Trello HTTP failure redaction does not yet have explicit token-leak regression coverage.

These notes are follow-up inputs, not exceptions to the requirements.

## 8. Traceability rules

- Every use case references its RF and RNF requirements.
- DOC-04 assigns responsibilities without redefining requirements.
- Every persistent or exchanged datum appears in DOC-05.
- Provider designs explain how RF-040 through RF-045 are realized.

## 9. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial requirements reconstructed from WorkForge 2.5.x |

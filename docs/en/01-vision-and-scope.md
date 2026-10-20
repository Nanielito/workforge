# DOC-01 — Vision and scope

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Purpose

Define the problem WorkForge solves, its users, current product boundary, and
principles. Testable commitments live in [DOC-02](02-software-requirements-specification.md).

## 2. Problem

Teams often describe work in Markdown but manage delivery in provider-specific
systems. Manually recreating issues, cards, task lists, status, and agent context
duplicates effort and makes automation depend on one provider.

## 3. Vision

WorkForge is a local-first CLI that turns readable requirements into
provider-neutral planning items and synchronizes their operational state with
Trello, GitHub Projects, and Jira.

**Current promise:** the same requirement and CLI workflow can be previewed,
created, discovered, inspected, and progressed without leaking provider concepts
into the shared domain or workspace artifacts.

## 4. Users

| Actor | Need |
| --- | --- |
| Maintainer | Turn reviewed requirements into provider items safely |
| Contributor | Claim an item, understand its tasks, and report progress |
| Automation agent | Consume stable context and complete tracked tasks |
| Team | Change planning providers without changing the requirement model |

## 5. Current scope

- Python 3.11+ CLI distributed through PyPI.
- Project-local or shared workspaces with isolated credentials.
- Markdown requirements with metadata and task lists.
- Preview before external writes.
- Trello, personal GitHub Projects v2, and Jira Cloud providers.
- Item creation, discovery, status, comments, assignment, movement, and task completion.
- Provider-neutral JSON and Markdown artifacts for local tracking and agent context.
- Task-list synchronization from requirements to existing items.

## 6. Out of scope

- Hosting a planning service, database, or credential store.
- Continuous synchronization, polling, or webhooks.
- Creating or administering provider projects, boards, workflows, fields, labels, or milestones.
- Guaranteeing atomic multi-request provider operations.
- Arbitrary bidirectional synchronization of provider content.
- Supporting multiple providers in one saved item set.
- Treating generated output as the remote source of truth.

## 7. Principles

1. Provider-neutral contracts before provider-specific behavior.
2. Preview before external mutation.
3. Credentials remain scoped to one workspace.
4. Remote provider state is authoritative; local output is recoverable tracking state.
5. Managed task content is changed narrowly; unrelated provider content is preserved.
6. Public CLI, configuration, and saved formats remain compatible within a major version.
7. New abstractions follow demonstrated provider needs.

## 8. Success indicators

- A contributor can initialize a workspace and validate its configured provider setup from its README.
- A reviewed requirement creates equivalent planning items across supported providers.
- Discovery can rebuild local item tracking after generated output is removed.
- Task completion updates only the intended managed task.
- Provider tests run without live external services or real credentials.
- Errors and artifacts do not expose workspace secrets.

## 9. Uncommitted future

Additional providers, organization-owned GitHub Projects, richer requirement
formats, continuous synchronization, and machine protocols require evidence and
an explicit contract change before adoption.

## 10. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial retrospective technical baseline |

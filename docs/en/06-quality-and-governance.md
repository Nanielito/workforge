# DOC-06 — Quality and governance

| Field | Value |
| --- | --- |
| Status | Draft |
| Version | 1.0.0 |
| Product target | WorkForge 2.5.x |
| Last updated | 2026-10-19 |

## 1. Strategy

WorkForge evolves through small provider-neutral capabilities implemented across
all providers. External writes require explicit authorization, and releases are
cut only from `main` after automated validation.

## 2. Definition of done

A product change is done when it:

- implements the requested behavior at the shared or provider boundary that owns it;
- preserves provider neutrality and public compatibility;
- validates configuration before effects where possible;
- includes the minimum observable tests proportional to risk;
- passes the focused tests and full local CI equivalent;
- updates affected README, contracts, provider designs, and examples;
- contains no credentials, unrelated files, or unverified claims;
- provides a PR-ready summary with risks and actual verification.

## 3. Test strategy

- Parser and model unit tests for provider-neutral behavior.
- Workspace tests for local configuration and environment isolation.
- CLI helper tests for matching, paths, artifacts, and generated context.
- Provider tests using `httpx.MockTransport` for requests, mapping, pagination, failures, ambiguity, and redaction.
- Full `pytest` execution on Python 3.11, 3.12, and 3.13 in CI.
- Wheel and source distribution build validation before release.

Live provider calls are excluded from automated tests. There is no percentage
coverage target; distinct effects, error branches, and contract changes require evidence.

## 4. Compatibility and versioning

- Patch releases fix behavior without changing public contracts.
- Minor releases add backward-compatible commands, capabilities, providers, or fields.
- Major releases may change CLI, workspace, provider, or saved-output contracts and require migration guidance.
- Release automation owns package version and generated changelog changes.
- Provider API changes that do not alter WorkForge's public contract may remain internal.

## 5. Documentation governance

1. English is canonical and Spanish is synchronized in the same change.
2. Both languages preserve identical IDs, statuses, versions, and normative meaning.
3. A behavior change reviews DOC-02, DOC-03, DOC-05, and the relevant provider design.
4. An architectural change reviews DOC-01, DOC-04, and whether an ADR is required.
5. Document history records normative changes, not typo-only corrections.
6. Approved documents are not silently rewritten to change past decisions.

## 6. ADR policy

An ADR is required for a durable decision that changes at least one of:

- provider-neutral boundaries;
- persistent workspace or artifact contracts;
- trust or credential boundaries;
- consistency and retry semantics;
- packaging or deployment model;
- a deliberately rejected architectural alternative likely to recur.

ADRs use `Proposed`, `Accepted`, `Rejected`, `Superseded`, or `Retired` and state
context, options, decision, consequences, validation, and review conditions.
Retrospective ADRs must say that they formalize an already implemented baseline.

## 7. Risks

| ID | Risk | Impact | Treatment |
| --- | --- | ---: | --- |
| RSK-001 | Provider behavior diverges behind a neutral command | High | Shared contract and cross-provider tests |
| RSK-002 | Partial external creation leaves duplicates on retry | High | Preview, explicit execution, recovery details, provider limits |
| RSK-003 | Credentials leak through HTTP errors or artifacts | High | Isolated env, translation/redaction tests, review |
| RSK-004 | Saved formats change without migration | High | DOC-05 and SemVer release gate |
| RSK-005 | Provider API changes break an adapter | Medium | Mocked contract tests plus explicit release verification |
| RSK-006 | Documentation translations drift | Medium | Same-change synchronization and stable IDs |
| RSK-007 | Generated output is mistaken for authoritative remote state | Medium | Live status reads and recoverability guidance |
| RSK-008 | CLI orchestration accumulates provider logic | Medium | Keep payload and API behavior inside provider modules |

## 8. Change process

1. Start from a scoped requirement or tracked issue.
2. Preview external planning changes before execution.
3. Claim the item and move it to `doing` when implementation begins.
4. Complete managed tasks only after their relevant verification passes.
5. Keep the issue open while the pull request is under review.
6. Let the merged pull request close the issue and project automation finalize status.

Operational details for agents and commits remain in `AGENTS.md`; this document
defines product-level quality and governance.

## 9. Review gates

- **Contract gate:** no undocumented CLI, workspace, model, or artifact change.
- **Provider gate:** every concrete provider satisfies the shared capability.
- **Security gate:** no secret-bearing output or fixture and no live test traffic.
- **Release gate:** tests, build, metadata verification, tag, and artifacts agree.
- **Documentation gate:** canonical and translated baselines remain synchronized.

## 10. Document history

| Version | Date | Change |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Initial quality and governance baseline |


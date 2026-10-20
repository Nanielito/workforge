# WorkForge technical documentation

This directory contains the normative technical baseline and supporting guides
for WorkForge.

[Documentación en español](es/README.md) · [English documentation](en/README.md)

## Baseline

| Field | Value |
| --- | --- |
| Documentation version | 1.0.0-draft |
| Product target | WorkForge 2.5.x |
| Canonical language | English; synchronized Spanish translation |
| Last synchronized | 2026-10-19 |

## Documentation map

| ID | English | Español | Purpose |
| --- | --- | --- | --- |
| DOC-01 | [Vision and scope](en/01-vision-and-scope.md) | [Visión y alcance](es/01-vision-y-alcance.md) | Problem, users, boundaries, and principles |
| DOC-02 | [Software requirements](en/02-software-requirements-specification.md) | [Especificación de requisitos](es/02-especificacion-de-requisitos.md) | Verifiable product behavior |
| DOC-03 | [Use cases](en/03-use-cases.md) | [Casos de uso](es/03-casos-de-uso.md) | Primary and alternative workflows |
| DOC-04 | [Software architecture](en/04-software-architecture.md) | [Arquitectura de software](es/04-arquitectura-de-software.md) | Components, flow, trust boundaries, and effects |
| DOC-05 | [Data contracts](en/05-data-contracts.md) | [Contratos de datos](es/05-contratos-de-datos.md) | Inputs, models, configuration, and saved artifacts |
| DOC-06 | [Quality and governance](en/06-quality-and-governance.md) | [Calidad y gobernanza](es/06-calidad-y-gobernanza.md) | Compatibility, testing, risks, and documentation rules |

Supporting references remain in English:

- [Distribution and release guide](distribution.md)
- [GitHub provider design](github-provider-design.md)
- [Jira provider design](jira-provider-design.md)
- [Trello provider design](trello-provider-design.md)

## Statuses

`Draft` → `In review` → `Approved` → `Superseded` or `Retired`.

## Rules

1. English is canonical; Spanish is synchronized in the same change.
2. Requirement, use-case, data, and risk IDs are stable and are not reused.
3. Behavior changes update every affected contract and use case.
4. Significant architectural changes require an ADR after the ADR catalog is established.
5. Markdown is the source of truth; generated formats are artifacts.


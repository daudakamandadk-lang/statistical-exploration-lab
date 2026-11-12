# Documentation

The lab currently supports structural profiling, field-role/type suggestions and
a separate legacy report renderer. Start with the selected investigation, then
open the component documentation for the result you are inspecting.

| Document | Purpose |
| --- | --- |
| [Inspection playground](../examples/inspect_table.py) | Run the first investigation one VS Code cell at a time |
| [Architecture](ARCHITECTURE.md) | Direct functions, optional recipes, evidence boundaries and separate presentation |
| [Build plan](BUILD_PLAN.md) | Current inspection work and how to choose the next reviewed component |
| [Contract](CONTRACT.md) | Profiling inputs, confirmed keys, findings, fingerprints and limits |
| [Typing](TYPING.md) | Role suggestions, sentinel choices, matching-table handoff and rationale |
| [Reporting](REPORTING.md) | Retained legacy renderer compatibility and output behavior |
| [Migration](MIGRATION.md) | Changes from the earlier 0.1 interfaces to the current 0.2 direction |
| [Status](STATUS.md) | Implemented components, current verification and historical evidence |
| [Contributing](../CONTRIBUTING.md) | Setup, playable chunks, explanation and verification |

## Preserved design references

| Reference | How to read it |
| --- | --- |
| [Workbench architecture, 2026-10-12](ARCHITECTURE.workbench-2026-10-12.md) | Verbatim earlier broad design; future ideas and historical claims |
| [Workbench build plan, 2026-10-12](BUILD_PLAN.workbench-2026-10-12.md) | Verbatim earlier implementation order; superseded by the current plan |
| [Reset-era architecture](ARCHITECTURE.reset-2026-10-12.md) | Earlier small-calculator/reset design |

These references remain available for context. They are not current feature
lists or automatic approval to implement later layers. After a break, read
Status and the current Build plan, then revisit the actual explanation of the
requested next calculation.

# Architecture

The current direction is a toolkit of independent components that a person
selects and combines for an investigation. Start with the data, the question and
the chosen fields. A universal automated pipeline is not required to use one
function.

The earlier broad workbench proposal is preserved in
[Workbench design reference](ARCHITECTURE.workbench-2026-10-12.md), alongside
the [reset-era reference](ARCHITECTURE.reset-2026-10-12.md). They preserve useful
ideas and history; their future layers and old status statements do not describe
what is currently implemented. This document and [Status](STATUS.md) describe
the current boundaries.

## Four responsibilities

| Responsibility | Purpose | Current position |
| --- | --- | --- |
| Direct functions | Accept explicit inputs, check their boundaries and return an inspectable result | Structural profiling and typing exist |
| Optional investigation recipes | Combine selected calls for a stated question or outcome | The table-inspection playground demonstrates this in ordinary Python |
| Shared result/storage conventions | Support reuse when several actual components need a common form | Existing dataclasses and detached dictionaries suffice for the present components; no registry exists |
| Presentation | Display supplied results without recalculating them | Retained legacy renderer only; new profile/typing display uses direct inspection |

The intended composition is:

```text
user chooses data + question + fields
                |
        selected direct function -----> inspect its result
                |
        optional selected next call --> inspect combined evidence
                |
        optional compatible view -----> display supplied evidence
```

These are responsibilities, not a request to create empty directories, routers,
registries or engine classes. A future component can use a small function before
a shared convention is justified by real use.

## What is implemented

### Structural profile and field contract

`profile_structure` accepts a DataFrame or dict-of-lists, optional declarations
and overrides, a gate policy and an optional confirmed `observation_key`.
It returns measured structure, field contracts, findings and a gate.

Candidate keys and `grain` are hints, not proof of the observation unit. Only a
caller-confirmed key supports key-failure stops; ordinary high-cardinality
measurements are not silently promoted to required keys. The explicit key may
contain one field or a composite.

Interpretations follow override > declared > inferred. Observed storage remains
a fact; disagreement becomes a finding. An explicit sentinel list, including
`[]`, is final. Profiling masks only explicitly selected sentinels on a copy.
See [Contract](CONTRACT.md).

### Semantic suggestions

`type_columns` accepts a non-stopped profile and the same unchanged table.
The data fingerprint checks that handoff. It returns field-role suggestions,
their rationale and provenance, plus sentinel candidates.

Inferred sentinel candidates are suggestions by default. Optional application
must be explicitly requested and cannot extend a declared/override list.
A type inferred from shape or cardinality is still an interpretation. The
caller can confirm a role or override it; neither action is a statistical test
or proof of meaning. See [Typing](TYPING.md).

### First selected investigation

[Inspect a table and choose its field roles](../examples/inspect_table.py) is a
playground with VS Code `# %%` cells. It makes the profile, gate, role choices and
typing calls visible. Its optional helper recipe is example-level composition,
not a new package orchestration framework. The data is artificial unless the
caller selects their own input.

### Retained presentation

`render_html` and `write_report` display a complete legacy report dictionary.
They cannot consume the new profile/typing dataclasses or their `to_dict()`
forms as a report. Do not add empty legacy sections to suggest missing
calculations happened. A later display adapter should be designed for the
actual selected results. See [Reporting](REPORTING.md).

## Evidence and failure boundaries

- Keep measured facts, inferred suggestions and confirmed choices distinct.
- A structural stop prevents the dependent typing call. A warning remains
  visible and needs interpretation; it does not certify data.
- Keep individual findings when combining results. A recipe must not erase a
  refusal, missing input, exclusion or assumption.
- `fingerprint` identifies a structural summary; `data_fingerprint` identifies
  the source table content and identity needed for handoff. They have different
  purposes. Neither proves source accuracy or representativeness.
- Result mappings are read-only. Use `to_dict()` for detached inspection and
  explicit reuse, rather than mutating evidence.
- Each new calculation declares its own accepted input, meaningful output and
  failure behavior. It must not load unrelated data, choose another method,
  write files or render HTML as a hidden side effect.

## Future statistical work

Probability calculations, descriptive summaries beyond current structure,
relationships, inference, distribution fitting, visualizations and
credit-specific components remain possible future work. A registry, catalogue
or broad engine is not a prerequisite to implementing one reviewed function.

Before inference, state the question, estimand and sampling/dependence design.
A method change must not silently change the question. Some results should be
descriptive-only or not estimable; bootstrap is not a universal repair and
confidence intervals must not silently become Bayesian credible intervals.
Distribution criteria such as AIC compare candidate support, not the probability
that a family is true. These cautions must be resolved when the relevant
calculation is requested, rather than implemented as automatic rules now.

A credit-risk project is an intended consumer of reusable lab functions. It
owns domain data, assumptions, interpretation and decisions; the lab does not
depend on credit logic. See [Build plan](BUILD_PLAN.md) for the current sequence
and [Contributing](../CONTRIBUTING.md) for the explanation/review process.

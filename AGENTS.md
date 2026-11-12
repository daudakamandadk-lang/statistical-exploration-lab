# Repository guidance

## Identity and current direction

`statistical-exploration-lab` is a standalone toolkit whose functions can be
selected and combined for a specific investigation. The current direction in
[Architecture](docs/ARCHITECTURE.md) follows the user's explicit request for
independent components, optional selected investigations and playable VS Code
chunks. Earlier workbench/reset designs remain historical references, not
mandatory prerequisites for every function.

Implemented components are `contract.py` (profiling and contracts),
`semantic_typer.py` (typing suggestions) and retained `reporting.py`
(`render_html`, `write_report`). The renderer requires a complete legacy report;
it neither calculates statistics nor accepts new profiles directly. Never claim
future calculators, registries, routers or plugins exist.

The lab has no credit-domain dependency. Consumers own their data, domain
interpretation and decisions. Generic technical documentation belongs here;
personal learning records stay with their owner. No user datasets are bundled
and no distribution license is declared.

## Component boundaries

- Prefer directly callable functions with explicit inputs, meaningful results
  and documented failures. The caller chooses fields and calculations.
- Optional recipes compose selected functions for a stated outcome. Keep their
  calls and assumptions visible; do not add an orchestration framework for the
  first example.
- Candidate keys and inferred semantic roles are suggestions. Only an explicit
  observation key justifies key-failure stops. Preserve declared/override
  choices, including an explicit empty sentinel list.
- Distinguish measured facts, inferred suggestions and human decisions. Pass
  matching data between dependent components and preserve their fingerprints.
- Keep presentation separate from calculation. Do not fabricate a legacy
  report to display a new result.
- Add shared results, storage, registries and broader engines when actual
  requested components need them. Do not create empty layers.
- Preserve the earlier deliberate full dependency stack unless requested
  otherwise; distinguish renderer internals from package dependencies.

## Explanation and authorization

Before implementing a new statistical calculation, require an explicit request
and a reviewed explanation of purpose, inputs/outputs, logic, assumptions, a
small worked example and failure boundaries. Correct gaps before adding the
smallest understood code. This applies to credit-specific calculations too.

The current requested change covers reviewed profiler/typer fixes, truthful
documentation and the first playground. It does not approve future statistics.
Explicit user requests can change the earlier build order; use the current
[Build plan](docs/BUILD_PLAN.md).

Tests support understanding; they do not establish it. Never invent learning
sign-off or treat assistant-written notes as approval. Keep actual explanation
evidence and personal learning questions in the owning private project. Do not
edit that project's documents as a side effect of lab work.

## Data, output and verification

- Never commit user datasets or generated reports. Label artificial inline
  examples and test fixtures clearly.
- Preserve renderer escaping, offline operation, supplied counts,
  skipped/unrequested distinctions and exact saved evidence.
- Keep rendering free of network requests and statistical recomputation.
  Write only to a new report directory; preserve prior outputs on failure.
- Test known answers and meaningful failure boundaries for changed components.
  Verify playable examples separately. Record actual checks; historical checks
  do not verify the current source.
- Preserve read-only result mappings and detached serialization. Fingerprints
  identify documented inputs; they do not establish source accuracy,
  representativeness or ownership.

Start with [README](README.md), [Status](docs/STATUS.md) and
[Contributing](CONTRIBUTING.md). Source work does not automatically authorize a
Git commit, push, GitHub change or publication. Follow the user's separate
explicit publication instructions when provided; do not ask again for an action
already authorized in the session.

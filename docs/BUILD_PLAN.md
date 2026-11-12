# Build plan

Build a useful, understood component for the question at hand. The current
direction allows direct calls and small selected investigations; it does not
require completing the earlier broad workbench first.

The prior sequence is preserved verbatim as
[Workbench build-plan reference](BUILD_PLAN.workbench-2026-10-12.md).
Its proposed registry, engines and inference layers are future options, not
implemented prerequisites.

## Current work

The next selected workflow reuses pandas and statsmodels for a generic
relationship investigation: explicit variable selection, numeric summaries,
OLS fit, row accounting and optional diagnostic views. See
[Investigation](INVESTIGATION.md). It is standalone lab work, not credit-risk
engine modeling. Reuse library algorithms and automate repeated workflow tasks;
retain the caller's choices and native library outputs.

1. **Make existing profiling and typing dependable.** Separate key suggestions
   from a confirmed observation key; validate role declarations and overrides;
   keep explicit sentinel lists final; make inferred sentinel masking opt-in;
   validate the unchanged-table handoff; keep results inspectable and read-only.
2. **Make the first investigation playable.** Use
   [Inspect a table and choose its field roles](../examples/inspect_table.py).
   Run its VS Code cells to inspect a table, view structural findings, choose
   roles and examine the resulting suggestions. Keep its optional recipe small
   and its calls visible. This is the selected current task.
3. **Verify and document actual behavior.** Check boundary failures as well as
   the worked example. Record checks in [Status](STATUS.md). Preserve legacy
   rendering; do not claim it accepts new results.

## Choose the next component

After reviewing the first investigation, request one concrete calculation or
outcome. Explain its inputs, output meaning, assumptions, tiny worked example
and failure boundaries before implementation. Possible later work includes
probabilities, distributions, descriptive summaries, relationships and visual
evidence; none is available merely because it appears in an older plan.

Use a directly callable function first. Add an optional recipe only when
combining selected functions helps a stated investigation. Introduce a common
result form, storage/registry or presentation adapter when real result reuse
requires it. Do not scaffold empty layers or manufacture legacy report data.

The credit-risk consumer can use understood lab components when needed; it
does not require the complete future catalogue. Domain conclusions and lending
logic stay with that consumer.

## Review loop

1. Request the next calculation and name the question it answers.
2. Explain purpose, accepted inputs, logic, assumptions, worked answer and
   failure boundaries.
3. Review gaps before code. Preserve actual personal learning records with
   their owner; never invent sign-off.
4. Implement the smallest requested part and meaningful checks.
5. Document its call, result meaning, limitations and any compatible examples.
6. Review presentation separately; it must preserve supplied evidence.

Tests support understanding, not approval. Source implementation and Git
publication are separate decisions; follow explicit publication instructions
when provided.

After a break, read [Status](STATUS.md), this plan and the actual explanation
record for the requested component. An archived design or a green test total
is not approval to start another feature.

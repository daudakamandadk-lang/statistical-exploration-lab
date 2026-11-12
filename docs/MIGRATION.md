# Migration to the component interfaces

The 0.2 direction exposes profiling and typing as selectable components.
The retained legacy report functions keep their separate input contract.
There is no restored old CSV-analysis CLI or installed `statistical-lab`
command. Start with [the inspection cells](../examples/inspect_table.py).

## Changes from the initial local profiler/typer

- **Confirm row keys explicitly.** Pass `observation_key="record_id"`, or a
  list/tuple for a composite key. `candidate_keys` and `grain` remain hints;
  high-cardinality measurements no longer justify key-conflict stops by
  themselves. Review code that relied on automatic grain enforcement.
- **Review role declarations.** Storage/semantic vocabulary and override inputs
  are validated. Correct misspelled/unsupported declarations rather than relying
  on a string silently passing through.
- **Choose sentinels deliberately.** `sentinel_candidates` are suggestions.
  Default typing does not mask inferred candidates. Explicit sentinel lists,
  including `[]`, are final. To apply guesses without a declared list, use
  `TyperPolicy(apply_inferred_sentinels=True)` deliberately; to confirm them,
  put the accepted list in profile overrides.
- **Keep the handoff unchanged.** Typing rejects stopped profiles and input
  inconsistent with `data_fingerprint`. Re-profile after changing values,
  index, dtypes or columns. The older structural `fingerprint` remains a
  summary identity, not a data-content guarantee.
- **Inspect rather than mutate results.** Mappings are read-only. Use
  `to_dict()` for detached inspection/reuse; re-run with explicit choices
  instead of modifying a returned contract or fact.

These changes intentionally strengthen boundaries and can change earlier typing
results, especially when legitimate negative values resembled sentinel tokens.

## Presentation and installation

`render_html`/`write_report` still require a complete legacy report dictionary.
Do not pass the new dataclasses or their dictionary forms directly. No new
correlation, statistical test or distribution calculation is supplied by this
revision.

The full earlier dependency stack remains declared. A renderer implementation
that internally uses only standard-library modules does not mean normal package
imports are dependency-free. Refresh the editable installation after metadata
changes. See [Contributing](../CONTRIBUTING.md), [Contract](CONTRACT.md) and
[Typing](TYPING.md) for the current calls and limits.

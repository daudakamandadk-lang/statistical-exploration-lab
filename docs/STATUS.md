# Status

**Current revision: 2026-11-12 — table inspection and field-role selection.**
The package contains structural profiling/contracts, semantic typing suggestions
and the retained offline legacy renderer. The current requested work improves
their boundaries and provides a playable inspection example. Statistical
calculators and the larger workbench remain future work.

| Component | Current position |
| --- | --- |
| `profile_structure` and contracts | Implemented; confirmed single/composite key, explicit choices and separate structural/data fingerprints |
| `type_columns` | Implemented; role rationale, sentinel candidates, opt-in inferred masking and matching-table validation |
| Result inspection | Read-only mappings with detached `to_dict()` conversion |
| `examples/inspect_table.py` | First selected investigation; VS Code cells and ordinary explicit composition |
| Offline renderer | Retained; complete legacy report dictionaries only |
| Probability/statistical calculations, new plots and inference | Not implemented |
| Registry, catalogue, broad engines and credit-specific components | Future options; not prerequisites for direct function use |

The current architecture is [component composition](ARCHITECTURE.md).
The [broad workbench design](ARCHITECTURE.workbench-2026-10-12.md) and
[earlier build plan](BUILD_PLAN.workbench-2026-10-12.md) are preserved as dated
references. Their historical status text must not be read as the current API.

## Current verification

Local checks on 2026-11-12 used CPython 3.14.8, pandas 3.0.6 and NumPy 2.5.3:

- 67 tests passed, including the retained renderer and new component-boundary
  and playground checks.
- The six-cell table-inspection example ran from start to finish.
- A 0.2.0 wheel built successfully. Current source and packaged behavior were
  checked separately from the earlier renderer-only reset.
- Active documentation links and current-file whitespace were checked.

These are local results for this revision. Check the repository's GitHub Actions
runs for a hosted result; the earlier public 0.1 run does not verify this rebuild.

No current learning sign-off is recorded by this document. The user requested
this composition work and reviewed behavior fixes; that does not imply approval
of future statistical calculations. Follow any separate explicit Git publication
instruction after verification.

## Historical checks

These are preserved records of the earlier local stages:

| Date | Recorded result | Scope |
| --- | --- | --- |
| 2026-10-12 | 21 contract/profiler tests plus 8 renderer tests passed | Initial profiling stage |
| 2026-10-13 | 17 typing tests; 46 total tests passed | Initial typer plus prior components |
| 2026-10-12 reset | Eight renderer/output tests, saved-evidence rendering and a wheel build were recorded | Renderer-only reset, before current dependencies and exports |

The full pandas, NumPy, SciPy, matplotlib and PyYAML dependency stack was an
explicit earlier user decision and remains declared. The reset-era observation
that a renderer-only package had no runtime dependencies no longer describes
normal package imports.

Historical checks do not establish behavior of the changed key, sentinel,
fingerprint or result-inspection interfaces, nor a new hosted CI result.

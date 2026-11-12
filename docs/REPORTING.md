# Reporting

The retained renderer displays evidence already calculated elsewhere. It has no
probability, distribution or correlation calculator.

## Current compatibility boundary

| Function | Behavior |
| --- | --- |
| `render_html(report, include_heatmaps=True)` | Return offline HTML from a complete legacy report dictionary |
| `write_report(report, output)` | Write that dictionary as JSON and render HTML in a new directory |

The supplied dictionary needs the earlier report structure: question,
observation/configuration, source, counts, distribution results, selected
relationships, group summaries, limitations and generation information.
The package has no runner that generates those calculations today.

A `StructureProfile`, `TypeProfile`, single probability or pair of arrays
cannot be passed directly to the renderer. Their `to_dict()` forms are useful
for inspection but are not legacy reports. Do not add empty sections to imply
missing calculations were performed. Use the playground's direct result
inspection for the new components.

The implementation uses standard-library modules. Normal imports of
`statistical_exploration_lab` also load profiling/typing, and the package keeps
its deliberately chosen pandas/NumPy/SciPy/matplotlib/PyYAML dependencies.

## Preserved presentation

- Overview, section navigation and folded distributions.
- Supplied Pearson/Spearman values side by side with usable/excluded counts.
- Optional coefficient maps that distinguish unrequested, skipped and
  same-field cells; a missing value never becomes zero or an invented one.
- Supplied categorical counts/percentages and group summaries.
- Escaped labels, complete configuration/evidence and offline HTML.

The caller owns the accuracy and compatibility of supplied evidence. The
renderer neither validates the statistical analysis nor recomputes it. Coefficient
color represents sign/magnitude, not statistical significance.

## Output behavior

The destination must not exist; prior reports are never overwritten.
`write_report` requires finite JSON values. Incompatible/incomplete dictionaries
may fail before output creation. If writing fails, cleanup attempts only the
files and directory created by that call.

Generated artifacts may reveal labels, source names, summaries and configuration
paths. Keep private results with their owner. The renderer fetches or copies no
dataset and makes no network requests.

## Later result presentation

Design an adapter or view when an actual selected calculation or investigation
needs it. Preserve its inputs, exclusions, assumptions, estimates and unavailable
states. A common result convention or registry can be introduced when real
reuse warrants it; neither must precede a small compatible view.

Keep calculation separate from presentation. The earlier broad registry-based
report proposal remains in the
[workbench reference](ARCHITECTURE.workbench-2026-10-12.md); it is future design,
not the active renderer's contract.

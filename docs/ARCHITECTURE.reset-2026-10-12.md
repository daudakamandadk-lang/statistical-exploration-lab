# Architecture

The toolkit will contain small statistical calculations that a person selects
and combines explicitly. It should be possible to explain one calculation
without first understanding a framework.

## Current implementation

The active package retains only `reporting.py` and the package exports for
`render_html` and `write_report`. The renderer displays an existing legacy
report dictionary. It performs no statistical calculations.

The previous CSV loader, configuration parser, analysis coordinator,
distribution/correlation calculators and command-line runner are outside the
active reset. No replacement calculators or execution framework exist yet.

## Planned component boundaries

| Component | Responsibility | State |
| --- | --- | --- |
| Individual calculator | Accept explicit inputs, validate its own boundaries and return one explained result | Planned |
| Caller | Choose the calculation and inputs, then explicitly combine results if needed | Planned usage pattern |
| Small report adapter | Convert selected calculator results into an agreed display form | Planned; no result format selected yet |
| Report renderer | Display supplied evidence and save an offline artifact | Retained; legacy report format only |

The intended flow is:

```text
chosen inputs -> one selected calculator -> its result
                                             |-> explicit reuse by another calculation
                                             `-> optional adapter -> offline presentation
```

Calculators and the adapter in this diagram are planned. Keeping the renderer
does not implement that flow.

## Calculator design

Start with an ordinary function for the requested concept. Agree on its input
form, output meaning and invalid-input behavior before writing code. Return
enough information to explain the result, without adding a universal result
object before one is needed.

A calculator should not discover fields, load a dataset, call unrelated
calculators, render HTML or write files. A caller can deliberately pass one
result into another calculation when the meanings and assumptions match.
There is no automatic composition or hidden selection of a statistical method.

Add a module only when its first reviewed calculation is requested. Do not
create empty topic packages, registries, routers, plugins or batch engines.
Dependencies should follow an actual calculation's requirements; no dependency
is needed merely to prepare for a future topic.

## Reporting boundary

Retain the useful Pearson/Spearman display, counts, skipped states and complete
evidence view. The renderer cannot turn a probability value into a report today:
it expects the earlier descriptive report structure.

After the first calculator is understood, agree on the smallest adapter needed
to show that result. Review which inputs, denominator, assumptions and failure
state the display must preserve. Avoid making the first calculation imitate a
large CSV report just to reuse the renderer.

See [Reporting](REPORTING.md) for the current API and
[Build plan](BUILD_PLAN.md) for implementation order.

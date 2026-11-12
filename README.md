# Statistical Exploration Lab

A Python toolkit for investigating data one component at a time. Choose your
data, question and fields, call the functions you need, then inspect and combine
their results. Optional investigation recipes can make a repeated task easier
while keeping the individual calls and choices visible.

**Available now:** structural profiling, declared field roles and semantic type
suggestions. An offline renderer is also retained for complete legacy reports;
it cannot render the new profile/typing results directly. Statistical tests,
probability calculations, distribution fitting and new result presentation are
future work.

The lab is standalone. A credit-risk project can use its components while
owning its data, domain interpretation and lending decisions separately.

## Try the first investigation

Open [Inspect a table and choose its field roles](examples/inspect_table.py) in
VS Code with the project's Python environment selected. Run its `# %%` cells
one at a time to inspect the input, profile its structure, choose field roles
and review suggestions. It uses a small artificial table by default; the cells
also show where to supply caller-owned data. No user dataset is bundled.

The functions work directly too:

```python
from statistical_exploration_lab import profile_structure, type_columns

table = {
    "record_id": ["r01", "r02", "r03", "r04"],
    "measurement": [1.2, 2.4, -1.0, 2.0],
    "group": ["A", "A", "B", "B"],
}
structure = profile_structure(
    table,
    observation_key="record_id",
    overrides={"measurement": {"semantic_type": "continuous", "sentinels": []}},
)
print(structure.gate.status, structure.facts)

if structure.gate.status != "stop":
    types = type_columns(structure, table)
    print(types.by_name()["measurement"])
```

Here `record_id` is an explicitly confirmed row key. The empty sentinel list
keeps `-1` as a legitimate measurement. Possible sentinel values and inferred
roles are labelled suggestions. Pass the same unchanged table from profiling
to typing.

## Choose a component

| Component | Input and result | Documentation |
| --- | --- | --- |
| `profile_structure` | Table and optional declarations/overrides/key → facts, contracts, findings and gate | [Contract](docs/CONTRACT.md) |
| `type_columns` | Non-stopped profile and the same table → role suggestions, sentinel candidates and rationale | [Typing](docs/TYPING.md) |
| `render_html`, `write_report` | Complete legacy report dictionary → offline HTML, or a new JSON/HTML directory | [Reporting](docs/REPORTING.md) |

The playground composes the first two calls explicitly. It does not calculate
correlations, run tests or manufacture a legacy report around their outputs.
Result mappings are read-only; `to_dict()` provides a detached form for
inspection and explicit reuse.

## Setup and development

Python 3.11+ is required. Follow [Contributing](CONTRIBUTING.md) for setup and
checks. The deliberately retained dependency stack includes pandas, NumPy,
SciPy, matplotlib and PyYAML. The renderer's implementation uses the standard
library, but normal package imports also load the profiling code.

Read [Architecture](docs/ARCHITECTURE.md) for component boundaries,
[Build plan](docs/BUILD_PLAN.md) for the next requested work and
[Status](docs/STATUS.md) for current limits and verification evidence. The
[documentation index](docs/README.md) links preserved earlier designs.
See [Migration](docs/MIGRATION.md) when updating code written against the initial
0.1 profiling/typing interfaces; there is no restored old analysis CLI.

New statistical calculations are explained and reviewed before implementation:
purpose, inputs, output meaning, assumptions, a worked example and failure
boundaries. Tests do not establish learning approval. Source changes and Git
publication are separate decisions; follow explicit publication instructions
when provided.

User datasets, generated reports, domain interpretations and individual learning
records belong with their owning project. No distribution license is declared.

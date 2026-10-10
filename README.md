# Statistical Exploration Lab

A small local lab for asking understandable questions about distributions and
relationships in one table. Version 0.1 produces descriptive calculations and an
offline HTML report you can open in a browser.

This is an independent public component. Its GitHub home is
[statistical-exploration-lab](https://github.com/daudakamandadk-lang/statistical-exploration-lab). It has
no dependency on the governed pipeline or a credit-risk engine. Private datasets
and domain-specific conclusions stay with the project that owns them. No datasets
are bundled here; demo observations are generated temporarily during execution.

## Start with a demo

Python 3.11 or newer is required. From this repository in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m statistical_exploration_lab --demo --output reports/demo
```

Open `reports/demo/report.html` in your browser and inspect the saved evidence in
`reports/demo/report.json`. The HTML window works offline. Use a new output folder
for each run: an existing destination is rejected to protect previous reports.

On Linux/macOS, use `.venv/bin/python` for the same commands. After installation,
the `statistical-lab` command is also available inside the environment.

## Explore your own table

Copy [examples/exploration.json](examples/exploration.json), give it one clear
question, then declare your input path, observation key and field roles. The input
path is relative to the configuration file's folder. The example therefore expects
a local `data/local/observations.csv` containing the named fields; that file is not
provided. Change the configuration to match your own table.

```powershell
.\.venv\Scripts\python.exe -m statistical_exploration_lab --config examples/exploration.json --output reports/my-analysis
```

Each run saves the exact configuration, source filename, byte count, SHA-256
fingerprint, row count, runtime information, calculation results and skipped
reasons. It does
not copy the source dataset into the report folder. Reports can still reveal
category values and summaries from your data; keep them local when the source is
private. Local data and reports are ignored by Git.

## What the engines do

| Engine | Question it answers |
| --- | --- |
| Input/configuration | Is this one table consistent with its declared grain, keys and field roles? |
| Distribution | What values, frequencies and spread does each declared field have? |
| Numeric relationships | Do selected numeric pairs move together linearly or by rank? |
| Categorical relationships | How do selected categories co-occur, and what is each row's percentage breakdown? |
| Group summaries | How does a selected numeric measure vary across a category's groups? |
| Reporting | What was calculated, which observations were usable, and what was skipped? |

Read [engine calculations and limits](docs/ENGINES.md) before interpreting results.
The HTML window contains readable tables and categorical frequency bars. An
interactive upload window and numeric scatter/histogram plotting are later work.
The first version has no joins, hypothesis tests, p-values, confidence intervals,
causal estimation, models or ETL orchestration. A report helps you formulate the
next question; an association does not establish its cause.

## Test and debug

Develop generic source, tests and documentation in this repository's checkout.
Temporary export/build snapshots in consuming projects are historical copies,
not development homes. Keep domain configurations and interpretations with the
consuming project. The editable installation above uses source from this checkout;
reinstall after changing dependency metadata or entry points. An environment
using a wheel needs a deliberate rebuild/reinstall to use a changed package.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests
```

Tests use generated small cases with known results. If a real result surprises
you, check field roles, row grain, usable counts, missing/nonfinite values and
minimum sample settings before changing a calculation. Reproduce the issue with
a tiny table you can calculate by hand.

The [configuration reference](docs/CONFIGURATION.md) explains every supported
setting. The [learning guide](docs/LEARNING_GUIDE.md) gives an ordered reading,
testing and return-after-a-break checklist. Dependencies are pandas and NumPy;
the project uses the Python standard library for its CLI, JSON and HTML reporting.

The [verification record](docs/VERIFICATION.md) records the 34 passing checks,
tested runtime and package build, plus the remaining browser-preview limitation.

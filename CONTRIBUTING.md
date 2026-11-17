# Contributing

Keep changes focused on a requested component, calculation, investigation recipe
or display behavior. Profiling and typing exist; the retained renderer accepts
legacy reports. See [Status](docs/STATUS.md) for current evidence.

## Explain before implementing

Before each new statistical calculation, review purpose, inputs/outputs, logic,
assumptions, a small worked example and failure boundaries. Implement the
smallest understood part. Tests support the explanation; they do not establish
understanding or replace the user's review.

Keep actual learning records with the owning private project. Never invent
approval. The user's current composition direction supersedes the earlier broad
build order; appearing in a design does not authorize a feature. See
[Architecture](docs/ARCHITECTURE.md) and [Build plan](docs/BUILD_PLAN.md).

## Local setup

Python 3.11+ is required. Reuse an existing `.venv` when available; otherwise
create one and install this checkout as editable:

```sh
# Linux / macOS
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m unittest discover -s tests -v
```

```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The full pandas, NumPy, SciPy, matplotlib and PyYAML stack was an explicit earlier
choice and remains declared. Although `reporting.py` uses the standard library
internally, normal package imports also load the profiler and require pandas.
Reinstall after changing package metadata.

## Play with a component

Open [the inspection playground](examples/inspect_table.py) in VS Code. Select
the project's `.venv` interpreter, then use **Run Cell** on its `# %%` blocks or
send selected lines to the Python interactive window. Its artificial example
does not require a user dataset. Edit its data/field choices to investigate
caller-owned data; keep files private and outside source control.

Keep examples ordinary Python: explicit input, visible calls, inspectable
results and small optional helper recipes. Honor structural stops before
typing and keep the same table between dependent calls. There is no installed
`statistical-lab` command or general configuration runner.

## Verification and output

Run focused checks for changed behavior and the package tests appropriate to
the change. Check gate failures, data handoff, explicit overrides and unchanged
input/result evidence when changing profiling or typing. Run the playground
separately; a test total alone does not verify its cells. Record actual checks
in [Status](docs/STATUS.md) without treating them as learning approval.

For renderer changes, verify supplied values, counts, skipped states, escaping
and prior-output preservation. Inspect HTML before claiming visual verification.
Use artificial evidence in tests; never commit user datasets or generated
reports. Reports must use a new output directory.

## Packaging and scope

With the environment activated:

```sh
python -m pip install build
python -m build
```

Build dependencies may need package-index access. Inspect package contents and
use a fresh environment when testing a wheel. Old renderer packaging and hosted
CI do not verify the current source.

Source changes, commits and publication are separate decisions. Git commits,
pushes and GitHub changes need an explicit instruction; follow that instruction
when provided. No distribution license is declared.

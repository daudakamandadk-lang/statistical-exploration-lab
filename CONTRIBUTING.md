# Contributing

Contributions should make a local descriptive analysis easier to reproduce and
interpret. Before proposing a calculation, describe its inputs, assumptions,
result schema, exclusions and numerical limits. Include an artificial example
with a known expected answer.

## Development environment

Follow the clone and environment commands in [README.md](README.md), then install
the package with `python -m pip install -e .` using that environment's Python.
An editable install picks up source changes from this checkout. Reinstall after
changing dependency metadata or command entry points. A wheel installation
requires a rebuild and reinstall to use changed code.

The commands below assume the virtual environment is activated. Alternatively,
replace `python` with `.venv/bin/python` on Linux/macOS or
`.\.venv\Scripts\python.exe` in Windows PowerShell.

To reproduce the dependency combination used by CI, install
`requirements-tested.txt` before the editable package, then run `python -m pip check`.
The package's declared compatibility ranges remain broader than those pins.

## Verify a change

```sh
python -m unittest discover -s tests -v
python -m statistical_exploration_lab --demo --output reports/contribution-check
```

Use a fresh output directory, open `report.html` and compare it with
`report.json`. Existing report destinations are intentionally rejected. Tests
use generated observations; do not add dataset files or generated reports.

For a bug fix, add a focused regression case for the trigger and failure boundary.
For a new calculation, cover a known answer, usable/excluded counts, empty or
small samples, constant values and relevant numerical limits. Report changes
must preserve HTML escaping, JSON evidence and prior-output protection.

## Build the package

```sh
python -m pip install build
python -m build
```

Builds use isolated build dependencies and may require package-index access.
Artifacts are written to ignored `dist/`. Install the built wheel into a fresh
environment, then run the tests and a demo there when reviewing packaging or
dependency changes. This distinguishes an installed package from an editable
checkout. See the [verification record](docs/VERIFICATION.md) for the environment
that has actually been checked.

## Review and release expectations

- Keep a change scoped to its stated behavior, with commands and results recorded
  in the pull request.
- Update [configuration](docs/CONFIGURATION.md) and [engines](docs/ENGINES.md) when
  public behavior or evidence changes. Update the [roadmap](docs/ROADMAP.md) only
  when implementation status changes.
- Preserve explicit field roles, key validation, source fingerprints and skipped
  reasons. Unsupported settings must be rejected rather than silently ignored.
- Keep reports self-contained and free of external script/resource requests.
- Use artificial data in issues and examples; inspect changed files and package
  contents for datasets, generated outputs and machine-specific paths.

Before a release, verify the version and metadata, test the wheel in a clean
environment, inspect a fresh report and record the tested dependency versions.
No distribution license is currently declared; resolve licensing before a
package release that grants reuse rights.

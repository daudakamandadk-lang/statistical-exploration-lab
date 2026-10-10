# Verification record

The initial **0.1.0** implementation was verified on **2026-10-10** with
**Python 3.14.6, pandas 3.0.6 and NumPy 2.5.3**.

| Check | Recorded result |
| --- | --- |
| Unit tests | All **34** checks passed |
| Packaging | Wheel built successfully with isolated setuptools build dependencies |
| Demo | Fresh JSON and offline HTML reports generated; temporary source observations removed after execution |
| Demo calculation | 12 observations, 11 usable numeric pairs and Spearman coefficient `1` |
| Supporting files | Python syntax, TOML metadata, example JSON and relative documentation links checked |

The tests cover known calculations, paired counts, missing/nonfinite/constant
values, typed categories, small groups, strict configuration, row keys, CSV
quoting/record widths, large-integer precision, HTML escaping, input preservation
and protection of existing reports.

HTML content and escaping have automated checks. Visual layout has not been
verified in an automated browser; inspect a fresh demo report locally after
presentation changes.

## Reproduce the checks

Install the package using [the quick start](../README.md#quick-start). With that
environment activated:

```sh
python -m unittest discover -s tests -v
python -m statistical_exploration_lab --demo --output reports/verification-demo
```

Alternatively, use `.venv/bin/python` on Linux/macOS or
`.\.venv\Scripts\python.exe` in Windows PowerShell. Choose a new output folder,
then open `report.html` and inspect the accompanying JSON. See
[Contributing](../CONTRIBUTING.md#build-the-package) for package-build commands.

The declared Python and dependency ranges are broader than this single recorded
environment. This record does not establish compatibility with every supported
combination, hosted CI success, large-data performance or features listed only
in the [roadmap](ROADMAP.md). A passing test suite verifies implementation
behavior, not the statistical validity of a user's data or interpretation.

## Continuous integration

The GitHub Actions workflow is configured to install the package with
`requirements-tested.txt`, check dependency consistency, run the unit tests and
build a wheel on Python 3.14. See
[workflow runs](https://github.com/daudakamandadk-lang/statistical-exploration-lab/actions/workflows/ci.yml)
for hosted results. Workflow configuration does not establish a passing run;
the dated local results above remain a separate record.

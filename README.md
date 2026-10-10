# Statistical Exploration Lab

[![CI](https://github.com/daudakamandadk-lang/statistical-exploration-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/daudakamandadk-lang/statistical-exploration-lab/actions/workflows/ci.yml)

Describe distributions and selected relationships in a local CSV, then inspect
the results in an offline report. Explicit field roles, row keys and usable
observation counts make each calculation traceable to its input.

Version **0.1.0** provides numeric and categorical summaries, Pearson and Spearman
correlation, contingency tables and numeric summaries by group. It runs locally
with Python 3.11+, pandas and NumPy. No datasets are bundled; the demo generates
temporary observations.

## Quick start

Clone the repository, create an environment and generate a demo report.

**Linux / macOS**

```sh
git clone https://github.com/daudakamandadk-lang/statistical-exploration-lab.git
cd statistical-exploration-lab
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m statistical_exploration_lab --demo --output reports/demo
```

**Windows PowerShell**

```powershell
git clone https://github.com/daudakamandadk-lang/statistical-exploration-lab.git
Set-Location statistical-exploration-lab
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m statistical_exploration_lab --demo --output reports/demo
```

Open `reports/demo/report.html` in a browser. The report needs no web server or
internet connection. `report.json` contains the underlying evidence. Choose a
new output directory for each run; an existing destination is rejected.

The `statistical-lab` command is also installed in the environment. The commands
above use the environment's Python directly, so activation is optional.

## Analyze your own CSV

Adapt [examples/exploration.json](examples/exploration.json) to your question,
CSV path, row grain, key columns and field roles. Its referenced input file is
not supplied. Run from the repository root, using the same environment:

```sh
# Linux / macOS
.venv/bin/python -m statistical_exploration_lab --config examples/exploration.json --output reports/my-analysis
```

```powershell
# Windows PowerShell
.\.venv\Scripts\python.exe -m statistical_exploration_lab --config examples/exploration.json --output reports/my-analysis
```

An input path is relative to the configuration file's directory. An output path
is relative to the command's working directory. See the
[configuration reference](docs/CONFIGURATION.md) for every supported setting.

| Field role | Behavior |
| --- | --- |
| Identifier | Preserved as text; combined key values must be present, nonblank and unique |
| Numeric | Parsed explicitly; invalid numeric text and integer precision loss stop the run |
| Categorical | Preserved as text, including labels such as `001` and `NA` |
| Excluded | Must be present but does not enter calculations |

Only empty CSV cells are treated as missing. Numeric calculations use finite
values; categorical pairs use complete observations. No values are imputed.

## Results and interpretation

| Calculation | Output |
| --- | --- |
| Numeric distribution | Counts, minimum, quartiles, median, maximum, mean and sample standard deviation |
| Categorical distribution | Counts and proportions among nonmissing observations |
| Numeric pair | Selected Pearson and/or average-tie-rank Spearman coefficients |
| Categorical pair | Contingency counts and percentages within each row category |
| Numeric measure by group | Counts, exclusions and descriptive statistics for each eligible group |

The HTML report includes tables, categorical frequency bars and skipped reasons.
Read each result's usable counts and denominator before interpreting it. Constant
fields, insufficient observations and numerical limits produce explicit skipped
results rather than invented coefficients.

Each configured run records the exact configuration, source filename, byte count,
SHA-256 fingerprint, row count and runtime versions. The fingerprint and analysis
come from the same source bytes. The source CSV is preserved and is not copied
into the report directory. Reports contain data-derived labels and summaries;
review them before sharing. Data and generated reports are ignored by Git.

This version does not fit probability distributions, perform hypothesis tests,
estimate uncertainty, infer causation or build predictive models. Numeric plots,
interactive controls, joins and filters are not implemented. The CSV is loaded
into memory; no large-data performance guarantee is made. See
[calculations and limits](docs/ENGINES.md) and the [roadmap](docs/ROADMAP.md).

## Documentation and development

- [Documentation index](docs/README.md): configuration, calculations and operational guidance.
- [Troubleshooting](docs/TROUBLESHOOTING.md): input errors, skipped results and report interpretation.
- [Contributing](CONTRIBUTING.md): editable installs, tests, package builds and change review.
- [Verification record](docs/VERIFICATION.md): tested runtime, 34 passing checks and verification limits.

Questions and reproducible issues can be filed in
[GitHub Issues](https://github.com/daudakamandadk-lang/statistical-exploration-lab/issues).
Use artificial observations in public examples. No distribution license has
been declared for this repository.

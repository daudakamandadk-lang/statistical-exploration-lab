# Engines: inputs, calculations and limits

The package separates input validation, descriptive calculations and reporting.
Version 0.1 follows this path:

```text
question + configuration + one CSV
              |
     validate roles and row keys
              |
  distributions + selected relationships
              |
    JSON evidence + offline HTML report
```

The lab reads one table and preserves it. It does not ingest a pipeline, repair
bad source values, change keys or join tables. Its descriptive calculations start
only after the input and configuration are accepted.

## Where each component lives

| File | Responsibility |
| --- | --- |
| [configuration.py](../src/statistical_exploration_lab/configuration.py) | Parse strict JSON and validate the declared analysis contract |
| [analysis.py](../src/statistical_exploration_lab/analysis.py) | Read the CSV, check row keys, preserve input evidence and coordinate selected engines |
| [distributions.py](../src/statistical_exploration_lab/distributions.py) | Describe individual numeric and categorical fields |
| [relationships.py](../src/statistical_exploration_lab/relationships.py) | Calculate selected numeric/categorical pairs and group summaries |
| [reporting.py](../src/statistical_exploration_lab/reporting.py) | Write JSON and the offline HTML window to a new folder |
| [cli.py](../src/statistical_exploration_lab/cli.py) | Select a configured run or temporary demo from command-line arguments |

The CLI coordinates a local exploration run. Calculation functions can also be
called directly with pandas objects; their accepted types are described below.

## Input and configuration

The runner validates version 1, supported keys, field roles and relationship
references. It loads a comma-separated UTF-8 CSV with explicit types, checks
unique/nonblank headers and record widths, and verifies every declared column.
Combined observation keys must be nonmissing, nonblank and unique. Identifier
and categorical fields remain strings; invalid numeric text stops the run.

Numeric engines use floating-point calculations. Integers that cannot be
represented exactly at that boundary are rejected rather than silently merged
or rounded; identifiers and categories preserve their separate declared roles.

The report records the source filename, byte count, SHA-256 fingerprint and row
count, plus the exact configuration and runtime information. Parsing and hashing
use the same byte snapshot. These identify the analysis input without copying the
source CSV into the report folder. Undeclared CSV columns do not enter calculations
and are recorded as ignored. Empty CSV cells are missing; literal text labels
such as `NA` are preserved. The full CSV is loaded into memory.

## Distributions

Numeric distributions describe each declared measure using finite values. Read
the total, usable, missing and nonfinite counts before the centre and spread.
Quartiles and the median use linear interpolation at position `(n - 1) * p` in
the sorted usable values. Standard deviation uses the sample convention (`ddof=1`)
and is unavailable with fewer than two finite values. With no finite values, the
result is skipped as `no_usable_values`. A statistic that exceeds floating-point
range is unavailable and flagged as `statistics_overflow`; inspect the retained
counts and other statistics rather than reading that value as zero.

Categorical distributions show category frequencies and the missing count. A
category's proportion divides its count by all nonmissing values in that field.
Categories retain first-occurrence order. These empirical summaries do not fit
theoretical probability models or test goodness of fit.

CSV categories are string labels. When engines are called directly with Python
values, accepted categories are strings, booleans, integers and finite floats
representable without conversion loss. Labels include their type so values such
as numeric `1` and string `"1"` cannot silently merge. Direct numeric inputs must
be real numbers in a pandas Series; numeric strings and booleans are rejected.

## Numeric relationships

Only selected numeric pairs are calculated. Both measurements must be finite in
the same row. Reported exclusions therefore belong to that pair, not automatically
to every analysis in the report.

| Method | Calculation | Meaning |
| --- | --- | --- |
| Pearson | Correlation of the paired numeric values | Direction and strength of linear association |
| Spearman | Pearson correlation of average ranks; ties receive average ranks | Direction and strength of monotonic association |

Both coefficients range from `-1` to `1` when defined. A perfectly increasing
straight line gives `1` for both; a decreasing line gives `-1`. A curved but
monotonic pattern can have stronger Spearman than Pearson correlation. A
nonmonotonic pattern may have weak coefficients while still containing structure.

A pair is skipped when it has too few usable rows or either field is constant.
Inspect the reason instead of interpreting an undefined coefficient as zero.
Extreme values can also produce an explicit `numerical_precision_limit` instead
of a trustworthy coefficient. Values are scaled before centering to reduce
overflow; coefficients are bounded to `[-1, 1]` for numerical roundoff. There are
no p-values, confidence intervals or significance labels. The lab uses
pandas/NumPy and implements rank correlation without a SciPy dependency. The
primary API references explain the underlying [Series correlation](https://pandas.pydata.org/docs/reference/api/pandas.Series.corr.html)
and [average-rank behaviour](https://pandas.pydata.org/docs/reference/api/pandas.Series.rank.html).

## Categorical relationships

For each selected pair, the contingency table counts complete rows in every
combination of categories. The first field determines rows and the second field
determines columns. A row percentage divides a cell count by the total count in
that row, then multiplies by 100. Row and column categories follow their first
occurrence among complete pairs.

For example, a row with counts `3` and `1` has row percentages `75%` and `25%`.
These answer how the second category is distributed within the first category;
they do not describe the share of the entire dataset. A pair below the configured
complete-row threshold is explicitly marked skipped, while its observed counts
and percentages remain available. No independence test is performed.

## Numeric group summaries

Each selected combination uses one categorical field to group rows and one
numeric field to summarize. It records group size, usable values and exclusions,
then describes finite measurements within each sufficiently large group.
Missing group labels cannot define a group and are counted separately. Groups
follow first-occurrence order. A group below the configured usable count retains
its counts and a skipped reason; its statistics are withheld. The top-level
result is skipped when no group has an eligible summary.

Comparing group means or medians is descriptive. Unequal sizes, outliers,
different missingness and other variables can change the comparison; this version
does not adjust for confounding or perform between-group hypothesis tests.

## Reporting

`report.json` preserves machine-readable evidence. `report.html` makes the
question, declared observation, distribution/relationship results, category
frequency bars, counts and skipped reasons readable together. It is a static
artifact that needs no web server or external resources. Text is HTML-escaped.

The report is an artifact of one run, not a live dashboard. Change the question or
configuration and run again into a fresh folder. Check the JSON when a displayed
value or count looks surprising. A demo source is generated in a temporary
directory, marked synthetic in the evidence and removed after the run.

## Scope and interpretation

The current component implements local CSV loading, strict configuration,
descriptive distributions, selected associations, group summaries and saved
reports. The test suite is for known calculations and failure cases; it does not
make an explored association causal or a dataset representative.

Joins, filters, fitted probability distributions, numeric scatter/histogram plots,
interactive controls, formal inference, causal estimation and models are not
implemented. Proposed extensions are listed separately in the [roadmap](ROADMAP.md).
Domain-specific measures and interpretation belong in their owning project.
Use [Troubleshooting](TROUBLESHOOTING.md) to investigate input errors, skipped
results and unexpected summaries.

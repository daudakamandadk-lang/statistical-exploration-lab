# Roadmap

This page distinguishes shipped behavior from proposed extensions. Proposed work
has no committed release date and is not available in the current package.

## Version 0.1.0

- One locally selected CSV, loaded into memory from a fingerprinted byte snapshot.
- Strict version 1 configuration, explicit field roles and unique observation keys.
- Numeric summaries, categorical counts and empirical proportions.
- Selected Pearson/Spearman pairs, contingency tables with row percentages and
  numeric summaries by category.
- Visible usable/excluded counts, sample thresholds and skipped reasons.
- JSON evidence and self-contained HTML with tables and category frequency bars.
- A temporary generated demo and regression checks for calculations, validation
  and report preservation.

## Proposed investigation capabilities

| Area | Design questions to resolve before implementation |
| --- | --- |
| Numeric visualizations | Histogram binning, scatter selection, missingness, large samples and evidence shared with the JSON report |
| Event-probability summaries | Explicit event and denominator definitions, observation horizons, missing outcomes and uncertainty |
| Candidate distribution investigation | Supported distributions, parameter fitting, support constraints, diagnostics and comparison limits |
| Interactive exploration | Local data handling, selection state and reproducibility of saved evidence |

These additions should help users refine stated assumptions using observable
evidence. A frequency or fitted curve alone does not establish a population
probability, a causal relationship or a predictive decision rule.

Joins, source cleaning, ETL orchestration, formal inference and predictive models
are outside the current package. Their inclusion would require a separate scope
decision. Improvements to installation compatibility and verification should
state the environments actually checked, rather than imply coverage of every
allowed dependency combination.

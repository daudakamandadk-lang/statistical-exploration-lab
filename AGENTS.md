# AGENTS.md

## Project identity

This is `statistical-exploration-lab`, an independent, generic statistical
exploration component. Its public GitHub home is
[statistical-exploration-lab](https://github.com/daudakamandadk-lang/statistical-exploration-lab).
Public source hosting does not authorise publishing user datasets. No license
has been selected yet.

Keep this repository distinct from both `governed-data-pipeline` and the private
credit-risk project. Credit-risk datasets, generators, modelling, scoring and
domain-specific interpretation belong in the private project. ETL ingestion,
quality gates, watermarks and orchestration belong in the pipeline project.

## Current scope

Version 0.1 accepts one locally selected CSV with explicitly declared field roles.
It describes numeric/categorical distributions, selected Pearson/Spearman numeric
pairs, categorical contingency counts/row percentages and numeric group
summaries. It saves JSON evidence and an offline HTML report.

Keep each engine understandable and independently testable. This is a learning
component, so avoid premature plugin frameworks or production abstractions.
Inference, causal claims, models, joins, filters and ETL orchestration are outside
the current implementation.

## Data and evidence

- Never commit user datasets or generated reports. Generate demo/test observations
  at runtime in temporary directories; do not add dataset files to the repository.
- Preserve inputs. The runner reads the source and writes to a new output folder;
  an existing output destination is rejected.
- Configuration is strict version 1. Reject unknown keys, conflicting field roles,
  missing declared columns and invalid relationships. Preserve string IDs and
  verify nonmissing, unique observation keys.
- Use pairwise finite/complete observations, with no imputation. Explain usable
  counts, exclusions and skipped results alongside calculations.
- Save the exact configuration and input fingerprint. Do not add resolved
  absolute machine paths to source/report metadata or fetch external resources.
  Absolute input paths are supported, and exact user-provided configuration
  paths may be saved in ignored local reports.
- Report associations as descriptions, not causation or lending decisions.

## Working and returning after a break

Edit generic source, tests and documentation in this checkout. Temporary
export/build snapshots in consuming projects are historical copies, not
development homes. Consumers own domain configurations and interpretation;
do not maintain copied generic engines there. Editable installations use this
checkout's source; reinstall when dependency metadata or entry points change,
and deliberately rebuild/reinstall environments that use a wheel.

Start with [README.md](README.md), then [the learning guide](docs/LEARNING_GUIDE.md),
[configuration](docs/CONFIGURATION.md) and [engines](docs/ENGINES.md). Keep these
consistent with actual code and distinguish implemented behaviour from proposals.
Run `python -m unittest discover -s tests` after meaningful calculation, validation
or report changes. Check a fresh demo report and inspect skipped cases before
claiming the implementation is verified.

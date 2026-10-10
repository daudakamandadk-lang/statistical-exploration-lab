# AGENTS.md

## Project identity

`statistical-exploration-lab` is an independent package for descriptive
exploration of a locally selected table. Keep its implementation and documentation
generic. Consuming projects own their datasets, configurations and domain
interpretation. This repository contains no bundled datasets. No distribution
license has been selected.

## Supported scope

Version 0.1 accepts one local CSV with explicit field roles and observation keys.
It provides numeric/categorical summaries, selected Pearson/Spearman pairs,
categorical contingency counts and row percentages, numeric group summaries,
JSON evidence and an offline HTML report.

Keep validation, calculations and reporting independently testable. Do not
introduce fitted distributions, inference, models, joins, filters or interactive
controls without an explicit design, configuration contract and meaningful checks.
Do not describe planned behavior as implemented.

## Data and evidence

- Generate demo/test observations at runtime in temporary directories. Never
  commit user datasets or generated reports.
- Preserve inputs. Write only to a new output directory and reject an existing
  destination.
- Retain strict version 1 configuration validation: reject unknown or duplicate
  keys, conflicting field roles, missing declared columns and invalid selections.
- Preserve identifier and category strings, and reject missing, blank or duplicate
  combined observation keys.
- Use finite/complete observations with no imputation. Report usable counts,
  exclusions, denominators and skipped reasons beside calculations.
- Preserve the exact configuration and fingerprint the same bytes that are
  analyzed. Do not add resolved absolute machine paths to report metadata or
  fetch external resources. An absolute path explicitly supplied by a user may
  remain in that user's saved configuration.
- Describe associations without causal, predictive or domain decision claims.

## Development and verification

Edit package source, tests and documentation in this checkout. An editable
installation uses this source; reinstall after dependency or entry-point changes.
Rebuild and reinstall wheels deliberately when testing packaged behavior.

Use [CONTRIBUTING.md](CONTRIBUTING.md) for development commands and
[docs/README.md](docs/README.md) for the public documentation map. Keep
configuration and calculation references consistent with the implementation.
Run `python -m unittest discover -s tests` after meaningful validation,
calculation or reporting changes. Generate a fresh demo after report changes
and inspect its layout before claiming visual verification.

Record the environment and actual checks. A passing implementation test does
not establish representativeness, statistical significance or causal validity.

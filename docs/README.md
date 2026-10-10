# Documentation

Start with the [project README](../README.md) to install the package and generate
a demo. Then use the references below for a configured analysis or a code change.

| Document | Purpose |
| --- | --- |
| [Configuration](CONFIGURATION.md) | Version 1 schema, field roles, input semantics and output paths |
| [Engines](ENGINES.md) | Calculation definitions, exclusions, numerical safeguards and report evidence |
| [Troubleshooting](TROUBLESHOOTING.md) | Diagnose rejected inputs, skipped results and unexpected summaries |
| [Verification](VERIFICATION.md) | Recorded checks, tested environment and verification boundaries |
| [Roadmap](ROADMAP.md) | Current functionality and proposed extensions |
| [Contributing](../CONTRIBUTING.md) | Development environment, tests, packaging and review expectations |

The [example configuration](../examples/exploration.json) includes every required
setting. It expects a locally supplied CSV; no dataset is included. Saved
configuration and report JSON preserve what a run requested and calculated.
Keep domain conclusions and sensitive observations with their owning project.

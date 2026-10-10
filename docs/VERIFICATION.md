# Local verification

Verified on **2026-10-10** using **Python 3.14.6, pandas 3.0.6 and NumPy 2.5.3**.

- All **34 unittest checks passed**. They cover known calculations, paired counts,
  missing/nonfinite/constant values, typed categories, small groups, strict
  configuration, keys, CSV quoting/record widths, large-integer precision,
  HTML escaping, report preservation and input preservation.
- The v0.1.0 wheel built successfully with isolated setuptools build dependencies.
- The demo generated a fresh JSON report and offline HTML window. Its temporary
  dataset was removed when the run ended; the demo has 12 observations and 11
  usable numeric pairs, with Spearman coefficient 1.
- Python syntax, TOML metadata, example JSON and relative documentation links
  were checked.

The browser automation helper failed during preview, so visual layout has not
been verified in an automated browser. HTML structure/content and escaping are
covered by tests. Open a fresh demo report to inspect the layout locally.

The project declares Python 3.11+ and compatible pandas/NumPy ranges; the local
result above covers one installed combination. Other combinations, hosted CI,
large datasets, inference and interactive upload are not verified here.

From the repository root after installation:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m statistical_exploration_lab --demo --output reports/verification-demo
```

Use a new output folder. Keep generated reports and source data local.

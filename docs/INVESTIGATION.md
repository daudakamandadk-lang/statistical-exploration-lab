# Library-backed relationship investigation

This is a generic statistical-lab workflow, not the private credit-risk engine
or a lending model. It organizes repeated investigation steps around existing
libraries. You choose the table, variables, preparation and statistical method.

## Install and try

Install this checkout with its optional regression dependencies:

```sh
python -m pip install -e ".[econometrics]"
python examples/investigate_relationship.py
```

Use the selected virtual environment's Python. Open
[the editable example](../examples/investigate_relationship.py) in VS Code and
run its six cells in order. It generates neutral artificial observations unless
you set `CSV_PATH`. Set the outcome, predictor names, row key, missing-row policy,
intercept, covariance method and t/normal reference explicitly. Imported CSV
identifiers remain text; only selected measurements are explicitly parsed.

The example returns a figure but does not save it. Set `SHOW_PLOTS=True` to
display it when running the whole script. The final expression displays it in
an interactive notebook window. No dataset or generated report is bundled.

## Three independent helpers

| Call | Existing implementation reused | Repeated work handled |
| --- | --- | --- |
| `summarize_numeric(data, columns)` | pandas `describe` | Select fields, validate numeric inputs, include total/missing counts |
| `fit_ols(data, outcome=..., predictors=..., missing=..., cov_type=...)` | statsmodels OLS and covariance/inference | Selected complete-row sample, row accounting, recorded choices/version/input fingerprint |
| `plot_ols_diagnostics(result)` | matplotlib and statsmodels Q-Q plotting | Residual/fitted and Q-Q views of the supplied fit; no refit or saving |

The OLS result exposes `.fitted`, the native statsmodels result. Use that directly
for another deliberate library operation rather than expanding this wrapper for
every library feature. `.coefficients(alpha=...)` arranges estimates, standard
errors, p-values and library confidence limits into a table. `.choices` is a
read-only record; the underlying library model remains mutable and is not a
frozen archive. Row positions are zero-based input positions, not index labels.

Missing summaries are per column. OLS `missing='drop'` uses complete observations
across only the selected outcome/predictors; unrelated missing fields do not
exclude rows. `missing='raise'` refuses missing selected values. No imputation,
categorical encoding, transformations or model selection happens automatically.

## Small worked example

For `x=[-2,-1,0,1,2]` and `y=[-3,-3,4,3,9]`, OLS with an intercept returns
intercept 2 and slope 3. The library performs the estimation. Choose `HC3` or
`nonrobust` covariance and `use_t` explicitly; these choices govern the reported
uncertainty, not the investigation's business meaning. Tests check the known
coefficients, chosen settings, exclusions and failure boundaries.

## Limits and deliberate decisions

Inputs must already be real numeric measurements. Text, boolean/complex fields,
infinity, nonrepresentable large integers, a rank-deficient design or insufficient
usable rows fail clearly. This helper deliberately requires positive residual
degrees of freedom. With an intercept, constant predictors are refused. Correct
the selected specification explicitly; there is no automatic fallback.

HC3 does not by itself address dependence between observations. Clustered,
time-series, panel, weighted or categorical/formula models are outside this first
helper. Use an appropriate direct library workflow for those questions. Plots do
not certify assumptions; a normal Q-Q view concerns residuals, not a requirement
that predictors have normal marginal distributions. Coefficients and p-values
alone do not establish causal effects or credit-risk validity.

No new legacy HTML report is manufactured. Inspect returned tables, model objects
and figures directly. Private data, domain interpretation and lending decisions
remain outside this standalone package.

## Library references

- [statsmodels OLS](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.html)
- [OLS fitting and covariance choices](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLS.fit.html)
- [Regression diagnostics](https://www.statsmodels.org/stable/diagnostic.html)

These libraries supply the statistical implementations. The lab supplies selected
workflow convenience and visible evidence; the caller supplies interpretation.

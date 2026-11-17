# Distribution and selected relationship investigations

These descriptive helpers reuse pandas quantiles and summaries, SciPy
correlations and matplotlib views. Use only numeric measurements you explicitly
select; a numeric category code does not become a measurement automatically.
Examples use artificial data. They do not implement fraud detection, causal
inference, survey inference, model selection or automatic cleaning.

## Distribution inspection

`inspect_distributions(data, columns, missing="exclude", fence_multiplier=1.5)`
returns counts, mean, sample SD, extremes, quartiles and IQR fences. Choose
`missing="raise"` to refuse missing selected values. Quartiles use pandas
linear interpolation. Fences are Q1 minus multiplier times IQR and Q3 plus
multiplier times IQR. Values strictly outside are flagged with original
zero-based row positions; duplicate index labels do not affect that identity.

For [1, 2, 3, 4, 100], Q1=2, Q3=4 and IQR=2. With multiplier 1.5 the fences
are -1 and 7, so original position 4 is flagged. The source remains unchanged.
Fewer than four valid observations or zero IQR produce an explicit unavailable
flagging status. This minimum is a workflow guard, not a reliability guarantee.
No observations yields missing summaries; one observation has no sample SD.
Infinity and precision-losing integer inputs are refused by the shared numeric
validation. Heavy tails, mixtures and skew can produce legitimate flags.

## Selected relationships

`inspect_relationships(data, [("x", "y")], method="pearson", missing="pairwise")`
returns only requested pairs with used/excluded counts and descriptive
coefficients. Choose Pearson for linear association or Spearman for monotonic
rank association; the caller chooses. No p-values or intervals are displayed.
Three complete observations are the helper's minimum; that does not establish
adequate sample size. Constant inputs and insufficient pairs have explicit
unavailable statuses. SciPy numerical warnings are retained beside coefficients.

For x=[1,2,3,4], y=[8,6,4,2], both coefficients equal -1. Missingness is handled
per requested pair, so different pairs may use different observations. Use the
existing shared-sample component first if you deliberately want common rows.
Such pairwise results are not promised to form a valid correlation matrix.
Duplicate/reversed pairs and self-pairs are refused. Selected numeric codes,
confounding, time trends and nonlinear patterns need investigator judgment.

## Views and sensitivity

`plot_distribution(data, result, field="x", bins=10)` returns a histogram and
empirical cumulative distribution. `plot_relationship(data, result, left="x",
right="y")` returns a scatterplot. Both require the unchanged fingerprinted
source, return figures without saving, and retain extreme observations.
Histogram bins are an explicit display choice. Dense scatterplots may overlap.

Run [the editable example](../examples/explore_measurements.py) to inspect an
artificial extreme observation, compare chosen coefficients, and examine a
deliberate alternative sample. Excluding a chosen row demonstrates sensitivity;
it does not justify deletion or select a preferred answer. Results contain
editable tables and creation-time choices; editing them does not update evidence.

## Research basis

- [NIST: detection and investigation of outliers](https://itl.nist.gov/div898/handbook/eda/section3/eda35h.htm)
- [NIST: boxplot fences](https://www.itl.nist.gov/div898/handbook/eda/section3/boxplot.htm)
- [pandas quantile interpolation](https://pandas.pydata.org/docs/reference/api/pandas.Series.quantile.html)
- [SciPy Pearson correlation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.pearsonr.html)
- [SciPy Spearman correlation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html)

These support flagging for review, visible sample handling and library reuse.
Normality tests, distribution fitting, group inference, repeated-observation
analysis and expanded model diagnostics remain later, separately scoped work.

# Selected grouped proportions

`summarize_binary` reuses pandas grouping and NumPy weighted averaging to
describe a caller-defined binary indicator. It does not choose indicators,
interpret codes, fit models or calculate survey confidence intervals.

## Choices and result

Call `summarize_binary(data, outcome="event", by="group", missing="exclude")`.
Use `by=None` for an overall result; pass `weight="weight"` only deliberately.
`eligible` optionally supplies one positional boolean per input row. Series
index labels are not used to align eligibility. Define eligibility from the
same unchanged table. Nonresponse/skip logic belongs in the caller's explicit
preparation; outcomes among eligible rows must be 0, 1 or missing.

The returned `.table` includes rows, eligible/ineligible counts, missing
outcomes, used observations, observed event counts, weight sum, proportion and
status. Counts are unweighted. Without weights, weight_sum equals used count.
A weight sum is not automatically a population count. `.choices` records the
selected fields, missing policy, eligible positions and library versions;
`.input_fingerprint` identifies the source. The result table is editable and
the evidence describes creation time only.

## Worked example

For outcomes [0, 1] and weights [1, 3], the weighted proportion is
`(0*1 + 1*3)/(1+3) = 0.75`, while the unweighted proportion is 0.5.
There are two respondents and one observed event, not four respondents.
Changing both weights by the same positive multiplier preserves the estimate.

## Boundaries

- `missing="raise"` refuses missing eligible outcomes; `"exclude"` reports
  and removes them from the denominator. Ineligible outcomes do not contribute.
- Missing group labels form a visible group; only observed groups are returned.
  No unused categorical levels or arbitrary group combinations are invented.
- Zero events with a usable denominator gives 0. No usable denominator gives
  a missing proportion and `not_estimable`. Empty grouped input gives no groups;
  empty overall input gives one unavailable row.
- Eligible weights must be real numeric, positive and finite. Missing, zero,
  negative or infinite eligible weights require review rather than silent removal.
- Select distinct fields for outcome, group and weight. Fingerprints require
  supported scalar values throughout the supplied analysis table.
- Weight meaning and population coverage are caller responsibilities. This
  helper provides descriptive point estimates only, with no significance test,
  effective sample size, causal interpretation or predictive probability.
- Missing group labels and small observed counts remain visible. The helper
  does not invent a minimum-count threshold or combine categories automatically.

See [the editable example](../examples/describe_groups.py). The credit-data
investigation motivated this helper, but domain data and reports remain local
to their owner. No source dataset or credit interpretation belongs in this API.

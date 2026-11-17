# Statistical Investigation Lab — wireframe and development map

**Status:** Proposed interface and capability roadmap, 2026-11-17. This document does not claim that all features below are implemented.

## Product boundary

The proposed public platform combines a **general-purpose Statistical Investigation Lab** with a separate **open, extensible Model Lab shell**. The statistical helpers are partially implemented; the screens and Model Lab shell are prototypes. The specialised Credit Risk Engine will later reuse the statistical foundation and build its own PD/LGD/EAD and econometric workflows. Do not embed credit-risk features in the public shell. The current Python repository is a composable toolkit, not a deployed interactive application.

## The four-screen interface

1. **Data Overview** — structure, data quality, sample/field roles, descriptive measures, missingness.
2. **Distribution Explorer** — shapes, candidate families, unusual observations, counts and transformations.
3. **Relationships & Tests** — associations, group comparisons, categorical methods, inference and subgroup analysis.
4. **Investigation Summary** — temporal/stability patterns, sensitivity, assumptions, evidence register and handoff.

A separate **Model Lab** page stays generic: selected data/evidence in; extensible configuration, estimation, diagnostics and results areas. Existing optional OLS functionality remains a reusable helper rather than a promise of a complete modelling platform.

Each screen shares: investigation setup, statistical measures and usable/excluded counts, relevant visual evidence, an explainable suggestion panel, and an investigation record. Unrun calculations must stay visibly unrun.

## The twenty investigation categories

Availability is measured against the development branch's documented v0.3.0 capabilities as of 2026-11-16. **Partial** means a subset is implemented, never the entire row.

| # | Home | Area | Key inputs and expected evidence | What hints could reveal | Availability |
|---|---|---|---|---|---|
| 1 | Overview | Data quality | Table, key, field roles; structure, types, completeness, duplicate keys, validity | Review questionable records and semantics | Partial: profiling/contracts |
| 2 | Overview | Central tendency | Numeric measures; mean, median, mode, trimmed/weighted mean | Sensitivity of typical values to extremes | Partial: pandas numeric summaries |
| 3 | Overview | Dispersion | Numeric measures; variance, SD, IQR, MAD, quantiles, CV when meaningful | Unusual spread and scale | Partial: quartiles, IQR, SD |
| 4 | Distributions | Distribution shape | Numeric field; histograms, ECDF, KDE, Q-Q, skewness/kurtosis | Skew, heavy tails, multiple peaks | Partial: histogram and ECDF |
| 5 | Distributions | Distribution fitting | Chosen candidate families; estimates, fit plots, AIC/BIC, calibrated tests as appropriate | Compare candidates, not declare truth | Proposed |
| 6 | Distributions | Outliers | Numeric field and explicit fence/robust rules | Legitimate extremes vs possible errors | Partial: review-only IQR flags |
| 7 | Relationships | Associations | Selected pairs; Pearson, Spearman, Kendall, scatter/heatmap | Linear, monotonic and hidden patterns | Partial: Pearson, Spearman, scatter |
| 8 | Relationships | Group comparisons | Group/outcome plus paired/independent design; relevant t/ANOVA/nonparametric tests | Differences with assumptions disclosed | Proposed |
| 9 | Relationships | Statistical inference | Explicit estimand/design; effect sizes, intervals, p-values, bootstrap/permutation if valid | Uncertainty and practical size | Partial: optional OLS library outputs |
| 10 | Overview | Sampling | Units, weights, groups and design; n, representation, power if justifiable | Coverage and representativeness | Partial: counts and row evidence |
| 11 | Summary | Time dependence | Time column, unit, frequency; ACF/PACF, rolling summaries, trends | Autocorrelation/seasonality | Proposed |
| 12 | Summary | Assumptions | Chosen statistical procedure and design; procedure-specific checks | Relevant assumptions not confirmed | Partial: OLS residual/Q-Q views |
| 13 | Overview | Missingness patterns | Fields/groups/time; missingness maps and conditional rates | Potentially systematic missingness | Partial: counts and confirmed sentinels |
| 14 | Relationships | Categorical analysis | Categorical pairs; counts, contingency, chi-square/Fisher, effect sizes | Sparse cells, category relationships | Partial: grouped binary descriptions |
| 15 | Distributions | Zeros and counts | Count field, zero interpretation; zero %, mean/variance, count-family diagnostics | Excess zeros, overdispersion | Proposed |
| 16 | Distributions | Transformations | Field, deliberate transformation; before/after views and provenance | Whether transform serves objective | Proposed; no automatic change |
| 17 | Summary | Population stability | Comparable periods/groups; quantile shifts, two-sample comparisons | Distribution change | Proposed |
| 18 | Relationships | Subgroups | Segment, outcome and weights/design; stratified summaries/plots | Aggregate patterns hiding subgroups | Partial: grouped descriptions |
| 19 | Summary | Sensitivity | Selected alternative specifications and samples | How findings change with exclusions | Partial: shared-sample comparison |
| 20 | Relationships | Multiple testing | Defined test family; Holm/BH/Bonferroni as appropriate | False discoveries from many tests | Proposed |

These are investigative questions, not automatic triggers for every dataset. For example, normality of predictors is not a general OLS requirement; formal regression diagnostics use a fitted specification and usually belong in the Model Lab.

## Common investigation contract

A future UI result should expose, where applicable:
- **Setup:** question, chosen fields, observation unit, filters, population, method, assumptions and exact/sampled mode.
- **Provenance:** source/version label and fingerprint, selected sample identity, code/library versions.
- **Counts:** eligible, usable and excluded observations, exclusion reasons and denominators.
- **Evidence:** result status (not run, running, complete, unavailable, failed, needs review), measures, figures, parameter choices, uncertainty and limitations.
- **Guidance:** observed finding, transparent rationale, possible next investigations and missing prerequisites, never an automatic model choice.
- **Decision:** separate analyst notes/decisions; never misrepresent an interpretation as a computed fact.

This is an interface target, not a statement that an implemented shared result schema already exists.

## Performance strategy

**Quick scan:** structure, types, missingness and inexpensive summaries. **Interactive:** user-selected distributions, correlations and groups. **Deep:** costly fitting, resampling or specialized tests only when a method has been separately reviewed and built. Display when an output is sampled/approximate, and define sampling so rare-event and tail conclusions are not overstated. Cache only when identical inputs, sample and relevant parameter choices are demonstrable; no caching is implemented by this proposal.

## Conservative assistant rules

- Link each hint to observed measures, assumptions and usable sample sizes.
- Distinguish fact, tentative interpretation and analyst decision.
- Suggest checks instead of pronouncing data/model invalid.
- Do not infer causal effects from associations or predictive Granger relationships.
- Never silently clean data, choose missing policies, discard outliers, transform variables, or pick models.
- Use a procedure-specific explanation of suitability; show unsupported/not-run states.
- Avoid a universal model-readiness pass/fail badge.

## Where this leaves the existing code

According to the development branch STATUS, v0.3.0 already contains profiling, typing, confirmed missing-value preparation, explicit complete-case selection, selected numeric/distribution/correlation descriptions and plots, grouped binary summaries, pandas numeric descriptions, optional statsmodels OLS and diagnostic views. A dated local verification reports **97 passing tests**. That is not proof that these prototype screens or the full twenty features run.

Safe next increments:

1. Add a self-contained, clearly **demo-only clickable four-screen wireframe**, preserving no connection to real input.
2. Review screen behavior with the user and refine the information architecture.
3. Connect a read-only Data Overview screen to existing profile/typing functions; preserve gate/status and chosen observation key.
4. Connect Distribution Explorer to implemented summaries, histogram/ECDF and IQR flags; show unavailable methods plainly.
5. Connect Relationships to chosen correlations, groups and sample accounting.
6. Design a shared evidence adapter only when actual results need to cross screens; do not fabricate legacy report dictionaries or store unsafe raw data.
7. Define a generic Model Lab extension contract and handoff; credit-risk specialisation stays in its separate project.
8. Review each **new statistical calculation** before writing it: purpose, accepted inputs, known-answer example, assumptions, result meaning and failure/test boundaries.

## Wireframe acceptance criteria

Four distinct investigation screens; accessible selectable cards and evidence pane; clear demo labels; no fictitious statistical execution; states for not-implemented/not-run; reproducible selected inputs; shared evidence language; generic Model Lab shell; no changes to current statistical algorithms. The prototype is not a production frontend or a substitute for validated calculations.

## Results reading view

Use [the question-led report](INVESTIGATION_REPORT.md) for implemented descriptive results. The four screens organize investigation choices; each result still needs a question, metric purpose, observation, interpretation, next step and limits. The prototype remains unconnected to calculations.

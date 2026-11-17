# Architecture

This is the governing design document for the rebuilt lab: a standalone,
reusable statistical workbench. It merges the architecture draft (v1) and the
inference layer addition into one flowing reference. **Nothing described here is
implemented yet** beyond the retained offline renderer noted at the end. Every
step is built systematically, documented as it goes, and reviewed together
before the next one starts.

How the work is ordered lives in [Build plan](BUILD_PLAN.md). The process rules
(explain before code, review each step, no commits or datasets) live in
`AGENTS.md` and [Contributing](../CONTRIBUTING.md) and are unchanged.

Phase 3 of the credit risk model uses this lab, but the lab does not depend on
credit logic. Credit-specific analysis plugs in as a separate pack
(section 8).

## 1. Purpose and principles

Seven principles govern the design:

1. **Profile first, decide second.** Every choice (which test, which plot,
   which flag) is a rule applied to a column's profile, not hardcoded per
   column.
2. **Facts, inferences and decisions stay separate.** Measured facts,
   rule-based guesses and human decisions are stored and labelled differently.
3. **Tests declare their own applicability.** Each test states what it accepts,
   so adding one means registering it, not rewiring the pipeline.
4. **Thresholds live in versioned config, not code.**
5. **Nothing is silent.** Disagreements become findings, and overrides are
   logged with who, why and when.
6. **Explainable by default.** Every test, plot and distribution carries a
   plain-language explanation, so a newcomer can learn from the output.
7. **Every estimate carries its uncertainty.** No bare numbers: a mean, a
   correlation or a default rate is always reported with an interval, a method
   and a sample size.

## 2. Architecture at a glance

| Layer | Job | Credit knowledge? |
|---|---|---|
| `core/` | Pure statistical functions (moments, tests, fits) | No |
| `contract/` | Builds the per-column contract from schema, data and overrides | No |
| `catalogue/` | Declared knowledge: distributions, tests, explanations | No |
| `engines/` | Univariate, bivariate and multivariate analysis, plus the dispatcher | No |
| `viz/` | Maps a profile to a plot specification | No |
| `registry/` | Stores every result with its fingerprints | No |
| `report/` | Renders from the registry and never recomputes | No |
| `credit/` | Plugin pack (WoE, IV, PSI, KS, leakage) | Yes |

The overall flow:

```text
 Declared schema    Observed data    Config, overrides
        \                |                /
         v               v               v
              Profile and contract          (ColumnProfile per column)
                        |
                      Gate                  (stop or warn if grain is broken)
                        |
   +--------------+-----+--------+----------------+
   |              |              |                |
Univariate     Bivariate    Multivariate     Credit pack (plugin)
   |              |              |                |
   +--------------+-----+--------+----------------+
                        |
                    Registry                (results + fingerprints)
                        |
        +---------------+----------------+
        |               |                |
    Findings       Decision log     Report and plots
```

Automation is allowed in these layers only because every automatic choice is
recorded as a traceable inference with its rule and evidence (principle 5):
the engine may choose, but never silently, and a human decision can always
override it in the decision log.

## 3. Inputs and the contract

### 3.1 The three inputs

- **Declared schema:** what your governance phase says the data should be
  (storage types, nullability, allowed ranges, known categories). It is
  human-authored intent.
- **Observed data:** what the lab *measures*: null counts, distinct values,
  min/max, skew, repeated spike values. It also includes rule-based guesses
  derived from those measurements. The dtype pandas assigns is only a weak
  hint, since `read_csv` guesses it.
- **Overrides:** your corrections where intent, inference and reality disagree.

### 3.2 Why the contract is its own layer

A data-engineering schema asks whether data is valid to store and move. The lab
contract asks how a column should be *analysed*. A schema can say `int` but
can't say "this int is really a category". If the lab read engineering schemas
directly, it could only run on data that came through your pipeline and would
stop being a general lab. So the lab owns a small contract format of its own.

### 3.3 How they link

A one-way adapter translates the declared schema into the lab's format. The lab
never imports from the engineering layer, so swapping schema formats means
writing a different adapter. If there's no schema, the lab infers everything.

```text
declared schema ──(adapter)──┐
observed data ───(inference)─┼──> draft contract ──(overrides win)──> final contract
```

The precedence rule has three parts:
- **Facts** (null %, cardinality, skew) come from observation only and are
  never overridden.
- **Interpretation** (semantic type, sentinels, level order): override beats
  declared, and declared beats inferred.
- **Disagreement** between declared and observed becomes a finding, never a
  silent fix.

### 3.4 Contract example with provenance

```yaml
columns:
  employment_status:
    storage_type: int            # source: declared
    semantic_type: nominal       # source: override (codes 1-5 are categories)
    sentinels: [-1]              # source: inferred
  monthly_income:
    storage_type: float          # source: declared
    semantic_type: continuous    # source: inferred
    sentinels: [-999]            # source: override
```

Your overrides are edits to this same file, versioned, with who, why and when
logged per field.

### 3.5 The estimand block — the inference counterpart of the contract

Beside the contract, a small `estimand` block in the config declares what the
inference is about *before* anything runs:

```yaml
inference:
  population: "applicants 2022-2024, through-the-door"   # what the sample represents
  unit: customer                                         # the grain
  cluster_key: customer_id                               # rows from one customer are not independent
  alpha: 0.05
  ci_level: 0.95
  smallest_effect_of_interest: {correlation: 0.1, cohens_d: 0.2, cramers_v: 0.1}
  seed: 20261012
```

Two items matter most. The cluster key stops the lab treating 24 monthly
snapshots of one customer as 24 independent observations, one of the most
common ways to produce falsely confident results. The smallest effect of
interest stops large samples from turning trivial differences into findings:
with hundreds of thousands of rows nearly everything is "significant", so a
finding fires only when the effect is both statistically detectable and larger
than this threshold.

## 4. Pipeline stages

**Stage 1: Structural profiler and gate.** Finds the grain of the table
(candidate keys, duplicate rows, duplicate keys with conflicting values), counts
rows and columns, and flags empty, constant and mixed-type columns. It stamps a
data fingerprint on the run. The gate then decides whether to stop or warn when
the structure is broken, because statistics on a table that doesn't mean what
you think it means are meaningless.
> *Note for users: Tells you what one row represents and stops the run if the table can't be trusted.*

**Stage 2: Semantic typer.** Decides how each column behaves:

| Condition | Inferred type |
|---|---|
| 1 unique value | constant |
| unique ratio ≥ ~95%, string or integer | ID candidate |
| 2 unique values | binary |
| parses as dates | date |
| numeric, few integer levels | ordinal/nominal candidate (confirm) |
| non-negative integer, many levels, right-skewed | count |
| float, many levels | continuous |
| string, high cardinality, long values | free text |

Sentinels (-999, "UNK") are masked first, otherwise they distort everything.
The output is a ColumnProfile per column.
> *Note for users: Classifies each column by how it behaves, so the right tests and charts are chosen automatically.*

**Stage 3: Univariate engines.**
- *Numeric:* moments, percentiles, median and MAD, zero share, outliers by IQR
  fence and modified z-score, shape label, and transform suggestions (never
  silent changes). Normality testing is used only at small n, because at
  credit-data sizes every test rejects, so skew, kurtosis and QQ plots are used
  instead.
- *Categorical:* frequencies, dominant-level share, rare levels, label hygiene
  ("Male" vs "male ").
- *Date:* range, gaps, future dates, volume per period.
- *Missingness:* percent, sentinel candidates, co-missingness.
- *Distribution matching:* described in section 5.

Every summary also carries its uncertainty (section 6): "median income 41,200
(95% CI 40,800–41,600), n = 118,432", not just the median.
> *Note for users: Describes each column on its own and flags anything suspicious.*

**Stage 4: Bivariate engine.** Routes by pair type, with assumption checks and
fallbacks:

| Pair | Default | Falls back to | Effect size |
|---|---|---|---|
| num–num | Pearson | Spearman (skew/outliers), Kendall (small n/ties) | r / ρ |
| cat–cat | Chi-square | Fisher, or merge rare levels | Cramér's V |
| num–binary | Welch t | Mann-Whitney | Hedges g / rank-biserial |
| num–cat (k groups) | Welch ANOVA | Kruskal-Wallis | η² / ε² |

The choice of method is an inference (principle 2): the engine may apply a
fallback, but the registry records which method ran, why the default was
rejected, and a decision-log entry can override it. Results are ranked by
effect size, not p-values (with large n everything is "significant"), and
Benjamini-Hochberg FDR control is applied across the many pairwise tests. A
finding fires only when the effect also clears the smallest effect of interest
from the estimand block, and each result carries a power note (section 6):
"no relationship" comes with "we could only have detected correlations above
0.15".
> *Note for users: Measures how pairs of columns relate and how strong the relationship is, using the method that fits their types.*

**Stage 5: Multivariate engine.** Builds a mixed-type association matrix,
clusters it to find redundancy groups (|ρ| > ~0.8), computes VIF and condition
number, and runs PCA for structure only.
> *Note for users: Finds groups of columns carrying the same information.*

**Stage 6: Visualization dispatcher.** Rules map the profile to a plot
specification (data, not a drawn picture), for example:

| Profile | Primary plot |
|---|---|
| Continuous, symmetric | Histogram + KDE, QQ plot |
| Continuous, skew > ~1 | Histogram on log scale |
| Zero-inflated | Share of zeros + histogram of the rest |
| Count | Bar by value |
| High-cardinality categorical | Top-N bar + "other" |
| num–num, large n | Hexbin / 2D density |
| cat–cat | Standardised-residual heatmap |

The dispatcher picks the standard informative chart for a profile the user has
already committed to analysing a certain way; it does not choose the analysis.
> *Note for users: Picks an informative chart for each column or pair automatically.*

**Stage 7: Registry and report.** Every result is a structured record: test id
and version, columns, assumption checks (pass/warn/fail), statistic, adjusted
p-value, effect size, interval and interval method, mode (exploratory or
confirmatory), sample size and cluster count, seed, data fingerprint, config
hash, code version, timestamp. The report renders only from the registry and
never recomputes. The full record shape is in section 6.
> *Note for users: Every number can be reproduced and audited.*

## 5. Distribution guide (the learning layer)

**Is this doable?** Yes, and it needs no new machinery. It uses the same
registry pattern as the tests: each probability distribution is a *declared
entry* in the catalogue, and a matcher compares each column's profile against
those entries.

### 5.1 What a catalogue entry contains

Each entry is a declared record with three explanation levels, so beginners and
experts both get what they need:

```yaml
lognormal:
  one_liner: "Positive values that grow by compounding percentages"
  story: >
    Appears when many small multiplicative effects stack up, so most values
    are modest and a few are very large.
  support: positive_continuous
  parameters:
    mu: "Typical size on the log scale (the median is e^mu)"
    sigma: "Spread on the log scale; larger means a heavier right tail"
  signature:                         # rules the matcher uses
    support: positive
    skew: "> 0.5"
    log_transform_skew: "close to 0"
  examples: [income, loan balance, transaction size]
  confirm: "QQ plot of log(x) is close to a straight line"
  implications:
    - "Mean exceeds median; report the median"
    - "Log-transform before Pearson-based methods, or use Spearman"
  confusable_with: [gamma, weibull]
  how_to_tell_apart: "Compare fit scores; log-skew near 0 favours lognormal"
  fit: fit_lognormal                 # code reference
  pdf: ...
  sample: ...
```

### 5.2 The matching flow

The matcher asks a short sequence of questions the profile can already answer,
which also works as a teaching device because it shows the reasoning:

```text
Discrete or continuous?
├─ Discrete
│   ├─ two values → Bernoulli
│   ├─ counts → variance ≈ mean? → Poisson
│   │           variance > mean? → negative binomial
│   │           far more zeros than expected? → zero-inflated version
│   └─ labelled categories → categorical (multinomial)
└─ Continuous
    ├─ bounded between 0 and 1 → beta (handle exact 0s and 1s separately)
    ├─ positive only
    │   ├─ right-skewed, log is symmetric → lognormal
    │   ├─ right-skewed, otherwise → gamma / Weibull
    │   └─ very heavy tail → Pareto (usually fits the tail only)
    └─ any real value
        ├─ symmetric, light tails → normal
        ├─ symmetric, heavy tails (high kurtosis) → Student-t
        └─ asymmetric → skew-normal
```

The support check comes first because it eliminates impossible families
immediately (a normal can't describe a strictly positive column well). The
remaining candidates are fitted by maximum likelihood and ranked by AIC/BIC,
not by p-values.

### 5.3 Confidence rules

The guide should be honest about uncertainty rather than always naming a
winner:

| Situation | Label |
|---|---|
| Best family beats the runner-up by ΔAIC > 10 and fit distance is acceptable | Strong match |
| ΔAIC between 2 and 10 | Moderate: runner-up also plausible |
| ΔAIC < 2 | Ambiguous: both reported |
| Fit distance exceeds the threshold for every family | No good fit: likely a mixture, spike or cap |

The last label matters in credit data, where columns are often a spike at zero
or at a cap plus a smooth body. The guide says so and points the user to treat
the spike separately. (The absolute "fit distance" check is an open decision —
see section 9.)

### 5.4 What a newcomer sees

```text
Column: monthly_income
Best match: Lognormal   (confidence: strong)
Runner-up: Gamma        (clearly worse, ΔAIC = 14)

Why it fits
- All values are positive and the right tail is long (skew 2.3)
- After taking logs the skew drops to 0.1, so the log is nearly symmetric

What that means
- Income behaves like compounding percentage changes
- The mean is pulled up by a few large values; use the median

Suggested handling
- Log-transform before Pearson-based methods, or use Spearman

Why not the others
- Normal: values can't be negative, and skew is 2.3
- Beta: values exceed 1

Check it yourself
- The QQ plot of log(income) should be close to a straight line
```

The "why not the others" section is generated from the rule that eliminated
each family. It is the most useful part for learning.

### 5.5 Starter catalogue

| Family | One-line story | Support | Credit example | Tell-tale sign |
|---|---|---|---|---|
| Bernoulli | Yes/no outcome | {0,1} | default flag | two values |
| Poisson | Rare events at a steady rate | counts ≥ 0 | enquiries per month | variance ≈ mean |
| Negative binomial | Counts with extra clumping | counts ≥ 0 | delinquency counts | variance > mean |
| Zero-inflated | Many structural zeros plus counts | counts ≥ 0 | products held | far more zeros than expected |
| Normal | Many small independent effects add up | all reals | score residuals | symmetric, light tails |
| Student-t | Normal-like but with extreme values | all reals | returns | high kurtosis |
| Lognormal | Effects multiply | positive | income, balances | log is symmetric |
| Gamma | Waiting or accumulation, positive | positive | claim sizes | right-skewed, no log symmetry |
| Weibull | Time until failure | positive | months to default | hazard changes over time |
| Pareto | Few giants dominate | tail above a threshold | large exposures | straight line on log-log plot |
| Beta | Proportion between 0 and 1 | [0,1] | utilisation, LGD | bounded, flexible shape |
| Exponential | Memoryless waiting time | positive | time between events | constant hazard |

### 5.6 Where it sits and how it grows

- `core/distributions`: fit, goodness-of-fit and sample functions.
- `catalogue/distributions.yaml`: the declared entries above.
- The univariate engine's "distribution candidates" step reads the profile,
  runs the matcher, and writes a ranked result to the registry like any other
  test.
- Anyone can add a family by adding one catalogue entry and one fit function.

The same pattern works for tests. If every registered test carries one-liner,
story, assumptions and "when not to use" fields, the lab teaches why it chose
Spearman over Pearson in the same way. The explanation layer becomes a
property of the whole registry rather than a one-off feature.

## 6. Inference layer

Everything so far is mostly descriptive (what is in this sample) plus tests.
Inference adds the step beyond that: what can we claim about the wider
population, and how sure are we? It is a thin layer on top of what exists, not
a new pipeline, governed by principle 7. The question is declared before
anything runs, via the `estimand` block in section 3.5.

### 6.1 Estimation with intervals

A routing table, like the bivariate one, picks the interval method from the
statistic and the profile:

| Statistic | Default interval | Falls back to |
|---|---|---|
| Mean | t-interval | Bootstrap when skewed or heavy-tailed |
| Median, percentiles | Bootstrap | n/a |
| Proportion (default rate) | Wilson | Bayesian credible interval for very small counts |
| Correlation | Fisher z | Bootstrap for Spearman/Kendall |
| Difference between groups | Welch interval | Bootstrap or permutation |
| Gini, KS, AUC | Bootstrap | n/a |

### 6.2 Resampling engine

Used wherever a formula is unreliable:
- **Bootstrap** (percentile or BCa) for intervals on awkward statistics.
- **Permutation tests** for a null distribution without distributional
  assumptions.
- **Cluster bootstrap**, which resamples whole customers rather than rows,
  whenever a cluster key is declared.
- The seed and number of resamples are recorded in the registry so any run
  reproduces exactly.

### 6.3 Hypothesis testing, made explicit

The Stage 4 tests already exist. Inference adds discipline around them:
- Declare one-sided or two-sided before testing.
- Define the **test family** for multiple-testing correction (for example "all
  pairwise correlations in this run"), then report raw and BH-adjusted p-values
  side by side.
- Offer **equivalence testing** (TOST) for questions of the form "has this
  stayed the same?" A non-significant difference is not proof of no difference,
  and equivalence testing answers the stability question properly.
- Every test result tags itself **exploratory** or **confirmatory**. Anything
  discovered by scanning many columns is exploratory by definition, and only a
  pre-declared hypothesis tested on held-out data counts as confirmatory.

### 6.4 Power and precision checks

- Each registered test already declares a minimum n. This adds the **detectable
  effect** at the current n, so a "no relationship" result comes with "we could
  only have detected correlations above 0.15".
- For rare events, a precision rule: bins with fewer than ~30 events get a
  warning, because their default-rate interval is too wide to rank anything.
- Optional Bayesian shrinkage (beta-binomial) for sparse categories, so a level
  with 3 defaults out of 10 isn't treated as a 30% risk. This can wait for a
  later phase (parked with the simulation bench).

### 6.5 Assumption diagnostics

A pass/warn/fail check feeds each inferential result:

| Assumption | Check |
|---|---|
| Independence | Cluster key declared? Autocorrelation across time? |
| Equal variances | Brown-Forsythe |
| Approximate normality of the statistic | QQ plot and skew/kurtosis at large n, since formal tests over-reject |
| Adequate expected counts | Chi-square rule (≥5), else Fisher or merge levels |
| Sample representativeness | Population declaration compared with what's actually in the data |

A failed assumption doesn't block the result. It switches the method (for
example mean interval to bootstrap) and records why.

### 6.6 Registry additions

```python
{
  "test_id": "welch_diff_means", "family": "income_by_region", "mode": "exploratory",
  "estimate": 120.0, "ci": [85.0, 155.0], "ci_method": "cluster_bootstrap",
  "alpha": 0.05, "n": 118432, "n_clusters": 41207, "seed": 20261012,
  "p_value": 3e-9, "p_adjusted": 2e-8,
  "effect_size": {"cohens_d": 0.03, "label": "negligible"},
  "assumptions": [{"check": "independence", "status": "pass"},
                  {"check": "equal_variance", "status": "warn"}],
  ...existing fingerprint fields
}
```

### 6.7 What a newcomer sees

```text
Question: Does average monthly_income differ between region A and region B?

Result: A is higher by 120 (95% CI: 85 to 155)
Test used: Mann-Whitney, not t-test (income is right-skewed, skew 2.3)
Adjusted p-value: 2e-8, effect size d = 0.03 (negligible)

Plain reading
- The difference is real in this data, but tiny: about 0.3% of typical income.
- Below your smallest effect of interest (d = 0.2), so no finding raised.

Careful
- Customers appear several times, so intervals were computed by resampling
  whole customers rather than rows.
- This is an exploratory result from scanning 40 variables; treat as a lead,
  not a conclusion.
```

### 6.8 Pitfalls the lab teaches against

Each of these can appear as a short note attached to relevant outputs:

| Misreading | What the lab says instead |
|---|---|
| "p = 0.03 means a 3% chance the null is true" | A p-value is the chance of data this extreme *if* the null were true |
| "The 95% CI contains the truth with 95% probability" | The *procedure* captures the truth 95% of the time over repeated samples |
| "Significant, so important" | Check the effect size against the smallest effect of interest |
| "Not significant, so no effect" | Check power and the interval width, or use equivalence testing |
| "I tested 400 pairs and found 20 hits" | Expect ~20 false positives at α = 0.05 without correction |
| "24 rows per customer, so n is large" | Effective sample size is closer to the number of customers |

## 7. Findings, decisions and governance

- **Result:** raw test output, stored in the registry.
- **Finding:** a result interpreted into a flag with severity and recommended
  action ("`monthly_income`: sentinel -999 found in 4,100 rows").
- **Decision:** what a human approved ("treat -999 as missing; log-transform").
  The decision log is the handoff to Phase 4.

Governance is built in at every layer: data fingerprints, config hashes, code
versions, contract provenance per field, and a logged reason for every
override.

## 8. Credit pack (plugin, parked until the core is stable)

WoE and IV, monotonic binning, KS/Gini/AUC per variable, PSI/CSI across time,
missingness-as-signal, leakage checks, and vintage views. It registers through
the same mechanism as the core engines, and target-related analysis runs on the
development sample only. Inference applies here too: intervals on default rate
per bin, bootstrap intervals on Gini and KS, and an equivalence-style check for
stability instead of relying on the PSI rule of thumb alone.

## 9. Open questions and deferred decisions

Recorded honestly, not silently resolved:

- **Grain of real data:** is the credit data one row per customer, or can a
  customer appear multiple times (monthly snapshots, multiple accounts)? If the
  latter, the cluster key and cluster bootstrap move from nice-to-have to
  essential. The same question applies to any panel data (e.g. one bond
  observed over time) before its bivariate results mean anything.
- **Absolute goodness-of-fit for the distribution matcher:** AIC/BIC rank
  families *relative to each other*; every family can be a bad fit and AIC
  still names a winner. The "fit distance" threshold in section 5.3 needs a
  definition (e.g. KS/CvM with parametric-bootstrap p-values), or v1 ships
  ΔAIC-only with QQ-plot confirmation.
- **Registry storage format:** JSON per run vs SQLite, decided when the
  registry is built (build plan step 3).
- **Report renderer:** the retained offline renderer only understands the old
  legacy report dict; a new report layer will render from the registry. The
  retained renderer stays working until then (see [Reporting](REPORTING.md)).
- **Simulation bench** (Monte Carlo, synthetic data, null distributions) and
  **Bayesian shrinkage** are parked; the bench will reuse the `sample`
  functions declared in the distribution catalogue, so nothing here needs to
  change when it arrives.

## 10. Where the work is ordered

The build order for realizing this design lives in
[Build plan](BUILD_PLAN.md). The process rules (explain before code, review
each step together, no commits or datasets) live in `AGENTS.md` and
[Contributing](../CONTRIBUTING.md) and are unchanged by this document. The
superseded reset-era architecture is preserved in
[ARCHITECTURE.reset-2026-10-12.md](ARCHITECTURE.reset-2026-10-12.md) for
history.

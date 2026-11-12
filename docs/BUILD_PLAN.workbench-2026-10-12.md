# Build plan

Build one layer at a time, in the order below, following the design in
[Architecture](ARCHITECTURE.md). The current step records the design; it
introduces no code. Each step is documented and reviewed together before the
next one starts.

## Build order

1. **Contract format, adapter and structural profiler with the gate.**
   Declared schema → lab contract translation, observed-data measurement,
   precedence rules (facts vs interpretation), grain detection and the
   stop-or-warn gate with the data fingerprint.
   **Done 2026-10-12** — see [Contract](CONTRACT.md); 21 tests passing.
2. **Semantic typer and ColumnProfile.** The type-decision table, sentinel
   masking, and the per-column profile record.
   **Done 2026-10-13** — see [Typing](TYPING.md); 17 tests passing
   (46 total with Step 1 and the retained renderer).
3. **Registry and result schema.** Structured records with test id, columns,
   assumption checks, statistic, effect size, fingerprint, config hash, code
   version, timestamp. The registry storage format (JSON per run vs SQLite) is
   decided here — see [Architecture §9](ARCHITECTURE.md#9-open-questions-and-deferred-decisions).
4. **Resampling engine and interval routing.** Bootstrap (percentile/BCa),
   permutation tests, cluster bootstrap when a cluster key is declared, and
   the interval-method routing table. Seed and resample count recorded in the
   registry. The estimand block (alpha, ci_level, smallest effects, seed)
   is read here.
5. **Univariate engines.** Numeric, categorical, date and missingness
   profiling; every summary carries its interval per principle 7.
6. **Bivariate engine and visualization dispatcher.** Pair-type routing with
   assumption checks and recorded method fallbacks, effect sizes, BH-FDR,
   exploratory/confirmatory tags, and power/detectable-effect notes. The
   dispatcher maps committed profiles to plot specifications.
7. **Distribution catalogue and matcher.** Catalogue entries with explanation
   levels, the support-first matching flow, ΔAIC/BIC ranking and the
   confidence labels. The absolute "fit distance" decision (section 5.3 of the
   architecture) is settled here or explicitly deferred.
8. **Multivariate engine.** Mixed-type association matrix, redundancy
   clustering, VIF, condition number, PCA for structure only.
9. **Findings and decision log.** Findings with severity, the human decision
   log with who/why/when, and the report layer that renders only from the
   registry (replacing the retained renderer's role over time).
10. **Credit pack.** WoE/IV, monotonic binning, KS/Gini/AUC, PSI/CSI,
    leakage checks, vintage views — parked until the core is stable.

**Parked for later:** the simulation bench (Monte Carlo, synthetic data, null
distributions) and optional Bayesian shrinkage. The simulation bench will
reuse the `sample` functions declared in the distribution catalogue, so
nothing in this plan needs to change when it arrives.

## Review loop for every step

1. Request one step and state its purpose.
2. Explain inputs/outputs, logic, assumptions, a tiny worked example and
   failure boundaries.
3. Review the explanation and correct gaps. Keep actual explanation evidence
   and unresolved questions in the owning private learning project.
4. Implement only the smallest understood part of the step and its relevant
   checks. Test fixtures use artificial data; real datasets are never committed.
5. Document the accepted input form, result meaning and limits in the
   architecture or a linked doc as part of the same change.
6. Add display support only when explicitly requested and its result form is
   clear.

Tests support the explanation; they do not establish understanding. Do not
record review completion from assistant-written notes or test results. Source
implementation and a Git commit remain separate decisions.

## Resume after a break

Check [Status](STATUS.md), the current build step and its actual review record.
Revisit the example and open decisions before adding code. There is no approved
implementation merely because a layer appears in this plan.

# Learning, testing and returning after a break

The aim is to understand a question, a table and its calculations well enough to
explain the resulting report. Work through the small engines before extending the
lab or applying it to a large private dataset.

## Read and run in this order

1. Read the [README](../README.md) for the project boundary and run a fresh demo.
2. Read [the configuration](CONFIGURATION.md) and identify the question, row
   grain, key, field roles and thresholds used by that demo.
3. Read [the distribution engine](ENGINES.md#distributions). Calculate a count,
   mean and median for a tiny list yourself, then compare its output.
4. Read [numeric relationships](ENGINES.md#numeric-relationships). Try increasing,
   decreasing, tied, constant and curved monotonic pairs.
5. Read [categorical relationships](ENGINES.md#categorical-relationships) and
   [group summaries](ENGINES.md#numeric-group-summaries). Check a `3:1` row's
   `75%:25%` breakdown and a small group's skipped reason.
6. Inspect `report.json` beside `report.html`. Confirm that displayed counts,
   results and reasons refer to the same evidence.

The example configuration selects only specific pairs; it does not search every
combination automatically. Keep each run anchored to a stated question.

## Known checks

Make generic code, test and documentation changes in this repository's checkout.
Temporary export/build snapshots kept by consuming projects are historical
copies. Keep each consumer's configurations and interpretation in that project.
An editable installation uses source from the current checkout; reinstall after
dependency or entry-point changes. If using a wheel, rebuild/reinstall explicitly
and confirm the imported package location before debugging changed behaviour.

Run the unittest suite using the environment described in the README. Read a
test's small input and expected result before treating it as a learning example.
The useful behaviours to understand are:

| Case | What you should be able to explain |
| --- | --- |
| Increasing/decreasing pair | Why Pearson and Spearman have the expected sign and magnitude |
| Tied ranks | Why Spearman uses average ranks for ties |
| Constant field | Why correlation is skipped rather than reported as zero |
| Missing/nonfinite pair | Which rows are usable and why exclusions differ across pairs |
| Known contingency counts | Which field sets rows, which sets columns, and what the percentage denominator is |
| Small/unequal groups | Why counts remain visible and when summaries are withheld |
| Invalid roles/settings | Why validation stops before exploration |
| Missing or duplicate key | How the error relates to the declared row grain |
| Fresh/repeated output path | Why a previous report is protected |
| Input/report evidence | How to check the source was preserved and the calculation can be reproduced |

Tests use generated observations rather than committed datasets. They check
implementation behaviour; interpreting a real result still requires you to know
how the observations were collected.

## Debug from the evidence

When a result looks wrong, keep the original configuration and report, then:

1. State what you expected and identify the exact field or selected pair.
2. Check the input filename/fingerprint and the declared row grain/key.
3. Inspect field roles and any numeric conversion error. Count usable, missing
   and nonfinite values for the result that surprised you.
4. Check the threshold and skipped reason. Do not lower a threshold just to make
   a result appear without understanding why the data are sparse.
5. Reproduce with a few artificial rows and calculate the expected answer by
   hand. Keep real sensitive data out of a bug report.
6. Decide whether the fault is the question/configuration, source data,
   calculation or report rendering. Fix the responsible component and run the
   relevant checks and a fresh demo.

For a code fix, record the trigger, expected behaviour, correction and check in
the commit or issue. Avoid changing several engines while debugging one result.

## Return-after-a-break checklist

- Read the README and repository status before assuming a proposed feature exists.
- Confirm the environment still installs and the unittest suite completes.
- Run `--demo` into a new report folder and open its HTML report.
- Reopen your last question, JSON configuration and report together.
- Reconfirm the input fingerprint, row grain, keys and field meanings.
- Read every result's usable/excluded counts and skipped reasons again.
- Write one sentence explaining what each selected engine answers.
- Record the next question and the smallest change needed to investigate it.

Your configuration and report are the memory of a run. They preserve what you
asked and calculated; your notes should preserve why that question mattered and
what remained uncertain.

## How other projects use the lab

A governed pipeline can provide a selected output table. The lab reads that table
as an independent input; it does not invoke ETL orchestration or control pipeline
checkpoints. Pipeline profiling describes data-quality evidence, while this lab
describes distributions and associations.

A credit-risk project can keep its own datasets and configurations locally, then
use this generic package to explore them. Credit-specific feature definitions,
outcomes, policy interpretation, scoring and models stay in that private project.
Neither integration changes the independent identities of the three projects.

## Before public updates and releases

The generic source has its own public GitHub repository. Review licensing, package
metadata, documentation, generated examples, ignore rules and full Git history
before publishing changes. Ensure no real datasets, private reports or
machine-specific paths enter the published project. A distribution license has
not been selected; public source hosting alone does not supply one.

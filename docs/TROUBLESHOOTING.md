# Troubleshooting

Keep the original configuration and report when investigating an unexpected
result. Start with the source filename/fingerprint, observation grain, field
roles and result-specific counts before changing a calculation.

## A run is rejected

| Symptom | Check |
| --- | --- |
| Input not found | Resolve `input.path` from the configuration file's directory. A relative output path instead uses the terminal's working directory. |
| Unknown or missing JSON setting | Compare with the complete [version 1 example](../examples/exploration.json). All schema sections are required; duplicate and unsupported keys are rejected. |
| Declared column absent | Compare spelling and case with the CSV header. Every declared field, including an excluded field, must exist. |
| Invalid CSV quoting or record width | Confirm comma-separated UTF-8 input with a unique, nonblank header and the same number of fields in each record. |
| Invalid numeric text | Inspect the declared numeric field. Currency formatting, thousands separators and category labels are not converted implicitly. |
| Integer precision error | A numeric integer cannot safely enter the floating-point calculation. If it is an identifier, declare it as an identifier; otherwise review representation and precision requirements. |
| Missing, blank or duplicate key | Check what one row represents and whether a composite key is needed. Repeated measurements may need more than an entity ID. |
| Invalid selected relationship | Numeric pairs must reference numeric fields, categorical pairs categorical fields, and group summaries one category plus one measure. |
| Output directory exists | Choose a new destination. Review earlier evidence before removing a report yourself. |

The [configuration reference](CONFIGURATION.md) defines required settings and
input semantics. The runner does not repair invalid data or guess field roles.

## A result is skipped

| Reason | Meaning |
| --- | --- |
| `no_usable_values` | No finite numeric values or nonmissing categorical values were available. |
| `insufficient_usable_pairs` | The selected pair did not meet its configured usable-row threshold. |
| `constant_field` | A numeric field is constant within the usable pair, so its correlation is undefined. |
| `numerical_precision_limit` | The correlation calculation could not return a trustworthy finite coefficient. |
| `statistics_overflow` | One or more summary statistics exceeded floating-point range; inspect retained counts and `overflow_statistics`. |
| `insufficient_usable_values` | A group's finite measure count is below the configured group threshold. |
| `no_group_has_usable_summary` | None of the observed groups produced an eligible summary. |

Check usable and excluded counts for the exact result. Numeric pairs require both
values to be finite; categorical pairs require both labels to be present. A row
excluded from one pair may still be used by another. Missing group labels are
counted separately. Do not treat an unavailable coefficient as zero or lower a
threshold merely to make a result appear.

## A result looks surprising

- Check denominators: categorical proportions use nonmissing values in that
  field; contingency percentages use complete pairs within each row category.
- Verify that IDs are identifiers and category codes are categorical. Literal
  `NA` is a label; only empty CSV cells are missing.
- Inspect outliers, group sizes and repeated observations. This version does not
  adjust for confounding or dependence among rows.
- Remember that Spearman uses average ranks for ties. Pearson describes linear
  association; Spearman describes monotonic association.
- Confirm that the report fingerprint and configuration belong to the intended
  source. Category and group ordering follows first occurrence, so row reordering
  may change display order without changing counts.

Reduce a suspected defect to a few artificial rows with a known answer. File an
[issue](https://github.com/daudakamandadk-lang/statistical-exploration-lab/issues)
with the command, dependency versions, configuration, expected result and actual
result. Keep sensitive observations and reports out of public issues.

## Changed code is not being used

An editable installation imports this checkout's source. Reinstall it after
dependency or entry-point changes. If using a wheel, rebuild and reinstall it.
Confirm the package location with the intended environment:

```sh
python -c "import statistical_exploration_lab; print(statistical_exploration_lab.__file__)"
```

For report display issues, compare `report.html` with `report.json` and include
the browser/version in a reproducible issue. Reports are static artifacts;
changing a configuration requires a new run and a fresh output directory.

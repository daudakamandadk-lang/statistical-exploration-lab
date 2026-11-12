# Semantic typing suggestions

`semantic_typer.py` suggests how columns behave, preserving declared/override
roles and recording rationale. It does not choose or run a statistical analysis.

## Call

```python
types = type_columns(structure, table, policy=None)
by_name = types.by_name()
```

`structure` must come from `profile_structure` and must not have a stopped
gate. Pass the same unchanged DataFrame or equivalent dict-of-lists used there.
The data fingerprint validates values, index, dtypes and column identity/order;
missing or changed input is rejected rather than typed against stale facts.
Profile again after intentionally changing the input.

`TyperPolicy` supplies thresholds for ID ratio, few integer levels, count skew,
date parsing, free-text length and sentinel candidates. It also has
`apply_inferred_sentinels=False` by default.

## Sentinel choices

A value resembling `-1`, `-999` or `"UNK"` is a candidate, not proof it is
missing. Default typing reports candidates and their findings without adding
them to the effective mask.

- A declared/override sentinel list is final and suppresses guessing for that
  column. `[]` means none, even if a value resembles a configured candidate.
- Without an explicit list, a caller may deliberately enable
  `TyperPolicy(apply_inferred_sentinels=True)`. Applied guesses retain
  inferred provenance and require interpretation.
- To confirm a choice, put the accepted list in the profile overrides and
  profile/type again. This keeps structural facts and the typing mask aligned.

## Types and result meaning

The inference rules consider empty/constant values, mixed storage, booleans and
dates, two-valued columns, string date parsing/free text, uniqueness, integer
levels and count shape. Inference is name-blind: two structurally equivalent
fields receive the same suggestion. An ID candidate may still be a measurement;
the caller chooses its actual role.

`TypeProfile` contains `TypedColumn` records and findings. Each column retains
its name, observed storage, semantic role/source, effective sentinels,
`sentinel_candidates`, sentinel provenance and rationale. Declared/override roles
remain distinct from inferred roles. A few-level integer suggestion can ask for
confirmation of ordinal versus nominal meaning; it does not invent level order.

`TypeProfile.data_fingerprint` retains the source-table identity.
`by_name()` provides lookup by field. Result mappings are read-only;
`to_dict()` returns detached inspection data. A composed investigation should
retain the structural result as well, including its gate and findings.

## Boundaries

This function does not parse the caller's entire dataset into new storage,
confirm a business meaning, select a test, calculate correlations or produce a
legacy report. Automatic sentinel application, when requested, does not rewrite
the original table or retroactively change structural facts.

Use [the inspection playground](../examples/inspect_table.py) to inspect the
calls one at a time. See [Status](STATUS.md) for current verification; the old
17-test typing result predates these boundary changes.

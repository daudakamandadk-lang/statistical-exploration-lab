# Contract and structural profiling

`contract.py` measures table structure and records explicit choices separately
from inferred hints. It accepts a pandas DataFrame or dict-of-lists; the caller
loads the data.

## Call and choices

```python
profile_structure(
    table, declared=None, overrides=None, policy=None, *,
    observation_key=None,
)
```

- `declared` and `overrides` use
  `{column: {"storage_type": ..., "semantic_type": ..., "sentinels": [...]}}`.
  Interpretation precedence is override > declared > inferred.
- Observed storage remains a fact. A declared mismatch becomes a finding,
  rather than silently changing the observed values.
- Storage and semantic vocabulary are validated. Supported roles include
  `identifier`, `id`, `id_candidate`, `continuous`, `count`, `ordinal`,
  `nominal`, `binary`, `date`, `free_text`, `excluded`, `mixed`, `empty`,
  `constant` and `ordinal_nominal_candidate`.
- A declared/override sentinel list is final, including `[]`. Explicit
  sentinels are masked on a copy; the input table is not rewritten.
- `observation_key` is an explicitly confirmed field name or list/tuple of
  names for a composite key. Without one, candidates remain hints.
- `GatePolicy` controls structural stop/warn behavior. It is not evidence
  that a candidate key has been confirmed.

`adapt_declared_schema` translates this simple mapping. It does not import the
governed pipeline or accept every engineering-schema format automatically.

## Keys and findings

`candidate_keys` and `grain` describe structural hints, not the business meaning
of one row. High uniqueness alone cannot make an ordinary measurement a required
key. Confirm the observation unit explicitly when it matters.

With a confirmed key, missing key values or conflicting records under that key
are key failures; composite uniqueness is assessed on the selected fields
together. Identical duplicate rows are reported separately. Empty tables and
ambiguous duplicate columns are structural failures under the default policy.
Warnings remain visible and need interpretation.

## Result

`StructureProfile` contains row/column counts, per-column contracts and
provenance, observed facts, candidate-key/grain hints, confirmed
`observation_key`, duplicate count, findings and `gate` (`proceed`, `warn`,
or `stop`).

Facts include observed storage, null count after explicit sentinel masking,
distinct count and numeric min/max. These are descriptive measurements, not
statistical tests or proof of source accuracy.

Two fingerprints have different meanings:

- `fingerprint`: a SHA-256 structural-summary identity. Different raw data can
  have the same counts and min/max and therefore the same structural summary.
- `data_fingerprint`: source table identity covering content, index, dtypes and
  columns for the dependent typing handoff. It detects changed/reordered input;
  it does not anonymize the data or establish its provenance.

Result mappings are read-only. Use `profile.to_dict()` to obtain detached
inspection data. Do not mutate evidence to express a new decision; profile again
with the chosen overrides and unchanged source table.

The detached dictionary is inspection data, not a canonical JSON report. Numeric
infinities can remain in observed extrema; strict JSON export needs an explicit
representation for such values. The data fingerprint checks a same-runtime
table handoff, not a complete registry identity for data, configuration and code.

## Limits and checks

Non-scalar/unhashable cells and invalid or ambiguous column identities are
outside the supported table form. This component does not calculate probability,
correlation, inference or distributions. Candidate keys and storage are not
substitutes for the caller's row-unit definition.

For compatibility, `GatePolicy.key_like_ratio` remains accepted but does not
promote inferred candidates to required keys. Duplicate column labels always
stop profiling, even if the older `stop_on_duplicate_columns` option is false,
because label-based measurement would be ambiguous.

See [Typing](TYPING.md) for the next optional call and [Status](STATUS.md) for
actual current checks. Historical initial-stage test counts are not verification
of the revised key/fingerprint boundaries.

# Configuration reference: version 1

Start from [the complete example](../examples/exploration.json). The runner accepts
one JSON configuration through `--config` or generates a temporary example through
`--demo`. Supply the output directory separately with `--output`.

Unknown keys are rejected, including nested keys. Settings from other prototypes
such as `selection`, `missingness`, `inference`, `output`, `format`, `read_only` or
field `units` are not part of this version. There are no implicit joins, filters,
type guesses or imputations to configure.

## Every setting

| Setting | Meaning | Example |
| --- | --- | --- |
| `version` | Configuration schema version; must be integer `1` | `1` |
| `question` | The descriptive question this run investigates | `"How do measurements vary across segments?"` |
| `input.path` | Local CSV path; resolved relative to the configuration file's directory | `"../data/local/observations.csv"` |
| `observation.grain` | What one row represents | `"one row per recorded observation"` |
| `observation.unit` | The unit of observation | `"observation"` |
| `observation.key` | One or more identifier columns whose combined values identify a row | `["record_id"]` |
| `fields.identifiers` | String identifiers used for keys; excluded from calculations | `["record_id"]` |
| `fields.numeric` | Columns explicitly parsed as numeric | `["measurement_x", "measurement_y"]` |
| `fields.categorical` | String category columns | `["segment", "group"]` |
| `fields.excluded` | Present columns explicitly left out of exploration | `[]` |
| `minimum_samples.numeric_pair` | Minimum usable finite rows for a numeric pair | `3` |
| `minimum_samples.categorical_pair` | Minimum complete rows for a categorical pair | `3` |
| `minimum_samples.group` | Minimum usable finite values for a numeric summary within a group | `2` |
| `relationships.numeric_pairs` | Selected pairs of declared numeric columns | `[["measurement_x", "measurement_y"]]` |
| `relationships.numeric_methods` | Selected methods: `pearson`, `spearman` | `["pearson", "spearman"]` |
| `relationships.categorical_pairs` | Selected pairs of declared categorical columns | `[["segment", "group"]]` |
| `relationships.group_summaries` | Declared category/measure combinations | `[{"group_by": "segment", "measure": "measurement_x"}]` |

Use empty `numeric_pairs`, `categorical_pairs` or `group_summaries` lists when a
question does not need that calculation. `numeric_methods` must still contain at
least one supported method. Lists must not contain duplicate fields, methods or
selected relationships; reversing a pair does not create a different pair.

Minimum counts are guardrails for displaying summaries, not guarantees of
statistical reliability. They must be integers: `numeric_pair` is at least `2`,
and `categorical_pair` and `group` are at least `1`. Increase them deliberately
for your question. Sample standard deviation requires at least two usable values
even if a smaller group threshold is allowed by the configuration.

## Declare the table before asking about relationships

1. Write the question and describe the row grain. Repeated observations from one
   person or device are still separate rows; this lab does not correct dependence
   between repeated observations.
2. Choose key columns that identify one row. Declare them as identifiers and
   verify their combined values are nonmissing and unique.
3. Assign each selected column exactly one role. A number-looking identifier is
   still an identifier; do not treat an ID as a measurement.
4. Select only the relationships you intend to inspect. Numeric pairs reference
   numeric fields, categorical pairs reference categorical fields, and group
   summaries reference one category and one numeric measure.
5. Set the thresholds, choose a fresh output folder and run.

Every declared field, including an excluded field, must exist in the CSV. Other
CSV columns may exist and are recorded as ignored. Numeric conversion rejects
invalid nonmissing text rather than silently turning it into missing data. Identifiers
and categories are read as strings, preserving values such as `001`. Only empty
CSV cells are treated as missing; a literal category label such as `NA` remains
a label. Missing
keys or duplicate combined keys stop the run before exploration.

## Missing observations and report paths

Missingness is fixed in this version. Numeric pairs use rows where both values
are finite. Categorical pairs use rows where both categories are present. A group
summary needs a present group label and a finite measure. No engine fills a
missing value. Different relationships can consequently use different rows; read
the usable and excluded counts for every result.

The configuration's input path is resolved from the configuration folder, while
a relative `--output` path is resolved from your current working directory.
The output directory must not already exist. To compare configurations, create
separate report folders and retain their JSON evidence.

The source filename, byte count and SHA-256 fingerprint identify the input in a
report.
Absolute resolved machine paths are not added to report metadata. The exact
configuration is retained, so prefer portable relative input paths when sharing
a configuration.

## Common errors

| Error | What to check |
| --- | --- |
| Input not found | Resolve `input.path` from the configuration's folder, not your terminal's folder. |
| Unknown setting | Compare your JSON with the supported version 1 example; remove prototype-only settings. |
| Missing declared column | Inspect the CSV header for spelling/case and update the role lists deliberately. |
| Numeric conversion failure | Find text or formatting in a declared numeric column; fix the source or reconsider the role. |
| Key missing or duplicated | Confirm the row grain and the complete key, especially for repeated observations. |
| Invalid relationship field | Match each relationship's fields to their declared roles. |
| Output already exists | Use another folder; inspect the earlier report before removing it yourself. |

"""A table-inspection playground: run the file or run its # %% cells in VS Code.

Edit the choices below. This example loads the selected table, calls two
independent lab functions and displays their evidence. It never writes data.
"""

# %% 1. Imports and small helpers
from pathlib import Path

import pandas as pd

from statistical_exploration_lab import profile_structure, type_columns


def load_table(csv_path=None):
    """The caller chooses the source; artificial values are generated in memory."""
    if csv_path is not None:
        # Preserve identifiers and literal category labels; parse numbers only
        # in the explicit preparation cell below. Empty cells are missing.
        return pd.read_csv(Path(csv_path), dtype="string", keep_default_na=False,
                           na_values=[""])
    return pd.DataFrame({
        "record_id": ["001", "002", "003", "004", "005"],
        "amount": [10.0, 20.0, -1.0, 40.0, 40.0],
        "group": ["A", "B", "A", "B", "A"],
        "note": ["ready", "UNK", "ready", "ready", "ready"],
    })


def field_choices(roles, missing_values):
    """Build only the choices supplied by the caller; infer nothing here."""
    choices = {name: {"semantic_type": role} for name, role in roles.items()}
    for name, values in missing_values.items():
        choices.setdefault(name, {})["sentinels"] = values
    return choices


def show_profile(profile):
    evidence = profile.to_dict()
    print("\nStructure:")
    print(pd.DataFrame.from_dict(evidence["facts"], orient="index").to_string())
    print("Chosen row key:", profile.observation_key or "not selected")
    print("Candidate keys (suggestions):", profile.candidate_keys)
    print("Gate:", profile.gate.status)
    for finding in profile.findings:
        print(f"  {finding.severity}: {finding.column or 'table'}: {finding.message}")


def show_types(typed):
    columns = ["name", "storage_type", "semantic_type", "semantic_source",
               "sentinels", "sentinel_candidates", "rationale"]
    print("\nField roles and suggestions:")
    print(pd.DataFrame(typed.to_dict()["columns"], columns=columns).to_string(index=False))
    for finding in typed.findings:
        print(f"  {finding.severity}: {finding.column or 'table'}: {finding.message}")


# %% 2. Your choices: edit these for the table you want to investigate
CSV_PATH = None  # Example: Path(r"D:\my-data\observations.csv")
SELECT_COLUMNS = None  # Or a list of columns, e.g. ["record_id", "amount"]
OBSERVATION_KEY = "record_id"  # None, one name, or a list for a composite key
NUMERIC_COLUMNS = ["amount"]  # Only these columns will be parsed as numbers
FIELD_ROLES = {
    "record_id": "identifier",
    "amount": "continuous",
    "group": "nominal",
}
MISSING_VALUES = {"amount": []}  # [] explicitly keeps -1 as a real measurement


# %% 3. Load and prepare the selected table
data = load_table(CSV_PATH)
if SELECT_COLUMNS is not None:
    data = data.loc[:, SELECT_COLUMNS].copy()
for name in NUMERIC_COLUMNS:
    data[name] = pd.to_numeric(data[name], errors="raise")
print("Selected table (first ten rows):")
print(data.head(10).to_string(index=False))
print("Rows:", len(data))


# %% 4. Inspect structure with your explicit choices
profile = profile_structure(
    data,
    observation_key=OBSERVATION_KEY,
    overrides=field_choices(FIELD_ROLES, MISSING_VALUES),
)
show_profile(profile)


# %% 5. Inspect types for the SAME table; review warnings before using results
if profile.gate.status == "stop":
    raise ValueError("Resolve the reported structural issue, then rerun cells 3-5.")
typed = type_columns(profile, data)
show_types(typed)

# 'UNK' is a suggestion, not an active missing-value rule. To deliberately
# treat it as missing, edit MISSING_VALUES to include "note": ["UNK"] and
# rerun cells 4-5. To try another field role, edit FIELD_ROLES and rerun.
# After changing/filtering/replacing data, rerun profiling before typing.


# %% 6. Optional recipe: compose the same components in an ordinary function
def inspect_selected_table(table, *, observation_key=None, roles=None,
                           missing_values=None):
    """Keep both results; a stopped profile returns no typing result."""
    structure = profile_structure(
        table, observation_key=observation_key,
        overrides=field_choices(roles or {}, missing_values or {}),
    )
    if structure.gate.status == "stop":
        return structure, None
    return structure, type_columns(structure, table)


recipe_profile, recipe_types = inspect_selected_table(
    data, observation_key=OBSERVATION_KEY, roles=FIELD_ROLES,
    missing_values=MISSING_VALUES,
)
print("\nRecipe completed:", recipe_profile.gate.status)
# Results are available as recipe_profile and recipe_types for your next cell.
# No calculations or HTML reports are invented around these inspection results.

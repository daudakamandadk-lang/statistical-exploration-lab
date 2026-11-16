"""Apply only caller-confirmed missing-value rules to a copied table."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import pandas as pd
from .contract import _mask_sentinels, _validate_entries, data_fingerprint

@dataclass(frozen=True)
class PreparedTable:
    """Creation-time evidence; table remains editable, evidence is not updated."""
    table: pd.DataFrame
    rules: Mapping
    changed_positions: Mapping
    input_fingerprint: str
    prepared_fingerprint: str

def prepare_missing_values(data, *, rules):
    """Apply {column: [confirmed sentinels]} using profiling's matching rules.

    Text matching trims and ignores case; numbers are not converted to text.
    Empty lists preserve values. Existing missing cells are not counted as new
    changes. No inference, dropping, encoding or imputation occurs. Dtypes may
    change when a missing marker is inserted. All fields must contain supported
    scalar values for fingerprinting; explicitly select your analysis table first.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a pandas DataFrame')
    if not data.columns.is_unique:
        raise ValueError('Table columns must be unique')
    if not isinstance(rules, Mapping):
        raise TypeError('rules must map column names to sentinel lists')
    entries = _validate_entries({k: {'sentinels': v} for k,v in rules.items()}, 'rules')
    absent = set(entries) - set(data.columns)
    if absent:
        raise ValueError(f'Rule columns are absent: {sorted(absent)}')
    original = data_fingerprint(data)
    table = data.copy(deep=True)
    changes = {}
    for name, entry in entries.items():
        before = table[name].isna()
        table[name] = _mask_sentinels(table[name], entry['sentinels'])
        changes[name] = tuple(i for i, changed in enumerate((~before & table[name].isna()).tolist()) if changed)
    return PreparedTable(table, MappingProxyType({k:v['sentinels'] for k,v in entries.items()}),
                         MappingProxyType(changes), original, data_fingerprint(table))

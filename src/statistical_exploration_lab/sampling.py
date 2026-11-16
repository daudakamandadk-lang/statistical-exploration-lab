"""Explicit sample preparation; no imputation or statistical estimation."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

import numpy as np
import pandas as pd

from .contract import data_fingerprint


@dataclass(frozen=True)
class CompleteCaseSelection:
    """Copied table plus original zero-based row positions and missing reasons.

    The table is intentionally editable for subsequent investigation. Evidence
    describes the selection at creation; it does not track later table edits.
    Pandas deep copies do not recursively clone objects inside object columns.
    """
    table: pd.DataFrame
    columns: tuple
    input_fingerprint: str
    selected_fingerprint: str
    total_rows: int
    used_positions: tuple
    excluded_positions: tuple
    missing_by_position: Mapping

    @property
    def used_rows(self):
        return len(self.used_positions)


def select_complete_cases(data, *, columns):
    """Keep rows complete across exactly the caller-selected fields.

    Uses pandas missingness (None/NaN/NA/NaT), not inferred sentinel rules.
    Keeps all table columns and original index labels, order and dtypes. Empty
    strings and infinity are not missing. No file I/O, mutation, encoding or
    imputation occurs. An empty result fails for explicit caller review.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a pandas DataFrame')
    if not data.columns.is_unique or any(not isinstance(c, str) or not c.strip()
                                         for c in data.columns):
        raise ValueError('Table columns must be unique nonblank strings')
    if (not isinstance(columns, (list, tuple)) or not columns
            or any(not isinstance(c, str) or not c.strip() for c in columns)
            or len(set(columns)) != len(columns)):
        raise ValueError('columns must be a nonempty list/tuple of distinct names')
    absent = set(columns) - set(data.columns)
    if absent:
        raise ValueError(f'Selected columns are absent: {sorted(absent)}')
    missing = data.loc[:, list(columns)].isna().to_numpy()
    incomplete = missing.any(axis=1)
    used = tuple(int(i) for i in np.flatnonzero(~incomplete))
    excluded = tuple(int(i) for i in np.flatnonzero(incomplete))
    if not used:
        raise ValueError('No complete selected observations remain; review the selected sample')
    reasons = MappingProxyType({
        i: tuple(name for j, name in enumerate(columns) if missing[i, j])
        for i in excluded
    })
    table = data.iloc[list(used)].copy(deep=True)
    return CompleteCaseSelection(table, tuple(columns), data_fingerprint(data),
                                 data_fingerprint(table), len(data), used, excluded, reasons)

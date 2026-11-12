"""Build step 1: contract format, declared-schema adapter, structural profiler, gate.

Domain-neutral by design: no column name has special meaning. Every
interpretation enters through the declared schema or overrides; the profiler
measures only. See docs/CONTRACT.md for the accepted input form, result
meaning and limits.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from fractions import Fraction
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np
import pandas as pd

__all__ = [
    'ColumnContract',
    'Finding',
    'GateDecision',
    'GatePolicy',
    'StructureProfile',
    'adapt_declared_schema',
    'data_fingerprint',
    'profile_structure',
]

_STORAGE = ('int', 'float', 'bool', 'date', 'str', 'mixed', 'empty')
_SEMANTIC = frozenset({
    'identifier', 'id', 'id_candidate', 'continuous', 'count', 'ordinal',
    'nominal', 'binary', 'date', 'free_text', 'excluded', 'mixed', 'empty',
    'constant', 'ordinal_nominal_candidate',
})


def _plain(value):
    """Return detached inspection data without copying read-only mappings."""
    if is_dataclass(value):
        return {field.name: _plain(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Mapping):
        return {key: _plain(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_plain(item) for item in value]
    if value is pd.NA or value is pd.NaT:
        return None
    if isinstance(value, np.generic):
        scalar = value.item()
        # NumPy extended precision scalars may return themselves from item().
        return str(value) if isinstance(scalar, np.generic) else _plain(scalar)
    if isinstance(value, (datetime, date, time, pd.Timestamp)):
        return value.isoformat()
    if isinstance(value, (Decimal, Fraction, timedelta)):
        return str(value)
    return value


def _freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: _freeze(item) for key, item in value.items()})
    if isinstance(value, (tuple, list)):
        return tuple(_freeze(item) for item in value)
    return value


class _Inspectable:
    def to_dict(self):
        """Return a detached plain dictionary for inspection or presentation."""
        return _plain(self)


def _validate_column_names(table):
    if any(not isinstance(name, str) or not name.strip() for name in table.columns):
        raise ValueError('Column names must be nonblank strings; rename columns explicitly')


def _scalar_identity(value):
    """Canonical scalar encodings: no numeric coercion or decimal rounding.

    Hash protocol v1 supports the scalar types used by pandas tables. Missing
    markers, strings, booleans and numbers remain distinguishable. Containers
    and arbitrary Python objects are deliberately rejected.
    """
    if value is None:
        return ['none']
    if value is pd.NA:
        return ['pandas.NA']
    if value is pd.NaT:
        return ['pandas.NaT']
    if isinstance(value, (np.datetime64, np.timedelta64)):
        return [str(value.dtype), str(value.view('i8'))]
    if isinstance(value, np.floating):
        return [str(value.dtype), np.format_float_scientific(value, unique=True)]
    if isinstance(value, np.integer):
        return [str(value.dtype), str(int(value))]
    if isinstance(value, (bool, np.bool_)):
        return ['bool', bool(value)]
    if isinstance(value, str):
        return ['str', value]
    if isinstance(value, bytes):
        return ['bytes', value.hex()]
    if isinstance(value, int):
        return ['int', str(value)]
    if isinstance(value, float):
        return ['float', value.hex()]
    if isinstance(value, complex):
        return ['complex', value.real.hex(), value.imag.hex()]
    if isinstance(value, (datetime, date, time, pd.Timestamp)):
        return [type(value).__module__ + '.' + type(value).__qualname__, value.isoformat()]
    if isinstance(value, (timedelta, pd.Timedelta)):
        if isinstance(value, pd.Timedelta):
            return ['pandas.Timedelta', str(value.value)]
        return ['timedelta', value.days, value.seconds, value.microseconds]
    if isinstance(value, Decimal):
        return ['Decimal', str(value)]
    if isinstance(value, Fraction):
        return ['Fraction', str(value.numerator), str(value.denominator)]
    if isinstance(value, tuple):  # MultiIndex entries, not arbitrary cell containers.
        return ['tuple', [_scalar_identity(item) for item in value]]
    if isinstance(value, pd.Period):
        return ['pandas.Period', str(value.ordinal), value.freqstr]
    if isinstance(value, pd.Interval):
        return ['pandas.Interval', _scalar_identity(value.left),
                _scalar_identity(value.right), value.closed]
    raise TypeError(f'Unsupported table scalar {type(value).__name__}; use scalar column values')


def _dtype_identity(dtype):
    result = [repr(dtype)]
    if isinstance(dtype, pd.CategoricalDtype):
        result.extend([bool(dtype.ordered),
                       [_scalar_identity(value) for value in dtype.categories]])
    return result


def data_fingerprint(table: pd.DataFrame) -> str:
    """Fingerprint an exact ordered table snapshot using hash protocol v1.

    Include columns, dtypes (including categorical metadata), index type/names/
    values and type-tagged cell values. Float encodings retain their exact
    value. This is separate from the older structural-summary fingerprint.
    """
    if not isinstance(table, pd.DataFrame):
        raise TypeError('data_fingerprint requires a pandas DataFrame')
    _validate_column_names(table)
    digest = hashlib.sha256()

    def update(value):
        raw = json.dumps(value, ensure_ascii=True, separators=(',', ':'),
                         allow_nan=False).encode('utf-8')
        digest.update(str(len(raw)).encode('ascii') + b':' + raw)

    update(['statistical-lab-table-v1', len(table), list(table.columns),
            [_dtype_identity(dtype) for dtype in table.dtypes],
            type(table.index).__module__ + '.' + type(table.index).__qualname__,
            [_scalar_identity(name) for name in table.index.names],
            [_dtype_identity(level.dtype) for level in table.index.levels]
            if isinstance(table.index, pd.MultiIndex)
            else [_dtype_identity(table.index.dtype)]])
    for index, row in zip(table.index, table.itertuples(index=False, name=None)):
        update([_scalar_identity(index), [_scalar_identity(value) for value in row]])
    return 'sha256:' + digest.hexdigest()


# --------------------------------------------------------------------------
# Contract format
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ColumnContract(_Inspectable):
    """How one column will be analysed, with per-field provenance.

    storage_type is an observed fact (never overridden). semantic_type is an
    interpretation: override beats declared beats inferred. sentinels are
    values masked as missing before anything else runs.
    """

    name: str
    storage_type: str
    semantic_type: str | None
    sentinels: tuple
    provenance: Mapping[str, str]  # field -> observed/declared/inferred/override/none

    def __post_init__(self):
        object.__setattr__(self, 'provenance', _freeze(self.provenance))


@dataclass(frozen=True)
class Finding(_Inspectable):
    """A structural observation with severity. Never a silent fix."""

    code: str
    severity: str  # 'stop' | 'warn' | 'info'
    message: str
    column: str | None = None


@dataclass(frozen=True)
class GateDecision(_Inspectable):
    status: str  # 'proceed' | 'warn' | 'stop'
    reasons: tuple[Finding, ...]


@dataclass(frozen=True)
class StructureProfile(_Inspectable):
    """Measured facts about the table plus the gate decision."""

    n_rows: int
    n_columns: int
    columns: tuple[ColumnContract, ...]
    facts: Mapping[str, Mapping[str, Any]]  # per column: storage/null/distinct/min/max
    candidate_keys: tuple[str, ...]
    grain: str | None
    exact_duplicate_rows: int
    fingerprint: str
    findings: tuple[Finding, ...]
    gate: GateDecision
    observation_key: tuple[str, ...] = ()
    data_fingerprint: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'facts', _freeze(self.facts))


@dataclass(frozen=True)
class GatePolicy(_Inspectable):
    """Thresholds and rulings live in config, not code (principle 4)."""

    stop_on_empty_table: bool = True
    stop_on_duplicate_columns: bool = True  # Legacy setting; ambiguous labels always stop.
    stop_on_conflicting_keys: bool = True
    warn_on_no_key: bool = True
    warn_on_exact_duplicates: bool = True
    warn_on_empty_columns: bool = True
    warn_on_constant_columns: bool = True
    key_like_ratio: float = 0.8  # Legacy hint threshold; never an assertion of row identity.


# --------------------------------------------------------------------------
# Declared-schema adapter (one-way, never imported from an engineering layer)
# --------------------------------------------------------------------------

def adapt_declared_schema(declared: Mapping[str, Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    """Translate a simple declared-schema mapping into declared contract entries.

    Expected shape: {column_name: {"storage_type": "int", "semantic_type": "...",
    "sentinels": [...]}}. Only the keys listed are read; anything else is
    ignored. The lab never imports from an engineering schema layer.
    """
    return _validate_entries(declared, 'declared schema', reject_unknown=False)


def _validate_entries(entries, location, *, reject_unknown=True):
    if not isinstance(entries, Mapping):
        raise TypeError(f'{location} must be a mapping of column names to entries')
    adapted: dict[str, dict[str, Any]] = {}
    for name, spec in entries.items():
        if not isinstance(name, str) or not name.strip():
            raise ValueError(f'{location} column names must be nonblank strings')
        if not isinstance(spec, Mapping):
            raise TypeError(
                f'{location} entry for {name!r} must be a mapping, '
                f'got {type(spec).__name__}'
            )
        unknown = set(spec) - {'storage_type', 'semantic_type', 'sentinels'}
        if reject_unknown and unknown:
            raise ValueError(f'{location} entry for {name!r} has unknown fields: '
                             f'{sorted(unknown, key=str)}')
        entry: dict[str, Any] = {}
        if 'storage_type' in spec:
            value = spec['storage_type']
            if not isinstance(value, str) or value not in _STORAGE:
                raise ValueError(
                    f'{location} storage_type for {name!r} must be one of '
                    f'{_STORAGE}, got {value!r}'
                )
            entry['storage_type'] = value
        if 'semantic_type' in spec:
            value = spec['semantic_type']
            if not isinstance(value, str) or value not in _SEMANTIC:
                raise ValueError(f'{location} semantic_type for {name!r} must be a '
                                 f'recognized type, got {value!r}')
            entry['semantic_type'] = value
        if 'sentinels' in spec:
            values = spec['sentinels']
            if not isinstance(values, (list, tuple)):
                raise TypeError(f'{location} sentinels for {name!r} must be a list or tuple '
                                '(use [] to preserve all values)')
            for value in values:
                if not pd.api.types.is_scalar(value):
                    raise TypeError(f'{location} sentinels for {name!r} must contain scalar values')
                _scalar_identity(value)  # Reject objects without a stable scalar representation.
            entry['sentinels'] = tuple(values)
        adapted[name] = entry
    return adapted


def _mask_sentinels(series, sentinels):
    """Use the same masking rule in profiling and typing; preserve the input.

    Text labels match trimmed, case-insensitively. Numeric values are not
    converted to text, so the sentinel string '1' does not erase number 1.
    """
    if not sentinels:
        return series
    mask = pd.Series(False, index=series.index)
    for sentinel in sentinels:
        if isinstance(sentinel, str):
            target = sentinel.strip().casefold()
            match = series.map(lambda value: isinstance(value, str)
                               and value.strip().casefold() == target)
        elif sentinel is None or sentinel is pd.NA or sentinel is pd.NaT:
            match = series.isna()
        else:
            match = series.eq(sentinel).fillna(False)
        mask = mask | match
    return series.where(~mask)


def _observation_key(value, columns):
    if value is None:
        return ()
    if isinstance(value, str):
        value = [value]
    if (not isinstance(value, (list, tuple)) or not value
            or any(not isinstance(name, str) or not name.strip() for name in value)):
        raise ValueError('observation_key must be a column name or nonempty list/tuple of names')
    if len(set(value)) != len(value):
        raise ValueError('observation_key cannot contain duplicate column names')
    missing = set(value) - set(columns)
    if missing:
        raise ValueError(f'observation_key columns are absent: {sorted(missing)}')
    return tuple(value)


# --------------------------------------------------------------------------
# Structural profiler and gate
# --------------------------------------------------------------------------

def _observe_storage(series: pd.Series) -> str:
    """Observed storage fact for one sentinel-masked column."""
    non_null = series.dropna()
    if non_null.empty:
        return 'empty'
    if pd.api.types.is_bool_dtype(series):
        return 'bool'
    if pd.api.types.is_integer_dtype(series):
        return 'int'
    if pd.api.types.is_float_dtype(series):
        return 'float'
    if pd.api.types.is_datetime64_any_dtype(series):
        return 'date'
    kinds = {type(v).__name__ for v in non_null}
    if kinds <= {'str'}:
        return 'str'
    if kinds <= {'int', 'float'}:
        return 'float' if 'float' in kinds else 'int'
    return 'mixed'


def _guess_semantic(storage: str, distinct: int, dedup_unique: bool) -> str | None:
    """Minimal Step-1 interpretation guesses; full typing is Step 2.

    id_candidate: an identifier-like column (int/str, no nulls) that is
    unique once exact duplicate rows are removed. count-vs-continuous for
    non-key int columns is deliberately left to Step 2.
    """
    if distinct <= 1:
        return 'constant'
    if distinct == 2:
        return 'binary'
    if storage in ('int', 'str') and dedup_unique:
        return 'id_candidate'
    if storage == 'float':
        return 'continuous'
    return None


def fingerprint_table(facts: Mapping[str, Mapping[str, Any]], n_rows: int,
                      column_order: list[str]) -> str:
    """SHA-256 over a stable structural summary; never raw values."""
    payload = json.dumps(
        {'n_rows': n_rows, 'columns': column_order,
         'facts': {c: _plain(facts[c]) for c in column_order}},
        sort_keys=True, default=str, separators=(',', ':'))
    return 'sha256:' + hashlib.sha256(payload.encode('utf-8')).hexdigest()


def profile_structure(
    table: pd.DataFrame | Mapping[str, Any],
    declared: Mapping[str, Mapping[str, Any]] | None = None,
    overrides: Mapping[str, Mapping[str, Any]] | None = None,
    policy: 'GatePolicy | None' = None,
    *,
    observation_key: str | list[str] | tuple[str, ...] | None = None,
) -> StructureProfile:
    """Measure a table's structure and decide whether analysis may proceed.

    Inputs: a DataFrame or dict-of-lists (the caller loads data; the lab
    never reads files), an optional declared schema and optional per-column
    overrides (both {column: {field: value}}). Returns measured facts, a
    contract per column with provenance, findings and a gate decision. No
    statistics beyond counts are computed here. Only observation_key asserts
    row identity. candidate_keys and, without an explicit key, grain are
    provisional hints and never cause a key-conflict stop.
    """
    policy = policy if policy is not None else GatePolicy()
    if not isinstance(policy, GatePolicy):
        raise TypeError('policy must be a GatePolicy')
    declared = adapt_declared_schema({} if declared is None else declared)
    overrides = _validate_entries({} if overrides is None else overrides, 'overrides')

    if not isinstance(table, pd.DataFrame):
        table = pd.DataFrame(table)
    _validate_column_names(table)
    selected_key = _observation_key(observation_key, table.columns)
    content_fingerprint = data_fingerprint(table)

    findings: list[Finding] = []
    n_rows_raw, n_columns_raw = len(table), len(table.columns)

    # -- stop conditions on raw structure ------------------------------------
    if policy.stop_on_empty_table and (n_columns_raw == 0 or n_rows_raw == 0):
        detail = ('table has no columns' if n_columns_raw == 0
                  else 'table has no rows')
        findings.append(Finding('empty_table', 'stop', detail))
    if table.columns.duplicated().any():
        dups = sorted({str(c) for c in table.columns[table.columns.duplicated()]})
        findings.append(Finding(
            'duplicate_columns', 'stop',
            f'duplicate column names: {dups}; row identity is ambiguous'))
        # Column access by label is ambiguous; nothing further can be measured
        # reliably. Return the stop decision with what is already known.
        unique_names = list(dict.fromkeys(table.columns))
        return StructureProfile(
            n_rows=len(table), n_columns=len(table.columns), columns=(),
            facts={}, candidate_keys=(), grain=None, exact_duplicate_rows=0,
            fingerprint=fingerprint_table({c: {} for c in unique_names},
                                          len(table), unique_names),
            findings=tuple(findings), gate=GateDecision('stop', tuple(findings)),
            observation_key=selected_key, data_fingerprint=content_fingerprint)

    n_rows, n_columns = len(table), len(table.columns)
    column_order = list(table.columns)

    # -- sentinel masking (declared/override sentinels only; guessing is Step 2)
    sentinels_by_col: dict[str, tuple] = {}
    masked = table.copy()
    for raw_name in table.columns:
        name = str(raw_name)
        sentinels: tuple = ()
        if name in declared and 'sentinels' in declared[name]:
            sentinels = tuple(declared[name]['sentinels'])
        if name in overrides and 'sentinels' in overrides[name]:
            sentinels = tuple(overrides[name]['sentinels'])  # override wins
        sentinels_by_col[name] = sentinels
        if sentinels:
            masked[raw_name] = _mask_sentinels(masked[raw_name], sentinels)

    # -- exact duplicate rows (masked values; used for keys and warnings) ------
    masked_no_dup_rows = masked.drop_duplicates()
    exact_dup_rows = int(n_rows - len(masked_no_dup_rows)) if n_rows else 0
    if exact_dup_rows and policy.warn_on_exact_duplicates:
        findings.append(Finding('exact_duplicate_rows', 'warn',
                                f'{exact_dup_rows} exact duplicate row(s)'))

    # -- per-column facts and contracts ---------------------------------------
    facts: dict[str, dict[str, Any]] = {}
    contracts: list[ColumnContract] = []
    for raw_name in masked.columns:
        name = str(raw_name)
        series = masked[raw_name]
        storage = _observe_storage(series)
        non_null = series.dropna()
        distinct = int(non_null.nunique())
        fact: dict[str, Any] = {'storage_type': storage,
                                'null_count': int(series.isna().sum()),
                                'distinct_count': distinct}
        if storage in ('int', 'float') and not non_null.empty:
            numeric = int if storage == 'int' else float
            fact['min'] = numeric(non_null.min())
            fact['max'] = numeric(non_null.max())
        facts[name] = fact

        if storage == 'empty' and policy.warn_on_empty_columns:
            findings.append(Finding('empty_column', 'warn',
                                    'column has no non-sentinel values', name))
        # a column whose only repeats are explained by exact duplicate rows
        # is unique on the deduplicated table
        dedup_unique = (not series.isna().any()
                        and masked_no_dup_rows[raw_name].nunique()
                        == len(masked_no_dup_rows))
        guess = _guess_semantic(storage, distinct, dedup_unique)
        if guess == 'constant' and policy.warn_on_constant_columns:
            findings.append(Finding('constant_column', 'warn',
                                    'column is constant', name))

        # interpretation precedence: override > declared > inferred
        semantic, source = guess, 'inferred'
        if name in declared and 'semantic_type' in declared[name]:
            semantic, source = declared[name]['semantic_type'], 'declared'
        if name in overrides and 'semantic_type' in overrides[name]:
            semantic, source = overrides[name]['semantic_type'], 'override'

        provenance: dict[str, str] = {
            'storage_type': 'observed',
            'semantic_type': source,
            'sentinels': (
                'override' if (name in overrides and 'sentinels' in overrides[name])
                else ('declared' if (name in declared and 'sentinels' in declared[name])
                      else 'none')),
        }
        contracts.append(ColumnContract(
            name=name, storage_type=storage, semantic_type=semantic,
            sentinels=sentinels_by_col[name], provenance=provenance))

    # -- declared-vs-observed disagreement becomes a finding, never a fix -----
    for name, spec in declared.items():
        if name not in facts:
            findings.append(Finding('declared_unknown_column', 'warn',
                                    'declared schema names a column not in '
                                    'the table', name))
            continue
        if 'storage_type' in spec and spec['storage_type'] != facts[name]['storage_type']:
            findings.append(Finding(
                'declared_storage_mismatch', 'warn',
                f'declared storage_type {spec["storage_type"]!r} but observed '
                f'{facts[name]["storage_type"]!r}; observed fact stands', name))
    for name in overrides:
        if name not in facts:
            findings.append(Finding('override_unknown_column', 'warn',
                                    'override names a column not in the table',
                                    name))


    # -- keys, duplicates, conflicts ------------------------------------------
    # Candidate keys are hints, never assertions about the observation grain.
    # Only the caller's explicit observation_key may produce a key stop.
    candidate_keys: list[str] = []
    for raw_name in masked.columns:
        name = str(raw_name)
        series = masked[raw_name]
        if (not n_rows or series.isna().any()
                or series.map(lambda value: isinstance(value, str) and not value.strip()).any()):
            continue
        if facts[name]['storage_type'] not in ('int', 'str'):
            continue
        dedup_unique = (masked_no_dup_rows[raw_name].nunique()
                        == len(masked_no_dup_rows))
        if dedup_unique:
            candidate_keys.append(name)
    if selected_key:
        severity = 'stop' if policy.stop_on_conflicting_keys else 'warn'
        key_frame = masked[list(selected_key)]
        for name in selected_key:
            if key_frame[name].isna().any():
                findings.append(Finding('missing_observation_key', severity,
                                        'selected observation key contains missing values', name))
            if key_frame[name].map(
                    lambda value: isinstance(value, str) and not value.strip()).any():
                findings.append(Finding('blank_observation_key', severity,
                                        'selected observation key contains blank values', name))
        if masked_no_dup_rows.duplicated(subset=list(selected_key), keep=False).any():
            findings.append(Finding(
                'conflicting_duplicate_key', severity,
                f'selected observation key {selected_key!r} repeats with '
                'different values in other columns',
                selected_key[0] if len(selected_key) == 1 else None))

    grain = (selected_key[0] if len(selected_key) == 1 else None) if selected_key else (
        candidate_keys[0] if candidate_keys else None)
    if not selected_key and not candidate_keys and n_rows and policy.warn_on_no_key:
        findings.append(Finding('no_candidate_key', 'warn',
                                'no candidate key; row identity is the row '
                                'number'))

    fingerprint = fingerprint_table(facts, n_rows, column_order)

    # -- gate ------------------------------------------------------------------
    stops = tuple(f for f in findings if f.severity == 'stop')
    warns = tuple(f for f in findings if f.severity == 'warn')
    if stops:
        gate = GateDecision('stop', stops + warns)
    elif warns:
        gate = GateDecision('warn', warns)
    else:
        gate = GateDecision('proceed', ())

    return StructureProfile(
        n_rows=n_rows, n_columns=n_columns, columns=tuple(contracts),
        facts=facts, candidate_keys=tuple(candidate_keys), grain=grain,
        exact_duplicate_rows=exact_dup_rows, fingerprint=fingerprint,
        findings=tuple(findings), gate=gate, observation_key=selected_key,
        data_fingerprint=content_fingerprint)

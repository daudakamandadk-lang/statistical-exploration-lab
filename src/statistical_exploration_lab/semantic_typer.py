"""Build step 2: semantic typer and ColumnProfile.

Decides how each column behaves so later steps know which tests and plots
apply. Domain-neutral: no column name has special meaning. Every guess
records which rule fired (principle 6). Input is the Step 1 StructureProfile
plus the same table the caller already profiled — the typer re-uses Step 1
facts and never re-measures them; the table is needed only for value-level
operations (sentinel scan, date-parse check, skew) that facts don't carry.

See docs/TYPING.md for the accepted input form, result meaning and limits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import pandas as pd

from .contract import (Finding, StructureProfile, _Inspectable, _freeze,
                       _mask_sentinels, _validate_column_names, data_fingerprint)

__all__ = [
    'TyperPolicy',
    'TypedColumn',
    'TypeProfile',
    'type_columns',
]


@dataclass(frozen=True)
class TyperPolicy(_Inspectable):
    """Thresholds and candidate lists live in config, not code (principle 4)."""

    id_uniqueness_ratio: float = 0.95
    few_int_levels: int = 20
    count_skew_min: float = 1.0
    date_parse_rate: float = 0.95
    free_text_mean_length: int = 20
    free_text_uniqueness_min: float = 0.5
    min_values_for_skew: int = 8
    sentinel_values: tuple = (-999, -99, -1, 9999, 99999)
    sentinel_strings: tuple = ('UNK', 'UNKNOWN', 'N/A', 'NA', 'NULL', 'NONE', '')
    apply_inferred_sentinels: bool = False

    def __post_init__(self):
        if type(self.apply_inferred_sentinels) is not bool:
            raise TypeError('apply_inferred_sentinels must be True or False')


@dataclass(frozen=True)
class TypedColumn(_Inspectable):
    """One column's typed contract with the rule rationale recorded."""

    name: str
    storage_type: str
    semantic_type: str | None
    sentinels: tuple
    sentinel_provenance: Mapping[str, str]  # sentinel value (as str) -> source
    semantic_source: str  # 'inferred' | 'declared' | 'override'
    rationale: str
    sentinel_candidates: tuple = ()

    def __post_init__(self):
        object.__setattr__(self, 'sentinel_provenance', _freeze(self.sentinel_provenance))


@dataclass(frozen=True)
class TypeProfile(_Inspectable):
    """Typed contracts plus the typer's findings. Step 1 facts are unchanged."""

    columns: tuple[TypedColumn, ...]
    findings: tuple[Finding, ...]
    data_fingerprint: str = ''

    def by_name(self) -> dict[str, TypedColumn]:
        return {c.name: c for c in self.columns}


def _guess_sentinels(series: pd.Series, storage: str,
                     policy: TyperPolicy) -> tuple[list, list[Finding], str]:
    """Find sentinel candidates in one unmasked column.

    Returns (guessed values, findings, column name is added by caller).
    Matching is exact for numerics and case-insensitive (trimmed) for strings.
    """
    guessed: list = []
    findings: list[Finding] = []
    non_null = series.dropna()
    if non_null.empty:
        return guessed, findings, ''
    if storage in ('int', 'float'):
        for candidate in policy.sentinel_values:
            count = int((series == candidate).sum())
            if count:
                guessed.append(candidate)
                findings.append(Finding(
                    'sentinel_candidate', 'warn',
                    f'sentinel candidate {candidate!r} in {count} row(s); '
                    f'confirm or override'))
    elif storage == 'str':
        normalized = series.str.strip().str.upper()
        for candidate in policy.sentinel_strings:
            count = int((normalized == candidate.upper()).sum())
            if count:
                guessed.append(candidate)
                findings.append(Finding(
                    'sentinel_candidate', 'warn',
                    f'sentinel candidate {candidate!r} in {count} row(s); '
                    f'confirm or override'))
    return guessed, findings, ''


def _date_parse_rate(values: pd.Series) -> float:
    """Share of non-null string values that parse as dates."""
    if values.empty:
        return 0.0
    parsed = pd.to_datetime(values, errors='coerce', format='mixed')
    return float(parsed.notna().mean())


def _after_id_rules(name: str, storage: str, masked: pd.Series,
                    policy: TyperPolicy) -> tuple[str, str, list[Finding]]:
    """Rules evaluated after the id/date checks (count through fallback)."""
    non_null = masked.dropna()
    distinct = int(non_null.nunique())
    n_valid = len(non_null)
    if n_valid == 0:
        return 'empty', 'no usable values after masking', [
            Finding('empty_column', 'warn',
                    'no usable values after masking sentinels', name)]
    if distinct <= 1:
        return 'constant', f'1 distinct value in {n_valid} row(s)', [
            Finding('constant_column', 'warn',
                    'single distinct value; carries no information', name)]
    if storage == 'int' and (masked.dropna() >= 0).all():
        levels = distinct
        if levels > policy.few_int_levels and n_valid >= policy.min_values_for_skew:
            skew = float(pd.to_numeric(non_null).skew())
            if skew >= policy.count_skew_min:
                return ('count',
                        f'non-negative int, {levels} levels, skew {skew:.2f}',
                        [])
    if storage == 'int' and distinct <= policy.few_int_levels:
        extra = [Finding(
            'confirm_type', 'warn',
            f'int column with {distinct} level(s); confirm whether codes '
            f'or measurements', name)]
        return ('ordinal_nominal_candidate',
                f'int with {distinct} level(s) <= {policy.few_int_levels}; '
                f'needs human confirmation', extra)
    if storage == 'float':
        return 'continuous', f'float with {distinct} distinct value(s)', []
    if storage == 'int':
        return 'continuous', f'int with {distinct} distinct value(s)', []
    if storage == 'str':
        return 'nominal', f'string with {distinct} distinct value(s)', []
    if storage == 'empty':
        return 'empty', 'no usable values after masking', [
            Finding('empty_column', 'warn',
                    'no usable values after masking sentinels', name)]
    return 'nominal', f'fallback for storage {storage!r}', []


def _decide_type(name: str, storage: str, masked: pd.Series,
                 dedup_unique: bool,
                 policy: TyperPolicy) -> tuple[str, str, list[Finding]]:
    """Apply the type-decision table top-down; first match wins."""
    non_null = masked.dropna()
    distinct = int(non_null.nunique())
    n_valid = len(non_null)
    unique_ratio = (distinct / n_valid) if n_valid else 0.0
    if n_valid == 0:
        return 'empty', 'no usable values after masking', [
            Finding('empty_column', 'warn',
                    'no usable values after masking sentinels', name)]
    if distinct <= 1:
        return 'constant', f'1 distinct value in {n_valid} row(s)', [
            Finding('constant_column', 'warn',
                    'single distinct value; carries no information', name)]
    if storage == 'mixed':
        return ('mixed', 'mixed observed storage; typer refuses to guess', [
            Finding('mixed_type', 'warn',
                    'mixed value types; resolve before typing', name)])
    if storage == 'bool':
        return 'binary', 'boolean storage', []
    if storage == 'date':
        return 'date', 'date storage', []
    if distinct == 2:
        return 'binary', f'2 distinct values in {n_valid} row(s)', []
    if storage == 'str':
        rate = _date_parse_rate(non_null.astype('string'))
        if rate >= policy.date_parse_rate:
            return 'date', f'{rate:.0%} of values parse as dates', []
        mean_len = float(non_null.astype(str).str.len().mean()) if n_valid else 0.0
        if (unique_ratio >= policy.free_text_uniqueness_min
                and mean_len >= policy.free_text_mean_length):
            return ('free_text',
                    f'string, unique ratio {unique_ratio:.2f}, '
                    f'mean length {mean_len:.1f}', [])
    if storage in ('int', 'str') and (
            unique_ratio >= policy.id_uniqueness_ratio or dedup_unique):
        return ('id_candidate',
                f'unique ratio {unique_ratio:.2f} '
                f'(dedup-unique={dedup_unique})', [])
    return _after_id_rules(name, storage, masked, policy)


def type_columns(step1: StructureProfile,
                 table, policy=None) -> TypeProfile:
    """Decide how each column behaves from Step 1 plus value-level checks.

    Step 1 facts are re-used. The exact table snapshot is checked before
    value-level typing; reprofile after changing values, selection, dtypes or
    index. A stopped gate must be resolved first. Inferred sentinels remain
    suggestions unless apply_inferred_sentinels is explicitly enabled.
    """
    if not isinstance(step1, StructureProfile):
        raise TypeError('step1 must be a StructureProfile from profile_structure')
    if step1.gate.status == 'stop':
        reasons = ', '.join(finding.code for finding in step1.gate.reasons)
        raise ValueError(f'Profile gate stopped ({reasons}); resolve it and reprofile before typing')
    policy = policy if policy is not None else TyperPolicy()
    if not isinstance(policy, TyperPolicy):
        raise TypeError('policy must be a TyperPolicy')
    import pandas as _pd
    if not isinstance(table, _pd.DataFrame):
        table = _pd.DataFrame(table)
    _validate_column_names(table)
    if not step1.data_fingerprint or data_fingerprint(table) != step1.data_fingerprint:
        raise ValueError('Table snapshot differs from the profile; reprofile the selected table before typing')
    dedup = table.drop_duplicates()
    typed: list[TypedColumn] = []
    findings: list[Finding] = []
    for contract in step1.columns:
        name = contract.name
        storage = contract.storage_type
        if name in step1.facts:
            storage = step1.facts[name]['storage_type']
        series = table[name]
        dedup_unique = False
        if name in dedup.columns and len(dedup) and len(table.columns) > 1:
            # Single-column tables always dedup to unique values, so the
            # dedup-unique signal is meaningless there; rely on the ratio.
            try:
                dedup_unique = bool(dedup[name].nunique() == len(dedup))
            except TypeError:
                dedup_unique = False
        base_source = contract.provenance.get('sentinels', 'none')
        if base_source in ('override', 'declared'):
            guessed, guess_findings = [], []
        else:
            guessed, guess_findings, _ = _guess_sentinels(series, storage, policy)
        for finding in guess_findings:
            treatment = ('applied by explicit policy' if policy.apply_inferred_sentinels
                         else 'suggestion only; not applied')
            findings.append(Finding(finding.code, finding.severity,
                                    f'{finding.message}; {treatment}', name))
        base = tuple(contract.sentinels)
        new_guessed = tuple(g for g in guessed if g not in base)
        sentinels = base + new_guessed if policy.apply_inferred_sentinels else base
        sentinel_prov: dict[str, str] = {}
        for sentinel in base:
            sentinel_prov[str(sentinel)] = base_source
        if policy.apply_inferred_sentinels:
            for sentinel in new_guessed:
                sentinel_prov[str(sentinel)] = 'inferred'
        source = contract.provenance.get('semantic_type', 'none')
        if source in ('override', 'declared') and contract.semantic_type:
            typed.append(TypedColumn(name=name, storage_type=storage, semantic_type=contract.semantic_type, sentinels=sentinels, sentinel_provenance=sentinel_prov, semantic_source=source, rationale=f'kept from contract ({source})', sentinel_candidates=new_guessed))
            continue
        masked = _mask_sentinels(series, sentinels)
        semantic, rationale, extra = _decide_type(name, storage, masked, dedup_unique, policy)
        findings.extend(extra)
        typed.append(TypedColumn(name=name, storage_type=storage, semantic_type=semantic, sentinels=sentinels, sentinel_provenance=sentinel_prov, semantic_source='inferred', rationale=f'{semantic}: {rationale}', sentinel_candidates=new_guessed))
    return TypeProfile(columns=tuple(typed), findings=tuple(findings),
                       data_fingerprint=step1.data_fingerprint)

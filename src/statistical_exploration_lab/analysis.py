"""Read one CSV snapshot and coordinate independently callable descriptive engines."""

import csv
from copy import deepcopy
import hashlib
import io
import platform
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from math import isfinite
from pathlib import Path

import numpy as np
import pandas as pd

from .configuration import load_configuration, validate_configuration
from .distributions import categorical_summary, numeric_summary
from .relationships import categorical_relationship, group_summary, numeric_relationship


def analyze_frame(data, config, source=None):
    """Analyze a declared single-table grain; preserve the caller's DataFrame."""
    validate_configuration(config)
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a pandas DataFrame')
    if not data.columns.is_unique:
        raise ValueError('Input column names must be unique')
    declared = [field for fields in config['fields'].values() for field in fields]
    missing = set(declared) - set(data.columns)
    if missing:
        raise ValueError(f'Configured fields are absent: {sorted(missing)}')
    keys = config['observation']['key']
    if data[keys].isna().any().any():
        raise ValueError('Observation keys must be nonmissing')
    if any(isinstance(value, str) and not value.strip()
           for column in keys for value in data[column]):
        raise ValueError('Observation keys must be nonblank')
    if data.duplicated(subset=keys).any():
        raise ValueError('Observation keys must be unique at the declared grain')
    fields = config['fields']
    relationships = config['relationships']
    minimum = config['minimum_samples']
    report = {
        'report_version': 1,
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'question': config['question'],
        'configuration': deepcopy(config),
        'source': deepcopy(source) if source else {'kind': 'in_memory'},
        'rows': len(data),
        'ignored_fields': [str(name) for name in data.columns if name not in declared],
        'runtime': {'python': platform.python_version(), 'pandas': pd.__version__,
                    'numpy': np.__version__},
        'missingness': 'Pairwise finite numeric values; complete categorical pairs; no imputation',
        'numeric_distributions': {name: numeric_summary(data[name]) for name in fields['numeric']},
        'categorical_distributions': {
            name: categorical_summary(data[name]) for name in fields['categorical']},
        'numeric_relationships': [
            numeric_relationship(data, left, right, methods=relationships['numeric_methods'],
                                 minimum=minimum['numeric_pair'])
            for left, right in relationships['numeric_pairs']],
        'categorical_relationships': [
            categorical_relationship(data, left, right, minimum=minimum['categorical_pair'])
            for left, right in relationships['categorical_pairs']],
        'group_summaries': [
            group_summary(data, item['group_by'], item['measure'], minimum=minimum['group'])
            for item in relationships['group_summaries']],
        'limitations': ['Descriptive associations do not establish causation.',
                        'Different pairs may use different observations.',
                        'No hypothesis tests, fitted models, joins or automated decisions are performed.'],
    }
    if report['source'].get('kind') == 'generated_demo':
        report['limitations'].append('Demo patterns are deliberately generated, not empirical evidence.')
    return report


def read_csv_snapshot(path, config):
    """Hash and parse the same bytes, preserving identifiers and literal category labels."""
    raw = Path(path).read_bytes()
    text = raw.decode('utf-8-sig')
    reader = csv.reader(io.StringIO(text), strict=True)
    try:
        header = next(reader)
    except StopIteration as exc:
        raise ValueError('Input CSV has no header') from exc
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV header quoting: {exc}') from exc
    if not header or len(header) != len(set(header)) or any(not name.strip() for name in header):
        raise ValueError('CSV column names must be nonblank and unique')
    try:
        for row_number, row in enumerate(reader, start=2):
            if len(row) != len(header):
                raise ValueError(f'CSV record {row_number} has {len(row)} fields; expected {len(header)}')
    except csv.Error as exc:
        raise ValueError(f'Invalid CSV quoting: {exc}') from exc
    data = pd.read_csv(io.StringIO(text), dtype='string', keep_default_na=False,
                       na_values=[''], skip_blank_lines=False)
    numeric_fields = config['fields']['numeric']
    for name in numeric_fields:
        if name not in data:
            raise ValueError(f'Configured field is absent: {name}')
        # Check integer-valued text before pandas can round a mixed numeric column.
        for value in data[name].dropna():
            try:
                exact = Decimal(value)
            except InvalidOperation:
                continue  # Strict numeric parsing below reports invalid text.
            if exact.is_finite() and exact == exact.to_integral_value():
                approximate = float(exact)
                if not isfinite(approximate) or Decimal(int(approximate)) != exact:
                    raise ValueError(f'Numeric field {name!r}: integer exceeds exact floating-point precision')
        try:
            data[name] = pd.to_numeric(data[name], errors='raise')
        except (TypeError, ValueError) as exc:
            raise ValueError(f'Numeric field {name!r} contains invalid numeric text') from exc
    evidence = {'kind': 'csv_snapshot', 'name': Path(path).name,
                'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}
    return data, evidence


def analyze_config_file(config_path):
    config_path = Path(config_path)
    config = load_configuration(config_path)
    source_path = Path(config['input']['path'])
    if not source_path.is_absolute():
        source_path = config_path.parent / source_path
    data, source = read_csv_snapshot(source_path, config)
    return analyze_frame(data, config, source)

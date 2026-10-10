"""Thin command-line coordination; neutral demo inputs live only in a temporary folder."""

import argparse
import json
import sys
import tempfile
from pathlib import Path

import pandas as pd

from .analysis import analyze_config_file, analyze_frame, read_csv_snapshot
from .reporting import write_report


def demo_configuration():
    return {
        'version': 1,
        'question': 'How do two measurements relate across generated groups?',
        'input': {'path': 'demo.csv'},
        'observation': {'grain': 'one row per observation', 'unit': 'observation',
                        'key': ['record_id']},
        'fields': {'identifiers': ['record_id'], 'numeric': ['measurement_x', 'measurement_y'],
                   'categorical': ['segment', 'group'], 'excluded': []},
        'minimum_samples': {'numeric_pair': 3, 'categorical_pair': 3, 'group': 2},
        'relationships': {'numeric_pairs': [['measurement_x', 'measurement_y']],
                          'numeric_methods': ['pearson', 'spearman'],
                          'categorical_pairs': [['segment', 'group']],
                          'group_summaries': [{'group_by': 'segment', 'measure': 'measurement_x'}]},
    }


def run_demo():
    config = demo_configuration()
    values = list(range(1, 13))
    data = pd.DataFrame({'record_id': [f'{value:03}' for value in values],
                         'measurement_x': values, 'measurement_y': [value ** 2 for value in values],
                         'segment': ['A' if value <= 6 else 'B' for value in values],
                         'group': ['odd' if value % 2 else 'even' for value in values]})
    data.loc[11, 'measurement_y'] = float('nan')
    with tempfile.TemporaryDirectory(prefix='statistical-lab-demo-') as folder:
        source = Path(folder) / 'demo.csv'
        data.to_csv(source, index=False)
        selected, evidence = read_csv_snapshot(source, config)
        evidence['kind'] = 'generated_demo'
        return analyze_frame(selected, config, evidence)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Explore declared CSV fields with descriptive statistics.')
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--config', type=Path, help='Version 1 JSON configuration; input relative to this file')
    selection.add_argument('--demo', action='store_true', help='Generate a neutral temporary sample')
    parser.add_argument('--output', required=True, type=Path, help='New local report folder; existing folders refused')
    args = parser.parse_args(argv)
    try:
        report = run_demo() if args.demo else analyze_config_file(args.config)
        window = write_report(report, args.output)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        print(f'Analysis failed: {exc}', file=sys.stderr)
        return 2
    print(f'Report window: {window.resolve()}')
    print(f'JSON evidence: {(args.output / "report.json").resolve()}')
    return 0

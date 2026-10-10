"""Input, configuration, output and CLI boundaries that can change analytical meaning."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from statistical_exploration_lab.analysis import analyze_config_file, analyze_frame
from statistical_exploration_lab.cli import demo_configuration, main, run_demo
from statistical_exploration_lab.configuration import load_configuration, validate_configuration
from statistical_exploration_lab.reporting import render_html, write_report


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory()
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name)
        self.config = demo_configuration()
        self.config['input']['path'] = 'sample.csv'
        self.source = self.root / 'sample.csv'
        self.source.write_text('record_id,measurement_x,measurement_y,segment,group,unused\n'
                               '001,1,1,NA,odd,x\n002,2,4,NA,even,x\n'
                               '003,3,9,A,odd,x\n004,4,,A,even,x\n', encoding='utf-8')
        self.config_path = self.root / 'job.json'
        self.save_config()

    def save_config(self):
        self.config_path.write_text(json.dumps(self.config), encoding='utf-8')

    def test_csv_snapshot_preserves_bytes_labels_and_pair_counts(self):
        before = self.source.read_bytes()
        report = analyze_config_file(self.config_path)
        self.assertEqual(self.source.read_bytes(), before)
        self.assertEqual(report['source']['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(report['ignored_fields'], ['unused'])
        categories = report['categorical_distributions']['segment']['categories']
        self.assertEqual(categories[0]['value'], 'string:NA')
        self.assertEqual(categories[0]['count'], 2)
        self.assertEqual(report['numeric_relationships'][0]['usable_count'], 3)
        self.assertAlmostEqual(report['numeric_relationships'][0]['coefficients']['spearman'], 1)

    def test_leading_zero_identifiers_are_not_collapsed(self):
        self.source.write_text('record_id,measurement_x,measurement_y,segment,group\n'
                               '01,1,2,A,B\n1,2,4,A,B\n001,3,6,A,B\n', encoding='utf-8')
        self.assertEqual(analyze_config_file(self.config_path)['rows'], 3)

    def test_duplicate_or_missing_keys_fail_before_output(self):
        original = self.source.read_text(encoding='utf-8')
        for changed in (original.replace('002,', '001,'), original.replace('002,', ','),
                        original.replace('002,', '   ,')):
            with self.subTest(changed=changed):
                self.source.write_text(changed, encoding='utf-8')
                with self.assertRaisesRegex(ValueError, 'keys'):
                    analyze_config_file(self.config_path)

    def test_duplicate_csv_headers_and_invalid_numeric_text_are_rejected(self):
        original = self.source.read_text(encoding='utf-8')
        self.source.write_text(original.replace(',unused', ',group'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'column names'):
            analyze_config_file(self.config_path)
        self.source.write_text(original.replace('002,2,4', '002,true,4'), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'invalid numeric text'):
            analyze_config_file(self.config_path)

    def test_ragged_or_badly_quoted_csv_cannot_silently_change_observations(self):
        original = self.source.read_text(encoding='utf-8')
        cases = [original.replace('001,1,1,NA,odd,x', '001,1,1,NA,odd,x,extra'),
                 original.replace('001,1,1,NA,odd,x', '001,1,1,NA,odd'),
                 original.replace('001,1,1,NA,odd,x', '001,1,1,NA,odd,"unclosed'),
                 '"unclosed header\n' + original]
        for content in cases:
            with self.subTest(content=content), self.assertRaisesRegex(ValueError, 'CSV'):
                self.source.write_text(content, encoding='utf-8')
                analyze_config_file(self.config_path)

    def test_large_integer_text_cannot_lose_rank_in_a_mixed_numeric_column(self):
        original = self.source.read_text(encoding='utf-8')
        for token in ('1152921504606846977', '1152921504606846977.0', '1.152921504606846977e18'):
            changed = original.replace('001,1,1', f'001,{token},1').replace('002,2,4', '002,1.5,4')
            self.source.write_text(changed, encoding='utf-8')
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, 'precision'):
                analyze_config_file(self.config_path)

    def test_header_only_input_is_reported_as_empty_with_explicit_skips(self):
        self.source.write_text(self.source.read_text(encoding='utf-8').splitlines()[0] + '\n',
                               encoding='utf-8')
        report = analyze_config_file(self.config_path)
        self.assertEqual(report['rows'], 0)
        self.assertEqual(report['numeric_relationships'][0]['status'], 'skipped')
        self.assertEqual(report['categorical_distributions']['segment']['usable_count'], 0)
        json.dumps(report, allow_nan=False)

    def test_report_configuration_is_a_snapshot_of_the_reviewed_settings(self):
        data = pd.DataFrame({'record_id': ['1', '2', '3'], 'measurement_x': [1, 2, 3],
                             'measurement_y': [2, 4, 6], 'segment': ['A', 'A', 'B'],
                             'group': ['odd', 'even', 'odd']})
        report = analyze_frame(data, self.config)
        self.config['minimum_samples']['numeric_pair'] = 100
        self.assertEqual(report['configuration']['minimum_samples']['numeric_pair'], 3)

    def test_configuration_rejects_unimplemented_settings_and_role_collisions(self):
        cases = []
        unknown = deepcopy(self.config)
        unknown['selection'] = {'joins': []}
        cases.append(unknown)
        collision = deepcopy(self.config)
        collision['fields']['numeric'].append('record_id')
        cases.append(collision)
        minimum = deepcopy(self.config)
        minimum['minimum_samples']['numeric_pair'] = True
        cases.append(minimum)
        bad_pair = deepcopy(self.config)
        bad_pair['relationships']['numeric_pairs'] = [['measurement_x', 'record_id']]
        cases.append(bad_pair)
        for config in cases:
            with self.subTest(config=config), self.assertRaises(ValueError):
                validate_configuration(config)

    def test_duplicate_json_settings_are_rejected(self):
        self.config_path.write_text('{"version":1,"version":1}', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON'):
            load_configuration(self.config_path)

    def test_composite_key_and_in_memory_data_preservation(self):
        config = deepcopy(self.config)
        config['fields']['identifiers'].append('visit')
        config['observation']['key'] = ['record_id', 'visit']
        data = pd.DataFrame({'record_id': ['a', 'a', 'b'], 'visit': [1, 2, 1],
                             'measurement_x': [1, 2, 3], 'measurement_y': [2, 4, 6],
                             'segment': ['A', 'A', 'B'], 'group': ['odd', 'even', 'odd']})
        before = data.copy(deep=True)
        self.assertEqual(analyze_frame(data, config)['rows'], 3)
        pd.testing.assert_frame_equal(data, before)

    def test_report_window_escapes_questions_and_category_labels(self):
        report = run_demo()
        report['question'] = '<script>alert("question")</script>'
        report['categorical_distributions']['segment']['categories'][0]['value'] = '<img src=x onerror=alert(1)>'
        page = render_html(report)
        self.assertNotIn('<script>', page)
        self.assertNotIn('<img', page)
        self.assertIn('&lt;script&gt;', page)
        self.assertIn('Content-Security-Policy', page)

    def test_output_refuses_existing_directory_and_preserves_prior_report(self):
        output = self.root / 'analysis'
        window = write_report(run_demo(), output)
        before = window.read_bytes()
        with self.assertRaises(FileExistsError):
            write_report(run_demo(), output)
        self.assertEqual(window.read_bytes(), before)
        self.assertEqual(set(path.name for path in output.iterdir()), {'report.json', 'report.html'})

    def test_failed_report_write_cleans_only_new_output(self):
        output = self.root / 'analysis'
        real_open = Path.open

        def fail_window(path, *args, **kwargs):
            if path.name == 'report.html':
                raise OSError('simulated output failure')
            return real_open(path, *args, **kwargs)

        with patch.object(Path, 'open', fail_window), self.assertRaisesRegex(OSError, 'simulated'):
            write_report(run_demo(), output)
        self.assertFalse(output.exists())
        self.assertTrue(self.source.exists())

    def test_cli_demo_writes_reports_without_bundled_data(self):
        output = self.root / 'demo-report'
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(['--demo', '--output', str(output)]), 0)
        report = json.loads((output / 'report.json').read_text(encoding='utf-8'))
        self.assertEqual(report['source']['kind'], 'generated_demo')
        self.assertEqual(report['numeric_relationships'][0]['usable_count'], 11)
        self.assertEqual(list(output.glob('*.csv')), [])
        self.assertNotIn('NaN', (output / 'report.json').read_text(encoding='utf-8'))

    def test_cli_input_error_leaves_no_output(self):
        self.config['fields']['numeric'].append('absent')
        self.save_config()
        output = self.root / 'bad-report'
        with redirect_stderr(io.StringIO()) as errors:
            self.assertEqual(main(['--config', str(self.config_path), '--output', str(output)]), 2)
        self.assertIn('absent', errors.getvalue())
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()

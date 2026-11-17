"""Check the retained display contract using saved values, never calculators."""

from copy import deepcopy
from html.parser import HTMLParser
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from statistical_exploration_lab.reporting import render_html, write_report


def saved_report():
    """Static legacy-format evidence for presentation tests, not analyzed data.

    Coefficients, summaries and counts below are arbitrary saved examples. They
    exercise display mapping and preservation; no source observations exist.
    This fixture does not define a future engine configuration contract.
    """
    return {
        'report_version': 1,
        'generated_at': '2026-10-12T00:00:00+00:00',
        'question': 'Display saved evidence without recomputing it',
        'configuration': {
            'version': 1,
            'question': 'Display saved evidence without recomputing it',
            'input': {'path': 'not-opened.csv'},
            'observation': {'grain': 'one saved fixture row', 'unit': 'fixture',
                            'key': ['record_id']},
            'fields': {'identifiers': ['record_id'],
                       'numeric': ['measure_a', 'measure_b', 'measure_c'],
                       'categorical': ['segment', 'region'], 'excluded': []},
            'minimum_samples': {'numeric_pair': 3, 'categorical_pair': 3, 'group': 2},
            'relationships': {
                'numeric_pairs': [['measure_a', 'measure_b']],
                'numeric_methods': ['pearson', 'spearman'],
                'categorical_pairs': [['segment', 'region']],
                'group_summaries': [{'group_by': 'segment', 'measure': 'measure_a'}],
            },
        },
        'source': {'kind': 'presentation_fixture', 'name': 'Static saved display values'},
        'rows': 7,
        'ignored_fields': [],
        'runtime': {'fixture': 'static; no analytical runtime'},
        'missingness': 'Display saved counts and exclusions; no imputation',
        'numeric_distributions': {
            'measure_a': {
                'usable_count': 5, 'missing_count': 2, 'nonfinite_count': 0,
                'mean': 10.5, 'median': 10, 'min': 2, 'q25': 5, 'q75': 15,
                'max': 20, 'std': 4.5, 'status': 'ok', 'reason': None,
            },
            'measure_b': {
                'usable_count': 6, 'missing_count': 1, 'nonfinite_count': 0,
                'mean': 12, 'median': 11, 'min': 3, 'q25': 8, 'q75': 16,
                'max': 23, 'std': 5, 'status': 'ok', 'reason': None,
            },
            'measure_c': {
                'usable_count': 7, 'missing_count': 0, 'nonfinite_count': 0,
                'mean': 8, 'median': 8, 'min': 1, 'q25': 4, 'q75': 12,
                'max': 15, 'std': 3, 'status': 'ok', 'reason': None,
            },
        },
        'categorical_distributions': {
            'segment': {
                'usable_count': 5, 'missing_count': 2, 'status': 'ok', 'reason': None,
                'proportion_denominator': 'usable category observations',
                'categories': [{'value': 'A', 'count': 3, 'proportion': .6},
                               {'value': 'B', 'count': 2, 'proportion': .4}],
            },
            'region': {
                'usable_count': 5, 'missing_count': 2, 'status': 'ok', 'reason': None,
                'proportion_denominator': 'usable category observations',
                'categories': [{'value': 'North', 'count': 3, 'proportion': .6},
                               {'value': 'South', 'count': 2, 'proportion': .4}],
            },
        },
        'numeric_relationships': [{
            'left': 'measure_a', 'right': 'measure_b',
            'coefficients': {'pearson': .625, 'spearman': -.25},
            'total_count': 7, 'usable_count': 5, 'excluded_count': 2,
            'status': 'ok', 'reason': None,
        }],
        'categorical_relationships': [{
            'left': 'segment', 'right': 'region', 'usable_count': 5,
            'excluded_count': 2, 'status': 'ok', 'reason': None,
            'percentage_denominator': 'the row category',
            'row_categories': ['A', 'B'], 'column_categories': ['North', 'South'],
            'counts': [[1, 2], [2, 0]],
            'row_percentages': [[33.33, 66.67], [100, 0]],
        }],
        'group_summaries': [{
            'group': 'segment', 'measure': 'measure_a', 'status': 'ok', 'reason': None,
            'missing_group_count': 1,
            'groups': [
                {'value': 'A', 'total_count': 4, 'usable_count': 3,
                 'missing_count': 1, 'nonfinite_count': 0, 'status': 'ok', 'reason': None,
                 'statistics': {'mean': 10, 'median': 9, 'std': 3}},
                {'value': 'B', 'total_count': 2, 'usable_count': 1,
                 'missing_count': 1, 'nonfinite_count': 0, 'status': 'skipped',
                 'reason': 'insufficient_samples',
                 'statistics': {'mean': None, 'median': None, 'std': None}},
            ],
        }],
        'limitations': ['Static presentation fixture; no calculator was executed.',
                        'Saved coefficients are display examples, not empirical findings.'],
    }


class ReportHTML(HTMLParser):
    """Read table cells and attributes without coupling checks to CSS."""

    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.tags = []
        self.sections = []
        self.table = self.row = self.cell = None
        self.feed(page)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append(tag)
        if tag == 'section':
            self.sections.append(attrs.get('id'))
        elif tag == 'table':
            self.table = {'attrs': attrs, 'section': self.sections[-1], 'rows': []}
        elif tag == 'tr' and self.table is not None:
            self.row = []
        elif tag in ('th', 'td') and self.row is not None:
            self.cell = {'attrs': attrs, 'text': ''}

    def handle_data(self, data):
        if self.cell is not None:
            self.cell['text'] += data

    def handle_endtag(self, tag):
        if tag in ('th', 'td') and self.cell is not None:
            self.row.append(self.cell)
            self.cell = None
        elif tag == 'tr' and self.row is not None:
            self.table['rows'].append(self.row)
            self.row = None
        elif tag == 'table' and self.table is not None:
            self.tables.append(self.table)
            self.table = None
        elif tag == 'section':
            self.sections.pop()


class ReportingTests(unittest.TestCase):
    def numeric_table(self, page):
        tables = [table for table in page.tables
                  if table['section'] == 'numeric-relationships'
                  and table['attrs'].get('class') != 'heatmap']
        self.assertEqual(len(tables), 1)
        return tables[0]

    def maps(self, page):
        return [table for table in page.tables if table['attrs'].get('class') == 'heatmap']

    def matrix_cell(self, table, left, right):
        headings = [cell['text'] for cell in table['rows'][0]]
        row = next(row for row in table['rows'][1:] if row[0]['text'] == left)
        return row[headings.index(right)]

    def test_saved_coefficients_and_counts_keep_their_display_mapping(self):
        page = ReportHTML(render_html(saved_report()))
        table = self.numeric_table(page)
        self.assertEqual([cell['text'] for cell in table['rows'][0]],
                         ['Left', 'Right', 'Pearson', 'Spearman', 'Total rows',
                          'Usable pairs', 'Excluded rows', 'Status / reason'])
        self.assertEqual([cell['text'] for cell in table['rows'][1]],
                         ['measure_a', 'measure_b', '0.625', '-0.25', '7', '5', '2', 'ok'])
        categories = next(table for table in page.tables
                          if table['section'] == 'categorical-relationships')
        self.assertEqual([cell['text'] for cell in categories['rows'][1]],
                         ['A', '1 (33.33%)', '2 (66.67%)'])
        groups = next(table for table in page.tables if table['section'] == 'group-summaries')
        self.assertEqual([cell['text'] for cell in groups['rows'][2]][:5],
                         ['B', '2', '1', '1', '0'])
        self.assertEqual(groups['rows'][2][-1]['text'], 'skipped: insufficient_samples')

    def test_selected_maps_preserve_values_counts_and_unrequested_states(self):
        page = ReportHTML(render_html(saved_report()))
        maps = self.maps(page)
        self.assertEqual(len(maps), 2)
        for table, coefficient in zip(maps, ['0.625', '-0.25']):
            self.assertEqual([cell['text'] for cell in table['rows'][0]],
                             ['Field', 'measure_a', 'measure_b', 'measure_c'])
            forward = self.matrix_cell(table, 'measure_a', 'measure_b')
            reverse = self.matrix_cell(table, 'measure_b', 'measure_a')
            self.assertEqual(forward['text'], coefficient)
            self.assertEqual(reverse['text'], coefficient)
            self.assertEqual(forward['attrs']['data-state'], 'coefficient')
            self.assertIn('Usable pairs 5 of 7; excluded rows 2; status ok',
                          forward['attrs']['title'])
            unrequested = self.matrix_cell(table, 'measure_a', 'measure_c')
            self.assertEqual(unrequested['text'], 'Not requested')
            self.assertEqual(unrequested['attrs']['data-state'], 'not-requested')
            diagonal = self.matrix_cell(table, 'measure_a', 'measure_a')
            self.assertEqual(diagonal['text'], 'Same field')
            self.assertEqual(diagonal['attrs']['data-state'], 'same-field')

    def test_method_subset_and_optional_maps_do_not_change_saved_evidence(self):
        report = saved_report()
        report['configuration']['relationships']['numeric_methods'] = ['spearman']
        report['numeric_relationships'][0]['coefficients'] = {'spearman': -.25}
        page = ReportHTML(render_html(report))
        self.assertEqual(len(self.maps(page)), 1)
        self.assertEqual([cell['text'] for cell in self.numeric_table(page)['rows'][1]][2:4],
                         ['Not requested', '-0.25'])
        self.assertIn('Spearman', self.matrix_cell(self.maps(page)[0], 'measure_a', 'measure_b')
                      ['attrs']['aria-label'])
        without_maps = ReportHTML(render_html(report, include_heatmaps=False))
        self.assertEqual(self.maps(without_maps), [])
        self.assertEqual(self.numeric_table(without_maps)['rows'], self.numeric_table(page)['rows'])

    def test_skipped_and_partial_results_keep_reasons_and_available_values(self):
        for coefficients in ({'pearson': None, 'spearman': None},
                             {'pearson': None, 'spearman': -.25}):
            with self.subTest(coefficients=coefficients):
                report = saved_report()
                pair = report['numeric_relationships'][0]
                pair.update(coefficients=coefficients, status='skipped',
                            reason='saved_result_unavailable')
                page = ReportHTML(render_html(report))
                row = [cell['text'] for cell in self.numeric_table(page)['rows'][1]]
                self.assertEqual(row[2], 'Skipped: saved_result_unavailable')
                self.assertEqual(row[3], '-0.25' if coefficients['spearman'] is not None
                                 else 'Skipped: saved_result_unavailable')
                self.assertEqual(row[4:], ['7', '5', '2', 'skipped: saved_result_unavailable'])
                maps = self.maps(page)
                self.assertEqual(self.matrix_cell(maps[0], 'measure_a', 'measure_b')
                                 ['attrs']['data-state'], 'skipped')
                self.assertEqual(self.matrix_cell(maps[1], 'measure_a', 'measure_b')
                                 ['attrs']['data-state'],
                                 'coefficient' if coefficients['spearman'] is not None else 'skipped')
                self.assertEqual(self.matrix_cell(maps[0], 'measure_a', 'measure_c')
                                 ['attrs']['data-state'], 'not-requested')

    def test_labels_are_escaped_and_rendering_does_not_mutate_saved_report(self):
        report = saved_report()
        label = '<img src=x onerror="alert(1)">'
        report['question'] = '<script>alert("question")</script>'
        report['configuration']['fields']['numeric'][0] = label
        report['configuration']['relationships']['numeric_pairs'][0][0] = label
        report['numeric_relationships'][0]['left'] = label
        report['categorical_distributions']['segment']['categories'][0]['value'] = label
        before = deepcopy(report)
        window = render_html(report)
        page = ReportHTML(window)
        self.assertEqual(report, before)
        self.assertNotIn('script', page.tags)
        self.assertNotIn('img', page.tags)
        self.assertIn('&lt;script&gt;', window)
        self.assertIn('&lt;img', window)
        self.assertEqual(self.numeric_table(page)['rows'][1][0]['text'], label)
        self.assertIn(label, self.matrix_cell(self.maps(page)[0], label, 'measure_b')
                      ['attrs']['aria-label'])
        self.assertIn('Content-Security-Policy', window)

    def test_new_destination_receives_saved_json_and_html_only(self):
        report = saved_report()
        before = deepcopy(report)
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'saved-report'
            window = write_report(report, output)
            self.assertEqual(window, output / 'report.html')
            self.assertEqual({path.name for path in output.iterdir()}, {'report.json', 'report.html'})
            self.assertEqual(json.loads((output / 'report.json').read_text(encoding='utf-8')), before)
            self.assertEqual(window.read_text(encoding='utf-8'), render_html(before))
            self.assertEqual(report, before)

    def test_existing_destination_is_refused_and_prior_files_are_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder) / 'saved-report'
            write_report(saved_report(), output)
            before = {path.name: path.read_bytes() for path in output.iterdir()}
            changed = saved_report()
            changed['question'] = 'Replacement must be refused'
            with self.assertRaises(FileExistsError):
                write_report(changed, output)
            self.assertEqual({path.name: path.read_bytes() for path in output.iterdir()}, before)

    def test_write_failure_cleans_new_files_and_preserves_unrelated_evidence(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            retained = root / 'previous-evidence.txt'
            retained.write_text('retain this saved evidence', encoding='utf-8')
            output = root / 'new-report'
            real_open = Path.open

            def fail_html(path, *args, **kwargs):
                if path.name == 'report.html':
                    raise OSError('simulated HTML output failure')
                return real_open(path, *args, **kwargs)

            with patch.object(Path, 'open', fail_html):
                with self.assertRaisesRegex(OSError, 'simulated HTML output failure'):
                    write_report(saved_report(), output)
            self.assertFalse(output.exists())
            self.assertEqual(retained.read_text(encoding='utf-8'), 'retain this saved evidence')


if __name__ == '__main__':
    unittest.main()

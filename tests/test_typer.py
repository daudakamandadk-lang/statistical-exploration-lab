"""Build step 2 tests: semantic typer. Artificial data only, neutral names."""

import unittest

from statistical_exploration_lab import (
    profile_structure,
    type_columns,
    TyperPolicy,
)


def profile_and_type(table, declared=None, overrides=None, policy=None):
    step1 = profile_structure(table, declared=declared, overrides=overrides)
    typed = type_columns(step1, table, policy=policy)
    return step1, typed.by_name(), typed.findings


class TestWorkedExample(unittest.TestCase):
    def test_approved_example_types(self):
        table = {
            'record_id': [1, 2, 3, 3, 5],
            'measure_a': [0.1, 0.4, 0.9, 0.9, 1.2],
            'measure_c': [7, 8, 9, 9, 11],
            'code_b': ['A', 'B', 'A', 'A', 'B'],
            'stamp': ['2024-01-01', '2024-01-02', '2024-01-03',
                      '2024-01-03', '2024-01-05'],
            # Rows 3 and 4 are exact duplicates, so record_id is dedup-unique.
            'amount': [100.0, 250.0, -999.0, -999.0, 60.0],
        }
        _, by_name, findings = profile_and_type(
            table, policy=TyperPolicy(apply_inferred_sentinels=True))
        # Both dedup-unique int columns type identically (name-blind typer).
        self.assertEqual(by_name['record_id'].semantic_type, 'id_candidate')
        self.assertEqual(by_name['measure_c'].semantic_type, 'id_candidate')
        self.assertEqual(by_name['measure_a'].semantic_type, 'continuous')
        self.assertEqual(by_name['code_b'].semantic_type, 'binary')
        self.assertEqual(by_name['stamp'].semantic_type, 'date')
        self.assertIn(-999, by_name['amount'].sentinels)
        self.assertEqual(by_name['amount'].semantic_type, 'continuous')
        self.assertEqual(
            by_name['amount'].sentinel_provenance['-999'], 'inferred')
        codes = [f.code for f in findings if f.column == 'amount']
        self.assertIn('sentinel_candidate', codes)

    def test_rule8_confirm_finding(self):
        table = {'code': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]}
        _, by_name, findings = profile_and_type(table)
        self.assertEqual(by_name['code'].semantic_type,
                         'ordinal_nominal_candidate')
        self.assertIn('confirm_type',
                      [f.code for f in findings if f.column == 'code'])


class TestDecisionTable(unittest.TestCase):
    def test_constant_and_empty(self):
        _, by_name, findings = profile_and_type(
            {'flat': [7, 7, 7], 'gone': [None, None, None]})
        self.assertEqual(by_name['flat'].semantic_type, 'constant')
        self.assertEqual(by_name['gone'].semantic_type, 'empty')
        self.assertIn('constant_column', [f.code for f in findings])
        self.assertIn('empty_column', [f.code for f in findings])

    def test_mixed_refusal(self):
        _, by_name, findings = profile_and_type(
            {'mix': [1, 'two', 3.0, 'four']})
        self.assertEqual(by_name['mix'].semantic_type, 'mixed')
        self.assertIn('mixed_type', [f.code for f in findings])

    def test_binary_int_and_bool(self):
        _, by_name, _ = profile_and_type(
            {'flag': [0, 1, 0, 1], 'ok': [True, False, True, False]})
        self.assertEqual(by_name['flag'].semantic_type, 'binary')
        self.assertEqual(by_name['ok'].semantic_type, 'binary')

    def test_count_detection(self):
        # 25 distinct levels (> 20), non-negative, right-skewed heap at 0.
        counts = ([0] * 40 + [1] * 12 + [2] * 8 + [3] * 5 + [4] * 3
                  + [5, 6, 7, 8, 9, 10, 12, 14, 16, 18, 20, 25, 30,
                     35, 40, 50, 60, 80, 100, 140, 200])
        _, by_name, _ = profile_and_type({'events': counts})
        self.assertEqual(by_name['events'].semantic_type, 'count')

    def test_nominal_and_free_text(self):
        _, by_name, _ = profile_and_type({
            'group': ['a', 'b', 'c', 'a', 'b', 'c', 'a', 'b', 'a',
                      'c', 'b', 'a'],
            'note': ['this is a fairly long free text note about topic %02d' % i
                     for i in range(12)],
        })
        self.assertEqual(by_name['group'].semantic_type, 'nominal')
        self.assertEqual(by_name['note'].semantic_type, 'free_text')

    def test_date_parse_failure_falls_back(self):
        # Repeats keep the uniqueness ratio low, so this is nominal, not id.
        _, by_name, _ = profile_and_type(
            {'when': ['not-a-date', 'either', 'nope', 'nah', 'nope',
                      'either', 'nah', 'not-a-date', 'no', 'nope']})
        self.assertEqual(by_name['when'].semantic_type, 'nominal')

class TestPrecedenceAndRationale(unittest.TestCase):
    def test_override_semantic_kept(self):
        table = {'code': [1, 2, 3, 1, 2, 3]}
        _, by_name, _ = profile_and_type(
            table, overrides={'code': {'semantic_type': 'nominal'}})
        self.assertEqual(by_name['code'].semantic_type, 'nominal')
        self.assertEqual(by_name['code'].semantic_source, 'override')

    def test_declared_semantic_kept(self):
        table = {'code': [1, 2, 3, 1, 2, 3]}
        _, by_name, _ = profile_and_type(
            table, declared={'code': {'semantic_type': 'ordinal'}})
        self.assertEqual(by_name['code'].semantic_type, 'ordinal')
        self.assertEqual(by_name['code'].semantic_source, 'declared')

    def test_override_sentinel_beats_guess(self):
        table = {'amount': [100, -999, 250, 80, 60]}
        _, by_name, _ = profile_and_type(
            table, overrides={'amount': {'sentinels': [-999]}})
        self.assertEqual(
            by_name['amount'].sentinel_provenance['-999'], 'override')

    def test_rationale_recorded(self):
        _, by_name, _ = profile_and_type({'measure_a': [0.1, 0.4, 0.9]})
        self.assertTrue(by_name['measure_a'].rationale)

    def test_string_sentinel_guess(self):
        _, by_name, findings = profile_and_type(
            {'label': ['red', 'UNK', 'blue', 'red']})
        self.assertIn('UNK', by_name['label'].sentinel_candidates)
        self.assertEqual(by_name['label'].sentinels, ())
        self.assertIn('sentinel_candidate',
                      [f.code for f in findings if f.column == 'label'])

    def test_step1_facts_untouched(self):
        table = {'amount': [100, -999, 250, 80, 60]}
        step1, _, _ = profile_and_type(table)
        self.assertEqual(step1.facts['amount']['distinct_count'], 5)

    def test_arbitrary_names_behave_identically(self):
        table_a = {'record_id': [1, 2, 3, 3, 5],
                   'measure_a': [0.1, 0.4, 0.9, 0.9, 1.2]}
        table_b = {'zz_alpha': [1, 2, 3, 3, 5],
                   'q7': [0.1, 0.4, 0.9, 0.9, 1.2]}
        _, a, _ = profile_and_type(table_a)
        _, b, _ = profile_and_type(table_b)
        self.assertEqual(a['record_id'].semantic_type,
                         b['zz_alpha'].semantic_type)
        self.assertEqual(a['measure_a'].semantic_type, b['q7'].semantic_type)

    def test_small_int_sample_not_count(self):
        _, by_name, _ = profile_and_type({'tiny': [0, 1, 5]})
        self.assertNotEqual(by_name['tiny'].semantic_type, 'count')

    def test_many_level_int_without_skew_is_continuous(self):
        # 30 distinct levels (> 20) but symmetric, skew ~0. Values repeat
        # across the two halves so the column is not dedup-unique.
        _, by_name, _ = profile_and_type(
            {'score': list(range(100, 130)) * 2,
             'half': ['a'] * 30 + ['b'] * 30})
        self.assertEqual(by_name['score'].semantic_type, 'continuous')


if __name__ == '__main__':
    unittest.main()

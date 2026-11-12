"""Regressions for making explicit choices and composing the two current steps."""

import json
import unittest

import numpy as np
import pandas as pd

from statistical_exploration_lab import (
    GatePolicy, TyperPolicy, data_fingerprint, profile_structure, type_columns,
)


class ObservationChoiceTests(unittest.TestCase):
    def test_repeated_measurement_is_not_an_asserted_key(self):
        table = {'record_id': [101, 102, 103, 104, 105],
                 'measurement': [10, 20, 30, 40, 40]}
        for key in (None, 'record_id'):
            with self.subTest(key=key):
                profile = profile_structure(
                    table, observation_key=key,
                    overrides={'measurement': {'semantic_type': 'continuous'}})
                self.assertEqual(profile.gate.status, 'proceed')
                self.assertEqual(type_columns(profile, table).by_name()[
                    'measurement'].semantic_type, 'continuous')

    def test_composite_key_and_exact_duplicate_warning(self):
        table = {'subject': ['A', 'A', 'B', 'B'],
                 'visit': [1, 2, 1, 1], 'value': [2., 3., 4., 4.]}
        profile = profile_structure(table, observation_key=['subject', 'visit'])
        self.assertEqual(profile.observation_key, ('subject', 'visit'))
        self.assertIsNone(profile.grain)  # No invented concatenated column name.
        self.assertEqual(profile.exact_duplicate_rows, 1)
        self.assertEqual(profile.gate.status, 'warn')
        self.assertEqual(len(type_columns(profile, table).columns), 3)
        table['value'][-1] = 5.
        conflicting = profile_structure(table, observation_key=('subject', 'visit'))
        self.assertEqual(conflicting.gate.status, 'stop')
        self.assertIn('conflicting_duplicate_key', {f.code for f in conflicting.findings})

    def test_selected_key_requires_present_nonblank_unique_names(self):
        for key in ('absent', [], ['id', 'id'], [''], 123):
            with self.subTest(key=key), self.assertRaises(ValueError):
                profile_structure({'id': [1, 2]}, observation_key=key)
        for values, code in ((['A', ' '], 'blank_observation_key'),
                             (['A', None], 'missing_observation_key')):
            with self.subTest(values=values):
                profile = profile_structure({'id': values}, observation_key='id')
                self.assertEqual(profile.gate.status, 'stop')
                self.assertIn(code, {f.code for f in profile.findings})

    def test_stopped_gate_is_not_lost_during_composition(self):
        table = {'id': [1, 1], 'value': [3., 4.]}
        stopped = profile_structure(table, observation_key='id')
        with self.assertRaisesRegex(ValueError, 'gate stopped'):
            type_columns(stopped, table)
        acknowledged = profile_structure(
            table, observation_key='id', policy=GatePolicy(stop_on_conflicting_keys=False))
        self.assertEqual(acknowledged.gate.status, 'warn')
        self.assertTrue(type_columns(acknowledged, table).columns)


class SentinelChoiceTests(unittest.TestCase):
    def test_candidates_do_not_change_the_default_investigation(self):
        table = {'amount': [-1., 10., 20.]}
        profile = profile_structure(table)
        column = type_columns(profile, table).by_name()['amount']
        self.assertEqual(column.semantic_type, 'continuous')
        self.assertEqual(column.sentinels, ())
        self.assertEqual(column.sentinel_candidates, (-1,))
        self.assertEqual(profile.facts['amount']['null_count'], 0)
        opted_in = type_columns(
            profile, table, policy=TyperPolicy(apply_inferred_sentinels=True)).by_name()['amount']
        self.assertEqual(opted_in.sentinels, (-1,))
        self.assertEqual(opted_in.semantic_type, 'binary')

    def test_explicit_empty_lists_suppress_guesses_in_both_sources(self):
        table = {'amount': [-1., 10., 20.]}
        for source in ('declared', 'overrides'):
            with self.subTest(source=source):
                profile = profile_structure(table, **{source: {'amount': {'sentinels': []}}})
                self.assertEqual(profile.columns[0].provenance['sentinels'],
                                 'declared' if source == 'declared' else 'override')
                column = type_columns(profile, table, policy=TyperPolicy(
                    apply_inferred_sentinels=True)).columns[0]
                self.assertEqual(column.sentinels, ())
                self.assertEqual(column.sentinel_candidates, ())
                self.assertEqual(column.semantic_type, 'continuous')

    def test_override_replaces_declared_list_without_adding_guesses(self):
        table = {'amount': [-1., 10., 20.]}
        profile = profile_structure(
            table, declared={'amount': {'sentinels': [-1]}},
            overrides={'amount': {'sentinels': [10]}})
        column = type_columns(profile, table, policy=TyperPolicy(
            apply_inferred_sentinels=True)).columns[0]
        self.assertEqual(column.sentinels, (10,))
        self.assertEqual(column.sentinel_candidates, ())
        self.assertEqual(profile.facts['amount']['null_count'], 1)
        self.assertEqual(column.sentinel_provenance['10'], 'override')

    def test_confirmed_string_sentinel_has_one_rule_across_steps(self):
        table = pd.DataFrame({'label': [' na ', 'red', 'blue']})
        before = table.copy(deep=True)
        profile = profile_structure(table, overrides={'label': {'sentinels': ['NA']}})
        column = type_columns(profile, table).columns[0]
        self.assertEqual(profile.facts['label']['null_count'], 1)
        self.assertEqual(column.semantic_type, 'binary')
        self.assertEqual(column.sentinels, ('NA',))
        pd.testing.assert_frame_equal(table, before)


class InputBoundaryTests(unittest.TestCase):
    def test_bad_override_shapes_fail_before_interpretation(self):
        invalid = [
            {'x': 'continuous'}, {'x': {'semantic_type': 'continuouss'}},
            {'x': {'semantic_type': None}}, {'x': {'sentinels': 'NA'}},
            {'x': {'sentinels': [[-1]]}}, {'x': {'sentinells': [-1]}},
        ]
        for override in invalid:
            with self.subTest(override=override), self.assertRaises((TypeError, ValueError)):
                profile_structure({'x': [1, 2, 3]}, overrides=override)

    def test_declared_known_values_are_validated_without_importing_metadata(self):
        for spec in ({'sentinels': 'NA'}, {'semantic_type': 'continuouss'}):
            with self.subTest(spec=spec), self.assertRaises((TypeError, ValueError)):
                profile_structure({'x': [1, 2]}, declared={'x': spec})
        result = profile_structure({'x': [1, 2]}, declared={
            'x': {'semantic_type': 'identifier', 'engineering_metadata': 'not imported'}})
        self.assertEqual(result.columns[0].semantic_type, 'identifier')

    def test_nonstring_or_blank_labels_are_not_silently_renamed(self):
        for table in (pd.DataFrame({0: [1, 2]}),
                      pd.DataFrame({1: [1, 2], '1': [3, 4]}),
                      pd.DataFrame({' ': [1, 2]})):
            with self.subTest(labels=list(table.columns)), self.assertRaisesRegex(
                    ValueError, 'Column names'):
                profile_structure(table)

    def test_snapshot_handoff_rejects_selection_values_index_and_dtype_changes(self):
        table = pd.DataFrame({'x': [1., 2., 3.], 'y': [4., 5., 6.]})
        profile = profile_structure(table)
        changed = table.copy()
        changed.loc[1, 'x'] = 2.5
        variants = [table[['x']], table[['y', 'x']], changed,
                    table.assign(x=['red', 'green', 'blue']),
                    table.astype({'x': 'int64'}), table.set_axis([10, 11, 12])]
        for different in variants:
            with self.subTest(different=different), self.assertRaisesRegex(
                    ValueError, 'reprofile'):
                type_columns(profile, different)
        self.assertEqual(len(type_columns(profile, table.copy(deep=True)).columns), 2)

    def test_profile_evidence_is_read_only_and_inspection_is_detached(self):
        table = {'x': [1., 2., 3.]}
        profile = profile_structure(table, overrides={'x': {'semantic_type': 'continuous'}})
        with self.assertRaises(TypeError):
            profile.facts['x']['storage_type'] = 'str'
        with self.assertRaises(TypeError):
            profile.columns[0].provenance['semantic_type'] = 'inferred'
        typed = type_columns(profile, table)
        with self.assertRaises(TypeError):
            typed.columns[0].sentinel_provenance['-1'] = 'override'
        display = profile.to_dict()
        display['facts']['x']['storage_type'] = 'str'
        self.assertEqual(profile.facts['x']['storage_type'], 'float')
        json.dumps(profile.to_dict(), allow_nan=False)
        json.dumps(typed.to_dict(), allow_nan=False)


class SnapshotIdentityTests(unittest.TestCase):
    def test_relationship_changes_do_not_hide_behind_a_structural_fingerprint(self):
        first = pd.DataFrame({'x': [1., 2., 3., 4.], 'y': [1., 2., 3., 4.]})
        second = first.assign(y=[1., 3., 2., 4.])
        left, right = profile_structure(first), profile_structure(second)
        self.assertEqual(left.fingerprint, right.fingerprint)
        self.assertNotEqual(left.data_fingerprint, right.data_fingerprint)
        with self.assertRaisesRegex(ValueError, 'reprofile'):
            type_columns(left, second)

    def test_type_tags_and_adjacent_floats_preserve_input_identity(self):
        numeric = pd.DataFrame({'x': pd.Series([1], dtype=object)})
        text = pd.DataFrame({'x': pd.Series(['1'], dtype=object)})
        boolean = pd.DataFrame({'x': pd.Series([True], dtype=object)})
        self.assertEqual(len({data_fingerprint(frame) for frame in
                              (numeric, text, boolean)}), 3)
        first = pd.DataFrame({'x': [1., 2., 3.]})
        adjacent = first.copy()
        adjacent.loc[1, 'x'] = np.nextafter(2., 3.)
        self.assertNotEqual(data_fingerprint(first), data_fingerprint(adjacent))

    def test_categorical_metadata_and_dict_dataframe_equivalence(self):
        first = pd.DataFrame({'label': pd.Categorical(['A', 'B'], categories=['A', 'B'])})
        second = first.assign(label=first['label'].cat.add_categories(['C']))
        self.assertNotEqual(data_fingerprint(first), data_fingerprint(second))
        table = {'x': [1., 2., 3.]}
        self.assertEqual(profile_structure(table).data_fingerprint,
                         profile_structure(pd.DataFrame(table)).data_fingerprint)

    def test_integer_extrema_are_observed_without_float_rounding(self):
        large = 2 ** 60 + 1
        profile = profile_structure({'counter': [large, large + 2]})
        self.assertEqual(profile.facts['counter']['min'], large)
        self.assertEqual(profile.facts['counter']['max'], large + 2)
        self.assertIsInstance(profile.facts['counter']['min'], int)


if __name__ == '__main__':
    unittest.main()

"""Step 1 checks: contract, adapter, profiler and gate — artificial data only."""

import unittest

import pandas as pd

from statistical_exploration_lab.contract import (
    GatePolicy,
    adapt_declared_schema,
    profile_structure,
)


def worked_example():
    """The approved domain-neutral example: row 4 duplicates row 3 exactly."""
    return {
        'record_id': [1, 2, 3, 3, 5],
        'measure_a': [0.1, 0.4, 0.9, 0.9, 1.2],
        'measure_b': [2.0, 2.1, 2.5, 2.5, 2.9],
        'measure_c': [7, 8, 9, 9, 11],
    }


class GateTests(unittest.TestCase):

    def test_worked_example_proceeds_with_warnings(self):
        result = profile_structure(worked_example())
        self.assertEqual(result.gate.status, 'warn')
        codes = {f.code for f in result.gate.reasons}
        self.assertIn('exact_duplicate_rows', codes)
        self.assertNotIn('conflicting_duplicate_key', codes)
        self.assertEqual(result.grain, 'record_id')
        self.assertEqual(result.exact_duplicate_rows, 1)

    def test_conflicting_duplicate_key_stops(self):
        table = worked_example()
        # record_id 3 appears in rows 2 and 3; make those rows disagree
        table['measure_a'] = [0.1, 0.4, 0.9, 5.5, 1.2]
        result = profile_structure(table, observation_key='record_id')
        self.assertEqual(result.gate.status, 'stop')
        stop_codes = {f.code for f in result.findings if f.severity == 'stop'}
        self.assertIn('conflicting_duplicate_key', stop_codes)

    def test_empty_table_stops(self):
        result = profile_structure({})
        self.assertEqual(result.gate.status, 'stop')
        self.assertIn('empty_table', {f.code for f in result.findings})

    def test_duplicate_column_names_stop(self):
        df = pd.DataFrame([[1, 2], [3, 4]], columns=['x', 'x'])
        result = profile_structure(df)
        self.assertEqual(result.gate.status, 'stop')
        self.assertIn('duplicate_columns', {f.code for f in result.findings})

    def test_clean_table_proceeds(self):
        result = profile_structure({
            'record_id': [1, 2, 3],
            'measure_a': [0.1, 0.4, 0.9],
        })
        self.assertEqual(result.gate.status, 'proceed')
        self.assertEqual(result.gate.reasons, ())


class ReusabilityTests(unittest.TestCase):
    """The lab's core intent: any table, any names, identical behaviour."""

    def test_arbitrary_column_names_behave_identically(self):
        base = profile_structure(worked_example())
        renamed = profile_structure({
            'zz_alpha': worked_example()['record_id'],
            'q7': worked_example()['measure_a'],
            'whatever_name': worked_example()['measure_b'],
            'last': worked_example()['measure_c'],
        })
        self.assertEqual(base.gate.status, renamed.gate.status)
        self.assertEqual(renamed.grain, 'zz_alpha')
        self.assertEqual(base.exact_duplicate_rows, renamed.exact_duplicate_rows)
        self.assertEqual(
            {f.code for f in base.findings}, {f.code for f in renamed.findings})

    def test_dict_of_lists_and_dataframe_agree(self):
        as_dict = profile_structure(worked_example())
        as_frame = profile_structure(pd.DataFrame(worked_example()))
        self.assertEqual(as_dict.facts, as_frame.facts)
        self.assertEqual(as_dict.fingerprint, as_frame.fingerprint)

    def test_fingerprint_changes_when_data_changes(self):
        before = profile_structure(worked_example())
        changed = worked_example()
        changed['measure_a'][0] = 0.2
        after = profile_structure(changed)
        self.assertNotEqual(before.fingerprint, after.fingerprint)

    def test_fingerprint_stable_across_calls(self):
        first = profile_structure(worked_example())
        second = profile_structure(worked_example())
        self.assertEqual(first.fingerprint, second.fingerprint)


class ContractAndPrecedenceTests(unittest.TestCase):

    def test_semantic_guesses(self):
        result = profile_structure(worked_example())
        semantics = {c.name: c.semantic_type for c in result.columns}
        self.assertEqual(semantics['record_id'], 'id_candidate')
        self.assertEqual(semantics['measure_a'], 'continuous')
        # int + unique after dedup reads as id_candidate at Step 1; an
        # override (or Step 2 typing) refines it to count/ordinal if needed
        self.assertEqual(semantics['measure_c'], 'id_candidate')

    def test_override_beats_declared(self):
        result = profile_structure(
            worked_example(),
            declared={'measure_a': {'semantic_type': 'ordinal'}},
            overrides={'measure_a': {'semantic_type': 'nominal'}},
        )
        contract = {c.name: c for c in result.columns}['measure_a']
        self.assertEqual(contract.semantic_type, 'nominal')
        self.assertEqual(contract.provenance['semantic_type'], 'override')

    def test_declared_beats_inferred(self):
        result = profile_structure(
            worked_example(),
            declared={'measure_c': {'semantic_type': 'count'}},
        )
        contract = {c.name: c for c in result.columns}['measure_c']
        self.assertEqual(contract.semantic_type, 'count')
        self.assertEqual(contract.provenance['semantic_type'], 'declared')

    def test_declared_storage_mismatch_is_finding_not_fix(self):
        result = profile_structure(
            worked_example(),
            declared={'measure_a': {'storage_type': 'str'}},
        )
        contract = {c.name: c for c in result.columns}['measure_a']
        self.assertEqual(contract.storage_type, 'float')  # fact stands
        self.assertIn('declared_storage_mismatch',
                      {f.code for f in result.findings})

    def test_sentinel_masking_counts_sentinel_as_missing(self):
        table = worked_example()
        table['measure_b'] = [-999.0, 2.1, 2.5, 2.5, 2.9]
        result = profile_structure(
            table, overrides={'measure_b': {'sentinels': [-999]}})
        self.assertEqual(result.facts['measure_b']['null_count'], 1)
        contract = {c.name: c for c in result.columns}['measure_b']
        self.assertEqual(contract.provenance['sentinels'], 'override')

    def test_unknown_columns_warn_not_crash(self):
        result = profile_structure(
            worked_example(),
            declared={'not_a_column': {'storage_type': 'int'}},
            overrides={'also_missing': {'semantic_type': 'nominal'}},
        )
        codes = {f.code for f in result.findings}
        self.assertIn('declared_unknown_column', codes)
        self.assertIn('override_unknown_column', codes)
        self.assertNotEqual(result.gate.status, 'stop')


class AdapterTests(unittest.TestCase):

    def test_adapter_normalises_entries(self):
        adapted = adapt_declared_schema(
            {'x': {'storage_type': 'int', 'sentinels': [-1, -9]}})
        self.assertEqual(adapted['x']['storage_type'], 'int')
        self.assertEqual(adapted['x']['sentinels'], (-1, -9))

    def test_adapter_rejects_bad_storage_type(self):
        with self.assertRaises(ValueError):
            adapt_declared_schema({'x': {'storage_type': 'banana'}})

    def test_adapter_rejects_non_mapping_entry(self):
        with self.assertRaises(TypeError):
            adapt_declared_schema({'x': 'not a mapping'})


class PolicyTests(unittest.TestCase):

    def test_policy_can_relax_no_key_warning(self):
        table = {'a': [1.5, 2.5, 3.5], 'b': [4.5, 5.5, 6.5]}  # no key-like col
        strict = profile_structure(table)
        relaxed = profile_structure(table, policy=GatePolicy(warn_on_no_key=False))
        self.assertIn('no_candidate_key', {f.code for f in strict.findings})
        self.assertNotIn('no_candidate_key',
                         {f.code for f in relaxed.findings})
        self.assertEqual(relaxed.gate.status, 'proceed')

    def test_all_null_column_warns(self):
        result = profile_structure({'x': [None, None, None], 'y': [1, 2, 3]})
        self.assertIn('empty_column', {f.code for f in result.findings})
        self.assertEqual(result.facts['x']['storage_type'], 'empty')

    def test_mixed_type_column_detected(self):
        result = profile_structure({'x': [1, 'two', 3], 'y': [1.0, 2.0, 3.0]})
        self.assertEqual(result.facts['x']['storage_type'], 'mixed')


if __name__ == '__main__':
    unittest.main()

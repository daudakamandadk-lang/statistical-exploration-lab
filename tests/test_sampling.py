"""Artificial fixtures for explicit selection, evidence and component handoff."""
import importlib.util
import unittest

import numpy as np
import pandas as pd

from statistical_exploration_lab import data_fingerprint, select_complete_cases


class SampleTests(unittest.TestCase):
    def test_selected_fields_only_and_source_positions_with_duplicate_labels(self):
        data = pd.DataFrame({'x': [1., np.nan, 3., 4.],
                             'y': [2., 3., np.nan, 8.],
                             'note': [None, 'b', 'c', None]}, index=['a', 'a', 'z', 'q'])
        before = data.copy(deep=True)
        sample = select_complete_cases(data, columns=['y', 'x'])
        self.assertEqual(sample.used_positions, (0, 3))
        self.assertEqual(sample.excluded_positions, (1, 2))
        self.assertEqual(dict(sample.missing_by_position), {1: ('x',), 2: ('y',)})
        self.assertEqual(sample.table.index.tolist(), ['a', 'q'])
        pd.testing.assert_frame_equal(data, before)
        pd.testing.assert_frame_equal(sample.table, data.iloc[[0, 3]])
        self.assertEqual(sample.input_fingerprint, data_fingerprint(data))
        self.assertEqual(sample.selected_fingerprint, data_fingerprint(sample.table))
        with self.assertRaises(TypeError):
            sample.missing_by_position[1] = ()
        sample.table.iloc[0, 0] = 99
        self.assertEqual(data.iloc[0, 0], 1.)
        self.assertNotEqual(sample.selected_fingerprint, data_fingerprint(sample.table))

    def test_nullable_fields_and_explicit_sentinel_boundary(self):
        data = pd.DataFrame({'value': pd.Series([1, None, -999, 4], dtype='Int64'),
                             'label': ['', 'a', 'b', None]})
        sample = select_complete_cases(data, columns=['value'])
        self.assertEqual(sample.used_positions, (0, 2, 3))
        self.assertEqual(str(sample.table['value'].dtype), 'Int64')
        self.assertEqual(select_complete_cases(data, columns=['label']).used_positions, (0, 1, 2))
        inf = select_complete_cases(pd.DataFrame({'x': [np.inf, 2]}), columns=['x'])
        self.assertEqual(inf.used_rows, 2)  # Preparation does not certify numeric suitability.

    def test_invalid_selection_and_empty_sample_fail_clearly(self):
        data = pd.DataFrame({'x': [1, 2]})
        for columns in ([], 'x', ['x', 'x'], ['absent'], [1], ['']):
            with self.subTest(columns=columns), self.assertRaises(ValueError):
                select_complete_cases(data, columns=columns)
        for bad in (pd.DataFrame({'x': []}), pd.DataFrame({'x': [None]})):
            with self.assertRaisesRegex(ValueError, 'No complete'):
                select_complete_cases(bad, columns=['x'])
        with self.assertRaises(TypeError):
            select_complete_cases({'x': [1]}, columns=['x'])
        with self.assertRaises(ValueError):
            select_complete_cases(pd.DataFrame([[1, 2]], columns=['x', 'x']), columns=['x'])

    @unittest.skipUnless(importlib.util.find_spec('statsmodels'), 'install econometrics extra')
    def test_two_chosen_specifications_share_rows_and_map_to_source(self):
        from statistical_exploration_lab import fit_ols
        data = pd.DataFrame({'x': [-2., -1., 0., 1., 2., 3.],
                             'z': [1., np.nan, 0., 2., -1., 1.],
                             'y': [-3., -3., 4., 3., 9., 10.]})
        sample = select_complete_cases(data, columns=['y', 'x', 'z'])
        fits = [fit_ols(sample.table, outcome='y', predictors=p, missing='raise',
                        cov_type='HC3') for p in (['x'], ['x', 'z'])]
        self.assertEqual(fits[0].used_positions, fits[1].used_positions)
        self.assertEqual(fits[0].input_fingerprint, sample.selected_fingerprint)
        self.assertEqual(tuple(sample.used_positions[i] for i in fits[1].used_positions),
                         (0, 2, 3, 4, 5))


if __name__ == '__main__':
    unittest.main()

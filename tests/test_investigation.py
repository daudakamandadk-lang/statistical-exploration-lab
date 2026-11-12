"""Known answers and workflow boundaries; statistics are delegated to libraries."""
import importlib.util
import unittest

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from statistical_exploration_lab import fit_ols, plot_ols_diagnostics, summarize_numeric


def observations():
    return pd.DataFrame({'x': [-2., -1., 0., 1., 2.],
                         'y': [-3., -3., 4., 3., 9.],
                         'unselected': ['a', 'b', None, 'd', 'e']})


class SummaryTests(unittest.TestCase):
    def test_selected_summary_uses_available_counts_without_changing_input(self):
        data = observations()
        data.loc[2, 'x'] = np.nan
        before = data.copy(deep=True)
        result = summarize_numeric(data, ['x', 'y'])
        self.assertEqual(result.loc['x', 'total'], 5)
        self.assertEqual(result.loc['x', 'missing'], 1)
        self.assertEqual(result.loc['x', 'count'], 4)
        self.assertEqual(result.loc['y', 'count'], 5)
        pd.testing.assert_frame_equal(data, before)

    def test_invalid_selections_and_unprepared_values_fail(self):
        for columns in ('x', [], ['x', 'x'], ['absent']):
            with self.subTest(columns=columns), self.assertRaises(ValueError):
                summarize_numeric(observations(), columns)
        for data in (pd.DataFrame({'x': ['1', '2']}), pd.DataFrame({'x': [True, False]})):
            with self.assertRaises(TypeError):
                summarize_numeric(data, ['x'])
        with self.assertRaisesRegex(ValueError, 'infinity'):
            summarize_numeric(pd.DataFrame({'x': [1., np.inf]}), ['x'])


@unittest.skipUnless(importlib.util.find_spec('statsmodels'), 'install the econometrics extra')
class OLSWorkflowTests(unittest.TestCase):
    def fit(self, data=None, **changes):
        options = dict(outcome='y', predictors=['x'], missing='raise',
                       cov_type='HC3', intercept=True, use_t=True)
        options.update(changes)
        return fit_ols(observations() if data is None else data, **options)

    def test_known_coefficients_and_underlying_library_access(self):
        result = self.fit()
        np.testing.assert_allclose(result.fitted.params, [2., 3.], atol=1e-12)
        self.assertEqual(result.fitted.cov_type, 'HC3')
        self.assertTrue(result.fitted.use_t)
        self.assertEqual(result.choices['predictors'], ('x',))
        coefficients = result.coefficients(alpha=0.1)
        np.testing.assert_allclose(coefficients['interval_low'], result.fitted.conf_int(alpha=0.1)[0])
        self.assertEqual(result.used_rows, 5)
        with self.assertRaises(TypeError):
            result.choices['cov_type'] = 'nonrobust'

    def test_missing_policy_is_explicit_and_uses_selected_fields_only(self):
        data = observations()
        self.assertEqual(self.fit(data).used_rows, 5)  # unrelated missing label is ignored
        data.loc[1, 'x'] = np.nan
        before = data.copy(deep=True)
        with self.assertRaisesRegex(ValueError, 'missing'):
            self.fit(data)
        result = self.fit(data, missing='drop')
        self.assertEqual(result.excluded_positions, (1,))
        self.assertEqual(result.used_positions, (0, 2, 3, 4))
        pd.testing.assert_frame_equal(data, before)

    def test_collinear_and_too_small_designs_are_not_silently_fitted(self):
        data = observations().assign(z=lambda d: 2*d['x'])
        with self.assertRaisesRegex(ValueError, 'rank deficient'):
            self.fit(data, predictors=['x', 'z'])
        with self.assertRaisesRegex(ValueError, 'More usable rows'):
            self.fit(observations().iloc[:2])

    def test_invalid_choices_do_not_select_another_method(self):
        for changes in ({'cov_type': 'magic'}, {'missing': 'impute'},
                        {'predictors': ['x', 'y']}, {'use_t': 'yes'}):
            with self.subTest(changes=changes), self.assertRaises((TypeError, ValueError)):
                self.fit(**changes)
        with self.assertRaises(ValueError):
            self.fit().coefficients(alpha=1)

    def test_no_intercept_choice_and_fingerprint_are_recorded(self):
        data = observations()
        first = self.fit(data, intercept=False, cov_type='nonrobust', use_t=False)
        self.assertEqual(list(first.fitted.params.index), ['x'])
        self.assertFalse(first.choices['intercept'])
        data.loc[0, 'y'] += 0.5
        self.assertNotEqual(first.input_fingerprint, self.fit(data).input_fingerprint)

    def test_plotting_returns_a_view_without_refitting(self):
        result = self.fit()
        before = result.fitted.params.copy()
        figure = plot_ols_diagnostics(result)
        self.assertEqual(len(figure.axes), 2)
        pd.testing.assert_series_equal(result.fitted.params, before)
        plt.close(figure)


if __name__ == '__main__':
    unittest.main()

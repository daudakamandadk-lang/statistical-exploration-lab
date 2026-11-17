import unittest
import pandas as pd
import numpy as np
import importlib.util
from statistical_exploration_lab import prepare_missing_values, select_complete_cases, fit_ols

class ReviewFixTests(unittest.TestCase):
    def test_confirmed_rules_and_handoff(self):
        data = pd.DataFrame({'x':[1., -999, np.nan, 4.], 'label':['ok',' UNK ','ok','ok']})
        before = data.copy(deep=True)
        result = prepare_missing_values(data, rules={'x':[-999], 'label':['unk']})
        self.assertEqual(dict(result.changed_positions), {'x':(1,), 'label':(1,)})
        self.assertEqual(select_complete_cases(result.table, columns=['x']).used_positions, (0,3))
        pd.testing.assert_frame_equal(data,before)
        self.assertEqual(prepare_missing_values(data,rules={'x':[]}).table.loc[1,'x'],-999)
        with self.assertRaises(ValueError): prepare_missing_values(data,rules={'absent':[]})
        with self.assertRaises(TypeError): prepare_missing_values(data,rules={'x':'bad'})
        with self.assertRaises(TypeError): result.rules['x']=()

    @unittest.skipUnless(importlib.util.find_spec('statsmodels'), 'install econometrics extra')
    def test_supplied_constant_detected(self):
        import statsmodels.api as sm
        data=pd.DataFrame({'one':[1.]*5,'x':[-2.,-1.,0.,1.,2.],'y':[-3.,-3.,4.,3.,9.]})
        for predictors in (['one','x'], ['x']):
            result=fit_ols(data,outcome='y',predictors=predictors,missing='raise',cov_type='nonrobust',intercept=False)
            native=sm.OLS(data.y,data[predictors]).fit()
            self.assertAlmostEqual(result.fitted.rsquared,native.rsquared)
            self.assertEqual(result.choices['design_has_constant'],bool(native.model.k_constant))

    def test_container_error_identifies_column(self):
        with self.assertRaisesRegex(TypeError,"Column 'metadata', row position 0"):
            select_complete_cases(pd.DataFrame({'x':[1], 'metadata':[[1]]}),columns=['x'])

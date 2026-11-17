import unittest
import numpy as np
import pandas as pd
from statistical_exploration_lab import summarize_binary

class GroupedTests(unittest.TestCase):
    def test_weighted_known_answer_and_missing_group(self):
        d=pd.DataFrame({'y':[0.,1.,1.,np.nan], 'g':['a','a',None,None], 'w':[1.,3.,2.,1.]})
        before=d.copy(deep=True)
        r=summarize_binary(d,outcome='y',by='g',weight='w',missing='exclude').table
        self.assertAlmostEqual(r.iloc[0].proportion,.75)
        self.assertEqual(r.iloc[1].missing_outcome,1)
        self.assertEqual(r.used.sum(),3)
        pd.testing.assert_frame_equal(d,before)

    def test_zero_events_differs_from_no_denominator(self):
        d=pd.DataFrame({'y':[0.,np.nan], 'g':['zero','empty']})
        r=summarize_binary(d,outcome='y',by='g',missing='exclude').table
        self.assertEqual(r.iloc[0].proportion,0.)
        self.assertTrue(pd.isna(r.iloc[1].proportion))
        self.assertEqual(r.iloc[1].status,'not_estimable')

    def test_eligibility_is_positional_and_excludes_invalid_outcomes(self):
        d=pd.DataFrame({'y':[1,99,0],'g':['a','a','b']},index=[8,8,2])
        r=summarize_binary(d,outcome='y',by='g',missing='raise',eligible=[True,False,True])
        self.assertEqual(r.table.ineligible.sum(),1)
        self.assertEqual(r.choices['eligible_positions'],(0,2))
        with self.assertRaises(ValueError): summarize_binary(d,outcome='y',by=None,missing='raise')

    def test_invalid_weights_and_missing_policy_fail(self):
        for weight in (0.,-1.,np.nan,np.inf):
            with self.subTest(weight=weight), self.assertRaises(ValueError):
                summarize_binary(pd.DataFrame({'y':[1.],'w':[weight]}),outcome='y',by=None,weight='w',missing='raise')
        with self.assertRaises(ValueError):
            summarize_binary(pd.DataFrame({'y':[np.nan]}),outcome='y',by=None,missing='raise')
        with self.assertRaises(ValueError):
            summarize_binary(pd.DataFrame({'y':[1]}),outcome='y',by=None,missing='raise',eligible=[1])

    def test_empty_and_unused_categories(self):
        d=pd.DataFrame({'y':pd.Series([],dtype=float)})
        self.assertEqual(summarize_binary(d,outcome='y',by=None,missing='exclude').table.iloc[0].status,'not_estimable')
        d=pd.DataFrame({'y':[1], 'g':pd.Categorical(['a'],categories=['a','b'])})
        self.assertEqual(len(summarize_binary(d,outcome='y',by='g',missing='raise').table),1)

    def test_weight_rescaling_leaves_proportions_unchanged(self):
        d=pd.DataFrame({'y':[1,0,1],'w':[1.,3.,2.]})
        a=summarize_binary(d,outcome='y',by=None,weight='w',missing='raise').table
        d.w*=100
        b=summarize_binary(d,outcome='y',by=None,weight='w',missing='raise').table
        self.assertAlmostEqual(a.iloc[0].proportion,.5)
        self.assertAlmostEqual(a.iloc[0].proportion,b.iloc[0].proportion)

import unittest
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from statistical_exploration_lab import inspect_distributions, inspect_relationships, plot_distribution, plot_relationship

class ExplorationTests(unittest.TestCase):
    def test_known_fences_positions_and_unchanged_data(self):
        d=pd.DataFrame({'x':[1.,2.,3.,4.,100.,np.nan]},index=['a']*6);before=d.copy(deep=True)
        r=inspect_distributions(d,['x'],missing='exclude')
        self.assertEqual(r.table.iloc[0].q25,2)
        self.assertEqual(r.table.iloc[0].upper_fence,7)
        self.assertEqual(r.rows.position.tolist(),[4])
        pd.testing.assert_frame_equal(d,before)
    def test_unavailable_flags_are_not_clean_bills_of_health(self):
        for values,status in [([1.,1.,1.,1.,9.],'zero_iqr'),([1.,2.],'fewer_than_four_observations'),([np.nan],'no_observations')]:
            self.assertEqual(inspect_distributions(pd.DataFrame({'x':values}),['x'],missing='exclude').table.iloc[0].flag_status,status)
    def test_missing_and_infinite_refusal(self):
        for values in ([1.,np.nan],[1.,np.inf]):
            with self.assertRaises(ValueError): inspect_distributions(pd.DataFrame({'x':values}),['x'],missing='raise')
        with self.assertRaises(ValueError):inspect_distributions(pd.DataFrame({'x':[1.]}),['x'],missing='raise',fence_multiplier=0)
    def test_correlations_known_answers_and_sample_counts(self):
        d=pd.DataFrame({'x':[1.,2.,3.,4.],'y':[8.,6.,4.,2.],'z':[1.,np.nan,3.,4.]})
        for method in ('pearson','spearman'):
            r=inspect_relationships(d,[('x','y'),('x','z')],method=method,missing='pairwise')
            np.testing.assert_allclose(r.table.coefficient,[-1,1])
            self.assertEqual(r.table.used.tolist(),[4,3])
            self.assertEqual(r.rows.loc[~r.rows.used,'position'].tolist(),[1])
    def test_constant_and_short_inputs(self):
        d=pd.DataFrame({'x':[1.,1.,1.],'y':[1.,2.,3.]})
        self.assertEqual(inspect_relationships(d,[('x','y')],method='pearson',missing='raise').table.iloc[0].status,'constant_input')
        self.assertEqual(inspect_relationships(d.iloc[:2],[('x','y')],method='spearman',missing='raise').table.iloc[0].status,'insufficient_pairs')
    def test_pair_selection_boundaries(self):
        d=pd.DataFrame({'x':[1.,2.,3.],'y':[2.,4.,np.nan]})
        for pairs in ([('x','x')],[('x','y'),('y','x')],[]):
            with self.assertRaises(ValueError):inspect_relationships(d,pairs,method='pearson',missing='pairwise')
        with self.assertRaises(ValueError):inspect_relationships(d,[('x','y')],method='pearson',missing='raise')
    def test_plot_checks_source_and_preserves_all_values(self):
        d=pd.DataFrame({'x':[1.,2.,3.,4.,100.]});r=inspect_distributions(d,['x'],missing='raise')
        fig=plot_distribution(d,r,field='x',bins=5)
        self.assertEqual(sum(p.get_height() for p in fig.axes[0].patches),5)
        self.assertEqual(fig.axes[1].lines[0].get_ydata()[-1],1)
        plt.close(fig)
        d.loc[0,'x']=9
        with self.assertRaises(ValueError):plot_distribution(d,r,field='x',bins=5)

    def test_scatter_uses_selected_complete_pairs_and_checks_snapshot(self):
        d=pd.DataFrame({'x':[1.,2.,3.,4.],'y':[2.,4.,6.,np.nan]})
        result=inspect_relationships(d,[('x','y')],method='pearson',missing='pairwise')
        fig=plot_relationship(d,result,left='x',right='y')
        self.assertEqual(len(fig.axes[0].collections[0].get_offsets()),3)
        plt.close(fig)
        d.loc[0,'y']=8
        with self.assertRaises(ValueError):plot_relationship(d,result,left='x',right='y')

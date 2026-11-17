import unittest
import pandas as pd
from statistical_exploration_lab.team_workbench import (
    read_local_csv, prepare_explicit_numeric, overview_evidence,
    relationship_evidence, grouped_evidence, notebook_item,
)

class WorkbenchTests(unittest.TestCase):
    def test_original_headers_and_literal_categories(self):
        for content in (b'x,x\n1,2', b',x\n1,2'):
            with self.assertRaises(ValueError): read_local_csv(content)
        frame=read_local_csv(b'id,category,value\n001,NA,\n002,ok,3')
        self.assertEqual(frame.loc[0,'id'],'001')
        self.assertEqual(frame.loc[0,'category'],'NA')
        self.assertTrue(pd.isna(frame.loc[0,'value']))

    def test_composite_key_and_numeric_generator(self):
        frame=pd.DataFrame({'unit':['a','a','b'],'period':[1,2,1],'x':[1.,2.,3.]})
        result=overview_evidence(frame,observation_key=['unit','period'],numeric_fields=(x for x in ['x']))
        self.assertIsNotNone(result['types'])
        self.assertIsNotNone(result['numeric'])

    def test_grouped_weight_and_eligibility_handoff(self):
        frame=pd.DataFrame({'y':[0,1,1],'w':[1.,3.,100.]})
        result=grouped_evidence(frame,outcome='y',group=None,weight='w',eligible=[True,True,False])
        self.assertEqual(result.table.loc[0,'proportion'],.75)
        self.assertEqual(result.table.loc[0,'used'],2)
        self.assertEqual(result.table.loc[0,'ineligible'],1)

    def test_preparation_copy_and_relationship_missing_choice(self):
        raw=pd.DataFrame({'x':['1','2',None],'y':[1.,2.,3.]})
        frame=prepare_explicit_numeric(raw,['x'])
        self.assertEqual(raw.loc[0,'x'],'1')
        with self.assertRaises(ValueError): relationship_evidence(frame,left='x',right='y',missing='raise',include_plot=False)
        result=relationship_evidence(frame,left='x',right='y',include_plot=False)
        self.assertEqual(result['result'].table.loc[0,'status'],'insufficient_pairs')
        self.assertIn('unavailable',result['hints'][0])

    def test_notebook_counts_detached(self):
        counts={'used':[2]}
        item=notebook_item('Demo',pd.DataFrame({'x':[1,2]}),chosen_fields=['x'],calculation='description',status='completed',counts=counts)
        counts['used'][0]=99
        self.assertEqual(item['counts']['used'],[2])

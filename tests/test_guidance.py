import unittest
import tempfile
from pathlib import Path
import pandas as pd
from statistical_exploration_lab import summarize_binary, inspect_relationships, write_investigation
from statistical_exploration_lab.guidance import explain_result


class GuidanceTests(unittest.TestCase):
    def groups(self, values, **kw):
        frame=pd.DataFrame({'event':values, 'group':['A']*len(values), 'w':list(range(1,len(values)+1))})
        return summarize_binary(frame,outcome='event',by='group',missing='exclude',**kw)

    def explain(self, result):
        return explain_result(result,question='What changed?',relevance='Compare the chosen event or relationship.')

    def test_changed_outcomes_change_facts(self):
        self.assertIn('0.0%', self.explain(self.groups([0,0])).observation)
        self.assertIn('100.0%', self.explain(self.groups([1,1])).observation)

    def test_unavailable_is_not_zero(self):
        section=self.explain(self.groups([None,None]))
        self.assertIn('unavailable',section.observation)
        self.assertNotIn('0.0%',section.observation)
        self.assertIn('no usable denominator',section.next_step)

    def test_missing_and_weighted_guidance(self):
        s=self.explain(self.groups([0,1,None],weight='w'))
        self.assertIn('66.7% weighted',s.observation)
        self.assertIn('1 missing eligible outcomes',s.observation)
        self.assertIn('sampling design',s.next_step)
        self.assertIn('Counts are unweighted',s.interpretation)

    def test_constant_replaces_relationship_claim(self):
        s=self.explain(inspect_relationships(pd.DataFrame({'x':[1,1,1],'y':[1,2,3]}),[('x','y')],method='pearson',missing='pairwise'))
        self.assertIn('unavailable (constant_input)',s.observation)
        self.assertIn('constant',s.next_step)
        self.assertNotIn('scatterplot',s.next_step)

    def test_direction_changes(self):
        for y, expected in [([1,2,3],'1.000'),([3,2,1],'-1.000')]:
            s=self.explain(inspect_relationships(pd.DataFrame({'x':[1,2,3],'y':y}),[('x','y')],method='pearson',missing='pairwise'))
            self.assertIn('correlation '+expected,s.observation)

    def test_snapshot_and_stale_explanation(self):
        result=self.groups([0,1]);s=self.explain(result)
        result.table.loc[0,'proportion']=0
        self.assertEqual(s.result.table.loc[0,'proportion'],.5)
        s.result.table.loc[0,'proportion']=1
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'review'
            with self.assertRaisesRegex(ValueError,'regenerate'):
                write_investigation(target,title='Test',source='Artificial',sections=[s])
            self.assertFalse(target.exists())

    def test_relevance_required(self):
        with self.assertRaises(ValueError): explain_result(self.groups([0,1]),question='?',relevance='')

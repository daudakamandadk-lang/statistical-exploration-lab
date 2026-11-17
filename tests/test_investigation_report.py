import json
import tempfile
import unittest
from pathlib import Path
import pandas as pd
from statistical_exploration_lab import summarize_binary, InvestigationSection, write_investigation

class InvestigationReportTests(unittest.TestCase):
    def section(self):
        result=summarize_binary(pd.DataFrame({'event':[0.,None],'g':['<script>alert(1)</script>','empty']}),outcome='event',by='g',missing='exclude')
        return InvestigationSection('Which group?',result,'Observed values','Descriptive only','Review missingness','No uncertainty estimate','Percent describes event frequency; counts show the denominator.')
    def test_saved_evidence_escaping_and_no_recomputation(self):
        section=self.section();before=section.result.table.copy(deep=True)
        with tempfile.TemporaryDirectory() as tmp:
            page=write_investigation(Path(tmp)/'new',title='<Title>',source='Artificial fixture',sections=[section])
            text=page.read_text(encoding='utf-8')
            self.assertNotIn('<script>alert',text)
            self.assertIn('&lt;script&gt;',text)
            self.assertIn('Unavailable',text)
            evidence=json.loads((page.parent/'evidence.json').read_text(encoding='utf-8'))
            self.assertEqual(evidence['sections'][0]['choices']['missing'],'exclude')
            self.assertIn('not_estimable',text)
            pd.testing.assert_frame_equal(before,section.result.table)
    def test_existing_folder_and_missing_explanation_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(FileExistsError):write_investigation(tmp,title='Title',source='Fixture',sections=[self.section()])
            bad=self.section()
            bad=InvestigationSection('',bad.result,'a','b','c','d','e')
            with self.assertRaises(ValueError):write_investigation(Path(tmp)/'new',title='Title',source='Fixture',sections=[bad])
            self.assertFalse((Path(tmp)/'new').exists())

    def test_numeric_evidence_roundtrips(self):
        section=self.section()
        section.result.table.loc[0,'proportion']=0.12345678901234568
        with tempfile.TemporaryDirectory() as tmp:
            page=write_investigation(Path(tmp)/'new',title='Title',source='Fixture',sections=[section])
            saved=json.loads((page.parent/'evidence.json').read_text(encoding='utf-8'))['sections'][0]['table']
            self.assertEqual(saved['data'][0][saved['columns'].index('proportion')],0.12345678901234568)
            self.assertIn('Why these measures',page.read_text(encoding='utf-8'))

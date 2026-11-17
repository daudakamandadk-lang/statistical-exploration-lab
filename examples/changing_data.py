"""Artificial changes exercise explanations; choose a new output to retain them."""
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from statistical_exploration_lab import summarize_binary, inspect_relationships, write_investigation
from statistical_exploration_lab.guidance import explain_result

def build_sections():
    sections=[]
    for label,values in [('Baseline',[0,1,0,1]),('All events',[1,1,1,1]),('No observed outcomes',[None]*4)]:
        result=summarize_binary(pd.DataFrame({'event':values}),outcome='event',by=None,missing='exclude')
        sections.append(explain_result(result,question=f'{label}: what is the recorded event frequency?',relevance='Verify that changing outcomes changes the factual explanation and next check.'))
    for label,values in [('Increasing',[1,2,3,4]),('Decreasing',[4,3,2,1]),('Constant',[2,2,2,2])]:
        result=inspect_relationships(pd.DataFrame({'x':[1,2,3,4],'y':values}),[('x','y')],method='pearson',missing='pairwise')
        sections.append(explain_result(result,question=f'{label}: is a linear association estimable?',relevance='Verify direction changes and the unavailable-result boundary.'))
    return sections

if __name__=='__main__':
    with TemporaryDirectory() as tmp:
        sections=build_sections()
        page=write_investigation(Path(tmp)/'review',title='Artificial data-change checks',source='Six deliberate artificial scenarios; no real-world conclusions.',sections=sections)
        for s in sections: print(s.question, s.observation)
        assert page.exists()

"""Artificial example: edit the question and interpretation in VS Code cells."""
# %% Choose data and calculation
from pathlib import Path
from tempfile import TemporaryDirectory
import pandas as pd
from statistical_exploration_lab import summarize_binary, InvestigationSection, write_investigation

data=pd.DataFrame({'group':['A','A','B','B'], 'event':[0,1,1,None]})
result=summarize_binary(data,outcome='event',by='group',missing='exclude')

# %% Explain supplied evidence; no automatic decisions
section=InvestigationSection(
    question='How common is the recorded event in each artificial group?',
    result=result,
    observation='A has 1 event in 2 observations; B has 1 event in 1 usable observation.',
    metric_purpose='Percentage describes event frequency. Eligible, missing and used counts expose the denominator.',
    interpretation='The percentages describe this tiny fixture; B has one missing outcome.',
    next_step='Inspect the missing outcome before comparing the groups.',
    limitations='Artificial data. No population claim, uncertainty estimate or meaningful ranking.'
)

# %% Temporary output for a repeatable smoke check.
# To retain a report, choose a new caller-owned directory instead.
if __name__=='__main__':
    with TemporaryDirectory() as tmp:
        page=write_investigation(Path(tmp)/'review',title='Artificial grouped investigation',source='Four artificial records',sections=[section])
        assert page.is_file() and (page.parent/'evidence.json').is_file()
        print('Question-led HTML and JSON written successfully to temporary storage.')

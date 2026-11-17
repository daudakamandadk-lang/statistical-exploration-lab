"""Question-led presentation of supplied descriptive lab results; no estimation."""
from dataclasses import dataclass
from pathlib import Path
import html
import json
import math
import pandas as pd
from .contract import _plain
from .exploration import Exploration
from .grouped import GroupedProportions

@dataclass(frozen=True)
class InvestigationSection:
    question: str
    result: object
    observation: str
    interpretation: str
    next_step: str
    limitations: str
    metric_purpose: str

def _frame_evidence(frame):
    # Preserve Python float round trips; pandas to_json rounds numeric values.
    def clean(value):
        value = _plain(value)
        if isinstance(value, float) and math.isnan(value):
            return None
        if isinstance(value, list):
            return [clean(v) for v in value]
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items()}
        return value
    return clean(frame.to_dict(orient='split'))


def _evidence(section):
    if not isinstance(section,InvestigationSection):raise TypeError('Use InvestigationSection entries')
    if not isinstance(section.result,(Exploration,GroupedProportions)):
        raise TypeError('This report accepts descriptive Exploration or GroupedProportions results')
    for name in ('question','observation','interpretation','next_step','limitations','metric_purpose'):
        if not isinstance(getattr(section,name),str) or not getattr(section,name).strip():
            raise ValueError(f'Supply explicit {name} text')
    result=section.result
    evidence={name:getattr(section,name) for name in ('question','observation','interpretation','next_step','limitations','metric_purpose')}
    evidence.update(table=_frame_evidence(result.table),
                    choices=_plain(result.choices),input_fingerprint=result.input_fingerprint)
    if hasattr(result,'rows'):evidence['row_evidence']=_frame_evidence(result.rows)
    return evidence

def _table(frame):
    return '<div class="scroll">'+frame.to_html(index=False,escape=True,na_rep='Unavailable',float_format=lambda x:f'{x:,.3f}')+'</div>'

def _body(title,source,sections,evidence):
    esc=html.escape
    content=[]
    for i,(section,item) in enumerate(zip(sections,evidence),1):
        result=section.result;table=result.table.copy(deep=True)
        if isinstance(result,GroupedProportions):
            table['percent']=100*table.proportion
            primary=table[['group','eligible','missing_outcome','used','events','percent','status']].rename(columns={
                'group':'Group','eligible':'Eligible','missing_outcome':'Missing outcome','used':'Observations used','events':'Observed events','percent':'Percent','status':'Calculation status'})
            method='Weighted descriptive percentage' if result.choices['weight'] else 'Unweighted descriptive percentage'
            method+=' · Counts are unweighted. No uncertainty interval calculated.'
        elif 'coefficient' in table:
            primary=table[['left','right','coefficient','used','excluded','status','warnings']].rename(columns={
                'left':'First field','right':'Second field','coefficient':'Correlation','used':'Pairs used','excluded':'Pairs excluded','status':'Calculation status','warnings':'Numerical warnings'})
            method=result.choices['method'].title()+' correlation · Unweighted · Descriptive only'
        else:
            primary=table[['field','used','missing','median','q25','q75','flagged','flag_status']].rename(columns={
                'field':'Field','used':'Observations used','missing':'Missing','median':'Middle value','q25':'25th percentile','q75':'75th percentile','flagged':'Review flags','flag_status':'Flag calculation status'})
            method='Unweighted distribution summary · Flags are review candidates, not errors'
        # Avoid thousands of positional values in the reading view; retain them in JSON.
        display_choices={k:(f'{len(v)} positions; see evidence.json' if k=='eligible_positions' else v)
                         for k,v in item['choices'].items()}
        content.append(f'''<section id="question-{i}"><span class="eyebrow">QUESTION {i}</span>
<h2>{esc(section.question)}</h2><p class="observation">{esc(section.observation)}</p>
<p><strong>Why these measures:</strong> {esc(section.metric_purpose)}</p>
<p class="method">{esc(method)}</p>{_table(primary)}
<div class="notes"><div><h3>What this means</h3><p>{esc(section.interpretation)}</p></div>
<div><h3>Next investigation</h3><p>{esc(section.next_step)}</p></div></div>
<p class="limit"><strong>Limits:</strong> {esc(section.limitations)}</p>
<details><summary>Inspect calculations and choices</summary>{_table(table)}
<pre>{esc(json.dumps(display_choices,indent=2,ensure_ascii=False))}</pre></details></section>''')
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>{esc(title)}</title><style>
body{{margin:0;background:#f3f5f7;color:#203444;font:17px/1.55 system-ui,sans-serif}}
main{{max-width:1080px;margin:auto;padding:32px 20px}}header{{padding:32px;background:#153d50;color:white;border-radius:12px}}
h1{{font-size:30px;line-height:1.2}}h2{{font-size:24px;line-height:1.3}}h3{{font-size:17px;margin-bottom:8px}}
section{{padding:28px;margin:24px 0;background:white;border:1px solid #d9e2e8;border-radius:12px}}
.eyebrow,.method{{font-size:13px;color:#526775}}.observation{{font-size:21px;font-weight:600}}
.notes{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.limit{{background:#fff4df;padding:14px;border-left:4px solid #b78421}}
.scroll{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:14px}}td,th{{padding:10px;text-align:left;border-bottom:1px solid #dce4e9}}
th{{background:#edf3f6}}pre{{white-space:pre-wrap;overflow-wrap:anywhere;font-size:12px}}details{{margin-top:18px}}summary{{cursor:pointer;font-weight:600}}
@media(max-width:650px){{.notes{{grid-template-columns:1fr}}section{{padding:18px}}h1{{font-size:26px}}}}
</style></head><body><main><header><p>STATISTICAL LAB · INVESTIGATION REVIEW</p><h1>{esc(title)}</h1>
<p>{esc(source)}</p></header><p>Read the observation first, then its meaning and next step. Calculation status describes whether a value was computed; it is not a reliability rating. Explanations are supplied by the investigator, not generated statistical conclusions.</p>
{''.join(content)}<footer><p>Supplied result values, choices and row evidence are saved in evidence.json. Missing results are shown as unavailable, never as zero. The renderer formats supplied statistics, including proportions as percentages; it does not estimate new statistics.</p></footer></main></body></html>'''

def write_investigation(output, *, title, source, sections):
    """Write HTML and JSON to a new directory; refuse existing destinations.

    Explanations are caller-authored. Does not validate their truth or recompute
    supplied statistics. Table edits are preserved as supplied, not re-estimated.
    """
    if not isinstance(title,str) or not title.strip() or not isinstance(source,str) or not source.strip():
        raise ValueError('Supply title and source text')
    sections=list(sections)
    if not sections:raise ValueError('Supply at least one investigation section')
    evidence=[_evidence(s) for s in sections]
    encoded=json.dumps({'title':title,'source':source,'sections':evidence},indent=2,ensure_ascii=False,allow_nan=False)
    page=_body(title,source,sections,evidence)
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    owned=[]
    try:
        for name,text in [('evidence.json',encoded),('review.html',page)]:
            path=output/name
            with path.open('x',encoding='utf-8') as handle:
                owned.append(path);handle.write(text)
    except BaseException:
        for path in owned:path.unlink(missing_ok=True)
        try:output.rmdir()
        except OSError:pass
        raise
    return output/'review.html'

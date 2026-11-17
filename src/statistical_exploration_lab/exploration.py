"""Selected descriptive investigations, delegated to pandas/NumPy/SciPy."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import warnings
import numpy as np
import pandas as pd
import scipy
from scipy import stats
from .contract import data_fingerprint
from .investigation import _numeric_selection

@dataclass(frozen=True)
class Exploration:
    """Editable tables and creation-time evidence; not a frozen archive."""
    table: pd.DataFrame
    rows: pd.DataFrame
    choices: Mapping
    input_fingerprint: str

def inspect_distributions(data, columns, *, missing, fence_multiplier=1.5):
    """Describe each selected numeric field and flag values outside IQR fences.

    Linear-interpolated quartiles; sample SD (ddof=1). No fitted distribution,
    significance test or automatic removal. Zero IQR disables flagging explicitly.
    Rows contains flagged original zero-based positions, field and value.
    """
    selected=_numeric_selection(data,columns)
    if missing not in ('raise','exclude'): raise ValueError("missing must be 'raise' or 'exclude'")
    if isinstance(fence_multiplier,bool) or not isinstance(fence_multiplier,(int,float)) or not np.isfinite(fence_multiplier) or fence_multiplier<=0:
        raise ValueError('fence_multiplier must be positive and finite')
    if missing=='raise' and selected.isna().any().any(): raise ValueError('Selected values are missing')
    records=[]; flags=[]
    for name in columns:
        s=selected[name].astype(float); valid=s.dropna(); n=len(valid)
        record={'field':name,'total':len(s),'used':n,'missing':int(s.isna().sum()),
                'mean':np.nan,'std':np.nan,'min':np.nan,'q25':np.nan,'median':np.nan,'q75':np.nan,'max':np.nan,
                'iqr':np.nan,'lower_fence':np.nan,'upper_fence':np.nan,'flagged':0,'flag_status':'no_observations'}
        if n:
            q=valid.quantile([.25,.5,.75],interpolation='linear');iqr=float(q.loc[.75]-q.loc[.25])
            record.update(mean=float(valid.mean()),std=float(valid.std(ddof=1)) if n>1 else np.nan,
                          min=float(valid.min()),q25=float(q.loc[.25]),median=float(q.loc[.5]),q75=float(q.loc[.75]),max=float(valid.max()),iqr=iqr)
            if n<4: record['flag_status']='fewer_than_four_observations'
            elif iqr==0: record['flag_status']='zero_iqr'
            else:
                lo=float(q.loc[.25]-fence_multiplier*iqr);hi=float(q.loc[.75]+fence_multiplier*iqr)
                if not np.isfinite([lo,hi,iqr]).all(): raise ValueError('Fence calculation overflow; rescale explicitly')
                positions=np.flatnonzero(((s<lo)|(s>hi)).to_numpy())
                record.update(lower_fence=lo,upper_fence=hi,flagged=len(positions),flag_status='evaluated')
                flags.extend({'field':name,'position':int(i),'value':float(s.iloc[i])} for i in positions)
        if any(np.isinf(record[key]) for key in ['mean','std','min','q25','median','q75','max','iqr']):
            raise ValueError('Summary calculation overflow; rescale measurements explicitly')
        records.append(record)
    return Exploration(pd.DataFrame(records),pd.DataFrame(flags,columns=['field','position','value']),
        MappingProxyType({'columns':tuple(columns),'missing':missing,'fence_multiplier':fence_multiplier,
                          'quantile_interpolation':'linear','minimum_flag_observations':4,
                          'pandas_version':pd.__version__}),data_fingerprint(data))

def inspect_relationships(data, pairs, *, method, missing):
    """Describe only chosen numeric pairs. missing='pairwise' or 'raise'.

    SciPy calculates Pearson or Spearman coefficients. No p-values are exposed:
    this exploratory helper does not establish a sampling/inference design.
    At least three complete pairs are required by this helper. Constant inputs
    return an unavailable coefficient; numerical warnings are retained.
    """
    if method not in ('pearson','spearman'): raise ValueError('Choose pearson or spearman')
    if missing not in ('raise','pairwise'): raise ValueError('Choose raise or pairwise missing handling')
    if not isinstance(pairs,(list,tuple)) or not pairs: raise ValueError('Select a nonempty list of pairs')
    seen=set();names=[]
    for pair in pairs:
        if not isinstance(pair,(list,tuple)) or len(pair)!=2 or any(not isinstance(c,str) for c in pair) or pair[0]==pair[1]:
            raise ValueError('Each pair must contain two distinct field names')
        key=frozenset(pair)
        if key in seen: raise ValueError('Duplicate or reversed pair selected')
        seen.add(key);names.extend(c for c in pair if c not in names)
    selected=_numeric_selection(data,names)
    records=[];row_records=[]
    for left,right in pairs:
        frame=selected[[left,right]]; complete=frame.notna().all(axis=1).to_numpy()
        if missing=='raise' and not complete.all(): raise ValueError(f'Missing selected values for {left}/{right}')
        used=frame.iloc[np.flatnonzero(complete)].astype(float);n=len(used)
        coefficient=np.nan;status='estimated';notes=''
        if n<3:status='insufficient_pairs'
        elif used[left].nunique()<2 or used[right].nunique()<2:status='constant_input'
        else:
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter('always')
                answer=(stats.pearsonr if method=='pearson' else stats.spearmanr)(used[left],used[right])
            coefficient=float(answer.statistic)
            notes='; '.join(str(w.message) for w in caught)
            if not np.isfinite(coefficient):status='numerically_unavailable'
            elif caught:status='estimated_with_warning'
        records.append({'left':left,'right':right,'method':method,'total':len(data),'used':n,
                        'excluded':len(data)-n,'coefficient':coefficient,'status':status,'warnings':notes})
        row_records.extend({'left':left,'right':right,'position':int(i),'used':bool(ok)} for i,ok in enumerate(complete))
    return Exploration(pd.DataFrame(records),pd.DataFrame(row_records),MappingProxyType({
        'pairs':tuple(tuple(p) for p in pairs),'method':method,'missing':missing,
        'minimum_pairs':3,'scipy_version':scipy.__version__,'pandas_version':pd.__version__}),data_fingerprint(data))

def plot_distribution(data, result, *, field, bins):
    """Histogram and empirical CDF; require the unchanged source and chosen bins."""
    if not isinstance(result,Exploration) or 'columns' not in result.choices: raise TypeError('Use a distribution result')
    if data_fingerprint(data)!=result.input_fingerprint: raise ValueError('Source changed; rerun investigation')
    if field not in result.choices['columns']:raise ValueError('Choose an investigated field')
    if isinstance(bins,bool) or not isinstance(bins,int) or bins<1:raise ValueError('bins must be a positive integer')
    values=data[field].dropna().to_numpy(dtype=float)
    if not len(values):raise ValueError('No observations to plot')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
    axes[0].hist(values,bins=bins);axes[0].set(xlabel=field,ylabel='Count',title=f'Histogram (n={len(values)})')
    unique,counts=np.unique(values,return_counts=True)
    axes[1].step(np.r_[unique[0],unique],np.r_[0,np.cumsum(counts)/len(values)],where='post')
    axes[1].set(xlabel=field,ylabel='Cumulative share',ylim=(0,1),title='Empirical distribution')
    return fig


def plot_relationship(data, result, *, left, right):
    """Scatter the complete observations for one explicitly investigated pair."""
    if not isinstance(result,Exploration) or 'pairs' not in result.choices:
        raise TypeError('Use a relationship result')
    if (left,right) not in result.choices['pairs']:
        raise ValueError('Choose an investigated pair in its original order')
    if data_fingerprint(data)!=result.input_fingerprint:
        raise ValueError('Source changed; rerun investigation')
    values=data[[left,right]].dropna()
    if values.empty:raise ValueError('No complete observations to plot')
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(6,4),layout='constrained')
    ax.scatter(values[left],values[right],alpha=.5)
    ax.set(xlabel=left,ylabel=right,title=f'Selected observations (n={len(values)})')
    return fig

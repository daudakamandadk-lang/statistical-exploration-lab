"""Explicit binary descriptions using pandas grouping and NumPy averaging."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping
import numpy as np
import pandas as pd
from .contract import data_fingerprint

@dataclass(frozen=True)
class GroupedProportions:
    """Editable result table with creation-time choices and source identity."""
    table: pd.DataFrame
    choices: Mapping
    input_fingerprint: str

def summarize_binary(data, *, outcome, by, missing, weight=None, eligible=None):
    """Describe an explicitly coded 0/1 outcome by one field, or overall.

    missing='raise' refuses missing outcomes among eligible rows; 'exclude'
    excludes them from the denominator and reports their count. Missing group
    labels form a visible group. eligible is a positional boolean sequence,
    never index-aligned. Weights must be positive finite numeric values for all
    eligible rows, even when the outcome is missing. No weight is inferred.
    Only observed groups are returned; empty input returns an overall unavailable
    row when by=None. No intervals, tests, population totals or predictions.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a pandas DataFrame')
    if not data.columns.is_unique:
        raise ValueError('Table columns must be unique')
    names=[outcome]+([by] if by is not None else [])+([weight] if weight is not None else [])
    if any(not isinstance(c,str) or not c.strip() for c in names):
        raise ValueError('Selected fields must be nonblank names')
    if len(set(names))!=len(names) or not set(names)<=set(data.columns):
        raise ValueError('Select distinct, present outcome/group/weight fields')
    if missing not in ('raise','exclude'):
        raise ValueError("missing must be 'raise' or 'exclude'")
    fingerprint=data_fingerprint(data)
    if eligible is None:
        mask=np.ones(len(data),dtype=bool)
    else:
        mask=np.asarray(eligible)
        if mask.ndim!=1 or len(mask)!=len(data) or mask.dtype.kind!='b':
            raise ValueError('eligible must contain exactly one boolean per input row')
    y=data[outcome].reset_index(drop=True)
    if not y[mask].dropna().isin([0,1]).all():
        raise ValueError('Eligible outcomes must be explicitly coded 0/1 or missing')
    if missing=='raise' and y[mask].isna().any():
        raise ValueError('Eligible outcomes are missing; review or choose missing="exclude"')
    w=pd.Series(np.ones(len(data)))
    if weight is not None:
        original=data[weight]
        if (not pd.api.types.is_numeric_dtype(original) or pd.api.types.is_bool_dtype(original)
                or pd.api.types.is_complex_dtype(original)):
            raise TypeError('Weights must be real numeric measurements')
        w=original.reset_index(drop=True).astype(float)
        if not np.isfinite(w[mask]).all() or (w[mask]<=0).any():
            raise ValueError('Eligible weights must be positive and finite; review explicitly')
    frame=pd.DataFrame({'value':y,'eligible':mask,'weight':w})
    if by is not None:
        frame['group']=data[by].reset_index(drop=True)
        groups=frame.groupby('group',dropna=False,observed=True,sort=False)
    else:
        groups=[('All',frame)]
    rows=[]
    for label, part in groups:
        target=part[part.eligible]
        used=target[target.value.notna()]
        events=int(used.value.sum())
        if len(used):
            weights=used.weight.to_numpy()
            # Scaling leaves the mean unchanged and avoids overflow in averaging.
            rate=float(np.average(used.value.astype(float),weights=weights/weights.max()))
            weight_sum=float(weights.sum())
            if not np.isfinite(weight_sum): raise ValueError('Weight sum overflow; rescale weights explicitly')
        else:
            rate=np.nan;weight_sum=0.
        rows.append({'group':label,'rows':len(part),'eligible':len(target),
                     'ineligible':len(part)-len(target),'missing_outcome':int(target.value.isna().sum()),
                     'used':len(used),'events':events,'weight_sum':weight_sum,
                     'proportion':rate,'status':'estimated' if len(used) else 'not_estimable'})
    columns=['group','rows','eligible','ineligible','missing_outcome','used','events','weight_sum','proportion','status']
    choices=MappingProxyType({'outcome':outcome,'by':by,'missing':missing,'weight':weight,
                             'eligible_positions':tuple(int(i) for i in np.flatnonzero(mask)),
                             'pandas_version':pd.__version__,'numpy_version':np.__version__})
    return GroupedProportions(pd.DataFrame(rows,columns=columns),choices,fingerprint)

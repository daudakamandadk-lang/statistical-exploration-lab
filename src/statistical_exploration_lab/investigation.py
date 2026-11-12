"""Small workflow helpers; pandas/statsmodels own the statistical calculations."""
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping

import numpy as np
import pandas as pd

from .contract import data_fingerprint


def _numeric_selection(data, columns):
    if not isinstance(data, pd.DataFrame):
        raise TypeError('data must be a pandas DataFrame; load and prepare it explicitly')
    if not data.columns.is_unique or any(not isinstance(c, str) or not c.strip()
                                         for c in data.columns):
        raise ValueError('Table columns must be unique nonblank strings')
    if (not isinstance(columns, (list, tuple)) or not columns
            or any(not isinstance(c, str) for c in columns)
            or len(set(columns)) != len(columns)):
        raise ValueError('columns must be a nonempty list/tuple of distinct names')
    absent = set(columns) - set(data.columns)
    if absent:
        raise ValueError(f'Selected columns are absent: {sorted(absent)}')
    selected = data.loc[:, list(columns)].copy(deep=True)
    for name in columns:
        series = selected[name]
        if (not pd.api.types.is_numeric_dtype(series)
                or pd.api.types.is_bool_dtype(series)
                or pd.api.types.is_complex_dtype(series)):
            raise TypeError(f'{name!r} must be real numeric data; prepare it explicitly')
        if pd.api.types.is_integer_dtype(series):
            if any(int(float(v)) != int(v) for v in series.dropna()):
                raise ValueError(f'{name!r} loses integer precision in floating-point analysis')
    values = selected.to_numpy(dtype=float, na_value=np.nan)
    if np.isinf(values).any():
        raise ValueError('Selected columns contain infinity; review the data explicitly')
    return selected


def summarize_numeric(data, columns):
    """Return pandas.describe plus total/missing counts for selected fields.

    Missing observations are counted and excluded per column by pandas. This
    is sample description, not a population estimate or a distribution fit.
    """
    selected = _numeric_selection(data, columns)
    if selected.empty:
        raise ValueError('Cannot summarize a table with no rows')
    summary = selected.describe().T
    summary.insert(0, 'total', len(selected))
    summary.insert(1, 'missing', selected.isna().sum())
    return summary


@dataclass(frozen=True)
class OLSInvestigation:
    """Choice/count evidence alongside the full, mutable statsmodels result.

    The native fitted result is intentionally available for direct library
    use. This object is not a frozen statistical archive or an HTML report.
    Row positions are zero-based positions in the input, not index labels.
    """
    fitted: Any
    choices: Mapping
    input_fingerprint: str
    total_rows: int
    used_positions: tuple
    excluded_positions: tuple

    @property
    def used_rows(self):
        return len(self.used_positions)

    def coefficients(self, *, alpha=0.05):
        """Arrange statsmodels outputs; alpha selects its confidence interval."""
        if isinstance(alpha, bool) or not 0 < alpha < 1:
            raise ValueError('alpha must be between 0 and 1')
        interval = self.fitted.conf_int(alpha=alpha)
        return pd.DataFrame({
            'estimate': self.fitted.params,
            'standard_error': self.fitted.bse,
            'p_value': self.fitted.pvalues,
            'interval_low': interval.iloc[:, 0],
            'interval_high': interval.iloc[:, 1],
        })


def fit_ols(data, *, outcome, predictors, missing, cov_type,
            intercept=True, use_t=True):
    """Fit the user's explicit numeric OLS specification using statsmodels.

    missing='raise' refuses missing selected values; 'drop' explicitly uses
    complete rows across the selected outcome and predictors. Nothing is
    imputed, encoded, transformed or selected automatically. cov_type is
    'nonrobust' or 'HC3'; use_t chooses statsmodels' inference reference.
    Enough rows and a full-rank design are required by this helper.
    """
    if not isinstance(outcome, str) or not outcome.strip():
        raise ValueError('outcome must name one column')
    if not isinstance(predictors, (list, tuple)) or not predictors:
        raise ValueError('predictors must be a nonempty list/tuple')
    selected = _numeric_selection(data, [outcome, *predictors])
    if missing not in ('raise', 'drop'):
        raise ValueError("missing must be 'raise' or 'drop'")
    if cov_type not in ('nonrobust', 'HC3'):
        raise ValueError("cov_type must be 'nonrobust' or 'HC3'")
    if not isinstance(intercept, bool) or not isinstance(use_t, bool):
        raise TypeError('intercept and use_t must be booleans')
    incomplete = selected.isna().any(axis=1).to_numpy()
    if incomplete.any() and missing == 'raise':
        raise ValueError("Selected values are missing; review them or explicitly choose missing='drop'")
    used = tuple(int(i) for i in np.flatnonzero(~incomplete))
    excluded = tuple(int(i) for i in np.flatnonzero(incomplete))
    frame = selected.iloc[list(used)].astype(float)
    if frame.empty:
        raise ValueError('No complete selected observations remain')
    try:
        import statsmodels
        import statsmodels.api as sm
    except ImportError as exc:
        raise ImportError('Install statistical-exploration-lab[econometrics] for OLS') from exc
    design = frame.loc[:, list(predictors)]
    if intercept:
        if 'const' in design.columns:
            raise ValueError("Rename predictor 'const' or choose intercept=False")
        design = sm.add_constant(design, has_constant='raise')
    if len(frame) <= design.shape[1]:
        raise ValueError('More usable rows than fitted parameters are required')
    if np.linalg.matrix_rank(design.to_numpy()) != design.shape[1]:
        raise ValueError('Selected design is rank deficient; review predictors explicitly')
    fitted = sm.OLS(frame[outcome], design, missing='raise', hasconst=intercept).fit(
        cov_type=cov_type, use_t=use_t)
    choices = MappingProxyType({
        'outcome': outcome, 'predictors': tuple(predictors), 'missing': missing,
        'cov_type': cov_type, 'intercept': intercept, 'use_t': use_t,
        'pandas_version': pd.__version__, 'numpy_version': np.__version__,
        'statsmodels_version': statsmodels.__version__,
    })
    return OLSInvestigation(fitted, choices, data_fingerprint(data), len(data), used, excluded)


def plot_ols_diagnostics(result):
    """Return residual/fitted and normal Q-Q views; do not save/show or refit.

    These views support inspection; they do not certify assumptions or causal
    identification. Call the library directly for other chosen diagnostics.
    """
    if not isinstance(result, OLSInvestigation):
        raise TypeError('result must come from fit_ols')
    import matplotlib.pyplot as plt
    from statsmodels.graphics.gofplots import qqplot
    figure, axes = plt.subplots(1, 2, figsize=(10, 4))
    axes[0].scatter(result.fitted.fittedvalues, result.fitted.resid, alpha=0.7)
    axes[0].axhline(0, color='gray', linewidth=1)
    axes[0].set(xlabel='Fitted value', ylabel='Residual', title='Residuals versus fitted')
    qqplot(np.asarray(result.fitted.resid), line='s', ax=axes[1])
    axes[1].set_title('Normal Q-Q view of residuals')
    figure.tight_layout()
    return figure

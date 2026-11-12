"""Generic statistical-lab investigation; no credit-risk model or real data.

Run the # %% cells in order. Edit the selection cell for your own question.
Requires the optional econometrics dependencies. No files are written.
"""

# %% 1. Existing library tools and reusable lab helpers
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from statistical_exploration_lab import (
    fit_ols, plot_ols_diagnostics, profile_structure, summarize_numeric,
)


# %% 2. Your data, variable and method choices
CSV_PATH = None  # Or Path(r"D:\my-data\observations.csv")
OUTCOME = 'response'
PREDICTORS = ['measure_a', 'measure_b']
OBSERVATION_KEY = 'record_id'
MISSING = 'drop'  # 'raise' refuses missing selected observations
COV_TYPE = 'HC3'  # Or 'nonrobust'; no automatic method selection
USE_T = True
INTERCEPT = True
SHOW_PLOTS = False  # True explicitly opens matplotlib views when running as a script


# %% 3. Load a selected table or generate an artificial demonstration
if CSV_PATH is None:
    rng = np.random.default_rng(20261112)
    a, b = rng.normal(size=(2, 40))
    data = pd.DataFrame({
        'record_id': [f'row-{i:03}' for i in range(40)],
        'measure_a': a, 'measure_b': b,
        'response': 2 + 3 * a - 0.5 * b + rng.normal(scale=0.4, size=40),
    })
    data.loc[5, 'measure_b'] = np.nan
else:
    data = pd.read_csv(Path(CSV_PATH), dtype='string', keep_default_na=False,
                       na_values=[''])
    for field in [OUTCOME, *PREDICTORS]:
        data[field] = pd.to_numeric(data[field], errors='raise')
print('Generic laboratory data; artificial unless CSV_PATH is selected.')
print(data.head().to_string(index=False))


# %% 4. Inspect explicitly selected variables
structure = profile_structure(data, observation_key=OBSERVATION_KEY)
print('Structural gate:', structure.gate.status)
if structure.gate.status == 'stop':
    raise ValueError(f'Resolve the structural findings first: {structure.findings}')
print(summarize_numeric(data, [OUTCOME, *PREDICTORS]).to_string())


# %% 5. Reuse statsmodels, with row accounting and your choices attached
investigation = fit_ols(
    data, outcome=OUTCOME, predictors=PREDICTORS, missing=MISSING,
    cov_type=COV_TYPE, intercept=INTERCEPT, use_t=USE_T,
)
print('Choices:', dict(investigation.choices))
print('Rows:', investigation.total_rows, 'Used:', investigation.used_rows,
      'Excluded positions:', investigation.excluded_positions)
print(investigation.coefficients(alpha=0.05).to_string())
# The original library result remains accessible:
print('R-squared:', investigation.fitted.rsquared)
# Other deliberate library calls can use investigation.fitted directly.


# %% 6. Optional presentation; no refitting or automatic interpretation
diagnostic_figure = plot_ols_diagnostics(investigation)
if SHOW_PLOTS:
    plt.show()
# In VS Code's interactive window this expression displays the figure.
diagnostic_figure
# These are sample associations, not causal conclusions or credit-risk scores.

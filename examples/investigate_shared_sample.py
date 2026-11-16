# %% Choose the question and fields. Artificial data only; no credit-risk model.
import numpy as np
import pandas as pd

from statistical_exploration_lab import fit_ols, select_complete_cases

OUTCOME = 'response'
BASE_PREDICTORS = ['measure_a']
EXTENDED_PREDICTORS = ['measure_a', 'measure_b']
COV_TYPE = 'HC3'
INTERCEPT = True
USE_T = True
ALPHA = 0.05  # 95% coefficient intervals; change deliberately.

# %% Create neutral artificial observations. Replace this cell with your own load.
rng = np.random.default_rng(16)
table = pd.DataFrame({
    'record_id': [f'r{i:02d}' for i in range(30)],
    'measure_a': rng.normal(size=30),
    'measure_b': rng.normal(size=30),
})
table['response'] = (2 + 3 * table['measure_a'] - 0.5 * table['measure_b']
                     + rng.normal(scale=0.5, size=30))
table.loc[[3, 9], 'measure_b'] = np.nan

# %% Review an explicitly shared sample before fitting either specification.
fields = list(dict.fromkeys([OUTCOME, *BASE_PREDICTORS, *EXTENDED_PREDICTORS]))
# Show the sample difference that separate missing-row dropping would create.
available_rows = pd.Series({
    'base alone': table[[OUTCOME, *BASE_PREDICTORS]].notna().all(axis=1).sum(),
    'extended alone': table[[OUTCOME, *EXTENDED_PREDICTORS]].notna().all(axis=1).sum(),
}, name='complete rows')
print(available_rows)
sample = select_complete_cases(table, columns=fields)
print('Rows used:', sample.used_rows, '/', sample.total_rows)
print('Original excluded positions and missing fields:', dict(sample.missing_by_position))
print(sample.table.head())
# Stop and review exclusions here. Complete cases need not represent the source population.

# %% Fit the two specifications you chose, on exactly this sample.
base = fit_ols(sample.table, outcome=OUTCOME, predictors=BASE_PREDICTORS,
               missing='raise', cov_type=COV_TYPE, intercept=INTERCEPT, use_t=USE_T)
extended = fit_ols(sample.table, outcome=OUTCOME, predictors=EXTENDED_PREDICTORS,
                   missing='raise', cov_type=COV_TYPE, intercept=INTERCEPT, use_t=USE_T)
if (base.used_positions != extended.used_positions
        or base.input_fingerprint != extended.input_fingerprint
        or base.input_fingerprint != sample.selected_fingerprint):
    raise ValueError('The fits no longer share the selected sample; rerun selection and both fits')

# %% Inspect native estimates side by side; no automatic winner or causal claim.
estimates = pd.concat({'base': base.fitted.params, 'extended': extended.fitted.params}, axis=1)
print(estimates)
# Inspect uncertainty as well as point estimates. These intervals use the
# covariance/reference choices above; they do not establish causal effects.
coefficient_details = pd.concat({
    'base': base.coefficients(alpha=ALPHA),
    'extended': extended.coefficients(alpha=ALPHA),
}, names=['specification', 'term'])
print(coefficient_details.to_string())
# The artificial generating coefficients were 2, 3 and -0.5. Noise means fitted
# values need not match them. Real investigations do not know these values.
# A blank coefficient means that term was not in that specification, not a zero effect.
# Fit positions refer to sample.table. Map them to original rows when needed:
original_positions = sample.source_positions(extended.used_positions)
print('Original rows used by extended specification:', original_positions)

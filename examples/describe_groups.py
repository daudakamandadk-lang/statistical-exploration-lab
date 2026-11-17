# %% Artificial observations: choose your event, groups and eligibility.
import pandas as pd
from statistical_exploration_lab import summarize_binary

data = pd.DataFrame({
    'event': [0., 1., 1., None, 0.],
    'group': ['A', 'A', 'B', 'B', None],
    'weight': [1., 3., 2., 1., 1.],
})

# %% Inspect unweighted counts and denominators first.
plain = summarize_binary(data, outcome='event', by='group', missing='exclude')
print(plain.table.to_string(index=False))

# %% Deliberately choose weights; inspect the native pandas result table.
weighted = summarize_binary(data, outcome='event', by='group',
                            weight='weight', missing='exclude')
print(weighted.table.to_string(index=False))
# A changes from 50% to 75%; B has one excluded missing outcome.
# Missing group labels stay visible. No uncertainty estimate is computed.

"""Artificial measurements; editable investigation and explicit sensitivity check."""
# %% Choose measurements and pairs; no automatic scan of every pair.
import pandas as pd
import matplotlib.pyplot as plt
from statistical_exploration_lab import (inspect_distributions, inspect_relationships,
    plot_distribution, plot_relationship)

data = pd.DataFrame({'measurement': [1., 2., 3., 4., 5., 6., 7., 30.],
                     'response': [2., 4., 6., 8., 10., 12., 14., 1.]})
PAIRS = [('measurement', 'response')]
SHOW_PLOTS = False

# %% Describe and inspect flagged source positions; retain the original data.
distribution = inspect_distributions(data, ['measurement'], missing='raise', fence_multiplier=1.5)
print(distribution.table.to_string(index=False))
print('Review candidates:', distribution.rows.to_string(index=False))

# %% Compare two deliberately selected descriptions on the same complete rows.
pearson = inspect_relationships(data, PAIRS, method='pearson', missing='raise')
spearman = inspect_relationships(data, PAIRS, method='spearman', missing='raise')
print(pd.concat([pearson.table, spearman.table]).to_string(index=False))
distribution_figure = plot_distribution(data, distribution, field='measurement', bins=5)
relationship_figure = plot_relationship(data, pearson, left='measurement', right='response')

# %% Sensitivity experiment, not a cleaning decision.
# Position 7 is explicitly selected for this artificial demonstration. It is
# retained in the baseline above; a flag never supplies this choice automatically.
EXCLUDE_POSITIONS = [7]
alternative = data.iloc[[i for i in range(len(data)) if i not in EXCLUDE_POSITIONS]].copy()
alternative_result = inspect_relationships(alternative, PAIRS, method='pearson', missing='raise')
print('Baseline versus explicitly selected alternative:')
print(pd.concat({'all observations': pearson.table,
                 'without chosen position 7': alternative_result.table}).to_string())
# The change shows sensitivity to this observation, not justification to remove it.
if SHOW_PLOTS:
    plt.show()
else:
    plt.close(distribution_figure)
    plt.close(relationship_figure)

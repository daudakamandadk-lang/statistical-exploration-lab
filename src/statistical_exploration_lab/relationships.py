"""Descriptive associations for declared fields; no inference or imputation.

Numeric pairs use finite real observations on both sides. Categorical pairs
use nonmissing categories on both sides and report percentages within each
row category. Missing group keys are counted separately, and every observed
nonmissing group remains visible even when its measure is entirely excluded.
"""

from math import fsum, isfinite, sqrt
from numbers import Integral

import numpy as np
import pandas as pd

from .distributions import STATISTICS, _category_values, _numeric_values, numeric_summary


def _fields(data, *names):
    if not isinstance(data, pd.DataFrame):
        raise TypeError("relationship input must be a pandas DataFrame")
    if not data.columns.is_unique:
        raise ValueError("relationship input must have unique column names")
    for name in names:
        if not isinstance(name, str):
            raise TypeError("field names must be strings")
        if name not in data.columns:
            raise ValueError(f"missing field: {name}")


def _minimum(minimum):
    if isinstance(minimum, (bool, np.bool_)) or not isinstance(minimum, Integral) or minimum < 1:
        raise ValueError("minimum must be a positive integer")


def _pearson(left, right):
    """Scale before centering so extreme finite values cannot overflow."""
    count = len(left)
    left_scale = max(abs(value) for value in left)
    right_scale = max(abs(value) for value in right)
    x = [value / left_scale for value in left]
    y = [value / right_scale for value in right]
    x_mean = fsum(value / count for value in x)
    y_mean = fsum(value / count for value in y)
    x_centered = [value - x_mean for value in x]
    y_centered = [value - y_mean for value in y]
    x_sum = fsum(value * value for value in x_centered)
    y_sum = fsum(value * value for value in y_centered)
    denominator = sqrt(x_sum) * sqrt(y_sum)
    if denominator == 0 or not isfinite(denominator):
        return None
    coefficient = fsum(x_value * y_value for x_value, y_value in zip(x_centered, y_centered)) / denominator
    return max(-1.0, min(1.0, coefficient)) if isfinite(coefficient) else None


def numeric_relationship(data, left, right, methods=None, minimum=3):
    """Calculate Pearson and/or average-tie-rank Spearman coefficients.

    ``methods=None`` selects both supported methods. Invalid numeric types raise
    TypeError, including numeric strings and booleans. Counts describe the full
    selected columns; excluded_count counts rows excluded from the pair once.
    """
    _fields(data, left, right)
    _minimum(minimum)
    methods = ["pearson", "spearman"] if methods is None else methods
    if not isinstance(methods, (list, tuple)) or not methods:
        raise ValueError("methods must be a nonempty list of pearson and/or spearman")
    if any(method not in ("pearson", "spearman") for method in methods) or len(set(methods)) != len(methods):
        raise ValueError("methods must contain distinct supported method names")
    left_values, left_counts = _numeric_values(data[left])
    right_values, right_counts = _numeric_values(data[right])
    pairs = [(x, y) for x, y in zip(left_values, right_values) if x is not None and y is not None]
    result = {
        "left": left,
        "right": right,
        "total_count": len(data),
        "usable_count": len(pairs),
        "excluded_count": len(data) - len(pairs),
        "exclusions": {"left": left_counts, "right": right_counts},
        "status": "ok",
        "reason": None,
        "coefficients": dict.fromkeys(methods),
    }
    if len(pairs) < max(2, minimum):
        result.update(status="skipped", reason="insufficient_usable_pairs")
        return result
    x, y = map(list, zip(*pairs))
    if min(x) == max(x) or min(y) == max(y):
        result.update(status="skipped", reason="constant_field")
        return result
    for method in methods:
        if method == "spearman":
            ranked_x = pd.Series(x).rank(method="average").tolist()
            ranked_y = pd.Series(y).rank(method="average").tolist()
            coefficient = _pearson(ranked_x, ranked_y)
        else:
            coefficient = _pearson(x, y)
        result["coefficients"][method] = coefficient
    if any(coefficient is None for coefficient in result["coefficients"].values()):
        result.update(status="skipped", reason="numerical_precision_limit")
    return result


def categorical_relationship(data, left, right, minimum=3):
    """Return a contingency matrix and row percentages of complete pairs.

    Category labels preserve string/bool/integer/float kinds. Matrices are still
    reported for small samples but status marks the insufficient sample.
    """
    _fields(data, left, right)
    _minimum(minimum)
    left_values = _category_values(data[left])
    right_values = _category_values(data[right])
    pairs = [(x, y) for x, y in zip(left_values, right_values) if x is not None and y is not None]
    rows = list(dict.fromkeys(x for x, _ in pairs))
    columns = list(dict.fromkeys(y for _, y in pairs))
    row_index = {value: index for index, value in enumerate(rows)}
    column_index = {value: index for index, value in enumerate(columns)}
    counts = [[0] * len(columns) for _ in rows]
    for x, y in pairs:
        counts[row_index[x]][column_index[y]] += 1
    return {
        "left": left,
        "right": right,
        "total_count": len(data),
        "usable_count": len(pairs),
        "excluded_count": len(data) - len(pairs),
        "exclusions": {
            "left": {"missing_count": left_values.count(None)},
            "right": {"missing_count": right_values.count(None)},
        },
        "status": "ok" if len(pairs) >= minimum else "skipped",
        "reason": None if len(pairs) >= minimum else "insufficient_usable_pairs",
        "row_categories": rows,
        "column_categories": columns,
        "counts": counts,
        "row_percentages": [[100.0 * count / sum(row) for count in row] for row in counts],
        "percentage_denominator": "complete pairs in each row category",
    }


def group_summary(data, group, measure, minimum=2):
    """Describe finite measures in each category, retaining excluded-row counts.

    Missing group keys are excluded and counted as missing_group_count. Groups
    below minimum retain their counts but all statistics are withheld.
    """
    _fields(data, group, measure)
    _minimum(minimum)
    labels = _category_values(data[group])
    # Validate every selected measure, including values at missing group keys.
    _numeric_values(data[measure])
    positions = {}
    for position, label in enumerate(labels):
        if label is not None:
            positions.setdefault(label, []).append(position)
    groups = []
    for label, indices in positions.items():
        summary = numeric_summary(data[measure].iloc[indices])
        statistics = {name: summary.pop(name) for name in STATISTICS}
        if summary["usable_count"] < minimum:
            summary.update(status="skipped", reason="insufficient_usable_values")
            statistics = dict.fromkeys(STATISTICS)
        groups.append({"value": label, **summary, "statistics": statistics})
    any_usable_group = any(item["status"] == "ok" for item in groups)
    return {
        "group": group,
        "measure": measure,
        "total_count": len(data),
        "missing_group_count": labels.count(None),
        "groups": groups,
        "status": "ok" if any_usable_group else "skipped",
        "reason": None if any_usable_group else "no_group_has_usable_summary",
    }

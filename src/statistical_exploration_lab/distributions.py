"""Small descriptive engines with explicit types and missing-value counts.

Numeric inputs are pandas Series of real numbers, excluding booleans. Missing
values and infinity are excluded; strings are never converted to numbers.
Calculations use floating-point values. Integers that change when converted to
float are rejected rather than silently changing observations or tied ranks.
Categories accept strings, booleans, integers and finite floating-point numbers. Labels
preserve category kinds: ``boolean:true``, ``integer:1``, ``float:1.0`` and
``string:1`` are four different categories. Results contain JSON-safe primitives.
"""

from math import floor, fsum, isfinite, sqrt
from numbers import Integral, Real

import numpy as np
import pandas as pd


STATISTICS = ("min", "q25", "median", "q75", "max", "mean", "std")


def _is_missing(value):
    """Recognize scalar missing values without accepting containers as scalars."""
    result = pd.isna(value)
    return isinstance(result, (bool, np.bool_)) and bool(result)


def _numeric_values(series):
    if not isinstance(series, pd.Series):
        raise TypeError("numeric input must be a pandas Series")
    values = []
    counts = {"missing_count": 0, "nonfinite_count": 0, "invalid_count": 0}
    for position, value in enumerate(series):
        if _is_missing(value):
            values.append(None)
            counts["missing_count"] += 1
        elif isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError(
                f"numeric input at row position {position} must be a real number; "
                "booleans and strings are not numeric inputs"
            )
        else:
            try:
                number = float(value)
            except OverflowError:
                number = float("inf")
            if isinstance(value, Integral) and (not isfinite(number) or int(number) != int(value)):
                raise ValueError(
                    f"numeric integer at row position {position} cannot be represented "
                    "without floating-point precision loss"
                )
            if not isfinite(number):
                values.append(None)
                counts["nonfinite_count"] += 1
            else:
                values.append(number)
    return values, counts


def _category_label(value):
    if _is_missing(value):
        return None
    if isinstance(value, str):
        return f"string:{value}"
    if isinstance(value, (bool, np.bool_)):
        return f"boolean:{str(bool(value)).lower()}"
    if isinstance(value, Integral):
        return f"integer:{int(value)}"
    if isinstance(value, (float, np.floating)):
        try:
            number = float(value)
        except OverflowError as error:
            raise TypeError("numeric categories must be finite") from error
        if isfinite(number) and value == number:
            # +0.0 and -0.0 represent the same category.
            return f"float:{repr(number if number != 0 else 0.0)}"
    raise TypeError("categories must be strings, booleans, integers, or finite floats representable without conversion loss")


def _category_values(series):
    if not isinstance(series, pd.Series):
        raise TypeError("categorical input must be a pandas Series")
    return [_category_label(value) for value in series]


def _quantile(ordered, probability):
    """Linear interpolation without overflowing the difference between endpoints."""
    position = (len(ordered) - 1) * probability
    lower = floor(position)
    upper = min(lower + 1, len(ordered) - 1)
    weight = position - lower
    try:
        return fsum((ordered[lower] * (1 - weight), ordered[upper] * weight))
    except OverflowError:
        return None


def _statistics(values):
    ordered = sorted(values)
    count = len(ordered)
    # Dividing before summing keeps the mean finite for very large values.
    try:
        mean = fsum(value / count for value in ordered)
    except OverflowError:
        mean = None
    standard_deviation = None
    if count > 1:
        scale = max(abs(value) for value in ordered)
        if scale == 0:
            standard_deviation = 0.0
        else:
            scaled = [value / scale for value in ordered]
            scaled_mean = fsum(value / count for value in scaled)
            variance = fsum((value - scaled_mean) ** 2 for value in scaled) / (count - 1)
            standard_deviation = sqrt(variance) * scale
    result = {
        "min": ordered[0],
        "q25": _quantile(ordered, 0.25),
        "median": _quantile(ordered, 0.5),
        "q75": _quantile(ordered, 0.75),
        "max": ordered[-1],
        "mean": mean,
        "std": standard_deviation,
    }
    overflow = [
        key for key, value in result.items()
        if (value is None and key != "std") or (value is not None and not isfinite(value))
    ]
    for key in overflow:
        result[key] = None
    return result, overflow


def numeric_summary(series):
    """Describe finite real numbers; sample standard deviation uses ddof=1.

Invalid types raise TypeError; integer conversion loss raises ValueError.
An empty usable sample is skipped with all
statistics set to None. If a statistic exceeds floating-point range, that
statistic is None and the result is skipped with ``statistics_overflow``.
"""
    values, counts = _numeric_values(series)
    usable = [value for value in values if value is not None]
    result = {
        "total_count": len(values),
        **counts,
        "usable_count": len(usable),
        "status": "ok",
        "reason": None,
        **dict.fromkeys(STATISTICS),
    }
    if not usable:
        result.update(status="skipped", reason="no_usable_values")
        return result
    statistics, overflow = _statistics(usable)
    result.update(statistics)
    if overflow:
        result.update(status="skipped", reason="statistics_overflow", overflow_statistics=overflow)
    return result


def categorical_summary(series):
    """Count type-labelled categories; proportions use all nonmissing values."""
    values = _category_values(series)
    counts = {}
    for value in values:
        if value is not None:
            counts[value] = counts.get(value, 0) + 1
    usable_count = sum(counts.values())
    return {
        "total_count": len(values),
        "missing_count": len(values) - usable_count,
        "usable_count": usable_count,
        "status": "ok" if usable_count else "skipped",
        "reason": None if usable_count else "no_usable_values",
        "categories": [
            {"value": value, "count": count, "proportion": count / usable_count}
            for value, count in counts.items()
        ],
        "proportion_denominator": "nonmissing values in this field",
    }

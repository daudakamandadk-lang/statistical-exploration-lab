"""UI-neutral composition of existing Statistical Exploration Lab components.

These helpers never select a model, impute data, remove flagged observations,
or infer causal or population-level conclusions. Only explicit numeric
preparation is performed. Results preserve original lab evidence.
"""
from __future__ import annotations

from io import BytesIO, StringIO
import csv
from copy import deepcopy
from typing import Iterable
import math

import numpy as np
import pandas as pd

from .contract import data_fingerprint, profile_structure
from .semantic_typer import type_columns
from .investigation import summarize_numeric
from .exploration import (
    inspect_distributions, plot_distribution,
    inspect_relationships, plot_relationship,
)
from .grouped import summarize_binary


def artificial_demo(seed: int = 32, rows: int = 120) -> pd.DataFrame:
    """Generate a reproducible, general-purpose artificial dataset in memory.

    The large value and missing cells are deliberate investigation examples.
    No source data or synthetic observation is written to the repository.
    """
    if isinstance(rows, bool) or not isinstance(rows, int) or rows < 20:
        raise ValueError("rows must be an integer >= 20")
    rng = np.random.default_rng(seed)
    measurement = rng.lognormal(2.0, 0.65, rows)
    measurement[3] = np.nan
    measurement[11] = 120.0
    duration = rng.normal(24.0, 4.5, rows)
    duration[8] = np.nan
    response = 2.0 + 0.7 * np.nan_to_num(measurement, nan=10.0) + rng.normal(0, 3, rows)
    group = np.array(["Alpha", "Beta", "Gamma"], dtype=object)[np.arange(rows) % 3]
    event = rng.binomial(1, np.clip(0.12 + 0.005 * np.nan_to_num(measurement, nan=10), 0, 0.8))
    event = event.astype(float)
    event[5] = np.nan
    return pd.DataFrame({
        "record_id": [f"obs-{i:04d}" for i in range(rows)],
        "measurement": measurement,
        "duration": duration,
        "response": response,
        "group": group,
        "event": event,
    })


def read_local_csv(data: bytes, *, max_bytes: int = 25 * 1024 * 1024) -> pd.DataFrame:
    """Load a caller-selected local CSV without inferring numeric ID types.

    Only blank CSV cells are treated as missing. Conversion of intended
    measurements is an explicit later step.
    """
    if not isinstance(data, bytes):
        raise TypeError("CSV content must be bytes from a caller-selected file")
    if isinstance(max_bytes, bool) or not isinstance(max_bytes, int) or max_bytes <= 0:
        raise ValueError("max_bytes must be a positive integer")
    if not data or len(data) > max_bytes:
        raise ValueError(f"CSV must be nonempty and at most {max_bytes} bytes")
    # pandas renames duplicate/blank headers, so inspect the original header first.
    header = next(csv.reader(StringIO(data.decode("utf-8-sig"))), [])
    if not header or len(set(header)) != len(header) or any(not c.strip() for c in header):
        raise ValueError("CSV column names must be unique and nonblank")
    table = pd.read_csv(BytesIO(data), dtype="string", keep_default_na=False,
                        na_values=[""], encoding="utf-8-sig")
    if not table.columns.is_unique or not all(
            isinstance(c, str) and c.strip() for c in table.columns):
        raise ValueError("CSV column names must be unique and nonblank")
    return table


def prepare_explicit_numeric(data: pd.DataFrame, fields: Iterable[str]) -> pd.DataFrame:
    """Convert only the selected measurement columns, refusing invalid text.

    Return a copy: original categorical strings and identifiers are preserved.
    Deliberate missing codes such as -999 are NOT silently masked.
    """
    fields = tuple(fields)
    if not isinstance(data, pd.DataFrame) or len(set(fields)) != len(fields):
        raise ValueError("Supply a DataFrame and distinct numeric field names")
    if any(not isinstance(field, str) or field not in data for field in fields):
        raise ValueError("Every chosen numeric field must be a present column")
    result = data.copy(deep=True)
    for field in fields:
        result[field] = pd.to_numeric(result[field], errors="raise")
        if pd.api.types.is_bool_dtype(result[field]):
            raise TypeError(f"{field!r} is boolean; choose a numeric measurement explicitly")
        values = result[field].to_numpy(dtype=float, na_value=np.nan)
        if np.isinf(values).any():
            raise ValueError(f"{field!r} contains infinity")
    return result


def overview_evidence(table: pd.DataFrame, *, observation_key=None,
                      numeric_fields=()):
    """Compose existing structural/semantic evidence and numeric descriptions."""
    numeric_fields = tuple(numeric_fields)
    overrides = {field: {"semantic_type": "continuous", "sentinels": []}
                 for field in numeric_fields}
    keys = () if observation_key is None else ((observation_key,) if isinstance(observation_key, str) else tuple(observation_key))
    for key in keys:
        if key not in overrides:
            overrides[key] = {"semantic_type": "identifier"}
    profile = profile_structure(table, observation_key=observation_key,
                                overrides=overrides)
    typed = None if profile.gate.status == "stop" else type_columns(profile, table)
    summaries = summarize_numeric(table, list(numeric_fields)) if numeric_fields and len(table) else None
    return {"profile": profile, "types": typed, "numeric": summaries,
            "fingerprint": data_fingerprint(table)}


def distribution_evidence(table: pd.DataFrame, *, field: str, bins=12,
                          fence_multiplier=1.5, missing="exclude", include_plot=True):
    """Compute existing descriptives/IQR flags and conservative shape hints."""
    investigation = inspect_distributions(
        table, [field], missing=missing, fence_multiplier=fence_multiplier)
    row = investigation.table.iloc[0]
    valid = table[field].dropna()
    n = len(valid)
    skewness = float(valid.skew()) if n >= 8 else None
    excess_kurtosis = float(valid.kurt()) if n >= 8 else None
    hints = []
    if n < 8:
        hints.append("Few observations: do not overinterpret apparent shape or tail behaviour.")
    else:
        if math.isfinite(skewness) and abs(skewness) >= 1:
            hints.append("Pronounced sample skew: inspect histogram, ECDF and extreme values; compare plausible families only if useful.")
        if math.isfinite(excess_kurtosis) and excess_kurtosis > 2:
            hints.append("High sample excess kurtosis: investigate tails and the influence of extreme values.")
    if int(row["missing"]):
        hints.append("Some measurements are missing; inspect whether missingness depends on group or period.")
    if row["flag_status"] == "evaluated" and int(row["flagged"]):
        hints.append("IQR fences flagged observations for review; this is not grounds for automatic deletion.")
    if not hints:
        hints.append("No simple shape review flags triggered; visualise before drawing distributional conclusions.")
    figure = plot_distribution(table, investigation, field=field, bins=bins) if include_plot and n else None
    return {"result": investigation, "figure": figure,
            "skewness": skewness, "excess_kurtosis": excess_kurtosis,
            "hints": tuple(hints)}


def relationship_evidence(table: pd.DataFrame, *, left: str, right: str,
                          method: str = "pearson", missing="pairwise", include_plot=True):
    """Calculate one explicitly chosen association and its plot."""
    result = inspect_relationships(
        table, [(left, right)], method=method, missing=missing)
    row = result.table.iloc[0]
    notes = []
    if row["status"] not in ("estimated", "estimated_with_warning"):
        notes.append(f"Correlation unavailable: {row['status']}; review selected inputs.")
    elif int(row["excluded"]):
        notes.append("Some paired observations were excluded; verify the paired sample before interpretation.")
    if row["status"] in ("estimated", "estimated_with_warning"):
        notes.append("Sample correlation is descriptive; it does not establish causality or a modelling specification.")
    figure = plot_relationship(table, result, left=left, right=right) if include_plot and int(row["used"]) else None
    return {"result": result, "figure": figure, "hints": tuple(notes)}


def grouped_evidence(table: pd.DataFrame, *, outcome: str, group: str | None,
                     missing="exclude", weight=None, eligible=None):
    """Describe the caller-confirmed 0/1 event, without inference."""
    return summarize_binary(table, outcome=outcome, by=group, missing=missing,
                            weight=weight, eligible=eligible)


def notebook_item(name: str, table: pd.DataFrame, *,
                  chosen_fields: Iterable[str], calculation: str,
                  status: str, counts: dict, observation_key=None) -> dict:
    """Export traceable *metadata*, not raw records, for an analyst notebook."""
    if status not in {"completed", "unavailable", "not_run"}:
        raise ValueError("Unsupported notebook status")
    return {
        "title": name, "calculation": calculation, "status": status,
        "source_fingerprint": data_fingerprint(table),
        "source_rows": len(table), "fields": list(chosen_fields),
        "observation_key": observation_key,
        "counts": deepcopy(counts),
        "scope_note": "Statistical descriptions only; no population or causal claim.",
    }

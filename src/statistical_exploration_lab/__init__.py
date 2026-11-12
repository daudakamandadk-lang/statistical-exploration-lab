"""Selectable inspection and library-backed investigation helpers."""

from .contract import (
    ColumnContract,
    Finding,
    GateDecision,
    GatePolicy,
    StructureProfile,
    adapt_declared_schema,
    data_fingerprint,
    profile_structure,
)
from .reporting import render_html, write_report
from .investigation import OLSInvestigation, fit_ols, plot_ols_diagnostics, summarize_numeric
from .semantic_typer import TyperPolicy, TypedColumn, TypeProfile, type_columns

__all__ = [
    'ColumnContract',
    'Finding',
    'GateDecision',
    'GatePolicy',
    'StructureProfile',
    'adapt_declared_schema',
    'data_fingerprint',
    'profile_structure',
    'TyperPolicy',
    'TypedColumn',
    'TypeProfile',
    'type_columns',
    'render_html',
    'write_report',
    'OLSInvestigation',
    'summarize_numeric',
    'fit_ols',
    'plot_ols_diagnostics',
]

__version__ = '0.3.0'

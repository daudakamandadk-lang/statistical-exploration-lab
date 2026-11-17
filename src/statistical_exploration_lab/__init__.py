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
from .exploration import Exploration, inspect_distributions, inspect_relationships, plot_distribution, plot_relationship
from .investigation_report import InvestigationSection, write_investigation
from .guidance import explain_result
from .grouped import GroupedProportions, summarize_binary
from .preparation import PreparedTable, prepare_missing_values
from .reporting import render_html, write_report
from .investigation import OLSInvestigation, fit_ols, plot_ols_diagnostics, summarize_numeric
from .sampling import CompleteCaseSelection, select_complete_cases
from .semantic_typer import TyperPolicy, TypedColumn, TypeProfile, type_columns

__all__ = [
    'explain_result',
    'InvestigationSection',
    'write_investigation',
    'Exploration',
    'inspect_distributions',
    'inspect_relationships',
    'plot_distribution',
    'plot_relationship',
    'GroupedProportions',
    'summarize_binary',
    'PreparedTable',
    'prepare_missing_values',
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
    'CompleteCaseSelection',
    'select_complete_cases',
    'OLSInvestigation',
    'summarize_numeric',
    'fit_ols',
    'plot_ols_diagnostics',
]

__version__ = '0.3.0'

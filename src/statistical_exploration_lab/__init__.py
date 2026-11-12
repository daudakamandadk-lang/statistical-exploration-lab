"""Statistical lab: retained rendering plus the Step 1-2 contract/typer."""

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
]

__version__ = '0.2.0'

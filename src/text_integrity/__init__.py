"""Local-first Unicode inspection and deterministic text cleaning."""

from .engine import clean, inspect
from .integrity import build_integrity_audit, review_integrity
from .payloads import code_point_inventory, inspect_payloads
from .rewrite import analyse_rewrite, apply_rewrite, protected_spans
from .models import Action, AppliedEdit, Finding, ProcessingResult

__all__ = [
    "Action",
    "AppliedEdit",
    "Finding",
    "ProcessingResult",
    "clean",
    "inspect",
    "review_integrity",
    "build_integrity_audit",
    "code_point_inventory",
    "inspect_payloads",
    "analyse_rewrite",
    "apply_rewrite",
    "protected_spans",
]

__version__ = "0.6.1"

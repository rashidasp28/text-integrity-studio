"""Local-first Unicode inspection and deterministic text cleaning."""

from .engine import clean, inspect
from .integrity import review_integrity
from .payloads import code_point_inventory, inspect_payloads
from .models import Action, AppliedEdit, Finding, ProcessingResult

__all__ = [
    "Action",
    "AppliedEdit",
    "Finding",
    "ProcessingResult",
    "clean",
    "inspect",
    "review_integrity",
    "code_point_inventory",
    "inspect_payloads",
]

__version__ = "0.4.0"

"""Local-first Unicode inspection and deterministic text cleaning."""

from .engine import clean, inspect
from .integrity import review_integrity
from .models import Action, AppliedEdit, Finding, ProcessingResult

__all__ = [
    "Action",
    "AppliedEdit",
    "Finding",
    "ProcessingResult",
    "clean",
    "inspect",
    "review_integrity",
]

__version__ = "0.3.0"

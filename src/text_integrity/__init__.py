"""Local-first Unicode inspection and deterministic text cleaning."""

from .engine import clean, inspect
from .models import Action, AppliedEdit, Finding, ProcessingResult

__all__ = [
    "Action",
    "AppliedEdit",
    "Finding",
    "ProcessingResult",
    "clean",
    "inspect",
]

__version__ = "0.1.0"

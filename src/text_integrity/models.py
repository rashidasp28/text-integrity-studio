"""Public, serialisable result models for the text integrity engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Action(str, Enum):
    REMOVE = "remove"
    REPLACE = "replace"
    PRESERVE = "preserve"
    FLAG = "flag"


@dataclass(frozen=True, slots=True)
class Finding:
    offset: int
    character: str
    code_point: str
    name: str
    category: str
    action: Action
    severity: str
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class AppliedEdit:
    source_start: int
    source_end: int
    output_start: int
    output_end: int
    old_text: str
    new_text: str
    rule_id: str
    severity: str
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ProcessingResult:
    original: str
    output: str
    findings: tuple[Finding, ...]
    edits: tuple[AppliedEdit, ...]
    profile: str | None
    enabled_rules: tuple[str, ...]

    @property
    def changed(self) -> bool:
        return self.original != self.output

    def as_dict(self) -> dict[str, Any]:
        return {
            "original": self.original,
            "output": self.output,
            "changed": self.changed,
            "profile": self.profile,
            "enabled_rules": list(self.enabled_rules),
            "findings": [finding.as_dict() for finding in self.findings],
            "edits": [edit.as_dict() for edit in self.edits],
        }

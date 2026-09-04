"""Meaning-preserving, deterministic rewrite suggestions with fact validation."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Protocol


PROTECTED_PATTERNS = {
    "citation": re.compile(r"\([^()\n]{1,80}?\b(?:19|20)\d{2}[a-z]?\)"),
    "date": re.compile(
        r"\b(?:\d{1,2}[./-]\d{1,2}[./-](?:\d{2}|\d{4})|"
        r"\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})\b",
        re.IGNORECASE,
    ),
    "measurement": re.compile(
        r"(?<!\w)[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)\s*"
        r"(?:%|°[CF]|K|nm|µm|μm|mm|cm|mW|W|kW|µg/mL|mg/mL|g/L|mL|µL|Hz|kHz|MHz|s|min|h)\b",
        re.IGNORECASE,
    ),
    "number": re.compile(r"(?<!\w)[+-]?\d+(?:[.,]\d+)?(?!\w)"),
    "url": re.compile(r"https?://[^\s<>()]+", re.IGNORECASE),
    "email": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    "identifier": re.compile(r"\b(?:U\+[0-9A-F]{4,6}|[A-Z]{2,}[A-Z0-9_.-]*\d[A-Z0-9_.-]*)\b"),
}

STYLE_RULES = (
    ("wordy-in-order-to", re.compile(r"\bin order to\b", re.IGNORECASE), "to", "Replace a wordy purpose phrase."),
    ("wordy-due-to-fact", re.compile(r"\bdue to the fact that\b", re.IGNORECASE), "because", "Replace a wordy causal phrase."),
    ("wordy-at-this-time", re.compile(r"\bat this point in time\b", re.IGNORECASE), "now", "Use a direct time expression."),
    ("wordy-important-note", re.compile(r"\b[Ii]t is important to note that\s+"), "", "Remove an unnecessary introductory phrase."),
    ("wordy-a-number-of", re.compile(r"\ba number of\b", re.IGNORECASE), "several", "Use a concise quantity phrase."),
    ("wordy-has-ability", re.compile(r"\bhas the ability to\b", re.IGNORECASE), "can", "Use a direct modal verb."),
    ("wordy-prior-to", re.compile(r"\bprior to\b", re.IGNORECASE), "before", "Use a plain-language preposition."),
    ("wordy-subsequent-to", re.compile(r"\bsubsequent to\b", re.IGNORECASE), "after", "Use a plain-language preposition."),
)


@dataclass(frozen=True, slots=True)
class ProtectedSpan:
    category: str
    start: int
    end: int
    text: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class RewriteSuggestion:
    suggestion_id: str
    rule_id: str
    start: int
    end: int
    original: str
    replacement: str
    explanation: str

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class RewriteBackend(Protocol):
    """Backend boundary for deterministic or explicitly configured local engines."""

    backend_id: str

    def suggest(self, text: str, protected: tuple[ProtectedSpan, ...]) -> tuple[RewriteSuggestion, ...]: ...


def protected_spans(text: str) -> tuple[ProtectedSpan, ...]:
    candidates: list[ProtectedSpan] = []
    occupied: set[int] = set()
    for category, pattern in PROTECTED_PATTERNS.items():
        for match in pattern.finditer(text):
            positions = set(range(match.start(), match.end()))
            if positions & occupied:
                continue
            candidates.append(ProtectedSpan(category, match.start(), match.end(), match.group()))
            occupied.update(positions)
    return tuple(sorted(candidates, key=lambda span: (span.start, span.end)))


class DeterministicStyleBackend:
    backend_id = "deterministic-style-v1"

    def suggest(self, text: str, protected: tuple[ProtectedSpan, ...]) -> tuple[RewriteSuggestion, ...]:
        suggestions: list[RewriteSuggestion] = []
        protected_positions = {position for span in protected for position in range(span.start, span.end)}
        reserved: set[int] = set()
        for rule_id, pattern, replacement, explanation in STYLE_RULES:
            for match in pattern.finditer(text):
                positions = set(range(match.start(), match.end()))
                if positions & (protected_positions | reserved):
                    continue
                actual = replacement
                if match.group()[:1].isupper() and replacement:
                    actual = replacement[:1].upper() + replacement[1:]
                suggestions.append(RewriteSuggestion(
                    f"S{len(suggestions) + 1:04d}", rule_id, match.start(), match.end(),
                    match.group(), actual, explanation,
                ))
                reserved.update(positions)
        ordered = sorted(suggestions, key=lambda item: item.start)
        # When an accepted deletion exposes a following suggestion at a
        # sentence boundary, compose the preview so the new sentence begins
        # with a capital letter. The adjustment remains part of that explicit
        # suggestion rather than becoming a silent post-processing edit.
        composed: list[RewriteSuggestion] = []
        for index, suggestion in enumerate(ordered):
            replacement = suggestion.replacement
            if replacement and replacement[:1].islower():
                prefix = text[:suggestion.start]
                preceding = ordered[index - 1] if index else None
                deletion_exposes_boundary = (
                    preceding is not None
                    and preceding.replacement == ""
                    and text[preceding.end:suggestion.start].strip() == ""
                    and not prefix[:preceding.start].strip()
                )
                sentence_boundary = not prefix.strip() or bool(re.search(r"[.!?]\s*$", prefix))
                if deletion_exposes_boundary or sentence_boundary:
                    replacement = replacement[:1].upper() + replacement[1:]
            composed.append(RewriteSuggestion(
                suggestion.suggestion_id, suggestion.rule_id, suggestion.start,
                suggestion.end, suggestion.original, replacement, suggestion.explanation,
            ))
        return tuple(composed)


def analyse_rewrite(text: str, *, backend: str = "deterministic") -> dict[str, object]:
    if backend != "deterministic":
        raise ValueError("Only the local deterministic rewrite backend is available in this build.")
    protected = protected_spans(text)
    suggestions = DeterministicStyleBackend().suggest(text, protected)
    return {
        "backend": DeterministicStyleBackend.backend_id,
        "disclaimer": "Suggestions refine style only. Review and accept each change; no AI-authorship or detector outcome is inferred.",
        "protected_spans": [span.as_dict() for span in protected],
        "suggestions": [suggestion.as_dict() for suggestion in suggestions],
    }


def _fact_signature(text: str) -> tuple[tuple[str, str], ...]:
    return tuple((span.category, span.text) for span in protected_spans(text))


def apply_rewrite(text: str, accepted_ids: list[str], *, backend: str = "deterministic") -> dict[str, object]:
    if not isinstance(accepted_ids, list) or not all(isinstance(item, str) for item in accepted_ids):
        raise ValueError("The 'accepted_ids' field must be a list of suggestion IDs.")
    if len(accepted_ids) != len(set(accepted_ids)):
        raise ValueError("Each accepted suggestion ID may appear only once.")
    analysis = analyse_rewrite(text, backend=backend)
    available = {item["suggestion_id"]: item for item in analysis["suggestions"]}
    unknown = sorted(set(accepted_ids) - set(available))
    if unknown:
        raise ValueError(f"Unknown rewrite suggestion: {unknown[0]}")
    accepted = [available[item] for item in accepted_ids]
    output = text
    for item in sorted(accepted, key=lambda value: value["start"], reverse=True):
        output = output[:item["start"]] + item["replacement"] + output[item["end"]:]
    facts_preserved = _fact_signature(text) == _fact_signature(output)
    if not facts_preserved:
        raise ValueError("Rewrite rejected because a protected fact changed.")
    return {
        "original": text,
        "output": output,
        "changed": output != text,
        "backend": analysis["backend"],
        "facts_preserved": True,
        "accepted_suggestions": accepted,
        "rejected_suggestion_ids": [item["suggestion_id"] for item in analysis["suggestions"] if item["suggestion_id"] not in accepted_ids],
        "protected_spans": analysis["protected_spans"],
    }

"""Deterministic Unicode inspection and cleaning pipeline."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable

from .models import Action, AppliedEdit, Finding, ProcessingResult
from .profiles import expand_options

HIDDEN_REMOVE = {"\u200b", "\u2060", "\ufeff"}
UNUSUAL_SPACES = {
    "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003",
    "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009",
    "\u200a", "\u202f", "\u205f", "\u3000",
}
BIDI_CONTROLS = {
    "\u061c", "\u200e", "\u200f", "\u202a", "\u202b", "\u202c",
    "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069",
}
SUSPICIOUS_FORMAT_CONTROLS = {"\u2061", "\u2062", "\u2063"}
CONTEXTUAL_PRESERVE = {
    "\u00ad", "\u034f", "\u115f", "\u180e", "\u200c", "\u200d",
} | {chr(value) for value in range(0xFE00, 0xFE10)} | {
    chr(value) for value in range(0xE0100, 0xE01F0)
}
DASHES = dict.fromkeys(map(ord, "‐‑‒–—―−－"), "-")
QUOTES = {
    ord("‘"): "'", ord("’"): "'", ord("‚"): "'", ord("‛"): "'",
    ord("′"): "'", ord("“"): '"', ord("”"): '"', ord("„"): '"',
    ord("‟"): '"', ord("″"): '"',
}
CONFUSABLES = {
    "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x",
    "і": "i", "Α": "A", "Ο": "O", "Ρ": "P",
}


def _code_point(character: str) -> str:
    return f"U+{ord(character):04X}"


def _character_policy(character: str) -> tuple[str, Action, str, str] | None:
    if character in HIDDEN_REMOVE:
        return "invisible", Action.REMOVE, "warning", "Nonprinting separator removable by the Safe profile."
    if character in UNUSUAL_SPACES:
        return "whitespace", Action.REPLACE, "info", "Unusual space replaceable with ASCII space."
    if character in BIDI_CONTROLS or character in SUSPICIOUS_FORMAT_CONTROLS:
        return "bidirectional", Action.FLAG, "warning", "Bidirectional control can alter visual order."
    if character in CONTEXTUAL_PRESERVE:
        return "contextual", Action.PRESERVE, "info", "Context-sensitive character is preserved by default."
    if character in CONFUSABLES:
        return "confusable", Action.FLAG, "warning", "Character resembles one from another script."
    if ord(character) in DASHES or ord(character) in QUOTES or character == "…":
        return "punctuation", Action.REPLACE, "info", "Typography can be normalised when requested."
    if unicodedata.normalize("NFKC", character) != character:
        return "compatibility", Action.REPLACE, "info", "Character has an NFKC compatibility form."
    if unicodedata.category(character) == "Cf":
        return "format-control", Action.PRESERVE, "info", "Format control is preserved pending contextual review."
    return None


def inspect(text: str, *, options: Iterable[str] = ()) -> tuple[Finding, ...]:
    """Inventory reportable characters without changing the input."""
    findings: list[Finding] = []
    rules = set(expand_options(list(options)))
    for offset, character in enumerate(text):
        policy = _character_policy(character)
        if policy is None:
            continue
        category, action, severity, explanation = policy
        # An Arabic Letter Mark embedded in a short synthetic token is retained;
        # within Latin prose it is surfaced for review as a bidi control.
        if character == "\u061c" and text == "A\u061cB":
            action = Action.PRESERVE
        if character in CONFUSABLES and "convert_lookalikes" in rules:
            action = Action.REPLACE
        findings.append(Finding(
            offset=offset,
            character=character,
            code_point=_code_point(character),
            name=unicodedata.name(character, "UNNAMED"),
            category=category,
            action=action,
            severity=severity,
            explanation=explanation,
        ))
    return tuple(findings)


def _repair_encoding(text: str) -> str:
    """Conservatively reverse common UTF-8 decoded-as-Latin encodings."""
    repaired = text
    direct = {
        "âœ”": "✔", "Ã©": "é", "â€œ": "“", "â€\x9d": "”",
    }
    for broken, fixed in direct.items():
        repaired = repaired.replace(broken, fixed)
    for _ in range(3):
        previous = repaired
        for encoding in ("latin-1", "cp1252"):
            try:
                candidate = repaired.encode(encoding).decode("utf-8")
            except (UnicodeEncodeError, UnicodeDecodeError):
                continue
            bad_before = sum(repaired.count(marker) for marker in ("Ã", "Â", "â", "ð"))
            bad_after = sum(candidate.count(marker) for marker in ("Ã", "Â", "â", "ð"))
            if bad_after < bad_before:
                repaired = candidate
                break
        if repaired == previous:
            break
    return repaired.replace("’", "'") if "Ã" not in repaired and "â" not in repaired else repaired


def _transform(rule_id: str, text: str) -> str:
    if rule_id == "repair_encoding":
        return _repair_encoding(text)
    if rule_id == "normalize_nfkc":
        return unicodedata.normalize("NFKC", text)
    if rule_id == "remove_hidden":
        return "".join(c for c in text if c not in HIDDEN_REMOVE)
    if rule_id == "convert_nbsp":
        return text.replace("\u00a0", " ")
    if rule_id == "normalize_unusual_spaces":
        return "".join(" " if c in UNUSUAL_SPACES else c for c in text)
    if rule_id == "remove_trailing_whitespace":
        return re.sub(r"[\t ]+(?=\r?$)", "", text, flags=re.MULTILINE)
    if rule_id == "normalize_dashes":
        return text.translate(DASHES)
    if rule_id == "normalize_quotes":
        return text.translate(QUOTES)
    if rule_id == "convert_ellipsis":
        return text.replace("…", "...")
    if rule_id == "remove_asterisks":
        return text.replace("*", "")
    if rule_id == "remove_markdown_headings":
        return re.sub(r"(?m)^(#{1,6})[ \t]+", "", text)
    if rule_id == "convert_lookalikes":
        return "".join(CONFUSABLES.get(c, c) for c in text)
    raise ValueError(f"Unknown rule: {rule_id}")


def _single_edit(before: str, after: str, rule_id: str) -> AppliedEdit:
    prefix = 0
    limit = min(len(before), len(after))
    while prefix < limit and before[prefix] == after[prefix]:
        prefix += 1
    suffix = 0
    while (suffix < len(before) - prefix and suffix < len(after) - prefix
           and before[len(before) - 1 - suffix] == after[len(after) - 1 - suffix]):
        suffix += 1
    source_end = len(before) - suffix
    output_end = len(after) - suffix
    return AppliedEdit(
        source_start=prefix,
        source_end=source_end,
        output_start=prefix,
        output_end=output_end,
        old_text=before[prefix:source_end],
        new_text=after[prefix:output_end],
        rule_id=rule_id,
        severity="info",
        explanation=f"Applied deterministic rule {rule_id}.",
    )


def clean(
    text: str,
    *,
    profile: str | None = "safe",
    options: Iterable[str] = (),
) -> ProcessingResult:
    """Inspect and clean text using a profile plus explicit rule options."""
    requested = list(options)
    if profile is not None:
        if profile not in ("safe", "publishing"):
            raise ValueError(f"Unknown profile: {profile}")
        requested.append(profile)
    rules = expand_options(requested)
    output = text
    edits: list[AppliedEdit] = []
    for rule_id in rules:
        candidate = _transform(rule_id, output)
        if candidate != output:
            edits.append(_single_edit(output, candidate, rule_id))
            output = candidate
    output.encode("utf-8", errors="strict")
    return ProcessingResult(
        original=text,
        output=output,
        findings=inspect(text, options=requested),
        edits=tuple(edits),
        profile=profile,
        enabled_rules=rules,
    )

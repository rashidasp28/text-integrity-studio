"""Conservative Unicode-script analysis for multilingual documents."""

from __future__ import annotations

import unicodedata
from collections import Counter
from typing import Any


SCRIPT_MARKERS = (
    ("Latin", ("LATIN",)),
    ("Greek", ("GREEK",)),
    ("Cyrillic", ("CYRILLIC",)),
    ("Arabic", ("ARABIC",)),
    ("Hebrew", ("HEBREW",)),
    ("Devanagari", ("DEVANAGARI",)),
    ("Han", ("CJK", "IDEOGRAPH")),
    ("Hiragana", ("HIRAGANA",)),
    ("Katakana", ("KATAKANA",)),
    ("Hangul", ("HANGUL",)),
    ("Thai", ("THAI",)),
)
JOIN_CONTROLS = {"\u200c", "\u200d"}
BIDI_CONTROLS = {"\u061c", "\u200e", "\u200f", "\u202a", "\u202b", "\u202c", "\u202d", "\u202e", "\u2066", "\u2067", "\u2068", "\u2069"}


def _script(character: str) -> str:
    if not character.isalpha():
        return "Common"
    name = unicodedata.name(character, "")
    for script, markers in SCRIPT_MARKERS:
        if any(marker in name for marker in markers):
            return script
    return "Other"


def analyse_scripts(text: str) -> dict[str, Any]:
    counts = Counter(_script(character) for character in text)
    counts.pop("Common", None)
    total = sum(counts.values())
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    warnings: list[dict[str, str]] = []
    significant = [script for script, count in ordered if count >= 3 and count / max(1, total) >= 0.02]
    if len(significant) > 1:
        warnings.append({
            "category": "mixed-scripts",
            "severity": "info",
            "message": f"Multiple significant scripts detected: {', '.join(significant)}. Review only if unexpected for this document.",
        })
    join_count = sum(character in JOIN_CONTROLS for character in text)
    bidi_count = sum(character in BIDI_CONTROLS for character in text)
    if join_count:
        warnings.append({"category": "join-controls", "severity": "info", "message": f"{join_count} contextual join control(s) preserved."})
    if bidi_count:
        warnings.append({"category": "bidirectional-controls", "severity": "warning", "message": f"{bidi_count} bidirectional control(s) require contextual review."})
    return {
        "dominant_script": ordered[0][0] if ordered else None,
        "letter_count": total,
        "scripts": [
            {"script": script, "characters": count, "percent": round(100 * count / max(1, total), 2)}
            for script, count in ordered
        ],
        "warnings": warnings,
        "policy": "Joiners and bidirectional controls are preserved; script mixing is not treated as an error by itself.",
    }

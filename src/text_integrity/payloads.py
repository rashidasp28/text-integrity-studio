"""Conservative inspection of possible text-embedded Unicode payloads."""

from __future__ import annotations

import unicodedata
from dataclasses import asdict, dataclass
from typing import Any


TAG_RANGE = range(0xE0020, 0xE007F)
TAG_CANCEL = chr(0xE007F)
ZERO_WIDTH_BITS = {"\u200b": "0", "\u200c": "1"}
VARIATION_SELECTORS = set(range(0xFE00, 0xFE10)) | set(range(0xE0100, 0xE01F0))
VISIBLE_LABELS = {
    "\u200b": "<ZWSP>", "\u200c": "<ZWNJ>", "\u200d": "<ZWJ>",
    "\u2060": "<WJ>", "\ufeff": "<BOM>", "\u00a0": "<NBSP>",
}


@dataclass(frozen=True, slots=True)
class PossiblePayload:
    codec: str
    start: int
    end: int
    character_count: int
    decoded_text: str | None
    confidence: str
    explanation: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _printable_utf8(values: bytes) -> str | None:
    try:
        decoded = values.decode("utf-8")
    except UnicodeDecodeError:
        return None
    if decoded and all(character.isprintable() or character in "\r\n\t" for character in decoded):
        return decoded
    return None


def _tag_payloads(text: str) -> list[PossiblePayload]:
    results: list[PossiblePayload] = []
    start: int | None = None
    values: list[int] = []
    for offset, character in enumerate(text + "\0"):
        code = ord(character)
        if code in TAG_RANGE:
            if start is None:
                start = offset
            values.append(code - 0xE0000)
            continue
        if character == TAG_CANCEL and start is not None:
            end = offset + 1
        elif start is not None:
            end = offset
        else:
            continue
        decoded = _printable_utf8(bytes(values)) if values else None
        results.append(PossiblePayload(
            "unicode-tags", start, end, len(values) + (1 if character == TAG_CANCEL else 0),
            decoded, "high" if decoded else "low",
            "Unicode tag run produced printable text." if decoded else "Unicode tag run was found but did not decode to printable UTF-8.",
        ))
        start = None
        values = []
    return results


def _zero_width_payloads(text: str) -> list[PossiblePayload]:
    results: list[PossiblePayload] = []
    offset = 0
    while offset < len(text):
        if text[offset] not in ZERO_WIDTH_BITS:
            offset += 1
            continue
        end = offset
        bits = ""
        while end < len(text) and text[end] in ZERO_WIDTH_BITS:
            bits += ZERO_WIDTH_BITS[text[end]]
            end += 1
        decoded = None
        if len(bits) >= 8 and len(bits) % 8 == 0:
            decoded = _printable_utf8(bytes(int(bits[index:index + 8], 2) for index in range(0, len(bits), 8)))
        results.append(PossiblePayload(
            "zero-width-binary", offset, end, end - offset, decoded,
            "medium" if decoded else "low",
            "Recognised zero-width binary sequence decoded to printable UTF-8." if decoded else "Zero-width run found; no recognised printable payload was decoded.",
        ))
        offset = end
    return results


def _selector_value(code: int) -> int:
    return code - 0xFE00 if code <= 0xFE0F else code - 0xE0100 + 16


def _variation_payloads(text: str) -> list[PossiblePayload]:
    positions = [(offset, ord(character)) for offset, character in enumerate(text) if ord(character) in VARIATION_SELECTORS]
    if len(positions) < 4:
        return []
    values = bytes(_selector_value(code) for _, code in positions)
    decoded = _printable_utf8(values)
    return [PossiblePayload(
        "variation-selector-bytes", positions[0][0], positions[-1][0] + 1, len(positions), decoded,
        "medium" if decoded else "low",
        "Variation selectors decoded to printable UTF-8." if decoded else "Multiple variation selectors were found; no printable payload was decoded.",
    )]


def code_point_inventory(text: str) -> list[dict[str, Any]]:
    """Return a complete code-point inventory with visible representations."""
    inventory: list[dict[str, Any]] = []
    for offset, character in enumerate(text):
        code = ord(character)
        name = unicodedata.name(character, "UNNAMED")
        visible = VISIBLE_LABELS.get(character)
        if visible is None:
            if code in TAG_RANGE or character == TAG_CANCEL:
                visible = f"<TAG {name}>"
            elif code in VARIATION_SELECTORS:
                visible = f"<VS {_selector_value(code):02X}>"
            elif unicodedata.category(character).startswith("C"):
                visible = f"<{name}>"
            else:
                visible = character
        inventory.append({
            "offset": offset,
            "character": character,
            "visible": visible,
            "code_point": f"U+{code:04X}",
            "name": name,
            "category": unicodedata.category(character),
        })
    return inventory


def inspect_payloads(text: str) -> dict[str, Any]:
    payloads = _tag_payloads(text) + _zero_width_payloads(text) + _variation_payloads(text)
    payloads.sort(key=lambda payload: (payload.start, payload.end, payload.codec))
    return {
        "disclaimer": "Possible encoded payloads are not confirmed AI watermarks or proof of authorship.",
        "code_point_count": len(text),
        "payloads": [payload.as_dict() for payload in payloads],
        "inventory": code_point_inventory(text),
    }

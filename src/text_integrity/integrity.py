"""Evidence-based pre-submission integrity checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    category: str
    severity: str
    message: str
    evidence: str
    offset: int
    status: str = "unresolved"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


AUTHOR_YEAR = re.compile(r"(?:\(|\[)(?P<body>[A-Z][A-Za-z'’-]+(?:\s+et\s+al\.)?\s*,?\s*(?:19|20)\d{2}[a-z]?)(?:\)|\])")
CITATION_KEY = re.compile(r"\[@(?P<key>[A-Za-z0-9_.:/-]+)\]")
YEAR = re.compile(r"\b(?:19|20)\d{2}[a-z]?\b")
REFERENCE_HEADING = re.compile(r"(?im)^\s*(references|bibliography|works cited)\s*$")
QUOTATION = re.compile(r"[“\"](?P<quote>[^“”\"\n]{40,})[”\"]")


def _normalise(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


def _split_document(text: str) -> tuple[str, str, int]:
    match = REFERENCE_HEADING.search(text)
    if not match:
        return text, "", len(text)
    return text[:match.start()], text[match.end():], match.end()


def _reference_records(reference_text: str, base_offset: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    cursor = base_offset
    for line in reference_text.splitlines(keepends=True):
        stripped = line.strip()
        years = YEAR.findall(stripped)
        surname = re.match(r"(?:\[\d+\]\s*)?([A-Z][A-Za-z'’-]+)", stripped)
        key = re.match(r"\s*@([A-Za-z0-9_.:/-]+)", stripped)
        if stripped and (years or key):
            records.append({
                "text": stripped,
                "surname": _normalise(surname.group(1)) if surname else "",
                "years": {_normalise(year) for year in years},
                "key": _normalise(key.group(1)) if key else "",
                "offset": cursor + len(line) - len(line.lstrip()),
            })
        cursor += len(line)
    return records


def review_integrity(text: str) -> dict[str, Any]:
    """Review citations, references and long quotations without changing text."""
    body, references, reference_offset = _split_document(text)
    records = _reference_records(references, reference_offset)
    findings: list[IntegrityFinding] = []
    cited_records: set[int] = set()
    citation_count = 0

    for match in CITATION_KEY.finditer(body):
        citation_count += 1
        key = _normalise(match.group("key"))
        matches = [index for index, record in enumerate(records) if record["key"] == key]
        if matches:
            cited_records.update(matches)
        else:
            findings.append(IntegrityFinding("citation-without-reference", "warning", "Citation key has no matching bibliography entry.", match.group(0), match.start()))

    for match in AUTHOR_YEAR.finditer(body):
        citation_count += 1
        body_text = match.group("body")
        surname_match = re.match(r"([A-Z][A-Za-z'’-]+)", body_text)
        year_match = YEAR.search(body_text)
        surname = _normalise(surname_match.group(1)) if surname_match else ""
        year = _normalise(year_match.group(0)) if year_match else ""
        matches = [index for index, record in enumerate(records) if record["surname"] == surname and year in record["years"]]
        if matches:
            cited_records.update(matches)
        else:
            findings.append(IntegrityFinding("citation-without-reference", "warning", "Author-year citation has no matching bibliography entry.", match.group(0), match.start()))

    for index, record in enumerate(records):
        if index not in cited_records:
            findings.append(IntegrityFinding("uncited-reference", "info", "Bibliography entry was not matched to an in-text citation.", record["text"][:160], record["offset"]))

    for match in QUOTATION.finditer(body):
        after = body[match.end():match.end() + 180]
        before = body[max(0, match.start() - 80):match.start()]
        if not (AUTHOR_YEAR.search(after) or CITATION_KEY.search(after) or AUTHOR_YEAR.search(before)):
            findings.append(IntegrityFinding("quotation-attribution", "warning", "Long quotation has no nearby recognised citation.", match.group("quote")[:160], match.start()))

    return {
        "disclaimer": "Local integrity diagnostics only. This is not a plagiarism verdict or a Turnitin score prediction.",
        "metrics": {
            "citations_detected": citation_count,
            "references_detected": len(records),
            "matched_references": len(cited_records),
            "unresolved_findings": len(findings),
        },
        "findings": [finding.as_dict() for finding in findings],
    }

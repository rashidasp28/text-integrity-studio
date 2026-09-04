"""Evidence-based pre-submission integrity checks."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from typing import Any


@dataclass(frozen=True, slots=True)
class IntegrityFinding:
    finding_id: str
    category: str
    severity: str
    message: str
    evidence: str
    offset: int
    status: str = "unresolved"
    source: str = "local-analysis"

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


WORD = re.compile(r"\b[\w'’-]+\b", re.UNICODE)
ALLOWED_EXCLUSIONS = {"bibliography", "quotation", "methods", "template", "legal", "common-technical"}


def _corpus_findings(body: str, sources: list[dict[str, str]], first_id: int) -> tuple[list[IntegrityFinding], set[int]]:
    """Find substantial exact-token overlap only in user-authorised sources."""
    body_tokens = [(match.group().casefold(), match.start(), match.end()) for match in WORD.finditer(body)]
    words = [item[0] for item in body_tokens]
    findings: list[IntegrityFinding] = []
    covered: set[int] = set()
    for source_index, source in enumerate(sources):
        source_words = [match.group().casefold() for match in WORD.finditer(source["text"])]
        blocks = SequenceMatcher(None, words, source_words, autojunk=False).get_matching_blocks()
        substantial = [block for block in blocks if block.size >= 12]
        if not substantial:
            continue
        # Report non-overlapping maximal passages, never a global plagiarism conclusion.
        for block in substantial:
            start = body_tokens[block.a][1]
            end = body_tokens[block.a + block.size - 1][2]
            if any(position in covered for position in range(start, end)):
                continue
            covered.update(range(start, end))
            evidence = body[start:end]
            findings.append(IntegrityFinding(
                f"F{first_id + len(findings):04d}", "authorised-corpus-match", "warning",
                f"A {block.size}-word passage also appears in the user-supplied source '{source['name']}'.",
                evidence[:240], start, source=source["name"],
            ))
    return findings, covered


def review_integrity(
    text: str,
    *,
    comparison_sources: list[dict[str, str]] | None = None,
    exclusions: list[str] | None = None,
) -> dict[str, Any]:
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
            findings.append(IntegrityFinding(f"F{len(findings) + 1:04d}", "citation-without-reference", "warning", "Citation key has no matching bibliography entry.", match.group(0), match.start()))

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
            findings.append(IntegrityFinding(f"F{len(findings) + 1:04d}", "citation-without-reference", "warning", "Author-year citation has no matching bibliography entry.", match.group(0), match.start()))

    for index, record in enumerate(records):
        if index not in cited_records:
            findings.append(IntegrityFinding(f"F{len(findings) + 1:04d}", "uncited-reference", "info", "Bibliography entry was not matched to an in-text citation.", record["text"][:160], record["offset"]))

    for match in QUOTATION.finditer(body):
        after = body[match.end():match.end() + 180]
        before = body[max(0, match.start() - 80):match.start()]
        if not (AUTHOR_YEAR.search(after) or CITATION_KEY.search(after) or AUTHOR_YEAR.search(before)):
            findings.append(IntegrityFinding(f"F{len(findings) + 1:04d}", "quotation-attribution", "warning", "Long quotation has no nearby recognised citation.", match.group("quote")[:160], match.start()))

    sources = comparison_sources or []
    if not isinstance(sources, list) or not all(
        isinstance(source, dict) and isinstance(source.get("name"), str) and isinstance(source.get("text"), str)
        for source in sources
    ):
        raise ValueError("Comparison sources must contain string 'name' and 'text' fields.")
    if len(sources) > 20 or sum(len(source["text"]) for source in sources) > 2 * 1024 * 1024:
        raise ValueError("Authorised comparison corpus exceeds the 20-file or 2 MB limit.")
    corpus_findings, covered = _corpus_findings(body, sources, len(findings) + 1)
    findings.extend(corpus_findings)

    requested_exclusions = exclusions or []
    if not isinstance(requested_exclusions, list) or not all(item in ALLOWED_EXCLUSIONS for item in requested_exclusions):
        raise ValueError("Invalid integrity-review exclusion.")
    excluded_findings: list[IntegrityFinding] = []
    active_findings: list[IntegrityFinding] = []
    for finding in findings:
        excluded = (
            ("bibliography" in requested_exclusions and finding.category == "uncited-reference")
            or ("quotation" in requested_exclusions and finding.category == "quotation-attribution")
        )
        (excluded_findings if excluded else active_findings).append(finding)

    coverage = round(100 * len(covered) / max(1, len(body)), 2)

    return {
        "disclaimer": "Local integrity diagnostics only. This is not a plagiarism verdict or a Turnitin score prediction.",
        "metrics": {
            "citations_detected": citation_count,
            "references_detected": len(records),
            "matched_references": len(cited_records),
            "authorised_sources": len(sources),
            "matched_passages": len(corpus_findings),
            "matched_text_coverage_percent": coverage,
            "excluded_findings": len(excluded_findings),
            "unresolved_findings": len(active_findings),
        },
        "limitations": [] if sources else ["No authorised comparison corpus was supplied; only citation and attribution checks were run."],
        "exclusions": requested_exclusions,
        "findings": [finding.as_dict() for finding in active_findings],
        "excluded": [finding.as_dict() | {"status": "excluded"} for finding in excluded_findings],
    }


def build_integrity_audit(report: dict[str, Any], decisions: dict[str, str], transparency_statement: str = "") -> dict[str, Any]:
    """Apply reviewer decisions to findings without changing document text."""
    if not isinstance(decisions, dict) or not all(
        isinstance(key, str) and value in {"unresolved", "reviewed", "dismissed"}
        for key, value in decisions.items()
    ):
        raise ValueError("Integrity decisions must map finding IDs to unresolved, reviewed or dismissed.")
    known = {finding["finding_id"] for finding in report.get("findings", [])}
    unknown = set(decisions) - known
    if unknown:
        raise ValueError(f"Unknown integrity finding: {sorted(unknown)[0]}")
    audited = []
    for finding in report.get("findings", []):
        audited.append(finding | {"status": decisions.get(finding["finding_id"], "unresolved")})
    counts = {status: sum(item["status"] == status for item in audited) for status in ("unresolved", "reviewed", "dismissed")}
    return {
        "disclaimer": report["disclaimer"],
        "metrics": report["metrics"] | counts,
        "limitations": report.get("limitations", []),
        "exclusions": report.get("exclusions", []),
        "findings": audited,
        "excluded": report.get("excluded", []),
        "authorship_transparency_statement": transparency_statement.strip(),
    }

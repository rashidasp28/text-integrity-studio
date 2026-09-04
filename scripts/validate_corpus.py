"""Validate Phase 0 behavioural cases without requiring production code."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CASES = ROOT / "corpus" / "cases"
SCHEMA = ROOT / "corpus" / "schema" / "case.schema.json"


def load_cases() -> list[dict]:
    cases: list[dict] = []
    for path in sorted(CASES.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise ValueError(f"{path}: top-level value must be a list")
        cases.extend(data)
    return cases


def validate() -> int:
    cases = load_cases()
    seen: set[str] = set()
    errors: list[str] = []
    required = {
        "case_id", "title", "input", "options", "expected_output",
        "expected_findings", "source", "confidence", "tags"
    }
    confidence_values = {"verified", "documented", "inferred", "proposed"}
    action_values = {"remove", "replace", "preserve", "flag"}
    for case in cases:
        case_id = case.get("case_id", "<missing>")
        if case_id in seen:
            errors.append(f"duplicate case_id: {case_id}")
        seen.add(case_id)
        missing = sorted(required - set(case))
        if missing:
            errors.append(f"{case_id}: missing fields: {', '.join(missing)}")
            continue
        if case["confidence"] not in confidence_values:
            errors.append(f"{case_id}: invalid confidence")
        if not isinstance(case["options"], list) or len(case["options"]) != len(set(case["options"])):
            errors.append(f"{case_id}: options must be a unique list")
        if not isinstance(case["tags"], list) or len(case["tags"]) != len(set(case["tags"])):
            errors.append(f"{case_id}: tags must be a unique list")
        for finding in case["expected_findings"]:
            code_point = finding.get("code_point", "")
            if not code_point.startswith("U+"):
                errors.append(f"{case_id}: invalid code point {code_point!r}")
            if finding.get("action") not in action_values:
                errors.append(f"{case_id}: invalid finding action")
            if not isinstance(finding.get("count"), int) or finding["count"] < 1:
                errors.append(f"{case_id}: finding count must be positive")
    if errors:
        print("\n".join(errors))
        return 1
    print(f"Validated {len(cases)} behavioural cases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())

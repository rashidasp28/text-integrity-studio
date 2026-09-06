"""Fail closed on release-readiness requirements."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_FILES = (
    "SECURITY.md", "CONTRIBUTING.md", "CHANGELOG.md",
    "docs/USER-GUIDE.md", "docs/ACCEPTANCE-TESTS.md",
    "docs/RELEASE-CHECKLIST.md", "docs/SECURITY-REVIEW.md",
    "docs/THIRD-PARTY-NOTICES.md", "docs/LICENSING-STATUS.md",
    "packaging/SIGNING.md", "requirements-runtime.txt",
)


def project_version() -> str:
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', content, re.MULTILINE)
    if not match:
        raise ValueError("Project version is missing from pyproject.toml.")
    return match.group(1)


def run_checks(*, production: bool = False) -> dict[str, object]:
    checks: list[dict[str, object]] = []
    for relative in REQUIRED_FILES:
        exists = (ROOT / relative).is_file()
        checks.append({"check": f"required-file:{relative}", "passed": exists, "blocking": True})
    version = project_version()
    checks.append({"check": "release-candidate-version", "passed": version == "0.8.0", "blocking": True, "value": version})
    licence_path = ROOT / "LICENSE"
    licence_selected = licence_path.is_file() and "MIT License" in licence_path.read_text(encoding="utf-8")
    checks.append({
        "check": "project-licence-selected", "passed": licence_selected,
        "blocking": production,
        "note": "The repository licence must remain present and match the approved MIT licence.",
    })
    signing_ready = (ROOT / "packaging" / "SIGNING-READY").is_file()
    checks.append({
        "check": "platform-signing-configured", "passed": signing_ready,
        "blocking": production,
        "note": "Required for v1.0.0; recorded but non-blocking for v0.8.0 RC.",
    })
    failed = [item for item in checks if item["blocking"] and not item["passed"]]
    return {
        "version": version,
        "release_level": "production" if production else "release-candidate",
        "passed": not failed,
        "checks": checks,
        "blocking_failures": [item["check"] for item in failed],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args()
    report = run_checks(production=args.production)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

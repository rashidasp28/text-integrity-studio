"""Command-line interface for local inspection and cleaning."""

from __future__ import annotations

import argparse
import base64
import json
import sys
from pathlib import Path

from .engine import clean, inspect
from .documents import import_document
from .multilingual import analyse_scripts
from .rewrite import analyse_rewrite, apply_rewrite


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="text-integrity")
    subparsers = parser.add_subparsers(dest="command", required=True)
    inspect_parser = subparsers.add_parser("inspect", help="Report unusual Unicode characters")
    inspect_parser.add_argument("input", help="UTF-8 text file or - for stdin")
    clean_parser = subparsers.add_parser("clean", help="Apply deterministic cleaning rules")
    clean_parser.add_argument("input", help="UTF-8 text file or - for stdin")
    clean_parser.add_argument("--profile", choices=("safe", "publishing"), default="safe")
    clean_parser.add_argument("--rule", action="append", default=[], help="Enable an additional rule")
    clean_parser.add_argument("--output", help="Write cleaned UTF-8 text to this file")
    clean_parser.add_argument("--report", help="Write a JSON audit report to this file")
    rewrite_parser = subparsers.add_parser("rewrite", help="Analyse or apply deterministic style suggestions")
    rewrite_parser.add_argument("input", help="UTF-8 text file or - for stdin")
    rewrite_parser.add_argument("--accept", action="append", default=[], help="Accept a suggestion ID, for example S0001")
    rewrite_parser.add_argument("--output", help="Write revised UTF-8 text to this file")
    rewrite_parser.add_argument("--report", help="Write a JSON analysis or revision audit")
    extract_parser = subparsers.add_parser("extract", help="Extract text from TXT, Markdown, HTML, DOCX or PDF")
    extract_parser.add_argument("input", help="Document path")
    extract_parser.add_argument("--output", help="Write extracted UTF-8 text to this file")
    extract_parser.add_argument("--report", help="Write document metadata and warnings as JSON")
    scripts_parser = subparsers.add_parser("scripts", help="Analyse Unicode scripts in a UTF-8 text file")
    scripts_parser.add_argument("input", help="UTF-8 text file or - for stdin")
    studio_parser = subparsers.add_parser("studio", help="Open the local visual interface")
    studio_parser.add_argument("--host", default="127.0.0.1")
    studio_parser.add_argument("--port", default=8765, type=int)
    studio_parser.add_argument("--no-browser", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "studio":
            from .studio import run_studio

            run_studio(args.host, args.port, open_browser=not args.no_browser)
            return 0
        if args.command == "extract":
            document_path = Path(args.input)
            result = import_document(document_path.name, base64.b64encode(document_path.read_bytes()).decode("ascii"))
            if args.output:
                Path(args.output).write_text(result["text"], encoding="utf-8")
            else:
                sys.stdout.write(result["text"])
            if args.report:
                metadata = {key: value for key, value in result.items() if key != "text"}
                Path(args.report).write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 0
        source = _read(args.input)
        if args.command == "inspect":
            print(json.dumps([finding.as_dict() for finding in inspect(source)], ensure_ascii=False, indent=2))
            return 0
        if args.command == "rewrite":
            result = apply_rewrite(source, args.accept) if args.accept else analyse_rewrite(source)
            if args.output:
                if not args.accept:
                    raise ValueError("--output requires at least one --accept suggestion ID.")
                Path(args.output).write_text(result["output"], encoding="utf-8")
            else:
                print(json.dumps(result, ensure_ascii=False, indent=2))
            if args.report:
                Path(args.report).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return 0
        if args.command == "scripts":
            print(json.dumps(analyse_scripts(source), ensure_ascii=False, indent=2))
            return 0
        result = clean(source, profile=args.profile, options=args.rule)
        if args.output:
            Path(args.output).write_text(result.output, encoding="utf-8")
        else:
            sys.stdout.write(result.output)
        if args.report:
            Path(args.report).write_text(
                json.dumps(result.as_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f"text-integrity: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Dependency-free local HTTP host for the visual studio preview."""

from __future__ import annotations

import json
import mimetypes
import threading
import webbrowser
from difflib import SequenceMatcher
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .engine import clean, inspect
from .documents import import_document
from .integrity import build_integrity_audit, review_integrity
from .multilingual import analyse_scripts
from .payloads import inspect_payloads
from .rewrite import analyse_rewrite, apply_rewrite

MAX_REQUEST_BYTES = 6 * 1024 * 1024
WEB_ROOT = files("text_integrity").joinpath("web")


def build_diff(original: str, output: str) -> list[dict[str, str]]:
    """Return safe, character-level diff segments for presentation."""
    segments: list[dict[str, str]] = []
    for operation, old_start, old_end, new_start, new_end in SequenceMatcher(
        None, original, output, autojunk=False
    ).get_opcodes():
        segments.append({
            "operation": operation,
            "original": original[old_start:old_end],
            "output": output[new_start:new_end],
        })
    return segments


def process_api(path: str, payload: dict[str, Any]) -> Any:
    if path == "/api/document/import":
        return import_document(payload.get("name"), payload.get("content"))
    if path == "/api/batch":
        batch_files = payload.get("files")
        if not isinstance(batch_files, list) or not all(
            isinstance(item, dict) and isinstance(item.get("name"), str) and isinstance(item.get("text"), str)
            for item in batch_files
        ):
            raise ValueError("Batch files must contain string 'name' and 'text' fields.")
        if len(batch_files) > 20 or sum(len(item["text"].encode("utf-8")) for item in batch_files) > 2 * 1024 * 1024:
            raise ValueError("Batch processing is limited to 20 files and 2 MB of UTF-8 text.")
        results = []
        for item in batch_files:
            processed = clean(item["text"], profile="safe").as_dict()
            results.append({
                "name": item["name"], "characters": len(item["text"]),
                "findings": len(processed["findings"]), "changes": len(processed["edits"]),
                "output": processed["output"], "audit": processed,
            })
        return {"files": results, "file_count": len(results), "processing": "local-in-memory"}
    text = payload.get("text")
    if not isinstance(text, str):
        raise ValueError("The 'text' field must be a string.")
    if path == "/api/inspect":
        return {"findings": [finding.as_dict() for finding in inspect(text)]}
    if path == "/api/clean":
        profile = payload.get("profile", "safe")
        options = payload.get("options", [])
        if profile is not None and not isinstance(profile, str):
            raise ValueError("Invalid profile.")
        if not isinstance(options, list) or not all(isinstance(option, str) for option in options):
            raise ValueError("Invalid profile or options.")
        result = clean(text, profile=profile, options=options).as_dict()
        result["diff"] = build_diff(text, result["output"])
        return result
    if path == "/api/integrity":
        return review_integrity(
            text,
            comparison_sources=payload.get("comparison_sources", []),
            exclusions=payload.get("exclusions", []),
        )
    if path == "/api/integrity/audit":
        report = payload.get("report")
        if not isinstance(report, dict):
            raise ValueError("The integrity report is required before exporting an audit.")
        return build_integrity_audit(
            report,
            payload.get("decisions", {}),
            payload.get("transparency_statement", ""),
        )
    if path == "/api/payloads":
        return inspect_payloads(text)
    if path == "/api/scripts":
        return analyse_scripts(text)
    if path == "/api/rewrite/analyse":
        return analyse_rewrite(text, backend=payload.get("backend", "deterministic"))
    if path == "/api/rewrite/apply":
        result = apply_rewrite(
            text,
            payload.get("accepted_ids", []),
            backend=payload.get("backend", "deterministic"),
        )
        result["diff"] = build_diff(text, result["output"])
        return result
    raise ValueError("Unknown API endpoint.")


class StudioHandler(BaseHTTPRequestHandler):
    server_version = "TextIntegrityStudio/0.1"

    def _json(self, status: HTTPStatus, body: Any) -> None:
        content = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self) -> None:  # noqa: N802
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > MAX_REQUEST_BYTES:
                self._json(HTTPStatus.REQUEST_ENTITY_TOO_LARGE, {"error": "Text exceeds 2 MB."})
                return
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            self._json(HTTPStatus.OK, process_api(urlparse(self.path).path, payload))
        except (UnicodeError, json.JSONDecodeError, ValueError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": str(error)})

    def do_GET(self) -> None:  # noqa: N802
        requested = urlparse(self.path).path
        relative = "index.html" if requested == "/" else requested.lstrip("/")
        if ".." in Path(relative).parts:
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        resource = WEB_ROOT.joinpath(relative)
        if not resource.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        content = resource.read_bytes()
        content_type = mimetypes.guess_type(relative)[0] or "application/octet-stream"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'self'; style-src 'self'; script-src 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format: str, *args: object) -> None:
        # Deliberately omit request paths and text from logs.
        return


def run_studio(host: str = "127.0.0.1", port: int = 8765, *, open_browser: bool = True) -> None:
    if host not in {"127.0.0.1", "localhost"}:
        raise ValueError("Studio may only bind to localhost.")
    server = ThreadingHTTPServer((host, port), StudioHandler)
    url = f"http://{host}:{port}"
    print(f"Text Integrity Studio is running at {url}")
    print("Press Ctrl+C to stop it.")
    if open_browser:
        threading.Timer(0.25, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

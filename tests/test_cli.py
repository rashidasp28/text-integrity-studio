import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from text_integrity.cli import main


class CliTests(unittest.TestCase):
    def test_inspect_reads_stdin_and_emits_json(self):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            with patch("sys.stdin", io.StringIO("A\u200bB")):
                exit_code = main(["inspect", "-"])

        findings = json.loads(stdout.getvalue())
        self.assertEqual(exit_code, 0)
        self.assertEqual(findings[0]["code_point"], "U+200B")

    def test_clean_writes_output_and_audit_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.txt"
            output = root / "cleaned.txt"
            report = root / "audit.json"
            source.write_text("A\u200b—B", encoding="utf-8")

            exit_code = main([
                "clean",
                str(source),
                "--profile",
                "publishing",
                "--output",
                str(output),
                "--report",
                str(report),
            ])

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "A-B")
            audit = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(audit["changed"])
            self.assertEqual([edit["rule_id"] for edit in audit["edits"]], [
                "remove_hidden",
                "normalize_dashes",
            ])

    def test_rewrite_writes_only_explicitly_accepted_suggestion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.txt"
            output = root / "revised.txt"
            report = root / "rewrite-audit.json"
            source.write_text("In order to proceed, we test.", encoding="utf-8")

            exit_code = main([
                "rewrite",
                str(source),
                "--accept",
                "S0001",
                "--output",
                str(output),
                "--report",
                str(report),
            ])

            self.assertEqual(exit_code, 0)
            self.assertEqual(output.read_text(encoding="utf-8"), "To proceed, we test.")
            audit = json.loads(report.read_text(encoding="utf-8"))
            self.assertTrue(audit["facts_preserved"])
            self.assertEqual(
                [item["suggestion_id"] for item in audit["accepted_suggestions"]],
                ["S0001"],
            )

    def test_rewrite_rejects_output_without_acceptance(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "input.txt"
            output = root / "revised.txt"
            source.write_text("In order to proceed, we test.", encoding="utf-8")
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main([
                    "rewrite",
                    str(source),
                    "--output",
                    str(output),
                ])

            self.assertEqual(exit_code, 2)
            self.assertFalse(output.exists())
            self.assertIn("--output requires at least one --accept", stderr.getvalue())

    def test_extract_writes_html_text_and_metadata_report(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "study.html"
            output = root / "study.txt"
            report = root / "import.json"
            source.write_text(
                "<h1>Study title</h1><p>Visible text</p><script>hidden()</script>",
                encoding="utf-8",
            )

            exit_code = main([
                "extract",
                str(source),
                "--output",
                str(output),
                "--report",
                str(report),
            ])

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                output.read_text(encoding="utf-8"),
                "Study title\nVisible text",
            )
            metadata = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(metadata["format"], "html")
            self.assertEqual(metadata["structure"], {"blocks": 2})
            self.assertEqual(metadata["processing"], "local-in-memory")
            self.assertNotIn("text", metadata)

    def test_scripts_reads_stdin_and_emits_json(self):
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            with patch("sys.stdin", io.StringIO("Latin text العربية العربية")):
                exit_code = main(["scripts", "-"])

        report = json.loads(stdout.getvalue())
        scripts = {item["script"] for item in report["scripts"]}
        self.assertEqual(exit_code, 0)
        self.assertEqual(scripts, {"Latin", "Arabic"})
        self.assertEqual(report["warnings"][0]["category"], "mixed-scripts")

    def test_extract_rejects_unsupported_document_type(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "study.csv"
            source.write_text("heading,value\nexample,1\n", encoding="utf-8")
            stderr = io.StringIO()

            with redirect_stderr(stderr):
                exit_code = main(["extract", str(source)])

            self.assertEqual(exit_code, 2)
            self.assertIn(
                "Supported document types are TXT, Markdown, HTML, DOCX and PDF",
                stderr.getvalue(),
            )

    def test_missing_input_returns_controlled_error(self):
        stderr = io.StringIO()

        with redirect_stderr(stderr):
            exit_code = main(["clean", "missing-input.txt"])

        self.assertEqual(exit_code, 2)
        self.assertIn("text-integrity:", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()

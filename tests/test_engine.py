import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_integrity import __version__, analyse_rewrite, apply_rewrite, clean, inspect, inspect_payloads
from text_integrity.studio import build_diff, process_api
from text_integrity.integrity import review_integrity


def all_cases():
    for path in sorted((ROOT / "corpus" / "cases").glob("*.json")):
        yield from json.loads(path.read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
    def test_release_version(self):
        self.assertEqual(__version__, "0.5.0")

    def test_every_corpus_case_has_exact_output(self):
        for case in all_cases():
            with self.subTest(case=case["case_id"]):
                result = clean(case["input"], profile=None, options=case["options"])
                self.assertEqual(result.output, case["expected_output"])

    def test_all_deterministic_cases_are_idempotent(self):
        for case in all_cases():
            with self.subTest(case=case["case_id"]):
                first = clean(case["input"], profile=None, options=case["options"])
                second = clean(first.output, profile=None, options=case["options"])
                self.assertEqual(second.output, first.output)

    def test_findings_match_expected_actions(self):
        for case in all_cases():
            actual = clean(case["input"], profile=None, options=case["options"]).findings
            for expected in case["expected_findings"]:
                matching = [f for f in actual if f.code_point == expected["code_point"]]
                self.assertGreaterEqual(len(matching), expected["count"], case["case_id"])
                self.assertEqual(matching[0].action.value, expected["action"], case["case_id"])

    def test_audit_edits_reconstruct_output(self):
        result = clean("A\u200b—B", profile="publishing")
        self.assertTrue(result.changed)
        self.assertEqual(result.output, "A-B")
        self.assertEqual([edit.rule_id for edit in result.edits], ["remove_hidden", "normalize_dashes"])

    def test_unknown_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown profile"):
            clean("text", profile="aggressive")

    def test_studio_api_uses_core_engine(self):
        result = process_api("/api/clean", {"text": "A\u200b—B", "profile": "publishing"})
        self.assertEqual(result["output"], "A-B")
        self.assertEqual(len(result["findings"]), 2)

    def test_studio_api_rejects_invalid_payload(self):
        with self.assertRaisesRegex(ValueError, "text"):
            process_api("/api/inspect", {"text": 42})

    def test_custom_rules_and_diff(self):
        result = process_api(
            "/api/clean",
            {"text": "A—B…", "profile": None, "options": ["normalize_dashes"]},
        )
        self.assertEqual(result["output"], "A-B…")
        self.assertTrue(any(segment["operation"] == "replace" for segment in result["diff"]))

    def test_diff_round_trip(self):
        diff = build_diff("old", "bold")
        self.assertEqual("".join(part["original"] for part in diff), "old")
        self.assertEqual("".join(part["output"] for part in diff), "bold")

    def test_integrity_review_reconciles_author_year_citation(self):
        report = review_integrity(
            "Evidence supports this (Smith, 2024).\n\nReferences\nSmith, J. (2024). Example study."
        )
        self.assertEqual(report["metrics"]["citations_detected"], 1)
        self.assertEqual(report["metrics"]["matched_references"], 1)
        self.assertEqual(report["findings"], [])

    def test_integrity_review_flags_missing_reference_and_uncited_entry(self):
        report = review_integrity(
            "A claim (Jones, 2025).\n\nReferences\nSmith, J. (2024). Example study."
        )
        categories = {finding["category"] for finding in report["findings"]}
        self.assertEqual(categories, {"citation-without-reference", "uncited-reference"})

    def test_integrity_review_flags_long_unattributed_quote(self):
        report = review_integrity(
            'The source states “This is a sufficiently long quotation that needs a nearby citation for attribution.”'
        )
        self.assertEqual(report["findings"][0]["category"], "quotation-attribution")

    def test_integrity_api_uses_local_reviewer(self):
        report = process_api("/api/integrity", {"text": "No citations here."})
        self.assertIn("Turnitin score prediction", report["disclaimer"])

    def test_unicode_tag_payload_decodes(self):
        encoded = "".join(chr(0xE0000 + ord(character)) for character in "hello") + chr(0xE007F)
        report = inspect_payloads("Visible" + encoded)
        self.assertEqual(report["payloads"][0]["codec"], "unicode-tags")
        self.assertEqual(report["payloads"][0]["decoded_text"], "hello")

    def test_zero_width_binary_payload_decodes(self):
        encoded = "".join("\u200b" if bit == "0" else "\u200c" for bit in "01000001")
        report = inspect_payloads(encoded)
        self.assertEqual(report["payloads"][0]["decoded_text"], "A")

    def test_variation_selector_payload_decodes(self):
        encoded = "".join(chr(0xE0100 + value - 16) for value in b"test")
        report = inspect_payloads("A" + encoded)
        self.assertEqual(report["payloads"][0]["codec"], "variation-selector-bytes")
        self.assertEqual(report["payloads"][0]["decoded_text"], "test")

    def test_inventory_makes_invisible_character_visible(self):
        report = process_api("/api/payloads", {"text": "A\u200bB"})
        self.assertEqual(report["inventory"][1]["visible"], "<ZWSP>")
        self.assertIn("not confirmed AI watermarks", report["disclaimer"])

    def test_rewrite_analysis_protects_scientific_facts(self):
        text = "In order to test 7.3 mW on 9 September 2026, we recorded data (Smith, 2024)."
        report = analyse_rewrite(text)
        self.assertEqual(report["suggestions"][0]["replacement"], "To")
        protected = {(span["category"], span["text"]) for span in report["protected_spans"]}
        self.assertIn(("measurement", "7.3 mW"), protected)
        self.assertIn(("date", "9 September 2026"), protected)
        self.assertIn(("citation", "(Smith, 2024)"), protected)

    def test_rewrite_applies_only_accepted_suggestions(self):
        text = "In order to proceed prior to imaging, we prepared samples."
        analysis = analyse_rewrite(text)
        result = apply_rewrite(text, [analysis["suggestions"][0]["suggestion_id"]])
        self.assertTrue(result["facts_preserved"])
        self.assertIn("To proceed prior to imaging", result["output"])
        self.assertEqual(len(result["accepted_suggestions"]), 1)
        self.assertEqual(len(result["rejected_suggestion_ids"]), 1)

    def test_rewrite_rejects_unknown_suggestion(self):
        with self.assertRaisesRegex(ValueError, "Unknown rewrite suggestion"):
            apply_rewrite("In order to proceed.", ["S9999"])

    def test_rewrite_api_round_trip(self):
        analysis = process_api("/api/rewrite/analyse", {"text": "Due to the fact that it rained, we stopped."})
        suggestion_id = analysis["suggestions"][0]["suggestion_id"]
        result = process_api("/api/rewrite/apply", {"text": "Due to the fact that it rained, we stopped.", "accepted_ids": [suggestion_id]})
        self.assertEqual(result["output"], "Because it rained, we stopped.")
        self.assertTrue(any(segment["operation"] == "replace" for segment in result["diff"]))

    def test_rewrite_rejects_duplicate_acceptance(self):
        with self.assertRaisesRegex(ValueError, "only once"):
            apply_rewrite("In order to proceed.", ["S0001", "S0001"])


if __name__ == "__main__":
    unittest.main()

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from text_integrity import clean, inspect
from text_integrity.studio import process_api


def all_cases():
    for path in sorted((ROOT / "corpus" / "cases").glob("*.json")):
        yield from json.loads(path.read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

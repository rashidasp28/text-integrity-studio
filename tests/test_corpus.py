import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def all_cases():
    for path in sorted((ROOT / "corpus" / "cases").glob("*.json")):
        yield from json.loads(path.read_text(encoding="utf-8"))


class CorpusTests(unittest.TestCase):
    def test_case_ids_are_unique(self):
        ids = [case["case_id"] for case in all_cases()]
        self.assertEqual(len(ids), len(set(ids)))

    def test_verified_cases_have_black_box_sources(self):
        for case in all_cases():
            if case["confidence"] == "verified":
                self.assertEqual(case["source"]["kind"], "black_box")

    def test_expected_findings_refer_to_present_characters(self):
        for case in all_cases():
            for finding in case["expected_findings"]:
                character = chr(int(finding["code_point"][2:], 16))
                self.assertGreaterEqual(case["input"].count(character), finding["count"])


if __name__ == "__main__":
    unittest.main()

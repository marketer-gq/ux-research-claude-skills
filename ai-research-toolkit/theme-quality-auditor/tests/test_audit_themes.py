"""Regression tests for scripts/audit_themes.py. Run from the skill folder:

    python3 -m unittest discover
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "audit_themes.py"
FIX = HERE / "fixtures"


def run(*args):
    """Run the script; return (exit code, stdout, stderr, parsed JSON or None)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.json"
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)] + [str(a) for a in args] + ["--json", str(out)],
            capture_output=True, text=True)
        data = json.loads(out.read_text()) if out.exists() else None
    return proc.returncode, proc.stdout, proc.stderr, data


def findings_for(data, theme):
    return [f for f in data["findings"] if f["theme"] == theme]


class ThinEvidence(unittest.TestCase):
    def test_one_participant_is_not_a_topic_summary(self):
        code, out, _, data = run(FIX / "thin_evidence.md")
        name = "Receipts get lost between approval steps"
        self.assertNotEqual(data["verdicts"][name], "topic summary")
        self.assertEqual(data["verdicts"][name], "review")
        ev = [f for f in findings_for(data, name) if f["check"] == "evidence"]
        self.assertEqual(len(ev), 1)
        self.assertEqual(ev[0]["level"], "review")
        self.assertIn("thin evidence", ev[0]["message"])
        self.assertEqual(code, 0)

    def test_question_fits_thin_evidence(self):
        _, out, _, _ = run(FIX / "thin_evidence.md")
        self.assertNotIn("apart from being about it", out)
        self.assertNotIn("beyond being about it", out)
        self.assertIn("Who else said something", out)


class TopicLabels(unittest.TestCase):
    TOPICS = ["Onboarding experiences and challenges", "Trust", "Trust in reporting",
              "Getting started", "Using the mobile app", "Managing permissions",
              "Admin pain points", "Customer support interactions",
              "Reporting needs of finance managers",
              "Billing: including invoices and receipts",
              "What do you think of the mobile app?"]
    CLAIMS = ["Pricing confuses admins", "Approvals stall in finance",
              "Admins don't trust the export numbers"]

    def test_topic_labels_flagged(self):
        code, _, _, data = run(FIX / "topic_labels.md")
        for name in self.TOPICS:
            with self.subTest(name=name):
                self.assertEqual(data["verdicts"].get(name), "topic summary")
        self.assertEqual(code, 1)

    def test_claim_labels_not_flagged(self):
        code, _, _, data = run(FIX / "claim_labels.md")
        for name in self.CLAIMS:
            with self.subTest(name=name):
                self.assertEqual(data["verdicts"].get(name), "theme")
                self.assertEqual(findings_for(data, name), [])
        self.assertEqual(code, 0)


class GuideOverlap(unittest.TestCase):
    def test_claim_name_not_flagged_on_word_overlap(self):
        _, _, _, data = run(FIX / "guide_overlap.md", "--guide", FIX / "guide.md")
        name = "Approvals stall in finance"
        self.assertEqual([f for f in findings_for(data, name) if f["check"] == "guide"], [])
        self.assertEqual(data["verdicts"][name], "theme")

    def test_topic_name_still_flagged(self):
        _, out, _, data = run(FIX / "guide_overlap.md", "--guide", FIX / "guide.md")
        guide = [f for f in findings_for(data, "Onboarding") if f["check"] == "guide"]
        self.assertEqual(len(guide), 1)
        self.assertEqual(data["verdicts"]["Onboarding"], "topic summary")
        # The question names the guide item it mirrors.
        self.assertIn("follows the guide item", out)

    def test_missing_guide_is_friendly(self):
        code, out, err, _ = run(FIX / "guide_overlap.md", "--guide", FIX / "no_such_guide.md")
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)
        self.assertIn("can't find the discussion guide", err)


class Affinity(unittest.TestCase):
    def test_affinity_mode(self):
        code, out, _, data = run(FIX / "affinity_groups.md", "--approach", "affinity")
        self.assertIn("Holtzblatt & Beyer", out)
        self.assertEqual(data["verdicts"]["Admin pain points"], "topic summary")
        self.assertEqual(data["verdicts"]["I don't know who approved what"], "theme")
        desc = [f for f in data["findings"] if f["check"] == "description"]
        self.assertTrue(desc)
        self.assertTrue(all(f["level"] == "note" for f in desc))
        self.assertEqual(code, 1)


class Blockquotes(unittest.TestCase):
    def test_multiline_blockquote_is_one_extract(self):
        _, out, _, data = run(FIX / "multiline_quote.md")
        name = "Approvers clear the queue rather than decide"
        self.assertIn("2 extract(s) from 2 participant(s)", out)
        self.assertEqual(data["verdicts"][name], "theme")


class Emergence(unittest.TestCase):
    def test_only_flags_emergence_about_themes(self):
        _, _, _, data = run(FIX / "emergence.md")
        lines = sorted(f["line"] for f in data["findings"] if f["check"] == "emergence")
        # line 3: "Three themes emerged", line 4: "insights surfaced in the data".
        # Not line 5 ("emerging markets") or the theme's "problem surfaced".
        self.assertEqual(lines, [3, 4])


if __name__ == "__main__":
    unittest.main()

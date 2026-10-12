"""Regression tests for scripts/score_moderation.py.

Run from the skill folder:  python3 -m unittest discover
All fixtures are synthetic.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "score_moderation.py"
FIX = HERE / "fixtures"


def run(*args):
    """Run the script; return (exit code, stdout+stderr, parsed JSON or None)."""
    with tempfile.TemporaryDirectory() as tmp:
        out = os.path.join(tmp, "out.json")
        proc = subprocess.run(
            [sys.executable, str(SCRIPT)] + [str(a) for a in args] + ["--json", out],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
        data = None
        if os.path.exists(out):
            with open(out, encoding="utf-8") as fh:
                data = json.load(fh)
        return proc.returncode, proc.stdout, data


def write_tmp(text, suffix=".txt"):
    fh = tempfile.NamedTemporaryFile("w", suffix=suffix, delete=False, encoding="utf-8")
    fh.write(text)
    fh.close()
    return fh.name


class TestVttSpeakers(unittest.TestCase):
    def test_voice_tags_give_two_speakers_and_correct_share(self):
        code, out, data = run(FIX / "voice_tags.vtt", "--moderator", "Alex")
        self.assertEqual(code, 0, out)
        self.assertEqual(data["speakers"], ["Alex", "Priya"])
        self.assertEqual(data["basis"], "duration")
        # Alex 10s, Priya 40s.
        self.assertAlmostEqual(data["participant_share"], 0.8, places=3)


class TestNoInventedPauses(unittest.TestCase):
    def test_plain_transcript_reports_silence_not_measured(self):
        code, out, data = run(FIX / "plain_no_end.txt")
        self.assertEqual(code, 0, out)
        self.assertFalse(data["have_gaps"])
        self.assertIsNone(data["interruptions"])
        self.assertEqual(data["silences"], [])
        self.assertIn("not measured", out)

    def test_back_to_back_cues_are_not_interruptions(self):
        code, out, data = run(FIX / "back_to_back.vtt")
        self.assertEqual(code, 0, out)
        # Two cues start exactly when the last ended (gap 0); one overlaps by 0.5s.
        self.assertEqual(data["interruptions"], 1)


class TestModeratorChoice(unittest.TestCase):
    def test_two_role_labels_is_ambiguous(self):
        code, out, _ = run(FIX / "two_role_labels.txt")
        self.assertNotEqual(code, 0)
        self.assertIn("--moderator", out)

    def test_question_count_tie_is_ambiguous(self):
        code, out, _ = run(FIX / "question_tie.txt")
        self.assertNotEqual(code, 0)
        self.assertIn("--moderator", out)

    def test_partial_name_does_not_match(self):
        code, out, _ = run(FIX / "al_alice.txt", "--moderator", "Al")
        self.assertNotEqual(code, 0)

    def test_exact_name_wins_over_prefix(self):
        for _ in range(3):
            code, out, data = run(FIX / "al_and_alice.txt", "--moderator", "Al")
            self.assertEqual(code, 0, out)
            self.assertEqual(data["moderators"], ["Al"])

    def test_two_moderators(self):
        code, out, data = run(FIX / "two_moderators.txt", "--moderator", "Alex,Sam")
        self.assertEqual(code, 0, out)
        self.assertEqual(data["moderators"], ["Alex", "Sam"])
        self.assertEqual(data["moderator_turns"], 2)
        self.assertGreater(data["participant_share"], 0.5)


class TestParsers(unittest.TestCase):
    def test_parenthesised_timestamp(self):
        code, out, data = run(FIX / "paren_ts.txt", "--moderator", "Alex")
        self.assertEqual(code, 0, out)
        self.assertEqual(data["speakers"], ["Alex", "Priya"])

    def test_otter_header_lines(self):
        code, out, data = run(FIX / "otter.txt", "--moderator", "Alex")
        self.assertEqual(code, 0, out)
        self.assertEqual(data["speakers"], ["Alex", "Priya"])
        self.assertEqual(data["turns"], 4)


def banded(mod_words, par_words):
    return write_tmp(
        "[00:00:00] Moderator: %s?\n[00:00:10] Participant: %s\n"
        % (" ".join(["word"] * mod_words), " ".join(["word"] * par_words)))


class TestSessionType(unittest.TestCase):
    def test_interview_bands(self):
        cases = [((15, 85), "ok"), ((25, 75), "acceptable"), ((35, 65), "REVIEW")]
        for (m, p), want in cases:
            path = banded(m, p)
            try:
                code, out, data = run(path)
                self.assertEqual(code, 0, out)
                self.assertEqual(data["talk_time_status"], want, (m, p))
            finally:
                os.unlink(path)

    def test_think_aloud_is_not_scored(self):
        path = banded(35, 65)
        try:
            for kind in ("think-aloud", "usability"):
                code, out, data = run(path, "--session-type", kind)
                self.assertEqual(code, 0, out)
                self.assertEqual(data["talk_time_status"], "info")
                self.assertIn("TALK TIME  [info]", out)
        finally:
            os.unlink(path)


class TestGuide(unittest.TestCase):
    def test_headings_skipped_and_coverage_never_review(self):
        code, out, data = run(FIX / "plain_no_end.txt", "--guide", FIX / "guide.md")
        self.assertEqual(code, 0, out)
        cov = data["coverage"]
        self.assertEqual(len(cov["covered"]) + len(cov["missed"]), 2)
        guide_lines = [ln for ln in out.splitlines() if ln.startswith("GUIDE")]
        self.assertTrue(guide_lines)
        self.assertNotIn("REVIEW", guide_lines[0])

    def test_missed_guide_items_are_info_only(self):
        guide = write_tmp("- Which competitor products have you tried this year?\n"
                          "- What would make you cancel your subscription?\n", ".md")
        try:
            code, out, data = run(FIX / "plain_no_end.txt", "--guide", guide)
            self.assertEqual(code, 0, out)
            self.assertEqual(len(data["coverage"]["covered"]), 0)
            guide_lines = [ln for ln in out.splitlines() if ln.startswith("GUIDE")]
            self.assertNotIn("REVIEW", guide_lines[0])
        finally:
            os.unlink(guide)


class TestLeadingLanguage(unittest.TestCase):
    def setUp(self):
        code, out, data = run(FIX / "leading.txt")
        self.assertEqual(code, 0, out)
        self.flagged = [x["question"] for x in data["leading"]]

    def assertFlagged(self, fragment):
        self.assertTrue(any(fragment in q for q in self.flagged),
                        "%r not flagged; flagged: %r" % (fragment, self.flagged))

    def assertNotFlagged(self, fragment):
        self.assertFalse(any(fragment in q for q in self.flagged),
                         "%r wrongly flagged" % fragment)

    def test_tag_questions(self):
        self.assertFlagged("didn't you?")
        self.assertFlagged("Isn't it so much faster")

    def test_how_much_did_you_love(self):
        self.assertFlagged("How much did you love")

    def test_norming(self):
        self.assertFlagged("Most people find")

    def test_comprehension_check_not_flagged(self):
        self.assertNotFlagged("Did I get that right?")

    def test_open_either_or_not_flagged(self):
        self.assertNotFlagged("or something else?")


class TestEstimatedDurations(unittest.TestCase):
    def test_untimed_longest_turn_labelled_estimated(self):
        code, out, data = run(FIX / "plain_no_end.txt")
        self.assertEqual(code, 0, out)
        self.assertTrue(data["longest_moderator_turn_estimated"])
        block = out.split("LONGEST MODERATOR TURN", 1)[1].split("\n\n", 1)[0]
        self.assertIn("estimated", block)

    def test_timed_longest_turn_not_estimated(self):
        code, out, data = run(FIX / "voice_tags.vtt", "--moderator", "Alex")
        self.assertEqual(code, 0, out)
        self.assertFalse(data["longest_moderator_turn_estimated"])


if __name__ == "__main__":
    unittest.main()

"""Regression tests for scripts/audit_evidence.py.

Run from the skill folder:  python3 -m unittest discover
Set EIA_SCRIPT to point the tests at a different copy of the script (used to
confirm each test fails against the pre-review version).

All fixtures are synthetic. No real participant data.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import synth_transcript as synth  # noqa: E402

FIXTURES = HERE / "fixtures"
SCRIPT = Path(os.environ.get("EIA_SCRIPT")
              or HERE.parent / "scripts" / "audit_evidence.py")
SKILL_MD = Path(os.environ.get("EIA_SKILL_MD") or HERE.parent / "SKILL.md")


def run(report_text, sources=None, args=(), report_in_sources=False):
    """Run the script on a report. sources is {filename: text} or None.

    Returns (exit code, stdout, stderr, parsed JSON or None).
    """
    tmp = Path(tempfile.mkdtemp(prefix="eia-test-"))
    try:
        src_dir = tmp / "sources"
        src_dir.mkdir()
        report = (src_dir if report_in_sources else tmp) / "report.md"
        report.write_text(report_text, encoding="utf-8")
        cmd = [sys.executable, str(SCRIPT), str(report), "--json", str(tmp / "out.json")]
        if sources is not None:
            for name, text in sources.items():
                (src_dir / name).write_text(text, encoding="utf-8")
            cmd += ["--sources", str(src_dir)]
        cmd += list(args)
        p = subprocess.run(cmd, capture_output=True, text=True)
        out = tmp / "out.json"
        data = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
        return p.returncode, p.stdout, p.stderr, data
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def verification(data):
    v = dict(data["stats"]["verification"])
    v.setdefault("not_located", 0)
    v.setdefault("verified", v["checked"] - v["absent"] - v["altered"] - v["not_located"])
    return v


def checks(data, severity=None):
    return [f for f in data["findings"]
            if severity is None or f["severity"] == severity]


class LongTranscriptMatching(unittest.TestCase):
    """Each quote form against a ~10k-word synthetic transcript."""

    @classmethod
    def setUpClass(cls):
        cls.transcript = synth.build_transcript()
        cls.sources = {"session-01.txt": cls.transcript}

    def case(self, key, args=()):
        report = "# Reporting\n\n%s\n" % synth.REPORT_QUOTES[key]
        rc, out, err, data = run(report, self.sources, args)
        self.assertIsNotNone(data, err)
        return rc, out, data

    def test_fixture_is_about_10k_words(self):
        self.assertGreaterEqual(len(self.transcript.split()), 10000)

    def assert_located(self, key):
        rc, out, data = self.case(key)
        v = verification(data)
        self.assertEqual(v["checked"], 1, out)
        self.assertEqual(v["absent"], 0, out)
        self.assertEqual(v["not_located"], 0, out)
        self.assertEqual(v["verified"] + v["altered"], 1, out)

    def test_exact_quote_located(self):
        self.assert_located("exact")

    def test_quote_with_fillers_removed_located(self):
        self.assert_located("fillers")

    def test_quote_with_ellipsis_located(self):
        self.assert_located("ellipsis")

    def test_quote_with_bracketed_insertion_located(self):
        self.assert_located("bracket")

    def test_quote_with_smart_quotes_located(self):
        self.assert_located("smart")

    def test_light_edits_verify_under_intelligent(self):
        for key in ("exact", "fillers", "ellipsis", "bracket", "smart"):
            with self.subTest(key=key):
                rc, out, data = self.case(key)
                self.assertEqual(verification(data)["verified"], 1, out)
                self.assertEqual(rc, 0, out)

    def test_paraphrase_is_altered(self):
        rc, out, data = self.case("paraphrase")
        self.assertEqual(verification(data)["altered"], 1, out)

    def test_invented_quote_is_absent_and_clearly_lower(self):
        rc, out, data = self.case("invented")
        self.assertEqual(verification(data)["absent"], 1, out)
        self.assertEqual(rc, 1, out)
        _, _, para = self.case("paraphrase")
        r_inv = data["quotes"][0]["match_ratio"]
        r_para = para["quotes"][0]["match_ratio"]
        self.assertLess(r_inv, r_para - 0.15)

    def test_full_report_on_10k_words_runs_in_seconds(self):
        report = "# Reporting\n\n" + "\n\n".join(synth.REPORT_QUOTES.values()) + "\n"
        start = time.time()
        rc, out, err, data = run(report, self.sources)
        elapsed = time.time() - start
        self.assertLess(elapsed, 10.0, "took %.1fs" % elapsed)
        statuses = [q["status"] for q in data["quotes"]]
        self.assertEqual(statuses, ["verified"] * 5 + ["altered", "absent"], out)


class VerbatimMode(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.sources = {"session-01.txt": synth.build_transcript()}
        cls.report = "# Reporting\n\n%s\n" % synth.REPORT_QUOTES["fillers"]

    def test_intelligent_is_default_and_notes_the_edit(self):
        rc, out, err, data = run(self.report, self.sources)
        self.assertEqual(verification(data)["verified"], 1, out + err)
        notes = [f for f in checks(data, "note") if f["check"] == "quote-verification"]
        self.assertTrue(notes, out)

    def test_strict_treats_light_edits_as_altered(self):
        rc, out, err, data = run(self.report, self.sources, ["--verbatim", "strict"])
        self.assertIsNotNone(data, err)
        self.assertEqual(verification(data)["altered"], 1, out)

    def test_strict_still_verifies_an_exact_quote(self):
        report = "# Reporting\n\n%s\n" % synth.REPORT_QUOTES["exact"]
        rc, out, err, data = run(report, self.sources, ["--verbatim", "strict"])
        self.assertIsNotNone(data, err)
        self.assertEqual(verification(data)["verified"], 1, out)


class NoAccusation(unittest.TestCase):

    def test_missing_quotes_are_not_called_generated(self):
        sources = {"s.txt": synth.build_transcript(2000)}
        report = "# Reporting\n\n%s\n\n%s\n" % (
            synth.REPORT_QUOTES["invented"], synth.REPORT_QUOTES["paraphrase"])
        rc, out, err, data = run(report, sources)
        self.assertNotIn("generated rather than extracted", out)
        self.assertNotIn("few percent", out)
        self.assertNotIn("30%", out)
        self.assertIn("Not located in sources", out)


class AttributionFormats(unittest.TestCase):

    def test_attribution_stripped_and_recorded(self):
        source = ("Interviewer: Tell me about reporting.\n\n"
                  "Participant: I export the board every Friday so finance can see "
                  "which requests are still waiting on legal review.\n\n"
                  "Participant: The reminder emails arrive after the deadline has "
                  "already passed, which makes them useless for planning.\n\n"
                  "Participant: Half my week goes on chasing approvals that should "
                  "have been automatic in the first place.\n\n"
                  "Participant: I keep a private spreadsheet because the shared one "
                  "gets overwritten by whoever saved last.\n")
        report = ("# Reporting\n\n"
                  "> I export the board every Friday so finance can see which requests "
                  "are still waiting on legal review. (P1)\n\n"
                  "> The reminder emails arrive after the deadline has already passed, "
                  "which makes them useless for planning. [P2]\n\n"
                  "> Half my week goes on chasing approvals that should have been "
                  "automatic in the first place. — P3\n\n"
                  "> I keep a private spreadsheet because the shared one gets "
                  "overwritten by whoever saved last. — Participant 4\n")
        rc, out, err, data = run(report, {"s.txt": source})
        self.assertEqual(sorted(data["stats"]["quote_counts"]), ["P1", "P2", "P3", "P4"])
        v = verification(data)
        self.assertEqual(v["verified"], 4, out)
        self.assertEqual(v["altered"], 0, out)


class VttParsing(unittest.TestCase):

    def test_quote_spanning_two_cues_verifies(self):
        vtt = (FIXTURES / "two_cues.vtt").read_text(encoding="utf-8")
        report = ("# Approval\n\n> The approval screen asks me for the cost centre "
                  "every single time, even though it never changes for my team. (P1)\n")
        rc, out, err, data = run(report, {"session.vtt": vtt})
        self.assertEqual(verification(data)["verified"], 1, out)


class ReportNotItsOwnSource(unittest.TestCase):

    def test_report_inside_sources_is_skipped(self):
        report = "# Reporting\n\n%s\n" % synth.REPORT_QUOTES["invented"]
        sources = {"session-01.txt": synth.build_transcript(2000)}
        rc, out, err, data = run(report, sources, report_in_sources=True)
        v = verification(data)
        self.assertEqual(v["verified"], 0, out)
        self.assertIn("report.md", err)


class SmallSampleReporting(unittest.TestCase):

    def setUp(self):
        text = (FIXTURES / "small_sample_report.md").read_text(encoding="utf-8")
        self.rc, self.out, _, self.data = run(text, None, ["--n", "8"])

    def flagged_lines(self):
        return {f["line"] for f in self.data["findings"]
                if f["check"] in ("interval", "small-sample")}

    def test_raw_count_not_flagged(self):
        self.assertNotIn(3, self.flagged_lines(), self.out)

    def test_dates_and_24_7_not_read_as_fractions(self):
        self.assertNotIn(5, self.flagged_lines(), self.out)

    def test_percentage_at_small_n_is_a_warning_to_report_a_count(self):
        hits = [f for f in self.data["findings"] if f["line"] == 7
                and f["check"] in ("interval", "small-sample")]
        self.assertEqual(len(hits), 1, self.out)
        self.assertEqual(hits[0]["severity"], "warning")
        self.assertIn("count", hits[0]["message"])
        self.assertEqual(self.rc, 0, self.out)


class Concentration(unittest.TestCase):

    REPORT = ("# Reporting\n\n"
              "> I export the board every Friday so finance can see what is waiting. (P1)\n\n"
              "> The reminders arrive after the deadline has passed, every single time. (P1)\n\n"
              "> I chase approvals for half the week and it never seems to get better. (P1)\n\n"
              "> I keep a private spreadsheet because the shared one gets overwritten. (P2)\n")

    def concentration(self, args):
        rc, out, err, data = run(self.REPORT, None, args)
        return [f for f in data["findings"] if f["check"] == "concentration"
                and "supplies" in f["message"]], out

    def test_below_five_participants_is_a_note(self):
        hits, out = self.concentration(["--n", "3"])
        self.assertEqual([f["severity"] for f in hits], ["note"], out)

    def test_five_or_more_participants_is_critical_with_neutral_wording(self):
        hits, out = self.concentration(["--n", "8"])
        self.assertEqual([f["severity"] for f in hits], ["critical"], out)
        self.assertIn("Check whether quote selection reflects the evidence base",
                      hits[0]["message"])


class DisconfirmingEvidence(unittest.TestCase):

    QUOTE = ("> I chase approvals for half the week and it never seems to get "
             "better. (P1)\n")

    def test_finding_without_disconfirming_evidence_warns(self):
        rc, out, err, data = run("# Approvals are slow\n\n" + self.QUOTE, None)
        hits = [f for f in data["findings"] if f["check"] == "disconfirming-evidence"]
        self.assertEqual(len(hits), 1, out)
        self.assertEqual(hits[0]["severity"], "warning")

    def test_finding_that_reports_a_contradiction_does_not_warn(self):
        report = ("# Approvals are slow\n\n" + self.QUOTE +
                  "\nP4 contradicted this: their approvals clear the same day.\n")
        rc, out, err, data = run(report, None)
        hits = [f for f in data["findings"] if f["check"] == "disconfirming-evidence"]
        self.assertEqual(hits, [], out)


class RecommendationBasis(unittest.TestCase):

    def test_see_is_not_a_citation(self):
        report = ("# Recommendations\n\nWe should rebuild the approval screen as a "
                  "single page, see appendix.\n")
        rc, out, err, data = run(report, None)
        hits = [f for f in data["findings"] if f["check"] == "recommendation-basis"]
        self.assertEqual(len(hits), 1, out)
        self.assertEqual(hits[0]["severity"], "warning")


class SkillExample(unittest.TestCase):
    """The example in SKILL.md is real output and its counts add up."""

    def example_block(self):
        text = SKILL_MD.read_text(encoding="utf-8")
        after = text.split("## Example", 1)[1]
        return after.split("```", 2)[1].strip("\n")

    def test_section_counts_match_items(self):
        lines = self.example_block().splitlines()
        for i, line in enumerate(lines):
            m = re.match(r"^(CRITICAL|WARNING|NOTE) \((\d+)\)$", line)
            if not m:
                continue
            items = 0
            for nxt in lines[i + 1:]:
                if not nxt.startswith("  - "):
                    break
                items += 1
            self.assertEqual(items, int(m.group(2)), line)

    def test_example_matches_script_output(self):
        ex = FIXTURES / "example"
        p = subprocess.run(
            [sys.executable, str(SCRIPT), str(ex / "readout.md"),
             "--sources", str(ex / "transcripts"), "--n", "8"],
            capture_output=True, text=True)
        self.assertEqual(p.stdout.strip("\n"), self.example_block())


if __name__ == "__main__":
    unittest.main()

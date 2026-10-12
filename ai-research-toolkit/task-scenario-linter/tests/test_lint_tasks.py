"""Regression tests for scripts/lint_tasks.py.

Run from the skill folder:  python3 -m unittest discover
Each test drives the script as a subprocess, the way a user runs it.
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
SCRIPT = SKILL / "scripts" / "lint_tasks.py"
FIXTURES = HERE / "fixtures"


def run(tasks_text, vocab_text="Approvals\nInsights\n", vocab_name="vocab.txt",
        args=()):
    """Run the linter. Returns (exit code, stdout, stderr, findings or None)."""
    with tempfile.TemporaryDirectory() as d:
        t = Path(d) / "tasks.md"
        t.write_text(tasks_text, encoding="utf-8")
        v = Path(d) / vocab_name
        v.write_text(vocab_text, encoding="utf-8")
        out = Path(d) / "out.json"
        p = subprocess.run(
            [sys.executable, str(SCRIPT), str(t), "--vocab", str(v),
             "--json", str(out)] + list(args),
            capture_output=True, text=True)
        findings = json.loads(out.read_text()) if out.exists() else None
        return p.returncode, p.stdout, p.stderr, findings


def task_count(stdout):
    for line in stdout.splitlines():
        if " task(s)" in line:
            return int(line.split()[0])
    raise AssertionError("no task count in output:\n" + stdout)


def checks(findings, task=None):
    return [(f["severity"], f["check"]) for f in findings
            if task is None or f["task"] == task]


GOOD_END = " Let me know when you're done."


class TaskSplitting(unittest.TestCase):

    def test_consecutive_bullets_are_separate_tasks(self):
        code, out, err, _ = run(
            "- You need to approve a budget request." + GOOD_END + "\n"
            "- You want to see last month's results." + GOOD_END + "\n"
            "- You're planning next week's sessions." + GOOD_END + "\n")
        self.assertEqual(task_count(out), 3, out)

    def test_task_n_headings_are_separate_tasks(self):
        code, out, err, _ = run(
            "## Task 1\n\nYou need to approve a budget request." + GOOD_END + "\n\n"
            "## Task 2\n\nYou want to see last month's results." + GOOD_END + "\n")
        self.assertEqual(task_count(out), 2, out)

    def test_task_n_colon_on_its_own_line(self):
        code, out, err, _ = run(
            "Task 1:\nYou need to approve a budget request." + GOOD_END + "\n"
            "Task 2:\nYou want to see last month's results." + GOOD_END + "\n")
        self.assertEqual(task_count(out), 2, out)

    def test_repeated_numbers_do_not_merge_findings(self):
        code, out, err, findings = run(
            "1. Click Approvals.\n\n"
            "1. You want to see last month's Insights." + GOOD_END + "\n")
        self.assertEqual(task_count(out), 2, out)
        # Each task keeps its own findings, under its own position.
        self.assertEqual({f["task"] for f in findings}, {1, 2}, findings)
        self.assertEqual(out.count('label "Approvals"'), 1, out)
        self.assertEqual(out.count('label "Insights"'), 1, out)

    def test_unnumbered_file_is_one_task(self):
        code, out, err, _ = run(
            "You need to approve a budget request.\n"
            "Let me know when you're done.\n")
        self.assertEqual(task_count(out), 1, out)


class Vocabulary(unittest.TestCase):

    def test_plural_label_matches_singular_text(self):
        _, _, _, findings = run("1. You need the latest report." + GOOD_END,
                                vocab_text="Reports\n")
        self.assertIn(("critical", "ui-vocabulary"), checks(findings))

    def test_singular_label_matches_plural_text(self):
        _, _, _, findings = run("1. You need the latest reports." + GOOD_END,
                                vocab_text="Report\n")
        self.assertIn(("critical", "ui-vocabulary"), checks(findings))

    def test_label_starting_with_symbol(self):
        _, _, _, findings = run(
            "1. You want to add participant details." + GOOD_END,
            vocab_text="+ Add Participant\n")
        self.assertIn(("critical", "ui-vocabulary"), checks(findings))

    def test_plus_new_label_is_found(self):
        _, _, _, findings = run("1. You need a new survey." + GOOD_END,
                                vocab_text="+ New\n")
        self.assertIn("ui-vocabulary", [c for _, c in checks(findings)])

    def test_common_single_word_label_is_warning(self):
        for word in ("Home", "Help", "Search", "Settings"):
            text = "1. You need %s with an invoice." % word.lower() + GOOD_END
            code, out, _, findings = run(text, vocab_text=word + "\n")
            self.assertIn(("warning", "ui-vocabulary"), checks(findings), word)
            self.assertNotIn(("critical", "ui-vocabulary"), checks(findings), word)
            self.assertEqual(code, 0, out)

    def test_allow_terms_skips_intentional_labels(self):
        code, out, err, findings = run(
            "1. You need to clear the Approvals queue." + GOOD_END,
            args=["--allow-terms", "Approvals"])
        self.assertEqual(code, 0, out + err)
        self.assertNotIn("ui-vocabulary", [c for _, c in checks(findings)])

    def test_allow_terms_is_plural_insensitive(self):
        code, out, err, findings = run(
            "1. You need to clear the approval." + GOOD_END,
            args=["--allow-terms", "Approvals,Insights"])
        self.assertEqual(code, 0, out + err)


class Language(unittest.TestCase):

    def test_easy_is_priming(self):
        _, _, _, findings = run("1. You need a budget. It's easy." + GOOD_END)
        self.assertIn(("warning", "priming"), checks(findings))

    def test_hypothetical_wording(self):
        for phrase in ("How would you approve a budget?",
                       "Show me how you would approve a budget."):
            _, _, _, findings = run("1. You need sign-off. " + phrase + GOOD_END)
            self.assertIn(("warning", "hypothetical"), checks(findings), phrase)

    def test_contracted_context_is_recognised(self):
        for opener in ("You'd like to book a room.",
                       "You've just moved teams.",
                       "You're planning a trip."):
            _, _, _, findings = run("1. " + opener + GOOD_END)
            self.assertNotIn("no-context", [c for _, c in checks(findings)], opener)

    def test_youve_just_is_not_priming(self):
        _, _, _, findings = run("1. You've just moved teams." + GOOD_END)
        self.assertNotIn("priming", [c for _, c in checks(findings)])

    def test_and_then_is_flagged(self):
        _, _, _, findings = run(
            "1. You need a budget approved and then sent to finance." + GOOD_END)
        self.assertIn(("warning", "multiple-tasks"), checks(findings))

    def test_length_is_labelled_heuristic(self):
        long_task = "1. You need " + "a very long task " * 20 + "." + GOOD_END
        _, out, _, findings = run(long_task)
        msgs = [f["message"] for f in findings if f["check"] == "length"]
        self.assertTrue(msgs and "heuristic" in msgs[0].lower(), findings)


class StudyType(unittest.TestCase):
    TASK = "1. You need a budget approved.\n"

    def end_state(self, *args):
        code, out, err, findings = run(self.TASK, args=list(args))
        self.assertIsNotNone(findings, err)
        return [s for s, c in checks(findings) if c == "no-success-criteria"]

    def test_qual_missing_end_state_is_warning(self):
        self.assertEqual(self.end_state("--study-type", "qual",
                                        "--mode", "unmoderated"), ["warning"])

    def test_moderated_qual_missing_end_state_is_warning(self):
        self.assertEqual(self.end_state("--study-type", "qual",
                                        "--mode", "moderated"), ["warning"])

    def test_quant_missing_end_state_is_critical(self):
        self.assertEqual(self.end_state("--study-type", "quant"), ["critical"])

    def test_tree_has_no_end_state_check(self):
        self.assertEqual(self.end_state("--study-type", "tree"), [])


class InputErrors(unittest.TestCase):

    def test_empty_tasks_file_exits_non_zero(self):
        code, out, err, _ = run("")
        self.assertNotEqual(code, 0, out)
        self.assertIn("no tasks", err)

    def test_json_vocab_with_non_string_value(self):
        code, out, err, _ = run("1. You need a budget." + GOOD_END,
                                vocab_text='{"nav": 5}', vocab_name="v.json")
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)
        self.assertIn("error:", err)

    def test_json_vocab_list_with_non_strings(self):
        code, out, err, _ = run("1. You need a budget." + GOOD_END,
                                vocab_text='["Approvals", 3, null]',
                                vocab_name="v.json")
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)
        self.assertIn("non-string", err)

    def test_invalid_json_vocab(self):
        code, out, err, _ = run("1. You need a budget." + GOOD_END,
                                vocab_text='{"nav": [', vocab_name="v.json")
        self.assertNotEqual(code, 0)
        self.assertNotIn("Traceback", err)


class WorkedExample(unittest.TestCase):
    """The counts in SKILL.md's worked example must match the script."""

    def test_summary_line_matches_skill_md(self):
        p = subprocess.run(
            [sys.executable, str(SCRIPT),
             str(FIXTURES / "worked_example_tasks.md"),
             "--vocab", str(FIXTURES / "worked_example_vocab.txt"),
             "--mode", "unmoderated", "--study-type", "quant"],
            capture_output=True, text=True)
        summary = [ln for ln in p.stdout.splitlines()
                   if ln.endswith(" note") and "critical" in ln]
        self.assertEqual(len(summary), 1, p.stdout + p.stderr)
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn(summary[0], skill_md)
        self.assertEqual(p.returncode, 1)

    def test_qual_counts_quoted_in_skill_md(self):
        p = subprocess.run(
            [sys.executable, str(SCRIPT),
             str(FIXTURES / "worked_example_tasks.md"),
             "--vocab", str(FIXTURES / "worked_example_vocab.txt"),
             "--mode", "unmoderated", "--study-type", "qual"],
            capture_output=True, text=True)
        self.assertIn("5 critical, 9 warning, 0 note", p.stdout)
        skill_md = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("5 critical, 9 warning", skill_md)


if __name__ == "__main__":
    unittest.main()

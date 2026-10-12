"""Regression tests for scripts/sample_size.py. Run: python3 -m unittest discover"""

import os
import subprocess
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, os.pardir, "scripts", "sample_size.py")
FIXTURES = os.path.join(HERE, "fixtures")


def run(*args):
    proc = subprocess.run([sys.executable, SCRIPT] + list(args),
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          universal_newlines=True)
    return proc.returncode, proc.stdout, proc.stderr


def load_module():
    sys.path.insert(0, os.path.join(HERE, os.pardir, "scripts"))
    try:
        import sample_size  # noqa: E402
        return sample_size
    finally:
        sys.path.pop(0)


class TestTCriticalValues(unittest.TestCase):
    def test_against_table_values(self):
        mod = load_module()
        self.assertTrue(hasattr(mod, "t_quantile"), "no stdlib inverse-t")
        for prob, df, expected in [(0.975, 7, 2.365), (0.975, 1, 12.706),
                                   (0.975, 30, 2.042), (0.995, 10, 3.169),
                                   (0.95, 20, 1.725)]:
            self.assertAlmostEqual(mod.t_quantile(prob, df), expected, places=3)


class TestTimes(unittest.TestCase):
    def test_log_interval_uses_t(self):
        code, out, _ = run("times", "32", "41", "38", "45", "210", "36", "40", "39")
        self.assertEqual(code, 0)
        self.assertIn("28.7 to 79.2", out)


class TestProportion(unittest.TestCase):
    def test_adjusted_wald_planning_correction_gives_39(self):
        code, out, _ = run("proportion", "--margin", "0.15")
        self.assertEqual(code, 0)
        self.assertIn("n = 39", out)

    def test_margin_table_uses_expected(self):
        code, out, _ = run("proportion", "--margin", "0.10", "--expected", "0.2")
        self.assertEqual(code, 0)
        self.assertIn("assuming p=0.2", out)
        # z*sqrt(0.2*0.8/(40+z^2)) = 0.1185 -> +/-12, not the p=0.5 value of 15
        self.assertRegex(out, r"n=40\s+\+/-12 points")

    def test_margin_table_states_default_assumption(self):
        _, out, _ = run("proportion")
        self.assertIn("assuming p=0.5", out)


class TestPlanSurvey(unittest.TestCase):
    def test_no_literal_double_percent(self):
        code, out, _ = run("plan", "survey")
        self.assertEqual(code, 0)
        self.assertNotIn("%%", out)
        self.assertIn("worst-case 50% split", out)


class TestPlanInterviews(unittest.TestCase):
    def test_four_segments(self):
        code, out, _ = run("plan", "interviews", "--segments", "4")
        self.assertEqual(code, 0, out)
        self.assertIn("9-17 interviews per segment", out)
        self.assertIn("36-68 interviews in total", out)
        self.assertIn("Hennink & Kaiser (2022)", out)
        self.assertIn("Hennink, Kaiser & Marconi (2017)", out)
        self.assertIn("counts of participants, not percentages", out)

    def test_focus_groups(self):
        code, out, _ = run("plan", "interviews", "--method", "focus-groups",
                           "--segments", "2")
        self.assertEqual(code, 0, out)
        self.assertIn("4-8 focus groups per segment", out)
        self.assertIn("8-16 focus groups in total", out)

    def test_goal_understanding(self):
        _, out, _ = run("plan", "interviews", "--goal", "understanding",
                        "--segments", "2")
        self.assertIn("16-24 per segment", out)
        self.assertIn("32-48 in total", out)

    def test_reflexive_ta_offers_information_power(self):
        code, out, _ = run("plan", "interviews", "--approach", "reflexive-ta")
        self.assertEqual(code, 0, out)
        self.assertIn("Braun & Clarke", out)
        self.assertIn("information power", out)
        for factor in ("Aim", "Sample specificity", "Theory", "Dialogue quality",
                       "Analysis strategy"):
            self.assertIn(factor, out)
        self.assertIn("budgeting", out)
        self.assertIn("counts of participants, not percentages", out)

    def test_qual_options_rejected_elsewhere(self):
        code, _, err = run("plan", "survey", "--segments", "3")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class TestSaturation(unittest.TestCase):
    def check(self, fixture):
        code, out, err = run("saturation", os.path.join(FIXTURES, fixture))
        self.assertEqual(code, 0, err)
        self.assertIn("Unique themes in the base: 8", out)
        self.assertIn("interviews 5-6   1 new   12%", out)
        self.assertIn("First met in the run covering interviews 6-7", out)
        self.assertIn("Last run (interviews 7-8): 0% new information. Threshold met",
                      out)
        self.assertIn("one stopping rule", out.lower())
        self.assertIn("Guest, Namey & Chen (2020)", out)

    def test_wide_csv(self):
        self.check("saturation_wide.csv")

    def test_long_csv(self):
        self.check("saturation_long.csv")

    def test_json(self):
        self.check("saturation.json")

    def test_threshold_configurable(self):
        _, out, _ = run("saturation", os.path.join(FIXTURES, "saturation_wide.csv"),
                        "--threshold", "0.15")
        self.assertIn("First met in the run covering interviews 5-6", out)

    def test_too_few_interviews(self):
        code, _, err = run("saturation",
                           os.path.join(FIXTURES, "saturation_too_short.csv"))
        self.assertEqual(code, 2)
        self.assertIn("needs at least 6", err)
        self.assertNotIn("Traceback", err)

    def test_missing_file(self):
        code, _, err = run("saturation", os.path.join(FIXTURES, "nope.csv"))
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class TestInputValidation(unittest.TestCase):
    CASES = [
        ("discover", "--problem-frequency", "1.5"),
        ("discover", "--problem-frequency", "0"),
        ("discover", "--n", "0"),
        ("proportion", "--margin", "15"),
        ("proportion", "--margin", "0"),
        ("proportion", "--expected", "0"),
        ("proportion", "--expected", "1.5"),
        ("interval", "1", "0"),
        ("interval", "3", "2"),
        ("plan", "formative-usability", "--target", "1.2"),
        ("plan", "formative-usability", "--problem-frequency", "-0.2"),
        ("plan", "interviews", "--segments", "0"),
        ("times", "30", "-4", "20"),
    ]

    def test_bad_inputs_exit_2_without_traceback(self):
        for case in self.CASES:
            with self.subTest(case=case):
                code, out, err = run(*case)
                self.assertEqual(code, 2, "exit %d for %r: %s" % (code, case, out))
                self.assertNotIn("Traceback", err)
                self.assertIn("error:", err)
                self.assertNotIn("n = 0", out)

    def test_margin_percentage_hint(self):
        _, _, err = run("proportion", "--margin", "15")
        self.assertIn("did you mean 0.15?", err.lower())


class TestCitationWording(unittest.TestCase):
    def test_faulkner_and_spool(self):
        _, out, _ = run("discover")
        self.assertNotIn("bottom half", out)
        self.assertIn("85% of known problems on average", out)
        self.assertIn("worst set found 55%", out)
        self.assertIn("35% discovery at 5 users", out)

    def test_estimated_frequency_flagged_as_inflated(self):
        _, out, _ = run("discover")
        self.assertIn("Lewis (2001)", out)


if __name__ == "__main__":
    unittest.main()

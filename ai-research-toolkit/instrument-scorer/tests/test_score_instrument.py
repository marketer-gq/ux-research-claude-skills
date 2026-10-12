"""Regression tests for scripts/score_instrument.py.

Run from the skill folder:  python3 -m unittest discover
All fixtures in tests/fixtures/ are synthetic.
"""

import importlib.util
import re
import subprocess
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parent / "scripts" / "score_instrument.py"
FIX = HERE / "fixtures"


def run(*args):
    p = subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                       capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def load_module():
    spec = importlib.util.spec_from_file_location("score_instrument", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class TCriticalValues(unittest.TestCase):
    def test_against_table(self):
        mod = load_module()
        for conf, df, want in ((0.95, 9, 2.262), (0.95, 2, 4.303),
                               (0.95, 30, 2.042), (0.90, 5, 2.015),
                               (0.99, 4, 4.604)):
            self.assertAlmostEqual(mod.t_crit(conf, df), want, places=3)


class SusScoring(unittest.TestCase):
    def test_t_interval_not_z(self):
        # scores 75, 100, 80: mean 85, t(0.975, 2) = 4.303 -> 52.1 to 100 (clamped)
        code, out, _ = run("sus", FIX / "sus_basic.csv")
        self.assertIn("85.0", out)
        self.assertIn("52.1 to 100.0", out)

    def test_interval_clamped_to_scale(self):
        code, out, _ = run("sus", FIX / "sus_near_ceiling.csv")
        m = re.search(r"interval\s+([\d.]+) to ([\d.]+)", out)
        self.assertIsNotNone(m, out)
        self.assertLessEqual(float(m.group(2)), 100.0)

    def test_no_per_respondent_grades(self):
        code, out, _ = run("sus", FIX / "sus_basic.csv", "--per-respondent")
        section = out.split("PER RESPONDENT", 1)[1].split("\n\n", 1)[0]
        rows = [ln for ln in section.splitlines()[1:] if ln.strip()]
        self.assertEqual(len(rows), 3)
        for ln in rows:
            self.assertRegex(ln, r"^\s+\d+\s+[\d.]+\s*$")
        self.assertIn("grade of mean", out)

    def test_positive_version(self):
        code, out, _ = run("sus", FIX / "sus_positive.csv", "--positive")
        self.assertEqual(code, 0, out)
        self.assertIn("87.5", out)  # all-5s = 100, all-4s = 75
        self.assertNotIn("POSSIBLE INCONSISTENCIES", out)

    def test_dropped_item_rescaled(self):
        code, out, _ = run("sus", FIX / "sus_drop4.csv", "--drop-item", 4)
        self.assertEqual(code, 0, out)
        self.assertIn("75.0", out)  # 27 x 100/36
        self.assertIn("Lewis & Sauro", out)


class CarelessResponding(unittest.TestCase):
    def test_all_threes_not_flagged_and_wording(self):
        code, out, _ = run("sus", FIX / "sus_straightline.csv")
        self.assertEqual(code, 1)
        self.assertIn("POSSIBLE INCONSISTENCIES (1)", out)
        self.assertNotIn("row 1:", out)
        self.assertIn("row 2:", out)
        self.assertNotIn("RESPONSE ERRORS", out)
        self.assertIn("Meade & Craig", out)
        # the two Sauro & Lewis statistics are separate claims
        self.assertIn("3 of 27", out)
        self.assertIn("21 of 158", out)
        self.assertNotIn("27 SUS datasets and found participant errors", out)


class OtherInstruments(unittest.TestCase):
    def test_umux_raw_primary_no_overstates(self):
        code, out, _ = run("umux-lite", FIX / "umux.csv")
        self.assertEqual(code, 0)
        self.assertNotIn("overstates", out)
        self.assertIn("raw score (primary)", out)
        self.assertIn("interpolation", out)
        self.assertIn("65.4", out)

    def test_seq_benchmark(self):
        code, out, _ = run("seq", FIX / "seq.csv")
        self.assertIn("5.5", out)
        self.assertIn("measuringu.com/seq10", out)

    def test_range_errors_say_1_to_7(self):
        for cmd, f in (("umux-lite", "umux_out_of_range.csv"),
                       ("seq", "seq_out_of_range.csv")):
            code, out, err = run(cmd, FIX / f)
            self.assertEqual(code, 2)
            self.assertIn("1-7", err)


class InputHandling(unittest.TestCase):
    def test_first_row_with_id_is_data(self):
        code, out, _ = run("sus", FIX / "sus_id_no_header.csv")
        self.assertIn("n = 2", out)

    def test_numeric_header_is_not_a_respondent(self):
        code, out, err = run("sus", FIX / "sus_numeric_header.csv")
        self.assertIn("n = 2", out, err)

    def test_json_with_id_key(self):
        code, out, err = run("sus", FIX / "sus_with_id.json")
        self.assertNotIn("Traceback", err)
        self.assertIn("n = 2", out)
        self.assertIn("87.5", out)

    def test_tlx_columns_matched_by_header(self):
        code, out, _ = run("tlx", FIX / "tlx_reordered_header.csv")
        self.assertRegex(out, r"mental demand\s+10\.0")
        self.assertRegex(out, r"frustration\s+70\.0")

    def test_wrong_item_count_is_fatal_exit_2(self):
        code, out, err = run("sus", FIX / "sus_short_row.csv")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)


class Validate(unittest.TestCase):
    def test_missing_file_friendly(self):
        code, out, err = run("validate", FIX / "does_not_exist.txt")
        self.assertEqual(code, 2)
        self.assertNotIn("Traceback", err)
        self.assertIn("no such file", err)

    def test_seven_point_sus_is_warning(self):
        code, out, _ = run("validate", FIX / "sus_canonical.txt", "--points", 7)
        self.assertEqual(code, 0, out)
        self.assertIn("WARNING", out)
        self.assertNotIn("BLOCKER", out)

    def test_dropped_item_allowed(self):
        code, out, _ = run("validate", FIX / "sus_dropped_item4.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("--drop-item 4", out)
        self.assertNotIn("ALTERED", out)

    def test_possessive_product(self):
        code, out, _ = run("validate", FIX / "umux_possessive.txt",
                           "--instrument", "umux-lite")
        self.assertEqual(code, 0, out)
        self.assertIn("system -> product", out)

    def test_multiword_product_name(self):
        code, out, _ = run("validate", FIX / "sus_multiword_product.txt")
        self.assertEqual(code, 0, out)
        self.assertIn("system -> Acme Cloud", out)
        self.assertIn("cumbersome -> awkward", out)

    def test_altered_reworded_item_still_caught(self):
        code, out, _ = run("validate", FIX / "umux_altered.txt",
                           "--instrument", "umux-lite")
        self.assertEqual(code, 1)
        self.assertIn("ALTERED", out)
        # instrument-specific message, no SUS benchmark wording
        self.assertNotIn("68", out)
        self.assertNotIn("grade curve", out)


if __name__ == "__main__":
    unittest.main()

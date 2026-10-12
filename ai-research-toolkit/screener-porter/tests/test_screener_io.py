"""Regression tests for scripts/screener_io.py. Plain unittest, stdlib only.

Run from the skill folder:  python3 -m unittest discover
All fixtures are synthetic.
"""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"
SCRIPT = HERE.parent / "scripts" / "screener_io.py"

_spec = importlib.util.spec_from_file_location("screener_io", str(SCRIPT))
sio = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(sio)


def run_cli(*args):
    return subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True)


def q(qid, text, qtype="single_choice", options=None, attribute="attr",
      qualify=None, disqualify=None, **extra):
    item = {"id": qid, "text": text, "type": qtype,
            "options": options if options is not None else ["A", "B", "C"],
            "required": True, "attribute": attribute,
            "qualify_if": qualify or [], "disqualify_if": disqualify or []}
    item["open_ended"] = qtype in sio.OPEN_ENDED_TYPES
    item.update(extra)
    return item


def screener(questions, **extra):
    p = {"version": 1, "name": "test", "study_type": "",
         "attribute_mapping_in_source": True, "questions": questions,
         "privacy_notice": "https://example.com/privacy"}
    p.update(extra)
    return p


def check(portable, **rules):
    r = dict(sio.DEFAULT_RULES)
    r.update(rules)
    return sio.check_screener(portable, r, {"entries": []})


def all_messages(rep):
    return rep.blockers + rep.warnings + rep.notes


class LeadingWording(unittest.TestCase):
    def wording_flags(self, text):
        rep = check(screener([q("x1", text, disqualify=["C"])]))
        return [w for w in rep.warnings if w.startswith("x1 wording")]

    def test_proper_nouns_with_great_pass(self):
        self.assertEqual(self.wording_flags("Have you used Great Question before?"), [])
        self.assertEqual(self.wording_flags("Have you lived in Great Britain?"), [])

    def test_evaluative_adjective_describing_the_thing_is_flagged(self):
        self.assertTrue(self.wording_flags("How great was your last onboarding?"))
        self.assertTrue(self.wording_flags("Was the new dashboard amazing?"))


class Thresholds(unittest.TestCase):
    def test_two_open_ended_questions_are_within_default(self):
        self.assertEqual(sio.DEFAULT_RULES["max_open_ended"], 2)
        qs = [q("o1", "Describe your week.", "long_text", options=[]),
              q("o2", "Describe your team.", "long_text", options=[])]
        rep = check(screener(qs))
        self.assertFalse([w for w in rep.warnings if "open-ended questions" in w])

    def test_question_count_is_a_warning_not_a_blocker(self):
        qs = [q("q%d" % i, "Which plan are you on %d?" % i, disqualify=["C"])
              for i in range(12)]
        rep = check(screener(qs))
        self.assertEqual(rep.blockers, [])
        self.assertTrue([w for w in rep.warnings if "12 questions, limit is 10" in w])

    def test_unmapped_attribute_is_a_warning_by_default(self):
        rep = check(screener([q("u1", "Which plan are you on?", attribute=None,
                                disqualify=["C"])]))
        self.assertEqual(rep.blockers, [])
        self.assertTrue([w for w in rep.warnings if "no attribute mapping" in w])

    def test_screener_only_tag_is_not_flagged(self):
        rep = check(screener([q("s1", "Which plan are you on?",
                                attribute="screener-only", disqualify=["C"])]))
        self.assertFalse([m for m in all_messages(rep) if "no attribute mapping" in m])

    def test_blocker_policy_still_available(self):
        rep = check(screener([q("u1", "Which plan are you on?", attribute=None,
                                disqualify=["C"])]),
                    unmapped_attribute_policy="blocker")
        self.assertTrue(rep.blockers)


class Ordering(unittest.TestCase):
    def test_demographic_with_screening_logic_is_a_qualifier(self):
        qs = [q("d1", "Which country do you live in?", options=["UK", "US", "Other"],
                disqualify=["Other"]),
              q("d2", "Which plan are you on?", disqualify=["C"])]
        rep = check(screener(qs))
        self.assertFalse([w for w in rep.warnings if "Demographic question" in w])

    def test_plain_demographic_before_qualifier_still_flagged(self):
        qs = [q("d1", "What is your gender?", options=["Woman", "Man", "Prefer not to say"]),
              q("d2", "Which plan are you on?", disqualify=["C"])]
        rep = check(screener(qs))
        self.assertTrue([w for w in rep.warnings if "Demographic question(s) d1" in w])


class NewChecks(unittest.TestCase):
    def test_yes_no_question_warns(self):
        rep = check(screener([q("y1", "Do you manage a team?", "yes_no",
                                options=["Yes", "No"], qualify=["Yes"])]))
        self.assertTrue([w for w in rep.warnings if w.startswith("Yes/no question(s) y1")])

    def test_special_category_warns(self):
        rep = check(screener([q("h1", "Do you have a long-term health condition?",
                                options=["Yes", "No", "Prefer not to say"],
                                disqualify=["No"])]))
        self.assertTrue([w for w in rep.warnings if "Article 9" in w and "h1" in w])

    def test_missing_privacy_notice_warns(self):
        p = screener([q("p1", "Which plan are you on?", disqualify=["C"])])
        del p["privacy_notice"]
        rep = check(p)
        self.assertTrue([w for w in rep.warnings if "privacy notice" in w.lower()])

    def test_privacy_text_in_helper_counts(self):
        p = screener([q("p1", "Which plan are you on?", disqualify=["C"],
                        helper="See our privacy notice before answering.")])
        del p["privacy_notice"]
        rep = check(p)
        self.assertFalse([w for w in rep.warnings if "No privacy notice" in w])

    def test_sensitive_demographic_without_prefer_not_to_say_warns(self):
        rep = check(screener([q("g1", "What is your gender?",
                                options=["Woman", "Man", "Non-binary"])]))
        self.assertTrue([w for w in rep.warnings if "Prefer not to say" in w and "g1" in w])

    def test_interview_without_articulation_question_warns(self):
        rep = check(screener([q("i1", "Which plan are you on?", disqualify=["C"])],
                             study_type="video_call"))
        self.assertTrue([w for w in rep.warnings if "articulation question" in w])


class Export(unittest.TestCase):
    def export(self, src, *extra):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "out.json"
            res = run_cli("export", src, "-o", out, *extra)
            self.assertEqual(res.returncode, 0, res.stderr)
            return json.loads(out.read_text(encoding="utf-8")), res

    def test_jsonapi_list(self):
        p, _ = self.export(FIXTURES / "jsonapi_list.json")
        self.assertEqual([x["id"] for x in p["questions"]], ["101", "102"])
        self.assertEqual(p["questions"][0]["type"], "single_choice")
        self.assertEqual(p["questions"][0]["disqualify_if"], ["Student"])

    def test_option_level_disqualify_flags_kept(self):
        p, _ = self.export(FIXTURES / "foreign_export.json")
        by_id = {x["id"]: x for x in p["questions"]}
        self.assertEqual(by_id["f2"]["disqualify_if"], ["Ledgerly", "None of these"])
        self.assertEqual(by_id["f4"]["disqualify_if"], ["None"])
        self.assertEqual(by_id["f4"]["qualify_if"], ["6 or more"])
        self.assertEqual(by_id["f1"]["qualify_if"], ["Yes"])

    def test_csv_import(self):
        p, _ = self.export(FIXTURES / "screener.csv")
        self.assertEqual(len(p["questions"]), 2)
        c1, c2 = p["questions"]
        self.assertEqual(c1["options"], ["Weekly", "Monthly", "Never"])
        self.assertEqual(c1["disqualify_if"], ["Never"])
        self.assertEqual(c1["attribute"], "expense_frequency")
        self.assertTrue(c1["required"])
        self.assertFalse(c2["required"])
        self.assertTrue(c2["open_ended"])
        self.assertTrue(p["attribute_mapping_in_source"])

    def test_export_accepts_study_style_values(self):
        p, _ = self.export(FIXTURES / "jsonapi_list.json", "--study-type", "video_call")
        self.assertEqual(p["study_type"], "interview")


class GQPlan(unittest.TestCase):
    def plan(self, portable, *extra):
        with tempfile.TemporaryDirectory() as d:
            src = Path(d) / "s.json"
            src.write_text(json.dumps(portable), encoding="utf-8")
            out = Path(d) / "plan.json"
            res = run_cli("plan", src, "-o", out, *extra)
            plan = json.loads(out.read_text(encoding="utf-8")) if out.exists() else None
            return plan, res

    def foreign_portable(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "s.json"
            res = run_cli("export", FIXTURES / "foreign_export.json", "-o", out)
            self.assertEqual(res.returncode, 0, res.stderr)
            return json.loads(out.read_text(encoding="utf-8"))

    def test_gq_plan_maps_types_and_carries_attributes(self):
        plan, res = self.plan(self.foreign_portable(), "--target", "gq",
                              "--study-type", "interview", "--study-id", "123")
        self.assertEqual(res.returncode, 0, res.stderr)
        steps = {s["step"]: s for s in plan["steps"]}
        f1, f2, f3, f4 = steps[2], steps[3], steps[4], steps[5]
        self.assertEqual(f1["arguments"]["question_type"], "yes_no")
        self.assertEqual(f1["arguments"]["options"], [])
        self.assertEqual(f2["arguments"]["question_type"], "multiple_choice")
        self.assertEqual(f2["arguments"]["disqualifying_answers"],
                         ["Ledgerly", "None of these"])
        self.assertEqual(f1["attribute"], "manages_budget")
        self.assertEqual(f2["attribute"], "tools_used")
        # Never pass through a type Great Question has not been seen to accept.
        for s in plan["steps"][1:]:
            self.assertIn(s["arguments"]["question_type"],
                          sio.GQ_QUESTION_TYPES | {None})
        self.assertIsNone(f3["arguments"]["question_type"])
        self.assertTrue(any("matrix" in p for p in f3["preconditions"]))
        # Dropped skip logic is reported.
        self.assertTrue(any("skip_logic" in w for w in f4.get("warnings", [])))
        self.assertTrue(any("skip_logic" in w for w in plan.get("warnings", [])))
        self.assertIn("skip_logic", res.stdout)

    def test_non_integer_study_id_gives_friendly_error(self):
        plan, res = self.plan(screener([q("a", "Which plan?")]), "--target", "gq",
                              "--study-type", "interview", "--study-id", "abc")
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("--study-id", res.stderr)
        self.assertNotIn("Traceback", res.stderr)


class WorkedExample(unittest.TestCase):
    def test_worked_example_has_six_questions_and_no_blockers(self):
        p = json.loads((FIXTURES / "worked_example.json").read_text(encoding="utf-8"))
        self.assertEqual(len(p["questions"]), 6)
        rep = check(copy.deepcopy(p))
        self.assertEqual(rep.blockers, [])
        self.assertTrue([w for w in rep.warnings if "4 question(s) with no attribute" in w])


if __name__ == "__main__":
    unittest.main()

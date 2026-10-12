"""Regression tests for scripts/attribute_clean.py. All fixtures are synthetic.

Run from the skill folder:  python3 -m unittest discover
Set PDS_SCRIPT to point the tests at a different copy of the script.
"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = Path(os.environ.get("PDS_SCRIPT", HERE.parent / "scripts" / "attribute_clean.py"))
FIX = HERE / "fixtures"


def run(*args):
    return subprocess.run([sys.executable, str(SCRIPT)] + [str(a) for a in args],
                          capture_output=True, text=True)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def cluster(self, fixture, attribute, *extra):
        out = self.dir / ("%s.json" % attribute.replace(" ", "_"))
        r = run("cluster", FIX / fixture, "--attribute", attribute, "-o", out, *extra)
        self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
        return json.loads(out.read_text()), out

    def groups(self, proposal):
        entries = proposal["clusters"] + proposal.get("orphans", [])
        return [set(v["value"] for v in c["variants"]) for c in entries]

    def assertApart(self, proposal, a, b):
        for g in self.groups(proposal):
            self.assertFalse(a in g and b in g, "%r and %r were merged" % (a, b))

    def assertTogether(self, proposal, *values):
        self.assertTrue(any(set(values) <= g for g in self.groups(proposal)),
                        "%r were not merged" % (values,))


class FalseMerges(Base):
    PAIRS = [
        ("employment", "Employed", "Unemployed"),
        ("employment", "Active", "Inactive"),
        ("employment", "Full-time", "Part-time"),
        ("satisfaction", "Satisfied", "Dissatisfied"),
        ("skill", "C++ Developer", "C# Developer"),
        ("company_size", "100-500", "1000-5000"),
        ("country", "Austria", "Australia"),
        ("country", "Niger", "Nigeria"),
        ("country", "Ireland", "Iceland"),
        # Same countries under an attribute name that is not geographic.
        ("origin", "Austria", "Australia"),
        ("origin", "Niger", "Nigeria"),
        ("origin", "Ireland", "Iceland"),
    ]

    def test_never_merged_at_default_or_loose_threshold(self):
        for threshold in ("0.88", "0.70"):
            for attribute, a, b in self.PAIRS:
                with self.subTest(threshold=threshold, pair=(a, b)):
                    proposal, _ = self.cluster("false_merges.json", attribute,
                                               "--threshold", threshold)
                    self.assertApart(proposal, a, b)

    def test_product_manager_still_merges(self):
        proposal, _ = self.cluster("false_merges.json", "role")
        self.assertTogether(proposal, "Product Manager", "product manager", "PM")

    def test_default_threshold_is_088(self):
        proposal, _ = self.cluster("false_merges.json", "role")
        self.assertEqual(proposal["threshold"], 0.88)

    def test_same_iso_code_groups_in_geographic_attribute(self):
        proposal, _ = self.cluster("false_merges.json", "country")
        self.assertTogether(proposal, "UK", "United Kingdom")


class Approval(Base):
    def test_plan_refuses_without_approved(self):
        _, prop = self.cluster("false_merges.json", "role")
        r = run("plan", prop, "-o", self.dir / "plan.json")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse((self.dir / "plan.json").exists())

    def test_plan_refuses_cluster_level_list(self):
        _, prop = self.cluster("false_merges.json", "role")
        legacy = self.dir / "legacy.json"
        legacy.write_text('["Product Manager"]')
        r = run("plan", prop, "--approved", legacy, "-o", self.dir / "plan.json")
        self.assertNotEqual(r.returncode, 0)

    def test_approval_is_per_variant(self):
        _, prop = self.cluster("false_merges.json", "role")
        approved = self.dir / "approved.json"
        r = run("approve", prop, "--variant", "PM", "-o", approved)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan_path = self.dir / "plan.json"
        r = run("plan", prop, "--approved", approved, "-o", plan_path)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(plan_path.read_text())
        self.assertTrue(plan["steps"])
        # Only PM was approved; "product manager" in the same cluster stays.
        self.assertEqual({s["from"] for s in plan["steps"]}, {"PM"})

    def test_blocked_merge_approved_without_editing_json(self):
        proposal, prop = self.cluster("false_merges.json", "role", "--threshold", "0.70")
        self.assertApart(proposal, "ResearchOps", "Research Operations")
        approved = self.dir / "approved.json"
        r = run("approve", prop, "--merge", "ResearchOps", "--into", "Research Operations",
                "-o", approved)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan_path = self.dir / "plan.json"
        r = run("plan", prop, "--approved", approved, "-o", plan_path)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(plan_path.read_text())
        self.assertTrue(all(s["to"] == "Research Operations" for s in plan["steps"]))
        self.assertTrue(plan["steps"])

    def test_hard_block_cannot_be_approved(self):
        _, prop = self.cluster("false_merges.json", "employment", "--threshold", "0.70")
        r = run("approve", prop, "--merge", "Unemployed", "--into", "Employed",
                "-o", self.dir / "approved.json")
        self.assertNotEqual(r.returncode, 0)

    def test_plan_has_reverse_steps(self):
        _, prop = self.cluster("false_merges.json", "role")
        approved = self.dir / "approved.json"
        run("approve", prop, "--variant", "PM", "--variant", "product manager", "-o", approved)
        plan_path = self.dir / "plan.json"
        r = run("plan", prop, "--approved", approved, "-o", plan_path)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan = json.loads(plan_path.read_text())
        self.assertEqual(len(plan["reverse_steps"]), len(plan["steps"]))
        fwd = {(s["candidate_id"], s["from"], s["to"]) for s in plan["steps"]}
        back = {(s["candidate_id"], s["to"], s["from"]) for s in plan["reverse_steps"]}
        self.assertEqual(fwd, back)


class CaseVariantNames(Base):
    def _plan(self, fixture, variants):
        _, prop = self.cluster(fixture, "role")
        approved = self.dir / "approved.json"
        args = ["approve", prop, "-o", approved]
        for v in variants:
            args += ["--variant", v]
        r = run(*args)
        self.assertEqual(r.returncode, 0, r.stderr)
        plan_path = self.dir / "plan.json"
        r = run("plan", prop, "--approved", approved, "-o", plan_path)
        self.assertEqual(r.returncode, 0, r.stderr)
        return json.loads(prop.read_text()), json.loads(plan_path.read_text())

    def test_json_writes_use_each_candidates_own_key(self):
        proposal, plan = self._plan("gq_case_variants.json", ["product manager", "PM"])
        by_cid = {s["candidate_id"]: s["attribute"] for s in plan["steps"]}
        self.assertEqual(by_cid.get("9003"), "role")
        self.assertEqual(by_cid.get("9004"), "role")
        # 9005 holds both Role and role: reported, never planned.
        self.assertNotIn("9005", by_cid)
        self.assertIn("9005", [c["candidate_id"] for c in proposal["collisions"]])

    def test_csv_writes_use_each_rows_own_column(self):
        proposal, plan = self._plan("case_variants.csv", ["product manager", "PM"])
        by_cid = {s["candidate_id"]: s["attribute"] for s in plan["steps"]}
        self.assertEqual(by_cid.get("r3"), "role")
        self.assertEqual(by_cid.get("r4"), "role")
        self.assertNotIn("r5", by_cid)
        self.assertIn("r5", [c["candidate_id"] for c in proposal["collisions"]])


class InputBugs(Base):
    def test_keys_reads_csv(self):
        r = run("keys", FIX / "case_variants.csv")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("team", r.stdout)

    def test_custom_type_beats_top_level_type(self):
        proposal, _ = self.cluster("gq_case_variants.json", "type")
        values = {v["value"] for c in proposal["clusters"] + proposal["orphans"]
                  for v in c["variants"]}
        self.assertNotIn("customer", values)
        self.assertIn("Agency", values)

    def test_keys_lists_custom_type(self):
        r = run("keys", FIX / "gq_case_variants.json")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r"\n  type\s")


class Sensitive(Base):
    def test_art9_attribute_needs_reviewer(self):
        proposal, prop = self.cluster("sensitive.json", "ethnicity")
        self.assertTrue(proposal["sensitive"])
        r = run("approve", prop, "--variant", "white british", "-o", self.dir / "a.json")
        self.assertNotEqual(r.returncode, 0)
        r = run("approve", prop, "--variant", "white british", "--reviewer", "Test Reviewer",
                "-o", self.dir / "a.json")
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_team_list_marks_attribute_sensitive(self):
        team = self.dir / "team.json"
        team.write_text('["household income"]')
        proposal, _ = self.cluster("sensitive.json", "Household Income", "--sensitive", team)
        self.assertTrue(proposal["sensitive"])


if __name__ == "__main__":
    unittest.main()

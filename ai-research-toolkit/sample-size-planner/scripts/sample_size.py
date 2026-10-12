#!/usr/bin/env python3
"""
Sample Size & Confidence Planner - compute n, and the interval that comes with it.

Subcommands:
  plan        the n rationale for a research plan, with its citation. For
              interviews and focus groups it gives a sourced starting range.
  saturation  Guest, Namey & Chen (2020) stopping rule on themes per interview
  discover    problem-discovery model: n for a target discovery rate, or the rate at n
  interval    adjusted-Wald confidence interval for a proportion at any n
  proportion  n needed for a proportion at a given confidence and margin of error
  times       how to summarise task times, with a log-transformed t interval

Every number printed carries its assumption. Stdlib only. Python 3.9+.
Bad input exits with status 2 and a one-line error, never a traceback.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
from statistics import NormalDist
from typing import Dict, List, Optional, Sequence, Tuple

CITATIONS = {
    "nielsen_landauer": (
        "Nielsen & Landauer (1993), problem-discovery model P(found) = 1-(1-p)^n"),
    "faulkner": (
        "Faulkner (2003), resampling 60 users: random sets of 5 found 85% of known "
        "problems on average, and the worst set found 55%"),
    "spool_schroeder": (
        "Spool & Schroeder (2001): roughly 35% discovery at 5 users on open-ended "
        "tasks"),
    "lewis_2001": (
        "Lewis (2001): problem frequencies estimated from a study's own first few "
        "sessions are inflated and should be adjusted before planning"),
    "nng_quant": (
        "Nielsen Norman Group: about 39 participants, rounded to 40, for a general "
        "quantitative usability study at 95% confidence and +/-15% margin of error"),
    "sauro_lewis_mean": (
        "Sauro & Lewis: geometric mean for task times below about n=25, median above"),
    "agresti_coull": (
        "Agresti & Coull (1998) adjusted-Wald interval, which holds its nominal "
        "coverage at small n where the standard Wald interval does not"),
    "hennink_kaiser_2022": (
        "Hennink & Kaiser (2022), Social Science & Medicine, systematic review of "
        "empirical saturation tests: 9-17 interviews or 4-8 focus groups for a "
        "fairly similar group with a narrow aim "
        "(https://pmc.ncbi.nlm.nih.gov/articles/PMC9359070)"),
    "hennink_2017": (
        "Hennink, Kaiser & Marconi (2017), Qualitative Health Research 27(4): code "
        "saturation (the range of issues) at about 9 interviews, meaning saturation "
        "(understanding them) at about 16-24"),
    "braun_clarke_saturation": (
        "Braun & Clarke reject saturation as a sample-size rationale for "
        "reflexive thematic analysis "
        "(https://uwe-repository.worktribe.com/output/4820803)"),
    "malterud_2016": (
        "Malterud, Siersma & Guassora (2016), Qualitative Health Research 26(13): "
        "information power"),
    "guest_2020": (
        "Guest, Namey & Chen (2020), PLOS ONE, base size, run length and "
        "new-information threshold (https://doi.org/10.1371/journal.pone.0232076)"),
}

EXIT_BAD_INPUT = 2


def fail(message: str) -> None:
    """Print a friendly error and exit 2. Never a traceback."""
    print("error: " + message, file=sys.stderr)
    sys.exit(EXIT_BAD_INPUT)


def check_unit_interval(value: float, name: str, example: str) -> None:
    """Require 0 < value < 1, with a hint when a percentage was typed instead."""
    if 0 < value < 1:
        return
    hint = ""
    if 1 < value < 100:
        hint = " Did you mean %g?" % (value / 100)
    fail("%s must be between 0 and 1, exclusive (e.g. %s).%s" % (name, example, hint))


def z_for(confidence: float) -> float:
    check_unit_interval(confidence, "--confidence", "0.95")
    return NormalDist().inv_cdf(1 - (1 - confidence) / 2)


# ------------------------------------------------------- t distribution

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta (modified Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1, a - 1
    c = 1.0
    d = 1 - qab * x / qap
    if abs(d) < tiny:
        d = tiny
    d = 1 / d
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        d = tiny if abs(d) < tiny else d
        c = 1 + aa / c
        c = tiny if abs(c) < tiny else c
        d = 1 / d
        delta = d * c
        h *= delta
        if abs(delta - 1) < 1e-14:
            break
    return h


def reg_inc_beta(a: float, b: float, x: float) -> float:
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    log_front = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                 + a * math.log(x) + b * math.log(1 - x))
    front = math.exp(log_front)
    if x < (a + 1) / (a + b + 2):
        return front * _betacf(a, b, x) / a
    return 1 - front * _betacf(b, a, 1 - x) / b


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * reg_inc_beta(df / 2, 0.5, df / (df + t * t))
    return 1 - tail if t >= 0 else tail


def t_quantile(prob: float, df: float) -> float:
    """Inverse Student t by bisection on the CDF. prob in (0.5, 1)."""
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < prob:
        hi *= 2
    for _ in range(200):
        mid = (lo + hi) / 2
        if t_cdf(mid, df) < prob:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


# ---------------------------------------------------------------- discovery

def discovery_rate(p: float, n: int) -> float:
    return 1 - (1 - p) ** n


def n_for_discovery(p: float, target: float) -> int:
    check_unit_interval(target, "--target", "0.85")
    return math.ceil(math.log(1 - target) / math.log(1 - p))


def cmd_discover(args: argparse.Namespace) -> int:
    p = args.problem_frequency
    check_unit_interval(p, "--problem-frequency", "0.31")
    if args.n is not None and args.n < 1:
        fail("--n must be at least 1")

    print("Problem-discovery model")
    print("=" * 60)
    print("Assumes every problem occurs in %.0f%% of sessions, independently."
          % (100 * p))
    print(CITATIONS["nielsen_landauer"])
    print()

    if args.n:
        rate = discovery_rate(p, args.n)
        print("At n=%d you would expect to find %.0f%% of problems occurring at "
              "%.0f%% frequency." % (args.n, 100 * rate, 100 * p))
    else:
        for target in (0.80, 0.85, 0.90, 0.95, 0.99):
            print("  %.0f%% of problems   n = %d"
                  % (100 * target, n_for_discovery(p, target)))
    print()
    print("Discovery by n at this frequency:")
    for n in (3, 5, 6, 8, 10, 12, 15, 20):
        print("  n=%-3d  %.0f%%" % (n, 100 * discovery_rate(p, n)))
    print()
    print("Read this as a planning aid, not a guarantee.")
    print("  - " + CITATIONS["faulkner"])
    print("    The average is not the outcome. Your study is one draw, and some")
    print("    draws of five find far fewer problems than the average.")
    print("  - " + CITATIONS["spool_schroeder"])
    print("    On open-ended tasks the model's assumptions break down and observed")
    print("    discovery is far lower than the curve predicts.")
    print("  - The model assumes one frequency for all problems. Real problems have")
    print("    a range, and rare ones need far more sessions than common ones.")
    print("  - If you estimated --problem-frequency from your own first sessions,")
    print("    treat it as inflated: small samples overstate p. " + CITATIONS["lewis_2001"] + ".")
    return 0


# ---------------------------------------------------------------- interval

def adjusted_wald(x: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Agresti-Coull adjusted-Wald interval. Returns (point, low, high)."""
    if n < 1:
        fail("n must be at least 1")
    if not 0 <= x <= n:
        fail("x must be between 0 and n")
    z = z_for(confidence)
    n_adj = n + z * z
    p_adj = (x + z * z / 2) / n_adj
    margin = z * math.sqrt(p_adj * (1 - p_adj) / n_adj)
    return x / n, max(0.0, p_adj - margin), min(1.0, p_adj + margin)


def cmd_interval(args: argparse.Namespace) -> int:
    point, low, high = adjusted_wald(args.x, args.n, args.confidence)
    width = high - low
    print("Proportion with a %.0f%% adjusted-Wald interval" % (100 * args.confidence))
    print("=" * 60)
    print("%d of %d = %.0f%%" % (args.x, args.n, 100 * point))
    print("  %.0f%% interval: %.1f%% to %.1f%%  (width %.0f points)"
          % (100 * args.confidence, 100 * low, 100 * high, 100 * width))
    print()
    print(CITATIONS["agresti_coull"])
    print()
    if width > 0.40:
        print("This interval is %.0f points wide. The point estimate carries almost"
              % (100 * width))
        print("no information on its own — report the interval or report the count.")
    elif width > 0.20:
        print("This interval is wide. Report it alongside the percentage; the")
        print("percentage alone will be read as more precise than it is.")
    if args.n < 30:
        print()
        print("At n=%d, prefer reporting the raw count (\"%d of %d participants\")"
              % (args.n, args.x, args.n))
        print("over a percentage. A percentage invites comparison the sample cannot")
        print("support. (The n=30 cut-off is a working default, not from the")
        print("literature.)")
    return 0


# -------------------------------------------------------------- proportion

def n_for_proportion(confidence: float, margin: float,
                     expected_p: float = 0.5) -> int:
    """n for an adjusted-Wald interval of half-width `margin`.

    The adjusted-Wald interval behaves like a Wald interval on n + z^2
    observations, so the planning n is the textbook z^2 p(1-p) / m^2 minus z^2.
    """
    check_unit_interval(margin, "--margin", "0.15")
    check_unit_interval(expected_p, "--expected", "0.5")
    z = z_for(confidence)
    return max(1, math.ceil(z * z * expected_p * (1 - expected_p) / (margin * margin)
                            - z * z))


def margin_at(n: int, confidence: float, expected_p: float) -> float:
    z = z_for(confidence)
    return z * math.sqrt(expected_p * (1 - expected_p) / (n + z * z))


def cmd_proportion(args: argparse.Namespace) -> int:
    n = n_for_proportion(args.confidence, args.margin, args.expected)
    z = z_for(args.confidence)
    print("Sample size for a proportion")
    print("=" * 60)
    print("Confidence %.0f%% · margin of error +/-%.0f points · expected proportion "
          "%.0f%%" % (100 * args.confidence, 100 * args.margin, 100 * args.expected))
    print()
    print("  n = %d" % n)
    print()
    print("Formula: n = z^2 p(1-p) / m^2 - z^2. The \"- z^2\" is the adjusted-Wald")
    print("planning correction: the adjusted-Wald interval adds z^2 (%.2f here) to n,"
          % (z * z))
    print("so the study needs that many fewer real participants to hit the margin.")
    print("(%s.)" % CITATIONS["agresti_coull"])
    if abs(args.expected - 0.5) < 1e-9:
        print()
        print("Expected proportion defaults to 50%, which is the worst case and")
        print("therefore the safe planning assumption. If you have a prior estimate,")
        print("pass --expected and n will fall.")
    print()
    print("For reference: " + CITATIONS["nng_quant"] + ".")
    if abs(args.confidence - 0.95) < 1e-9 and abs(args.margin - 0.15) < 1e-9 \
            and abs(args.expected - 0.5) < 1e-9:
        print("That matches the corrected formula above: 39 before rounding up to 40.")
    print()
    print("Margin of error at this confidence by n, assuming p=%g%s:"
          % (args.expected,
             " (the default)" if abs(args.expected - 0.5) < 1e-9 else " (--expected)"))
    for nn in (5, 10, 20, 30, 40, 60, 100, 200, 385):
        print("  n=%-4d  +/-%.0f points" % (nn, 100 * margin_at(nn, args.confidence,
                                                                args.expected)))
    return 0


# ------------------------------------------------------------------- times

def geometric_mean(values: Sequence[float]) -> float:
    return math.exp(sum(math.log(v) for v in values) / len(values))


def median(values: Sequence[float]) -> float:
    s = sorted(values)
    mid = len(s) // 2
    return s[mid] if len(s) % 2 else (s[mid - 1] + s[mid]) / 2


def log_interval(values: Sequence[float], confidence: float) -> Tuple[float, float]:
    """Interval for the geometric mean: t interval (df = n-1) on log values."""
    check_unit_interval(confidence, "--confidence", "0.95")
    logs = [math.log(v) for v in values]
    n = len(logs)
    mean_log = sum(logs) / n
    if n < 2:
        return math.exp(mean_log), math.exp(mean_log)
    var = sum((x - mean_log) ** 2 for x in logs) / (n - 1)
    se = math.sqrt(var / n)
    t = t_quantile(1 - (1 - confidence) / 2, n - 1)
    return math.exp(mean_log - t * se), math.exp(mean_log + t * se)


def cmd_times(args: argparse.Namespace) -> int:
    values = args.values
    n = len(values)
    if n == 0:
        fail("pass task times as positional arguments")
    if any(v <= 0 for v in values):
        fail("task times must all be positive")
    check_unit_interval(args.confidence, "--confidence", "0.95")

    arith = sum(values) / n
    geo = geometric_mean(values)
    med = median(values)
    low, high = log_interval(values, args.confidence)

    print("Task time summary (n=%d)" % n)
    print("=" * 60)
    print("  arithmetic mean   %.1f   <- do not report this" % arith)
    print("  geometric mean    %.1f" % geo)
    print("  median            %.1f" % med)
    print()
    recommended = "geometric mean" if n < 25 else "median"
    print("Report the %s: %.1f" % (recommended, geo if n < 25 else med))
    if n >= 2:
        print("  %.0f%% interval (t on log-transformed values, df=%d): %.1f to %.1f"
              % (100 * args.confidence, n - 1, low, high))
    else:
        print("  No interval: one value has no spread to estimate.")
    print()
    print(CITATIONS["sauro_lewis_mean"])
    print()
    print("Task times are right-skewed: a few slow sessions pull the arithmetic mean")
    print("above the typical experience. Here the arithmetic mean is %.0f%% higher"
          % (100 * (arith / geo - 1)))
    print("than the geometric mean. Intervals are computed on log-transformed values")
    print("with a t critical value and converted back, which is why they are")
    print("asymmetric around the centre.")
    return 0


# -------------------------------------------------------------- saturation

def _split_codes(cell: str) -> List[str]:
    parts = []
    for chunk in cell.replace("|", ";").split(";"):
        chunk = chunk.strip()
        if chunk:
            parts.append(chunk)
    return parts


def load_codes(path: str) -> List[Tuple[str, List[str]]]:
    """Return [(interview_id, [codes])] in file order.

    JSON: a list of lists, a list of {"interview": id, "codes": [...]}, or an
    object {id: [codes]} in interview order.
    CSV: a header row, then rows whose first column is the interview ID and whose
    other cells hold codes (several per cell separated by ; or |). Repeated IDs
    are merged, so one-row-per-code files work too.
    """
    if not os.path.isfile(path):
        fail("file not found: %s" % path)
    try:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    except (OSError, UnicodeDecodeError) as exc:
        fail("could not read %s (%s)" % (path, exc))

    order: List[str] = []
    codes: Dict[str, List[str]] = {}

    def add(iid: str, items: Sequence[object]) -> None:
        if iid not in codes:
            order.append(iid)
            codes[iid] = []
        for item in items:
            if not isinstance(item, str):
                fail("codes must be strings; interview %s has %r" % (iid, item))
            for c in _split_codes(item):
                if c not in codes[iid]:
                    codes[iid].append(c)

    if path.lower().endswith(".json"):
        try:
            data = json.loads(text)
        except ValueError as exc:
            fail("%s is not valid JSON (%s)" % (path, exc))
        if isinstance(data, dict):
            for iid, items in data.items():
                if not isinstance(items, list):
                    fail("each interview's value must be a list of codes")
                add(str(iid), items)
        elif isinstance(data, list):
            for i, entry in enumerate(data, 1):
                if isinstance(entry, list):
                    add("interview %d" % i, entry)
                elif isinstance(entry, dict) and isinstance(
                        entry.get("codes", entry.get("themes")), list):
                    iid = entry.get("interview", entry.get("id", "interview %d" % i))
                    add(str(iid), entry.get("codes", entry.get("themes")))
                else:
                    fail("JSON entry %d must be a list of codes or an object with "
                         "a \"codes\" list" % i)
        else:
            fail("JSON must be a list or an object")
    else:
        rows = list(csv.reader(text.splitlines()))
        rows = [r for r in rows if any(cell.strip() for cell in r)]
        if len(rows) < 2:
            fail("CSV needs a header row and at least one interview row")
        for row in rows[1:]:
            iid = row[0].strip()
            if not iid:
                fail("every CSV row needs an interview ID in the first column")
            add(iid, row[1:])

    if not order:
        fail("no interviews found in %s" % path)
    return [(iid, codes[iid]) for iid in order]


def saturation_analysis(interviews: Sequence[Tuple[str, List[str]]], base: int,
                        run: int, threshold: float) -> dict:
    seen: set = set()
    per_interview = []
    for iid, items in interviews:
        new = [c for c in items if c not in seen]
        seen.update(items)
        per_interview.append({"id": iid, "new": len(new), "cumulative": len(seen)})

    base_size = per_interview[base - 1]["cumulative"] if len(interviews) >= base else 0
    runs = []
    for start in range(base, len(interviews) - run + 1):
        new_in_run = sum(per_interview[i]["new"] for i in range(start, start + run))
        ratio = new_in_run / base_size if base_size else float("inf")
        runs.append({"first": start + 1, "last": start + run,
                     "new": new_in_run, "ratio": ratio,
                     "met": ratio <= threshold + 1e-12})
    first_met = next((r for r in runs if r["met"]), None)
    return {"per_interview": per_interview, "base_size": base_size,
            "runs": runs, "first_met": first_met,
            "last_run": runs[-1] if runs else None}


def cmd_saturation(args: argparse.Namespace) -> int:
    if args.base < 1:
        fail("--base must be at least 1")
    if args.run < 1:
        fail("--run must be at least 1")
    check_unit_interval(args.threshold, "--threshold", "0.05")
    interviews = load_codes(args.file)
    if len(interviews) < args.base + args.run:
        fail("%d interviews in the file; this rule needs at least %d (base %d + "
             "run %d) before it can say anything"
             % (len(interviews), args.base + args.run, args.base, args.run))
    result = saturation_analysis(interviews, args.base, args.run, args.threshold)
    if result["base_size"] == 0:
        fail("no codes in the first %d interviews, so there is no base to compare "
             "against" % args.base)

    print("Saturation check (one stopping rule, not proof)")
    print("=" * 60)
    print("Base size %d interviews · run length %d · new-information threshold "
          "<= %.0f%%" % (args.base, args.run, 100 * args.threshold))
    print(CITATIONS["guest_2020"] + ".")
    print()
    print("New themes per interview, in order:")
    for i, row in enumerate(result["per_interview"], 1):
        marker = "  (base)" if i <= args.base else ""
        print("  %-3d %-20s new %-3d cumulative %d%s"
              % (i, row["id"][:20], row["new"], row["cumulative"], marker))
    print()
    print("Unique themes in the base: %d" % result["base_size"])
    print("Runs (new themes in the run / themes in the base), sliding one interview "
          "at a time:")
    for r in result["runs"]:
        print("  interviews %d-%d   %d new   %.0f%%%s"
              % (r["first"], r["last"], r["new"], 100 * r["ratio"],
                 "   <= threshold" if r["met"] else ""))
    print()
    last = result["last_run"]
    print("Last run (interviews %d-%d): %.0f%% new information. Threshold %s."
          % (last["first"], last["last"], 100 * last["ratio"],
             "met" if last["met"] else "not met"))
    first = result["first_met"]
    if first:
        print("First met in the run covering interviews %d-%d."
              % (first["first"], first["last"]))
    else:
        print("Not met in any run yet.")
    print()
    print("This is one stopping rule. It counts new codes; it says nothing about")
    print("whether the codes are understood, and a different base, run or threshold")
    print("gives a different answer. Report the parameters with the result. For")
    print("reflexive thematic analysis, saturation is not the right frame at all:")
    print(CITATIONS["braun_clarke_saturation"] + ".")
    return 0


# -------------------------------------------------------------------- plan

METHOD_GUIDANCE = {
    "formative-usability": (
        "Formative usability (finding problems to fix)",
        "Use the discovery model. n is driven by the problem frequency you care "
        "about and the discovery rate you will accept — not by a rule of thumb.",
        "discover"),
    "summative-usability": (
        "Summative usability (measuring against a benchmark)",
        "Use the proportion calculation. This is a measurement study and needs a "
        "confidence level and a margin of error before n means anything.",
        "proportion"),
    "survey": (
        "Survey (estimating a proportion in a population)",
        "Use the proportion calculation. State the margin of error in the report, "
        "every time.",
        "proportion"),
    "interviews": (
        "Qualitative interviews or focus groups (understanding, not measuring)",
        "Start from the empirical saturation literature for a budget, then adjust "
        "for your study. Do not report percentages from this study.",
        "qual"),
    "benchmark": (
        "Benchmark study (tracking a metric over time)",
        "Use the proportion calculation, and hold n constant across waves. A metric "
        "that moves because n changed is not a finding.",
        "proportion"),
}

QUAL_RANGES = {
    "interviews": (9, 17, "interviews"),
    "focus-groups": (4, 8, "focus groups"),
}

INFORMATION_POWER = [
    ("Aim", "narrow aim -> fewer; broad aim -> more"),
    ("Sample specificity", "participants who closely fit the aim -> fewer; "
                           "loosely fitting -> more"),
    ("Theory", "applying established theory -> fewer; no theoretical "
               "framework -> more"),
    ("Dialogue quality", "strong, focused conversations -> fewer; weak or "
                         "unfocused -> more"),
    ("Analysis strategy", "in-depth analysis of a few cases -> fewer; "
                          "exploratory cross-case analysis -> more"),
]


def print_qual_plan(args: argparse.Namespace) -> None:
    segments = args.segments
    lo, hi, unit = QUAL_RANGES[args.qual_method]

    print("Approach: %s · method: %s · segments: %d · goal: %s"
          % (args.approach, args.qual_method, segments, args.goal))
    print()
    if args.approach == "reflexive-ta":
        print("Starting range for budgeting only (see the reflexive TA note below):")
    else:
        print("Starting range:")
    print("  %d-%d %s per segment" % (lo, hi, unit))
    print("  %d-%d %s in total (%d segment%s)"
          % (lo * segments, hi * segments, unit, segments,
             "" if segments == 1 else "s"))
    print("  Source: " + CITATIONS["hennink_kaiser_2022"] + ".")
    print("  A segment is a group you expect to differ; within one, participants")
    print("  should be fairly similar for the range to apply.")
    print()

    if args.qual_method == "interviews":
        if args.goal == "issues":
            g_lo, g_hi, g_text = 9, 9, "about 9 per segment reaches code saturation"
        else:
            g_lo, g_hi, g_text = 16, 24, ("about 16-24 per segment reaches meaning "
                                          "saturation")
        total = ("about %d" % (g_lo * segments) if g_lo == g_hi
                 else "%d-%d" % (g_lo * segments, g_hi * segments))
        print("Goal: %s. For this goal, %s (%s in total)." % (
            "find the range of issues" if args.goal == "issues"
            else "understand the issues in depth", g_text, total))
        print("  Source: " + CITATIONS["hennink_2017"] + ".")
    else:
        print("Goal: the code/meaning saturation figures (Hennink, Kaiser & Marconi")
        print("2017) come from interviews; for focus groups use the range above.")
    print()

    if args.approach == "reflexive-ta":
        print("Reflexive thematic analysis: " + CITATIONS["braun_clarke_saturation"]
              + ".")
        print("Use information power instead (" + CITATIONS["malterud_2016"] + ").")
        print("Each factor moves n up or down from the starting range:")
        for name, direction in INFORMATION_POWER:
            print("  - %-18s %s" % (name, direction))
        print("The range above is for budgeting and recruitment, not a stopping rule.")
    else:
        label = "codebook analysis" if args.approach == "codebook" else "affinity mapping"
        print("For %s, check the range against your own data as you go:" % label)
        print("`saturation` applies Guest, Namey & Chen's (2020) stopping rule to the")
        print("themes per interview.")
    print()

    print("Rationale paragraph for the plan:")
    print()
    if args.approach == "reflexive-ta":
        lines = [
            "We will run %d-%d %s across %d segment%s as a starting budget, based"
            % (lo * segments, hi * segments, unit, segments,
               "" if segments == 1 else "s"),
            "on the range in Hennink & Kaiser's (2022) review. Because this is",
            "reflexive thematic analysis, we will judge sufficiency by information",
            "power (Malterud, Siersma & Guassora, 2016) rather than saturation,",
            "adjusting n for the study's aim, sample specificity, use of theory,",
            "dialogue quality and analysis strategy.",
        ]
    else:
        lines = [
            "We will run %d-%d %s: %d-%d in each of %d segment%s, the range at"
            % (lo * segments, hi * segments, unit, lo, hi, segments,
               "" if segments == 1 else "s"),
            "which empirical studies reached saturation for fairly similar groups",
            "(Hennink & Kaiser, 2022).",
        ]
        if args.qual_method == "interviews":
            if args.goal == "issues":
                lines.append("Our goal is the range of issues, which reached code "
                             "saturation at about")
                lines.append("9 interviews per group (Hennink, Kaiser & Marconi, 2017).")
            else:
                lines.append("Our goal is in-depth understanding, which needed about "
                             "16-24 interviews")
                lines.append("per group for meaning saturation (Hennink, Kaiser & "
                             "Marconi, 2017).")
    lines += [
        "Findings will be reported as counts of participants, not percentages,",
        "because a purposive sample does not support estimating proportions in a",
        "population.",
    ]
    for line in lines:
        print("  " + line)


def cmd_plan(args: argparse.Namespace) -> int:
    key = args.method
    label, guidance, route = METHOD_GUIDANCE[key]

    qual_opts = [args.approach, args.segments, args.goal, args.qual_method]
    if route != "qual" and any(o is not None for o in qual_opts):
        fail("--approach, --segments, --goal and --method only apply to "
             "`plan interviews`")
    if route == "qual":
        args.approach = args.approach or "affinity"
        args.segments = 1 if args.segments is None else args.segments
        args.goal = args.goal or "issues"
        args.qual_method = args.qual_method or "interviews"
        if args.segments < 1:
            fail("--segments must be at least 1")
    elif route == "discover":
        check_unit_interval(args.problem_frequency, "--problem-frequency", "0.31")
        check_unit_interval(args.target, "--target", "0.85")
    else:
        check_unit_interval(args.margin, "--margin", "0.15")
        z_for(args.confidence)

    print("n rationale for a research plan")
    print("=" * 60)
    print("Method: %s" % label)
    print()
    print(guidance)
    print()

    if route == "discover":
        p = args.problem_frequency
        target = args.target
        n = n_for_discovery(p, target)
        print("  n = %d" % n)
        print()
        print("Rationale line for the plan:")
        print()
        print("  We will run %d sessions. At an assumed problem frequency of %.0f%%,"
              % (n, 100 * p))
        print("  this gives roughly %.0f%% expected discovery of problems at that"
              % (100 * target))
        print("  frequency (%s)." % CITATIONS["nielsen_landauer"])
        print("  Expected discovery is an average across possible samples, not a")
        print("  guarantee for ours: %s." % CITATIONS["faulkner"])
        print("  Rarer problems and open-ended tasks will need more sessions.")
    elif route == "proportion":
        n = n_for_proportion(args.confidence, args.margin, 0.5)
        print("  n = %d" % n)
        print()
        print("Rationale line for the plan:")
        print()
        print("  We will recruit %d participants. At %.0f%% confidence this gives a"
              % (n, 100 * args.confidence))
        print("  margin of error of +/-%.0f percentage points on a proportion,"
              % (100 * args.margin))
        print("  assuming the worst-case 50% split. Results will be reported with")
        print("  adjusted-Wald intervals (%s)." % CITATIONS["agresti_coull"])
    else:
        print_qual_plan(args)
    print()
    print("Paste the rationale into the plan. The number on its own invites the")
    print("question; the number with its assumption answers it.")
    return 0


# -------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="sample_size.py",
        description="Compute n, and the interval that comes with it.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="the n rationale for a plan")
    p.add_argument("method", choices=sorted(METHOD_GUIDANCE))
    p.add_argument("--problem-frequency", type=float, default=0.31)
    p.add_argument("--target", type=float, default=0.85)
    p.add_argument("--confidence", type=float, default=0.95)
    p.add_argument("--margin", type=float, default=0.15)
    p.add_argument("--approach", choices=["reflexive-ta", "codebook", "affinity"],
                   help="interviews only: analysis approach, default affinity")
    p.add_argument("--segments", type=int,
                   help="interviews only: number of segments, default 1")
    p.add_argument("--goal", choices=["issues", "understanding"],
                   help="interviews only: range of issues or in-depth "
                        "understanding, default issues")
    p.add_argument("--method", dest="qual_method",
                   choices=["interviews", "focus-groups"],
                   help="interviews only: interviews or focus groups, "
                        "default interviews")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("saturation",
                       help="Guest, Namey & Chen stopping rule on themes per interview")
    p.add_argument("file", help="CSV or JSON of codes/themes per interview, in order")
    p.add_argument("--base", type=int, default=4, help="base size, default 4")
    p.add_argument("--run", type=int, default=2, help="run length, default 2")
    p.add_argument("--threshold", type=float, default=0.05,
                   help="new-information threshold, default 0.05")
    p.set_defaults(func=cmd_saturation)

    p = sub.add_parser("discover", help="problem-discovery model")
    p.add_argument("--problem-frequency", type=float, default=0.31,
                   help="assumed frequency of a problem, default 0.31")
    p.add_argument("--n", type=int, help="report discovery at this n instead")
    p.set_defaults(func=cmd_discover)

    p = sub.add_parser("interval", help="adjusted-Wald interval for a proportion")
    p.add_argument("x", type=int)
    p.add_argument("n", type=int)
    p.add_argument("--confidence", type=float, default=0.95)
    p.set_defaults(func=cmd_interval)

    p = sub.add_parser("proportion", help="n for a target margin of error")
    p.add_argument("--confidence", type=float, default=0.95)
    p.add_argument("--margin", type=float, default=0.15)
    p.add_argument("--expected", type=float, default=0.5)
    p.set_defaults(func=cmd_proportion)

    p = sub.add_parser("times", help="summarise task times correctly")
    p.add_argument("values", nargs="+", type=float)
    p.add_argument("--confidence", type=float, default=0.95)
    p.set_defaults(func=cmd_times)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""
Standardised-Instrument Scorer - score SUS, UMUX-Lite, SEQ and NASA-TLX
correctly, and catch the coding errors that silently void the benchmark.

Subcommands:
  sus         score the System Usability Scale, with grade, percentile and interval
  umux-lite   score UMUX-Lite, raw (primary) and SUS-equivalent (secondary)
  seq         score the Single Ease Question
  tlx         score raw NASA-TLX
  validate    check a questionnaire's wording and scale against the canonical form

Usage:
  python score_instrument.py sus responses.csv
  python score_instrument.py sus responses.csv --positive
  python score_instrument.py sus responses.csv --drop-item 4
  python score_instrument.py validate my_sus.txt --instrument sus --points 5

Exit codes: 0 = clean, 1 = findings to review, 2 = fatal error (bad input).

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

# Brooke (1996). Odd items are positively worded, even items negatively.
SUS_ITEMS = [
    "I think that I would like to use this system frequently.",
    "I found the system unnecessarily complex.",
    "I thought the system was easy to use.",
    "I think that I would need the support of a technical person to be able to use this system.",
    "I found the various functions in this system were well integrated.",
    "I thought there was too much inconsistency in this system.",
    "I would imagine that most people would learn to use this system very quickly.",
    "I found the system very cumbersome to use.",
    "I felt very confident using the system.",
    "I needed to learn a lot of things before I could get going with this system.",
]

# Substituting the product noun is documented as acceptable and does not
# materially move scores. Anything else is a change to the instrument.
PRODUCT_NOUNS = ["system", "product", "website", "site", "app", "application",
                 "tool", "platform"]
CUMBERSOME_SUBS = ["cumbersome", "awkward"]

# Sauro & Lewis curved grading scale. It describes study means, so the
# script grades the mean only, never an individual respondent.
SUS_GRADES = [
    (84.1, 100.1, "A+", "96th-100th percentile"),
    (80.8, 84.1, "A", "90th-95th"),
    (78.9, 80.8, "A-", "85th-89th"),
    (77.2, 78.9, "B+", "80th-84th"),
    (74.1, 77.2, "B", "70th-79th"),
    (72.6, 74.1, "B-", "65th-69th"),
    (71.1, 72.6, "C+", "60th-64th"),
    (65.0, 71.1, "C", "41st-59th"),
    (62.7, 65.0, "C-", "35th-40th"),
    (51.7, 62.7, "D", "15th-34th"),
    (0.0, 51.7, "F", "0-14th"),
]

SUS_MEAN = 68.0

UMUX_LITE_ITEMS = [
    "This system's capabilities meet my requirements.",
    "This system is easy to use.",
]
# Regression from raw UMUX-Lite to the SUS scale. Maps 0..100 to 22.9..87.9.
UMUX_SLOPE, UMUX_INTERCEPT = 0.65, 22.9

SEQ_ITEM = "Overall, how difficult or easy was the task to complete?"
# MeasuringU, https://measuringu.com/seq10/
SEQ_BENCHMARK = 5.5

TLX_SUBSCALES = ["mental demand", "physical demand", "temporal demand",
                 "performance", "effort", "frustration"]
TLX_KEYWORDS = ["mental", "physical", "temporal", "perform", "effort", "frustr"]

# Column or key names treated as identifiers, not responses.
ID_NAME = re.compile(
    r"(^|[\s_.-])(id|uid|pid|participant|respondent|user|name|email|"
    r"timestamp|date|time)([\s_.-]|$)", re.IGNORECASE)


def fatal(msg: str) -> None:
    print("error: " + msg, file=sys.stderr)
    sys.exit(2)


# ------------------------------------------------------- t distribution

def _betacf(a: float, b: float, x: float) -> float:
    """Continued fraction for the regularized incomplete beta (Lentz)."""
    tiny = 1e-300
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    d = 1.0 / (d if abs(d) > tiny else tiny)
    h = d
    for m in range(1, 300):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        d = 1.0 / (d if abs(d) > tiny else tiny)
        c = 1.0 + aa / c
        c = c if abs(c) > tiny else tiny
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-14:
            break
    return h


def _betai(a: float, b: float, x: float) -> float:
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 1.0
    lbt = (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
           + a * math.log(x) + b * math.log(1.0 - x))
    if x < (a + 1.0) / (a + b + 2.0):
        return math.exp(lbt) * _betacf(a, b, x) / a
    return 1.0 - math.exp(lbt) * _betacf(b, a, 1.0 - x) / b


def t_cdf(t: float, df: float) -> float:
    tail = 0.5 * _betai(df / 2.0, 0.5, df / (df + t * t))
    return 1.0 - tail if t > 0 else tail


def t_quantile(p: float, df: float) -> float:
    """Inverse t CDF for p in (0.5, 1), by bisection."""
    lo, hi = 0.0, 1.0
    while t_cdf(hi, df) < p:
        hi *= 2.0
    for _ in range(200):
        mid = (lo + hi) / 2.0
        if t_cdf(mid, df) < p:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


def t_crit(confidence: float, df: int) -> float:
    return t_quantile(1 - (1 - confidence) / 2, df)


def mean_ci(values: Sequence[float], confidence: float,
            bounds: Tuple[float, float]) -> Tuple[float, float, float]:
    """Mean and t-interval (df = n - 1), clamped to the scale range."""
    n = len(values)
    m = sum(values) / n
    if n < 2:
        return m, m, m
    var = sum((v - m) ** 2 for v in values) / (n - 1)
    half = t_crit(confidence, n - 1) * math.sqrt(var / n)
    return m, max(bounds[0], m - half), min(bounds[1], m + half)


# ------------------------------------------------------------------- input

def _to_float(v: Any) -> Optional[float]:
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v.strip())
        except ValueError:
            return None
    return None


def _match_names(names: Sequence[str], keywords: Sequence[str]) -> Optional[List[int]]:
    """Index of the one column/key containing each keyword, or None."""
    idx = []
    for kw in keywords:
        hits = [i for i, n in enumerate(names) if kw in n.lower()]
        if len(hits) != 1 or hits[0] in idx:
            return None
        idx.append(hits[0])
    return idx


def _is_header(cells: List[str], expected: int) -> bool:
    filled = [c for c in cells if c.strip()]
    nums = [_to_float(c) for c in filled]
    numeric = [x for x in nums if x is not None]
    if len(numeric) * 2 < len(filled):
        return True  # mostly text: a header, even with an ID cell in a data row
    # Column numbers used as a header (1, 2, ... n) are not a respondent.
    return expected >= 3 and numeric == [float(i) for i in range(1, expected + 1)]


def load_responses(path: str, expected: int,
                   keywords: Optional[Sequence[str]] = None
                   ) -> Tuple[List[List[float]], bool]:
    """Rows of numeric responses. Returns (rows, matched_by_name)."""
    p = Path(path)
    if not p.is_file():
        fatal("no such file: %s" % path)

    rows: List[List[float]] = []
    by_name = False
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            fatal("%s is not valid JSON (%s)" % (path, e))
        if isinstance(data, dict):
            data = data.get("responses", data.get("data", []))
        if not isinstance(data, list):
            fatal("%s: expected a list of responses" % path)
        for r in data:
            if isinstance(r, dict):
                keys = [k for k in r if not ID_NAME.search(str(k))]
                idx = _match_names(keys, keywords) if keywords else None
                if idx is not None:
                    by_name = True
                    keys = [keys[i] for i in idx]
                else:
                    keys = sorted(keys, key=_numeric_key)
                vals = [_to_float(r[k]) for k in keys]
            elif isinstance(r, list):
                vals = [_to_float(v) for v in r]
            else:
                vals = [_to_float(r)]
            nums = [v for v in vals if v is not None]
            if nums:
                rows.append(nums)
    else:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            raw_rows = [[c.strip() for c in r] for r in csv.reader(fh)]
        raw_rows = [r for r in raw_rows if any(r)]
        cols: Optional[List[int]] = None
        if raw_rows and _is_header(raw_rows[0], expected):
            header = raw_rows.pop(0)
            cols = [i for i, h in enumerate(header) if not ID_NAME.search(h)]
            if keywords:
                idx = _match_names([header[i] for i in cols], keywords)
                if idx is not None:
                    by_name = True
                    cols = [cols[i] for i in idx]
        for raw in raw_rows:
            cells = [raw[i] if i < len(raw) else "" for i in cols] if cols is not None else raw
            nums = [x for x in (_to_float(c) for c in cells if c) if x is not None]
            if nums:
                rows.append(nums)

    if not rows:
        fatal("no response rows found in %s" % path)
    bad = [i for i, r in enumerate(rows, 1) if len(r) != expected]
    if bad:
        fatal("%d row(s) do not have exactly %d numeric responses (rows %s). "
              "A row with the wrong item count is the most common source of a "
              "miscoded score. If the file has a numeric ID column, give it a "
              "header such as 'id' so it is skipped."
              % (len(bad), expected, ", ".join(map(str, bad[:8]))))
    return rows, by_name


def _numeric_key(k: str) -> Tuple[int, str]:
    m = re.search(r"\d+", str(k))
    return (int(m.group()) if m else 999, str(k))


def check_range(rows: List[List[float]], low: float, high: float, what: str) -> None:
    for i, r in enumerate(rows, 1):
        for v in r:
            if not low <= v <= high:
                fatal("row %d contains %g. %s %g-%g." % (i, v, what, low, high))


# --------------------------------------------------------------------- SUS

def score_sus_row(row: Sequence[float], items: Sequence[int],
                  positive: bool = False) -> float:
    """items: the 1-based SUS item number of each value in row.

    Standard SUS: odd items (response - 1), even items (5 - response).
    All-positive SUS (Sauro & Lewis 2011): every item (response - 1).
    The sum is rescaled to 0-100, which is x 2.5 for all ten items and
    x 100/36 when one item is dropped (Lewis & Sauro 2017).
    """
    total = 0.0
    for item, v in zip(items, row):
        total += (v - 1) if (positive or item % 2 == 1) else (5 - v)
    return total * 100.0 / (4 * len(items))


def sus_grade(score: float) -> Tuple[str, str]:
    for low, high, grade, pct in SUS_GRADES:
        if low <= score < high:
            return grade, pct
    return "F", "0-14th"


def detect_possible_inconsistencies(rows: List[List[float]], items: Sequence[int],
                                    positive: bool = False) -> List[str]:
    """Patterns that may mean a respondent missed the reversal on the
    standard SUS. Flags for review, not errors: nothing is dropped.
    The thresholds (4+ = agree, 2- = disagree) are a working default, not
    from the literature."""
    if positive:
        # Every item points the same way, so uniform or matching answers
        # are consistent.
        return []
    issues = []
    for i, row in enumerate(rows, 1):
        r = dict(zip(items, row))
        if len(set(row)) == 1:
            if row[0] != 3:  # all-neutral is not contradictory
                issues.append(
                    "row %d: every item answered %g, so the respondent %s with "
                    "both the positively and negatively worded items."
                    % (i, row[0], "agreed" if row[0] > 3 else "disagreed"))
            continue
        if 3 in r and 8 in r:
            if r[3] >= 4 and r[8] >= 4:
                issues.append("row %d: agreed 'easy to use' (%g) and 'very "
                              "cumbersome' (%g). May have missed the reversal."
                              % (i, r[3], r[8]))
            if r[3] <= 2 and r[8] <= 2:
                issues.append("row %d: disagreed 'easy to use' (%g) and 'very "
                              "cumbersome' (%g). May have missed the reversal."
                              % (i, r[3], r[8]))
        if 2 in r and 3 in r and r[2] >= 4 and r[3] >= 4:
            issues.append("row %d: agreed 'unnecessarily complex' (%g) and 'easy "
                          "to use' (%g). May have missed the reversal."
                          % (i, r[2], r[3]))
    return issues


def cmd_sus(args: argparse.Namespace) -> int:
    if args.drop_item is not None and not 1 <= args.drop_item <= 10:
        fatal("--drop-item must be an item number from 1 to 10.")
    items = [k for k in range(1, 11) if k != args.drop_item]
    rows, _ = load_responses(args.responses, len(items))
    check_range(rows, 1, 5, "SUS items are scored")

    scores = [score_sus_row(r, items, args.positive) for r in rows]
    mean, low, high = mean_ci(scores, args.confidence, (0.0, 100.0))
    grade, pct = sus_grade(mean)

    title = "System Usability Scale"
    if args.positive:
        title += " (all-positive version)"
    print(title)
    print("=" * 60)
    print("n = %d" % len(scores))
    print()

    issues = detect_possible_inconsistencies(rows, items, args.positive)
    if issues:
        print("POSSIBLE INCONSISTENCIES (%d) - flagged for review, not dropped"
              % len(issues))
        for m in issues:
            print("  - " + m)
        print()
        print("These rows are included in the mean below. Following Meade & Craig "
              "(2012), flag careless responding and decide any exclusion "
              "explicitly; say what you excluded and why.")
        print("For context, Sauro & Lewis report two separate problems: 3 of 27 "
              "SUS datasets were miscoded by researchers, and 21 of 158 "
              "individual questionnaires contained participant errors.")
        print()

    print("  mean SUS score   %.1f" % mean)
    if len(scores) > 1:
        print("  %.0f%% interval    %.1f to %.1f  (t-interval, df = %d)"
              % (100 * args.confidence, low, high, len(scores) - 1))
    print("  grade of mean    %s  (%s of products benchmarked)" % (grade, pct))
    print("  against the %.0f benchmark: %+.1f" % (SUS_MEAN, mean - SUS_MEAN))
    print()
    if args.positive:
        print("Scoring (all-positive SUS): every item (response - 1), summed and "
              "rescaled to 0-100.")
    else:
        print("Scoring: odd items (response - 1), even items (5 - response), "
              "summed and rescaled to 0-100.")
    if args.drop_item:
        print("Item %d dropped: the 9-item sum is multiplied by 100/36 instead of "
              "2.5 (Lewis & Sauro 2017)." % args.drop_item)
    else:
        print("With all ten items the rescaling is x 2.5.")
    print()

    if args.per_respondent:
        print("PER RESPONDENT (scores only: the grade curve describes study "
              "means, not individuals)")
        for i, s in enumerate(scores, 1):
            print("  %-4d %6.1f" % (i, s))
        print()

    if not issues:
        print("No possible inconsistencies detected.")
        print()
    print("A SUS score is not a percentage. %.1f is grade %s against the benchmark "
          "distribution, not '%.0f%% usable'." % (mean, grade, mean))
    return 1 if issues else 0


# --------------------------------------------------------------- UMUX-Lite

def cmd_umux_lite(args: argparse.Namespace) -> int:
    rows, _ = load_responses(args.responses, 2)
    check_range(rows, 1, 7, "UMUX-Lite items are scored")

    raw = [((r[0] - 1) + (r[1] - 1)) / 12 * 100 for r in rows]
    adjusted = [UMUX_SLOPE * x + UMUX_INTERCEPT for x in raw]
    m_raw, lo_raw, hi_raw = mean_ci(raw, args.confidence, (0.0, 100.0))
    m_adj, lo_adj, hi_adj = mean_ci(
        adjusted, args.confidence,
        (UMUX_INTERCEPT, UMUX_SLOPE * 100 + UMUX_INTERCEPT))

    print("UMUX-Lite")
    print("=" * 60)
    print("n = %d" % len(rows))
    print("  raw score (primary)        %.1f  (%.1f to %.1f)" % (m_raw, lo_raw, hi_raw))
    print("  SUS-equivalent (secondary) %.1f  (%.1f to %.1f)" % (m_adj, lo_adj, hi_adj))
    print()
    print("Raw = ((item1-1)+(item2-1))/12 x 100 on the two 7-point items. Report "
          "this as the UMUX-Lite score.")
    print("SUS-equivalent applies the regression 0.65 x raw + 22.9. It is higher "
          "than raw below a raw score of about 65.4 and lower above it; here it "
          "differs by %+.1f points." % (m_adj - m_raw))
    print("MeasuringU now prefers interpolation to this regression for putting "
          "UMUX-Lite on the SUS scale "
          "(https://measuringu.com/from-umux-lite-to-ux-lite/). If you compare "
          "with a SUS benchmark, say which conversion you used.")
    return 0


# --------------------------------------------------------------------- SEQ

def cmd_seq(args: argparse.Namespace) -> int:
    rows, _ = load_responses(args.responses, 1)
    check_range(rows, 1, 7, "SEQ is scored")
    values = [r[0] for r in rows]
    m, lo, hi = mean_ci(values, args.confidence, (1.0, 7.0))
    print("Single Ease Question")
    print("=" * 60)
    print("n = %d" % len(values))
    print("  mean            %.2f  (%.2f to %.2f)" % (m, lo, hi))
    print("  top-two-box     %.0f%%  (rated 6 or 7)"
          % (100 * sum(1 for v in values if v >= 6) / len(values)))
    print("  against the ~%.1f average: %+.2f  (MeasuringU, "
          "https://measuringu.com/seq10/)" % (SEQ_BENCHMARK, m - SEQ_BENCHMARK))
    print()
    print("SEQ is a single 7-point item asked immediately after a task. It is "
          "ordinal: report the mean with its interval and the top-two-box, and do "
          "not treat a small difference between tasks as meaningful without a "
          "test designed for it.")
    return 0


# --------------------------------------------------------------------- TLX

def cmd_tlx(args: argparse.Namespace) -> int:
    rows, by_name = load_responses(args.responses, 6, TLX_KEYWORDS)
    check_range(rows, 0, 100, "Raw TLX subscales are scored")

    per_row = [sum(r) / 6 for r in rows]
    m, lo, hi = mean_ci(per_row, args.confidence, (0.0, 100.0))

    print("NASA-TLX (raw / unweighted)")
    print("=" * 60)
    print("n = %d" % len(rows))
    if by_name:
        print("Subscale columns matched by header name.")
    else:
        print("No subscale names found in the header; columns read in order: "
              + ", ".join(TLX_SUBSCALES) + ".")
    print("  overall workload  %.1f  (%.1f to %.1f)" % (m, lo, hi))
    print()
    print("BY SUBSCALE")
    for i, name in enumerate(TLX_SUBSCALES):
        vals = [r[i] for r in rows]
        sm, slo, shi = mean_ci(vals, args.confidence, (0.0, 100.0))
        bar = "#" * int(round(sm / 4))
        print("  %-18s %5.1f  %-25s (%.1f to %.1f)" % (name, sm, bar, slo, shi))
    print()
    print("This is raw TLX: the unweighted average of the six subscales. The "
          "weighted version needs the 15 pairwise comparisons, which most studies "
          "skip. Say which you used - they are not interchangeable.")
    print("Report the subscales. The overall number hides which kind of workload "
          "the task imposes, and that is usually the finding.")
    return 0


# ---------------------------------------------------------------- validate

VALIDATE_INFO = {
    "sus": {"items": SUS_ITEMS, "points": 5, "name": "SUS",
            "altered": "Altered wording means the 68 benchmark and the Sauro-Lewis "
                       "grade curve no longer apply to your score. Either restore "
                       "the canonical wording, or keep the change and stop "
                       "reporting against the benchmark.",
            "ok": "The 68 benchmark and the grade curve apply."},
    "umux-lite": {"items": UMUX_LITE_ITEMS, "points": 7, "name": "UMUX-Lite",
                  "altered": "Altered wording means the score no longer compares "
                             "with published UMUX-Lite results, and neither does "
                             "any SUS-equivalent derived from it. Either restore "
                             "the canonical wording, or report it as a modified "
                             "instrument.",
                  "ok": "Published UMUX-Lite comparisons apply."},
    "seq": {"items": [SEQ_ITEM], "points": 7, "name": "SEQ",
            "altered": "Altered wording means the result no longer compares with "
                       "the ~5.5 SEQ average or other published SEQ data. Either "
                       "restore the canonical wording, or report it as a modified "
                       "question.",
            "ok": "The ~5.5 SEQ average applies."},
}


def cmd_validate(args: argparse.Namespace) -> int:
    info = VALIDATE_INFO[args.instrument]
    canonical: List[str] = info["items"]
    name = info["name"]
    p = Path(args.questionnaire)
    if not p.is_file():
        fatal("no such file: %s" % args.questionnaire)
    text = p.read_text(encoding="utf-8")
    lines = [re.sub(r"^\s*\d+[.)]\s*", "", ln).strip()
             for ln in text.splitlines() if ln.strip()]
    lines = [ln for ln in lines if len(ln) > 15]

    print("Instrument validation: %s" % name)
    print("=" * 60)

    problems = 0
    warnings = 0

    if args.points and args.points != info["points"]:
        warnings += 1
        print("WARNING: scale has %d points. %s is a %d-point instrument. This "
              "script scores the %d-point version only, and published benchmarks "
              "were built on it. Say that you changed the scale, and treat "
              "benchmark comparisons with caution."
              % (args.points, name, info["points"], info["points"]))
        print()

    numbers = list(range(1, len(canonical) + 1))
    if args.instrument == "sus" and len(lines) == 9:
        dropped = _find_dropped_item(lines, args.product)
        warnings += 1
        print("WARNING: found 9 items. Item %d (\"%s\") appears to have been "
              "dropped. Lewis & Sauro (2017) show SUS can be scored with one item "
              "left out if the sum is rescaled: score with --drop-item %d, and "
              "report that you did." % (dropped, SUS_ITEMS[dropped - 1], dropped))
        print()
        numbers = [k for k in numbers if k != dropped]
        canonical = [SUS_ITEMS[k - 1] for k in numbers]
    elif len(lines) != len(canonical):
        problems += 1
        print("BLOCKER: found %d items, expected %d. A %s with a missing, added or "
              "reordered item is not a %s."
              % (len(lines), len(canonical), name, name))
        print()

    print("ITEM BY ITEM")
    for i, want in enumerate(canonical):
        got = lines[i] if i < len(lines) else ""
        status, note = _classify(want, got, args.product)
        if status == "exact":
            print("  %2d  exact" % numbers[i])
        elif status == "sub":
            print("  %2d  accepted substitution (%s)" % (numbers[i], note))
        else:
            problems += 1
            ratio = SequenceMatcher(None, _norm(want), _norm(got)).ratio() if got else 0.0
            print("  %2d  ALTERED (%.0f%% match)" % (numbers[i], 100 * ratio))
            print("      canonical: %s" % want)
            print("      yours:     %s" % (got or "(missing)"))

    print()
    if problems:
        print("%d problem(s). %s" % (problems, info["altered"]))
        return 1
    if warnings:
        print("Wording is canonical, with %d warning(s) above. Report the change "
              "alongside the score." % warnings)
        return 0
    print("Canonical. %s" % info["ok"])
    return 0


def _norm(s: str) -> str:
    s = s.lower().replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^\w\s']", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _clean(s: str) -> str:
    """Like _norm but keeps case, so proper nouns can be recognised."""
    s = s.replace("’", "'").replace("‘", "'")
    s = re.sub(r"[^\w\s'&-]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _item_pattern(want: str, product: Optional[str]) -> "re.Pattern[str]":
    noun_alts = []
    if product:
        noun_alts.append("(?i:%s)" % r"\s+".join(map(re.escape, _clean(product).split())))
    noun_alts.append("(?i:%s)" % "|".join(PRODUCT_NOUNS))
    if not product:
        # No name given: accept one to four capitalised words as the name.
        noun_alts.append(r"[A-Z][\w&.-]*(?:\s+[A-Z][\w&.-]*){0,3}")
    noun = "|".join(noun_alts)

    toks = _clean(want).split()
    parts: List[str] = []
    for i, t in enumerate(toks):
        base, poss = (t[:-2], True) if t.lower().endswith("'s") else (t, False)
        if base.lower() == "system":
            p = "(?P<noun%d>%s)%s" % (i, noun, "'s" if poss else "")
            if parts and toks[i - 1].lower() in ("the", "this"):
                # A product name usually replaces "the system" as a whole.
                p = r"(?:%s\s+)?%s" % (parts.pop(), p)
            parts.append(p)
        elif t.lower() == "cumbersome":
            parts.append("(?P<cmb%d>(?i:%s))" % (i, "|".join(CUMBERSOME_SUBS)))
        else:
            parts.append("(?i:%s)" % re.escape(t))
    return re.compile(r"\s+".join(parts))


def _classify(want: str, got: str, product: Optional[str]) -> Tuple[str, str]:
    if not got:
        return "altered", ""
    if _norm(want) == _norm(got):
        return "exact", ""
    m = _item_pattern(want, product).fullmatch(_clean(got))
    if not m:
        return "altered", ""
    notes = []
    for key, val in m.groupdict().items():
        if val is None:
            continue
        orig = "system" if key.startswith("noun") else "cumbersome"
        if val.lower() != orig:
            notes.append("%s -> %s" % (orig, val))
    return ("sub", ", ".join(notes)) if notes else ("exact", "")


def _find_dropped_item(lines: List[str], product: Optional[str]) -> int:
    """The SUS item whose removal best lines the nine items up with canon."""
    best, best_score = 1, -1.0
    for k in range(1, 11):
        canon = [SUS_ITEMS[j - 1] for j in range(1, 11) if j != k]
        score = 0.0
        for want, got in zip(canon, lines):
            if _classify(want, got, product)[0] != "altered":
                score += 1.0
            else:
                score += SequenceMatcher(None, _norm(want), _norm(got)).ratio() / 2
        if score > best_score:
            best, best_score = k, score
    return best


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="score_instrument.py",
        description="Score standardised usability instruments correctly. "
                    "Exit 0 = clean, 1 = findings to review, 2 = fatal error.")
    sub = ap.add_subparsers(dest="command", required=True)

    for name, fn, helptext in (
            ("sus", cmd_sus, "score the System Usability Scale"),
            ("umux-lite", cmd_umux_lite, "score UMUX-Lite"),
            ("seq", cmd_seq, "score the Single Ease Question"),
            ("tlx", cmd_tlx, "score raw NASA-TLX")):
        p = sub.add_parser(name, help=helptext)
        p.add_argument("responses", help="CSV or JSON of responses, one row each")
        p.add_argument("--confidence", type=float, default=0.95)
        if name == "sus":
            p.add_argument("--per-respondent", action="store_true",
                           help="list each respondent's score (no grades)")
            p.add_argument("--positive", action="store_true",
                           help="all-positive SUS: every item scored response - 1")
            p.add_argument("--drop-item", type=int, metavar="N",
                           help="the file has 9 items because item N was dropped")
        p.set_defaults(func=fn)

    p = sub.add_parser("validate", help="check wording against the canonical form")
    p.add_argument("questionnaire")
    p.add_argument("--instrument", choices=["sus", "umux-lite", "seq"], default="sus")
    p.add_argument("--points", type=int, help="number of scale points used")
    p.add_argument("--product", help="product name used in place of 'system', "
                                     "e.g. \"Acme Cloud\"")
    p.set_defaults(func=cmd_validate)

    args = ap.parse_args(argv)
    if hasattr(args, "confidence") and not 0 < args.confidence < 1:
        fatal("--confidence must be between 0 and 1, e.g. 0.95.")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

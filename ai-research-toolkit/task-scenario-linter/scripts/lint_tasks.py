#!/usr/bin/env python3
"""
Task Scenario Linter - check usability task scenarios before a study runs.

The main check is a literal match of task wording against the product's own
navigation labels and button text. A task that names the button is usually a
task that tests reading, not finding.

Usage:
  python lint_tasks.py tasks.md --vocab nav_labels.txt
  python lint_tasks.py tasks.md --vocab nav.json --mode unmoderated
  python lint_tasks.py tasks.md --vocab nav.txt --study-type quant
  python lint_tasks.py tasks.md --vocab nav.txt --allow-terms "Approvals,Search"
  python lint_tasks.py tasks.md --vocab nav.txt --json findings.json

Exit codes: 0 no criticals, 1 at least one critical, 2 input error.

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Heuristic, not from the literature: above roughly this many words a
# participant tends to re-read the task instead of attempting it.
MAX_WORDS = 60

# Working default, not from the literature: labels shorter than this match too
# much ordinary text to be useful.
MIN_TERM_CHARS = 3

# Single-word labels that are also everyday words. A hit on one of these is a
# warning, not a critical: "search for the invoice" or "you need help" is
# usually ordinary language rather than the participant being handed the
# label. Heuristic list; extend it if your product's labels are similar.
COMMON_WORD_LABELS = {
    "home", "help", "search", "setting", "account", "profile", "share",
    "save", "send", "edit", "delete", "add", "new", "open", "close", "cancel",
    "done", "next", "back", "more", "menu", "start", "view", "print",
    "download", "upload", "filter", "sort", "support", "contact", "about",
    "message", "notification", "people", "team", "history", "file", "inbox",
    "calendar",
}

INSTRUCTION_VERBS = [
    "click", "tap", "press", "select", "choose", "navigate", "go to",
    "open the", "scroll to", "type", "enter", "use the", "hit the",
    "find the button", "drag", "hover over", "expand the", "collapse the",
]

DEPENDENCY_MARKERS = [
    r"\bthe (one|item|project|file|report|study) you (just )?(created|made|saved|set up)\b",
    r"\bfrom the (previous|last|earlier) task\b",
    r"\bas (you did )?(before|earlier|above)\b",
    r"\bagain\b",
    r"\bthat (same|one)\b",
    r"\bin task \d+\b",
]

PRIMING_WORDS = [
    (r"\beasy\b", "tells the participant it should be easy"),
    (r"\beasily\b", "tells the participant it should be easy"),
    (r"\bsimply\b", "tells the participant it should be easy"),
    (r"(?<!you've )(?<!you have )(?<!you'd )\bjust\b"
     r"(?!\s+(?:been|had|got|now|finished|started|arrived|joined))",
     "minimises the task before they attempt it"),
    (r"\bquickly\b", "introduces a speed expectation the study did not set"),
    (r"\bnew\b", "draws attention to recency, which primes exploration"),
    (r"\bimproved\b", "evaluative"),
    (r"\bhandy\b", "evaluative"),
    (r"\buseful\b", "evaluative"),
    (r"\bintuitive\b", "evaluative, and the thing you are trying to measure"),
    (r"\bobviously\b", "presupposes the answer"),
]

# Framing that gives the participant a reason to act. Without one, the task is
# an instruction rather than a scenario.
CONTEXT_MARKERS = [
    r"\byou (want|need|would like|have decided|are trying)\b",
    r"\byou'd (like|want|need)\b",
    r"\byou('ve| have) just\b",
    r"\byou('re| are)\b",
    r"\byour (goal|job|manager|team|colleague)\b",
    r"\bimagine\b", r"\bsuppose\b", r"\bbecause\b",
    r"\bso that\b", r"\bin order to\b",
]

SUCCESS_MARKERS = [
    r"\buntil you\b", r"\bwhen you have\b", r"\byou are done when\b",
    r"\bstop when\b", r"\bsuccess\b", r"\bfinish(ed)? when\b",
    r"\btell (me|us) when\b", r"\blet (me|us) know when\b",
]

# Hypothetical framing asks the participant to describe or imagine rather than
# act. NN/g's task-writing guidance prefers direct imperatives.
HYPOTHETICAL_MARKERS = [
    r"\bshow (me|us) how you would\b",
    r"\bhow would you\b",
    r"\bhow might you\b",
    r"\bwhat would you do\b",
    r"\bwhere would you\b",
]


class InputError(Exception):
    pass


class Task:
    """number is the task's position in the file (1..n), so findings for two
    tasks never merge. label is the number the author wrote, which may repeat."""

    def __init__(self, number: int, text: str, line: int,
                 label: Optional[str] = None) -> None:
        self.number, self.text, self.line = number, text.strip(), line
        self.label = label if label is not None else str(number)


class Finding:
    def __init__(self, severity: str, check: str, task: int, message: str,
                 label: Optional[str] = None) -> None:
        self.severity, self.check, self.task, self.message = severity, check, task, message
        self.label = label if label is not None else str(task)

    def to_dict(self) -> Dict[str, Any]:
        return {"severity": self.severity, "check": self.check,
                "task": self.task, "task_label": self.label,
                "message": self.message}


# --- vocabulary ------------------------------------------------------------

def _core(term: str) -> str:
    """The label without leading or trailing symbols, so "+ New" matches "new"."""
    return re.sub(r"^\W+|\W+$", "", term.strip())


def _singular(word: str) -> str:
    w = word.lower()
    if len(w) > 4 and w.endswith("ies"):
        return w[:-3] + "y"
    if len(w) > 4 and re.search(r"(xes|ches|shes|sses|zes)$", w):
        return w[:-2]
    if w in ("news", "series", "status", "canvas", "analysis"):
        return w
    if len(w) > 3 and w.endswith("s") and not re.search(r"(ss|us|is)$", w):
        return w[:-1]
    return w


def normalise_term(term: str) -> str:
    """Lowercase, symbols stripped, last word singular. "+ New Reports" -> "new report"."""
    words = _core(term).lower().split()
    if words:
        words[-1] = _singular(words[-1])
    return " ".join(words)


def term_pattern(term: str) -> str:
    """Regex for a label that also matches its singular or plural form."""
    words = _core(term).lower().split()
    last = _singular(words[-1])
    if len(last) > 2 and last.endswith("y") and last[-2] not in "aeiou":
        last_re = re.escape(last[:-1]) + "(?:y|ies)"
    else:
        last_re = re.escape(last) + "(?:s|es)?"
    parts = [re.escape(w) for w in words[:-1]] + [last_re]
    return r"(?<!\w)" + r"\s+".join(parts) + r"(?!\w)"


def is_common_word_label(term: str) -> bool:
    norm = normalise_term(term)
    return " " not in norm and norm in COMMON_WORD_LABELS


def load_vocab(path: str) -> List[str]:
    p = Path(path)
    if not p.exists():
        raise InputError("no such file: %s" % path)
    if p.suffix.lower() == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except ValueError as e:
            raise InputError("%s is not valid JSON (%s)" % (path, e))
        shape = ("%s must be a JSON list of strings, or an object whose values "
                 "are strings or lists of strings" % path)
        terms: List[Any] = []
        if isinstance(data, dict):
            for key, v in data.items():
                if isinstance(v, list):
                    terms.extend(v)
                elif isinstance(v, str):
                    terms.append(v)
                else:
                    raise InputError('%s. The value for "%s" is a %s.'
                                     % (shape, key, type(v).__name__))
        elif isinstance(data, list):
            terms = list(data)
        else:
            raise InputError(shape)
        bad = [t for t in terms if not isinstance(t, str)]
        if bad:
            raise InputError("%s. Found a non-string term: %s"
                             % (shape, json.dumps(bad[0])))
    else:
        terms = p.read_text(encoding="utf-8").splitlines()
    out = []
    for t in terms:
        t = t.strip()
        # One- and two-character labels match everything.
        if len(_core(t)) >= MIN_TERM_CHARS:
            out.append(t)
    return sorted(set(out), key=lambda s: (-len(_core(s)), s))


def parse_allow_terms(values: Optional[List[str]]) -> List[str]:
    out: List[str] = []
    for v in values or []:
        out.extend(x.strip() for x in v.split(",") if x.strip())
    return out


# --- task parsing ----------------------------------------------------------

HEADING_TASK = re.compile(
    r"^\s*#{1,6}\s*(?:task\s*)?(\d{1,3})\b\s*[.):\-–—]?\s*(.*)$", re.I)
WORD_TASK = re.compile(
    r"^\s*(?:\*\*)?task\s*(\d{1,3})(?:\s*[.):\-–—]\s*(?:\*\*)?\s*(.*)|\s*(?:\*\*)?\s*)$",
    re.I)
LIST_TASK = re.compile(r"^(\s*)(\d{1,3})[.):]\s+(.*)$")
BULLET = re.compile(r"^(\s*)[-*+]\s+(.*)$")
HEADING = re.compile(r"^\s*#{1,6}\s")


def parse_tasks(text: str) -> List[Task]:
    """Split a tasks file into tasks.

    A new task starts at a numbered item ("1.", "2)"), a "Task 1:" line, a
    numbered heading ("## Task 1", "## 1)"), or a bullet. A marker with no text
    after it ("## Task 1", "Task 1:") takes the following lines, across blank
    lines, until the next marker or heading. A marker with inline text ends at
    the next blank line. Bullets indented under a numbered task stay part of
    it. Text outside any marker is ignored, unless the file has no markers at
    all, in which case the whole file is one task.
    """
    found: List[Dict[str, Any]] = []
    cur: Dict[str, Any] = {}

    def flush() -> None:
        if cur and cur["parts"] and cur["kind"] != "loose":
            found.append(dict(cur))
        cur.clear()

    def start(label: Optional[str], first: str, line: int, block: bool,
              kind: str, indent: int) -> None:
        flush()
        cur.update(label=label, parts=[first.strip()] if first.strip() else [],
                   line=line, block=block, kind=kind, indent=indent)

    lines = text.splitlines()
    for i, line in enumerate(lines):
        n = i + 1
        m = HEADING_TASK.match(line)
        if m:
            start(m.group(1), m.group(2), n, not m.group(2).strip(), "heading", 0)
            continue
        m = WORD_TASK.match(line)
        if m:
            rest = m.group(2) or ""
            start(m.group(1), rest, n, not rest.strip(), "word", 0)
            continue
        m = LIST_TASK.match(line)
        if m:
            start(m.group(2), m.group(3), n, False, "list", len(m.group(1)))
            continue
        if HEADING.match(line):
            # A heading that is not a task marker ("# Tasks") ends the task.
            flush()
            continue
        m = BULLET.match(line)
        if m:
            indent = len(m.group(1))
            nested = (cur and cur["kind"] in ("list", "heading", "word")
                      and (cur["block"] or indent > cur["indent"]))
            if nested:
                cur["parts"].append(m.group(2).strip())
            else:
                start(None, m.group(2), n, False, "bullet", indent)
            continue
        if line.strip():
            if cur:
                cur["parts"].append(line.strip())
            else:
                cur.update(label=None, parts=[line.strip()], line=n,
                           block=False, kind="loose", indent=0)
        elif cur and not cur["block"]:
            flush()
    flush()

    if not found:
        body = " ".join(ln.strip() for ln in lines if ln.strip())
        return [Task(1, body, 1)] if body else []

    tasks = []
    for idx, t in enumerate(found, 1):
        tasks.append(Task(idx, " ".join(t["parts"]), t["line"],
                          t["label"] if t["label"] is not None else str(idx)))
    return tasks


# --- checks ----------------------------------------------------------------

def find_vocab_hits(low: str, vocab: List[str],
                    allow: Optional[List[str]] = None) -> List[str]:
    allowed = {normalise_term(a) for a in (allow or [])}
    hits: List[str] = []
    covered: List[tuple] = []
    seen = set()
    # vocab is sorted longest first, so "Account Settings" claims its span
    # before "Settings" can, and "Reports" before "Report".
    for term in vocab:
        norm = normalise_term(term)
        if norm in allowed or norm in seen:
            continue
        new_span = False
        for m in re.finditer(term_pattern(term), low):
            if not any(a <= m.start() and m.end() <= b for a, b in covered):
                new_span = True
            covered.append((m.start(), m.end()))
        if new_span:
            hits.append(term)
            seen.add(norm)
    return hits


def missing_end_state_severity(study_type: str, mode: str) -> Optional[str]:
    if study_type == "tree":
        return None  # choosing a node is the end state
    if study_type == "quant":
        return "critical"
    return "warning"


def lint_task(task: Task, vocab: List[str], mode: str = "moderated",
              study_type: str = "qual",
              allow: Optional[List[str]] = None) -> List[Finding]:
    f: List[Finding] = []
    text = task.text
    low = text.lower().replace("’", "'").replace("‘", "'")

    def add(sev: str, check: str, msg: str) -> None:
        f.append(Finding(sev, check, task.number, msg, task.label))

    # 1. Product vocabulary. The check this skill exists for.
    hits = find_vocab_hits(low, vocab, allow)
    for term in hits:
        if is_common_word_label(term):
            add("warning", "ui-vocabulary",
                'Uses "%s", which is a product label and also an everyday word. '
                "Check whether the task points the participant at the label. If "
                "the use is intentional, pass it with --allow-terms." % term)
        else:
            add("critical", "ui-vocabulary",
                'Uses the product\'s own label "%s". The participant can match '
                "the word on screen instead of finding the feature, so the task "
                "tests reading rather than discoverability." % term)

    # 2. Embedded instructions.
    for verb in INSTRUCTION_VERBS:
        if re.search(r"\b%s\b" % re.escape(verb), low):
            add("critical" if hits else "warning", "embedded-instruction",
                'Contains the instruction "%s". A scenario gives a goal; naming '
                "the action removes the decision you are trying to observe." % verb)
            break

    # 3. Dependencies between tasks.
    for pattern in DEPENDENCY_MARKERS:
        m = re.search(pattern, low)
        if m:
            add("warning", "task-dependency",
                'Depends on an earlier task ("%s"). If the earlier task fails, '
                "this one cannot be attempted and you lose two data points "
                "instead of one. It also stops you randomising task order."
                % m.group(0))
            break

    # 4. Priming and evaluative language.
    for pattern, why in PRIMING_WORDS:
        m = re.search(pattern, low)
        if m:
            add("warning", "priming", 'The word "%s" %s.' % (m.group(0), why))

    # 5. Hypothetical wording. Tree tests ask "where would you look" by design.
    if study_type != "tree":
        for pattern in HYPOTHETICAL_MARKERS:
            m = re.search(pattern, low)
            if m:
                add("warning", "hypothetical",
                    'Hypothetical wording ("%s"). Ask the participant to do the '
                    "thing rather than describe how they would; NN/g's task "
                    "guidance prefers a direct imperative." % m.group(0))
                break

    # 6. Context.
    if not any(re.search(p, low) for p in CONTEXT_MARKERS):
        add("warning", "no-context",
            "No scenario framing. Nothing tells the participant why they would "
            "be doing this, so they optimise for completing your instruction "
            "rather than their goal.")

    # 7. Success criteria. Severity depends on the study type and mode.
    sev = missing_end_state_severity(study_type, mode)
    if sev and not any(re.search(p, low) for p in SUCCESS_MARKERS):
        if study_type == "quant":
            why = ("In a quantitative study the completion rate is the measure, "
                   "so the participant must know when they are done.")
        elif mode == "unmoderated":
            why = ("In an unmoderated study there is no moderator to ask, so the "
                   "participant decides when they are done.")
        else:
            why = ("A moderator can clarify live, which lowers the risk, but "
                   "agree the criterion before the sessions start.")
        add(sev, "no-success-criteria", "No stated end state. " + why)

    # 8. Length. Heuristic threshold.
    words = len(re.findall(r"\b\w+\b", text))
    if words > MAX_WORDS:
        add("warning", "length",
            "%d words. As a heuristic, above about %d a participant re-reads the "
            "task instead of attempting it." % (words, MAX_WORDS))

    # 9. Over-specified sequence.
    if re.search(r"\bfirst\b.{0,120}\bthen\b", low):
        add("warning", "over-specified",
            "Prescribes a sequence (\"first ... then ...\"). The order a "
            "participant chooses is usually the finding.")

    # 10. Several tasks in one.
    if re.search(r"\band then\b", low):
        add("warning", "multiple-tasks",
            "Joins steps with \"and then\". That is usually two tasks in one: "
            "if the first part fails you cannot see the second, and the "
            "completion result covers both. Split it.")

    return f


# --- output ----------------------------------------------------------------

def render(tasks: List[Task], findings: List[Finding], vocab: List[str],
           mode: str, source: str, study_type: str = "qual",
           allow: Optional[List[str]] = None) -> str:
    L = ["Task scenario lint: %s" % source, "=" * 60]
    L.append("%d task(s) · %d vocabulary term(s) · %s %s study"
             % (len(tasks), len(vocab), mode, study_type))
    if allow:
        L.append("Allowed terms (not checked): %s" % ", ".join(allow))
    L.append("")

    by_task: Dict[int, List[Finding]] = {}
    for f in findings:
        by_task.setdefault(f.task, []).append(f)

    for t in tasks:
        items = by_task.get(t.number, [])
        crit = sum(1 for i in items if i.severity == "critical")
        status = "FAIL" if crit else ("review" if items else "ok")
        name = "Task %d" % t.number
        if t.label != str(t.number):
            name += " (numbered %s in the file)" % t.label
        L.append("%s [%s]  %s" % (name, status,
                                  t.text[:70] + ("..." if len(t.text) > 70 else "")))
        for i in items:
            L.append("    %-8s (%s) %s" % (i.severity.upper(), i.check, i.message))
        L.append("")

    crit_total = sum(1 for f in findings if f.severity == "critical")
    L.append("%d critical, %d warning, %d note"
             % (crit_total,
                sum(1 for f in findings if f.severity == "warning"),
                sum(1 for f in findings if f.severity == "note")))
    if crit_total:
        L.append("")
        L.append("Fix the criticals before fielding. A task naming the product's own "
                 "label produces a completion rate that measures reading.")
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="lint_tasks.py",
        description="Check usability task scenarios before a study runs.")
    ap.add_argument("tasks")
    ap.add_argument("--vocab", required=True,
                    help="product nav labels and button text, one per line or JSON")
    ap.add_argument("--mode", choices=["moderated", "unmoderated"],
                    default="moderated")
    ap.add_argument("--study-type", choices=["qual", "quant", "tree"],
                    default="qual",
                    help="qual (default), quant (completion rates are reported), "
                         "or tree (tree test)")
    ap.add_argument("--allow-terms", action="append", metavar="TERMS",
                    help="comma-separated labels the study names on purpose; "
                         "repeatable")
    ap.add_argument("--json", help="also write findings as JSON")
    args = ap.parse_args(argv)

    try:
        p = Path(args.tasks)
        if not p.exists():
            raise InputError("no such file: %s" % args.tasks)
        vocab = load_vocab(args.vocab)
        if not vocab:
            raise InputError("no usable terms in %s (terms under %d characters "
                             "are skipped because they match everything)"
                             % (args.vocab, MIN_TERM_CHARS))
        tasks = parse_tasks(p.read_text(encoding="utf-8"))
        if not tasks:
            raise InputError("no tasks found in %s (the file is empty)" % args.tasks)
    except InputError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2

    allow = parse_allow_terms(args.allow_terms)
    findings: List[Finding] = []
    for t in tasks:
        findings.extend(lint_task(t, vocab, args.mode, args.study_type, allow))

    print(render(tasks, findings, vocab, args.mode, p.name, args.study_type, allow))

    if args.json:
        Path(args.json).write_text(json.dumps(
            [f.to_dict() for f in findings], indent=2) + "\n", encoding="utf-8")
        print("\nwrote %s" % args.json)

    return 1 if any(f.severity == "critical" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

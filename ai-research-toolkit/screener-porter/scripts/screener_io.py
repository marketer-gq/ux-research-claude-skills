#!/usr/bin/env python3
"""
Screener Porter - move participant screeners between tools as portable files,
and pre-flight them before launch.

Works on an export from any platform. Nothing here talks to a research tool.

Subcommands:
  export      normalise an exported screener (JSON or CSV) into the portable format
  check       run launch pre-flight checks; exits 1 when blockers are found
  plan        turn a portable screener into an ordered list of write intents
  fingerprint record red-herring question fingerprints after a launch

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

FORMAT_VERSION = 1
FINGERPRINT_FILE = ".screener-fingerprints.json"

# Seconds per question, used only for the completion-time estimate.
# Working defaults, unsourced: for comparing two drafts, not for predicting.
SECONDS_CLOSED = 15
SECONDS_OPEN = 45

DEFAULT_RULES = {
    "max_questions": 10,          # working default, unsourced; a warning only
    "max_open_ended": 2,
    "unmapped_attribute_policy": "warning",  # or "blocker"
    "red_herring_reuse_days": 180,  # heuristic
    "red_herring_marker": "[RH]",
}

# Attribute value for a question whose answer is deliberately not kept as a
# profile attribute (data minimisation). Not flagged as unmapped.
SCREENER_ONLY_TAGS = {"screener-only", "screener_only", "screener only"}

# Key candidates seen across platform exports. The exporter stays tolerant
# rather than assuming one schema; unmapped fields are reported by name.
QUESTION_CONTAINER_KEYS = ["questions", "screener_questions", "items", "data",
                           "attributes"]
# Great Question's MCP puts the question text in `label` and has no separate
# internal label, so `label` is read as text here, not as an internal label.
FIELD_ALIASES = {
    "text": ["text", "question", "title", "label", "prompt", "body"],
    "type": ["question_type", "type", "kind", "format"],
    "options": ["options", "choices", "answers", "values"],
    "required": ["required", "is_required", "mandatory"],
    "attribute": ["attribute", "attribute_id", "candidate_attribute",
                  "attribute_key", "maps_to"],
    "qualify_if": ["qualifying_answers", "qualifying_options", "qualify_if",
                   "screen_in", "screen_in_options"],
    "disqualify_if": ["disqualifying_answers", "disqualifying_options",
                      "disqualify_if", "disqualify", "screen_out",
                      "screen_out_options"],
    "helper": ["helper", "help_text", "hint", "description"],
    "skip_logic": ["skip_logic", "logic", "branching"],
    "position": ["position", "order", "index"],
    "label": ["internal_label", "admin_label"],
    "id": ["id", "uuid", "key", "question_id"],
}

CLOSED_TYPES = {"single_choice", "multiple_choice", "single_select",
                "multi_select", "multiselect", "yes_no", "boolean", "dropdown",
                "select", "radio", "checkbox", "scale", "rating", "nps", "likert",
                "ranking", "matrix", "opinion_scale"}
YES_NO_TYPES = {"yes_no", "boolean", "yesno"}

OPEN_ENDED_TYPES = {"open", "open_ended", "text", "long_text", "short_text",
                    "free_text", "paragraph", "textarea"}

DEMOGRAPHIC_PATTERNS = [
    r"\bage\b", r"\bgender\b", r"\bincome\b", r"\beducation\b",
    r"\bethnicit", r"\bhousehold\b", r"\bmarital\b", r"\bwhere do you live\b",
    r"\bcountry\b", r"\bregion\b", r"\bzip\b", r"\bpostcode\b",
    r"\bcompany size\b", r"\bhow many employees\b",
    r"\bhow many people work\b", r"\bpeople work at your\b",
    r"\bsize of your (company|organi[sz]ation)\b",
]

# Advisory only. Wording is a judgement call; these are prompts for a human.
# Evaluative adjectives are only flagged when they describe the thing being
# asked about ("How great was...", "Was the setup great?"). The adjective is
# matched lower-case only, so proper nouns such as "Great Question" or
# "Great Britain" pass.
_EVALUATIVE = r"(great|excellent|terrible|awful|amazing)"
LEADING_PATTERNS = [
    (r"(?i:\bdon'?t you\b)", "tag question invites agreement"),
    (r"(?i:\bwouldn'?t you\b)", "tag question invites agreement"),
    (r"(?i:\bdo you agree that\b)", "presupposes the proposition"),
    (r"(?i:\bhow (much|often) do you (love|enjoy|like)\b)", "presupposes a positive"),
    (r"(?i:\bhow (frustrating|difficult|painful)\b)", "presupposes a negative"),
    (r"(?i:\bhow )" + _EVALUATIVE + r"\b", "evaluative adjective describes the thing asked about"),
    (r"(?i:\b(is|was|are|were|be|been|find|found)\b)(\s+[\w'-]+){0,3}\s+"
     + _EVALUATIVE + r"\b", "evaluative adjective describes the thing asked about"),
    (r"(?i:\bobviously\b)", "presupposes the answer"),
    (r"(?i:\bmost people\b)", "social proof primes the answer"),
]

# Possible GDPR Article 9 special-category data. Keyword-based and advisory.
SPECIAL_CATEGORY_PATTERNS = [
    (r"\b(health|medical|medication|diagnos\w*|disabilit\w*|illness|"
     r"chronic condition|pregnan\w*)\b", "health"),
    (r"\b(ethnic\w*|racial)\b", "racial or ethnic origin"),
    (r"\b(sexual orientation|sexuality|sex life|lgbt\w*)\b",
     "sex life or sexual orientation"),
    (r"\b(religio\w*|faith|philosophical beliefs?)\b",
     "religious or philosophical beliefs"),
    (r"\b(politic\w*|voted?|voting)\b", "political opinions"),
    (r"\b(trade union|union member\w*|labou?r union)\b", "trade union membership"),
    (r"\b(biometric\w*|fingerprints?|facial recognition|face scan|genetic\w*|dna)\b",
     "biometric or genetic data"),
]
# Demographic questions where respondents should be able to decline.
SENSITIVE_DEMOGRAPHIC_PATTERNS = [
    r"\bage\b", r"\bhow old\b", r"\bgender\b", r"\bincome\b", r"\bsalary\b",
] + [p for p, _ in SPECIAL_CATEGORY_PATTERNS]
PREFER_NOT_PATTERN = re.compile(
    r"prefer not|rather not|decline|not to (say|answer|disclose)", re.I)
PRIVACY_PATTERN = re.compile(
    r"\b(privacy|consent|personal data|data protection)\b", re.I)
PRIVACY_META_KEYS = ["privacy_notice", "privacy_policy", "consent_text",
                     "consent", "consent_form"]

# Option-level screening flags some tools put on each option instead of
# listing qualifying / disqualifying answers on the question.
OPTION_DISQUALIFY_KEYS = ["disqualify", "disqualifies", "disqualifying",
                          "is_disqualifying", "screen_out", "reject"]
OPTION_QUALIFY_KEYS = ["qualify", "qualifies", "qualifying", "is_qualifying",
                       "screen_in", "accept"]
OPTION_ACTION_KEYS = ["action", "logic", "outcome", "result"]

# CSV export: one row per question. These columns hold several values,
# separated by "|".
CSV_LIST_FIELDS = ("options", "qualify_if", "disqualify_if")
CSV_LIST_SEPARATOR = "|"

# Great Question MCP. The study-ID argument names were read from the live
# server's own "Missing required arguments" errors on the get_*_screener tools
# on 24 Sep 2026. The create/add argument names mirror the read shape and are
# unverified: the server names any missing argument on the first call.
GQ_TARGETS = {
    "interview": {"id_arg": "interview_id",
                  "get": "get_interview_screener",
                  "create": "create_interview_screener",
                  "add": "add_interview_screener_question",
                  "template": "apply_interview_screener_template"},
    "unmoderated": {"id_arg": "unmoderated_study_id",
                    "get": "get_unmoderated_screener",
                    "create": "create_unmoderated_screener",
                    "add": "add_unmoderated_screener_question",
                    "template": "apply_unmoderated_screener_template"},
    "survey": {"id_arg": "survey_id",
               "get": "get_survey_screener",
               "create": "create_survey_screener",
               "add": "add_survey_screener_question",
               "template": "apply_survey_screener_template"},
}
# Great Question study `style` values seen on list_studies, mapped to screener type.
GQ_STYLE_TO_TYPE = {"video_call": "interview", "unmoderated_test": "unmoderated",
                    "survey": "survey"}
# Accepted by both `export --study-type` and `plan --study-type`.
STUDY_TYPE_CHOICES = ["survey", "interview", "unmoderated",
                      "video_call", "unmoderated_test"]

# The only question types observed on a live Great Question screener read.
# The plan never emits any other type: anything that does not map onto one of
# these is left unresolved for a person to decide.
GQ_QUESTION_TYPES = {"single_choice", "multiple_choice", "long_text", "yes_no"}
GQ_TYPE_MAP = {
    "single_choice": "single_choice", "single_select": "single_choice",
    "radio": "single_choice", "dropdown": "single_choice", "select": "single_choice",
    "multiple_choice": "multiple_choice", "multi_select": "multiple_choice",
    "multiselect": "multiple_choice", "checkbox": "multiple_choice",
    "checkboxes": "multiple_choice",
    "yes_no": "yes_no", "boolean": "yes_no", "yesno": "yes_no", "bool": "yes_no",
    "long_text": "long_text", "open": "long_text", "open_ended": "long_text",
    "text": "long_text", "short_text": "long_text", "free_text": "long_text",
    "paragraph": "long_text", "textarea": "long_text",
}

OTHER_SPECIFY_PATTERN = re.compile(r"other\b.{0,20}(specify|please)", re.I)


# ---------------------------------------------------------------- utilities

def _first(d: Dict[str, Any], names: List[str], default: Any = None) -> Any:
    for n in names:
        if n in d and d[n] not in (None, ""):
            return d[n]
    return default


def _norm_text(s: str) -> str:
    """Normalise question text for fingerprinting: lowercase, collapse
    whitespace, drop punctuation."""
    s = s.lower()
    s = re.sub(r"[^\w\s]", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def fingerprint(text: str) -> str:
    return hashlib.sha256(_norm_text(text).encode("utf-8")).hexdigest()[:16]


def _load_json(path: str) -> Any:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        sys.exit(f"error: no such file: {path}")
    except json.JSONDecodeError as exc:
        sys.exit(f"error: {path} is not valid JSON: {exc}")


def _is_open_ended(q: Dict[str, Any]) -> bool:
    if q.get("open_ended") is not None:
        return bool(q["open_ended"])
    qtype = (q.get("type") or "").lower().replace("-", "_").replace(" ", "_")
    if qtype in OPEN_ENDED_TYPES:
        return True
    if qtype in CLOSED_TYPES:
        return False
    # Unknown type: no options means free text in practice.
    return not q.get("options")


def _has_screening_logic(q: Dict[str, Any]) -> bool:
    return bool(q.get("qualify_if") or q.get("disqualify_if"))


def _norm_type(t: Any) -> str:
    return str(t or "").strip().lower().replace("-", "_").replace(" ", "_")


def _is_screener_only(q: Dict[str, Any]) -> bool:
    return str(q.get("attribute") or "").strip().lower() in SCREENER_ONLY_TAGS


def _is_yes_no(q: Dict[str, Any]) -> bool:
    if _norm_type(q.get("type")) in YES_NO_TYPES:
        return True
    opts = {str(o).strip().lower() for o in (q.get("options") or [])}
    return opts == {"yes", "no"}


def _truthy(v: Any) -> bool:
    if isinstance(v, str):
        return v.strip().lower() in ("1", "true", "yes", "y")
    return bool(v)


def _option_flag(opt: Dict[str, Any]) -> Optional[str]:
    """Return 'disqualify', 'qualify' or None for an option-level flag."""
    if any(_truthy(opt.get(k)) for k in OPTION_DISQUALIFY_KEYS if k in opt):
        return "disqualify"
    if any(_truthy(opt.get(k)) for k in OPTION_QUALIFY_KEYS if k in opt):
        return "qualify"
    for k in OPTION_ACTION_KEYS:
        v = str(opt.get(k) or "").lower()
        if "disqualif" in v or "reject" in v or "screen_out" in v:
            return "disqualify"
        if "qualif" in v or "accept" in v or "screen_in" in v:
            return "qualify"
    return None


def _yes_no_value(v: Any) -> Any:
    if isinstance(v, bool):
        return "Yes" if v else "No"
    s = str(v).strip().lower()
    if s in ("true", "yes", "y", "1"):
        return "Yes"
    if s in ("false", "no", "n", "0"):
        return "No"
    return v


# ------------------------------------------------------------------ export

def find_questions(raw: Any, depth: int = 0) -> List[Dict[str, Any]]:
    """Locate the question list in an exported screener, tolerating wrappers
    such as Great Question's JSON:API shape (data -> attributes -> questions)."""
    if depth > 6:
        return []
    if isinstance(raw, list):
        dicts = [q for q in raw if isinstance(q, dict)]
        if not dicts:
            return []
        if any(a in dicts[0] for a in FIELD_ALIASES["text"]):
            return dicts
        # JSON:API list: data: [{id, type, attributes: {...}}]. Flatten each
        # resource; the resource `type` is the JSON:API type, not a question type.
        if all(isinstance(d.get("attributes"), dict) for d in dicts) and \
                any(a in dicts[0]["attributes"] for a in FIELD_ALIASES["text"]):
            flat = []
            for d in dicts:
                item = dict(d["attributes"])
                if "id" in d and not any(k in item for k in FIELD_ALIASES["id"]):
                    item["id"] = d["id"]
                flat.append(item)
            return flat
        for d in dicts:
            found = find_questions(d, depth + 1)
            if found:
                return found
        return []
    if not isinstance(raw, dict):
        return []
    for key in QUESTION_CONTAINER_KEYS:
        if key in raw:
            found = find_questions(raw[key], depth + 1)
            if found:
                return found
    for val in raw.values():
        if isinstance(val, (dict, list)):
            found = find_questions(val, depth + 1)
            if found:
                return found
    return []


def normalise_question(raw_q: Dict[str, Any], index: int) -> Tuple[Dict[str, Any], List[str], bool]:
    """Return (question, dropped_source_keys, source_had_attribute_field)."""
    q: Dict[str, Any] = {}
    used_keys = set()
    for field, aliases in FIELD_ALIASES.items():
        val = _first(raw_q, aliases)
        if val is not None:
            q[field] = val
        for a in aliases:
            if a in raw_q:
                used_keys.add(a)
    had_attribute = any(a in raw_q for a in FIELD_ALIASES["attribute"])

    q.setdefault("id", "q%d" % (index + 1))
    q["id"] = str(q["id"])
    q.setdefault("text", "")
    q.setdefault("type", "")
    q.setdefault("options", [])
    q.setdefault("required", True)
    q.setdefault("attribute", None)
    q.setdefault("qualify_if", [])
    q.setdefault("disqualify_if", [])

    for key in ("qualify_if", "disqualify_if"):
        if not isinstance(q[key], list):
            q[key] = [q[key]]

    if isinstance(q["options"], list):
        flat = []
        for opt in q["options"]:
            if isinstance(opt, dict):
                text = str(_first(opt, ["text", "label", "value", "title"], ""))
                flat.append(text)
                # Keep option-level screening flags rather than dropping them.
                flag = _option_flag(opt)
                target = {"disqualify": "disqualify_if",
                          "qualify": "qualify_if"}.get(flag or "")
                if text and target and text not in q[target]:
                    q[target].append(text)
            else:
                flat.append(str(opt))
        q["options"] = [o for o in flat if o]

    # Yes/no questions often arrive with no options listed, and some tools
    # record their screening answers as booleans.
    if _norm_type(q.get("type")) in YES_NO_TYPES:
        if not q["options"]:
            q["options"] = ["Yes", "No"]
        for key in ("qualify_if", "disqualify_if"):
            q[key] = [_yes_no_value(v) for v in q[key]]

    q["open_ended"] = _is_open_ended(q)
    dropped = sorted(k for k in raw_q.keys() if k not in used_keys)
    return q, dropped, had_attribute


def read_csv_questions(path: str) -> List[Dict[str, Any]]:
    """Read a CSV export with one row per question. Header names are matched
    against FIELD_ALIASES (case-insensitive, spaces read as underscores).
    Options and qualifying / disqualifying answers are separated by "|"."""
    alias_to_field = {a: f for f, aliases in FIELD_ALIASES.items() for a in aliases}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as fh:
            rows = list(csv.DictReader(fh))
    except FileNotFoundError:
        sys.exit(f"error: no such file: {path}")
    except (csv.Error, UnicodeDecodeError) as exc:
        sys.exit(f"error: {path} is not a readable CSV file: {exc}")

    out = []
    for row in rows:
        item: Dict[str, Any] = {}
        for header, value in row.items():
            if header is None or value is None:
                continue
            key = header.strip().lower().replace(" ", "_").replace("-", "_")
            value = value.strip()
            if not value:
                # Keep an empty attribute column visible, so "this file can
                # carry mappings and this row has none" is not read as "this
                # file cannot carry mappings".
                if alias_to_field.get(key) == "attribute":
                    item[key] = None
                continue
            if alias_to_field.get(key) in CSV_LIST_FIELDS:
                item[key] = [v.strip() for v in value.split(CSV_LIST_SEPARATOR)
                             if v.strip()]
            elif alias_to_field.get(key) == "required":
                item[key] = _truthy(value)
            else:
                item[key] = value
        if any(v is not None for v in item.values()):
            out.append(item)
    return out


def cmd_export(args: argparse.Namespace) -> int:
    is_csv = args.format == "csv" or (args.format is None
                                      and args.input.lower().endswith(".csv"))
    if is_csv:
        raw: Any = {}
        raw_questions = read_csv_questions(args.input)
        raw_questions = [q for q in raw_questions
                         if any(a in q for a in FIELD_ALIASES["text"])]
    else:
        raw = _load_json(args.input)
        raw_questions = find_questions(raw)
    if not raw_questions:
        sys.exit("error: could not find a question list in %s. Check the raw "
                 "response shape and pass the inner object if it is wrapped."
                 % args.input)

    questions = []
    all_dropped = set()
    any_attribute_field = False
    for i, rq in enumerate(raw_questions):
        q, dropped, had_attr = normalise_question(rq, i)
        questions.append(q)
        all_dropped.update(dropped)
        any_attribute_field = any_attribute_field or had_attr

    meta = raw if isinstance(raw, dict) else {}
    study_type = args.study_type or _first(meta, ["study_type", "type"], "")
    study_type = GQ_STYLE_TO_TYPE.get(study_type, study_type)
    portable = {
        "version": FORMAT_VERSION,
        "name": args.name or _first(meta, ["name", "title", "screener_name"],
                                    "Untitled screener"),
        "study_type": study_type,
        "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "attribute_mapping_in_source": any_attribute_field,
        "questions": questions,
    }
    privacy = args.privacy_notice or _first(meta, PRIVACY_META_KEYS)
    if privacy:
        portable["privacy_notice"] = privacy

    Path(args.output).write_text(json.dumps(portable, indent=2) + "\n", encoding="utf-8")
    print("wrote %s (%d questions)" % (args.output, len(questions)))

    if all_dropped:
        print("\nfields present in the source but not carried into the portable "
              "format:\n  " + ", ".join(sorted(all_dropped)))
        print("  If any of those matter, add an alias in FIELD_ALIASES and re-export.")

    if not any_attribute_field:
        print("\nnote: the source carries no attribute-mapping field on any question, so "
              "the mapping check cannot run from this file. (The Great Question MCP "
              "screener read is one such source.)")

    if args.md:
        Path(args.md).write_text(render_markdown(portable), encoding="utf-8")
        print("wrote %s" % args.md)
    return 0


def render_markdown(p: Dict[str, Any]) -> str:
    lines = ["# %s" % p.get("name", "Screener"), ""]
    if p.get("study_type"):
        lines += ["Study type: %s" % p["study_type"], ""]
    if p.get("privacy_notice"):
        lines += ["Privacy notice: %s" % p["privacy_notice"], ""]
    for i, q in enumerate(p["questions"], 1):
        lines.append("## %d. %s" % (i, q.get("text", "").strip() or "(no text)"))
        lines.append("")
        bits = ["Type: `%s`" % (q.get("type") or "unspecified")]
        bits.append("Required: %s" % ("yes" if q.get("required") else "no"))
        if p.get("attribute_mapping_in_source", True):
            bits.append("Attribute: %s" % (q.get("attribute") or "**unmapped**"))
        lines.append(" · ".join(bits))
        lines.append("")
        for opt in q.get("options") or []:
            if opt in (q.get("disqualify_if") or []):
                mark = " **(disqualifies)**"
            elif opt in (q.get("qualify_if") or []):
                mark = " (qualifies)"
            else:
                mark = ""
            lines.append("- %s%s" % (opt, mark))
        if q.get("options"):
            lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------- check

class Report:
    def __init__(self) -> None:
        self.blockers: List[str] = []
        self.warnings: List[str] = []
        self.notes: List[str] = []

    def add(self, level: str, msg: str) -> None:
        getattr(self, level + "s").append(msg)

    def render(self) -> str:
        out = []
        for label, items in (("BLOCKERS", self.blockers),
                             ("WARNINGS", self.warnings),
                             ("NOTES", self.notes)):
            if items:
                out.append("%s (%d)" % (label, len(items)))
                out += ["  - " + i for i in items]
                out.append("")
        if not (self.blockers or self.warnings or self.notes):
            out.append("Clean. No blockers, warnings or notes.")
        return "\n".join(out)


def load_fingerprints(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"version": FORMAT_VERSION, "entries": []}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print("warning: %s is unreadable; treating as empty" % path, file=sys.stderr)
        return {"version": FORMAT_VERSION, "entries": []}


def _is_red_herring(q: Dict[str, Any], marker: str, ids: set) -> bool:
    if str(q.get("id")) in ids:
        return True
    return marker.lower() in str(q.get("label") or "").lower()


def check_screener(portable: Dict[str, Any], rules: Dict[str, Any],
                   fingerprints: Dict[str, Any], rh_ids: Optional[set] = None) -> Report:
    rh_ids = rh_ids or set()
    rep = Report()
    questions = portable.get("questions", [])
    n = len(questions)

    # 1. Length. A warning: drop-off stays roughly flat as closed questions
    # are added, so length alone is not a reason to stop a launch.
    max_q = rules["max_questions"]
    if n > max_q:
        rep.add("warning", "%d questions, limit is %d. Consider cutting %d; "
                           "check whether the extra ones are open-ended."
                % (n, max_q, n - max_q))
    else:
        rep.add("note", "%d questions (limit %d)." % (n, max_q))

    # 2. Open-ended count.
    open_q = [q for q in questions if q.get("open_ended")]
    max_open = rules["max_open_ended"]
    if len(open_q) > max_open:
        rep.add("warning",
                "%d open-ended questions, limit is %d: %s. Open-ended questions "
                "are the main driver of screener drop-off."
                % (len(open_q), max_open,
                   ", ".join(q["id"] for q in open_q)))
    study_type = GQ_STYLE_TO_TYPE.get(portable.get("study_type") or "",
                                      portable.get("study_type") or "")
    if study_type == "interview" and questions and not open_q:
        rep.add("warning", "No open-ended question. For interview recruiting, "
                           "include at least one articulation question (\"Tell "
                           "us about the last time you...\"). It shows whether "
                           "someone can talk about the topic and helps catch "
                           "fraudulent respondents.")

    # 3. Completion time estimate.
    secs = sum(SECONDS_OPEN if q.get("open_ended") else SECONDS_CLOSED
               for q in questions)
    rep.add("note", "Estimated completion time %dm %02ds (assumes %ds per "
                    "closed question, %ds per open one)."
            % (secs // 60, secs % 60, SECONDS_CLOSED, SECONDS_OPEN))

    # 4. Unmapped attributes - only meaningful if the source could carry them.
    # A question tagged "screener-only" is deliberately not kept as a profile
    # attribute (data minimisation) and is not flagged.
    unmapped = [q["id"] for q in questions if not q.get("attribute")]
    if not portable.get("attribute_mapping_in_source", True):
        rep.add("note", "The source export carries no attribute-mapping field, so "
                        "mappings cannot be checked from this file. Confirm them in "
                        "the source tool before relying on this screener for "
                        "filtering.")
    elif unmapped:
        level = "blocker" if rules["unmapped_attribute_policy"] == "blocker" else "warning"
        rep.add(level, "%d question(s) with no attribute mapping: %s. Responses "
                       "to these cannot be filtered on later. If that is "
                       "deliberate, set the attribute to \"screener-only\"."
                % (len(unmapped), ", ".join(unmapped)))

    # 5. Closed questions with no screening logic in either direction.
    no_dq = [q["id"] for q in questions
             if not q.get("open_ended") and q.get("options")
             and not _has_screening_logic(q) and not _is_demographic(q)]
    if no_dq:
        rep.add("warning", "%d closed question(s) with no qualifying or "
                           "disqualifying answers: %s. They look like screening but "
                           "let everyone through." % (len(no_dq), ", ".join(no_dq)))

    # 6. Ordering: demographics before the last qualifying question. A
    # demographic question with screening logic (country, company size) is
    # itself a qualifier and is not flagged.
    demo_idx = [i for i, q in enumerate(questions)
                if _is_demographic(q) and not _has_screening_logic(q)]
    qual_idx = [i for i, q in enumerate(questions) if _has_screening_logic(q)]
    if demo_idx and qual_idx and min(demo_idx) < max(qual_idx):
        early = [questions[i]["id"] for i in demo_idx if i < max(qual_idx)]
        rep.add("warning", "Demographic question(s) %s appear before the last "
                           "qualifying question. Respondents who will not "
                           "qualify answer them for nothing."
                % ", ".join(early))

    # 7. Leading wording (advisory).
    for q in questions:
        text = q.get("text", "")
        for pattern, why in LEADING_PATTERNS:
            if re.search(pattern, text):
                rep.add("warning", "%s wording: %s — \"%s\""
                        % (q["id"], why, text.strip()[:80]))
                break

    # 8. Red herring reuse.
    marker = rules["red_herring_marker"]
    window = rules["red_herring_reuse_days"]
    seen = {e["fingerprint"]: e for e in fingerprints.get("entries", [])}
    now = datetime.now(timezone.utc)
    for q in questions:
        if not _is_red_herring(q, marker, rh_ids):
            continue
        fp = fingerprint(q.get("text", ""))
        prior = seen.get(fp)
        if not prior:
            continue
        try:
            used = datetime.strptime(prior["used_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc)
        except (KeyError, ValueError):
            continue
        age = (now - used).days
        if age <= window:
            rep.add("warning", "%s is a red herring last used %d days ago on "
                               "\"%s\" (reuse window %d days). It is burned — "
                               "respondents have learned the answer."
                    % (q["id"], age, prior.get("study", "an earlier study"), window))

    # 9. Other-specify options.
    other_qs = [q["id"] for q in questions
                if any(OTHER_SPECIFY_PATTERN.search(o) for o in (q.get("options") or []))]
    if other_qs:
        rep.add("note", "Question(s) %s contain an \"Other — please specify\" "
                        "option. Filtering "
                        "on the parent \"Other\" separately from its free-text "
                        "sub-answers is a known limitation; see "
                        "references/known_limitations.md."
                % ", ".join(other_qs))

    # 10. Yes/no screening questions make the qualifying answer easy to guess.
    yn = [q["id"] for q in questions if _is_yes_no(q)]
    if yn:
        rep.add("warning", "Yes/no question(s) %s. A yes/no screening question "
                           "signals the answer you want. Ask a multiple-choice "
                           "question where the qualifying answer is one of "
                           "several plausible options." % ", ".join(yn))

    # 11. Possible GDPR Article 9 special-category data.
    special = []
    for q in questions:
        text = q.get("text") or ""
        cats = [cat for pat, cat in SPECIAL_CATEGORY_PATTERNS
                if re.search(pat, text, re.I)]
        if cats:
            special.append("%s (%s)" % (q["id"], ", ".join(cats)))
    if special:
        rep.add("warning", "Possible special-category data under GDPR Article 9: "
                           "%s. These need explicit consent from the respondent, "
                           "and a reason to collect them at all."
                % "; ".join(special))

    # 12. Privacy notice or consent text.
    has_privacy = bool(portable.get("privacy_notice")) or any(
        PRIVACY_PATTERN.search(str(q.get("text") or "") + " "
                               + str(q.get("helper") or ""))
        for q in questions)
    if questions and not has_privacy:
        rep.add("warning", "No privacy notice or consent text found. If the "
                           "destination attaches one at study level, confirm it "
                           "is attached and set \"privacy_notice\" in this file.")

    # 13. Sensitive demographics with no way to decline.
    no_decline = [q["id"] for q in questions
                  if not q.get("open_ended") and q.get("options")
                  and any(re.search(p, q.get("text") or "", re.I)
                          for p in SENSITIVE_DEMOGRAPHIC_PATTERNS)
                  and not any(PREFER_NOT_PATTERN.search(str(o))
                              for o in q["options"])]
    if no_decline:
        rep.add("warning", "Sensitive question(s) %s have no \"Prefer not to say\" "
                           "option." % ", ".join(no_decline))

    return rep


def _is_demographic(q: Dict[str, Any]) -> bool:
    text = (q.get("text") or "").lower()
    return any(re.search(p, text) for p in DEMOGRAPHIC_PATTERNS)


def cmd_check(args: argparse.Namespace) -> int:
    portable = _load_json(args.input)
    rules = dict(DEFAULT_RULES)
    if args.rules:
        rules.update(_load_json(args.rules))
    fps = load_fingerprints(args.fingerprints)
    rep = check_screener(portable, rules, fps, _parse_ids(args.red_herrings))

    print("Screener pre-flight: %s" % portable.get("name", args.input))
    print("=" * 60)
    print(rep.render())

    if rep.blockers:
        print("FAIL: %d blocker(s). Not ready to launch." % len(rep.blockers))
        return 1
    print("PASS: no blockers.")
    return 0


# -------------------------------------------------------------------- plan

def gq_question_type(q: Dict[str, Any]) -> Optional[str]:
    """Map a portable question type onto a Great Question type, or None when
    there is no documented equivalent. Never passes an unknown type through."""
    qtype = _norm_type(q.get("type"))
    if qtype:
        return GQ_TYPE_MAP.get(qtype)
    # No type in the source: infer only the unambiguous cases.
    if _is_yes_no(q):
        return "yes_no"
    if q.get("open_ended") or not q.get("options"):
        return "long_text"
    return None


def cmd_plan(args: argparse.Namespace) -> int:
    portable = _load_json(args.input)
    study_type = args.study_type or portable.get("study_type")
    if not study_type:
        sys.exit("error: --study-type is required (survey, interview or unmoderated)")
    study_type = GQ_STYLE_TO_TYPE.get(study_type, study_type)
    gq = args.target == "gq"
    if gq and study_type not in GQ_TARGETS:
        sys.exit("error: --target gq needs --study-type interview, unmoderated or survey")
    if gq and not args.study_id:
        sys.exit("error: --target gq needs --study-id (the Great Question study id)")
    study_id: Optional[int] = None
    if gq:
        try:
            study_id = int(str(args.study_id).strip())
        except ValueError:
            sys.exit("error: --study-id must be a whole number, the numeric Great "
                     "Question study id (got %r)" % args.study_id)

    steps: List[Dict[str, Any]] = []
    plan_warnings: List[str] = []
    if gq:
        t = GQ_TARGETS[study_type]
        steps.append({
            "step": 1, "tool": t["create"],
            "arguments": {t["id_arg"]: study_id},
            "note": "skip if the study already has a screener (has_screener on "
                    "list_studies); check list_templates first — %s is cheaper than "
                    "adding questions one by one" % t["template"],
        })
    else:
        steps.append({
            "step": 1,
            "intent": "create the %s screener on the target study" % study_type,
            "arguments": {"study_type": study_type,
                          "name": portable.get("name", "Screener")},
        })

    mappings_in_source = portable.get("attribute_mapping_in_source", True)
    for i, q in enumerate(portable.get("questions", []), start=2):
        pre: List[str] = []
        warn: List[str] = []
        attribute = q.get("attribute")
        if mappings_in_source and not attribute:
            pre.append("no attribute mapping — resolve before writing, or set "
                       "it to \"screener-only\" if the answer should not be kept")
        if gq:
            t = GQ_TARGETS[study_type]
            src_type = _norm_type(q.get("type"))
            gq_type = gq_question_type(q)
            if gq_type is None:
                pre.append("source type '%s' has no documented Great Question "
                           "equivalent (known types: %s). Decide the type by "
                           "hand; do not split a matrix into single-selects "
                           "silently." % (q.get("type") or "unspecified",
                                          ", ".join(sorted(GQ_QUESTION_TYPES))))
            elif src_type and src_type != gq_type:
                warn.append("question type '%s' mapped to '%s'"
                            % (q.get("type"), gq_type))
            a = {t["id_arg"]: study_id,
                 "label": q.get("text", ""),
                 "question_type": gq_type,
                 "required": q.get("required", True),
                 "options": [] if gq_type == "yes_no" else q.get("options", []),
                 "qualifying_answers": q.get("qualify_if", []),
                 "disqualifying_answers": q.get("disqualify_if", [])}
            if q.get("helper"):
                a["helper"] = q["helper"]
            if q.get("skip_logic"):
                warn.append("skip_logic is not carried into this plan; "
                            "re-create it in Great Question after the import")
            step = {"step": i, "tool": t["add"], "arguments": a,
                    "preconditions": pre}
            if attribute:
                # Carried through, but not as a tool argument: the screener
                # write has no documented attribute field.
                step["attribute"] = attribute
                if not _is_screener_only(q):
                    warn.append("set attribute mapping '%s' on this question in "
                                "Great Question after it is created" % attribute)
            if warn:
                step["warnings"] = warn
            steps.append(step)
        else:
            steps.append({
                "step": i,
                "intent": "add a screener question to the %s screener" % study_type,
                "arguments": {
                    "text": q.get("text", ""), "type": q.get("type", ""),
                    "options": q.get("options", []),
                    "required": q.get("required", True),
                    "attribute": attribute,
                    "qualify_if": q.get("qualify_if", []),
                    "disqualify_if": q.get("disqualify_if", []),
                    "helper": q.get("helper"),
                    "skip_logic": q.get("skip_logic") or [],
                },
                "preconditions": pre,
            })
        plan_warnings += ["%s: %s" % (q.get("id"), w) for w in warn
                          if w.startswith("skip_logic")]

    plan = {"version": FORMAT_VERSION, "study_type": study_type,
            "target": args.target, "steps": steps}
    if plan_warnings:
        plan["warnings"] = plan_warnings
    if gq:
        plan["verification"] = (
            "Study-ID argument names verified against the live Great Question MCP "
            "on 24 Sep 2026. Question field names and the four question types "
            "mirror the get_*_screener read shape and are unverified for writes: "
            "the server returns 'Missing required arguments: <name>' naming any "
            "it expects, so correct and retry on the first step rather than "
            "guessing. Attribute mappings are listed per step for setting in the "
            "app; they are not passed as arguments.")
    Path(args.output).write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
    unresolved = sum(1 for s_ in steps if s_.get("preconditions"))
    print("wrote %s (%d steps%s)" % (args.output, len(steps),
                                     ", Great Question MCP target" if gq else ""))
    if unresolved:
        print("%d step(s) have preconditions to resolve before writing." % unresolved)
    for w in plan_warnings:
        print("warning: " + w)
    return 0


# ------------------------------------------------------------- fingerprint

def _parse_ids(raw: Optional[str]) -> set:
    return {x.strip() for x in (raw or "").split(",") if x.strip()}


def cmd_fingerprint(args: argparse.Namespace) -> int:
    portable = _load_json(args.input)
    rules = dict(DEFAULT_RULES)
    if args.rules:
        rules.update(_load_json(args.rules))
    marker = rules["red_herring_marker"]

    store = load_fingerprints(args.fingerprints)
    entries = store.setdefault("entries", [])
    existing = {e["fingerprint"] for e in entries}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    added = 0
    rh_ids = _parse_ids(args.red_herrings)
    for q in portable.get("questions", []):
        if not _is_red_herring(q, marker, rh_ids):
            continue
        fp = fingerprint(q.get("text", ""))
        entries.append({"fingerprint": fp, "study": args.study,
                        "used_at": now, "question_id": q.get("id")})
        added += 1
        if fp in existing:
            print("note: %s was already recorded; logging this use as well" % q.get("id"))

    Path(args.fingerprints).write_text(json.dumps(store, indent=2) + "\n",
                                       encoding="utf-8")
    if added:
        print("recorded %d red-herring fingerprint(s) in %s" % (added, args.fingerprints))
    else:
        print("no questions labelled %s or listed in --red-herrings — nothing "
              "recorded" % marker)
    return 0


# -------------------------------------------------------------------- main

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="screener_io.py",
        description="Move participant screeners between tools as portable files.")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("export", help="normalise a platform export (JSON or CSV)")
    p.add_argument("input")
    p.add_argument("-o", "--output", default="screener.json")
    p.add_argument("--md", help="also write a markdown rendering to this path")
    p.add_argument("--format", choices=["json", "csv"],
                   help="input format; default is csv for a .csv file, else json")
    p.add_argument("--study-type", choices=STUDY_TYPE_CHOICES)
    p.add_argument("--name", help="screener name, when the source has none")
    p.add_argument("--privacy-notice",
                   help="privacy notice text or URL, when the source has none")
    p.set_defaults(func=cmd_export)

    p = sub.add_parser("check", help="run launch pre-flight checks")
    p.add_argument("input")
    p.add_argument("--rules", help="JSON file of threshold overrides")
    p.add_argument("--fingerprints", default=FINGERPRINT_FILE)
    p.add_argument("--red-herrings",
                   help="comma-separated question ids that are red herrings, for "
                        "tools with no internal-label field (e.g. Great Question)")
    p.set_defaults(func=cmd_check)

    p = sub.add_parser("plan", help="build an ordered list of write intents")
    p.add_argument("input")
    p.add_argument("-o", "--output", default="plan.json")
    p.add_argument("--study-type", choices=STUDY_TYPE_CHOICES)
    p.add_argument("--target", choices=["generic", "gq"], default="generic",
                   help="gq emits Great Question MCP tool names and field names")
    p.add_argument("--study-id", help="target study id, required with --target gq")
    p.set_defaults(func=cmd_plan)

    p = sub.add_parser("fingerprint", help="record red-herring fingerprints")
    p.add_argument("input")
    p.add_argument("--study", required=True, help="study name, for the log")
    p.add_argument("--rules")
    p.add_argument("--fingerprints", default=FINGERPRINT_FILE)
    p.add_argument("--red-herrings", help="comma-separated question ids")
    p.set_defaults(func=cmd_fingerprint)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

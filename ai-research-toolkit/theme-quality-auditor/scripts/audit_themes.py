#!/usr/bin/env python3
"""
Theme Quality Auditor - check whether the themes in a qualitative analysis are
themes, or topic summaries wearing a theme's name.

A theme, in Braun & Clarke's reflexive thematic analysis, is a pattern of
shared meaning organised around a central concept - something a reader could
disagree with. A topic summary collects everything participants said about a
subject ("Onboarding", "Pricing", "Views on the dashboard") and has no central
claim. This script flags the second kind, and the habits that produce it.

It does not rewrite themes. It asks the questions that get the analyst to one.

Usage:
  python audit_themes.py themes.md
  python audit_themes.py themes.md --guide discussion_guide.md
  python audit_themes.py themes.json --approach codebook --json out.json
  python audit_themes.py affinity_groups.md --approach affinity

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------- patterns

# Names that announce a topic rather than a claim. Most are the shape of an
# interview question turned into a heading.
TOPIC_NAME_PATTERNS = [
    r"^(experiences?|journeys?) (of|with|using|in)\b",
    r"^(views?|thoughts?|feelings?|opinions?|attitudes?|perceptions?|feedback|"
    r"sentiment|reactions?|impressions?) (on|about|of|towards?|regarding|to)\b",
    r"^(challenges?|issues?|problems?|barriers?|pain ?points?|frustrations?|"
    r"benefits?|needs?|goals?|motivations?|concerns?|blockers?|drivers?)"
    r"( (with|of|in|around|for|to|when|using))?\b",
    r"^(the )?(role|use|usage|importance|impact) of\b",
    r"^(understanding|awareness|knowledge) of\b",
    r"^(current|existing) (process|processes|workflow|workflows|tools?|state)\b",
    r"^(likes|dislikes|likes and dislikes|positives?|negatives?)\b",
    r"^(other|miscellaneous|general|misc)\b",
]

# Domain nouns that, alone, name a subject rather than say anything about it.
DOMAIN_NOUNS = {
    "onboarding", "pricing", "price", "cost", "costs", "notifications",
    "communication", "collaboration", "usability", "navigation", "performance",
    "support", "features", "feature", "integration", "integrations", "workflow",
    "workflows", "reporting", "reports", "search", "security", "privacy", "ui",
    "ux", "design", "experience", "feedback", "challenges", "pain", "points",
    "frustrations", "needs", "goals", "motivations", "barriers", "benefits",
    "issues", "tools", "tool", "process", "processes", "trust", "time", "speed",
    "adoption", "training", "documentation", "setup", "configuration",
    "permissions", "approvals", "approval", "dashboard", "dashboards", "data",
    "mobile", "access", "accessibility", "content", "team", "teams", "culture",
    "management", "planning", "budget", "budgets", "roles", "role", "value",
    "quality", "reliability", "context", "environment", "usage", "habits",
    "behaviour", "behavior", "attitudes", "perceptions", "expectations",
    "requirements", "preferences", "workarounds", "sharing", "visibility",
    "billing", "invoices", "invoicing", "receipts", "payments", "admin",
    "admins", "experiences", "alerts",
}

# Head nouns that name a category of things people said, not what it means:
# "Admin pain points", "Customer support interactions", "Onboarding
# experiences and challenges", "Reporting needs of finance managers".
TOPIC_HEADS = {
    "experience", "experiences", "challenges", "challenge", "interactions",
    "interaction", "points", "needs", "issues", "problems", "frustrations",
    "concerns", "expectations", "preferences", "perceptions", "attitudes",
    "views", "opinions", "thoughts", "feelings", "feedback", "habits",
    "behaviours", "behaviors", "journeys", "journey", "motivations", "goals",
    "barriers", "benefits", "considerations", "requirements", "reactions",
    "impressions", "usage", "adoption",
}

# Words that can be a noun or a verb. They only count as a claim when used
# as a verb: after a subject, and not followed by a preposition or the end of
# the name. "Trust", "Trust in reporting" and "Reporting needs of finance
# managers" are noun phrases; "Admins need a faster export" is a claim.
NOUN_OR_VERB = {
    "trust", "trusts", "need", "needs", "use", "uses", "work", "works", "fear",
    "fears", "matter", "matters", "start", "starts", "stop", "stops", "keep",
    "keeps", "wait", "waits", "take", "takes", "own", "owns", "mean", "means",
    "feel", "feels", "want", "wants", "make", "makes", "get", "gets", "see",
    "sees", "give", "gives", "do", "does", "come", "comes", "cost", "costs",
    "block", "blocks", "drive", "drives", "break", "breaks", "love", "hate",
    "struggle", "struggles", "lead", "leads", "miss", "misses", "delays",
}
NOUN_FOLLOWERS = {"of", "in", "for", "with", "around", "about", "on", "and",
                  "or", "&", "to", "towards", "toward", "between", "across"}

# A theme name written as an interview question.
QUESTION_NAME = re.compile(
    r"\?\s*$|^(what|how|why|when|where|which|who|do you|did you|tell me|"
    r"describe|walk me)\b", re.I)

# After a colon, these introduce a list of contents, not a claim:
# "Billing: including invoices and receipts".
CONTENTS_AFTER_COLON = re.compile(
    r"^\s*(?:including\b|incl\b|such as\b|covering\b|for example\b|"
    r"e\.g\.|from\b)", re.I)
CONNECTORS = {"and", "&", "or", "of", "the", "a", "an", "with", "in", "on",
              "for", "to", "vs", "versus", "around", "about"}

# Tokens that suggest a claim is being made. Not a parser; a signal.
CLAIM_TOKENS = {
    "is", "are", "was", "were", "be", "been", "being", "am", "isn't", "aren't",
    "can't", "cannot", "don't", "doesn't", "won't", "didn't", "not", "no",
    "never", "only", "rather", "than", "instead", "because", "so", "but",
    "without", "over", "until", "unless", "before", "after", "more", "less",
    "want", "wants", "need", "needs", "feel", "feels", "trust", "trusts",
    "avoid", "avoids", "prefer", "prefers", "treat", "treats", "see", "sees",
    "use", "uses", "rely", "relies", "fear", "fears", "expect", "expects",
    "resist", "resists", "choose", "chooses", "become", "becomes", "make",
    "makes", "keep", "keeps", "hide", "hides", "protect", "protects", "lose",
    "loses", "work", "works", "wait", "waits", "give", "gives", "take",
    "takes", "own", "owns", "mean", "means", "matter", "matters", "comes",
    "come", "get", "gets", "stop", "stops", "start", "starts", "has", "have",
    "had", "do", "does", "did", "should", "would", "could", "will", "must",
    "may", "might", "confuse", "confuses", "stall", "stalls", "kill", "kills",
    "break", "breaks", "block", "blocks", "cost", "costs", "fail", "fails",
    "drive", "drives", "replace", "replaces", "ignore", "ignores", "forget",
    "forgets", "hate", "hates", "love", "loves", "miss", "misses", "struggle",
    "struggles", "depend", "depends", "happen", "happens", "lead", "leads",
    "slows", "delays", "lost",
}

DOMAIN_SUMMARY_PATTERNS = [
    (r"\bparticipants? (talked|spoke|discussed|mentioned|described|shared|"
     r"commented|reflected) (about|on|how|their|a range|various|several|many)\b",
     "describes what was discussed, not what it means"),
    (r"\bthis theme (covers|includes|captures|encompasses|groups|contains|"
     r"brings together|relates to|is about|looks at|explores|collects)\b",
     "describes the theme's contents rather than stating its claim"),
    (r"\b(a range of|a variety of|a number of|various|several different|"
     r"different aspects of|many aspects of)\b",
     "a container of varied material, which is the mark of a topic summary"),
    (r"\btopics? (such as|like|including)\b", "lists topics"),
    (r"\b(everything|anything|all comments|all feedback) (related|relating) to\b",
     "a bucket, not a pattern of meaning"),
]

# Emergence language is only flagged when it is about themes or findings, so
# "emerging markets" and "the problem surfaced at checkout" pass.
_FINDING_NOUNS = r"(themes?|findings?|patterns?|insights?|categories|codes?)"
EMERGENCE_PATTERNS = [
    (r"\bthemes? (emerged|emerge|emerging|emerges)\b", "themes emerged"),
    (r"\b%s\b[^.;]{0,40}?\b(emerged|emerge|emerges|surfaced|surface|surfaces)\b"
     % _FINDING_NOUNS, "emerged / surfaced"),
    (r"\bemerg(ent|ing)\s+%s\b" % _FINDING_NOUNS, "emerging themes"),
    (r"\b(emerged|surfaced) (from|in|through|out of|across) (the |our )?"
     r"(data|interviews?|transcripts?|research|analysis|sessions?|responses)\b",
     "emerged from the data"),
    (r"\bthe data (revealed|reveals|showed|shows|told us|tells us|suggests|"
     r"suggested)\b", "the data revealed"),
    (r"\bthemes? (were|was) (found|identified|discovered|uncovered|located)\b",
     "themes were found"),
    (r"\b(came|fell) out of the data\b", "came out of the data"),
    (r"\barose from the data\b", "arose from the data"),
]

FREQUENCY_WARRANT = re.compile(
    r"\b(\d+|most|many|majority|all|several|half|few)\b( of the)?( \d+)? "
    r"(participants|users|people|respondents|interviewees|customers)\b"
    r".{0,20}\b(mentioned|said|talked|raised|reported|noted|brought up|agreed)\b",
    re.I)

ATTRIBUTION = [
    r"[—–-]{1,2}\s*\(?\b(P\d{1,3})\b", r"\(\s*\b(P\d{1,3})\b[^)]*\)",
    r"[—–-]{1,2}\s*\(?\bParticipant\s+(\d{1,3})\b",
    r"\(\s*\bParticipant\s+(\d{1,3})\b[^)]*\)", r"\[\s*\b(P\d{1,3})\b[^\]]*\]",
]

STOPWORDS = CONNECTORS | {"is", "are", "was", "were", "be", "it", "its", "this",
                          "that", "they", "their", "them", "we", "our", "you",
                          "your", "how", "what", "why", "when", "do", "does",
                          "did", "can", "could", "would", "tell", "me", "us",
                          "about", "describe", "walk", "through", "last", "time",
                          "any", "some"}


# ---------------------------------------------------------------- model

class Theme:
    def __init__(self, name: str, line: int) -> None:
        self.name = name.strip()
        self.line = line
        self.description_lines: List[str] = []
        self.quotes: List[Tuple[str, Optional[str]]] = []
        self.subthemes: List[str] = []
        self.flags: List[str] = []
        self.guide_item: Optional[str] = None

    @property
    def description(self) -> str:
        return " ".join(self.description_lines).strip()

    @property
    def participants(self) -> Set[str]:
        return {p for _, p in self.quotes if p}


def _who(text: str) -> Optional[str]:
    for pat in ATTRIBUTION:
        m = re.search(pat, text, re.I)
        if m:
            g = m.group(1)
            return g.upper() if g.upper().startswith("P") else "P" + g
    return None


def parse_markdown(text: str) -> Tuple[List[Theme], List[str]]:
    lines = text.splitlines()
    themes: List[Theme] = []
    current: Optional[Theme] = None
    top_level_seen = False

    # If the file uses '#' for themes (no '##'), treat '#' as theme level.
    has_h2 = any(re.match(r"^##\s+", ln) for ln in lines)
    theme_level = 2 if has_h2 else 1

    i = 0
    while i < len(lines):
        ln = lines[i]
        m = re.match(r"^(#{1,6})\s+(.*)$", ln)
        if m:
            level = len(m.group(1))
            title = re.sub(r"^(theme|sub-?theme)\s*\d*\s*[:.\-–—]\s*", "", m.group(2).strip(),
                           flags=re.I)
            if level < theme_level:
                top_level_seen = True
                current = None
            elif level == theme_level:
                current = Theme(title, i + 1)
                themes.append(current)
            elif current is not None:
                current.subthemes.append(title)
            i += 1
            continue

        if current is None:
            i += 1
            continue

        if ln.lstrip().startswith(">"):
            # A run of consecutive '>' lines is one extract, attributed once.
            parts = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                part = re.sub(r"^\s*>\s?", "", lines[i]).strip()
                if part:
                    parts.append(part)
                i += 1
            body = " ".join(parts)
            tail = lines[i] if i < len(lines) else ""
            who = _who(body) or (_who(tail) if re.match(r"^\s*[—–(\[-]", tail) else None)
            body = re.sub(r"\s*[—–-]{1,2}\s*\(?(P\d{1,3}|Participant\s+\d{1,3})\b.*$",
                          "", body, flags=re.I).strip()
            body = re.sub(r"\s*[(\[]\s*P\d{1,3}\b[^)\]]*[)\]]\s*$", "", body).strip()
            if body:
                current.quotes.append((body, who))
            continue

        for q in re.finditer(r"[\"“]([^\"”]{25,})[\"”]", ln):
            current.quotes.append((q.group(1), _who(ln[q.end():q.end() + 60]) or _who(ln)))

        stripped = ln.strip()
        if stripped and not re.match(r"^[-*+]\s", stripped) and not stripped.startswith("|") \
                and not re.match(r"^[—–-]{1,2}\s*\(?P\d", stripped):
            current.description_lines.append(stripped)
        i += 1

    return themes, lines


def parse_json(text: str) -> Tuple[List[Theme], List[str]]:
    data = json.loads(text)
    if isinstance(data, dict):
        data = data.get("themes", data.get("data", []))
    themes = []
    for i, item in enumerate(data):
        if isinstance(item, str):
            t = Theme(item, i + 1)
        else:
            t = Theme(str(item.get("name") or item.get("title") or ""), i + 1)
            desc = item.get("description") or item.get("summary") or ""
            if desc:
                t.description_lines.append(str(desc))
            for q in item.get("quotes") or item.get("evidence") or []:
                if isinstance(q, dict):
                    t.quotes.append((str(q.get("text") or q.get("quote") or ""),
                                     q.get("participant") or q.get("speaker")))
                else:
                    t.quotes.append((str(q), _who(str(q))))
            t.subthemes = [str(s.get("name") if isinstance(s, dict) else s)
                           for s in item.get("subthemes") or []]
        themes.append(t)
    return themes, text.splitlines()


# ---------------------------------------------------------------- checks

def content_words(text: str) -> Set[str]:
    words = re.findall(r"[a-z][a-z'&]+", text.lower())
    return {w for w in words if w not in STOPWORDS and len(w) > 2}


def has_claim(tokens: List[str]) -> bool:
    """True if the tokens look like they make a claim (a verb, a negation, a
    contrast). Words that double as nouns only count when used as verbs."""
    for i, t in enumerate(tokens):
        if t not in CLAIM_TOKENS:
            continue
        if t in NOUN_OR_VERB:
            prev = tokens[i - 1] if i > 0 else None
            nxt = tokens[i + 1] if i + 1 < len(tokens) else None
            if prev is None or prev in CONNECTORS or nxt is None \
                    or nxt in NOUN_FOLLOWERS:
                continue
        return True
    return False


def name_signal(name: str) -> Optional[Tuple[str, str]]:
    """Return (strength, reason) if the name reads as a topic, else None."""
    low = name.lower().strip().rstrip(".")
    if QUESTION_NAME.search(low):
        return ("strong", "an interview question used as a theme name (\"%s\"). A "
                          "theme states what the answers mean" % name)
    # A claim after a colon rescues a topic prefix: "Onboarding: people give up
    # early". A list of contents after the colon does not: "Billing: including
    # invoices and receipts".
    if ":" in low:
        head, tail = low.split(":", 1)
        tail_tokens = re.findall(r"[a-z']+", tail)
        if CONTENTS_AFTER_COLON.search(tail):
            return ("strong", "a subject followed by a list of what it contains "
                              "(\"%s\"), with no claim" % name)
        if len(tail_tokens) >= 3 and has_claim(tail_tokens):
            return None
        low = head.strip()
    for pat in TOPIC_NAME_PATTERNS:
        if re.search(pat, low):
            return ("strong", "named as a topic (\"%s\") — the shape of an interview "
                              "question turned into a heading" % name)
    tokens = re.findall(r"[a-z'&]+", low)
    if not tokens:
        return None
    if has_claim(tokens):
        return None
    content = [t for t in tokens if t not in CONNECTORS]
    if tokens[0].endswith("ing") and tokens[0] not in DOMAIN_NOUNS:
        return ("strong", "an activity label (\"%s\") with no claim in it. It names "
                          "something participants do, not what happens when they "
                          "do it" % name)
    if content and len(content) <= 6 and any(t in TOPIC_HEADS for t in content):
        return ("strong", "named as a category (\"%s\"): it says what kind of "
                          "thing participants talked about, not what it means" % name)
    if content and all(t in DOMAIN_NOUNS for t in content) and len(content) <= 4:
        return ("strong", "a bare subject label (\"%s\") with no claim in it" % name)
    if len(content) <= 2:
        return ("medium", "a short label (\"%s\") that names a subject without saying "
                          "anything about it" % name)
    return None


class Finding:
    def __init__(self, level: str, check: str, message: str,
                 theme: Optional[str] = None, line: Optional[int] = None) -> None:
        self.level, self.check, self.message = level, check, message
        self.theme, self.line = theme, line

    def to_dict(self) -> Dict[str, Any]:
        return {"level": self.level, "check": self.check, "message": self.message,
                "theme": self.theme, "line": self.line}


def audit(themes: List[Theme], lines: List[str], guide: List[str],
          approach: str, min_participants: int) -> Tuple[List[Finding], Dict[str, str]]:
    findings: List[Finding] = []
    verdicts: Dict[str, str] = {}
    codebook = approach == "codebook"
    affinity = approach == "affinity"
    guide_words = [(g, content_words(g)) for g in guide]

    for t in themes:
        strong, medium = [], []
        t.flags = []

        sig = name_signal(t.name)
        if sig:
            (strong if sig[0] == "strong" else medium).append(("name", sig[1]))

        desc = t.description
        if not desc:
            findings.append(Finding("note", "description", "No description. A theme's "
                                    "central organising concept should be statable in a "
                                    "sentence; if it can't be written, it may not exist "
                                    "yet.", t.name, t.line))
        else:
            for pat, why in DOMAIN_SUMMARY_PATTERNS:
                m = re.search(pat, desc, re.I)
                if m:
                    msg = "%s (\"%s\")" % (why[0].upper() + why[1:], m.group(0))
                    if affinity:
                        # Affinity notes often summarise a group's contents on
                        # purpose; the label is what has to carry the claim.
                        findings.append(Finding("note", "description", msg,
                                                t.name, t.line))
                    else:
                        medium.append(("description", msg))
                    break
            if FREQUENCY_WARRANT.search(desc):
                findings.append(Finding("note", "prevalence", "The description leans on "
                                        "how many participants said it. Prevalence can be "
                                        "reported, but it is not what makes something a "
                                        "theme — the shared meaning is.", t.name, t.line))

        # Guide mirroring. A name that already makes a claim is not flagged on
        # shared words alone ("Approvals stall in finance" vs "Tell me about
        # approvals in finance"); only a near-copy of the guide item is.
        if guide_words:
            tw = content_words(t.name)
            for g, gw in guide_words:
                if not tw or not gw:
                    continue
                overlap = len(tw & gw) / len(tw)
                near_copy = SequenceMatcher(None, t.name.lower(), g.lower()).ratio() > 0.7
                if near_copy or (overlap >= 0.6 and sig is not None):
                    strong.append(("guide", "mirrors a discussion-guide item (\"%s\"). "
                                   "Themes organised around the questions you asked are "
                                   "usually summaries of the answers to them" % g[:80]))
                    t.guide_item = g
                    break

        # Thin evidence is reported on its own and never counts toward the
        # topic-summary verdict: something mentioned once can be central.
        thin = []
        n_q = len(t.quotes)
        n_p = len(t.participants)
        if n_q == 0:
            thin.append("no quotes or data extracts attached")
        elif n_p and n_p < min_participants:
            thin.append("thin evidence: rests on %d participant%s (%s). Check whether "
                        "more participants support this"
                        % (n_p, "" if n_p == 1 else "s", ", ".join(sorted(t.participants))))

        # Verdict, from the name, the guide and the description only.
        name_or_guide = any(k in ("name", "guide") for k, _ in strong + medium)
        if strong or (len(medium) >= 2 and name_or_guide):
            verdict = "topic summary"
        elif strong or medium or thin:
            verdict = "review"
        else:
            verdict = "theme"

        if codebook and verdict == "topic summary":
            verdict = "review"

        level = "fail" if verdict == "topic summary" else "review"
        for kind, msg in strong + medium:
            lvl = "note" if codebook else level
            findings.append(Finding(lvl, kind, msg, t.name, t.line))
            t.flags.append(kind)
        for msg in thin:
            findings.append(Finding("review", "evidence", msg, t.name, t.line))
            t.flags.append("evidence")
        verdicts[t.name] = verdict

    # Overlap between themes.
    for i, a in enumerate(themes):
        wa = content_words(a.name + " " + a.description)
        qa = {q for q, _ in a.quotes}
        for b in themes[i + 1:]:
            wb = content_words(b.name + " " + b.description)
            if wa and wb:
                j = len(wa & wb) / len(wa | wb)
                if j >= 0.45:
                    findings.append(Finding("review", "overlap",
                                            "\"%s\" and \"%s\" share %.0f%% of their "
                                            "vocabulary. Either they are one theme, or the "
                                            "boundary between them needs stating."
                                            % (a.name, b.name, 100 * j)))
            shared = qa & {q for q, _ in b.quotes}
            if shared:
                findings.append(Finding("review", "overlap",
                                        "%d quote(s) appear under both \"%s\" and \"%s\"."
                                        % (len(shared), a.name, b.name)))

    # Report-wide language.
    for idx, ln in enumerate(lines, 1):
        for pat, label in EMERGENCE_PATTERNS:
            if re.search(pat, ln, re.I):
                findings.append(Finding("review", "emergence",
                                        "\"%s\" — Braun & Clarke reject this framing: themes "
                                        "are constructed by the analyst, not found in the "
                                        "data. Say what you did (\"we developed\", "
                                        "\"we constructed\")." % label, None, idx))
                break

    n = len(themes)
    if n > 10:
        findings.append(Finding("note", "count", "%d themes. There is no correct number. "
                                "The skill's own heuristic: more than about ten often "
                                "means codes have been promoted to themes." % n))
    elif 0 < n < 2:
        findings.append(Finding("note", "count", "Only one theme. Check it is not the whole "
                                "dataset under a single heading."))
    return findings, verdicts


def prompt_for(t: Theme) -> str:
    """Ask the question that fits what was flagged: no claim, mirrors the
    guide, or thin evidence."""
    n = len(t.quotes)
    no_claim = any(k in ("name", "description") for k in t.flags)
    guide = "guide" in t.flags
    thin = "evidence" in t.flags
    parts = []
    if guide and t.guide_item:
        parts.append("\"%s\" follows the guide item \"%s\". Across the answers to "
                     "that question, what do participants share beyond having answered "
                     "it? Write it as one sentence someone could disagree with."
                     % (t.name, t.guide_item[:80].rstrip(".")))
    elif no_claim:
        if n == 0:
            parts.append("What is \"%s\" claiming? Write it as one sentence someone "
                         "could disagree with, then find the extracts that support it."
                         % t.name)
        elif n == 1:
            parts.append("What is the one extract under \"%s\" saying, beyond being "
                         "about it? Write it as one sentence someone could disagree with."
                         % t.name)
        else:
            parts.append("What do the %d extracts under \"%s\" have in common, apart "
                         "from being about it? Write it as one sentence someone could "
                         "disagree with." % (n, t.name))
    if thin:
        if n == 0:
            parts.append("Which extracts support \"%s\"? Add them, or say where the "
                         "claim comes from." % t.name)
        elif no_claim or guide:
            parts.append("Then check whether more participants support it.")
        else:
            parts.append("Who else said something that means the same as \"%s\"? If "
                         "nobody did, it can still be central; say why it matters."
                         % t.name)
    return " ".join(parts)


def render(themes: List[Theme], findings: List[Finding], verdicts: Dict[str, str],
           source: str, approach: str) -> str:
    L = ["Theme quality audit: %s" % source, "=" * 62]
    counts = {v: sum(1 for x in verdicts.values() if x == v)
              for v in ("theme", "review", "topic summary")}
    L.append("%d themes · %d read as themes · %d need review · %d read as topic "
             "summaries · approach: %s"
             % (len(themes), counts["theme"], counts["review"], counts["topic summary"],
                approach))
    if approach == "affinity":
        L.append("Affinity mode: group labels are checked as themes. Contextual Design "
                 "(Holtzblatt & Beyer)")
        L.append("writes labels in the user's voice, as statements, not categories. "
                 "Description summaries are notes.")
    L.append("")

    by_theme: Dict[Optional[str], List[Finding]] = {}
    for f in findings:
        by_theme.setdefault(f.theme, []).append(f)

    for t in themes:
        v = verdicts.get(t.name, "theme")
        tag = {"theme": "ok", "review": "REVIEW", "topic summary": "TOPIC SUMMARY"}[v]
        L.append("[%s] %s" % (tag, t.name))
        L.append("    %d extract(s) from %d participant(s)%s"
                 % (len(t.quotes), len(t.participants),
                    " · %d subtheme(s)" % len(t.subthemes) if t.subthemes else ""))
        for f in by_theme.get(t.name, []):
            L.append("    - (%s) %s" % (f.check, f.message))
        q = prompt_for(t) if v != "theme" else ""
        if q:
            L.append("    ask: %s" % q)
        L.append("")

    general = by_theme.get(None, [])
    if general:
        L.append("ACROSS THE ANALYSIS")
        for f in general:
            loc = " [line %d]" % f.line if f.line else ""
            L.append("  - (%s)%s %s" % (f.check, loc, f.message))
        L.append("")

    L.append("This audit does not rewrite themes. Deciding what a pattern means is the "
             "analyst's work;")
    L.append("the prompts above are questions, not answers.")
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="audit_themes.py",
                                 description="Check whether themes are themes.")
    ap.add_argument("themes", help="markdown (## per theme) or JSON")
    ap.add_argument("--guide", help="discussion guide, one item per line")
    ap.add_argument("--approach", choices=["reflexive", "codebook", "affinity"],
                    default="reflexive",
                    help="codebook downgrades topic-summary findings to notes, for "
                         "approaches that intend domain summaries; affinity checks "
                         "group labels as themes and treats description summaries "
                         "as notes")
    ap.add_argument("--min-participants", type=int, default=2,
                    help="below this many participants a theme gets a thin-evidence "
                         "note (working default: 2)")
    ap.add_argument("--json", help="also write findings as JSON")
    args = ap.parse_args(argv)

    p = Path(args.themes)
    if not p.exists():
        sys.exit("error: no such file: %s" % args.themes)
    text = p.read_text(encoding="utf-8", errors="replace")
    themes, lines = (parse_json(text) if p.suffix.lower() == ".json"
                     else parse_markdown(text))
    if not themes:
        sys.exit("error: no themes found. Use one '## heading' per theme, or a JSON list.")

    guide = []
    if args.guide:
        gp = Path(args.guide)
        if not gp.is_file():
            sys.exit("error: can't find the discussion guide: %s\n"
                     "Check the path, or run without --guide to skip the guide check."
                     % args.guide)
        guide = [re.sub(r"^\s*[-*\d.)#]+\s*", "", g).strip()
                 for g in gp.read_text(encoding="utf-8", errors="replace").splitlines()
                 if g.strip() and len(g.strip()) > 8]

    findings, verdicts = audit(themes, lines, guide, args.approach, args.min_participants)
    print(render(themes, findings, verdicts, p.name, args.approach))

    if args.json:
        Path(args.json).write_text(json.dumps({
            "verdicts": verdicts, "findings": [f.to_dict() for f in findings]},
            indent=2) + "\n", encoding="utf-8")
        print("\nwrote %s" % args.json)
    return 1 if any(v == "topic summary" for v in verdicts.values()) else 0


if __name__ == "__main__":
    sys.exit(main())

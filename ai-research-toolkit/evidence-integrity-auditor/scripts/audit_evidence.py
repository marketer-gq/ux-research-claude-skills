#!/usr/bin/env python3
"""
Evidence Integrity Auditor - audit a research report against its own evidence.

Checks:
  * quote verification    - can each quote be located in a source transcript?
  * quote concentration   - is one participant carrying the findings?
  * claim linkage         - claims about users with no evidence attached
  * small-sample numbers  - percentages reported at an n too small for them
  * recommendation basis  - recommendations with no cited finding
  * disconfirming evidence- findings that never say whether anyone disagreed
  * participant x theme   - a matrix, so contradictory use of one voice is visible

Usage:
  python audit_evidence.py report.md
  python audit_evidence.py report.md --sources transcripts/ --n 8
  python audit_evidence.py report.md --sources transcripts/ --verbatim strict
  python audit_evidence.py report.md --sources sources.json --json out.json

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from bisect import bisect_left
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# All thresholds below are working defaults, not from the literature.

# A quote shorter than this is a phrase, not evidence; ignored for verification.
MIN_QUOTE_CHARS = 40
# At or above this match ratio (after normalisation) a quote is verified.
VERIFIED_AT = 0.97
# Between ALTERED_AT and VERIFIED_AT the quote is present but altered.
ALTERED_AT = 0.70
# Between ABSENT_BELOW and ALTERED_AT the quote is "not located" (a warning).
# Below ABSENT_BELOW nothing close was found, and only then is it critical.
ABSENT_BELOW = 0.50
# Parts of an ellipsis-split quote further apart than this many words, or out
# of order, may be two quotes merged into one.
MERGE_GAP_WORDS = 250
# Ellipsis/bracket fragments shorter than this many words are too short to
# locate on their own and are ignored (unless nothing longer is left).
MIN_SEGMENT_WORDS = 3
# One participant supplying more than this share of quotes is a concentration flag.
CONCENTRATION_SHARE = 0.40
# ...but it is only critical when the study has at least this many participants.
CONCENTRATION_MIN_N = 5
# Percentages at an n below this should be reported as counts.
SMALL_N = 10

ATTRIBUTION_PATTERNS = [
    r"[—–-]{1,2}\s*\(?\b(P\d{1,3})\b",
    r"\(\s*\b(P\d{1,3})\b[^)]*\)",
    r"[—–-]{1,2}\s*\(?\bParticipant\s+(\d{1,3})\b",
    r"\(\s*\bParticipant\s+(\d{1,3})\b[^)]*\)",
    r"\[\s*\b(P\d{1,3})\b[^\]]*\]",
    r"\[\s*\bParticipant\s+(\d{1,3})\b[^\]]*\]",
]

_WHO = r"(?:P\d{1,3}|Participant\s+\d{1,3})"
# An attribution at the end of a quote: "— P1", "(P1)", "[P1]", "— Participant 3".
TRAILING_ATTRIBUTION = re.compile(
    r"\s*(?:[—–-]{1,2}\s*\(?\b%s\b[^\n]*|\(\s*\b%s\b[^)]*\)|\[\s*\b%s\b[^\]]*\])"
    r"\s*[.,;:]?\s*$" % (_WHO, _WHO, _WHO), re.I)

# Dropped from both quote and source before matching. Removing them is the
# most common light edit in intelligent verbatim transcription.
FILLER_WORDS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "like"}
FILLER_BIGRAMS = {("you", "know")}

# Not used as single-word anchors when searching a source for a quote.
STOPWORDS = {
    "that", "this", "with", "have", "from", "they", "were", "what", "when", "there",
    "their", "would", "about", "which", "just", "really", "because", "then", "than",
    "them", "been", "into", "some", "very", "your", "it's", "don't", "i'm", "that's",
}

CLAIM_MARKERS = [
    r"\busers?\b", r"\bparticipants?\b", r"\bcustomers?\b", r"\bresearchers?\b",
    r"\bpeople\b", r"\beveryone\b", r"\bmost\b", r"\bmany\b", r"\bseveral\b",
    r"\ball\b", r"\bnone\b", r"\bconsistently\b", r"\btypically\b", r"\busually\b",
]

HEDGE_FREE_GENERALISATIONS = [
    r"\busers (want|need|prefer|expect|hate|love|struggle)\b",
    r"\bparticipants (want|need|prefer|expect|hate|love|struggle)\b",
    r"\bcustomers (want|need|prefer|expect|hate|love|struggle)\b",
    r"\beveryone\b", r"\bnobody\b", r"\ball users\b", r"\bno users\b",
    r"\balways\b", r"\bnever\b",
]

RECOMMENDATION_MARKERS = [
    r"\bwe should\b", r"\bwe recommend\b", r"\brecommendation\b", r"\bmust\b",
    r"\bshould\b", r"\bneeds? to\b", r"\bprioriti[sz]e\b", r"\bnext steps?\b",
    r"\baction\b",
]

# A recommendation that names a participant or a finding counts as cited.
# "see" on its own does not: "see appendix" is not evidence.
CITATION_RE = re.compile(r"\bP\d{1,3}\b|\bParticipant\s+\d+\b|\bfindings?\b", re.I)

INTERVAL_MARKERS = [
    r"±", r"\+/-", r"\bconfidence interval\b", r"\bCI\b", r"\b95%\s*(CI|confidence)",
    r"\binterval\b", r"\bmargin of error\b",
]

# Language that shows the researcher looked for, or reported, disagreement.
DISCONFIRMING_MARKERS = [
    r"\bcontradict", r"\bdisagree", r"\bexceptions?\b", r"\bcounter-?examples?\b",
    r"\bnegative case", r"\bin contrast\b", r"\bunlike\b", r"\bnot everyone\b",
    r"\bpushed back\b", r"\bdissent", r"\bdid not (share|agree|mention|experience)\b",
    r"\bdidn't (share|agree|mention|experience)\b",
]

PERCENT_RE = re.compile(r"(\d{1,3}(?:\.\d+)?)\s*(?:%|per ?cent)", re.I)
# "3 of 8", "3 out of 8", and "3/8" (but not dates like 12/03/2026, and not 24/7).
FRACTION_RE = re.compile(
    r"(?<![\d/])\b(\d{1,3})\s*(?:of|out of|/)\s*(\d{1,3})\b(?![\d/])", re.I)

TOKEN_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)*")


# ------------------------------------------------------------ normalisation

def fold(text: str) -> str:
    t = text.lower()
    for a, b in (("’", "'"), ("‘", "'"), ("“", '"'), ("”", '"'), ("…", "...")):
        t = t.replace(a, b)
    return t


def norm(text: str) -> str:
    t = fold(text)
    t = re.sub(r"[^\w\s']", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def tokens(text: str) -> List[str]:
    return TOKEN_RE.findall(fold(text))


def drop_fillers(toks: List[str]) -> Tuple[List[str], List[int]]:
    """Return tokens with fillers removed, and each kept token's original index."""
    kept: List[str] = []
    idx: List[int] = []
    i = 0
    while i < len(toks):
        if i + 1 < len(toks) and (toks[i], toks[i + 1]) in FILLER_BIGRAMS:
            i += 2
            continue
        if toks[i] in FILLER_WORDS:
            i += 1
            continue
        kept.append(toks[i])
        idx.append(i)
        i += 1
    return kept, idx


def split_sentences(text: str) -> List[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\"'])", text)
    return [p.strip() for p in parts if p.strip()]


def parse_vtt(text: str) -> str:
    """Strip WEBVTT/SRT scaffolding and join the cue text into one passage.

    Cue numbers, timestamps, NOTE/STYLE blocks and <v Name> voice tags are
    removed, so a quote that runs across two cues can still be found.
    """
    out: List[str] = []
    for block in re.split(r"\n\s*\n", text.replace("\r\n", "\n")):
        lines = block.strip().split("\n")
        if not lines or not lines[0].strip():
            continue
        if re.match(r"^(WEBVTT|NOTE|STYLE|REGION)\b", lines[0].strip()):
            continue
        ts = [i for i, ln in enumerate(lines) if "-->" in ln]
        body = lines[ts[0] + 1:] if ts else lines
        for ln in body:
            s = ln.strip()
            if not s or re.fullmatch(r"\d+", s):
                continue
            s = re.sub(r"<v(?:\.[^\s>]*)?\s+[^>]*>", "", s)
            s = re.sub(r"</?[^>]+>", "", s)
            if s.strip():
                out.append(s.strip())
    return " ".join(out)


# -------------------------------------------------------------- extraction

class Quote:
    def __init__(self, text: str, participant: Optional[str],
                 theme: Optional[str], line: int) -> None:
        self.text = text.strip()
        self.participant = participant
        self.theme = theme
        self.line = line
        self.match_ratio: Optional[float] = None
        self.match_source: Optional[str] = None
        self.edits: List[str] = []
        self.verdict: Optional[str] = None

    @property
    def status(self) -> str:
        return self.verdict or "unverified"

    def to_dict(self) -> Dict[str, Any]:
        return {"line": self.line, "text": self.text, "participant": self.participant,
                "theme": self.theme, "status": self.status,
                "match_ratio": None if self.match_ratio is None
                else round(self.match_ratio, 3),
                "match_source": self.match_source, "edits": self.edits}


def find_attribution(context: str) -> Optional[str]:
    for pattern in ATTRIBUTION_PATTERNS:
        m = re.search(pattern, context, re.I)
        if m:
            g = m.group(1)
            return g.upper() if g.upper().startswith("P") else "P" + g
    return None


def split_attribution(text: str) -> Tuple[str, Optional[str]]:
    """Remove a trailing attribution from quote text and return it separately."""
    t = text.strip()
    who = None
    m = TRAILING_ATTRIBUTION.search(t)
    if m:
        who = find_attribution(m.group(0))
        t = t[:m.start()].rstrip()
    t = t.strip().strip('"“”').strip()
    return t, who


def parse_report(text: str) -> Tuple[List[Quote], List[Tuple[int, str, str]], List[str]]:
    """Return (quotes, sentences as (line, theme, text), themes)."""
    lines = text.splitlines()
    quotes: List[Quote] = []
    sentences: List[Tuple[int, str, str]] = []
    themes: List[str] = []
    current_theme = "(no theme heading)"

    i = 0
    while i < len(lines):
        line = lines[i]
        heading = re.match(r"^(#{1,6})\s+(.*)$", line)
        if heading:
            current_theme = heading.group(2).strip()
            if current_theme not in themes:
                themes.append(current_theme)
            i += 1
            continue

        # Blockquote, possibly spanning several lines.
        if line.lstrip().startswith(">"):
            block, start = [], i
            while i < len(lines) and (lines[i].lstrip().startswith(">")
                                      or not lines[i].strip()):
                if lines[i].lstrip().startswith(">"):
                    block.append(re.sub(r"^\s*>\s?", "", lines[i]))
                elif block:
                    break
                i += 1
            body, who = split_attribution(" ".join(block))
            # Attribution may also sit on the next line.
            if not who:
                tail = lines[i] if i < len(lines) else ""
                who = find_attribution(tail)
            if body:
                quotes.append(Quote(body, who, current_theme, start + 1))
            continue

        # Inline quoted strings long enough to be evidence.
        for m in re.finditer(r"[\"“]([^\"”]{%d,})[\"”]" % MIN_QUOTE_CHARS, line):
            body, who = split_attribution(m.group(1))
            who = (who or find_attribution(line[m.end():m.end() + 80])
                   or find_attribution(line))
            quotes.append(Quote(body, who, current_theme, i + 1))

        stripped = re.sub(r"^[\s>*+-]*(\d+\.)?\s*", "", line).strip()
        if stripped and not stripped.startswith("|"):
            for sent in split_sentences(stripped):
                sentences.append((i + 1, current_theme, sent))
        i += 1

    return quotes, sentences, themes


def read_source(f: Path) -> str:
    text = f.read_text(encoding="utf-8", errors="replace")
    if f.suffix.lower() in (".vtt", ".srt") or text.lstrip().startswith("WEBVTT"):
        return parse_vtt(text)
    return text


def load_sources(path: str, report: Optional[Path] = None
                 ) -> Tuple[Dict[str, str], List[str]]:
    """Return ({name: text}, [skipped names]). The report itself is never a source."""
    p = Path(path)
    if not p.exists():
        sys.exit("error: no such path: %s" % path)
    rep = report.resolve() if report else None
    skipped: List[str] = []
    if p.is_dir():
        out = {}
        for f in sorted(p.iterdir()):
            if f.suffix.lower() not in (".txt", ".md", ".vtt", ".srt", ".json"):
                continue
            if rep is not None and f.resolve() == rep:
                skipped.append(f.name)
                continue
            out[f.name] = read_source(f)
        if not out:
            sys.exit("error: no .txt/.md/.vtt/.srt/.json source files in %s "
                     "(the report itself is not counted)" % path)
        return out, skipped
    if rep is not None and p.resolve() == rep:
        sys.exit("error: --sources points at the report itself. Every quote would "
                 "verify against itself. Pass the transcripts instead.")
    if p.suffix.lower() == ".json":
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return {k: (parse_vtt(str(v)) if str(v).lstrip().startswith("WEBVTT")
                        else str(v)) for k, v in data.items()}, skipped
        sys.exit("error: %s must be an object of {source_name: text}" % path)
    return {p.name: read_source(p)}, skipped


# ------------------------------------------------------------ verification

class Source:
    """A transcript tokenised for matching, with an n-gram index for anchors."""

    def __init__(self, name: str, text: str) -> None:
        self.name = name
        # [laughs], [crosstalk], [inaudible] and similar annotations are not speech.
        text = re.sub(r"\[[^\]]{0,40}\]", " ", text)
        self.raw = tokens(text)
        self.toks, self.raw_idx = drop_fillers(self.raw)
        self.joined = " ".join(self.toks)
        self.padded = " " + self.joined + " "
        self.offsets: List[int] = []
        pos = 0
        for t in self.toks:
            self.offsets.append(pos)
            pos += len(t) + 1
        self._index: Dict[int, Dict[Tuple[str, ...], List[int]]] = {}

    def index(self, n: int) -> Dict[Tuple[str, ...], List[int]]:
        if n not in self._index:
            d: Dict[Tuple[str, ...], List[int]] = defaultdict(list)
            for i in range(len(self.toks) - n + 1):
                d[tuple(self.toks[i:i + n])].append(i)
            self._index[n] = d
        return self._index[n]

    def fillers_between(self, s: int, e: int) -> int:
        """Filler tokens inside the source span covering kept tokens s..e-1."""
        if e <= s:
            return 0
        return (self.raw_idx[e - 1] - self.raw_idx[s] + 1) - (e - s)


def match_segment(seg: List[str], src: Source) -> Tuple[float, int, int]:
    """Best (ratio, start, end) for a token sequence within a source.

    Exact matches are found by substring search. Otherwise candidate start
    positions are voted for by shared word n-grams, and only windows around
    those candidates are scored, so long transcripts stay fast.
    """
    L = len(seg)
    if not L or not src.toks:
        return 0.0, 0, 0
    nq = " ".join(seg)
    pos = src.padded.find(" " + nq + " ")
    if pos >= 0:
        s = bisect_left(src.offsets, pos)
        return 1.0, s, s + L

    votes: Counter = Counter()
    for n in (3, 2, 1):
        if L < n:
            continue
        idx = src.index(n)
        for i in range(L - n + 1):
            gram = tuple(seg[i:i + n])
            if n == 1 and (len(gram[0]) < 4 or gram[0] in STOPWORDS):
                continue
            for p in idx.get(gram, ()):
                votes[p - i] += 1
        if votes:
            break

    candidates: List[int] = []
    for start, _ in votes.most_common():
        if all(abs(start - c) > 2 for c in candidates):
            candidates.append(start)
        if len(candidates) >= 8:
            break

    sm = SequenceMatcher(None, autojunk=False)
    sm.set_seq2(nq)
    best = (0.0, 0, 0)
    for c in candidates:
        for ds in range(-3, 4):
            for dl in range(-3, 4):
                s = max(0, c + ds)
                e = min(len(src.toks), s + L + dl)
                if e <= s:
                    continue
                sm.set_seq1(" ".join(src.toks[s:e]))
                if sm.real_quick_ratio() <= best[0] or sm.quick_ratio() <= best[0]:
                    continue
                r = sm.ratio()
                if r > best[0]:
                    best = (r, s, e)
    return best


def prepare_quote(text: str) -> Tuple[List[Tuple[List[str], int]], List[str]]:
    """Split a quote into matchable segments and list the light edits it shows.

    Returns ([(kept tokens, filler count)], edits). [sic] is removed and is not
    an edit. "..." and [bracketed insertions] split the quote into parts that
    are matched separately.
    """
    t = fold(text)
    t = re.sub(r"\[\s*sic\s*\]", " ", t)
    edits: List[str] = []
    if "..." in t:
        edits.append("ellipsis")
    if re.search(r"\[[^\]]*\]", t):
        edits.append("bracketed insertion")
    parts = re.split(r"\.{3,}|\[[^\]]*\]", t)
    segs: List[Tuple[List[str], int]] = []
    for part in parts:
        raw = tokens(part)
        kept, _ = drop_fillers(raw)
        if kept:
            segs.append((kept, len(raw) - len(kept)))
    usable = [s for s in segs if len(s[0]) >= MIN_SEGMENT_WORDS]
    if not usable and segs:
        merged: List[str] = []
        for s in segs:
            merged.extend(s[0])
        usable = [(merged, sum(s[1] for s in segs))]
    return usable, edits


def verify_quotes(quotes: List[Quote], sources: Dict[str, str],
                  verbatim: str = "intelligent") -> None:
    srcs = [Source(name, body) for name, body in sources.items()]
    for q in quotes:
        if len(norm(q.text)) < MIN_QUOTE_CHARS:
            continue
        segs, edits = prepare_quote(q.text)
        if not segs:
            continue
        total = sum(len(s[0]) for s in segs)
        best_ratio, best_src, best_res = -1.0, None, []
        for src in srcs:
            res = [match_segment(s[0], src) for s in segs]
            ratio = sum(r[0] * len(s[0]) for r, s in zip(res, segs)) / total
            if ratio > best_ratio:
                best_ratio, best_src, best_res = ratio, src, res
            if ratio == 1.0:
                break
        if best_src is None:
            continue

        edits = list(edits)
        for (r, s, e), (_, q_fillers) in zip(best_res, segs):
            if r > 0 and best_src.fillers_between(s, e) > q_fillers:
                edits.append("filler words removed")
                break
        if VERIFIED_AT <= best_ratio < 1.0:
            edits.append("minor wording differences")
        far_apart = False
        if len(best_res) > 1:
            for (r1, s1, e1), (r2, s2, e2) in zip(best_res, best_res[1:]):
                if s2 < s1 or s2 - e1 > MERGE_GAP_WORDS:
                    far_apart = True
        if far_apart:
            edits.append("parts found far apart")

        q.match_ratio, q.match_source, q.edits = best_ratio, best_src.name, edits
        if best_ratio >= VERIFIED_AT:
            if far_apart or (verbatim == "strict" and edits):
                q.verdict = "altered"
            else:
                q.verdict = "verified"
        elif best_ratio >= ALTERED_AT:
            q.verdict = "altered"
        elif best_ratio >= ABSENT_BELOW:
            q.verdict = "not_located"
        else:
            q.verdict = "absent"


# ----------------------------------------------------------------- finding

class Finding:
    def __init__(self, severity: str, check: str, message: str,
                 line: Optional[int] = None) -> None:
        self.severity, self.check, self.message, self.line = severity, check, message, line

    def to_dict(self) -> Dict[str, Any]:
        return {"severity": self.severity, "check": self.check,
                "message": self.message, "line": self.line}


def fractions(sent: str) -> List[Tuple[int, int]]:
    out = []
    for m in FRACTION_RE.finditer(sent):
        a, b = int(m.group(1)), int(m.group(2))
        if (a, b) == (24, 7) or b == 0 or a > b:
            continue
        out.append((a, b))
    return out


def audit(quotes: List[Quote], sentences: List[Tuple[int, str, str]],
          themes: List[str], n: Optional[int], verified: bool,
          verbatim: str = "intelligent") -> Tuple[List[Finding], Dict[str, Any]]:
    findings: List[Finding] = []

    # --- quote verification -------------------------------------------------
    if verified:
        for q in quotes:
            pct = 100 * (q.match_ratio or 0)
            if q.status == "absent":
                findings.append(Finding(
                    "critical", "quote-verification",
                    'Not located in sources (best match %.0f%%), and nothing close '
                    'was found. Check for a translation or a missing transcript: "%s"'
                    % (pct, q.text[:90]), q.line))
            elif q.status == "not_located":
                findings.append(Finding(
                    "warning", "quote-verification",
                    'Not located in sources (best match %.0f%%). Check for an edit, a '
                    'translation, or a missing transcript: "%s"' % (pct, q.text[:90]),
                    q.line))
            elif q.status == "altered":
                why = (" (%s)" % ", ".join(q.edits)) if q.edits else ""
                findings.append(Finding(
                    "warning", "quote-verification",
                    'Quote differs from the source%s (%.0f%% match against %s): "%s"'
                    % (why, pct, q.match_source, q.text[:90]), q.line))
            elif q.status == "verified" and q.edits:
                findings.append(Finding(
                    "note", "quote-verification",
                    'Verified with light edits (%s), accepted under intelligent '
                    'verbatim. Use --verbatim strict to treat these as altered: "%s"'
                    % (", ".join(q.edits), q.text[:90]), q.line))

    # --- quote concentration ------------------------------------------------
    attributed = [q for q in quotes if q.participant]
    unattributed = [q for q in quotes if not q.participant]
    counts = Counter(q.participant for q in attributed)
    if unattributed:
        findings.append(Finding(
            "warning", "attribution",
            "%d quote(s) carry no participant attribution. An unattributed quote "
            "cannot be checked for concentration or contradiction."
            % len(unattributed), unattributed[0].line))
    if attributed:
        top, top_n = counts.most_common(1)[0]
        share = top_n / len(attributed)
        study_n = n or len(counts)
        if share > CONCENTRATION_SHARE:
            msg = ("%s supplies %d of %d attributed quotes (%.0f%%). Check whether "
                   "quote selection reflects the evidence base. Articulate "
                   "participants are often over-quoted."
                   % (top, top_n, len(attributed), 100 * share))
            if study_n >= CONCENTRATION_MIN_N:
                findings.append(Finding("critical", "concentration", msg))
            else:
                findings.append(Finding(
                    "note", "concentration",
                    msg + " (Fewer than %d participants, so this is a note only.)"
                    % CONCENTRATION_MIN_N))
        if n and len(counts) < n:
            silent = n - len(counts)
            findings.append(Finding(
                "warning", "concentration",
                "%d of %d participants are never quoted. Findings drawn from %d "
                "voices are being presented as findings from %d."
                % (silent, n, len(counts), n)))

    # --- participant x theme ------------------------------------------------
    matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for q in attributed:
        matrix[q.participant][q.theme or "(none)"] += 1
    multi = {p: dict(t) for p, t in matrix.items() if len(t) > 1}
    for p, t in sorted(multi.items(), key=lambda kv: -len(kv[1]))[:5]:
        findings.append(Finding(
            "note", "cross-theme",
            "%s is quoted under %d different themes (%s). Check the quotes are not "
            "being used to support conclusions that contradict each other."
            % (p, len(t), ", ".join(sorted(t)))))

    # --- disconfirming evidence ---------------------------------------------
    quotes_by_theme: Dict[str, List[Quote]] = defaultdict(list)
    for q in quotes:
        quotes_by_theme[q.theme or "(none)"].append(q)
    for theme, qs in quotes_by_theme.items():
        text = " ".join(s for _, t, s in sentences if t == theme)
        if any(re.search(m, text, re.I) for m in DISCONFIRMING_MARKERS):
            continue
        findings.append(Finding(
            "warning", "disconfirming-evidence",
            '"%s" cites %d quote(s) and never says whether any participant '
            "contradicted it. Say who disagreed, or state that no one did "
            "(negative case analysis)." % (theme, len(qs)), qs[0].line))

    # --- claims with no evidence -------------------------------------------
    quote_lines = {q.line for q in quotes}
    for line, theme, sent in sentences:
        if not any(re.search(m, sent, re.I) for m in CLAIM_MARKERS):
            continue
        near_quote = any(abs(line - ql) <= 3 for ql in quote_lines)
        if near_quote:
            continue
        if any(re.search(g, sent, re.I) for g in HEDGE_FREE_GENERALISATIONS):
            findings.append(Finding(
                "warning", "claim-linkage",
                'Unhedged generalisation with no quote within three lines: "%s"'
                % sent[:100], line))

    # --- percentages at small n ---------------------------------------------
    # Raw counts ("3 of 8") are the right way to report a qualitative study and
    # are never flagged. Percentages are, when n is small.
    for line, theme, sent in sentences:
        pm = PERCENT_RE.search(sent)
        if not pm:
            continue
        if any(re.search(m, sent, re.I) for m in INTERVAL_MARKERS):
            continue
        fr = fractions(sent)
        eff_n = fr[0][1] if fr else n
        if eff_n and eff_n < SMALL_N:
            findings.append(Finding(
                "warning", "small-sample",
                'Percentage at n=%d: report as a count ("%d of %d"), not a '
                'percentage: "%s"'
                % (eff_n, round(float(pm.group(1)) * eff_n / 100), eff_n, sent[:100]),
                line))
        elif not eff_n:
            findings.append(Finding(
                "note", "small-sample",
                'Percentage with no stated n. If n is under about %d, report it as '
                'a count. Pass --n to check: "%s"' % (SMALL_N, sent[:100]), line))

    # --- recommendations with no basis --------------------------------------
    for line, theme, sent in sentences:
        if not any(re.search(m, sent, re.I) for m in RECOMMENDATION_MARKERS):
            continue
        near_quote = any(abs(line - ql) <= 5 for ql in quote_lines)
        if not near_quote and not CITATION_RE.search(sent):
            findings.append(Finding(
                "warning", "recommendation-basis",
                'Recommendation with no finding or quote attached: "%s"'
                % sent[:100], line))

    stats = {
        "quotes": len(quotes),
        "attributed_quotes": len(attributed),
        "participants_quoted": len(counts),
        "themes": len(themes),
        "quote_counts": dict(counts),
        "matrix": {p: dict(t) for p, t in matrix.items()},
        "verified": verified,
        "verbatim": verbatim,
        "verification": {
            "checked": sum(1 for q in quotes if q.match_ratio is not None),
            "verified": sum(1 for q in quotes if q.status == "verified"),
            "altered": sum(1 for q in quotes if q.status == "altered"),
            "not_located": sum(1 for q in quotes if q.status == "not_located"),
            "absent": sum(1 for q in quotes if q.status == "absent"),
        } if verified else None,
    }
    return findings, stats


def render(findings: List[Finding], stats: Dict[str, Any],
           title: str, n: Optional[int]) -> str:
    L = ["Evidence integrity audit: %s" % title, "=" * 60]
    L.append("%d quotes (%d attributed) from %d participants across %d headings"
             % (stats["quotes"], stats["attributed_quotes"],
                stats["participants_quoted"], stats["themes"]))
    if n:
        L.append("Study n given as %d" % n)
    v = stats.get("verification")
    if v:
        L.append("Checked against sources (%s verbatim): %d checked, %d verified, "
                 "%d altered, %d not located, %d absent"
                 % (stats["verbatim"], v["checked"], v["verified"], v["altered"],
                    v["not_located"], v["absent"]))
    else:
        L.append("No sources given, so quotes were not verified. Pass --sources to "
                 "check that each quote exists.")
    L.append("")

    for sev, label in (("critical", "CRITICAL"), ("warning", "WARNING"), ("note", "NOTE")):
        items = [f for f in findings if f.severity == sev]
        if not items:
            continue
        L.append("%s (%d)" % (label, len(items)))
        for f in items:
            loc = " [line %d]" % f.line if f.line else ""
            L.append("  - (%s)%s %s" % (f.check, loc, f.message))
        L.append("")

    if stats["quote_counts"]:
        L.append("QUOTES PER PARTICIPANT")
        total = sum(stats["quote_counts"].values())
        for p, c in sorted(stats["quote_counts"].items(), key=lambda kv: -kv[1]):
            bar = "#" * int(round(30 * c / max(total, 1)))
            L.append("  %-8s %3d  %-30s %.0f%%" % (p, c, bar, 100 * c / total))
        L.append("")

    if not findings:
        L.append("No findings. The report's evidence structure holds up.")
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="audit_evidence.py",
        description="Audit a research report against its own evidence.")
    ap.add_argument("report")
    ap.add_argument("--sources", help="transcript directory, file, or JSON map")
    ap.add_argument("--n", type=int, help="participants in the study")
    ap.add_argument("--verbatim", choices=("intelligent", "strict"),
                    default="intelligent",
                    help="intelligent (default): light edits such as removed filler "
                         "words, ellipses and [bracketed] clarifications count as "
                         "verified, with a note. strict: any edit counts as altered.")
    ap.add_argument("--json", help="also write findings as JSON to this path")
    args = ap.parse_args(argv)

    path = Path(args.report)
    if not path.exists():
        sys.exit("error: no such file: %s" % args.report)
    text = path.read_text(encoding="utf-8", errors="replace")

    quotes, sentences, themes = parse_report(text)
    verified = False
    skipped: List[str] = []
    if args.sources:
        sources, skipped = load_sources(args.sources, path)
        for name in skipped:
            print("warning: skipped %s from --sources because it is the report being "
                  "audited." % name, file=sys.stderr)
        verify_quotes(quotes, sources, args.verbatim)
        verified = True

    findings, stats = audit(quotes, sentences, themes, args.n, verified, args.verbatim)
    for name in skipped:
        findings.append(Finding(
            "note", "sources",
            "Skipped %s from --sources: it is the report being audited, and every "
            "quote would verify against itself." % name))
    print(render(findings, stats, path.name, args.n))

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"findings": [f.to_dict() for f in findings], "stats": stats,
             "quotes": [q.to_dict() for q in quotes]},
            indent=2) + "\n", encoding="utf-8")
        print("\nwrote %s" % args.json)

    return 1 if any(f.severity == "critical" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())

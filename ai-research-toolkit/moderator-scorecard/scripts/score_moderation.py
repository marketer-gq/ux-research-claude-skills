#!/usr/bin/env python3
"""
Moderator Quality Scorecard - measure interview moderation from a diarised
transcript.

For a researcher's own self-review and coaching they ask for. Not for
performance evaluation.

Reports talk-time share, longest moderator monologue, use of silence after a
participant stops, overlapping starts, question type mix, leading language,
and (informational only) coverage of the discussion guide.

Usage:
  python score_moderation.py session.vtt
  python score_moderation.py session.txt --moderator "Alex" --guide guide.md
  python score_moderation.py session.vtt --moderator "Alex,Sam"
  python score_moderation.py session.vtt --session-type think-aloud
  python score_moderation.py session.vtt --json scorecard.json

WebVTT gives start and end times, which is what silence and interruption
measurement need. Plain timestamped transcripts support everything else;
pauses and interruptions are reported as not measured.

Stdlib only. Python 3.9+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

SESSION_TYPES = ("interview", "think-aloud", "usability")

# Interview talk-time bands for the participant's share. The 80% target is
# Steve Portigal's 80:20 ("might be 90:10"):
# https://uxpod.com/episodes/user-research-interviews-an-interview-with-steve-portigal.html
# The 70% floor of the "acceptable" band is a working default, not from the
# literature. Think-aloud and usability sessions are not scored on talk share.
INTERVIEW_TARGET_SHARE = 0.80
INTERVIEW_ACCEPTABLE_SHARE = 0.70
# Above this, a moderator turn is a monologue rather than a question.
# Working default, not from the literature.
MONOLOGUE_SECONDS = 30.0
# Measurement threshold for a deliberate pause: Rowe (1986), "wait time",
# Journal of Teacher Education 37(1):43-50. NN/g's teaching rule is longer:
# count to 10 before filling a pause
# (https://www.nngroup.com/articles/talking-to-users/).
SILENT_PROBE_SECONDS = 3.0
# Speaking rate used to estimate a turn's length when there are no timings
# (2.5 words/s = 150 wpm). Working default, not from the literature.
WORDS_PER_SECOND = 2.5
# A guide item counts as covered at or above this similarity.
# Working default, not from the literature.
GUIDE_MATCH = 0.55
# Same-speaker cues closer together than this are merged into one turn.
# Working default, not from the literature.
MERGE_GAP = 1.0
# Fallback moderator detection: the top question-asker must ask at least this
# many times as many questions as the next speaker, or the script asks for
# --moderator. Working default, not from the literature.
QUESTION_RATIO = 2.0

ROLE_LABEL = re.compile(r"moderator|interviewer|researcher|facilitator", re.I)

LEADING_PATTERNS = [
    (r"\bdon't you (think|feel|agree)\b", "tag question inviting agreement"),
    (r"\bwouldn't you (say|agree|think)\b", "tag question inviting agreement"),
    (r",\s*(?:didn|don|doesn|isn|wasn|weren|aren|haven|hasn|wouldn|couldn|won|can)'?t\s+"
     r"(?:you|it|they|that|this|there|we|he|she)\s*\?", "tag question inviting agreement"),
    (r"\b(?:isn|wasn|aren)'?t (?:it|that|this|they) (?:so|really|just|way)\b",
     "tag question that supplies the judgement"),
    (r"\bdo you agree\b", "asks for assent rather than a view"),
    (r"\bso you(?:'re| are)? (saying|thinking|feeling)\b",
     "puts words in the participant's mouth"),
    (r"\bwas that (frustrating|annoying|confusing|difficult|easy)\b",
     "names the emotion for them"),
    (r"\bthat must have been\b", "supplies the interpretation"),
    (r"\bI (guess|assume|imagine) you\b", "supplies the answer"),
    (r",\s*right\?\s*$", "seeks confirmation of the moderator's framing"),
    (r"\bwould you say (it'?s|that'?s|you'?re)\b", "offers the answer to agree with"),
    (r"\bis it because\b", "offers a single cause to accept"),
    (r"\bhow much (?:did|do|would) you (?:love|like|enjoy|hate|appreciate|value)\b",
     "presumes the feeling and asks only how strong it is"),
    (r"\b(?:most|many|a lot of|other) (?:people|users|participants|customers) "
     r"(?:find|say|tell us|think|feel|like|prefer|struggle)\b",
     "norming: tells them what others think"),
    (r"\b(?:everyone|everybody) (?:finds|says|tells us|thinks|feels|likes|prefers|struggles)\b",
     "norming: tells them what others think"),
]

# Not leading: checking you understood them.
COMPREHENSION_CHECK = re.compile(
    r"^(?:(?:and|so|okay|ok|just to check)[,\s]+)?"
    r"(?:did i (?:get|understand) (?:that|this|you|it) (?:right|correctly)"
    r"|(?:have|had) i got (?:that|this|it) right"
    r"|is that (?:right|correct)"
    r"|am i (?:understanding|getting) (?:that|this|you|it) (?:right|correctly))\s*\??$",
    re.I)
# Not leading: an either/or that leaves the door open.
OPEN_ALTERNATIVE = re.compile(
    r"\bor (?:something|anything|somewhere|someone) else\b|\bor not\b"
    r"|\bor (?:neither|none)\b|\bor (?:some|any) other\b"
    r"|\bor (?:was it|is it|was that|is that) something else\b", re.I)

OPEN_STARTERS = [
    r"^what\b", r"^how\b", r"^why\b", r"^tell me\b", r"^walk me\b",
    r"^describe\b", r"^talk me through\b", r"^in what\b", r"^when you\b",
    r"^what'?s\b", r"^say more\b", r"^can you (tell|walk|describe|say)\b",
]
CLOSED_STARTERS = [
    r"^(did|do|does|is|are|was|were|have|has|had|can|could|would|will|should|"
    r"am|shall)\b",
]


class ModeratorError(Exception):
    pass


class Turn:
    def __init__(self, speaker: str, text: str, start: Optional[float],
                 end: Optional[float]) -> None:
        self.speaker, self.text = speaker, text.strip()
        self.start, self.end = start, end

    @property
    def words(self) -> int:
        return len(re.findall(r"\b[\w']+\b", self.text))

    @property
    def duration(self) -> Optional[float]:
        if self.start is None or self.end is None:
            return None
        return max(0.0, self.end - self.start)


# ------------------------------------------------------------------ parsing

TS = r"(\d{1,2}):(\d{2})(?::(\d{2}))?(?:[.,](\d{1,3}))?"
# A timestamp optionally wrapped in [] or ().
WRAPPED_TS = r"[\[(]?" + TS + r"[\])]?"


def to_seconds(m: Sequence[Optional[str]]) -> float:
    a, b, c, ms = m
    if c is not None:
        h, mi, s = int(a), int(b), int(c)
    else:
        h, mi, s = 0, int(a), int(b)
    return h * 3600 + mi * 60 + s + (int(ms.ljust(3, "0")) / 1000 if ms else 0.0)


VOICE_TAG = re.compile(r"<v(?:\.[^\s>]+)*\s+([^>]+?)\s*>")


def parse_vtt(text: str) -> List[Turn]:
    turns: List[Turn] = []
    blocks = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    cue = re.compile(TS + r"\s*-->\s*" + TS)
    for block in blocks:
        m = cue.search(block)
        if not m:
            continue
        g = m.groups()
        start, end = to_seconds(g[0:4]), to_seconds(g[4:8])
        # Anything after the end time on the timing line is cue settings.
        rest = block[m.end():]
        body = rest.split("\n", 1)[1] if "\n" in rest else ""
        # Read the speaker from <v Name> before the tags are stripped.
        vm = VOICE_TAG.search(body)
        if vm:
            speaker = vm.group(1).strip()
            line = re.sub(r"<[^>]+>", "", body)
        else:
            body = re.sub(r"<[^>]+>", "", body).strip()
            sm = re.match(r"^\s*([^:\n]{1,40}):\s*(.*)$", body, re.S)
            if sm:
                speaker, line = sm.group(1).strip(), sm.group(2)
            else:
                speaker, line = "UNKNOWN", body
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            turns.append(Turn(speaker, line, start, end))
    return merge_consecutive(turns)


# "[00:01:23] Name: text", "Name (00:01:23): text", "Name 00:01:23: text"
PLAIN_LINE = re.compile(
    r"^\s*(?:" + WRAPPED_TS + r"\s*)?([^:\n\[\]()]{1,40}?)\s*(?:" + WRAPPED_TS
    + r")?\s*:\s*(.*)$")
# Otter-style header on its own line: "Name  0:05", text on the lines below.
HEADER_LINE = re.compile(r"^\s*([^\d\s:\[\]()][^:\n\[\]()]{0,39}?)\s+" + TS + r"\s*$")


def _otter_headers(lines: List[str]) -> List[int]:
    """Indexes of header lines. A header follows a blank line or starts the
    file, so a sentence that happens to end in a time is not taken for one."""
    out = []
    for i, ln in enumerate(lines):
        if HEADER_LINE.match(ln) and (i == 0 or not lines[i - 1].strip()):
            out.append(i)
    return out


def parse_plain(text: str) -> List[Turn]:
    lines = text.replace("\r\n", "\n").split("\n")
    headers = _otter_headers(lines)
    plain_hits = sum(1 for ln in lines if PLAIN_LINE.match(ln))
    turns: List[Turn] = []

    if headers and len(headers) >= plain_hits:
        hset = set(headers)
        for i, ln in enumerate(lines):
            if i in hset:
                m = HEADER_LINE.match(ln)
                assert m is not None
                turns.append(Turn(m.group(1).strip(), "", to_seconds(m.groups()[1:5]), None))
            elif ln.strip() and turns:
                turns[-1].text = (turns[-1].text + " " + ln.strip()).strip()
    else:
        for ln in lines:
            if not ln.strip():
                continue
            m = PLAIN_LINE.match(ln)
            if not m:
                if turns:
                    turns[-1].text += " " + ln.strip()
                continue
            g = m.groups()
            start = to_seconds(g[0:4]) if g[0] else (to_seconds(g[5:9]) if g[5] else None)
            turns.append(Turn(g[4].strip(), g[9].strip(), start, None))

    # Plain transcripts give a start time at most. End times are left unknown:
    # inferring them from the next start would invent pauses and interruptions.
    turns = [t for t in turns if t.text]
    return merge_consecutive(turns)


def merge_consecutive(turns: List[Turn]) -> List[Turn]:
    out: List[Turn] = []
    for t in turns:
        if out and out[-1].speaker == t.speaker:
            prev = out[-1]
            untimed = prev.end is None or t.start is None
            if untimed or (t.start - prev.end) < MERGE_GAP:  # type: ignore[operator]
                prev.text += " " + t.text
                prev.end = t.end
                continue
        out.append(t)
    return out


def speakers_in_order(turns: List[Turn]) -> List[str]:
    seen: List[str] = []
    for t in turns:
        if t.speaker not in seen:
            seen.append(t.speaker)
    return seen


def identify_moderators(turns: List[Turn],
                        given: Optional[str]) -> Tuple[List[str], str]:
    """Return (moderator labels, how they were chosen). Never guesses: if the
    choice is ambiguous, raises ModeratorError asking for --moderator."""
    speakers = speakers_in_order(turns)
    listing = ", ".join(speakers)
    if given:
        chosen: List[str] = []
        for want in [w.strip() for w in given.split(",") if w.strip()]:
            hits = [s for s in speakers if s == want]
            if not hits:
                hits = [s for s in speakers if s.lower() == want.lower()]
            if not hits:
                raise ModeratorError("no speaker named exactly %r. Speakers found: %s"
                                     % (want, listing))
            if len(hits) > 1:
                raise ModeratorError("%r matches more than one speaker label (%s). "
                                     "Use the exact label." % (want, ", ".join(hits)))
            if hits[0] not in chosen:
                chosen.append(hits[0])
        if not chosen:
            raise ModeratorError("--moderator was empty. Speakers found: %s" % listing)
        if len(chosen) == len(speakers):
            raise ModeratorError("every speaker was named as a moderator, so there is "
                                 "no participant. Speakers found: %s" % listing)
        return chosen, "--moderator"

    if len(speakers) < 2:
        raise ModeratorError("only one speaker found (%s). Check the speaker labels."
                             % listing)

    role = [s for s in speakers if ROLE_LABEL.search(s)]
    if len(role) == 1:
        return role, "speaker label"
    if len(role) > 1:
        raise ModeratorError(
            "several speakers are labelled like moderators (%s). Pass --moderator "
            "with the one who moderated, or --moderator \"A,B\" if both did."
            % ", ".join(role))

    counts = {s: sum(t.text.count("?") for t in turns if t.speaker == s)
              for s in speakers}
    ranked = sorted(speakers, key=lambda s: (-counts[s], speakers.index(s)))
    top, runner_up = counts[ranked[0]], counts[ranked[1]]
    if top == 0 or top < QUESTION_RATIO * runner_up:
        detail = ", ".join("%s %d" % (s, counts[s]) for s in ranked)
        raise ModeratorError(
            "can't tell who moderated from the speaker labels or question counts "
            "(questions asked: %s). Pass --moderator \"Name\", or "
            "--moderator \"A,B\" for two moderators." % detail)
    return [ranked[0]], "most questions asked"


# ---------------------------------------------------------------- analysis

def _sentences(turns: List[Turn], moderators: List[str]) -> List[str]:
    out = []
    for t in turns:
        if t.speaker not in moderators:
            continue
        for sent in re.split(r"(?<=[.!?])\s+", t.text):
            sent = sent.strip()
            if sent:
                out.append(sent)
    return out


def extract_questions(turns: List[Turn], moderators: List[str]) -> List[str]:
    return [s for s in _sentences(turns, moderators) if s.endswith("?")]


def moderator_sentences(turns: List[Turn], moderators: List[str]) -> List[str]:
    """Every sentence the moderator says. Leading language and guide coverage
    both live outside question marks — "that must have been frustrating" leads
    without asking, and "tell me about X" covers a guide item without a '?'."""
    return [s for s in _sentences(turns, moderators) if len(s) > 3]


def find_leading(sentences: List[str]) -> List[Dict[str, str]]:
    found = []
    for sent in sentences:
        s = sent.replace("\u2019", "'").replace("\u2018", "'")
        if COMPREHENSION_CHECK.match(s.strip()) or OPEN_ALTERNATIVE.search(s):
            continue
        for pattern, why in LEADING_PATTERNS:
            if re.search(pattern, s, re.I):
                found.append({"question": sent, "why": why})
                break
    return found


def classify_question(q: str) -> str:
    low = re.sub(r"^\s*(and|so|ok(ay)?|right|um|uh)[,\s]+", "", q.strip().lower())
    for p in OPEN_STARTERS:
        if re.search(p, low):
            return "open"
    for p in CLOSED_STARTERS:
        if re.search(p, low):
            return "closed"
    return "other"


def talk_time_status(share: float, session_type: str) -> str:
    if session_type != "interview":
        return "info"
    if share >= INTERVIEW_TARGET_SHARE:
        return "ok"
    if share >= INTERVIEW_ACCEPTABLE_SHARE:
        return "acceptable"
    return "REVIEW"


def analyse(turns: List[Turn], moderators: List[str],
            guide: Optional[List[str]], session_type: str = "interview",
            detected_by: str = "--moderator") -> Dict[str, Any]:
    mod = [t for t in turns if t.speaker in moderators]
    par = [t for t in turns if t.speaker not in moderators]

    timed = all(t.duration is not None for t in turns) and bool(turns)
    if timed:
        mod_time = sum(t.duration or 0 for t in mod)
        par_time = sum(t.duration or 0 for t in par)
        basis = "duration"
    else:
        mod_time, par_time = float(sum(t.words for t in mod)), float(sum(t.words for t in par))
        basis = "word count"
    total = mod_time + par_time or 1.0
    share = par_time / total

    def length(t: Turn) -> float:
        return t.duration if t.duration is not None else t.words / WORDS_PER_SECOND

    longest = max(mod, key=length, default=None)
    longest_secs = length(longest) if longest else 0.0
    longest_estimated = bool(longest) and longest.duration is None  # type: ignore[union-attr]

    # Silence after a participant finishes, and overlapping starts. Both need
    # real end times; without them nothing is measured.
    silences: List[float] = []
    overlaps = 0
    have_gaps = False
    for i in range(len(turns) - 1):
        a, b = turns[i], turns[i + 1]
        if a.speaker in moderators or b.speaker not in moderators:
            continue
        if a.end is None or b.start is None:
            continue
        have_gaps = True
        gap = b.start - a.end
        if gap < 0:
            overlaps += 1
        silences.append(max(0.0, gap))

    mean_silence = (sum(silences) / len(silences)) if silences else None
    if not have_gaps:
        silence_status = "not measured"
    elif session_type != "interview":
        silence_status = "info"
    else:
        silence_status = ("ok" if mean_silence is not None
                          and mean_silence >= SILENT_PROBE_SECONDS else "REVIEW")

    questions = extract_questions(turns, moderators)
    kinds = {"open": 0, "closed": 0, "other": 0}
    for q in questions:
        kinds[classify_question(q)] += 1

    sentences = moderator_sentences(turns, moderators)
    leading = find_leading(sentences)

    coverage = None
    if guide:
        covered, missed = [], []
        for g in guide:
            best, bq = 0.0, None
            for q in sentences:
                r = SequenceMatcher(None, _norm(g), _norm(q)).ratio()
                if r > best:
                    best, bq = r, q
            (covered if best >= GUIDE_MATCH else missed).append(
                {"guide": g, "asked": bq, "match": round(best, 2)})
        coverage = {"covered": covered, "missed": missed,
                    "rate": len(covered) / len(guide), "status": "info"}

    return {
        "moderator": " + ".join(moderators),
        "moderators": list(moderators),
        "moderator_detected_by": detected_by,
        "speakers": speakers_in_order(turns),
        "session_type": session_type,
        "basis": basis,
        "turns": len(turns),
        "moderator_turns": len(mod),
        "moderator_share": mod_time / total,
        "participant_share": share,
        "talk_time_status": talk_time_status(share, session_type),
        "longest_moderator_turn_seconds": longest_secs,
        "longest_moderator_turn_estimated": longest_estimated,
        "longest_moderator_turn_text": longest.text[:160] if longest else "",
        "silences": silences,
        "mean_silence": mean_silence,
        "silences_over_probe": sum(1 for s in silences if s >= SILENT_PROBE_SECONDS),
        "silence_status": silence_status,
        "have_gaps": have_gaps,
        "interruptions": overlaps if have_gaps else None,
        "questions": len(questions),
        "question_mix": kinds,
        "leading": leading,
        "coverage": coverage,
    }


def _norm(s: str) -> str:
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return re.sub(r"\s+", " ", s).strip()


def load_guide(text: str) -> List[str]:
    """One question per line. Markdown headings are section titles, not
    questions, so they are skipped."""
    out = []
    for ln in text.splitlines():
        if not ln.strip() or re.match(r"^\s*#", ln):
            continue
        item = re.sub(r"^\s*[-*\d.)]+\s*", "", ln).strip()
        if len(item) > 10:
            out.append(item)
    return out


# ------------------------------------------------------------------ report

def render(a: Dict[str, Any], source: str) -> str:
    L = ["Moderator scorecard: %s" % source, "=" * 62]
    L.append("For the moderator's own self-review and coaching they ask for.")
    L.append("Not for performance evaluation.")
    L.append("")
    L.append("Moderator: %s (chosen by %s) · %s session · %d turns"
             % (a["moderator"], a["moderator_detected_by"], a["session_type"], a["turns"]))
    L.append("Talk time measured by %s%s"
             % (a["basis"], "" if a["basis"] == "duration" else " (estimated)"))
    L.append("Check the speaker labels first. A misattributed turn moves every number below.")
    L.append("")

    share = a["participant_share"]
    status = a["talk_time_status"]
    L.append("TALK TIME  [%s]" % status)
    L.append("  participant  %5.1f%%   %s" % (100 * share, "#" * int(round(40 * share))))
    L.append("  moderator    %5.1f%%   %s"
             % (100 * a["moderator_share"], "#" * int(round(40 * a["moderator_share"]))))
    if a["session_type"] == "interview":
        L.append("  interview target: participant at or above %.0f%% (Portigal's 80:20); "
                 "%.0f-%.0f%% acceptable"
                 % (100 * INTERVIEW_TARGET_SHARE, 100 * INTERVIEW_ACCEPTABLE_SHARE,
                    100 * INTERVIEW_TARGET_SHARE))
        if status == "acceptable":
            L.append("  Inside the acceptable band. Worth a look at the recording, not a")
            L.append("  problem on its own.")
        elif status == "REVIEW":
            L.append("  The moderator used %.0f%% of the talk. The recording will show where:"
                     % (100 * a["moderator_share"]))
            L.append("  usually the opening, rephrased questions, or long acknowledgements.")
    else:
        L.append("  Not scored. In %s sessions silent task work and neutral prompts"
                 % a["session_type"])
        L.append("  are expected (Boren & Ramey 2000), so there is no interview target here.")
    L.append("")

    secs = a["longest_moderator_turn_seconds"]
    est = a["longest_moderator_turn_estimated"]
    L.append("LONGEST MODERATOR TURN  [%s]"
             % ("REVIEW" if secs > MONOLOGUE_SECONDS else "ok"))
    if est:
        L.append("  about %.0f seconds, estimated from word count at %.1f words/s "
                 "(threshold %.0f)" % (secs, WORDS_PER_SECOND, MONOLOGUE_SECONDS))
    else:
        L.append("  %.0f seconds (threshold %.0f)" % (secs, MONOLOGUE_SECONDS))
    if a["longest_moderator_turn_text"]:
        L.append('  "%s..."' % a["longest_moderator_turn_text"][:120])
    L.append("")

    if a["have_gaps"]:
        ms = a["mean_silence"]
        L.append("SILENCE AFTER THE PARTICIPANT STOPS  [%s]" % a["silence_status"])
        L.append("  mean pause before the moderator speaks: %.1fs" % (ms or 0.0))
        L.append("  pauses of %.0fs or more: %d of %d"
                 % (SILENT_PROBE_SECONDS, a["silences_over_probe"], len(a["silences"])))
        if a["session_type"] == "interview":
            L.append("  3s is the measurement threshold (Rowe 1986, wait time). NN/g's")
            L.append("  teaching rule is to count to 10 before filling the gap.")
        else:
            L.append("  Not scored. Long silences during task work are expected.")
        L.append("")
        L.append("INTERRUPTIONS  [%s]" % ("ok" if a["interruptions"] == 0 else "REVIEW"))
        L.append("  %d moderator turn(s) started before the participant's turn ended"
                 % a["interruptions"])
        L.append("  Counts real overlaps only. Many exports never overlap cues, so 0 here")
        L.append("  does not prove there were no interruptions.")
        L.append("")
    else:
        L.append("SILENCE AND INTERRUPTIONS  [not measured]")
        L.append("  The transcript has no turn end times, so pauses and interruptions")
        L.append("  cannot be measured. Export as WebVTT to get this section.")
        L.append("")

    mix = a["question_mix"]
    total_q = max(a["questions"], 1)
    L.append("QUESTIONS")
    L.append("  %d asked · open %d (%.0f%%) · closed %d (%.0f%%) · other %d"
             % (a["questions"], mix["open"], 100 * mix["open"] / total_q,
                mix["closed"], 100 * mix["closed"] / total_q, mix["other"]))
    L.append("")

    L.append("LEADING LANGUAGE  [%s]" % ("ok" if not a["leading"] else "REVIEW"))
    if a["leading"]:
        for item in a["leading"]:
            L.append('  - "%s"' % item["question"][:100])
            L.append("      %s" % item["why"])
    else:
        L.append("  None matched the patterns checked.")
    L.append("")

    cov = a["coverage"]
    if cov:
        L.append("GUIDE COVERAGE  [info]")
        L.append("  %d of %d guide questions matched (%.0f%%)"
                 % (len(cov["covered"]), len(cov["covered"]) + len(cov["missed"]),
                    100 * cov["rate"]))
        for m in cov["missed"]:
            L.append("  not matched: %s" % m["guide"][:90])
        L.append("  Informational. Following a tangent is often where the insight is.")
        L.append("")

    L.append("This is a coaching instrument. It measures the mechanics of "
             "moderation, not")
    L.append("the quality of the conversation. A session can score well and still "
             "miss the point.")
    return "\n".join(L)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(
        prog="score_moderation.py",
        description="Measure interview moderation from a diarised transcript.")
    ap.add_argument("transcript")
    ap.add_argument("--moderator",
                    help="exact speaker label; 'A,B' for two moderators. "
                         "Auto-detected only when unambiguous")
    ap.add_argument("--session-type", choices=SESSION_TYPES, default="interview",
                    help="interview (default), think-aloud or usability")
    ap.add_argument("--guide", help="discussion guide; one question per line")
    ap.add_argument("--json", help="also write the scorecard as JSON")
    args = ap.parse_args(argv)

    p = Path(args.transcript)
    if not p.exists():
        sys.exit("error: no such file: %s" % args.transcript)
    text = p.read_text(encoding="utf-8", errors="replace")

    turns = parse_vtt(text) if ("-->" in text) else parse_plain(text)
    if not turns:
        sys.exit("error: no speaker turns found. Expected WebVTT, or lines like "
                 "'[00:01:23] Speaker: text'.")

    try:
        moderators, how = identify_moderators(turns, args.moderator)
    except ModeratorError as e:
        sys.exit("error: %s" % e)

    guide = None
    if args.guide:
        guide = load_guide(Path(args.guide).read_text(encoding="utf-8"))

    a = analyse(turns, moderators, guide, args.session_type, how)
    print(render(a, p.name))

    if args.json:
        Path(args.json).write_text(json.dumps(a, indent=2) + "\n", encoding="utf-8")
        print("\nwrote %s" % args.json)

    return 0


if __name__ == "__main__":
    sys.exit(main())

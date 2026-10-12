"""Deterministic synthetic interview transcript for the matching tests.

Everything here is invented. No real participant data. The same seed always
produces the same ~10,000-word transcript, with the target passages below
planted at fixed points so the tests know what each quote should match.
"""

import random

SEED = 20261012
TARGET_WORDS = 10000

# Passages the report quotes from, planted verbatim in the transcript.
PLANTED = {
    "exact": "Honestly the weekly export is the only reason I open the reporting "
             "page at all these days.",
    "fillers": "So um the thing is, uh, we never really trusted the numbers on the "
               "shared dashboard because, you know, nobody owned them.",
    "ellipsis": "I spent most of Tuesday rebuilding the same filter three times, "
                "which was annoying, and by the end I had stopped caring whether "
                "the totals matched anything.",
    "bracket": "When it times out halfway through the approval, I have to start "
               "the whole request again from the first screen.",
    "smart": "I don't mind the extra step if it means my manager can't change the "
             "budget after I've submitted it.",
    "paraphrase": "Every month I copy the invoices into a spreadsheet by hand "
                  "because the finance system will not export them in a format "
                  "our auditors accept.",
}

# How each case appears in a report.
REPORT_QUOTES = {
    "exact": "> Honestly the weekly export is the only reason I open the reporting "
             "page at all these days. (P1)",
    "fillers": "> So the thing is, we never really trusted the numbers on the shared "
               "dashboard because nobody owned them. [P2]",
    "ellipsis": "> I spent most of Tuesday rebuilding the same filter three times... "
                "by the end I had stopped caring whether the totals matched "
                "anything. — P3",
    "bracket": "> When [the approval tool] times out halfway through the approval, "
               "I have to start the whole request again from the first screen. "
               "— Participant 4",
    "smart": "P5 put it plainly: “I don’t mind the extra step if it means my "
             "manager can’t change the budget after I’ve submitted it.” (P5)",
    "paraphrase": "> Each month I have to move the invoices into a spreadsheet "
                  "myself, since the finance tool can't export them in a way the "
                  "auditors will accept. (P6)",
    "invented": "> The onboarding checklist made me feel like the company actually "
                "cared about getting my first week right. (P7)",
}

_SUBJECTS = ["the team", "my manager", "our ops lead", "the vendor", "finance",
             "the new hire", "our designer", "the support desk", "legal", "we"]
_VERBS = ["looked at", "talked about", "moved", "checked", "rewrote", "skipped",
          "scheduled", "argued over", "signed off on", "forgot about"]
_OBJECTS = ["the quarterly plan", "a meeting invite", "the shared calendar",
            "the travel policy", "a slide deck", "the onboarding notes",
            "the coffee rota", "the parking form", "a status update",
            "the holiday schedule", "the office move", "the team offsite"]
_TAILS = ["on Monday", "last week", "before lunch", "after the standup",
          "most afternoons", "when it rained", "during the review",
          "without telling anyone", "twice in a row", "for no clear reason"]
_INTERVIEWER = [
    "Can you tell me more about that?", "What happened next?",
    "How did that make you feel?", "Walk me through the last time that happened.",
    "Who else was involved?", "What did you do after that?",
    "Is that typical for your week?", "What would you change about it?",
]


def _sentence(rng: random.Random) -> str:
    s = "%s %s %s %s." % (rng.choice(_SUBJECTS), rng.choice(_VERBS),
                          rng.choice(_OBJECTS), rng.choice(_TAILS))
    return s[0].upper() + s[1:]


def build_transcript(target_words: int = TARGET_WORDS, seed: int = SEED) -> str:
    rng = random.Random(seed)
    keys = list(PLANTED)
    # Spread planted passages evenly through the transcript.
    plant_at = {int(target_words * (i + 1) / (len(keys) + 1)): k
                for i, k in enumerate(keys)}
    lines = []
    words = 0
    pending = sorted(plant_at)
    while words < target_words:
        q = rng.choice(_INTERVIEWER)
        lines.append("Interviewer: " + q)
        words += len(q.split())
        turn = [_sentence(rng) for _ in range(rng.randint(2, 5))]
        if pending and words >= pending[0]:
            turn.insert(rng.randint(0, len(turn)), PLANTED[plant_at[pending.pop(0)]])
        text = " ".join(turn)
        lines.append("Participant: " + text)
        words += len(text.split())
    return "\n\n".join(lines) + "\n"


if __name__ == "__main__":
    t = build_transcript()
    print(len(t.split()), "words")

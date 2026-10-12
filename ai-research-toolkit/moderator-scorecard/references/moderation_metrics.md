# Moderation metrics: thresholds and where they come from

| Metric | Threshold | Source |
|---|---|---|
| Participant talk-time share (interview) | ≥ 80% target | Steve Portigal's 80:20, "might be 90:10" ([UX Podcast](https://uxpod.com/episodes/user-research-interviews-an-interview-with-steve-portigal.html)) |
| Participant talk-time share (interview) | 70–80% acceptable | Working default, not from the literature |
| Talk-time share (think-aloud, usability) | not scored | Silent task work and neutral prompts are expected (Boren & Ramey 2000, *IEEE Trans. Prof. Comm.* 43:261–278; [NN/g](https://www.nngroup.com/articles/thinking-aloud-the-1-usability-tool/)) |
| Longest moderator turn | ≤ 30s | Working default, not from the literature |
| Speaking rate for estimated turn length | 2.5 words/s | Working default, not from the literature |
| Silence before filling a pause | ≥ 3s measured | Rowe (1986), "wait time", *Journal of Teacher Education* 37(1):43–50 |
| Silence before filling a pause | count to 10, taught | [NN/g, talking to users](https://www.nngroup.com/articles/talking-to-users/) |
| Interruption | start before the participant's turn ends (overlap below 0s) | Definition, not a threshold |
| Guide coverage match | similarity ≥ 0.55 | Working default, not from the literature; informational only |
| Merge same-speaker cues | gap < 1s | Working default, not from the literature |
| Auto-detect moderator by questions | ≥ 2× the next speaker | Working default, not from the literature; otherwise asks for `--moderator` |

The working defaults are marked as such deliberately — a threshold presented as a
standard when it is a convention is how conventions turn into rules nobody can
question.

Change them in `scripts/score_moderation.py` and record why in your fork.

## Talk time

This applies to interviews. In think-aloud and usability sessions the participant
may work silently for long stretches and the moderator's neutral prompts are part of
the method, so talk share is reported but not scored.

An 80% target sounds high until you measure a real session. Moderator talk
accumulates in three places:

1. **The opening.** Context-setting that could be two sentences becomes forty seconds.
2. **Rephrasing.** A question that lands badly gets restated, and each restatement is
   more specific than the last until it contains the answer.
3. **Acknowledgement.** "Right, yeah, that makes sense, so what I'm hearing is…" —
   which is both talk time and, usually, leading.

The opening is the cheapest to fix and moves the number most.

## The silent probe

After a participant stops, the instinct is to fill the gap. The gap is where the
second half of the answer lives — the part they were deciding whether to say.

NN/g teaches counting to 10. Three seconds is used as the measurement threshold,
following Rowe's (1986) work on "wait time": long enough to be deliberate, short
enough that a real session produces some.

A low mean pause (the example output shows 1.6 seconds) suggests the moderator is
closing most gaps. It is often the most improvable habit on the scorecard and needs
no new skill, only tolerance for discomfort.

This needs real end times. For plain transcripts with start times only, silence and
interruptions are reported as not measured rather than inferred from the next turn's
start.

## Leading language

The common shapes, all pattern-matchable:

**Naming the emotion.** "That must have been frustrating." The participant agrees,
because agreeing is easier than correcting you, and now there is a quote about
frustration in the transcript that the participant did not volunteer.

**Summarising into a stronger claim.** "So you're saying the tool didn't help at all?"
They said one specific thing. The summary is broader and more quotable.

**Tag questions.** "Don't you think…", "Wouldn't you say…", "…, didn't you?",
"Isn't it so much…?". Structurally an invitation to agree.

**Presuming the feeling.** "How much did you love…" leaves only the degree open.

**Norming.** "Most people find…" tells the participant what the expected answer is.

Deliberately not flagged: comprehension checks ("Did I get that right?") and either/or
questions that offer an open option ("…, or something else?"). Both are good practice.

The reason these matter more than a badly worded screener question is that the
resulting quote enters the analysis looking like evidence, and nothing downstream can
tell it was produced by the question. This is exactly what the
`evidence-integrity-auditor` skill cannot catch — the quote is real and verifiable, and
the moderator put it there.

## Question mix

Open questions produce narrative; closed questions confirm facts. Both belong in a
session.

The diagnostic pattern is drift: a session that starts open and becomes progressively
closed usually means the moderator stopped listening and started confirming a
hypothesis. Look at the order, not just the ratio.

## Guide coverage

Coverage is informational and never flagged for review. In semi-structured interviews
tangents are often where the insight is. Low coverage is ambiguous and should be read
with the recording.

- **Good:** the participant went somewhere more interesting and the moderator followed.
- **Bad:** the moderator lost the thread, or ran out of time because of the opening
  monologue.

The value is knowing which, before you try to compare answers across participants and
discover three of them were never asked.

## What is deliberately not measured

**Rapport.** Real, important, and not computable from a transcript.

**Whether the right questions were asked.** That is a study design question, and it
belongs in the guide review, not the session review.

**Participant quality.** Different skill, different data.

---
name: moderator-scorecard
description: Measure moderation mechanics from a diarised interview, think-aloud or usability transcript — talk-time share, longest moderator monologue, silence after a participant stops, overlapping starts, question mix, leading language and discussion-guide coverage. For a researcher's own self-review or coaching they ask for, not performance evaluation. Measures how the session was run, not what the participant said.
---

# Moderator Quality Scorecard

**For a researcher's own self-review, and coaching they ask for. Not for performance evaluation.** Participant consent should cover QA review of transcripts before you run this on a session; if your consent form only covers analysis, check first.

Moderation is rarely measured. Analysis gets reviewed, plans get reviewed, reports get reviewed. The session itself is watched live by one or two people, remembered impressionistically, and seldom quantified — so a moderator who talks for a third of every session may find out years later, or never.

Sales teams have had talk-time metrics for years. Fathom ships them in its AI scorecards. This is a version built around research sessions rather than sales calls.

Everything here is computable from a diarised transcript. Diarisation errors are common (often 10–20% or more of speech misattributed; working default, not from the literature) and can flip a talk-time result, so check the speaker labels before reading any number.

## Goal

The moderator sees, from their own transcript, how much room their participants had to talk and where their questions may have steered the answers, and leaves with one or two concrete things to try in the next session.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You are a research coach who has run and reviewed many sessions, helping a peer who asked for feedback on their own moderation.

- Read the numbers in light of the session type and the moment. A long moderator turn may be a task briefing, a consent explanation or rescuing a stuck participant.
- Check speaker labels before trusting any metric, and say when a result depends on them.
- Lead with what went well, then the one or two changes that would make the biggest difference to what participants could say. Quote the moment from the transcript.
- This is for development, not evaluation. Keep the tone of a trusted colleague, never an assessor.

## Quick start

```bash
python scripts/score_moderation.py session.vtt
python scripts/score_moderation.py session.vtt --guide guide.md --moderator "Alex"
python scripts/score_moderation.py session.vtt --moderator "Alex,Sam"      # two moderators
python scripts/score_moderation.py session.vtt --session-type think-aloud
python scripts/score_moderation.py session.txt --json scorecard.json
```

## What it needs

**WebVTT, ideally.** VTT carries a start *and* an end time per cue, which is what silence and interruption measurement need. Zoom, Teams and most transcription tools export it.

**A plain timestamped transcript works** for everything except pauses and interruptions. `[00:01:23] Speaker: text`, `Speaker (00:01:23): text` and Otter-style `Speaker  0:05` header lines (text on the lines below) are all recognised. Without end times the script does not guess: silence and interruptions are reported as "not measured", talk time is by word count, and turn lengths are labelled "estimated".

**The moderator** is detected only when it is unambiguous: exactly one speaker labelled moderator, interviewer, researcher or facilitator, or one speaker who asks at least twice as many questions as anyone else (working default, not from the literature). Otherwise the script stops and asks for `--moderator`. `--moderator` matches the label exactly ("Al" does not match "Alice"); use `--moderator "A,B"` when two people moderated.

**The session type**, with `--session-type interview|think-aloud|usability` (default `interview`). It changes what gets scored; see Talk time.

**The discussion guide**, optionally, as one question per line. Markdown headings are skipped. Adds the guide coverage section.

## What it measures

### Talk time

The share of the session each side used, by duration where timings allow and by word count otherwise — the output says which.

For **interviews**, the target is the participant at 80% or more, after Steve Portigal's 80:20 rule of thumb, which he says "might be 90:10" ([UX Podcast](https://uxpod.com/episodes/user-research-interviews-an-interview-with-steve-portigal.html)). 70–80% is reported as acceptable (working default, not from the literature); below 70% is flagged for review. A moderator at 30% is worth a look at the recording: that is a third of a session the participant was recruited for.

For **think-aloud and usability** sessions, talk share and silence are reported but not scored. Silent task work is expected, and so are neutral prompts like "What are you thinking?" (Boren & Ramey 2000, *IEEE Transactions on Professional Communication* 43:261–278; [NN/g on thinking aloud](https://www.nngroup.com/articles/thinking-aloud-the-1-usability-tool/)). An interview target would mark a well-run test as a failure.

### Longest moderator turn

Flagged above 30 seconds (working default, not from the literature). Without timings the length is estimated from word count at 2.5 words a second (working default, not from the literature) and labelled "estimated". Long moderator turns cluster at the start, where the context-setting monologue lives, and in the middle, where a question gets rephrased three times until it becomes a leading one.

### Silence after the participant stops

The mean gap before the moderator speaks, and how many gaps reached three seconds. Three seconds is the measurement threshold, from Rowe's work on "wait time" (Rowe 1986, *Journal of Teacher Education* 37(1):43–50). NN/g's teaching rule is longer: count to 10 before filling a pause ([NN/g, talking to users](https://www.nngroup.com/articles/talking-to-users/)). Reported but not scored for think-aloud and usability sessions. The silent probe is the cheapest follow-up available and the first thing an anxious moderator abandons.

### Interruptions

Moderator turns that start before the participant's turn has ended: a real overlap in the timestamps. Back-to-back cues (the moderator starting the moment the participant's cue ends) are not counted. Requires end timestamps. Many exports never produce overlapping cues, so zero here does not prove there were no interruptions.

### Question mix

Questions ending in a question mark, classified as open (what, how, why, tell me, walk me, describe), closed (did, do, is, are, can, would) or other. Closed questions are not a defect — they are how you confirm a specific fact — but a session that is mostly closed questions starts to look like a survey conducted out loud.

### Leading language

Pattern-matched across everything the moderator says, not only questions, because the worst examples are statements:

- "That must have been frustrating." — supplies the interpretation.
- "So you're saying the tool didn't help at all?" — puts words in their mouth.
- "Don't you think…", "…, didn't you?", "Isn't it so much…?" — tag questions that invite agreement.
- "How much did you love…" — presumes the feeling and asks only how strong it is.
- "Most people find…" — norming: tells them what others think before they answer.

Not flagged: comprehension checks ("Did I get that right?") and either/or questions that leave the door open ("…, or something else?").

The participant will often accept the framing, and the quote that results reads like evidence.

### Guide coverage

Each guide item matched against the moderator's actual sentences by similarity (covered at 0.55 or above; working default, not from the literature). Reports which were matched and which were not. **Informational only — never flagged for review.**

In a semi-structured interview, the tangent is often where the insight is. Coverage is a fact the debrief should have, not a score: it saves discovering three sessions later that a question you meant to compare across participants was never asked.

## Reading the output

```
TALK TIME  [REVIEW]
  participant   66.3%   ###########################
  moderator     33.7%   #############
  interview target: participant at or above 80% (Portigal's 80:20); 70-80% acceptable

LONGEST MODERATOR TURN  [REVIEW]
  38 seconds (threshold 30)
  "Thanks so much for joining today. Before we start I just want to give you..."

SILENCE AFTER THE PARTICIPANT STOPS  [REVIEW]
  mean pause before the moderator speaks: 1.6s
  pauses of 3s or more: 2 of 5

INTERRUPTIONS  [REVIEW]
  1 moderator turn(s) started before the participant's turn ended

QUESTIONS
  3 asked · open 1 (33%) · closed 1 (33%) · other 1

LEADING LANGUAGE  [REVIEW]
  - "That must have been frustrating."
      supplies the interpretation
  - "So you're saying the tool didn't help at all?"
      puts words in the participant's mouth

GUIDE COVERAGE  [info]
  2 of 4 guide questions matched (50%)
```

(Example output; the numbers are illustrative.)

Each flagged line is a possible coaching conversation, not a verdict. The 38-second opening is usually the easiest fix and the one that moves the talk-time number most.

## How to use it without it being horrible

This measures a person. That changes how it should be introduced.

- **Let moderators run it on themselves first.** A metric that arrives as a manager's report is a performance review. The same metric self-served is a practice tool.
- **Trend, not snapshot.** One session is noise. A moderator whose talk-time share falls from 30% to 12% over six sessions is learning, and that is the thing worth showing.
- **Never rank moderators against each other on it.** Session types differ. A first-time participant in a sensitive domain needs more moderator talk than a repeat panelist walking through a workflow.
- **Pair it with the recording.** The numbers say where to look. They do not say what happened.

## Limitations

- **Diarisation errors become moderation findings.** A transcript that attributes the participant's words to the moderator produces a talk-time figure that is simply wrong, and errors on this scale are common. Run `transcript-cleaner`'s speaker attribution review first. This matters more here than in any other skill.
- **No end timestamps means no silence or interruption data.** The script says so rather than estimating.
- **Interruptions are only as good as the cue timings.** Only real overlaps count, and many exporters never overlap cues.
- **Session type matters.** Scoring a think-aloud test against an interview target produces nonsense. Pass `--session-type`.
- **Leading language is pattern-matched.** It catches the common constructions and will miss a leading question phrased unusually. A clean result means nothing matched, not that nothing led.
- **Guide matching is similarity-based.** A guide question asked in substantially different words may read as missed. Check before treating it as one.
- **Talk-time by word count is not talk-time.** People speak at different rates. Where the transcript has no timings, treat the share and any turn lengths as estimates.
- **It cannot tell you the session was good.** A moderator can hit every number and never ask the question that mattered. This measures mechanics.

## Workflow

1. Clean the transcript and fix speaker attribution (`transcript-cleaner`).
2. Run the scorecard with the guide and the right `--session-type`.
3. Read it against the recording for the two or three findings you want to act on. Not all of them.
4. Keep the JSON. The value is in the sixth session, not the first.

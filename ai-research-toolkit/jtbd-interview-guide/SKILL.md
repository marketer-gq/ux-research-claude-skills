---
name: jtbd-interview-guide
description: >-
  Generate a complete JTBD (Jobs-to-Be-Done) interview moderation guide for product research. Use this skill whenever a PM, product designer, or researcher needs to plan and run a JTBD-style user interview using the Bob Moesta timeline interview method. Triggers on "create interview guide", "write interview questions for JTBD", "help me run a JTBD interview", "what should I ask in a user interview", "interview guide for a product or feature", "moderation guide", "discussion guide", "research script". Also use proactively when someone is preparing for upcoming user interviews and wants a structured approach. Outputs a complete moderation guide with timeline walkthrough, probing questions, and facilitation notes — the kind of guide a PM or designer can pick up and use in 30 minutes of prep.
---

# JTBD Interview Guide Generator

Creates a complete moderation guide for running JTBD timeline interviews, based on Bob Moesta's Competing Against Luck methodology. The output is a practical guide a PM or designer can use immediately — not a generic question bank.

## The JTBD Timeline Interview (the approach)

Bob Moesta's core insight: the richest data comes from walking people *backwards through the specific story of how they made a decision*, not from asking them what they generally want. People are bad at predicting future behavior but surprisingly accurate at recalling past events and the feelings that accompanied them.

The interview has a clear arc:
1. **First thought** — when did they first realize the old situation wasn't working?
2. **Passive looking** — were they casually aware of alternatives?
3. **Active looking** — what triggered them to actually start searching?
4. **Decision** — what happened the day they chose?
5. **First use** — what was the onboarding/early experience like?
6. **Now** — are they getting the progress they hired the product for?

This arc is not just good structure — it systematically surfaces push forces (steps 1–3), pull forces (step 3–4), anxieties (step 4), habits (step 4), and desired outcomes (step 5–6).

## Step 1: Gather context

Before generating the guide, ask for:

**Required:**
- What product / feature / decision are you researching?
- What's the core research question? (What do you most need to understand by the end of this study?)
- Who is the participant? (Role, segment, behavior — e.g., "a PM who recently adopted a new research tool")

**Helpful:**
- Is this an existing user, a churned user, a prospect, or someone who *didn't* switch? Each changes the timeline and framing considerably.
- How long is the session? (45 min is ideal; 30 min is tight but workable; 60 min allows deeper probing)
- Are there specific hypotheses you want to test? (These become probe areas in the guide)

If any of these are unclear, ask before writing the guide. A guide built for the wrong participant type wastes everyone's time.

## Step 2: Generate the guide

### Structure

The guide has these sections:

**Introduction (5 min)**
**Timeline Walkthrough (20–30 min)** — the heart of the interview
**Four Forces Deep Dive (10–15 min)** — probing push, pull, anxiety, habits
**Desired Outcomes (5 min)** — what does success look like to them?
**Wrap-up (2–3 min)**

### Introduction section

Include:
- A brief framing statement the interviewer reads aloud (permission, purpose, "there are no wrong answers")
- Warm-up question(s) to establish rapport and context
- A reminder to the moderator to listen for the *language* the participant uses — their own words are gold for copy and positioning

Example framing: *"Thanks for joining us. I want to be upfront — I'm not testing you, and there are no wrong answers. We're trying to understand how [people like you] make decisions, so everything you share is helpful. I'm going to ask you to walk me back through a specific experience, even if it feels like ancient history. Is that okay?"*

### Timeline walkthrough section

For each stage of the timeline, provide:
- The opening question (gets them into the story)
- 3–4 probing questions (for when they need prompting)
- Facilitation note (what the moderator is listening for and why)

**Stage 1: First thought**
Opening: *"Cast your mind back to when you first started thinking that [old situation] wasn't working well enough. When was that? What was happening?"*

Probes:
- "What made that moment stick out?"
- "Had you been feeling this way for a while, or was it sudden?"
- "What were you trying to get done at the time?"
- "Who else was affected by this?"

*What to listen for: the functional frustration (push force) and the context/trigger event. Participants often gloss over this quickly — press for the story.*

**Stage 2: Passive looking**
Opening: *"At that point, were you aware of other ways people handled this? Were you loosely keeping an eye out for alternatives?"*

Probes:
- "What had you heard about [alternatives]?"
- "Did you talk to anyone about it?"
- "What were you hoping to find?"

*What to listen for: informal research behaviors, word-of-mouth influence, first impressions of competing solutions.*

**Stage 3: Active looking / trigger event**
Opening: *"What happened that made you go from 'this is annoying' to actually doing something about it? Was there a specific moment?"*

Probes:
- "Walk me through that day/week."
- "What was the deadline or pressure?"
- "Who else was involved in that decision?"
- "What did you do first?"

*What to listen for: the 'last straw' event — this is often the most emotionally charged part and the richest push force data. Take your time here.*

**Stage 4: Decision**
Opening: *"Tell me about the day you decided to [try/buy/switch]. What made you pull the trigger?"*

Probes:
- "What almost stopped you?"
- "What questions did you need answered before committing?"
- "Who else weighed in?"
- "What did you imagine it was going to do for you?"

*What to listen for: pull forces (what they were attracted to), anxieties (what almost stopped them), and the mental image they had — this reveals expected outcomes vs. reality.*

**Stage 5: First use / onboarding**
Opening: *"What was the first week like? Walk me through what you actually did."*

Probes:
- "Was it what you expected?"
- "What surprised you, in a good way or bad?"
- "Where did you get stuck?"
- "What did you have to let go of from the old way?"

*What to listen for: habit forces (what they had to unlearn), unmet expectations (gaps between imagined pull and reality), and early wins that reinforced the decision.*

**Stage 6: Current state (if applicable)**
Opening: *"Now that you've been using it for [time], how would you describe it? Is it doing the job you hired it for?"*

Probes:
- "What's still not quite right?"
- "Is there something you still do the old way?"
- "If this went away tomorrow, what would you lose?"

*What to listen for: desired outcomes (what they're measuring success by), residual anxieties, and unmet jobs — these are often the most actionable product opportunities.*

### Four Forces deep dive section

After the timeline, optionally go deeper on any forces that came up:

**If push forces were vague:**
*"You mentioned [X] was frustrating. Can you give me a specific example of when that happened? What did you do when it went wrong?"*

**If pull forces were unclear:**
*"When you imagined [new solution] working perfectly, what did you picture? What would you be able to do that you couldn't do before?"*

**If anxieties surfaced:**
*"You mentioned being worried about [X]. What would have happened if that fear had come true? What was the worst case in your head?"*

**If habits seemed like a factor:**
*"What did you have to stop doing or change when you switched? Was that hard? What did you miss?"*

### Desired outcomes section

End with explicit outcome questions:

- *"How do you know when [this type of work] has gone well? What does success look like?"*
- *"What would have to be true for you to say [product] is genuinely solving this for you?"*
- *"If you were recommending this to a colleague, what would you tell them it's good for?"*

*These questions generate the outcome statements PMs and designers can use for roadmap prioritization.*

### Wrap-up

- *"Is there anything important about how you make these kinds of decisions that I haven't asked about?"*
- Thank them genuinely and tell them what you'll do with the research
- Note: offer to share a summary of findings — most participants appreciate it and it builds future goodwill for your research program

## Output format

```markdown
# JTBD Interview Guide: [Product/Study Name]

**Research question:** [What you most need to learn]
**Participant profile:** [Who this guide is for]
**Session length:** [X minutes]
**Prepared:** [Date]

---

## Moderator notes (read before the session)

[2–3 key reminders: what to listen for, what hypotheses to test, what to probe harder on]

---

## Introduction (5 min)

**Read aloud:**
[Framing statement]

**Warm-up:**
[1–2 warm-up questions]

---

## Timeline Walkthrough (~[X] min)

### Stage 1: First thought
**Ask:** [Opening question]
**Probe if needed:**
- [Probe 1]
- [Probe 2]
- [Probe 3]
*[Facilitation note]*

### Stage 2: Passive looking
[Same format]

### Stage 3: Active looking / trigger event
[Same format]

### Stage 4: Decision
[Same format]

### Stage 5: First use
[Same format]

### Stage 6: Current state *(if relevant)*
[Same format]

---

## Four Forces Deep Dive (~[X] min)

*Use these only if the timeline didn't naturally surface the forces. Pick the 1–2 most relevant.*

[Push / Pull / Anxiety / Habit probes as appropriate]

---

## Desired Outcomes (~5 min)

[Outcome questions]

---

## Wrap-up (2–3 min)

[Closing question + thank-you]

---

## Quick reference: what to listen for

| Force | Listen for | Example phrases |
|-------|-----------|-----------------|
| Push | Frustration, frequency, last straw | "every time", "I kept having to", "finally" |
| Pull | Imagined solution, first impression | "I thought it would", "what attracted me was" |
| Anxiety | Hesitation, what-ifs | "I was worried", "what if", "I wasn't sure" |
| Habits | Old behaviors, inertia | "I'm used to", "we've always", "it would mean changing" |
| Outcomes | Success criteria | "I'd know it's working when", "what I really need is" |
```

## Adaptation notes

**For churned users**: flip stages 5–6 to ask "what made you fire it?" instead of current state. The exit interview is often the most valuable JTBD data you'll ever collect.

**For prospects who haven't switched yet**: stages 1–3 are rich; stages 4–6 are hypothetical. Acknowledge this and use conditional probes ("If you were to...").

**For 30-min sessions**: compress stages 2 and 3 into one, skip the four forces deep dive unless something critical needs probing, and cut stage 6. Prioritize the trigger event (stage 3) and decision (stage 4) — those are where the four forces live.

**For async/written interviews**: convert opening questions to clear written prompts. Note that probing is harder; build more probes into the initial question to compensate.

---
name: jtbd-analyzer
description: >-
  Analyze user research through the Jobs-to-Be-Done (JTBD) lens using the Bob Moesta / Competing Against Luck framework. Use this skill whenever a PM, product designer, or researcher wants to extract JTBD insights from transcripts, interview notes, or raw observations. Triggers on "analyze this through JTBD", "what's the job to be done", "extract jobs from this transcript", "JTBD analysis", "what are users hiring this for", "four forces analysis", "push pull analysis", "struggling moments", "switching triggers". Also use proactively when someone shares interview transcripts and wants to understand why users switched, what progress they're trying to make, or what's driving adoption. This skill does the analytical heavy lifting that normally takes a researcher hours of manual coding.
---

# JTBD Analyzer

Extracts Jobs-to-Be-Done insights from user research using the Bob Moesta / Competing Against Luck framework. Takes transcripts, notes, or observations and produces a structured analysis of the jobs users are trying to get done, the forces driving their decisions, and the outcomes they're seeking.

## The Framework (quick reference)

Bob Moesta's JTBD framework asks: **what progress is this person trying to make in their life?** People don't buy products — they *hire* them to make progress. When they're unhappy enough with their current situation, they *fire* the old solution and hire a new one.

The four forces that drive every switching decision:

```
PUSH (away from old situation)          PULL (toward new solution)
"This is frustrating enough that        "That looks like it could
I need to do something"                 solve this for me"

ANXIETY (about switching)               HABITS (holding them back)
"What if the new thing doesn't          "I already know how to do it
work out? What's the risk?"             this way. Change is effort."
```

A person switches when: **Push + Pull > Anxiety + Habits**

The job itself has three dimensions:
- **Functional**: the practical task ("I need to consolidate feedback from five tools")
- **Emotional**: how they want to feel ("I want to feel confident presenting to stakeholders")
- **Social**: how they want to be perceived ("I want to be seen as someone who runs rigorous research")

## Step 1: Assess what you have

Before starting the analysis, understand your inputs:

- **Single transcript**: do a full four forces analysis for that participant
- **Multiple transcripts**: look for patterns across participants — which forces appear most frequently? Where do people diverge?
- **Notes or summary**: do the best you can with what's there, but flag where quotes would strengthen the analysis
- **Session recordings/highlights**: ask if there are transcripts available; recordings without transcripts limit depth

Ask the user: how many transcripts/interviews are you working from? This shapes how you frame the output (individual portrait vs. cross-study synthesis).

## Step 2: Extract the raw material

Read through the input carefully and pull out:

**Timeline anchors** (Moesta calls this the "timeline interview"):
- When did they first realize something wasn't working? (First thought)
- What happened that made them start actively looking? (Event)
- What did they try first? (Passive looking → active looking)
- When did they make a decision?
- What happened after? (Onboarding experience — often reveals unmet expectations)

**Quotes to capture:**
- Frustration language: "I kept having to...", "every time I...", "the problem was..."
- Aspiration language: "what I really wanted was...", "I imagined...", "I was hoping..."
- Anxiety language: "I was worried that...", "what if...", "I wasn't sure whether..."
- Habit language: "we've always done it this way", "I'm used to...", "changing would mean..."

## Step 3: Build the analysis

### Job Statement

Write a core job statement using the format Bob Moesta uses:

> **When** [situation/context], **I want to** [motivation/desired progress], **so I can** [expected outcome].

Write one statement that captures the central job. Then write the functional, emotional, and social dimensions below it.

Good job statement: *"When I finish a round of user interviews, I want to quickly surface the key themes and present them confidently, so I can influence the product roadmap before priorities get locked."*

Weak job statement (avoid): *"I want a tool that organizes research findings."* — too solution-focused, not progress-focused.

### Four Forces Analysis

For each force, list:
- The specific evidence from the transcript(s)
- Representative quote(s) where available
- Magnitude: High / Medium / Low (based on how much the participant dwelled on it)

**Push forces** (what's frustrating enough to trigger change):
- What was broken, slow, or creating anxiety in the old situation?
- What was the "last straw" moment?

**Pull forces** (what made the new solution attractive):
- What did they imagine the new solution doing for them?
- What specific capability or outcome were they attracted to?

**Anxieties** (what almost stopped them from switching):
- What were they worried about losing?
- What risks did they perceive?
- What questions did they need answered before committing?

**Habits** (what inertia worked against switching):
- What existing behaviors/workflows would need to change?
- What were they giving up that had value?

### Desired Outcomes

List 3–6 outcomes the user is trying to achieve. These are the metrics by which they'll judge whether the "hired" solution is doing its job.

Format:
- **[Outcome]**: [Evidence from transcript]

Example:
- **Present findings in under 30 minutes**: *"I used to spend half a day building the readout deck. I can't do that before every sprint."*

### Competing Solutions (what they were "firing")

What did they have before? What did they almost choose instead? This reveals:
- What "good enough" looked like before switching
- What the real competitive set is (often not who you think)

### Unmet Jobs / Tension Points

Are there jobs mentioned in the transcript that the current solution isn't fully addressing? These are product opportunities. List them clearly.

## Step 4: Cross-study synthesis (if multiple transcripts)

If analyzing more than one transcript, add a synthesis section:

**Consensus Jobs** — which job statements appear consistently across participants?
**Contested Forces** — where do participants diverge? (e.g., for some participants anxiety is high; for others it barely registered)
**Segment hypothesis** — do the patterns suggest different user segments with different primary jobs? Describe each.

## Output format

```markdown
# JTBD Analysis: [Study Name / Date]

**Source:** [X transcripts / interview notes / etc.]
**Analyzed:** [Date]

---

## Core Job Statement

> When [situation], I want to [progress], so I can [outcome].

**Functional job:** [what they're trying to accomplish practically]
**Emotional job:** [how they want to feel]
**Social job:** [how they want to be perceived]

---

## Four Forces

### Push (driving away from old situation)
| Force | Evidence | Quote | Magnitude |
|-------|----------|-------|-----------|
| [Force] | [Context] | "[Quote]" | High/Med/Low |

### Pull (attracting toward new solution)
[Same table format]

### Anxieties (fears about switching)
[Same table format]

### Habits (inertia to overcome)
[Same table format]

---

## Desired Outcomes

- **[Outcome 1]**: [Evidence]
- **[Outcome 2]**: [Evidence]

---

## Competing Solutions

**What they were firing:** [Previous solution + why it fell short]
**What else they considered:** [Alternatives evaluated]

---

## Unmet Jobs / Opportunities

1. [Job or need that isn't fully served — product opportunity]
2. [etc.]

---

## Cross-Study Synthesis *(if multiple transcripts)*

**Consensus:** [Jobs/forces that appear in most transcripts]
**Divergence:** [Where participants differ and what that might mean]
**Segment hypothesis:** [If patterns suggest different user types]

---

## Raw Evidence Bank

Key quotes organized by force — useful for readouts and stakeholder presentations:

**Push quotes:**
- "[Quote]" — Participant [role/context]

**Pull quotes:**
- "[Quote]" — Participant [role/context]

[etc.]
```

## Common mistakes to avoid

- **Projecting jobs**: Only write down what participants actually said, not what you think they meant. If you're inferring, say so.
- **Confusing the job with the solution**: "I want a dashboard" is not a job. "I want to always know where things stand without asking" is.
- **Skipping the timeline**: The sequence of events is where the push/pull forces live. Don't skip to "what do you want" without understanding what happened first.
- **Single quote ≠ pattern**: In a single-participant analysis, note when something is a unique observation vs. something you'd expect to generalize.

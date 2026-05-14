---
name: survey-designer
description: Design research-quality surveys for product teams. Use this skill whenever a PM, product designer, or researcher needs to create a survey — whether to validate a feature hypothesis, test a concept, measure NPS/CSAT, or follow up on user interviews at scale. Also triggers when someone says "write survey questions", "help me build a survey", "I need to validate this with a survey", "what questions should I ask", or any time survey-based research is needed. Produces clean, analysis-ready markdown surveys with validated questions, response options, and strategic rationale. Always use this skill rather than just winging survey questions — biased or poorly structured questions kill research quality.
---

# Survey Designer

Creates research-quality surveys for product teams. Takes a research goal and outputs a complete, ready-to-use survey in markdown with questions, response formats, and the rationale behind each choice.

## Step 1: Gather context

Before writing any questions, collect what you need:

**Required:**
- What are you trying to learn or validate? (the research question/hypothesis)
- Survey type — ask the user to pick one or more:
  - **Feature validation** — does this proposed feature solve the right problem?
  - **Concept testing** — should we build this idea at all? Which direction resonates?
  - **NPS / CSAT** — how satisfied are users? Would they recommend? Where's the friction?
  - **Post-interview follow-up** — you've run interviews; now test whether the themes hold at scale

**Good to know (ask if not obvious):**
- Who is the audience? (existing customers, specific segments, prospects)
- How long can it be? (rule of thumb: 5 min max for cold audiences, 10 min for engaged users)
- What decision will this survey inform? (helps prioritize what to ask)

If the user hasn't provided these, ask before proceeding. A survey built on unclear goals produces unusable data.

## Step 2: Design the survey

### Structure

Every survey follows this skeleton — adapt length to the survey type:

1. **Context-setter** (1 question): Establish where they are in their journey. Usually a role/segment qualifier. Keeps analysis clean.
2. **Behavioral anchor** (1–2 questions): What do they *actually do* today? Grounds their opinions in real behavior, not hypotheticals.
3. **Core questions** (3–7 questions): The heart of what you're testing. See type-specific guidance below.
4. **Open-ended closer** (1 question): "Is there anything else you'd like to share about [topic]?" Always include this — it surfaces what you didn't think to ask.

### Survey type guidance

**Feature validation**
- Ask about the problem first, not the solution. ("How often do you [face this pain]?" before "Would you use a feature that...")
- Use frequency scales over opinion scales where possible: "How often do you..." is more actionable than "How important is..."
- Include a "none of the above" or "this isn't a problem for me" escape hatch so non-sufferers can self-identify

**Concept testing**
- Show the concept clearly (link, description, or mockup) before asking questions
- Always include a comprehension check: "In your own words, what does this do?"
- Ask about desirability, clarity, and believability separately — they're different things
- Test 2–3 concepts comparatively when possible rather than asking about one in isolation

**NPS / CSAT**
- NPS question: "How likely are you to recommend [product] to a colleague or friend?" (0–10 scale, standard wording)
- CSAT: "How satisfied are you with [specific interaction]?" (1–5 scale)
- Always follow with: "What's the primary reason for your score?" — without this, you can't act on the number
- Segment by user role/tenure in analysis, not just raw score

**Post-interview follow-up**
- Start with the top 3–5 themes from your interviews stated as hypotheses
- For each theme: measure prevalence ("How often do you...") and severity ("How much does this affect your work?")
- Include the verbatim language your interviewees used — surveys confirm; interviews discover
- Keep this under 8 questions. You already have depth; you need breadth.

### Response format guide

Choose response formats that match what you actually want to measure:

| Goal | Format |
|------|--------|
| Measure frequency | Never / Rarely / Sometimes / Often / Always |
| Measure satisfaction | 1–5 Likert (Very dissatisfied → Very satisfied) |
| Measure agreement | Strongly disagree → Strongly agree (5-point) |
| Rank priorities | Drag-to-rank or "select top 3" (max-diff style) |
| Capture open qualitative | Free text (1–2 per survey max) |
| NPS | 0–10 numeric scale |
| Yes/No/Maybe | 3-option multiple choice |

Avoid: 7-point scales (cognitive overload), double-barreled questions ("Was it easy and useful?"), and scales without neutral midpoints.

## Step 3: Quality check before outputting

Before finalizing, scan every question for these failure modes:

- **Leading questions**: "How much did you enjoy X?" assumes enjoyment. Fix: "How would you describe your experience with X?"
- **Double-barreled**: "Was it fast and easy?" — can't answer both at once. Split into two.
- **Jargon**: Would a first-day user understand this? If not, rewrite.
- **Hypothetical trap**: "Would you use a feature that..." produces inflated intent. Reframe as behavioral: "How do you currently handle...?"
- **Too many open-ended questions**: More than 2 kills completion rates. Convert extras to multiple choice.

Flag any questions you had to revise and briefly note why — this helps the user understand the changes.

## Output format

Produce a clean markdown document with this structure:

```
# [Survey Name]

**Goal:** [One sentence — what decision will this inform?]
**Audience:** [Who should take this]
**Estimated time:** [X minutes]
**Recommended tool:** Great Question / Typeform / Google Forms

---

## Survey Questions

**Q1. [Question text]**
*Type: [Multiple choice / Likert / Open text / etc.]*
- Option A
- Option B
- Option C

*Why this question:* [1–2 sentences on what it measures and why it's here]

---

[Repeat for each question]

---

## Analysis notes

[Brief guidance on how to slice/interpret the data — e.g., "Compare Q3 responses by role (Q1) to see if the pain is role-specific", "Treat Q5 open text as a follow-up interview queue"]
```

The "Why this question" rationale is important — it helps PMs and designers trust the survey and defend it to stakeholders.

## Tips for Great Question specifically

- GQ supports logic branching — note any skip logic in the question rationale
- Keep survey names descriptive for the repository (e.g., "Feature Validation: Bulk Export — May 2025" not "Survey 3")
- Tag studies with the product area for searchability

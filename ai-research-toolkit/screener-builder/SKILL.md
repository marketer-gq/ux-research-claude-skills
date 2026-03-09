---
name: screener-builder
description: Generate participant screening surveys with qualification logic, disqualifiers, scoring rubrics, and attention checks. Use when a researcher needs to recruit the right participants for a study and needs a screener questionnaire. Also triggers on screener survey, recruitment screener, participant screening, screening questions, recruit participants, or participant qualification criteria. Outputs a complete screening survey with questions, response options, scoring logic, and qualification rules.
---

# Screener Builder

Generates participant screening surveys with qualification logic and scoring.

## When to Use

- During study setup, after defining the target participant profile
- When recruiting for interviews, usability tests, diary studies, or focus groups
- When existing screeners need updating for a new study

## Required Input

1. **Target participant description** — Who are you looking for? Be specific about role, experience, behaviors, or demographics.
2. **Research objectives** — What the study is about (this shapes which attributes matter most for screening).

Optional:
- Number of participants needed
- Study type (interview, usability test, survey, diary study)
- Known disqualifiers (competitors, professional respondents)
- Compensation details (helps set expectations in the screener intro)

## Screener Structure

```
# Participant Screener: [Study Name]

## Screener Introduction
"Thank you for your interest in this research study. We're looking for people
with specific experiences to share their perspective. This screener takes about
3-5 minutes. Your answers help us find the right participants — please answer
honestly. There are no right or wrong answers."

## Section 1: Basic Qualification (Hard Disqualifiers)

These questions determine pass/fail. A "wrong" answer ends the screening.

### Q1: [Question]
- [ ] Option A → QUALIFY
- [ ] Option B → QUALIFY
- [ ] Option C → DISQUALIFY
- [ ] Option D → DISQUALIFY

**Logic:** [Why this question matters]
**Disqualify message:** "Thank you for your interest. Based on your responses,
this particular study isn't the right fit, but we may have other opportunities
in the future."

## Section 2: Experience & Behavior (Scoring)

These questions rank-order qualified candidates.

### Q3: [Question]
- [ ] Option A → +3 points (ideal match)
- [ ] Option B → +2 points
- [ ] Option C → +1 point
- [ ] Option D → 0 points

## Section 3: Attention & Quality Checks

### Q7: [Attention check question]
**Purpose:** Filters out people not reading carefully.
**Correct answer:** [X]
**Action if wrong:** Flag for review (don't auto-disqualify — one miss may be
an honest mistake)

## Section 4: Logistics

### Q10: Availability
[Date/time preference options]

### Q11: Technology setup (if relevant)
[Device, browser, software requirements]

## Scoring Rubric

| Score Range | Classification | Action |
|-------------|---------------|--------|
| 12-15 | Ideal match | Schedule immediately |
| 8-11 | Good match | Schedule if needed |
| 4-7 | Marginal match | Waitlist |
| 0-3 | Poor match | Do not schedule |

## Qualification Summary
- Hard disqualifiers: [list]
- Minimum score to qualify: [X]
- Target sample: [X] participants from [Y] screener completions
```

## Question Design Rules

### Hard Disqualifiers (Section 1)

These are must-have criteria. Keep them to 3-5 questions maximum.

**Always include:**
- The core experience or behavior you're studying
- Professional respondent check (see below)
- Competitor employee check (if relevant)

**Professional respondent filter:**
```
In the past 6 months, how many paid research studies have you participated in?
- [ ] None → +2
- [ ] 1-2 → +1
- [ ] 3-5 → 0 (flag for review)
- [ ] More than 5 → DISQUALIFY
```

**Competitor check (adapt to your context):**
```
Do you or does anyone in your household work for any of the following companies?
[List competitors + your own company as decoys among unrelated companies]
- [ ] [Competitor A] → DISQUALIFY
- [ ] [Competitor B] → DISQUALIFY
- [ ] [Unrelated Company] → no effect
- [ ] None of the above → QUALIFY
```

### Scoring Questions (Section 2)

These differentiate between qualified candidates. Award more points for:
- Recency of relevant experience (last month > last year)
- Frequency of relevant behavior (daily > occasionally)
- Closeness to ideal profile (decision-maker > influencer > end user)

**Avoid:**
- Self-assessment questions ("How experienced are you with...") — people overestimate
- Hypothetical questions ("Would you be interested in...") — everyone says yes
- Questions that reveal what you're looking for (participants will game obvious screeners)

### Attention Checks (Section 3)

Include 1-2 attention checks, placed mid-screener:

**Instructional check:**
```
We want to make sure you're reading each question carefully.
For this question, please select "Somewhat agree."
- [ ] Strongly agree
- [ ] Somewhat agree ← correct
- [ ] Neutral
- [ ] Somewhat disagree
- [ ] Strongly disagree
```

**Consistency check:**
Ask a question early that you can verify against a later response. If answers contradict, flag for review.

### Response Option Design

- Randomize option order for any question where order might bias responses
- Include "Other (please specify)" for questions where your options might not cover all cases
- Avoid "N/A" unless it's genuinely possible — it becomes a lazy default
- For frequency questions, use specific anchors ("2-3 times per week") not vague ones ("sometimes")

## Common Screener Mistakes This Skill Prevents

1. **Too strict** — Screener disqualifies 95% of respondents. The skill differentiates hard disqualifiers from nice-to-have criteria.
2. **Telegraphing answers** — Questions make it obvious what you're looking for. The skill disguises qualifying criteria.
3. **No scoring** — All qualified candidates treated equally. The skill rank-orders so you interview the best matches first.
4. **No attention checks** — Professional survey takers slip through. The skill includes quality filters.
5. **Leading questions** — Questions that prime participants before the study even starts. The skill keeps screener questions neutral.

## Chaining with Other Skills

- **Input from:** research-brief-writer (participant criteria and study type)
- **Output to:** Paste into your recruitment platform (Great Question, User Interviews, Respondent, etc.)

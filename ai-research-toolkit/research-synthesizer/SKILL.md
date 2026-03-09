---
name: research-synthesizer
description: Synthesize patterns, themes, and contradictions across multiple research transcripts or notes. Use when a researcher has 5-30 cleaned transcripts (or sets of interview notes) and needs to identify recurring themes, flag contradictions, and map evidence strength. Also triggers on cross-study synthesis, thematic analysis, pattern finding across interviews, or consolidating research findings. Outputs a structured synthesis document with ranked themes, supporting quotes, contradictions, and signals worth investigating.
---

# Research Synthesizer

Processes multiple transcripts or research notes and produces a structured thematic synthesis.

## When to Use

- After cleaning transcripts (pairs well with the transcript-cleaner skill)
- When you have 5-15 transcripts or sets of notes to analyze
- For cross-study synthesis across related research efforts
- Before building stakeholder readouts or presentations

For sets larger than 15, run in batches of 10-12 and then synthesize the batch outputs together.

## How It Works

### Step 1: Ingest and Index

Read all provided transcripts/notes. For each document, extract:
- Participant identifier (use pseudonyms if real names aren't provided)
- Key statements, observations, and quotes
- Contextual metadata (role, company size, use case) if available

### Step 2: Bottom-Up Theme Identification

Identify themes inductively from the data rather than imposing categories:

1. **Extract atomic observations** — individual claims, behaviors, or reactions from each participant
2. **Cluster by similarity** — group observations that address the same underlying topic or behavior
3. **Name the clusters** — give each theme a descriptive, specific name (not vague labels like "usability issues" — instead: "onboarding flow creates false confidence about feature completeness")
4. **Assign prevalence** — count how many unique participants contributed evidence to each theme

### Step 3: Analyze Contradictions

This is where the most valuable insights often hide. For each theme, actively look for:
- Participants who expressed the opposite view
- Behaviors that contradict stated preferences
- Differences that correlate with participant attributes (role, experience level, company size)

### Step 4: Identify Weak Signals

Flag observations from only 1-2 participants that seem significant despite low prevalence. These are often early indicators of emerging patterns that a larger study would confirm.

## Output Format

Always structure the synthesis document as follows:

```
# Research Synthesis: [Topic/Study Name]

## Study Overview
- Number of participants: X
- Participant profiles: [brief summary of who was interviewed]
- Research questions: [what the study set out to learn]
- Date range: [when sessions occurred]

## Theme Summary
| Theme | Prevalence | Strength | Key Insight |
|-------|-----------|----------|-------------|
| [Name] | X/Y participants | Strong/Moderate/Emerging | [One sentence] |

## Detailed Themes

### Theme 1: [Specific, descriptive name]
**Prevalence:** X of Y participants
**Strength:** Strong / Moderate / Emerging

**Summary:** [2-3 sentences explaining the theme]

**Supporting Evidence:**
- P3: "[Direct quote]" — [context for the quote]
- P7: "[Direct quote]" — [context]
- P11: [Observed behavior or paraphrased insight]

**Nuances:** [Important variations within this theme]

[Repeat for each theme, ranked by prevalence]

## Contradictions
[For each contradiction, explain what's in tension, who said what, and possible explanations for the disagreement]

## Weak Signals
[Observations from 1-2 participants that seem worth investigating further, with reasoning for why they matter]

## Methodology Notes
[Any caveats about the analysis — sample size, participant skew, topics not covered]
```

## Quality Guidelines

**Do:**
- Use direct quotes as evidence wherever possible
- Distinguish between what participants said vs. what they did (stated vs. revealed preferences)
- Note when a theme is driven primarily by one vocal participant vs. broadly supported
- Flag your confidence level for each theme

**Don't:**
- Editorialize or make product recommendations — that's the researcher's job
- Treat prevalence as the only measure of importance (a safety issue mentioned by 1 person can matter more than a convenience issue mentioned by 10)
- Merge genuinely different themes just because they're related
- Strip context from quotes in ways that change their meaning

## Batch Processing for Large Studies

For 15+ transcripts:

1. Split into batches of 10-12 (group by participant similarity if possible)
2. Run synthesis on each batch
3. Create a meta-synthesis from the batch outputs, looking for:
   - Themes that appear across multiple batches (strong signal)
   - Themes unique to one batch (may correlate with participant attributes)
   - Contradictions between batches

## Chaining with Other Skills

- **Input from:** transcript-cleaner (cleaned transcripts)
- **Output to:** stakeholder-readout-generator (synthesis becomes the basis for readouts), insight-tagger (themes inform taxonomy)

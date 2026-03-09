---
name: insight-tagger
description: Categorize and tag research highlights, quotes, and observations with themes, sentiment, and connections. Use when a researcher has a set of highlights or quotes from interviews, usability tests, or surveys and needs structured taxonomy applied. Also triggers on tag research data, categorize highlights, organize insights, taxonomy building, code qualitative data, or thematic coding. Outputs tagged highlights with theme labels, sentiment scores, cross-references, and an emergent taxonomy.
---

# Insight Tagger

Applies structured taxonomy to research highlights — themes, sentiment, and cross-references.

## When to Use

- After synthesis, when organizing insights for a research repository
- For batch processing highlights from external sources before importing into a repository tool
- To audit and clean up existing tags for consistency
- When processing open-ended survey responses
- During ongoing repository maintenance as new highlights come in

## Input Format

Accepts highlights in any of these formats:
- A list of quotes with participant identifiers
- A spreadsheet or CSV of highlights
- Synthesis output from the research-synthesizer skill
- Raw notes with observations and quotes mixed together

If the input is messy, first extract discrete highlights (one observation or quote per entry) before tagging.

## Tagging Process

### Step 1: Extract Highlights

If input isn't already in discrete highlight form, break it down:
- Each highlight = one atomic observation, quote, or behavioral note
- Preserve the participant identifier and source context
- Keep quotes verbatim; paraphrase observations clearly

### Step 2: Generate Theme Tags

Use bottom-up coding (tags emerge from the data, not from a predetermined list):

1. Read through all highlights once without tagging
2. On second pass, assign 1-3 theme tags per highlight
3. Tags should be specific and descriptive:
   - Good: `onboarding-expectations-mismatch`, `workaround-for-missing-export`
   - Bad: `usability`, `feature-request`, `general-feedback`
4. Consolidate similar tags as you go (don't let `signup-friction` and `registration-difficulty` and `account-creation-issues` all coexist — pick the best one)

**If the user provides an existing taxonomy**, use it as the primary tag set. Add new tags only when existing ones genuinely don't fit. Flag any new tags for the user to review.

### Step 3: Assign Sentiment

For each highlight, assign one of:
- **Positive** — Participant expressed satisfaction, delight, or praise
- **Negative** — Participant expressed frustration, confusion, or criticism
- **Neutral** — Factual observation or description without emotional valence
- **Mixed** — Contains both positive and negative elements (common in "I like X but Y is frustrating" statements)

### Step 4: Cross-Reference

Identify connections between highlights:
- Highlights that support the same theme from different participants
- Highlights that contradict each other
- Highlights that describe the same workflow from different angles

### Step 5: Build Taxonomy Summary

After tagging all highlights, produce a taxonomy overview:

```
## Taxonomy Summary

| Tag | Count | Sentiment Distribution | Example Highlight |
|-----|-------|----------------------|-------------------|
| [tag-name] | X highlights | +Y / -Z / ~W | "[shortest representative quote]" |

### Tag Hierarchy
- [Parent category]
  - [Child tag 1] (X highlights)
  - [Child tag 2] (Y highlights)
- [Parent category]
  - [Child tag 1] (X highlights)
```

## Output Format

```
# Tagged Highlights: [Study/Project Name]

## Taxonomy Summary
[As above]

## Tagged Highlights

### H1
- **Quote/Observation:** "[text]"
- **Participant:** [identifier]
- **Source:** [transcript/session reference]
- **Tags:** `tag-1`, `tag-2`
- **Sentiment:** Positive / Negative / Neutral / Mixed
- **Connected to:** H4, H12 (same theme, different participant); H7 (contradicts)

### H2
[Same structure]
```

## Quality Checks

After tagging is complete, run these checks:

1. **Orphan tags** — Any tag applied to only 1 highlight? Consider whether it's genuinely unique or should merge with a related tag.
2. **Overloaded tags** — Any tag applied to 20%+ of all highlights? Probably too broad — look for meaningful sub-categories.
3. **Sentiment skew** — If 90%+ of highlights are the same sentiment, either the research had very uniform findings (possible) or the tagging is too coarse (more likely).
4. **Missing cross-references** — Highlights with the same tag from different participants should be connected.

## Integrating with an Existing Taxonomy

When the user provides their team's existing tag set:

1. Map each existing tag to the data — which highlights fit?
2. Identify gaps — highlights that don't fit any existing tag
3. Propose new tags for the gaps (clearly marked as additions)
4. Flag existing tags that had zero matches (may be obsolete or not relevant to this study)
5. Present the mapping to the user for review before finalizing

## Chaining with Other Skills

- **Input from:** research-synthesizer (themes inform initial tag candidates), transcript-cleaner (clean quotes for tagging)
- **Output to:** affinity-mapper (tagged highlights as input for clustering), stakeholder-readout-generator (tagged data supports evidence-based readouts)

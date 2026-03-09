---
name: affinity-mapper
description: Run digital affinity mapping on research observations, quotes, or notes — grouping related items into clusters, naming clusters, identifying outliers, and showing relationships. Use when a researcher has a large volume of unstructured observations from interviews, usability tests, survey open-ends, or support tickets that need organizing into meaningful groups. Also triggers on affinity diagram, cluster observations, group research notes, sort findings, thematic clustering, or card sorting analysis. Outputs clustered observations with named groups, outlier highlights, and a relationship map.
---

# Affinity Mapper

Runs digital affinity mapping — groups observations into meaningful clusters.

## When to Use

- During analysis, when you have a large set of unstructured observations (50+)
- After interviews, usability testing, or survey open-end analysis
- When you need to make sense of support tickets, feature requests, or feedback themes
- As input for synthesis (affinity mapping is often the step before formal synthesis)

## Input

Accepts observations in any format:
- A list of quotes or notes (one per line)
- Sticky-note style observations (short phrases)
- Spreadsheet or CSV exports
- Mixed notes and quotes from multiple sources

Each observation should be one discrete thought. If the input contains compound observations ("The signup was easy but the dashboard was confusing"), split them into separate items before mapping.

## The Affinity Mapping Process

### Step 1: Normalize Observations

Ensure each input item is:
- One atomic observation (one idea per item)
- Attributed to a source if possible (participant ID, ticket number, etc.)
- Written in consistent form (all observations or all quotes — don't mix without labeling)

### Step 2: First-Pass Grouping

Read through all observations and create initial clusters based on semantic similarity:

1. Start with the first observation — it becomes Cluster 1
2. For each subsequent observation, either:
   - Add it to an existing cluster if it's clearly related
   - Create a new cluster if it represents a genuinely different topic
3. Don't force items into clusters — if something doesn't fit, leave it ungrouped for now

Target 8-15 clusters for a set of 50-100 observations. Fewer than 8 usually means clusters are too broad. More than 20 usually means they're too granular.

### Step 3: Name the Clusters

Each cluster gets two labels:
- **Descriptive name** — What this cluster is about (e.g., "Integration setup overwhelm")
- **Insight statement** — What this cluster reveals (e.g., "Users expect integrations to work automatically and are frustrated when manual configuration is required")

Naming rules:
- Names should be specific enough that someone could guess what's in the cluster
- Avoid generic labels: "Usability" tells you nothing. "Navigation between sections breaks user flow" tells you everything.
- The insight statement is the researcher's interpretation — what the cluster means, not just what it contains

### Step 4: Identify Outliers

Items that don't fit any cluster are often the most interesting:
- Mark them explicitly as outliers
- For each outlier, note why it doesn't fit (genuinely unique? Or is the cluster structure wrong?)
- Group outliers loosely if there are more than 5 — they might form their own emerging cluster

### Step 5: Map Relationships

Between clusters, identify:
- **Causal relationships** — Cluster A leads to Cluster B (e.g., "Confusing onboarding" causes "Workaround creation")
- **Tensions** — Cluster A contradicts Cluster B (e.g., "Users want simplicity" vs. "Users want advanced controls")
- **Sequences** — Cluster A happens before Cluster B in the user journey

## Output Format

```
# Affinity Map: [Study/Project Name]

## Overview
- Total observations: [X]
- Clusters identified: [Y]
- Outliers: [Z]
- Sources: [participant count or data sources]

## Cluster Map

### Cluster 1: [Descriptive Name]
**Insight:** [What this cluster reveals]
**Size:** [X] observations
**Sources:** [Which participants/sources contributed]

Observations:
1. "[Observation text]" — [Source]
2. "[Observation text]" — [Source]
3. "[Observation text]" — [Source]

---

### Cluster 2: [Descriptive Name]
[Same structure]

---

## Outliers
These observations didn't fit established clusters but may signal emerging patterns:

1. "[Observation]" — [Source] — **Why it's notable:** [brief note]
2. "[Observation]" — [Source] — **Why it's notable:** [brief note]

## Relationships Between Clusters

| From | To | Relationship | Evidence |
|------|----|-------------|----------|
| Cluster 1 | Cluster 3 | Causes | [Brief explanation] |
| Cluster 2 | Cluster 5 | Contradicts | [Brief explanation] |
| Cluster 1 | Cluster 2 | Precedes (journey) | [Brief explanation] |

## Cluster Hierarchy (if applicable)

If some clusters are sub-groups of a larger theme:
- **[Parent theme]**
  - Cluster 1: [Name] ([X] observations)
  - Cluster 3: [Name] ([Y] observations)
- **[Parent theme]**
  - Cluster 2: [Name] ([X] observations)
```

## Important Limitations

This skill does semantic grouping — it clusters items based on the words and concepts they share. But research insight often comes from connections that aren't semantically obvious.

**Use this output as a draft, not a finished analysis.** The value is that 80% of the sorting is done correctly, freeing the researcher to spend their time on:
- Moving items between clusters where the AI's grouping doesn't match their domain knowledge
- Identifying non-obvious connections between clusters
- Challenging the cluster structure itself (maybe the categories are wrong)
- Drawing interpretive conclusions from the patterns

## Chaining with Other Skills

- **Input from:** insight-tagger (tagged highlights), transcript-cleaner (clean quotes)
- **Output to:** research-synthesizer (clusters inform theme identification), stakeholder-readout-generator (cluster insights become presentation content)

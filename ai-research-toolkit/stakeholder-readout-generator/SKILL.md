---
name: stakeholder-readout-generator
description: Reframe research findings for different stakeholder audiences — PMs, designers, leadership, or cross-functional teams. Use when a researcher has synthesis or findings and needs to present them to different audiences with different framing. Also triggers on research readout, stakeholder presentation, present findings, executive summary of research, PM research summary, or design research handoff. Outputs structured content blocks tailored to the specified audience, ready to paste into slides or documents.
---

# Stakeholder Readout Generator

Takes research findings and reframes them for specific stakeholder audiences.

## When to Use

- After synthesis, before presenting findings
- When the same research needs to reach different audiences
- When translating research into language that drives action for a specific team

## Required Input

1. **Research findings** — A synthesis document, set of themes, or findings summary. The richer the input, the better the output.
2. **Target audience** — Who is this readout for?

## Audience Profiles

### Product Managers
**What they need:** Decisions and priorities.
**Lead with:** Actionable recommendations mapped to product decisions.
**Structure:**
- What we learned (3-5 bullet summary)
- What this means for the roadmap (specific recommendations with evidence)
- What to build / change / stop (prioritized)
- Open questions that need more research
- Risk of inaction

**Tone:** Direct, decision-oriented. Connect every finding to a product implication.

### Designers
**What they need:** User behavior, mental models, and pain points.
**Lead with:** User journey moments and experience details.
**Structure:**
- User mental models (how participants think about the problem space)
- Key pain points mapped to specific journey moments
- Workarounds participants have created (design inspiration lives here)
- Quotes that capture the emotional experience
- Design implications and opportunity areas

**Tone:** Empathetic, detail-rich. Preserve the human stories.

### Leadership / Executives
**What they need:** Business impact and strategic implications.
**Lead with:** The "so what" — why this matters to the business.
**Structure:**
- Executive summary (3 sentences max)
- Business impact of key findings (revenue, retention, competitive position)
- Strategic recommendations (with confidence levels)
- Investment required vs. expected return
- Risks if findings are ignored

**Tone:** Concise, business-oriented. No jargon. Every finding connects to a metric or outcome they care about.

### Cross-Functional Teams
**What they need:** Shared understanding and alignment.
**Lead with:** The story — what participants experience and why it matters.
**Structure:**
- Research context (why we did this, who we talked to)
- The participant story (narrative arc of the key findings)
- What each team should take away (engineering, design, marketing, support)
- Shared priorities and next steps
- How to dig deeper (where to find the full data)

**Tone:** Narrative, accessible. Avoid team-specific jargon.

## Output Format

The output is structured content blocks — not a slide deck. Each block has a header, key points, and supporting evidence that can be dropped into any presentation format.

```
# Research Readout: [Study Name]
## Prepared for: [Audience]

### Context
- Study type: [methodology]
- Participants: [count and profile summary]
- Research period: [dates]

---

### [Section 1 — varies by audience]

**Key point:** [One clear statement]

**Evidence:**
- [Supporting data point or quote]
- [Supporting data point or quote]

**Implication:** [What this means for this audience specifically]

---

### [Section 2]
[Same structure]

---

### Recommendations
1. [Specific, actionable recommendation] — Confidence: High/Medium/Low
   - Based on: [which findings support this]
2. [Recommendation]
3. [Recommendation]

### Open Questions
- [What we still don't know and how to find out]

### Appendix: Key Quotes
[5-8 most impactful participant quotes with context]
```

## Reframing Guidelines

The same finding gets different framing depending on the audience. Here's how the same insight translates:

**Finding:** 8 of 12 participants abandoned onboarding at the integration step.

- **For PMs:** "The integration step is the primary drop-off point in onboarding. Recommend prioritizing a guided setup flow or reducing required integrations for first-time setup. Estimated impact: 15-20% improvement in activation rate based on the volume of drop-offs at this step."
- **For Designers:** "Participants hit a wall at the integration step. They described feeling 'overwhelmed by options' and 'not sure which ones I actually need.' Several tried to skip it entirely. The mental model mismatch is between 'I want to try the product' and 'the product wants me to commit to a full setup.'"
- **For Leadership:** "We're losing a significant portion of new signups at a single friction point in onboarding. The fix is scoped and high-confidence. Resolving it could meaningfully improve our trial-to-paid conversion."

## Quality Checks

Before delivering a readout:

1. **The "so what" test** — Every finding should answer "so what?" for the target audience. If a finding just states what happened without connecting it to what the audience should do or care about, it needs reframing.
2. **Evidence check** — Every claim should trace back to specific data. No unsupported assertions.
3. **Jargon check** — Review for research jargon that the target audience wouldn't use. Replace with their language.
4. **Action check** — Does the readout make clear what should happen next? Findings without implications are just trivia.

## Chaining with Other Skills

- **Input from:** research-synthesizer (synthesis document is the primary input)
- **Output to:** This is typically the end of the analysis chain. Output goes into presentations, documents, or Slack updates.

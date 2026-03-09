---
name: research-brief-writer
description: Generate complete research briefs from a business question or product decision — including methodology recommendation, participant criteria, timeline, and success metrics. Use when a PM or stakeholder brings a question that needs translating into a research plan, or when a researcher needs to write a brief for a new study. Also triggers on research plan, study brief, research proposal, project brief for research, methodology recommendation, or study design. Outputs a complete research brief ready for stakeholder review and approval.
---

# Research Brief Writer

Translates business questions into structured research briefs with methodology recommendations.

## When to Use

- At project kickoff, when a stakeholder brings a question
- When planning a new research study
- For training purposes — showing what a solid brief looks like for different study types
- When comparing methodology options for a given question

## Required Input

At minimum:
1. **The business question or decision** — What does the team need to know? What decision will this research inform?

Helpful context:
- Who is asking and why now
- What's already known (prior research, analytics, assumptions)
- Timeline constraints
- Budget or resource constraints
- Target audience or user segment

## Brief Structure

```
# Research Brief: [Study Title]

## Background
[2-3 paragraphs on why this research is needed. What's the business context?
What decision is pending? What do we already know and what's missing?]

## Research Objectives
Primary: [The main question this study must answer]
Secondary:
- [Additional question 1]
- [Additional question 2]

## Recommended Methodology

**Method:** [Specific method]
**Rationale:** [Why this method is the best fit for these objectives]

**Alternative considered:** [Other method and why it was deprioritized]

### Method Details
- Format: [Remote/in-person, moderated/unmoderated]
- Session length: [Duration]
- Number of sessions: [Count with justification]

## Participant Criteria

### Must-Have (Hard Requirements)
- [Criterion 1]: [Specific definition]
- [Criterion 2]: [Specific definition]

### Nice-to-Have (Soft Preferences)
- [Criterion]: [Why this matters]

### Exclusions
- [Who to exclude and why]

### Sample Composition
| Segment | Count | Rationale |
|---------|-------|-----------|
| [Segment A] | X | [Why this many] |
| [Segment B] | Y | [Why this many] |
| **Total** | **Z** | |

## Timeline

| Phase | Duration | Dates | Owner |
|-------|----------|-------|-------|
| Brief approval | X days | | |
| Screener & guide development | X days | | |
| Recruitment | X days | | |
| Data collection | X days | | |
| Analysis & synthesis | X days | | |
| Readout & share-out | X days | | |
| **Total** | **X weeks** | | |

## Success Metrics
How we'll know this research was successful:
- [Metric 1: e.g., "Clear recommendation on whether to pursue Feature X"]
- [Metric 2: e.g., "Participant persona validated or revised"]
- [Metric 3: e.g., "Top 3 usability barriers identified with severity ranking"]

## Stakeholders
| Name | Role | Involvement |
|------|------|-------------|
| [Name] | Decision-maker | Brief approval, readout |
| [Name] | Collaborator | Guide review, observation |
| [Name] | Informed | Readout recipient |

## Risks & Mitigation
| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| [Risk 1] | High/Med/Low | [Plan] |
| [Risk 2] | High/Med/Low | [Plan] |

## Appendix: Prior Research
[Links or summaries of relevant existing research]
```

## Methodology Selection Logic

This is the skill's standout feature — it doesn't just fill in a template, it evaluates the research question against method fit.

### Decision Framework

**Use generative interviews when:**
- Exploring a problem space or unmet need
- The team doesn't know what they don't know
- You need rich, contextual understanding of behavior and motivation
- Sample: 8-15 participants

**Use usability testing (moderated) when:**
- Evaluating a specific design or prototype
- You need to observe real-time behavior and ask follow-up questions
- Tasks are complex or the product is early-stage
- Sample: 5-8 participants

**Use usability testing (unmoderated) when:**
- Evaluating specific, well-defined tasks
- You need larger sample sizes for comparison
- The product is mature enough for self-guided testing
- Sample: 10-20 participants

**Use surveys when:**
- You need to validate findings at scale
- Questions can be answered without observation
- You need quantitative confidence intervals
- Sample: 100+ responses (calculate based on population and confidence level)

**Use diary studies when:**
- Behavior happens over time (not in a single session)
- Context matters (work environment, daily routines)
- You need to capture in-the-moment reactions
- Sample: 10-15 participants over 1-4 weeks

**Use card sorting when:**
- Designing information architecture or navigation
- Understanding mental models for categorization
- Sample: 15-30 participants (open sort), 30+ (closed sort)

**Use concept testing when:**
- Comparing multiple concepts or directions
- Validating value propositions before building
- Gauging initial reactions and comprehension
- Sample: 8-12 per concept (qualitative), 50+ per concept (quantitative)

### Recommending Mixed Methods

Some questions need more than one method. When recommending mixed methods:
- Explain what each method contributes that the other can't
- Sequence them logically (usually qualitative first to explore, quantitative second to validate)
- Show how findings from phase 1 inform phase 2

## Sample Size Justification

Don't just state a number — explain why:

- **Qualitative studies:** Reference saturation (most themes emerge by 8-12 interviews in a homogeneous sample). If the sample is diverse, more sessions are needed.
- **Usability testing:** Reference Nielsen's finding that 5 users find ~85% of usability issues (for a single user group doing the same tasks).
- **Surveys:** Calculate based on population size, desired confidence level (usually 95%), and margin of error (usually ±5%).
- **If the user's study doesn't fit neat formulas**, explain the tradeoffs between sample size, confidence, and practical constraints.

## Chaining with Other Skills

- **Input from:** This is typically the starting point of a research project
- **Output to:** discussion-guide-builder (objectives and participant criteria feed the guide), screener-builder (participant criteria become screener questions)

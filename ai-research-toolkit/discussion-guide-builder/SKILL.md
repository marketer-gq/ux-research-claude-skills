---
name: discussion-guide-builder
description: Generate semi-structured discussion guides for qualitative research interviews. Use when a researcher has defined research objectives and needs an interview protocol with warm-up questions, core topic blocks, follow-up probes, transition language, and timing estimates. Also triggers on interview guide, interview script, qualitative protocol, moderator guide, or research interview questions. Outputs a ready-to-use discussion guide formatted for moderated research sessions.
---

# Discussion Guide Builder

Creates semi-structured discussion guides for qualitative research interviews.

## When to Use

- During research planning, after research questions are defined
- When setting up moderated interviews or focus groups
- When a PM or stakeholder provides a business question that needs translating into interview structure

## Required Input

Before generating, you need at minimum:

1. **Research objectives** — What specific questions is this study trying to answer? (Vague objectives like "understand the user experience" produce vague guides. Push for specifics.)
2. **Participant profile** — Who will be interviewed? Their role, experience level, and relationship to the topic shape question framing.

Optional but helpful:
- Session length (default: 60 minutes)
- Moderation style preference (conversational vs. structured)
- Specific topics or features to cover
- Questions to avoid (competitor NDAs, sensitive topics)

## Guide Structure

Always follow this structure, adjusting timing to fit the session length:

```
# Discussion Guide: [Study Name]

## Session Details
- Duration: [X] minutes
- Participant profile: [who]
- Research objectives: [what we're learning]
- Moderator notes: [any special considerations]

---

## Introduction (5 minutes)

[Rapport-building script including:]
- Welcome and thank you
- Purpose framing (honest but not leading)
- Recording consent and confidentiality
- "No wrong answers" framing
- Permission to ask follow-ups

**Script:**
"Thanks for taking the time to talk with me today. I'm [name], and I'm researching [broad topic — not your hypothesis]. I'll ask some questions about your experience with [domain], and I'm genuinely curious about your perspective — there are no right or wrong answers. Everything you share stays confidential and will only be used to improve [product/service]. Is it okay if I record this session? The recording is just for my notes and won't be shared outside the research team."

---

## Warm-Up (5 minutes)

[2-3 easy, non-threatening questions that:]
- Build comfort with the interview format
- Establish relevant context about the participant
- Create a natural bridge to core topics

---

## Core Topics

### Topic 1: [Name] (X minutes)

**Primary question:**
[Open-ended question that targets the research objective]

**Follow-up probes (use as needed):**
- [Probe for depth]
- [Probe for specific examples]
- [Probe for process/workflow]
- [Probe for emotions/reactions]

**Transition to next topic:**
"[Natural bridge sentence]"

### Topic 2: [Name] (X minutes)
[Same structure]

### Topic 3: [Name] (X minutes)
[Same structure]

---

## Wrap-Up (5 minutes)

- "Is there anything about [topic] that I didn't ask about but you think is important?"
- "If you could change one thing about [relevant experience], what would it be?"
- Thank participant
- Explain next steps
- Ask if they'd be open to a brief follow-up if needed
```

## Question Quality Rules

These rules exist because the most common failure in discussion guides is asking questions that produce shallow or biased answers.

**Replace closed questions with open ones:**
- Bad: "Do you find the onboarding confusing?"
- Good: "Walk me through what happened when you first set up your account."

**Replace leading questions with neutral ones:**
- Bad: "How frustrated were you when the export failed?"
- Good: "What happened when you tried to export? How did you react?"

**Replace hypothetical questions with experience-based ones:**
- Bad: "Would you use a feature that automatically tagged your data?"
- Good: "Tell me about the last time you organized or categorized your research data. What did that process look like?"

**Replace jargon with participant language:**
- Bad: "How do you handle participant recruitment for longitudinal studies?"
- Good: "When you need to talk to the same people over a longer period, how do you find and keep in touch with them?"

**After generating the guide, review every question and flag any that are likely to produce:**
- Yes/no answers
- Socially desirable responses
- Hypothetical speculation instead of real experience

Suggest alternatives for each flagged question.

## Timing Guidelines

For a 60-minute session:
- Introduction: 5 minutes
- Warm-up: 5 minutes
- Core topics: 40-45 minutes (3-4 topics, 10-12 minutes each)
- Wrap-up: 5 minutes

Scale proportionally for other session lengths. The most common mistake is cramming too many topics into the available time. 3-4 core topics is usually the maximum for a 60-minute session if you want depth.

## Moderator Notes

Include inline notes throughout the guide for the moderator:

- `[LISTEN FOR: specific thing to pay attention to]`
- `[IF PARTICIPANT MENTIONS X: ask about Y]`
- `[SKIP IF: condition when this section isn't relevant]`
- `[TIME CHECK: you should be here by X minutes in]`

## Chaining with Other Skills

- **Input from:** research-brief-writer (research objectives and methodology)
- **Output to:** transcript-cleaner (guides help identify expected speaker roles for cleaning)

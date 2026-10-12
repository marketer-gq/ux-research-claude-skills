---
name: theme-quality-auditor
description: Check whether the themes (or affinity labels) in a qualitative analysis are themes or topic summaries — flagging subject labels with no claim, themes that mirror the discussion guide, descriptions that list what was discussed rather than what it means, thin evidence, overlapping themes, and "themes emerged" language. Use on a synthesis or readout before it is shared, including one an AI tool produced. Asks questions to sharpen a theme; it never rewrites one.
---

# Theme Quality Auditor

Most syntheses contain themes called "Onboarding", "Pricing" and "Views on the mobile app". Those aren't themes. They're folders.

Braun & Clarke, whose reflexive thematic analysis is the method most research teams say they're using, draw the line clearly. A theme is a pattern of shared meaning organised around a **central organising concept**: a claim about what the data means, one a reader could disagree with. A topic summary gathers everything participants said about a subject, and it has no central claim. "Onboarding" is a topic summary. "People give up on setup before they reach anything they'd value" is a theme.

Topic summaries are common, in human and AI-produced syntheses alike, because grouping by subject is easy and interpreting isn't. This skill catches them.

It doesn't fix it, and that's deliberate. Deciding what a pattern means is the analyst's job. For each flagged theme the skill asks the question that gets the analyst to a claim. It doesn't write the claim.

## Goal

Every theme in the synthesis makes a claim about what the data means, one a reader could disagree with, and is backed by enough evidence to carry it. The analyst gets there by answering your questions, not by accepting your rewrites.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You know reflexive thematic analysis, codebook approaches and affinity diagramming well enough to tell which one the analyst is using and to judge their themes by that method's standards, not another's.

- Respect the analyst's interpretive authority. Your job is to ask the question that gets them to a claim, never to write the claim for them.
- A flag is a prompt for a conversation. A short name can still carry a sharp claim, and a theme from one participant can still be central; say so when the context shows it.
- Ask about the participants who don't fit. A theme that can't account for divergent cases isn't finished.
- Be specific and collegial. Name the theme, the reason it was flagged and the one question that would move it forward.

## Quick start

```bash
python scripts/audit_themes.py themes.md
python scripts/audit_themes.py themes.md --guide discussion_guide.md
python scripts/audit_themes.py themes.json --approach codebook --json findings.json
python scripts/audit_themes.py affinity_groups.md --approach affinity
```

The exit code is 1 when any theme reads as a topic summary, so the check can gate a readout.

## Input

**Themes** as markdown, one `##` heading per theme. Under each heading: description paragraphs, blockquoted extracts with attribution (`— P3`, `(P3)`, `[P3]`), and `###` subthemes. Consecutive `>` lines are one extract, attributed once, and the attribution can sit on the line after the block. A top-level `#` title is ignored. If the file uses only `#` headings, those are read as themes.

Or JSON: a list of `{name, description, quotes, subthemes}`, where each quote is either a string or `{text, participant}`.

**The discussion guide**, optionally, with `--guide`, one item per line. This enables the most telling check: a theme that is really one of your interview questions turned into a heading.

## What it checks

| Check | Signal strength | What it catches |
|---|---|---|
| Topic-shaped name | strong | "Views on…", "Experience of…", "Challenges with…", "Role of…", "Likes and dislikes", "Other"; category labels ("Admin pain points", "Customer support interactions", "Onboarding experiences and challenges"); activity labels with no claim ("Getting started", "Managing permissions"); interview questions as names ("What do you think of the mobile app?") |
| Bare subject label | strong | "Pricing", "Receipts", "Trust", "Trust in reporting": a subject with no claim |
| Mirrors the guide | strong | "Onboarding" when the guide asked "Tell me about your onboarding experience". A name that already makes a claim isn't flagged for sharing words with a guide item, only for being a near-copy of it |
| Short label | medium | Two words or fewer that aren't recognised as a subject or a claim |
| Domain-summary description | medium | "Participants talked about…", "This theme covers…", "A range of…" |
| Thin evidence | review | No extracts, or extracts from fewer than 2 participants (`--min-participants`, a working default, not from the literature). Reported separately; never counts toward a topic-summary verdict |
| Overlap | review | Two themes sharing 45% or more of their vocabulary (working default, not from the literature), or the same extract under both |
| Emergence language | review | "Themes emerged", "insights surfaced in the data", "the data revealed". Only when it's about themes or findings, so "emerging markets" and "the problem surfaced at checkout" pass |
| Prevalence as warrant | note | "Most participants mentioned…" used as the reason something is a theme |
| Theme count | note | More than about ten often means codes were promoted to themes. That's the skill's own heuristic, not a rule from the literature |

**Verdicts.** A theme reads as a **topic summary** when it has one strong signal, or two medium signals where one is about its name. Evidence doesn't count toward this: something mentioned once can be central. A theme is marked **review** with any other signal, including thin evidence, and **ok** otherwise.

A claim after a colon counts. "Workarounds: people keep a private record because they don't trust the tool's totals" passes, because the part after the colon says something. A list of contents after the colon doesn't: "Billing: including invoices and receipts" is still a topic.

## The questions it asks

For every theme that isn't clean, the output ends with a question for the analyst. The question fits what was flagged:

- **No claim:** *"What do the 2 extracts under 'Onboarding' have in common, apart from being about it? Write it as one sentence someone could disagree with."*
- **Mirrors the guide:** *"'Views on the mobile app' follows the guide item 'What do you think of the mobile app?'. Across the answers to that question, what do participants share beyond having answered it?"*
- **Thin evidence only:** *"Who else said something that means the same as 'Receipts get lost between approval steps'? If nobody did, it can still be central; say why it matters."*

For every theme, flagged or not, also ask whether it accounts for participants who said the opposite. A theme that only holds because the divergent cases were left out needs those cases named, or a narrower claim.

These are questions rather than rewrites for two reasons.

**It's where researchers draw the line.** In Maze's survey, 82% of researchers "say interpreting nuance and emotion still requires human judgment" ([Maze](https://maze.co/blog/ai-study-builder/)). A tool that rewrote themes would be taking over the part researchers say needs them.

**It's also where AI rewrites fail.** A model asked to turn "Pricing" into a theme will produce a fluent claim, drawn from whatever it finds plausible rather than from what the extracts share. The question forces the analyst back to the data.

## Codebook approaches

Not every team is doing reflexive thematic analysis. Framework analysis and other codebook approaches sometimes use domain summaries deliberately, as a way of organising material rather than interpreting it.

`--approach codebook` downgrades the topic-summary findings to notes and exits 0. Every other check still runs. Use it when domain summaries are the intended output, and say so in the report so readers know what they're looking at.

## Affinity diagrams

Affinity diagramming (the KJ method) is the most common way UX teams group findings ([UXPA Body of Knowledge](https://usabilitybok.org/affinity-diagram)). `--approach affinity` checks each group label as if it were a theme. That's the method's own standard: Holtzblatt & Beyer's Contextual Design writes affinity labels in the user's voice, as statements ("I don't know who approved what"), not categories ("Audit history").

Descriptions that summarise a group's contents ("This group covers…") are downgraded to notes, as in codebook mode, because the label is what has to carry the claim. Label findings still count, and the exit code is still 1 when a label reads as a topic summary.

## Limitations

- **Name detection is pattern-based, not a parser.** It recognises claim-shaped names by claim-carrying words and gerund openings. An unusually phrased theme can be misread either way. Read the flagged theme before acting on the verdict.
- **It can't judge whether a claim is a good one.** "Users want it to be better" passes the name check and is still nearly empty. The skill catches the absence of a claim, not a weak one.
- **Guide matching is word overlap.** A name that already makes a claim is only flagged when it's a near-copy of a guide item, but the claim detection is pattern-based, so a real theme can still be flagged. Check it.
- **Overlap uses vocabulary, not meaning.** Two themes about the same thing in different words won't be caught, and two genuinely distinct themes that share domain words may be flagged.
- **It doesn't verify the extracts.** Whether each quote exists in the transcripts is the `evidence-integrity-auditor`'s job. Run both: that one checks the evidence is real, and this one checks the theme is a theme.

## Worked example

A five-theme synthesis from eight interviews, audited against its discussion guide:

```
5 themes · 2 read as themes · 0 need review · 3 read as topic summaries

[TOPIC SUMMARY] Onboarding
    - (name) a bare subject label ("Onboarding") with no claim in it
    - (guide) mirrors a discussion-guide item ("Tell me about your onboarding experience.")
    - (description) Describes what was discussed, not what it means ("Participants talked about")
    ask: "Onboarding" follows the guide item "Tell me about your onboarding experience".
         Across the answers to that question, what do participants share beyond having
         answered it? Write it as one sentence someone could disagree with.

[ok] Approvers treat the tool as a queue to clear, not a decision to make
    3 extract(s) from 3 participant(s)

[TOPIC SUMMARY] Views on the mobile app
    - (name) named as a topic — the shape of an interview question turned into a heading
    - (guide) mirrors a discussion-guide item ("What do you think of the mobile app?")
    - (evidence) thin evidence: rests on 1 participant (P3). Check whether more
      participants support this

[TOPIC SUMMARY] Receipts
    - (name) a bare subject label ("Receipts") with no claim in it
    - (evidence) thin evidence: rests on 1 participant (P6). Check whether more
      participants support this
    ask: What is the one extract under "Receipts" saying, beyond being about it? Write it
         as one sentence someone could disagree with. Then check whether more
         participants support it.

[ok] Workarounds: people keep a private record because they don't trust the tool's totals
    - (prevalence) The description leans on how many participants said it.

ACROSS THE ANALYSIS
  - (emergence) [line 3] "themes emerged" — themes are constructed by the analyst,
    not found in the data. Say what you did ("we developed", "we constructed").
```

"Receipts" is a topic summary because of its name, not its evidence. Renamed "Receipts go missing between approval steps" with the same single extract, it would be marked review for thin evidence only.

The two themes that pass are the only two telling a stakeholder something they couldn't have guessed from the interview questions. The other three are the questions, with answers filed underneath.

## Workflow

1. Run `evidence-integrity-auditor` first, so the extracts under each theme are real.
2. Run this on the themes, with the guide.
3. For each topic summary, answer the question it asks. Sometimes the answer is a claim, and the theme gets renamed. Sometimes the extracts share nothing beyond a subject, and the "theme" gets split up or dropped.
4. Re-run. Treat a rename that only swaps a label for a longer label ("Onboarding experiences and challenges") as still failing.

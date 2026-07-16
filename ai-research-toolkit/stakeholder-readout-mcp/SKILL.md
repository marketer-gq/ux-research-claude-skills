---
name: stakeholder-readout-mcp
description: Pull recent findings, highlights, and insights from one or more Great Question studies and draft a stakeholder readout in your team's preferred format, with supporting quotes from transcripts. Use when summarizing one or more studies for leadership, a stakeholder, or a cross-functional audience. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.1
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Stakeholder Readout (MCP)
Take a researcher from "I need to brief leadership on the dashboard study" to "here's a draft you can put in the deck or send as an email." Pulls insights, highlights, and supporting quotes from one or more studies, then assembles them into the format your team uses, with your team's voice.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which encode your team's readout format, voice, and conventions. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "find recent insights on this study"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Output format
- **Default format:** `{{default_format}}`
  <!-- Options that come up often: slide-deck bullets (one finding per slide with supporting quote underneath); exec one-pager (top 3 findings, each two sentences); narrative email (intro, 3-5 findings as prose, recommended next step); structured doc (sections per finding with full evidence). Pick the format your team uses most often; the agent will produce that unless the researcher asks for another. -->
- **Format-specific structure:** `{{format_structure}}`
  <!-- For each format your team uses, the structural rules. For example, for slide-deck bullets: "Headline (8 words max). One finding sentence (under 15 words). One supporting quote with speaker attribution. No more than 5 bullets per slide." -->
### Voice and framing
- **Voice:** `{{voice_description}}`
  <!-- For example: "Plain, declarative, second-person when addressing the reader. Avoid hedging words. Avoid 'users felt X' phrasing; say 'X' directly." -->
- **Finding framing:** `{{finding_framing}}`
  <!-- For example: "Each finding leads with the takeaway, not the method. Stakeholders don't need to know we used a card sort to learn that the nav is confusing." -->
- **Quote handling:** `{{quote_handling}}`
  <!-- For example: "Use exact participant words. Light copy-editing for fluency is okay (filler removal, sentence-boundary fixes). Never paraphrase a quote and present it as a quote. Attribute by role and segment, not by name." -->
### Evidence rules
- **Quotes per finding:** `{{quotes_per_finding}}`
  <!-- For example: "One supporting quote per finding in slide format, two for a one-pager, three or more for a structured doc." -->
- **Highlight precedence:** `{{highlight_precedence}}`
  <!-- For example: "Prefer highlights tagged by the research team over highlights tagged by automation. Prefer highlights with multiple supporting moments over single-instance highlights." -->
- **Insight reuse:** `{{insight_reuse_rule}}`
  <!-- For example: "If an insight already exists in the repository for the study, lead with the insight's title and one-line description, then add evidence beneath. Don't restate findings that the insight already names; build on them." -->
### Sensitive content
- **Confidential or NDA-flagged studies:** `{{confidentiality_rule}}`
  <!-- For example: "If the source studies are flagged confidential, surface that prominently in the readout header. If any quote contains the participant's company name or customer identifiers, redact before including." -->
- **What never appears in a stakeholder readout:** `{{never_include}}`
  <!-- For example: "Participant names. Email addresses. Anything from a screener response. Internal Slack reactions or commentary from the research team." -->
### Scope and length
- **Default scope:** `{{default_scope}}`
  <!-- For example: "One study unless the researcher names more. If the researcher says 'recent work on X,' look back 90 days within studies on that topic." -->
- **Default length:** `{{default_length}}`
  <!-- For example: "5 findings for slide format, 3 for a one-pager, 5-8 for a structured doc. The agent can go shorter if the evidence is thin." -->
## How this works with Great Question
<!--
GQ mechanics: plain-language steps describing how to drive Great Question
to accomplish the task. These steps name intents, not specific tool names.
The agent resolves intents to concrete tools at runtime using the MCP
server's own tool listing. Future state: this section migrates to a
GQ-owned playbook when that layer exists.
-->
The agent runs these steps in order.
### 1. Understand the brief
Gather, from the researcher:
- Which studies to draw from (by ID, name, or description like "our recent onboarding work").
- The audience and format (apply **Your rules** defaults if not specified).
- Anything to lead with or avoid (specific themes, sensitivities, recommendations the researcher already wants to land).
If the researcher gives a vague scope ("everything from the last quarter"), surface the candidate study set before pulling evidence. Don't burn time pulling content from studies the researcher didn't intend.
### 2. Pull the existing repository content for those studies
For each study in scope, find:
- Any insights already authored for the study. These are the strongest starting point because the research team has already done the synthesis work; the readout's job is to retell them for a stakeholder audience.
- Highlights filed against the study. Apply the **Your rules** highlight precedence rule.
- Reels filed against the study, if any. Reels are often the cleanest evidence to point a stakeholder at, especially for video-rich studies.
If a study has no insights and few highlights, surface that to the researcher before drafting. Either the study isn't synthesized yet, or it's a candidate for a different kind of readout (raw findings rather than synthesized).
### 3. Pull supporting quotes from transcripts
For each finding the agent is about to write, find one or more supporting quotes from the study's transcripts using full-text search on the finding's keywords. Apply the **Your rules** quote-handling rule for editing and attribution.
If a finding has no clean supporting quote available, surface that to the researcher. The finding may still be valid (numbers can support it; behavioral observations can support it) but absent a quote, the readout reader gets less feeling for the participant's experience. The researcher decides whether to include the finding without a quote, soften the claim, or drop it.
### 4. Draft the readout
Apply, in this order:
- The format from **Your rules** (slide-deck bullets, one-pager, email, doc).
- The format-specific structure from **Your rules**.
- The voice and finding framing from **Your rules**.
- The evidence rules from **Your rules** for quote count, highlight precedence, and insight reuse.
- The sensitive-content rules from **Your rules**.
Lead with the most important finding. Don't bury the headline.
### 5. Surface the draft to the researcher
Hand the researcher:
- The draft readout, in the format from **Your rules**.
- A brief inventory of what was pulled: which studies, which insights, which highlights, how many quotes per finding.
- Any flags: findings without supporting quotes, confidentiality concerns, scope decisions the agent made on the researcher's behalf.
- A note about what's intentionally not in the readout (per **Your rules**): participant names, screener content, internal commentary.
The researcher edits or asks for revisions. The agent doesn't publish, post, or send the readout anywhere; that's the researcher's call.
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **Insights are the strongest starting point.** When a study has insights authored, they represent work the research team has already done. The readout's job is to retell that work for a stakeholder audience, not to redo synthesis from raw highlights and transcripts.
- **Highlights are richer than transcripts for evidence.** A highlight already carries a research-team annotation explaining why the moment matters. A raw transcript snippet has no such framing. Prefer highlight content over raw transcript snippets when both cover the same ground.
- **Full-text search across transcripts is a search, not a guarantee.** The agent's query keywords may miss the moment that best supports a finding. If the researcher pushes back on a quote choice, search again with different terms rather than defending the original.
- **Don't publish or send.** The skill drafts. The researcher decides where the readout ends up: a deck, an email, a doc, a Slack post. The agent never sends a readout to a stakeholder directly.
- **If a study has no insights and few highlights, say so.** Drafting a readout from sparse evidence produces a readout that overclaims. Surface the gap rather than papering over it.
## External-system hooks
<!--
Reserved seam for forking customers to extend with their own integrations
(Slack, Notion, Linear, PagerDuty, calendars, etc.). The library template
ships with this section visible but empty. The skill works end-to-end
against Great Question alone. If your team adds an integration, document
it here so the next person who edits the skill can see the seam.
-->
_None in the library template. The skill works end-to-end against Great Question alone._
Common extensions teams add when they fork:
- **Push the finished readout into the team's slide template** so the format-specific structure renders into real slides automatically.
- **Cross-link the readout to the research plan or project tracker** so the finished artifact shows up where the work lives.
- **Post a short notice in your team chat** when a readout is drafted, so reviewers know to look.
- **Pull stakeholder-specific context from your CRM or product analytics** when the audience is a specific customer or a specific feature team.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a request like:
> Draft a stakeholder readout from our dashboard usability study. Slide-deck bullets format. Audience is the product team.
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms the study and the format. Confirms the audience.
3. Pulls the existing insights on the dashboard study (3 authored insights). Pulls highlights filed against the study (24 highlights, of which 18 are research-team-tagged per the precedence rule). Reels: none.
4. For each of the 3 insights, finds one supporting quote from transcripts that best illustrates the insight. Two of the three have clean quotes; one finding has no quote that lands cleanly.
5. Drafts the readout: 3 finding slides plus a context slide and a "what's next" slide. Each finding leads with the takeaway, has one supporting quote with role-and-segment attribution. The one finding without a clean quote is flagged inline for the researcher's call.
6. Hands the draft to the researcher: 5-slide outline, inventory of what was pulled, flag on the quoteless finding, note that confidentiality was checked and the study is not NDA-flagged.
Time elapsed: a couple of minutes plus the researcher's review. The researcher's edits are usually small: tightening a headline, swapping a quote for one they remember being stronger, sometimes adding a recommendation the agent didn't propose.
## Changelog
- **0.1 (2026-06-10):** Initial library template version. Lean toward insights as the strongest starting point; highlights and transcripts as supporting evidence. Multiple output formats supported through **Your rules** placeholders.

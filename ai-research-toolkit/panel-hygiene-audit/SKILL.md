---
name: panel-hygiene-audit
description: Audit your Great Question candidate panel for over-recruitment, thin segments, and cooldown violations, then propose remediation. Read-only — it reports and recommends but never modifies candidates. Use before a recruitment-heavy study or as a regular panel health check. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.1
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Panel Hygiene Audit
Run a structured read of your candidate panel: who's been over-recruited, which segments are running thin, which candidates are inside their cooldown window, and where the agent would recommend recruiting from next. This skill audits and reports. It doesn't shortlist, invite, or modify candidates; that's the recruitment skill's job.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which encode your team's panel-health thresholds and policy. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
For the recruitment workflow itself (shortlist, send invitations), see the recruitment skill. This skill informs that decision but doesn't make it.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "list saved candidate segments"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Health thresholds
- **Over-recruitment threshold:** `{{over_recruitment_threshold}}`
  <!-- For example: "More than 3 studies in the past 12 months, or more than 1 study in the past 60 days." Defines when a candidate is over-tapped relative to your org's panel-health goals. -->
- **Cooldown period:** `{{cooldown_period_days}}`
  <!-- For example: 60. Candidates within this window since their last participation are flagged as on-cooldown. Distinct from the over-recruitment threshold: cooldown is recency; over-recruitment is total frequency. -->
- **Segment health threshold:** `{{segment_health_threshold}}`
  <!-- For example: "A segment is healthy if it has at least 50 contactable candidates not on cooldown. Below 30 is concerning. Below 10 is critical." Use absolute counts that match your team's expected recruitment volume. -->
- **Engagement quality:** `{{engagement_quality_rule}}`
  <!-- For example: "Candidates who declined or no-showed their last two invitations get flagged for engagement-decay even when other thresholds pass." -->
### Audit scope
- **Default lookback window:** `{{default_lookback_days}}`
  <!-- For example: 90. The window the audit considers for "recent" participation activity. Older history is still factored into over-recruitment totals but isn't the primary focus. -->
- **Default audit scope:** `{{default_audit_scope}}`
  <!-- For example: "Audit the top 10 segments by recruitment volume. The full panel is too broad for a useful first-pass audit; sampling by segment gives faster signal." -->
- **Specific segments to always include:** `{{always_audit_segments}}`
  <!-- For example: "Always include our 'enterprise customers' and 'high-engagement panel' segments because they're load-bearing for most studies." -->
- **Segments to always exclude:** `{{never_audit_segments}}`
  <!-- For example: "Internal employees, opted-out candidates, and the 'do not recruit' list." -->
### Remediation framing
- **What "healthy" looks like in the report:** `{{healthy_definition}}`
  <!-- For example: "A segment is healthy when it has enough contactable, not-on-cooldown candidates to support 3 months of normal recruitment volume." -->
- **How to phrase concerns:** `{{concern_phrasing_rule}}`
  <!-- For example: "Lead with the concrete impact: 'segment X has 12 contactable candidates; your typical study needs 25.' Don't editorialize beyond the numbers; let the researcher draw their own conclusions about urgency." -->
- **Recommended action types:** `{{recommended_action_types}}`
  <!-- For example: "When a segment is low, recommend one of: (a) broaden the segment criteria, (b) recruit new candidates with a panel-growth study, (c) pause recruitment from the segment for a quarter to let cooldown clear, (d) split into sub-segments to find untapped pools. Don't recommend more aggressive contact of cooldown candidates as a remediation." -->
## How this works with Great Question
<!--
GQ mechanics: plain-language steps describing how to drive Great Question
to accomplish the task. These steps name intents, not specific tool names.
The agent resolves intents to concrete tools at runtime using the MCP
server's own tool listing. Future state: this section migrates to a
GQ-owned playbook when that layer exists.
-->
The agent runs these steps in order.
### 1. Understand the audit request
Gather, from the researcher:
- The scope. Is this a general panel health check, an audit ahead of a specific study, or a deep-dive on one segment?
- Any segments to focus on or exclude beyond the **Your rules** defaults.
- The lookback window if different from the **Your rules** default.
- What output the researcher wants: a written report, a list of action items, both.
If the request is general ("how healthy is our panel?"), surface the **Your rules** default scope as a starting point and let the researcher narrow or broaden.
### 2. Enumerate the segments in scope
List the saved candidate segments on the account. Apply:
- The **Your rules** default audit scope (e.g., "top 10 by recruitment volume" or "all segments").
- The always-include and never-exclude rules from **Your rules**.
- Anything the researcher named in step 1.
End of step 2: a list of segments to audit.
### 3. Pull candidate-level data for each segment in scope
For each segment:
- Resolve the segment to its candidate pool.
- For each candidate in the pool, gather participation history within the lookback window.
This is read-heavy. For large segments, the agent should paginate cleanly rather than trying to pull the entire pool in one call. Surface the pagination state to the researcher if it affects how quickly the audit completes.
### 4. Apply the health rules from Your rules
For each candidate, determine:
- Are they currently on cooldown (per **Your rules** cooldown period)?
- Are they over-recruited (per **Your rules** over-recruitment threshold)?
- Are they showing engagement decay (per **Your rules** engagement quality rule)?
For each segment, aggregate:
- Total candidates, contactable candidates, candidates not on cooldown, healthy candidates (contactable + not on cooldown + not over-recruited + not engagement-decayed).
- Compare against the **Your rules** segment health threshold.
### 5. Draft the report
Apply the **Your rules** concern-phrasing rule. The report has three parts:
- **Snapshot:** what's healthy, what's concerning, what's critical. One-line per segment with the headline number.
- **Detail per segment:** for each segment, the breakdown of total / contactable / not-on-cooldown / healthy. Flag the candidates contributing most to over-recruitment or engagement decay so the researcher can investigate individually if needed.
- **Recommendations:** for each concerning or critical segment, one or two recommended actions from the **Your rules** recommended-action-types list. Don't pad. If a segment is healthy, don't invent a recommendation.
### 6. Hand back to the researcher
Send the researcher:
- The report.
- A short inventory: which segments audited, which candidates flagged individually, any segments the agent couldn't fully audit (e.g., pagination limits or missing data).
- A pointer to the recruitment skill for any action the researcher decides to take. The audit doesn't act; it informs.
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **This skill is read-only by design.** No shortlisting, no invitations, no candidate updates. The audit informs decisions; the recruitment skill acts on them. If the researcher asks "okay, invite the healthy candidates from segment X," hand them to the recruitment skill rather than acting in this skill.
- **Segments are read-only via MCP today.** The agent can list, get, and use segments as filters, but can't create or modify segment definitions through this skill. If a recommendation calls for splitting a segment into sub-segments, the recommendation is for the researcher to do that work in the GQ UI; the agent can't.
- **Large segments need paginated reads.** The candidate-search and list tools paginate. For segments with hundreds of candidates, the audit may take multiple calls. Surface the pagination state if it affects how the audit completes; don't silently truncate at the first page.
- **Server-side filters (contactability, restriction, eligibility) are inherited by reads.** The agent's view of a segment is already filtered to what the caller can access. If a segment appears smaller than the researcher expects, restriction may be in play; mention that as a possible explanation rather than reporting a misleading count.
- **Don't recommend over-contacting cooldown candidates.** No matter how short a segment is, the cooldown rule from **Your rules** is policy, not a suggestion. The remediation options are broaden, grow, pause, or split, not "recruit through the cooldown."
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
- **Cross-reference segments against external CRM or product-usage data** to surface segments whose definition has drifted from how the underlying audience actually behaves.
- **Push the report into a recurring panel-health dashboard** outside GQ so the team can spot trends across audits.
- **Open a ticket per critical segment** so remediation work has a tracked artifact.
- **Schedule the audit on a recurring basis** (e.g., monthly) so panel hygiene becomes a habit, not a one-off.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a request like:
> Run a panel hygiene audit before we launch the Q3 enterprise admin study. Focus on the enterprise segments.
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms scope (enterprise segments only) and lookback (90 days, per **Your rules** default).
3. Lists saved segments. Filters to enterprise-named segments plus the always-include set from **Your rules**: enterprise-admins-US, enterprise-admins-EU, enterprise-decision-makers, and the always-included high-engagement-panel.
4. Pulls candidates and participation history for each segment.
5. Applies thresholds: cooldown (60 days), over-recruitment (more than 3 studies in 12 months), engagement decay (2+ recent declines).
6. Aggregates:
   - **enterprise-admins-US**: 64 total, 51 contactable, 38 not on cooldown, 29 healthy. Healthy ✓.
   - **enterprise-admins-EU**: 22 total, 18 contactable, 12 not on cooldown, 9 healthy. Concerning. Recommendation: broaden the segment criteria (currently filters to only 5 countries) before launching the Q3 study.
   - **enterprise-decision-makers**: 41 total, 35 contactable, 28 not on cooldown, 24 healthy. Healthy ✓.
   - **high-engagement-panel**: 18 total, 17 contactable, 4 not on cooldown, 4 healthy. Critical. Recommendation: pause recruitment from this segment for a quarter to let cooldown clear; consider running a panel-growth study to refresh it.
7. Hands back the report with the four segment summaries, the recommendations, a flagged list of 6 candidates contributing disproportionately to over-recruitment across the audited segments, and a pointer to the recruitment skill for action.
Time elapsed: a couple of minutes for a focused audit; longer for a full panel scan. The value is consistency: the same thresholds applied every time, the same recommendation framing, no editorializing beyond the numbers.
## Changelog
- **0.1 (2026-06-10):** Initial library template version. Read-only audit workflow. Covers segment-level and candidate-level health checks against **Your rules** thresholds. Hands off to the recruitment skill for action.

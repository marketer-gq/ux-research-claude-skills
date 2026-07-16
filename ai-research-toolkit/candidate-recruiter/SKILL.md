---
name: candidate-recruiter
description: Find the right candidates for a Great Question study, filter for fit, shortlist them, and send screener invitations, applying your org's recruitment rules. Use when recruiting participants onto a study by name, by segment, or by a description of who you're looking for; the skill confirms before anything is sent. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.2
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Candidate Recruiter
Take a researcher from "I want to talk to this kind of person" to "the invitations are out." Handles candidate discovery (from a segment, a search, or a hand-curated list), filters for fit, shortlists onto the study, and sends screener invitations. The researcher confirms before anything is sent.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which encode your org's recruitment policy: contactability rules, cooldown periods, over-recruitment thresholds, batch sizing, and confirmation thresholds. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
For authoring the screener email copy itself, see the email-copy skill. This skill sends invitations; the email-copy skill writes them.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "search for candidates," "shortlist candidates onto the study," "send screener invitations"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Candidate discovery preferences
- **Preferred starting point:** `{{preferred_starting_point}}`
  <!-- Where the agent looks first. Options: "an existing segment," "a fresh search by attribute," "a list the researcher hands me." Most orgs lean on segments first because they encode panel hygiene rules already. -->
- **When the researcher describes who they want in plain language:** `{{description_resolution_rule}}`
  <!-- For example: "First, check whether a saved segment matches the description. If yes, use the segment. If no, run a search and propose a new segment definition for the researcher to save." -->
### Eligibility and fit
- **Cooldown period:** `{{cooldown_period_days}}`
  <!-- For example: 60. Candidates who participated in any study within the last N days are deprioritized or skipped. Encode your org's cooldown here. GQ's server-side filter handles contactability; this is the extra rule layered on top. -->
- **Over-recruitment threshold:** `{{over_recruitment_threshold}}`
  <!-- For example: "no more than 3 studies in the past 12 months." Defines when a candidate is over-tapped relative to your org's panel health goals. -->
- **Segment exclusions:** `{{segment_exclusions}}`
  <!-- Any segments the agent should always exclude from recruitment (e.g., a "do not recruit" segment, internal employees, etc.). List them here. -->
- **Geographic, demographic, or attribute filters:** `{{baseline_attribute_filters}}`
  <!-- Any baseline filters your org always applies (e.g., "exclude anyone with consent_expired flag," "exclude candidates flagged as low engagement"). -->
### Batch sizing
- **Default invitation batch size:** `{{default_batch_size}}`
  <!-- For example: 30. The number of candidates to invite at once when the target sample is reached through multiple invitations. Smaller batches give better quality and recovery; larger batches hit target faster. Most orgs land between 25 and 75. -->
- **Maximum per batch:** 500
  <!-- Hard GQ limit. The shortlist tool accepts up to 500 candidate IDs per call. Don't propose larger batches even when the segment is bigger; split into multiple sends. -->
- **Oversample factor:** `{{oversample_factor}}`
  <!-- For example: 3x. Invite this many times the target sample because not everyone will respond, qualify, or schedule. -->
### Confirmation
**The agent must get explicit researcher approval before sending screener invitations. Always. No exceptions.**
Sending is not recallable. Once an invitation email is dispatched, there is no unsend, no cancel, no retraction. Even a small batch sent in error has real cost: candidate goodwill, panel hygiene, the researcher's relationship with their participants. Treat every send as a one-way door.
The skill enforces this with two separate approvals at two separate moments, even when the researcher's original request was "do both" (shortlist and send). See orchestration steps 4 and 6.
- **Shortlist approval:** the researcher confirms the candidate list before any shortlist write. Shortlisting is reversible.
- **Send approval:** the researcher confirms again, with the actual message preview, immediately before any send. The two approvals are not interchangeable.
- **Hard-stop thresholds (additional caution beyond the standard approval):** `{{hard_stop_thresholds}}`
  <!-- For example: "Stop and explicitly call out before requesting send approval if the batch is over 200 candidates, or if any candidate has been invited in the last 14 days, or if the message is a custom draft rather than the configured screener message." These are situations where the agent surfaces extra warnings on top of the standard send approval, not replacements for it. -->
### Reporting
- **What to report back:** `{{reporting_rules}}`
  <!-- For example: "Counts of invited, skipped (by reason), and remaining-in-segment. Names of candidates the agent flagged for cooldown or over-recruitment. Link to the study's participants page in GQ." -->
## How this works with Great Question
<!--
GQ mechanics: plain-language steps describing how to drive Great Question
to accomplish the task. These steps name intents, not specific tool names.
The agent resolves intents to concrete tools at runtime using the MCP
server's own tool listing. Future state: this section migrates to a
GQ-owned playbook when that layer exists.
-->
The agent runs these steps in order.
### 1. Understand the recruitment request
Gather, from the researcher:
- The study (by ID or by name).
- Who they want to talk to. The researcher may give this as:
  - A specific saved segment ("invite our enterprise admins segment")
  - A description ("admins at companies with 1000+ employees who haven't been in a study this year")
  - A hand-curated list of names, emails, or candidate IDs
- The target sample size.
- Whether to send screener invitations now, just shortlist for now, or both.
- Any deviations from the org's standard recruitment rules (e.g., "ignore the cooldown for this one because it's an urgent customer escalation").
If anything required is missing, ask for it before proceeding. Group missing fields into a single message rather than asking one at a time.
### 2. Resolve the candidate pool
Based on the researcher's framing:
- **Named segment:** look up the segment by name, confirm with the researcher that it's the right one, and search for candidates matching the segment.
- **Description:** apply the description-resolution rule from **Your rules**. Usually: check whether an existing saved segment matches; if not, run a search using attribute filters that match the description.
- **Hand-curated list:** look up each candidate by name, email, or ID. Surface anyone the agent can't find.
At the end of step 2, the agent has a candidate pool. Don't shortlist or invite yet.
### 3. Apply org recruitment rules
For each candidate in the pool, apply the rules in **Your rules**:
- Skip candidates within the cooldown period.
- Skip or flag candidates over the over-recruitment threshold.
- Apply segment exclusions.
- Apply baseline attribute filters.
GQ also filters server-side: candidates already on the study, inaccessible to the caller's teams, uncontactable, or ineligible are skipped automatically at shortlist time and at send time. The agent doesn't need to re-implement those checks; the agent's job is the org-policy layer on top.
After applying the rules, the agent has a filtered pool. Apply the oversample factor from **Your rules** to determine how many candidates to invite.
### 4. Get shortlist approval
Surface to the researcher:
- The count of candidates the agent plans to invite, the target sample size, and the oversample factor applied.
- A breakdown of the filtering: candidates discovered, candidates skipped by reason (cooldown, over-recruited, excluded, etc.).
- A statement that this approval is **for shortlisting only**, not for sending invitations. Sending will require a separate approval in step 6.
Wait for explicit researcher approval before any write action. If the researcher says "looks good, send them," do not treat that as send approval. Confirm: "I'll shortlist these 24 candidates now. I'll come back to you with the actual screener message preview before sending invitations, even though you've already said yes to sending." Then proceed.
### 5. Shortlist the candidates onto the study
Once approved, shortlist the candidates onto the study. GQ accepts up to 500 candidate IDs per call; if the approved batch is larger, split into multiple shortlist calls.
The shortlist response will report any candidates skipped server-side (already on the study, inaccessible, uncontactable, ineligible). Capture those for the final report.
### 6. Get send approval, then send (if the researcher asked to send)
If the researcher asked only for shortlisting, skip this step. Tell them where to send from in the GQ UI if they change their mind.
If the researcher asked to send invitations, do **not** send yet. First:
- Confirm which message will be used. By default, GQ uses the study's configured screener message. If the researcher wants a different message, the email-copy skill is the right surface to author or revise it first, and the resulting message can be referenced here.
- **Show the actual message that will go out.** Subject line, body, sender. Don't summarize it. Don't describe it. Render it.
- Show the final recipient count (after any server-side filtering during shortlist in step 5).
- Surface any hard-stop thresholds from **Your rules** that apply (large batch, recent re-invite, custom message draft, etc.). These are warnings on top of the standard approval, not replacements for it.
- Ask the researcher explicitly: "Send this screener invitation to these N candidates? Yes or no."
Wait for an unambiguous yes. Treat ambiguous answers ("looks good," "go ahead," "ship it") as a request for clarification, not as approval. Confirm: "Sending the invitation as shown to the N candidates listed above. Confirm with a clear yes to proceed."
Only after an unambiguous yes: send. The send tool only delivers to contactable candidates. Server-side filtering applies the same way it does for shortlisting. For batches over 500, split into multiple sends.
### 7. Report back to the researcher
Send the researcher:
- Counts: shortlisted, invited (if applicable), skipped (broken down by reason).
- Any flags: candidates skipped for cooldown or over-recruitment, candidates the agent couldn't resolve from the original input, hard-stop thresholds that triggered.
- A link to the study's participants page in GQ.
- Recommended next step: "Invite another batch in a few days if the response rate is below target," or "the segment is exhausted; consider broadening the criteria."
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **Sending is not recallable. Get explicit approval at the moment of send.** Once a screener invitation is sent, the email is out. There is no unsend. The shortlist approval in step 4 is not send approval, even if the researcher said "send them too" in their original request. Always show the actual message and the final recipient count and ask for an unambiguous yes immediately before sending. Treat ambiguous answers as a request for clarification, not as approval.
- **Shortlist and send tools have a 500-candidate maximum per call.** For batches over 500, split into multiple calls. Surface the split to the researcher so they can see what's happening.
- **GQ server-side filters apply automatically.** The shortlist and send tools skip candidates who are already on the study, inaccessible to the caller's teams, uncontactable, or ineligible. The agent's filtering (cooldown, over-recruitment, exclusions) is the additional org-policy layer; don't try to replicate the server-side checks.
- **The send tool sends to the study's configured screener message by default.** If the researcher wants a different message, the email-copy skill is the right surface to draft or revise it first. The send tool can take an optional message reference if the researcher has authored one specifically for this batch.
- **If a step fails after candidates have been shortlisted, stop the workflow.** Don't retry sends silently. Summarize what was successfully shortlisted, whether anything was sent, and what state the study is in. Ask the researcher how to proceed.
- **Re-invitations within a short window can damage panel goodwill.** The cooldown rule from **Your rules** is policy, not just convention. If the agent finds itself proposing to re-invite anyone who was invited recently, surface that prominently rather than treating it as a routine skip.
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
- **Pull a candidate list from your CRM or panel-management tool** before step 2, when the researcher hands the agent a description rather than a segment.
- **Post a recruitment summary to your team chat** after step 7, so the team has visibility into who's been invited and when.
- **Cross-link the recruitment batch to your project tracker** so each batch shows up in the work record.
- **Log over-recruitment flags to a panel-health dashboard** outside GQ, so the team can spot patterns across studies.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a request like:
> Recruit for our enterprise dashboard study. Pull from the "Enterprise admins, US" segment. Target sample is 8 sessions, so invite 24 people. Don't invite anyone who was in our last admin study (the one from April).
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms the study, confirms the segment, confirms the target (8) and oversample (3x = 24).
3. Searches candidates matching the "Enterprise admins, US" segment. Pool size: 78.
4. Applies **Your rules**: cooldown period filters out 12 candidates invited in the last 60 days. Over-recruitment filter flags 4 candidates who've been in 3+ studies in the past year. The "previous admin study from April" exclusion the researcher named removes another 9. Filtered pool: 53.
5. Selects 24 from the filtered pool. Shows the researcher: 24 to shortlist (this approval is for shortlisting only), 25 remaining in the filtered pool for future batches, breakdown of the 25 skipped.
6. Researcher approves the shortlist.
7. Shortlists the 24 candidates onto the study. GQ reports 1 server-side skip (a candidate who became uncontactable since the last segment refresh). 23 successfully shortlisted.
8. Comes back to the researcher with the actual screener message that will go out: subject, body, sender, final recipient count (23). Asks explicitly: "Send this screener invitation to these 23 candidates? Yes or no."
9. Researcher says yes.
10. Sends the screener invitation to the 23 shortlisted candidates using the study's configured screener message.
11. Returns a summary: "Shortlisted 23 candidates (1 server-skipped for contactability). Invitations sent to 23. 25 candidates remain in the filtered pool. Link to participants page."
Time elapsed: a couple of minutes plus whatever the agent waits for the researcher's review. The value is consistency: the same recruitment rules applied every time, the same record of what was filtered and why.
## Changelog
- **0.2 (2026-06-10):** Made send approval an explicit, mandatory, separate step from shortlist approval. Even when the researcher's original request is "shortlist and send," the agent requests two distinct approvals at two distinct moments. Ambiguous answers ("looks good," "go ahead") are treated as requests for clarification, not as approval. The Confirmation subsection of Your rules was promoted from a buried bullet to a top-level commitment.
- **0.1 (2026-06-10):** Initial library template version. Covers the full recruitment workflow: discovery via segment / search / hand-curated list, org-rules filtering, oversampling, shortlist, send. Defers screener email authoring to the email-copy skill.

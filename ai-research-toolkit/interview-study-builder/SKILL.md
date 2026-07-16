---
name: interview-study-builder
description: Set up a complete moderated interview study in Great Question from a research brief — study, screener, moderators, scheduling, livestream, and incentive — in one orchestrated workflow, stopping just short of activation. Use when a researcher wants to launch a new interview study and has a brief or enough context to describe one. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.4
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Interview Study Builder
Take a researcher from "I have a brief" to "the study is ready to activate" in one orchestrated workflow. Handles study creation, screener, moderators, scheduling configuration, livestream, and incentive. The researcher activates the study in the GQ UI when they're ready to recruit.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which are the org-specific decisions you'll customize when you fork. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "create an interview study"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Naming
- **Study title format:** `{{title_format}}`
  <!-- Example: `[Team] | [Project] | Interviews | [Market] | [Segment]`. One title per segment. Don't combine markets or segments in a single study title. -->
### Incentive policy
- **Default incentive method:** `tremendous`
  <!-- GQ supports `manual` and `tremendous`. Use `tremendous` unless your org has a specific reason to handle incentives manually. -->
- **Currency by market:** `{{currency_by_market}}`
  <!-- For example: US gets USD, UK gets GBP, EU and other markets get EUR. Currency is set on the study and can only be changed while the study is in draft state. -->
- **Incentive amount:** `{{incentive_amount}}`
  <!-- A flat rate, a table by role and duration, or whatever your team uses. If you encode a table, keep it here rather than scattering it through the orchestration steps below. -->
- **No-incentive cases:** internal-employee studies, plus any study the researcher explicitly flags as no-incentive. When in doubt, ask the researcher rather than assuming.
### Duration and scheduling
- **Default session duration:** `{{default_duration_minutes}}` <!-- For example, 30. Max 60. -->
- **Meeting provider:** `{{meeting_provider}}` <!-- Options: `manual`, `zoom`, `google_meet`, `microsoft_teams`, `webex`, `in_person`. Pick the one your team uses by default. -->
- **Booking buffer:** `{{buffer_minutes}}` minutes between sessions <!-- A common starting point is 0 or 15. -->
- **Minimum notice:** `{{minimum_notice_minutes}}` minutes <!-- A common starting point is 120 (two hours). -->
- **Weekly hours:** `{{weekly_hours}}` <!-- For example, Monday to Friday, 09:00 to 17:00. Note: GQ requires the same start/end window across every listed day; you can omit days but you can't vary the times day-by-day. -->
### Screener policy
- **What's always on the screener:** `{{always_on_screener}}`
  <!-- The questions every screener for this study type must include. Many orgs put consent, incentive opt-in, and a screening-disclosure question here, in a fixed order. List yours; the agent will use this verbatim. -->
- **What to consider including:** `{{contextual_screener_questions}}`
  <!-- Questions the agent should add only when relevant to the study topic. List the pool; the agent will pick. -->
### Moderator defaults
- **Default observers:** `{{default_observers}}` <!-- For example, a shared recordings calendar. Always added regardless of study, unless explicitly disabled. -->
### Tone
- **Tone for participant-facing copy:** `{{tone_guidance}}` <!-- For example, "warm, professional, second-person, no jargon." -->
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
Gather, from the researcher or from a linked plan:
- Team, project, segments, markets
- Research goal in plain language
- Target sample size per segment
- Session duration, scheduling window, named moderators
- Whether the study needs an incentive (apply the rules in **Your rules**)
If anything required is missing, ask for it before proceeding. Group missing fields into a single message rather than asking one at a time.
### 2. Plan one study per segment
If the brief covers multiple segments, that's multiple studies, not one. Run steps 3 through 7 once per segment. Use the same moderator team across all segment studies unless the brief explicitly assigns different people per segment.
### 3. Create the study
Create an interview study with:
- Title applied from the **Your rules** title format
- Research goal: short noun phrase derived from the brief
- Duration: from the brief or the **Your rules** default
- Meeting provider: from the **Your rules** default
- Buffer and minimum notice: from the **Your rules** defaults
- Scheduling style derived from the moderator setup:
  - One moderator: one on one
  - One moderator plus one alternative: round robin, with availability-based assignment
  - Two or more main moderators: collective
Do not pass a screener payload at study-creation time. The screener gets created separately in step 5.
### 4. Set incentive and scheduling window
While the study is still in draft, update it with:
- Incentive method, currency, and amount, from **Your rules**
- Availability: booking window plus weekly hours from **Your rules**
Currency can only be set while the study is in draft state. Don't skip this step or you'll have to recreate the study to change it later.
### 5. Apply the screener
Create the screener separately from the study. Add the contextual questions from **Your rules** that are relevant to this study topic, then add the always-on questions in the order **Your rules** specifies.
If your screener uses skip logic, apply it in a second pass after the screener is created. Skip logic is not supported on the initial screener-creation call.
### 6. Add moderators and observers
List the moderators currently attached to the study first. The study creator is added automatically, so you don't need to add them again.
For each moderator named in the brief, add them by email.
Add the default observers from **Your rules**.
If a moderator can't be added (most often because they don't have a moderator-level seat in your account), continue without them and flag the issue in the final summary. Don't block the rest of the workflow.
### 7. Enable livestream
Enable livestream on the interview calendar settings for the study. Always enable this. The researcher can disable it in the GQ UI if they need to.
Don't send screener invitations from this skill. Sending invitations is the recruitment skill's job, not study setup. If the researcher asks the agent to send invitations as part of this workflow, hand them to the recruitment skill instead.
### 8. Hand back to the researcher
Don't activate the study. The MCP doesn't support activation deliberately. The researcher activates manually in the GQ UI when they're ready to recruit, which prevents the recruitment clock from starting before the study has been reviewed.
Send the researcher:
- A link to the new study (or studies, if multiple segments)
- A short checklist of anything they need to do before activating:
  - Review the screener and remove any contextual questions that aren't relevant for this study
  - Confirm scheduling timezone and availability
  - Activate when ready to recruit
- Any flags from step 6 (for example, moderators that couldn't be added)
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **Call ordering matters.** The study must be created before the screener is created. Incentive currency must be set while the study is in draft state. Skip logic must be applied after the screener exists, not at screener-creation time.
- **No screener inline at study creation.** Always create the screener as a separate step.
- **Weekly hours uses one window across all days.** GQ accepts a set of weekly days (Monday, Tuesday, etc.) and a single `start`/`end` time window that applies to every listed day. You can omit a day to mark it unavailable, but you can't set different times for different days. Sending different windows per day is rejected.
- **If a step fails after the study is created, stop the workflow.** Don't retry destructive operations silently and don't try to clean up. Summarize what was successfully created, what failed, and what state the study is in. Ask the researcher how to proceed. A half-built draft study is recoverable; a silently mangled one is not.
- **Activation is intentionally manual.** There is no MCP path to activate a study. The researcher always finishes the workflow in the GQ UI.
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
- **Read the brief from a research plan in your docs tool** before step 1, instead of asking the researcher to paste it in.
- **Post a launch notification to your team chat** after step 8.
- **Open a ticket** for any moderator that couldn't be added in step 6 (seat upgrade requested).
- **Cross-link the study back to your research plan** so the plan and the GQ study stay connected.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a brief along these lines:
> Set up an interview study for our product research team. We're talking to power users about a new dashboard feature. 30-minute sessions, standard incentive, Google Meet. Two moderators on the team, alice@example.com and ben@example.com. Scheduling window over the next three weeks.
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms the brief, asks for the research goal in plain language (the brief didn't include one), and confirms the always-on screener content from **Your rules** is current.
3. Plans one study (single segment in this brief; multiple if the brief had named more).
4. Creates the study with the title from **Your rules**, 30 minutes, Google Meet, round-robin scheduling because there are two moderators.
5. Sets the incentive in draft, plus the booking window for the next three weeks.
6. Creates the screener: contextual questions relevant to the dashboard topic, then the always-on questions from **Your rules**. Applies any skip logic in a second pass.
7. Adds both moderators by email, plus the default observers.
8. Enables livestream.
9. Returns the study link with a short checklist: review the screener for relevance, confirm the timezone, activate when ready.
Time elapsed: a couple of minutes plus whatever the agent waits for the researcher to clarify. The same setup by hand takes roughly 30 minutes with several places to mis-paste a value or forget a step.
## Changelog
- **0.4 (2026-06-10):** Added a failure-handling note to "Notes for the agent" so a mid-workflow failure produces a useful summary rather than a silently-mangled draft study.
- **0.3 (2026-06-10):** Removed Perk-specific screener tiering and screenerless-flow branching. Switched moderator-add to email-by-default. Cleared the meeting-provider default to a customer choice rather than Google Meet. Verified scheduling fields against the live MCP and added the weekly-hours one-window quirk. Renamed "Known fragile points" to "Notes for the agent." Trimmed redundant rules.
- **0.2 (2026-06-10):** Reworked to express tool use as intent rather than naming specific tools. Added an **Agent setup** section explaining the runtime resolution. Simplified the screener policy from three named tiers to "always on" plus "contextual." Generalized the worked example. Em dashes removed throughout.
- **0.1 (2026-06-10):** Initial library template version.

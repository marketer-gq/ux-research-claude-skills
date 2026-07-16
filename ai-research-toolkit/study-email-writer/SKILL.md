---
name: study-email-writer
description: Draft, revise, and review the participant-facing emails on a Great Question study — invitations, reminders, and post-session messages — with your team's voice, mandatory disclosures, and incentive-mention rules applied consistently. Use when writing or improving the emails participants receive; the skill never sends without confirmation. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.2
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Study Email Writer
Compose new email messages on a study, or refine existing ones, with your team's voice, mandatory disclosures, and incentive-mention rules applied consistently. Covers every email kind GQ supports, from initial invitations to post-session thanks. The researcher reviews and the agent doesn't send anything without confirmation.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which encode your org's voice, sign-offs, mandatory disclosures, and incentive-mention rules. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "fetch the account's default template for this message kind"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Voice and tone
- **Voice:** `{{voice_description}}`
  <!-- For example: "warm but professional, second-person, never breezy, never apologetic." The agent applies this to every message it drafts or revises. -->
- **Reading level:** `{{reading_level}}`
  <!-- For example: "8th grade. Short sentences, common words." -->
- **Sign-off:** `{{signoff}}`
  <!-- For example: "Thanks, the [Team] research team." Include the exact phrasing your emails end with. The agent uses this verbatim. -->
### Mandatory disclosures
- **Always include:** `{{mandatory_disclosures}}`
  <!-- The legal/compliance lines that must appear in every participant-facing email regardless of kind. For example: a GDPR consent reminder, a clause about how the participant can withdraw, a link to your privacy policy. List the exact wording. -->
- **Placement:** `{{disclosure_placement}}`
  <!-- For example: "Below the main message body, above the sign-off. Same paragraph break treatment in every email." Tells the agent where in the message these go. -->
### Incentive mentions
- **When to mention the incentive:** `{{incentive_mention_rule}}`
  <!-- For example: "Mention in invitation, booking confirmation, and post-session thanks. Don't mention in reminders or reschedule requests." -->
- **How to phrase it:** `{{incentive_phrasing}}`
  <!-- For example: "Refer to the incentive in plain terms. Don't editorialize about value. Never imply payment is contingent on saying what we want to hear." -->
- **When the study is no-incentive:** `{{no_incentive_handling}}`
  <!-- For example: "Don't mention payment. Don't apologize for not having one. Keep the tone friendly without compensating with extra warmth." -->
### Message templates
GQ supports account-level message templates per kind. When a template exists for a kind, every new message of that kind starts from it. This is the primary mechanism for getting consistent copy across studies without re-authoring every time.
- **Default behavior:** start every compose from the account template (or the system default if no account template exists). The skill applies your **Your rules** rules on top.
- **When the template is enough:** if the account template plus the **Your rules** rules already produces an acceptable message, the agent can compose it as-is without surfacing a draft. Surface a draft when the brief asks for study-specific content beyond what the template covers.
### Per-kind defaults
The 13 message kinds GQ supports split into two tiers. The agent applies the per-kind rules below to the primary tier. The secondary tier defers to the account or system template by default; the agent doesn't draft custom copy for these unless the researcher explicitly asks.
**Primary kinds** (researchers regularly customize these):
- **Invitation (`invite`):** `{{invitation_rules}}`
  <!-- For example: "Open with the study topic in one line. Mention duration and incentive. Link the booking page. No hard sell." -->
- **Screener email (`screener`):** `{{screener_rules}}`
  <!-- For example: "Make the screener time-cost explicit ('takes about 3 minutes'). Frame as 'help us understand if this study is the right fit.'" -->
- **Thanks message (`thanks`):** `{{thanks_rules}}`
  <!-- For example: "Short. Genuine. Mention the incentive timing if applicable." -->
- **Invited reminder (`invited_reminder`):** `{{invited_reminder_rules}}`
  <!-- For example: "Brief. Single call to action. Don't apologize for the reminder." -->
**Secondary kinds** (account or system template is usually sufficient):
- `booked` (booking confirmation)
- `booked_reminder` (reminder to attend the booked session)
- `started_reminder` (reminder to finish a started task or session)
- `reschedule_request`
- `cancel_interview`
- `cancel_task`
- `ad_hoc`
- `signed_consent_form`
- `welcome`
For secondary kinds, the agent compose from the account template, apply **Your rules** voice and mandatory-disclosure rules, and skip the per-kind custom drafting unless the researcher asks for it. If the researcher does ask for custom drafting on a secondary kind, treat it the same way as a primary kind for that one request: surface a draft, apply **Your rules**, get approval.
### Sender
- **Default sender:** the study owner. The agent doesn't override this unless the researcher explicitly asks.
### Safety
- **Never send without confirmation.** The agent drafts and revises freely. The researcher always confirms before any send happens.
- **Treat reschedule, cancellation, and ad-hoc messages with extra care.** These reach a participant who's already committed. Show the draft to the researcher and explicitly call out anything the researcher might want to soften.
## How this works with Great Question
<!--
GQ mechanics: plain-language steps describing how to drive Great Question
to accomplish the task. These steps name intents, not specific tool names.
The agent resolves intents to concrete tools at runtime using the MCP
server's own tool listing. Future state: this section migrates to a
GQ-owned playbook when that layer exists.
-->
The skill has two flows: composing a new message, or revising an existing one. The agent picks the right flow based on the researcher's request.
### 1. Understand the request
Gather, from the researcher:
- The study (by ID or by name).
- Which message kind they want to work on. Common kinds: invitation, screener, booking confirmation, thanks, reminder. Less common: reschedule, cancel, ad-hoc, consent-form-signed. If the researcher describes the goal rather than naming the kind ("I want to follow up with people who haven't booked yet"), map it to the right kind (`invited_reminder` in that example).
- Whether they're composing a new message or refining an existing one.
- Any specific points the message must include or avoid (study-specific content, audience-specific framing, etc.).
If the researcher is unclear which kind they need, list the relevant kinds with one-line descriptions and ask.
### 2. Compose flow
When the researcher wants a new message on a kind that doesn't exist yet:
1. **Fetch the account's default template for the kind.** This gives you the starting subject and body and ensures the message aligns with whatever the account has set up.
2. **Adapt the template** to the study and the brief, applying:
   - Voice, reading level, and sign-off from **Your rules**
   - The mandatory disclosures, placed per **Your rules**
   - The incentive mention rule for this kind, per **Your rules**
   - The per-kind defaults for this kind, per **Your rules**
3. **Show the draft to the researcher** before composing. Highlight the parts that came from the template versus the parts the agent wrote. Get explicit approval.
4. **Compose the message** with the approved subject, body, and the study owner as sender (unless the researcher specified a different sender).
### 3. Revise flow
When the researcher wants to update an existing message:
1. **List the messages on the study** to find the one to revise.
2. **Fetch the current message** and show it to the researcher alongside the proposed changes.
3. **Apply the changes** the researcher asks for, keeping the policy rules from **Your rules** intact unless the researcher explicitly overrides.
4. **Show the revised draft** before revising. Get explicit approval.
5. **Revise the message** in place.
### 4. Body format
Message bodies are stored as TipTap JSON, not plain text or HTML. The agent constructs the body as a TipTap document, not as a plain string. If you're starting from a template fetched in step 2.1 or 3.2, reuse the template's TipTap structure and modify nodes rather than rebuilding the document from scratch.
### 5. Send is never automatic
The agent composes and revises. The researcher sends, in the GQ UI. Don't claim a message has been sent; don't ask if the researcher wants it sent. Drafting is reversible; sending is not.
If the researcher explicitly asks "send this now," remind them that send happens in the GQ UI and offer to walk them to the right place rather than triggering anything automatically. (Today the MCP doesn't expose a send action for ad-hoc messages anyway. This is policy that survives if that changes.)
### 6. Hand back to the researcher
Send the researcher:
- The link to the study's messages in the GQ UI
- A short summary of what changed (composed or revised, which kinds, key edits)
- Any flags about the draft, e.g., "this reschedule message is friendlier than the standard tone you usually use; flagging in case you want it tighter."
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **Compose vs. revise are different operations.** Composing creates a new message on the study. Revising updates a message that already exists. Use the listing intent to check which exists before composing, to avoid creating duplicates.
- **Message body is TipTap JSON.** The body field expects a structured document, not plain text or markdown. Always fetch a template (or the existing message) first and modify its structure rather than constructing one from scratch.
- **The account-template fallback is system-level.** When you fetch a template for a kind, GQ returns the account's customization if one exists, otherwise the system default. The system default is a generic starting point; the account template usually reflects the org's voice. Either way, the customer's `{{voice_description}}` and other rules from **Your rules** override.
- **If a step fails after a draft is composed, stop the workflow.** Don't retry the compose, and don't try to clean up partial state. Summarize what was successfully drafted, what failed, and what state the message is in. Ask the researcher how to proceed.
- **Send is not an MCP action.** The agent never sends, even if asked. Sending happens in the GQ UI; that's a deliberate boundary, not a missing feature.
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
- **Pull approved boilerplate from a shared doc** (e.g., your team's standing copy patterns) before drafting in step 2.
- **Log a record of every drafted message** to a shared channel or tracker, so the team has a history of what's gone out and how it landed.
- **Cross-link the draft back to your project tracker** so messaging changes show up where the work lives.
- **Run drafts past a separate approval step** (e.g., legal review for ad-hoc messages) before showing the researcher.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a request like:
> Write the invitation email for our power-users dashboard study. Mention the $25 incentive and that the session is 30 minutes. The booking link is on the study page already; just point them to it.
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms the kind (`invite`), confirms the study, confirms the voice and incentive-mention rule from **Your rules**.
3. Fetches the account's default invite template for the message subject and body structure.
4. Adapts the template: applies the org voice, sets reading level, slots in the 30-minute and $25 details, applies the mandatory disclosures per **Your rules**, applies the org sign-off.
5. Shows the draft to the researcher with a note about which lines came from the template versus the agent's adaptation.
6. On approval, composes the message on the study with the agreed subject, body, and the study owner as sender.
7. Returns a link to the study's messages page and a short summary: "Drafted invite. Used the account template as a starting point. Highlighted the 30-min and $25 details per your brief. Sign-off and disclosure block applied per Your rules. Ready for you to send in GQ when you're ready."
Time elapsed: a couple of minutes plus whatever the agent waits for the researcher's review. The value is consistency: the same disclosures, the same voice, the same incentive phrasing across every study.
## Changelog
- **0.2 (2026-06-10):** Reframed per-kind defaults into a primary/secondary tier so the agent doesn't over-author. Secondary kinds default to the account or system template plus the **Your rules** rules. Removed the layout placeholder (not load-bearing for v1). Default sender simplified to "the study owner." Added an explicit **Message templates** subsection in **Your rules** describing the template-first default behavior.
- **0.1 (2026-06-10):** Initial library template version. Covers all 13 message kinds at the orchestration level; per-kind policy lives in **Your rules**. Two flows: compose new and revise existing. Send remains UI-only by design.

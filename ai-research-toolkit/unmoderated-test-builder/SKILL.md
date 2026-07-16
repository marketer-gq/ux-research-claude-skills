---
name: unmoderated-test-builder
description: Set up a complete unmoderated test in Great Question from a research brief — study, blocks, screener, and incentive — in one orchestrated workflow, stopping just short of activation. Use when launching a prototype test, website test, card sort, tree test, or survey-style task collection. Requires the Great Question MCP integration to be connected.
owner: Great Question
version: 0.1
last_reviewed: 2026-06-10
tested_against: MCP tools as of 2026-06-10
license: MIT
---

# Unmoderated Test Builder
Take a researcher from "I have a brief" to "the test is ready to activate" in one orchestrated workflow. Handles study creation, block authoring (the body of the test itself), screener, and incentive. The researcher activates the study in the GQ UI when they're ready to recruit.
## How to customize
This template ships with sensible defaults. Most of the value is in the `{{placeholders}}` in **Your rules**, which are the org-specific decisions you'll customize when you fork. The **How this works with Great Question** section is the orchestration logic; change it only when GQ's workflow itself changes, not as a way of expressing policy. The **External-system hooks** section is empty by default. Add your team's integrations there.
## Agent setup
Before executing this skill, list the available MCP tools on the Great Question server and identify the tools that map to each step in **How this works with Great Question**. The step descriptions name intents (for example, "create an unmoderated study," "add a block to the study"), not specific tool names. Use the MCP server's own tool descriptions to resolve each intent to a concrete tool call at runtime. If you can't resolve an intent to exactly one tool, ask the researcher rather than guessing.
## Your rules
<!--
Business policy: the org-specific decisions that should drive the agent's
behavior. Edit this section freely when you fork. Future state: this section
migrates to account config when that layer exists.
-->
### Naming
- **Study title format:** `{{title_format}}`
  <!-- Example: `[Team] | [Project] | Unmoderated | [Test type] | [Segment]`. One title per segment. Don't combine markets or segments in a single study title. -->
### Incentive policy
- **Default incentive method:** `{{default_incentive_method}}`
  <!-- GQ supports `manual`, `tremendous`, `coupon`, `product`, `other`, or no incentive. Pick the one your team uses by default. -->
- **Currency by market:** `{{currency_by_market}}`
  <!-- For example: US gets USD, UK gets GBP, EU and other markets get EUR. Currency is set on the study and can only be changed while the study is in draft state. -->
- **Incentive amount:** `{{incentive_amount}}`
  <!-- A flat rate, a table by test length, or whatever your team uses. If you encode a table, keep it here rather than scattering it through the orchestration steps below. -->
- **No-incentive cases:** internal-employee tests, plus any study the researcher explicitly flags as no-incentive. When in doubt, ask the researcher rather than assuming.
### Test composition
- **Default block sequence for a prototype test:** `{{prototype_test_blocks}}`
  <!-- For example: one warm-up text question, the prototype-test block itself, one or two reflection questions. Customers can encode their preferred opening/closing patterns here. -->
- **Default block sequence for a website test:** `{{website_test_blocks}}`
- **Default block sequence for a card sort:** `{{card_sort_blocks}}`
  <!-- Card sorts and tree tests usually want a short pre-task instruction block and a short post-task reflection question. -->
- **Default block sequence for a tree test:** `{{tree_test_blocks}}`
- **Block defaults:**
  - **Required by default:** all blocks are marked `required: true` unless the brief says otherwise. Flip per-block when needed.
  - **Randomization:** for card sorts, default to `randomise_cards: true` and `randomise_categories: false`. For tree tests, default to `randomise_tree_nodes: false`. Override per study when the brief calls for it.
### Participation
- **Default participation limit:** `{{participation_limit}}`
  <!-- Most unmoderated tests are capped. A common starting point is 20 or 50 depending on test type. -->
- **Default participant language:** `{{participant_language}}`
  <!-- One of: de, en, es, fr, it, pt-BR, tr. Defaults to en if not set. -->
- **Started grace period:** `{{started_grace_period_minutes}}`
  <!-- GQ default is 60 minutes for unmoderated. After this many minutes of inactivity, a "Started" participation reverts to "Invited" so the slot can be reused. -->
- **Consent form:** `{{default_consent_form_id}}`
  <!-- Your org's default consent form, if you have one. List available IDs via the consent-forms tools when you fork. -->
### Screener policy
- **What's always on the screener:** `{{always_on_screener}}`
  <!-- The questions every screener for this study type must include. Many orgs put consent, incentive opt-in, and a screening-disclosure question here, in a fixed order. List yours; the agent will use this verbatim. -->
- **What to consider including:** `{{contextual_screener_questions}}`
  <!-- Questions the agent should add only when relevant to the study topic. List the pool; the agent will pick. -->
### Tone
- **Tone for participant-facing copy:** `{{tone_guidance}}`
  <!-- For example, "warm, professional, second-person, no jargon." Applies to block titles, descriptions, and any participant-facing instructions the agent drafts. -->
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
- Test type (prototype test, website test, card sort, tree test, or a custom composition)
- Target sample size
- For prototype tests: the Figma prototype URL
- For website tests: the URL under test
- For card sorts: the cards and (if closed/hybrid) the categories
- For tree tests: the tree structure
- Whether the test needs an incentive (apply the rules in **Your rules**)
If anything required is missing, ask for it before proceeding. Group missing fields into a single message rather than asking one at a time.
### 2. Plan one study per segment
If the brief covers multiple segments, that's multiple studies, not one. Run steps 3 through 6 once per segment. Use the same block sequence and screener across all segment studies unless the brief explicitly varies them.
### 3. Create the study
Create an unmoderated study with:
- Title applied from the **Your rules** title format
- Research goal: short noun phrase derived from the brief
- Participation limit: from the **Your rules** default or the brief
- Language: from the **Your rules** default or the brief
- Grace period: from the **Your rules** default
- Consent form: from the **Your rules** default, if set
Do not pass a screener payload at study-creation time if the screener is large. The screener gets created separately in step 5.
Structural blocks (welcome, thank you, permissions, AI-moderated interview if applicable) are added by GQ automatically when the study is created. Don't try to create those yourself.
### 4. Set incentive
While the study is still in draft, update it with incentive method, currency, and amount from **Your rules**. Currency can only be set while the study is in draft state. Don't skip this step or you'll have to recreate the study to change it later.
For non-monetary incentives, set the `incentive_title` (e.g., the gift card name) and `incentive_instructions` (how the participant redeems it). For coupon incentives, supply the coupon codes.
### 5. Author the blocks
Add the content blocks that make up the body of the test, in the order from the relevant block sequence in **Your rules**. For each block:
- Set the `kind` based on the block's role (e.g., `prototype_test`, `card_sort`, `short_text`, `long_text`, `email`, `number`, `date`, `location`, `website`, `website_test`, `tree_test`).
- Set the title and description in the tone from **Your rules**.
- Apply the per-block defaults from **Your rules** (required, randomization, etc.).
- For type-specific fields, supply what the brief calls for:
  - Prototype test: the Figma URL.
  - Website test: the URL under test.
  - Card sort: cards, categories (if closed or hybrid), `sort_type`, randomization options, and whether all cards must be sorted.
  - Tree test: the tree structure with `selected: true` on correct-answer nodes.
If the brief has a non-default block ordering, reorder after creation rather than trying to insert in the right position the first time. The reorder step is cheap; getting position numbers right on insert is error-prone.
### 6. Apply the screener
Create the screener separately from the study. Add the contextual questions from **Your rules** that are relevant to this study topic, then add the always-on questions in the order **Your rules** specifies.
If your screener uses skip logic, apply it in a second pass after the screener is created. Skip logic is not supported on the initial screener-creation call.
### 7. Hand back to the researcher
Don't activate the study. The MCP doesn't support activation deliberately. The researcher activates manually in the GQ UI when they're ready to recruit, which prevents the recruitment clock from starting before the test has been reviewed.
Send the researcher:
- A link to the new study (or studies, if multiple segments)
- A short checklist of anything they need to do before activating:
  - Review the block sequence and confirm the order matches the test you intended
  - For prototype tests: confirm the screen graph fetched correctly (this happens asynchronously after block creation, so it may not appear immediately)
  - Review the screener and remove any contextual questions that aren't relevant for this test
  - Activate when ready to recruit
## Notes for the agent
<!--
Workflow constraints the agent can't discover from the tool schema alone.
Specific tool names are deliberately not listed here; the agent resolves
them at runtime. Edit this list when GQ changes a workflow constraint.
-->
- **Call ordering matters.** The study must be created before any blocks are added. Incentive currency must be set while the study is in draft state. Skip logic must be applied after the screener exists, not at screener-creation time.
- **Structural blocks are created by GQ.** Welcome, thank-you, permissions, and AI-moderated interview blocks come with the study automatically. Don't try to create them; only add content blocks (text, prototype test, website test, card sort, tree test, etc.).
- **Prototype-test screen graphs load asynchronously.** When you create a prototype-test block with a Figma URL, the response is returned before the screen graph is fetched from Figma. Screens and paths will not be present in the immediate response. The researcher should expect a short delay before the prototype is fully resolved in the GQ UI.
- **Reorder blocks rather than inserting at position.** Adding blocks in the desired order, or adding them in any order and then reordering with a single call, is more reliable than trying to insert each block at a specific position number on first add.
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
- **Pull card lists or tree structures from a shared spreadsheet** in step 1 or step 5, so designers don't have to retype them into the brief.
- **Post a launch notification to your team chat** after step 7.
- **Cross-link the study back to your research plan or design file** so the test and the source artifacts stay connected.
Each of these is your fork's responsibility, not the library template's.
## Example
A researcher pastes a brief along these lines:
> Set up a card sort to test our new navigation IA. Closed sort with the eight nav items as cards, and our six proposed top-level categories. 20 participants, $15 incentive, English. Randomize the card order.
The agent:
1. Resolves the MCP tool names against the live server (per the **Agent setup** section).
2. Confirms the brief, asks for the research goal in plain language (the brief didn't include one), and confirms the always-on screener content from **Your rules** is current.
3. Plans one study (single segment in this brief).
4. Creates the study with the title from **Your rules**, participation limit 20, English, the default grace period.
5. Sets the incentive in draft: tremendous, USD, $15.
6. Authors the blocks: a short pre-task instruction block, then the card-sort block with the eight cards, six categories, `sort_type: closed`, `randomise_cards: true`, `randomise_categories: false`, `require_all_sorted: true`. Then a short post-task reflection question.
7. Creates the screener: any contextual questions relevant to the navigation topic, then the always-on questions from **Your rules**. Applies any skip logic in a second pass.
8. Returns the study link with a short checklist: review the block sequence, review the screener, activate when ready.
Time elapsed: a couple of minutes plus whatever the agent waits for the researcher to clarify. The same setup by hand takes considerably longer, especially typing out the card list and category list correctly.
## Changelog
- **0.1 (2026-06-10):** Initial library template version. Covers all block kinds at the orchestration level (prototype test, website test, card sort, tree test, plus standard collectors). Customer encodes their default block sequences per test type in **Your rules**.

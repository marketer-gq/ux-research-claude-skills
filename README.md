# Claude skills for UX research

26 free Claude skills from [Great Question](https://www.greatquestion.com). We run research too, and we got tired of explaining the same method to Claude every time. So we wrote them down.

## Install

```bash
npx skills add marketer-gq/ux-research-claude-skills
```

That fetches all 26 and lets you pick which ones you want. For a single skill:

```bash
npx skills add marketer-gq/ux-research-claude-skills --skill affinity-mapper
```

Add `--global` to install them for every project rather than just the current directory.

Works in Claude Code, Claude Desktop, Cursor, Codex, Gemini CLI, GitHub Copilot, Zed and any other agent that reads the [Agent Skills](https://agentskills.io) format.

<details>
<summary>Installing without the CLI</summary>

**Claude Desktop** — open Settings → Capabilities → Skills and upload the `SKILL.md` from any skill folder.

**Claude Code** — copy the skill folder into your project's `.claude/skills/` directory.

**Cowork** — drop the skill folder into your skills directory.

</details>

## What's in here

### Works on files you supply

No account or integration needed. Hand these transcripts, notes or findings.

| Skill | What it does |
|---|---|
| [transcript-cleaner](ai-research-toolkit/transcript-cleaner) | Turns raw Otter, Fireflies, Zoom, Rev or Grain exports into analysis-ready transcripts, speakers resolved and timestamps kept |
| [research-brief-writer](ai-research-toolkit/research-brief-writer) | Turns a business question into a research brief, naming the method to run and the decision waiting on the result |
| [discussion-guide-builder](ai-research-toolkit/discussion-guide-builder) | Turns objectives into a semi-structured guide, every question traced to the objective it serves, leading ones rewritten |
| [jtbd-interview-guide](ai-research-toolkit/jtbd-interview-guide) | Writes a JTBD moderation guide around the Moesta timeline interview, including the probes that get people back to what happened |
| [screener-builder](ai-research-toolkit/screener-builder) | Turns a persona description into screener questions with qualifying logic, written so nobody can tell which answer gets them in |
| [survey-designer](ai-research-toolkit/survey-designer) | Turns a research goal into a survey you can actually analyse, with the reasoning for every question next to the question |
| [insight-tagger](ai-research-toolkit/insight-tagger) | Tags highlights against your codebook, holding a written definition for every code and flagging quotes it could not place |
| [jtbd-analyzer](ai-research-toolkit/jtbd-analyzer) | Codes transcripts against Jobs to be Done — the four forces and the moment someone switched, with the quote behind each |
| [affinity-mapper](ai-research-toolkit/affinity-mapper) | Clusters raw observations into themes bottom-up, then tells you which of those themes you should not trust yet |
| [research-synthesizer](ai-research-toolkit/research-synthesizer) | Reads across several studies at once and reports where they contradict, keeping study and participant on every claim |
| [synthetic-user-skill-public](ai-research-toolkit/synthetic-user-skill-public) | Builds reusable customer profiles from clusters of real interview evidence, every attribute cited to its session and every gap marked |
| [stakeholder-readout-generator](ai-research-toolkit/stakeholder-readout-generator) | Reframes findings for PMs, designers, leadership or a cross-functional audience |

> On **synthetic-user-skill-public**: these profiles are for piloting an instrument, generating hypotheses and stress-testing an artefact before you go to real people. They are not a substitute for participants and should not carry a decision on their own. Every attribute is cited to a real session and every gap is marked so you can see what the evidence does not cover.

### Checks your research

These check work that already exists rather than producing it: themes, reports, tasks, screeners, questionnaires, sessions and panel data. Each ships a stdlib-only Python script and runs on files you supply, with no account needed.

| Skill | What it does |
|---|---|
| [theme-quality-auditor](ai-research-toolkit/theme-quality-auditor) | Checks whether your synthesis themes are real findings or just topic labels, and asks a question to help you turn each label into a finding. |
| [evidence-integrity-auditor](ai-research-toolkit/evidence-integrity-auditor) | Checks a research report against its transcripts for quotes that can't be found, findings that rest on one person, and numbers that mislead. |
| [sample-size-planner](ai-research-toolkit/sample-size-planner) | Tells you how many participants your study needs, with the published source behind the number and a sentence you can paste into your plan. |
| [task-scenario-linter](ai-research-toolkit/task-scenario-linter) | Checks your usability test tasks for wording that gives the answer away, such as naming the button, before you run the test. |
| [moderator-scorecard](ai-research-toolkit/moderator-scorecard) | Shows you, from your own interview transcript, how much you talked, interrupted or led the participant, so you can get better at moderating. |
| [instrument-scorer](ai-research-toolkit/instrument-scorer) | Scores standard usability questionnaires like SUS correctly, compares them to the benchmark, and checks your questions still match the standard wording. |
| [screener-porter](ai-research-toolkit/screener-porter) | Checks a recruitment screener before launch and helps you copy it into another study or tool without losing which answers qualify people. Also runs through the Great Question MCP. |
| [panel-data-steward](ai-research-toolkit/panel-data-steward) | Finds messy participant data, like one job title stored four different ways, and proposes fixes that a person approves before anything changes. Also runs through the Great Question MCP. |

<details>
<summary>What each check does, in plain terms</summary>

**theme-quality-auditor**
- **The problem:** People label a synthesis theme "Onboarding" or "Pricing". That's a topic, not a finding. It says what people talked about, not what you learned from them.
- **You give it:** your list of themes from analysis, and your discussion guide if you have it.
- **It tells you:** which themes are just topic labels, and for each one a question to help you turn it into a real finding, like "People give up on setup before they see any value". It never rewrites a theme for you.
- **Use it:** before you share a synthesis or readout.

**evidence-integrity-auditor**
- **The problem:** A research report can contain quotes that were changed or can't be found, findings that rest on one person, or "40% of users" when only eight people took part.
- **You give it:** the report and the interview transcripts.
- **It tells you:** which quotes it can't find in the transcripts, which findings rest on too few people, which numbers are misleading, and whether each finding mentions anyone who disagreed. It doesn't accuse anyone of making things up. It flags things for a person to check.
- **Use it:** before a report goes to stakeholders, especially if AI helped write it.

**sample-size-planner**
- **The problem:** "How many people do I need?" usually gets answered with "five", and no reason for it.
- **You give it:** the kind of study you're running and how many user groups you're studying.
- **It tells you:** a recommended number or range, the published source behind it, and a sentence you can paste into your research plan. It can also tell you whether new interviews have stopped turning up new themes.
- **Use it:** when you're planning a study, or when a stakeholder asks "is that enough people?".

**task-scenario-linter**
- **The problem:** A usability task like "Click Reports to find last month's spend" gives the answer away by naming the button. You end up testing whether people can read, not whether they can find things.
- **You give it:** your usability tasks and a list of the product's menu and button names.
- **It tells you:** which tasks use the product's own words, give step-by-step instructions, contain words like "easy" or "simply", or have no clear point where the participant knows they're done.
- **Use it:** before you run a usability test.

**moderator-scorecard**
- **The problem:** Interviewers rarely find out how much they talk, interrupt or lead the participant.
- **You give it:** a transcript of an interview you ran.
- **It tells you:** how much of the session you talked compared with the participant, your longest speeches, any interruptions, and questions that pushed toward an answer.
- **Use it:** to review your own sessions and improve. It isn't for managers grading people.

**instrument-scorer**
- **The problem:** Standard usability questionnaires like SUS are easy to score wrongly, and if someone rewords a question the score can no longer be compared to the benchmark.
- **You give it:** the questionnaire responses.
- **It tells you:** the correct score, how it compares to the published benchmark, any responses that look inconsistent, and whether your questions still match the standard wording.
- **Use it:** whenever you run SUS, SEQ, UMUX-Lite or NASA-TLX.

**screener-porter**
- **The problem:** Copying a recruitment screener between studies or tools by hand loses its logic: which answers qualify someone, and where the answers get saved.
- **You give it:** a screener exported from any tool.
- **It tells you:** whether the screener has problems before you launch it, such as questions that are easy to guess or sensitive questions with no consent, plus a step-by-step plan to copy it into the new study or tool without losing anything.
- **Use it:** when you're reusing or moving a screener.

**panel-data-steward**
- **The problem:** Participant data gets messy. The same job title is stored as "Product Manager", "product manager", "PM" and "Product Mgr", so filtering on one misses most of the people and the panel looks smaller than it is.
- **You give it:** an export of your participant panel.
- **It tells you:** which fields are mostly empty, which are duplicates, and which values are different spellings of the same thing. It proposes fixes, and nothing changes until a person approves each one.
- **Use it:** when your panel seems too small, or as a regular clean-up.

</details>

### Works inside your Great Question account

These act on your real data — creating studies, recruiting, drafting participant comms, pulling findings. Anything that writes to your account confirms with you first.

> Requires the [Great Question MCP integration](https://www.greatquestion.com/features/mcp-integration) connected to your Claude environment.

| Skill | What it does |
|---|---|
| [interview-study-builder](ai-research-toolkit/interview-study-builder) | Builds a moderated interview study from a brief — study, screener, moderators, scheduling, livestream, incentive — stopping short of activation |
| [unmoderated-test-builder](ai-research-toolkit/unmoderated-test-builder) | Builds an unmoderated test from a brief — study, blocks, screener, incentive — for prototype tests, website tests, card sorts, tree tests and survey tasks |
| [candidate-recruiter](ai-research-toolkit/candidate-recruiter) | Screens your panel against the criteria on a study you have already built, then gets the people who qualify invited |
| [study-email-writer](ai-research-toolkit/study-email-writer) | Drafts the invitations, reminders and follow-ups a study needs, in your voice and with your disclosure rules |
| [stakeholder-readout-mcp](ai-research-toolkit/stakeholder-readout-mcp) | Builds a readout from finished studies in your repo, with the real session highlights behind every finding |
| [panel-hygiene-audit](ai-research-toolkit/panel-hygiene-audit) | Read-only audit of your panel for over-recruitment, thin segments and cooldown violations, plus who is doing most of the participating and how heavily each segment is used, with recommended remediation |

## How they chain

You don't need all 26 on a project. Start with the one that targets your biggest bottleneck.

**Planning** — research-brief-writer → discussion-guide-builder (or jtbd-interview-guide) → screener-builder (or survey-designer)

**Analysis** — transcript-cleaner → insight-tagger → affinity-mapper → research-synthesizer (or jtbd-analyzer)

**Checking** — task-scenario-linter and screener-porter before fielding · moderator-scorecard after a session · theme-quality-auditor and evidence-integrity-auditor before a readout · sample-size-planner when planning

**Communication** — stakeholder-readout-generator

**Running it in Great Question** — panel-hygiene-audit → candidate-recruiter → interview-study-builder *or* unmoderated-test-builder → study-email-writer → stakeholder-readout-mcp

## Customising them

Every skill is a markdown file. Open it, edit the instructions, save. If your team has its own templates, taxonomies or methods, adapt the skills to match. For the MCP skills most of the customisation lives in the `Your rules` section — study naming, default incentive, cooldown periods, tone and disclosures.

## Built by Great Question

These complement Great Question's built-in AI research features. If you already use Great Question, a lot of this is native to the platform — these skills extend it to data from outside sources and into the rest of your AI workflow.

Browse the library at [greatquestion.com/resources/claude-skills-library](https://www.greatquestion.com/resources/claude-skills-library).

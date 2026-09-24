# Claude skills for UX research

18 free Claude skills from [Great Question](https://www.greatquestion.com). We run research too, and we got tired of explaining the same method to Claude every time. So we wrote them down.

## Install

```bash
npx skills add marketer-gq/ux-research-claude-skills
```

That fetches all 18 and lets you pick which ones you want. For a single skill:

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

You don't need all 18 on a project. Start with the one that targets your biggest bottleneck.

**Planning** — research-brief-writer → discussion-guide-builder (or jtbd-interview-guide) → screener-builder (or survey-designer)

**Analysis** — transcript-cleaner → insight-tagger → affinity-mapper → research-synthesizer (or jtbd-analyzer)

**Communication** — stakeholder-readout-generator

**Running it in Great Question** — panel-hygiene-audit → candidate-recruiter → interview-study-builder *or* unmoderated-test-builder → study-email-writer → stakeholder-readout-mcp

## Customising them

Every skill is a markdown file. Open it, edit the instructions, save. If your team has its own templates, taxonomies or methods, adapt the skills to match. For the MCP skills most of the customisation lives in the `Your rules` section — study naming, default incentive, cooldown periods, tone and disclosures.

## Built by Great Question

These complement Great Question's built-in AI research features. If you already use Great Question, a lot of this is native to the platform — these skills extend it to data from outside sources and into the rest of your AI workflow.

Browse the library at [greatquestion.com/resources/claude-skills-library](https://www.greatquestion.com/resources/claude-skills-library).

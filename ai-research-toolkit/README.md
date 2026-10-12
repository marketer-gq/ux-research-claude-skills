# AI Research Toolkit

26 Claude skills that turn AI into your UX research assistant.

```bash
npx skills add marketer-gq/ux-research-claude-skills
```

## What's Inside

### File-based skills

These process transcripts, notes, and findings you hand them. No account or integration required.

| Skill | What It Does |
|-------|-------------|
| **transcript-cleaner** | Cleans raw transcripts from Otter, Fireflies, Zoom, Rev, or Grain into analysis-ready documents |
| **research-synthesizer** | Finds patterns, themes, and contradictions across multiple transcripts or notes |
| **discussion-guide-builder** | Generates semi-structured interview guides with warm-up, probes, and timing |
| **insight-tagger** | Tags research highlights with themes, sentiment, and cross-references |
| **stakeholder-readout-generator** | Reframes findings for PMs, designers, leadership, or cross-functional teams |
| **screener-builder** | Creates screening surveys with qualification logic, scoring, and attention checks |
| **affinity-mapper** | Groups observations into meaningful clusters with named themes and relationships |
| **research-brief-writer** | Translates business questions into complete research plans with methodology recommendations |
| **survey-designer** | Designs research-quality surveys with validated questions, response options, and strategic rationale |
| **jtbd-interview-guide** | Generates a JTBD moderation guide using the Bob Moesta timeline interview method |
| **jtbd-analyzer** | Extracts Jobs-to-Be-Done insights from transcripts — four forces, switching triggers, struggling moments |
| **synthetic-user-skill-public** | Builds reusable customer profiles from clusters of real interview evidence, every attribute cited to its session and every gap marked |

> **On synthetic users.** These profiles are for piloting an instrument, generating hypotheses and stress-testing an artefact before you go to real people. They are not a substitute for participants and should not carry a decision on their own. Every attribute is cited to a real session and every gap is marked so you can see what the evidence does not cover.

### Research quality checks

These check existing work rather than producing it. Each ships a stdlib-only Python script with tests (`python3 -m unittest discover` inside the skill folder). No account or integration required.

| Skill | What It Does |
|-------|-------------|
| **theme-quality-auditor** | Checks whether your themes are themes or topic labels, then asks the question that gets each one to a claim. It never rewrites a theme |
| **evidence-integrity-auditor** | Checks a report against its transcripts: quotes that can't be found, findings resting on one participant, percentages at small n, and findings that never say whether anyone disagreed |
| **sample-size-planner** | Gives a sourced starting range for interviews and focus groups, checks saturation, and works out sample sizes and intervals for usability and survey studies |
| **task-scenario-linter** | Flags usability tasks that use the product's own labels, give instructions, prime the participant or have no clear end point |
| **moderator-scorecard** | Measures a session from its transcript (talk-time share, monologues, interruptions, leading questions) for your own self-review, not for performance evaluation |
| **instrument-scorer** | Scores SUS, UMUX-Lite, SEQ and NASA-TLX correctly, flags possible inconsistent answers, and checks the wording is still the standard version |
| **screener-porter** | Converts a screener between tools, checks it before launch, and plans the import, with attribute mappings kept. Also runs through the Great Question MCP |
| **panel-data-steward** | Finds duplicate and sparsely filled panel attributes and merges variant spellings, proposing every change for approval first. Also runs through the Great Question MCP |

### Great Question MCP skills

These act directly inside your Great Question account — creating studies, recruiting participants, drafting study emails, and pulling findings. They're forkable templates: edit the `Your rules` section in each `SKILL.md` to match how your team works. Anything that writes to your account confirms with you before it sends, recruits, or changes something.

> **Require the [Great Question MCP integration](https://www.greatquestion.com/features/mcp-integration).** These skills only work when the MCP is connected to your Claude environment.

| Skill | What It Does |
|-------|-------------|
| **interview-study-builder** | Builds a complete moderated interview study from a brief — study, screener, moderators, scheduling, livestream, incentive — up to activation |
| **unmoderated-test-builder** | Builds a complete unmoderated test from a brief — study, blocks, screener, incentive — for prototype tests, website tests, card sorts, tree tests, and survey tasks |
| **study-email-writer** | Drafts and refines the participant-facing emails on a study with your voice, disclosures, and incentive rules; never sends without confirmation |
| **candidate-recruiter** | Finds, filters, and shortlists candidates and sends screener invitations, applying your recruitment rules; confirms before sending |
| **stakeholder-readout-mcp** | Pulls findings, highlights, and quotes from one or more studies and drafts a stakeholder readout in your team's format |
| **panel-hygiene-audit** | Read-only audit of your candidate panel for over-recruitment, thin segments, and cooldown violations, plus participation and per-segment utilisation, with recommended remediation |

## How to Install

### Command line (recommended)

```bash
npx skills add marketer-gq/ux-research-claude-skills
```

Pick the skills you want from the list. For one skill:

```bash
npx skills add marketer-gq/ux-research-claude-skills --skill affinity-mapper
```

Add `--global` to install for every project rather than the current directory. This works in Claude Code, Cursor, Codex, Gemini CLI, GitHub Copilot, Zed and any other agent that reads the [Agent Skills](https://agentskills.io) format.

### Claude Desktop
1. Open **Settings → Capabilities → Skills**
2. Upload the SKILL.md file from any skill folder
3. Done — Claude will use the skill automatically when relevant

### Claude Code (manual)
1. Copy the skill folder into your project's `.claude/skills/` directory
2. Claude reads it automatically when handling related tasks

### Cowork
1. Drop the skill folder into your skills directory
2. Available immediately

> For the **Great Question MCP skills**, also connect the [Great Question MCP integration](https://www.greatquestion.com/features/mcp-integration) in your Claude environment — the skills call it to do their work.

## Recommended Workflow

These skills chain together across a full research project.

**Planning:** research-brief-writer → discussion-guide-builder (or jtbd-interview-guide) → screener-builder (or survey-designer)

**Analysis:** transcript-cleaner → insight-tagger → affinity-mapper → research-synthesizer (or jtbd-analyzer)

**Checking:** task-scenario-linter and screener-porter before fielding · moderator-scorecard after a session · theme-quality-auditor and evidence-integrity-auditor before a readout · sample-size-planner when planning

**Communication:** stakeholder-readout-generator

**Run it in Great Question (requires the MCP):** panel-hygiene-audit → candidate-recruiter → interview-study-builder *or* unmoderated-test-builder → study-email-writer → stakeholder-readout-mcp

You don't need all 26 on every project. Start with the one that targets your biggest bottleneck.

## Customization

Every skill is just a markdown file. Open it, edit the instructions, save. If your team has specific templates, taxonomies, or methodologies, adapt the skills to match. For the MCP skills, most of the customization lives in the `Your rules` section — study naming, default incentive, cooldown periods, tone, and disclosures.

## Built by Great Question

These skills complement Great Question's built-in AI research features. If you're using Great Question, many of these capabilities are already native to the platform. These skills extend that functionality to data from external sources and into your broader AI workflow.

Learn more at [greatquestion.com](https://www.greatquestion.com)

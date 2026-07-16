# AI Research Toolkit

17 Claude skills that turn AI into your UX research assistant.

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

### Great Question MCP skills

These act directly inside your Great Question account — creating studies, recruiting participants, drafting study emails, and pulling findings. They're forkable templates: edit the `Your rules` section in each `SKILL.md` to match how your team works. Anything that writes to your account confirms with you before it sends, recruits, or changes something.

> **Require the [Great Question MCP integration](https://greatquestion.co/features/mcp-integration).** These skills only work when the MCP is connected to your Claude environment.

| Skill | What It Does |
|-------|-------------|
| **interview-study-builder** | Builds a complete moderated interview study from a brief — study, screener, moderators, scheduling, livestream, incentive — up to activation |
| **unmoderated-test-builder** | Builds a complete unmoderated test from a brief — study, blocks, screener, incentive — for prototype tests, website tests, card sorts, tree tests, and survey tasks |
| **study-email-writer** | Drafts and refines the participant-facing emails on a study with your voice, disclosures, and incentive rules; never sends without confirmation |
| **candidate-recruiter** | Finds, filters, and shortlists candidates and sends screener invitations, applying your recruitment rules; confirms before sending |
| **stakeholder-readout-mcp** | Pulls findings, highlights, and quotes from one or more studies and drafts a stakeholder readout in your team's format |
| **panel-hygiene-audit** | Read-only audit of your candidate panel for over-recruitment, thin segments, and cooldown violations, with recommended remediation |

## How to Install

### Claude Desktop
1. Open **Settings → Capabilities → Skills**
2. Upload the SKILL.md file from any skill folder
3. Done — Claude will use the skill automatically when relevant

### Claude Code
1. Copy the skill folder into your project's `.claude/skills/` directory
2. Claude reads it automatically when handling related tasks

### Cowork
1. Drop the skill folder into your skills directory
2. Available immediately

> For the **Great Question MCP skills**, also connect the [Great Question MCP integration](https://greatquestion.co/features/mcp-integration) in your Claude environment — the skills call it to do their work.

## Recommended Workflow

These skills chain together across a full research project.

**Planning:** research-brief-writer → discussion-guide-builder (or jtbd-interview-guide) → screener-builder (or survey-designer)

**Analysis:** transcript-cleaner → insight-tagger → affinity-mapper → research-synthesizer (or jtbd-analyzer)

**Communication:** stakeholder-readout-generator

**Run it in Great Question (requires the MCP):** panel-hygiene-audit → candidate-recruiter → interview-study-builder *or* unmoderated-test-builder → study-email-writer → stakeholder-readout-mcp

You don't need all 17 on every project. Start with the one that targets your biggest bottleneck.

## Customization

Every skill is just a markdown file. Open it, edit the instructions, save. If your team has specific templates, taxonomies, or methodologies, adapt the skills to match. For the MCP skills, most of the customization lives in the `Your rules` section — study naming, default incentive, cooldown periods, tone, and disclosures.

## Built by Great Question

These skills complement Great Question's built-in AI research features. If you're using Great Question, many of these capabilities are already native to the platform. These skills extend that functionality to data from external sources and into your broader AI workflow.

Learn more at [greatquestion.co](https://greatquestion.co)

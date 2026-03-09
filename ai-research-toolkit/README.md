# AI Research Toolkit

8 Claude skills that turn AI into your UX research assistant.

## What's Inside

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

## Recommended Workflow

These skills chain together across a full research project:

**Planning:** research-brief-writer → discussion-guide-builder → screener-builder

**Analysis:** transcript-cleaner → insight-tagger → affinity-mapper → research-synthesizer

**Communication:** stakeholder-readout-generator

You don't need all 8 on every project. Start with the one that targets your biggest bottleneck.

## Customization

Every skill is just a markdown file. Open it, edit the instructions, save. If your team has specific templates, taxonomies, or methodologies, adapt the skills to match.

## Built by Great Question

These skills complement Great Question's built-in AI research features. If you're using Great Question, many of these capabilities are already native to the platform. These skills extend that functionality to data from external sources.

Learn more at [greatquestion.co](https://greatquestion.co)

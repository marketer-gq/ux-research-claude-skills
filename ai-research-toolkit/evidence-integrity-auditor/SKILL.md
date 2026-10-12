---
name: evidence-integrity-auditor
description: Audit a research report, findings list or synthesis against its own evidence — locating every quote in the source transcripts, measuring whether one participant is carrying the findings, and flagging claims, percentages and recommendations with nothing behind them. Use before a readout goes to stakeholders, or when reviewing a synthesis an AI tool produced. Audits an existing draft; it does not write findings.
---

# Evidence Integrity Auditor

Most research tooling generates findings. Almost none checks them.

This skill is the check. Point it at a report and its source transcripts and it answers five questions a reader cannot answer by eye:

1. **Can every quote be found in the sources?** Mehta et al. (2025, *Scientific Reports* 15:34993, https://doi.org/10.1038/s41598-025-18969-w) found GPT-4o's quote selection was low and variable in accuracy, with altered, truncated and merged quotes. A quote that reads well looks the same whether it was copied, tidied or changed.
2. **How many voices are really behind this?** A report citing eight participants can be carried by two. Concentration is invisible in prose and obvious in a count.
3. **Is each claim attached to evidence?** Unhedged generalisations — "users always", "everyone wants" — with no quote nearby.
4. **Is each number in a form the sample supports?** "40% of participants" at n=8 implies a precision eight people cannot carry. "3 of 8" says the same thing honestly.
5. **Does each finding say whether anyone disagreed?** A finding that never mentions a contradicting participant may not have looked for one.

It works on any report, whoever or whatever wrote it. Running it on your own drafts is the point; running it on an AI-generated synthesis is where it earns its keep.

## Goal

Before a report reaches stakeholders, every quote can be traced to a source, every finding rests on evidence that can carry it, and every number is stated in a form the sample supports. Real problems are caught without accusing the researcher of errors they didn't make.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You review reports the way a careful research lead would before they go to stakeholders: protective of the evidence, and fair to the researcher who wrote it.

- Assume good faith. Light editing of quotes is standard practice. A quote you can't locate is a question about a missing transcript, a translation or an edit, never an accusation.
- Judge each finding by whether the evidence carries it: how many participants, how varied, and whether anyone disagreed.
- Prefer counts over percentages at small n, and say why in one line a stakeholder would accept.
- Rank what you report. Lead with what could mislead a decision; leave cosmetic issues for last.

## Quick start

```bash
# Structure only — concentration, claims, numbers, recommendations, disagreement
python scripts/audit_evidence.py report.md --n 8

# With sources, which adds quote verification
python scripts/audit_evidence.py report.md --sources transcripts/ --n 8

# Treat any edit to a quote, however light, as "altered"
python scripts/audit_evidence.py report.md --sources transcripts/ --verbatim strict

# Machine-readable output as well
python scripts/audit_evidence.py report.md --sources transcripts/ --n 8 --json findings.json
```

Exit code is 1 when there is a critical finding, so it can gate a publish step.

## What it needs

**The report** as markdown or plain text. Quotes are found in blockquotes (`> ...`) and in double-quoted strings of 40 characters or more. Quotes under 40 characters (a working default, not from the literature) are treated as phrases and are not checked against the sources. Attribution is read from `— P3`, `(P3)`, `[P3]`, `— Participant 3` and the same forms with an en dash or hyphen. It is stripped from the quote before matching and recorded as the attribution.

**The sources**, optionally: a directory of transcripts (`.txt`, `.md`, `.vtt`, `.srt`, `.json`), a single file, or a JSON object of `{"session name": "text"}`. WebVTT and SRT files have their cue numbers, timestamps and `<v Name>` tags removed and their cues joined, so a quote that runs across two cues is still found. If the report itself sits inside the sources folder it is skipped with a warning; otherwise every quote would verify against itself. Without sources the audit still runs, but quote verification is skipped, and that is the most valuable check, so supply them whenever they exist.

**The participant count** via `--n`, optionally. It enables two checks that cannot run without it: how many participants are never quoted, and whether a percentage is being reported at an n too small to support it. It also decides whether a concentration finding is critical.

**The verbatim standard** via `--verbatim`, optionally. `intelligent` (the default) accepts light edits — filler words removed, an ellipsis, a `[bracketed]` clarification — as verified, with a note. `strict` treats any edit as altered. Light editing is standard practice in qualitative reporting (Corden & Sainsbury 2006, https://www.york.ac.uk/inst/spru/pubs/pdf/verb.pdf), so use `strict` only when your team has agreed to quote word for word.

## Reading the output

Findings come in three severities.

**Critical** — a quote with nothing close to it in any source, or one participant supplying more than 40% of attributed quotes in a study of five or more (both working defaults). Resolve these before the report goes out.

**Warning** — quotes that differ from the source or could not be located, unattributed quotes, participants never quoted, findings that never mention disagreement, unhedged generalisations, percentages at small n, recommendations with nothing attached.

**Note** — quotes verified with light edits, concentration in a study of under five, percentages with no stated n, and a participant quoted under several themes. None is wrong on its own. The cross-theme note is where contradictory use of one voice shows up, and the only way to see it is the matrix.

The quotes-per-participant bar chart at the end is often the finding people react to most. A report that felt broad turns out to rest on two people.

## What the checks mean

### Quote verification

Before matching, the attribution is stripped, case, punctuation and curly quotes are folded, filler words (um, uh, er, like, you know) are dropped from both the quote and the source, `[sic]` is removed, and the quote is split at each `...` or `[bracketed insertion]` so each part is matched on its own. Each part is located with a word n-gram search and scored against the best-aligned window of the source.

| Match | Status | Severity |
|---|---|---|
| 97% or more | verified (a note if it was lightly edited; altered under `--verbatim strict`) | — |
| 70–97% | altered: present but changed, often a paraphrase | warning |
| 50–70% | not located: "Check for an edit, a translation, or a missing transcript" | warning |
| under 50% | absent: nothing close in any source | critical |

All four bands are working defaults, not from the literature. They were set so that lightly cleaned quotes verify and a paraphrase lands in "altered" on a synthetic 10,000-word test transcript; see `tests/`. Ellipsis parts found out of order or more than 250 words apart (also a working default) are marked altered, because that is what a merged quote looks like.

A quote the audit cannot find is not proof it was made up. Translations, a transcript missing from the folder and heavy tidying all look the same to a string match. The finding tells you where to look.

### Concentration

Attributed quotes are counted per participant. Over 40% from one person is flagged: critical when the study has five or more participants, a note below that, where one voice dominating is hard to avoid. Both numbers are working defaults, not from the literature. The finding asks you to check whether quote selection reflects the evidence base, because articulate participants are often over-quoted. With `--n`, participants who never appear are counted — a report drawing on two voices while presenting itself as the view of eight is the most common way a small study overstates itself.

### Claim linkage

Sentences making a claim about users with no quote within three lines, and using unhedged language — "users always", "everyone", "nobody", "all users" — are flagged. The three-line window is a working default, not from the literature. Hedged claims are left alone. This check is deliberately narrow: it catches the sentences that assert most and evidence least, rather than trying to grade every sentence.

### Small-sample numbers

Raw counts like "3 of 8" are never flagged. Counts are how small qualitative studies should report numbers (NN/g and Maxwell; https://www.nngroup.com/videos/numbers-small-ux-studies/). A percentage is flagged as a warning when its n is under 10 (a working default, not from the literature), with the count to use instead. The n comes from an `x of y` in the same sentence, or from `--n`. With no n at all, the percentage gets a note. Dates such as `12/03/2026` and `24/7` are not read as fractions.

Intervals are optional and only mean something for a random sample. A sentence that already gives one is left alone. If you need one, the `sample-size-planner` skill computes it.

### Recommendation basis

Sentences containing recommendation language with no quote within five lines (a working default) and no citation of a participant or finding. "See appendix" does not count as a citation. A recommendation is where research turns into a decision, and it is the last place an unsupported claim should survive.

### Disconfirming evidence

Every heading that cites quotes is checked for language reporting disagreement: a participant who contradicted it, an exception, a negative case. If there is none, it is a warning asking whether anyone contradicted the finding. This is Lincoln & Guba's negative case analysis. It is the check that catches one participant being used to support two contradictory findings: a researcher asked "did anyone disagree?" goes back to the transcripts and finds them. Stating that no participant contradicted the finding clears the warning.

## Limitations, stated plainly

- **Attribution formats it does not recognise will read as unattributed.** If your team writes `(Sarah, PM at Acme)` rather than `(P3)`, add the pattern to `ATTRIBUTION_PATTERNS` and `TRAILING_ATTRIBUTION` in the script.
- **A quote attributed to the wrong participant will still verify.** The check is that the words exist in the corpus, not that they came from the person named. Check speaker labels in the transcripts yourself, or optionally with the `transcript-cleaner` skill.
- **Short quotes are not checked.** Quotes under 40 characters are skipped by verification.
- **The match bands overlap at the edges.** A heavy paraphrase and an invented quote built from the participant's own phrases can both land at 50–70%. That is why that band is a warning, not a critical.
- **The disconfirming-evidence check reads words, not meaning.** It clears when a heading mentions a contradiction, an exception or a negative case. It cannot tell whether that mention is adequate.
- **It cannot tell you a theme is wrong.** It can tell you the theme rests on one person. Whether a theme is a theme at all — or a topic summary — is the `theme-quality-auditor` skill.
- **Claim linkage is proximity-based.** A claim evidenced by a quote six lines away reads as unsupported. Tighten the layout or accept the false positive; do not loosen the threshold until the check reports nothing.
- **It does not read tables.** Lines beginning with `|` are skipped, so numbers reported only in a table are not checked.

## Workflow

1. Check speaker labels in the transcripts first. The `transcript-cleaner` skill can help but is optional. Verification against a mis-attributed transcript verifies the wrong thing.
2. Run the audit on the draft with sources.
3. Fix the criticals. For a quote that cannot be found, look for the transcript, the translation or the original wording, then replace it with the real one — not a paraphrase made defensible.
4. Re-run. Confirm nothing is left absent or not located, rather than fewer.
5. For concentration findings, the fix is usually not more quotes from the same person. Either bring in the quieter participants or narrow what the report claims.
6. Run it once more before the readout goes out.

## Example

A readout drawing on eight interviews, audited against the transcripts (this is `tests/fixtures/example/`, run with `--n 8`):

```
Evidence integrity audit: readout.md
============================================================
4 quotes (4 attributed) from 2 participants across 5 headings
Study n given as 8
Checked against sources (intelligent verbatim): 4 checked, 3 verified, 0 altered, 0 not located, 1 absent

CRITICAL (2)
  - (quote-verification) [line 11] Not located in sources (best match 42%), and nothing close was found. Check for a translation or a missing transcript: "The approval timeout is the single biggest blocker to my whole workflow and nobody will ow"
  - (concentration) P3 supplies 3 of 4 attributed quotes (75%). Check whether quote selection reflects the evidence base. Articulate participants are often over-quoted.

WARNING (6)
  - (concentration) 6 of 8 participants are never quoted. Findings drawn from 2 voices are being presented as findings from 8.
  - (disconfirming-evidence) [line 5] "Approval timeouts" cites 2 quote(s) and never says whether any participant contradicted it. Say who disagreed, or state that no one did (negative case analysis).
  - (disconfirming-evidence) [line 11] "Visibility" cites 2 quote(s) and never says whether any participant contradicted it. Say who disagreed, or state that no one did (negative case analysis).
  - (claim-linkage) [line 19] Unhedged generalisation with no quote within three lines: "Everyone wants this to be faster."
  - (small-sample) [line 15] Percentage at n=8: report as a count ("3 of 8"), not a percentage: "40% of participants mentioned visibility as their top issue."
  - (recommendation-basis) [line 25] Recommendation with no finding or quote attached: "We should rebuild the approval screen as a single page."

NOTE (2)
  - (quote-verification) [line 13] Verified with light edits (filler words removed), accepted under intelligent verbatim. Use --verbatim strict to treat these as altered: "So the thing is, we never really trusted the numbers on the shared dashboard because nobod"
  - (cross-theme) P3 is quoted under 2 different themes (Approval timeouts, Visibility). Check the quotes are not being used to support conclusions that contradict each other.

QUOTES PER PARTICIPANT
  P3         3  ######################         75%
  P7         1  ########                       25%
```

The report reads as the considered view of eight people. It is two people, one quote nobody can find, a percentage eight people cannot support, and two findings that never say whether anyone disagreed.

That is the gap this skill exists to close.

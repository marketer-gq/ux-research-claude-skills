---
name: instrument-scorer
description: Score SUS, UMUX-Lite, SEQ and NASA-TLX with the published formulas, grade curves and intervals, and validate that the questionnaire wording and scale still match the canonical instrument. Use when scoring a standardised usability questionnaire, checking a score someone else reported, or before fielding a SUS that has been reworded. Scores validated instruments; it does not design custom survey questions.
---

# Standardised-Instrument Scorer

Standardised instruments are valuable because the benchmark travels. A SUS score means something because many studies scored the same ten items the same way.

Two things break that, and both are common.

**Miscoding.** Sauro & Lewis reviewed 27 SUS datasets and found 3 of them miscoded by the researchers. The reversal rule for even-numbered items is easy to apply to the wrong items, or to forget entirely, and the resulting score looks perfectly plausible.

**Silent alteration.** Reword an item and the score no longer compares to the 68 benchmark or the grade curve (both Sauro & Lewis). Nothing warns you. The number still comes out between 0 and 100.

This skill does the arithmetic and checks the instrument is still the instrument.

## Goal

Each standardised score is computed correctly from an unaltered instrument and reported with its benchmark and uncertainty, so the team can trust it and compare it with other studies.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You use standardised questionnaires alongside qualitative work, and you know what their numbers can and can't tell a team.

- Score correctly first, then interpret. Put the score next to its benchmark and its interval, and say what the interval means at this sample size.
- Treat inconsistent responses as something to look at, not something to delete. Explain what you'd check and why.
- Pair the number with the qualitative evidence. A low score is a reason to look at what participants said and did, not a finding on its own.
- Be plain about limits: small samples, altered wording, and comparisons that don't hold.

## Quick start

```bash
# Score a SUS from a CSV of responses
python scripts/score_instrument.py sus responses.csv --per-respondent

# All-positive SUS, or a SUS with one item dropped
python scripts/score_instrument.py sus responses.csv --positive
python scripts/score_instrument.py sus responses.csv --drop-item 4

# Check the questionnaire is still canonical before you field it
python scripts/score_instrument.py validate my_sus.txt --instrument sus --points 5

# Other instruments
python scripts/score_instrument.py umux-lite responses.csv
python scripts/score_instrument.py seq seq.csv
python scripts/score_instrument.py tlx tlx.csv
```

Responses are a CSV or JSON with one row per respondent and one column per item, in item order. A header row is detected and skipped, including one that just numbers the columns. A first row that starts with a participant ID is treated as data. Columns or JSON keys named like an ID (`id`, `participant`, `respondent`, `email` and so on) are ignored. For NASA-TLX, subscale columns are matched by header name when the header names them, so column order doesn't matter.

A row with the wrong number of items stops the run rather than being scored — a short row is the most common cause of a miscoded mean.

Exit codes: 0 means clean, 1 means there are findings to review (possible inconsistencies, altered wording), 2 means a fatal input error (missing file, wrong item count, out-of-range value).

## SUS

**Formula.** Odd items score `response − 1`, even items score `5 − response`, summed and multiplied by 2.5. The script prints this next to every score so the arithmetic is auditable.

**All-positive SUS (`--positive`).** Sauro & Lewis (2011) published a version with every item worded positively, and Kortum et al. (2020, https://pubmed.ncbi.nlm.nih.gov/31913715/) assessed it further. Every item scores `response − 1`, summed and multiplied by 2.5. Use this flag only if that is the version you fielded.

**One item dropped (`--drop-item N`).** Lewis & Sauro (2017) show SUS still works with one item left out, as long as the nine-item sum is rescaled: multiply by 100/36 instead of 2.5. The file then has nine columns. Say in the report which item you dropped.

**Output.** Mean, 95% t-interval (df = n − 1, clamped to 0–100), the Sauro–Lewis grade of the mean with its percentile band, and the difference from the 68 benchmark. `--per-respondent` adds the individual scores. It does not grade individuals: the grade curve describes study means, not single respondents.

**Possible inconsistencies.** Sauro & Lewis report two separate problems: 3 of 27 SUS datasets were miscoded by the researchers, and 21 of 158 individual questionnaires contained participant errors. The script looks for two participant-side patterns on the standard SUS:

- **Straight-lining at agree or disagree.** Every item answered 4 or 5 (or 1 or 2) means agreeing (or disagreeing) with both the positive and the negative items. All-3s is not flagged: neutral on everything is not contradictory.
- **Contradictions.** Agreeing (4+) with both "easy to use" and "very cumbersome", disagreeing (2 or below) with both, or agreeing with both "unnecessarily complex" and "easy to use". The respondent may have missed the reversal. These thresholds are a working default, not from the literature.

These are flags, not errors, and nothing is dropped. Following Meade & Craig (2012), the script flags possible careless responding and leaves the decision to exclude to you. They are reported before the mean, because each one would move it. The exit code is 1 when any are found. The all-positive version has no reversed items, so these checks don't run with `--positive`.

**The thing to say out loud.** A SUS score is not a percentage. A mean of 68.8 is a C on the Sauro–Lewis curve, not "69% usable". The script prints this every time, because the misreading is common.

## UMUX-Lite

Two 7-point items. Raw score is `((item1−1)+(item2−1))/12 × 100`. Report the raw score as the UMUX-Lite result; it is the primary output.

The script also prints a secondary SUS-equivalent using the regression `0.65 × raw + 22.9`, with the gap between them. The gap is `0.35 × raw − 22.9`: zero at a raw score of about 65.4, with the SUS-equivalent higher than raw below that and lower above it. MeasuringU now prefers interpolation to this regression for putting UMUX-Lite on the SUS scale (https://measuringu.com/from-umux-lite-to-ux-lite/). If you compare against a SUS benchmark, say which conversion you used.

## SEQ

A single 7-point item asked immediately after a task. Mean with t-interval (clamped to 1–7), top-two-box (6 or 7), and the difference from the average of about 5.5 (MeasuringU, https://measuringu.com/seq10/).

It is ordinal. A small difference between two tasks is not a finding without a test designed to detect one.

## NASA-TLX

Raw (unweighted) TLX: the mean of the six subscales. The script reports the overall figure and every subscale with its own t-interval (clamped to 0–100) and a bar.

Report the subscales. A task that is high on temporal demand and low on physical demand is a different problem from the reverse, and the overall number hides which one you have. The weighted version needs the 15 pairwise comparisons, which most studies skip — say which you used.

## validate

Compares a questionnaire against the canonical item wording, item by item.

Three outcomes per item:

- **exact** — unchanged.
- **accepted substitution** — a documented swap that does not materially move scores. Substituting the product noun (`system` → `product`, `website`, `app`, `tool`, `platform`, or the product's name) and `cumbersome` → `awkward` are accepted; the script names the substitution it found. Possessives ("This product's capabilities") and multi-word names ("Acme Cloud", with or without the "the"/"this" before it) are handled. Pass `--product "Acme Cloud"` to accept only that name; without it, any one to four capitalised words in the noun's place are read as a product name.
- **ALTERED** — anything else, shown next to the canonical wording so the difference is visible.

Two things produce a **warning** rather than a blocker:

- **Scale points.** Pass `--points`. SUS is a 5-point instrument and UMUX-Lite and SEQ are 7-point. A different number of points is flagged: the script scores only the standard scale, and published benchmarks were built on it. Say that you changed it.
- **One SUS item dropped.** Nine items are lined up against the canonical ten, and the script names the missing item and tells you to score with `--drop-item` (Lewis & Sauro 2017).

Any other missing or added item is a blocker. Messages are specific to the instrument: UMUX-Lite and SEQ output doesn't mention the SUS benchmark.

Example on a reworded SUS:

```
WARNING: scale has 7 points. SUS is a 5-point instrument. ...

   1  accepted substitution (system -> product)
   ...
   8  ALTERED (13% match)
      canonical: I found the system very cumbersome to use.
      yours:     The product felt really clunky and hard to get around.
```

Item 8 reads better. It is also no longer SUS, and the 68 benchmark no longer applies to the result. That is a legitimate choice — it just has to be a choice.

## Limitations

- **It cannot detect a reversed scale label.** If your form ran 1 = strongly agree instead of 5, every score is wrong and looks fine. Check the form, not just the data.
- **It cannot detect item reordering with canonical wording.** `validate` compares item 1 to item 1. Items in a different order will show as altered, which is the right outcome, but shuffled numbering in the response file will not be caught.
- **Inconsistency detection is conservative.** It catches straight-lining and direct contradictions. A respondent who answered thoughtfully but misread one item is undetectable, and a flagged respondent may have meant exactly what they said.
- **`validate` checks the standard SUS wording only.** It has no canonical text for the all-positive version.
- **Intervals are t-intervals, which assume the scores are roughly normal.** Treat them with more caution at very small n; the cut-off of about n = 10 is a working default, not from the literature. Intervals are clamped to the scale range, so a bound sitting at 0 or 100 has been cut off.
- **No weighted NASA-TLX.** The pairwise weighting needs data this script does not take.

## Workflow

1. `validate` the questionnaire before fielding. This is the step that gets skipped and the one that voids the benchmark.
2. Field it.
3. Score with `--per-respondent`.
4. Review the flagged rows. The script flags, it doesn't drop (Meade & Craig 2012). Excluding a row is a decision you make and report: say what you excluded and why.
5. Report the mean with its interval and grade, never the mean alone — the `evidence-integrity-auditor` skill flags a bare percentage, and at small n the interval can be tens of points wide.

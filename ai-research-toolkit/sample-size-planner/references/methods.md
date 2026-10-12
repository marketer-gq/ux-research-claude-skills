# The numbers, their formulas, and their sources

## Qualitative interviews and focus groups

**Starting range.** 9–17 interviews or 4–8 focus groups per fairly similar group with a
narrow aim. Hennink & Kaiser (2022), *Social Science & Medicine*, a systematic review of
empirical tests of saturation (https://pmc.ncbi.nlm.nih.gov/articles/PMC9359070).
Multiply by the number of segments you expect to differ: four segments gives 36–68
interviews.

**Code vs meaning saturation.** About 9 interviews to capture the range of issues (code
saturation), about 16–24 to understand them (meaning saturation). Hennink, Kaiser &
Marconi (2017), *Qualitative Health Research* 27(4). These are interview figures; don't
apply them to focus groups.

**Reflexive thematic analysis.** Braun & Clarke reject saturation as a sample-size
rationale for reflexive TA, because themes are developed by the researcher rather than
found in the data (https://uwe-repository.worktribe.com/output/4820803). Use information
power instead: Malterud, Siersma & Guassora (2016), *Qualitative Health Research* 26(13).
Five factors, each moving n down or up:

| Factor | Fewer participants | More participants |
|---|---|---|
| Aim | narrow | broad |
| Sample specificity | dense: participants closely fit the aim | sparse |
| Theory | applies established theory | no theoretical framework |
| Dialogue quality | strong | weak |
| Analysis strategy | in-depth case analysis | exploratory cross-case analysis |

The Hennink range still helps with budgeting and recruitment. Label it as a starting
point, not a stopping rule.

**Reporting rule.** Report findings from interviews as counts of participants, not
percentages. The sample is purposive and does not support estimating proportions in a
population.

## Saturation stopping rule

**Method.** Guest, Namey & Chen (2020), *PLOS ONE*
(https://doi.org/10.1371/journal.pone.0232076).

- **Base size.** The unique themes in the first 4 interviews.
- **Run length.** The next 2 interviews.
- **New-information threshold.** New themes in the run divided by themes in the base,
  ≤5%.

All three are configurable. This skill checks runs as a sliding window, one interview at
a time; that is an implementation choice, not part of the source.

**What it is not.** One stopping rule. It counts new codes and says nothing about whether
they are understood. Report the base, run and threshold with the result. It does not
apply to reflexive TA.

## Problem discovery

**Formula.** `P(found) = 1 - (1-p)^n`, where `p` is the probability a given problem
occurs in a single session. Nielsen & Landauer (1993).

**Conventional p.** 0.31, which is where "five users finds 85% of problems" comes from:
`1 - 0.69^5 = 0.84`.

**Why the conventional p is often wrong.** It was derived from a specific set of studies.
The problems a mature product has left are rarer than the problems an immature one has.
At p = 0.10, 85% discovery needs 19 sessions rather than 6 (from the formula above).

**Estimating p from your own sessions.** A p estimated from a study's first few sessions is
inflated, because small samples miss the rare problems that would pull the average down.
Lewis (2001) evaluated adjustments for this. Treat a self-estimated p as an upper bound.

**The three qualifications that matter.**

1. *Faulkner (2003).* Resampled 60 users. Random sets of 5 found 85% of known problems on
   average; the worst set found 55%
   (https://www.humanfactors.com/newsletters/enough_is_enough.html). The model's output
   is an expectation across possible samples; your study is one draw from that
   distribution.
2. *Spool & Schroeder (2001).* Observed roughly 35% discovery at 5 users on open-ended
   tasks. Where users take different paths, the independence assumption fails.
3. *Uniform frequency.* The model assumes every problem has the same p. Real problem sets
   have a long tail, and the tail is frequently where the valuable findings are.

## Adjusted-Wald interval

**Formula.** Agresti & Coull (1998). With `z` the normal quantile for the confidence level:

```
n_adj = n + z²
p_adj = (x + z²/2) / n_adj
margin = z × sqrt( p_adj(1-p_adj) / n_adj )
interval = p_adj ± margin
```

**Why not the standard Wald interval.** At small n and proportions near 0 or 1 the Wald
interval's actual coverage falls well below nominal, and it can produce bounds outside
[0,1]. The adjustment fixes both.

**The number worth memorising.** 1 of 5 = 20%, 95% interval 2.0% to 64.0% (from the
formula above).

**Reporting rule.** Below n=30, report the count. "One of five participants" is honest and
cannot be misread. "20%" invites a comparison the sample cannot support. The n=30 cut-off
is a working default, not from the literature.

## Sample size for a proportion

**Formula.** `n = z² × p(1-p) / m² − z²`, with `m` the margin of error.

The `− z²` is the adjusted-Wald planning correction. The adjusted-Wald interval behaves
like a Wald interval on `n + z²` observations, so reaching margin `m` needs `z²` fewer
real participants than the textbook `z² × p(1-p) / m²`. At 95% confidence `z² ≈ 3.84`.

**Expected proportion.** Defaults to 0.5, which maximises `p(1-p)` and so gives the
largest, safest n. A credible prior estimate lowers n, sometimes a lot. The script's
margin-of-error table uses `--expected` when given and says it assumes p = 0.5 when not.

**Reference points at 95% confidence, p = 0.5** (from the formula above):

| n | Margin of error |
|---|---|
| 20 | ±20 points |
| 40 | ±15 points |
| 100 | ±10 points |
| 385 | ±5 points |

**On the NN/g number.** Nielsen Norman Group gives 40 participants for a general
quantitative usability study at 95% / ±15% (https://www.nngroup.com/articles/summary-quant-sample-sizes/).
Its calculation comes to about 39, rounded to 40. The corrected formula above gives the
same 39. The uncorrected textbook formula gives 43.

## Task times

**Sauro & Lewis.** Report the geometric mean below about n=25 and the median above it.

**Why not the arithmetic mean.** Task times are right-skewed and bounded below by zero.
A single slow session moves the arithmetic mean substantially and the median barely.
The arithmetic mean describes a session nobody had.

**Intervals.** A t interval (df = n − 1) on log-transformed values, converted back, which
is why it is asymmetric. Use t, not z: at n = 8 the 95% critical value is 2.365, not 1.96.
An interval on raw times can extend below zero, which is nonsense for a duration.

## What needs a different calculation

**Comparing two groups.** Needs power analysis, and typically a far larger n than people
expect. Not in this skill.

**Ordinal scales.** Averaging severity ratings or satisfaction levels treats ordered
categories as numbers. Use the distribution, or top-two-box. See the
`instrument-scorer` skill for the instruments that do have a defined scoring rule.

**Significance tests on interview data.** Small-n tests are valid, but they can only
detect large effects (MeasuringU, https://measuringu.com/small-n/). The real obstacle for
interviews is the sampling: a purposive or qualitative sample does not support inference
to a population. The skill has no subcommand for it, deliberately.

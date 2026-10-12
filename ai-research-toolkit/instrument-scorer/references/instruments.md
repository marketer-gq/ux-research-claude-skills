# Instrument reference

## SUS — System Usability Scale (Brooke, 1996)

Ten items, five-point agreement scale, alternating positive and negative wording.

1. I think that I would like to use this system frequently.
2. I found the system unnecessarily complex.
3. I thought the system was easy to use.
4. I think that I would need the support of a technical person to be able to use this system.
5. I found the various functions in this system were well integrated.
6. I thought there was too much inconsistency in this system.
7. I would imagine that most people would learn to use this system very quickly.
8. I found the system very cumbersome to use.
9. I felt very confident using the system.
10. I needed to learn a lot of things before I could get going with this system.

**Scoring.** Odd items: `response − 1`. Even items: `5 − response`. Sum, multiply by 2.5.
Range 0–100, in steps of 2.5.

**All-positive version** (Sauro & Lewis 2011; Kortum et al. 2020,
https://pubmed.ncbi.nlm.nih.gov/31913715/). Every item is worded positively, so every
item scores `response − 1`. Sum, multiply by 2.5. Score it with `--positive`.

**One item dropped** (Lewis & Sauro 2017). A nine-item SUS can be scored if the sum is
rescaled: multiply by 100/36 instead of 2.5. Score it with `--drop-item N`, and say which
item you dropped.

**Benchmark.** Mean of approximately 68 across benchmarked products (Sauro & Lewis). 68 is
the average, not a pass mark.

**Sauro–Lewis curved grading scale.** The curve describes study means. Grade the mean of
a study, not individual respondents.

| Score | Grade | Percentile |
|---|---|---|
| 84.1–100 | A+ | 96–100 |
| 80.8–84.0 | A | 90–95 |
| 78.9–80.7 | A− | 85–89 |
| 77.2–78.8 | B+ | 80–84 |
| 74.1–77.1 | B | 70–79 |
| 72.6–74.0 | B− | 65–69 |
| 71.1–72.5 | C+ | 60–64 |
| 65.0–71.0 | C | 41–59 |
| 62.7–64.9 | C− | 35–40 |
| 51.7–62.6 | D | 15–34 |
| 0–51.6 | F | 0–14 |

**Accepted substitutions.** Replacing `system` with the product noun — product, website,
site, app, application, tool, platform — is documented as not materially affecting
scores. `cumbersome` → `awkward` in item 8 is also widely accepted.

**Not accepted.** Rewriting an item, adding one, or changing the agreement anchors. Any
of these means the benchmark and the grade curve no longer apply. Dropping one item is
the exception above, with rescaling. Changing the number of scale points is flagged as
a warning: say you did it, and treat benchmark comparisons with caution.

**Known error rates.** Sauro & Lewis report two separate figures. Researcher side: of
27 SUS datasets they reviewed, 3 were miscoded. Participant side: of 158 individual
questionnaires, 21 contained a participant error.

**Possible inconsistencies, not errors.** A pattern that suggests a missed reversal is a
flag for review. Flag it rather than drop it (Meade & Craig 2012), and report any
exclusion you then choose to make. Answering 3 to every item is neutral, not
contradictory.

## UMUX-Lite

Two items on a 7-point scale:

1. This system's capabilities meet my requirements.
2. This system is easy to use.

**Raw score.** `((item1 − 1) + (item2 − 1)) / 12 × 100`.

Report the raw score as the UMUX-Lite result.

**SUS-equivalent (secondary).** `0.65 × raw + 22.9`, the regression discussed at
https://measuringu.com/from-umux-lite-to-ux-lite/. Raw minus SUS-equivalent is
`0.35 × raw − 22.9`, which is zero at a raw score of about 65.4. Below that the
SUS-equivalent is higher than raw; above it, lower. The same MeasuringU page now prefers
interpolation to the regression for putting UMUX-Lite on the SUS scale. Whichever you
use against a SUS benchmark, say so.

## SEQ — Single Ease Question

One 7-point item immediately after a task: *"Overall, how difficult or easy was the
task to complete?"*

Report the mean with its interval and the top-two-box percentage. The average across
tasks is about 5.5 (MeasuringU, https://measuringu.com/seq10/). It is ordinal, so
small mean differences between tasks are not findings on their own.

## NASA-TLX

Six subscales, each 0–100 in 5-point increments: mental demand, physical demand,
temporal demand, performance, effort, frustration.

**Raw TLX** is the unweighted mean of the six. **Weighted TLX** requires 15 pairwise
comparisons of the subscales to derive weights. Most studies run raw and report it as
"NASA-TLX", which is fine as long as it is stated.

Always report the subscales alongside the overall. Two tasks with the same overall
workload can impose completely different kinds of it.

## Rules that apply to all of them

**Do not average ordinal levels across different instruments.** A SUS of 74 and an SEQ
of 5.8 do not combine into anything.

**Report the interval.** The script uses t-intervals (df = n − 1), clamped to the scale
range. At small n a SUS interval can be tens of points wide. The point estimate alone is the kind of claim the `evidence-integrity-auditor` skill
exists to flag.

**Hold n constant across waves** when benchmarking over time. A metric that moved
because the sample size changed is not a result.

**State which instrument and which variant.** Raw or weighted TLX, raw or
SUS-equivalent UMUX-Lite, canonical or reworded SUS. Each pair is a different number.

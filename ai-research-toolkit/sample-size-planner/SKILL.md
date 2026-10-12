---
name: sample-size-planner
description: Plan how many participants a study needs, with its source. Gives a starting range for interviews and focus groups per segment (saturation or information power), checks saturation from themes per interview, and covers problem-discovery n, adjusted-Wald intervals, margin of error and task times. Use when writing the n rationale for a research plan, or before reporting a percentage from a small study. Refuses significance tests on interview data.
---

# Sample Size & Confidence Planner

The "five users is enough" rule is the most repeated and least qualified number in the profession. Faulkner resampled 60 users and found that random sets of five located 85% of known problems on average, but the worst set found only 55%. The average is fine. Your study is one draw, and it may not be an average one.

This skill replaces the rule of thumb with a calculation or a sourced range, and attaches the citation so the number survives contact with a stakeholder who asks where it came from.

Every output states its assumption. A sample size without the assumption behind it is just a different rule of thumb.

## Goal

The researcher leaves with a sample size they can defend: a number or range, the assumption behind it, the citation for it, and a sentence they can paste into the plan for stakeholders.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You plan qualitative studies more often than quantitative ones, and you know the difference matters more than any formula.

- Start from the research question and the decision it informs, then the method, then the number. A sample size is only as good as the question behind it.
- For qualitative work, give a sourced starting range and the reasoning that moves it up or down. Don't present a range as a requirement.
- Push back, kindly and with the citation, when a stakeholder asks for a percentage, a p-value or a significance test from a purposive sample.
- Be honest about budget trade-offs. Fewer segments done properly usually beats every segment done thinly; say which you'd cut and why.

## Quick start

```bash
# How many interviews for four segments?
python scripts/sample_size.py plan interviews --segments 4

# Reflexive TA, aiming for depth rather than a list of issues
python scripts/sample_size.py plan interviews --approach reflexive-ta --goal understanding

# Have new interviews stopped adding themes?
python scripts/sample_size.py saturation codes_by_interview.csv

# How many sessions to find 85% of problems occurring in 31% of sessions?
python scripts/sample_size.py discover --problem-frequency 0.31

# What does "1 of 5 participants" actually mean?
python scripts/sample_size.py interval 1 5

# How many people for +/-15 points at 95% confidence?
python scripts/sample_size.py proportion --confidence 0.95 --margin 0.15

# How should these task times be summarised?
python scripts/sample_size.py times 32 41 38 45 210 36 40 39
```

## Which subcommand

| You are | Use |
|---|---|
| Planning interviews or focus groups | `plan interviews`, with `--segments`, `--approach`, `--goal`, `--method` |
| Checking whether interviews have stopped adding themes | `saturation` |
| Planning a study that finds problems to fix | `discover`, then `plan formative-usability` |
| Planning a study that measures something | `proportion`, then `plan summative-usability` or `plan survey` |
| Reporting "x of n participants" | `interval` |
| Reporting task times | `times` |

## What each one does

### plan interviews

Gives a sourced starting range, per segment and in total, and writes the rationale paragraph for the plan.

| Option | Values | Default |
|---|---|---|
| `--approach` | `reflexive-ta`, `codebook`, `affinity` | `affinity` |
| `--segments` | number of groups you expect to differ | 1 |
| `--goal` | `issues`, `understanding` | `issues` |
| `--method` | `interviews`, `focus-groups` | `interviews` |

- **Starting range.** 9–17 interviews, or 4–8 focus groups, per fairly similar group. This is the range at which empirical tests reached saturation in Hennink & Kaiser's (2022) systematic review (*Social Science & Medicine*, https://pmc.ncbi.nlm.nih.gov/articles/PMC9359070). The total is the range times the number of segments: `--segments 4` gives 36–68 interviews.
- **Goal.** `issues` (finding the range of issues) reached code saturation at about 9 interviews per group. `understanding` (making sense of them) needed about 16–24 for meaning saturation. Source: Hennink, Kaiser & Marconi (2017), *Qualitative Health Research* 27(4). These figures come from interviews, so for focus groups the output sticks to the 4–8 range.
- **Reflexive TA.** Braun & Clarke reject saturation as a rationale for reflexive thematic analysis (https://uwe-repository.worktribe.com/output/4820803). The output offers information power instead (Malterud, Siersma & Guassora 2016, *Qualitative Health Research* 26(13)), with its five factors: aim, sample specificity, theory, dialogue quality and analysis strategy. A narrow aim, closely fitting participants, established theory, strong dialogue and in-depth case analysis each move n down; their opposites move it up. The Hennink range is still printed, labelled as a starting point for budgeting.
- **Codebook and affinity.** The output points to `saturation` as a check you can run on your own data while fieldwork is underway.

The rationale paragraph always says findings will be reported as counts of participants, not percentages. That is the commitment that stops a nine-person study producing "67% of users".

### saturation

Applies the Guest, Namey & Chen (2020) stopping rule (*PLOS ONE*, https://doi.org/10.1371/journal.pone.0232076) to the themes or codes from each interview, in the order you ran them.

- **Input.** CSV with a header row, then the interview ID in the first column and codes in the other cells (several per cell separated by `;`). One row per code also works: repeated IDs are merged. Or JSON: a list of `{"interview": "P1", "codes": [...]}` objects, a list of lists, or `{"P1": [...], ...}`.
- **Defaults.** Base size 4, run length 2, new-information threshold ≤5%, all from Guest et al. Change them with `--base`, `--run` and `--threshold`.
- **Output.** New themes per interview, the unique themes in the base, the % new information in each run (new themes in the run divided by themes in the base), the % in the last run, and whether the threshold is met. Runs are checked as a sliding window, one interview at a time (this skill's implementation choice).

It is one stopping rule, not proof. It counts new codes, not whether they are understood, and a different base, run or threshold gives a different answer, so report the parameters with the result. It does not apply to reflexive TA.

### discover

The problem-discovery model, `P(found) = 1-(1-p)^n` (Nielsen & Landauer 1993). Give it the frequency of the problems you care about and it returns n for 80%, 85%, 90%, 95% and 99% expected discovery, plus the discovery curve by n.

At the conventional p=0.31, five sessions gives 84% expected discovery, which is where "five users" comes from. The skill prints that number next to three reasons not to treat it as a promise:

- Faulkner's resampling: 85% on average for random sets of five, 55% for the worst set.
- Spool & Schroeder's roughly 35% observed discovery at five users on open-ended tasks, where the model's assumptions do not hold.
- The model assumes one frequency for every problem. Rare problems need far more sessions than common ones, and the problems worth finding are often the rare ones.

Lower `--problem-frequency` when the issues you are hunting are subtle. At p=0.10, 85% discovery needs 19 sessions, not 6.

If you estimated `--problem-frequency` from your own first few sessions, treat it as inflated: small samples overstate p. Lewis (2001) evaluated ways of adjusting the estimate down before using it to plan.

### interval

The adjusted-Wald (Agresti–Coull 1998) interval for a proportion, which holds its nominal coverage at small n where the textbook Wald interval does not.

`interval 1 5` returns **20%, with a 95% interval from 2.0% to 64.0%**. That is a 62-point-wide interval. A stakeholder reading "20% of users struggled" is reading a number that is consistent with almost any conclusion.

Below n=30 the output recommends reporting the raw count instead of the percentage (the n=30 cut-off is a working default, not from the literature).

### proportion

n for a target confidence and margin of error, using the adjusted-Wald planning formula `n = z²p(1−p)/m² − z²`. The adjusted-Wald interval adds z² to n, so you need z² fewer real participants than the textbook formula says. At 95% and ±15 points this gives **39**, which is the figure NN/g computes before rounding to 40 (https://www.nngroup.com/articles/summary-quant-sample-sizes/).

It also prints the margin of error by n, which is usually more persuasive than the single answer. The table uses `--expected` when you pass it and says it assumes p=0.5 when you don't. At p=0.5, 40 participants gives ±15 points, 100 gives ±10 and 385 gives ±5. That table is what a budget conversation actually needs.

### times

Task times are right-skewed. One slow session drags the arithmetic mean above the typical experience, and reporting that mean overstates how long the task takes for most people.

The output shows all three measures and tells you which to report: geometric mean below about n=25, median above, per Sauro & Lewis. The interval is a t interval (df = n−1) on log-transformed values, converted back, which is why it is asymmetric around the centre.

The arithmetic mean is printed with "do not report this" next to it, because it is the one people reach for.

### plan (other methods)

`formative-usability`, `summative-usability`, `survey` and `benchmark` produce the n rationale paragraph for a research plan: the number, the assumption behind it, the citation and the caveat. Paste it in.

## What it refuses

**Significance tests on interview data.** There is no subcommand for it. Small-n tests are valid; they can only detect large effects (MeasuringU, https://measuringu.com/small-n/). The problem with interview data is the sampling. Interview participants are chosen purposively, and a purposive or qualitative sample does not support inference to a population, whatever the test says.

**A single number with no assumption attached.** Every output carries the assumption and the citation. This is deliberate: the reason "five users" spread is that it travelled without either.

## Input errors

Bad input exits with status 2 and a one-line message, never a traceback. Problem frequency, margin, expected proportion, confidence, target and the saturation threshold must be between 0 and 1, exclusive. A margin typed as a percentage gets a hint ("did you mean 0.15?"). n and `--segments` must be at least 1, and task times must be positive.

## Limitations

- The interview ranges come from studies of fairly similar groups with narrow aims. A broad aim or a mixed sample needs more, which is why the output works per segment.
- The discovery model assumes problems occur independently at a uniform frequency. Real problems cluster and vary. Treat the curve as an upper bound on what you will find, not a forecast.
- The proportion calculation assumes simple random sampling. A panel is not a random sample of a population, and no arithmetic fixes that. The margin of error describes sampling error only.
- Task-time intervals assume the log-transformed values are roughly normal. At very small n this is an assumption you are making, not one the data supports.
- Nothing here helps with comparing two groups. That needs a different calculation and usually a much larger n than people expect.

## Worked example

A researcher is planning interviews with admins and finance managers at small and large companies: four segments.

```
$ python scripts/sample_size.py plan interviews --segments 4

Starting range:
  9-17 interviews per segment
  36-68 interviews in total (4 segments)
  Source: Hennink & Kaiser (2022), Social Science & Medicine, ...

Goal: find the range of issues. For this goal, about 9 per segment
reaches code saturation (about 36 in total).
  Source: Hennink, Kaiser & Marconi (2017), Qualitative Health Research 27(4) ...
```

The budget conversation now starts from 36, not from "eight interviews should do it". Halfway through fieldwork, they check one segment:

```
$ python scripts/sample_size.py saturation admins_small.csv

  interviews 5-6   1 new   12%
  interviews 6-7   0 new   0%   <= threshold
  interviews 7-8   0 new   0%   <= threshold

Last run (interviews 7-8): 0% new information. Threshold met.
```

That supports stopping that segment, with the parameters stated.

A usability lead on the same team has been told to run five sessions:

```
$ python scripts/sample_size.py discover --problem-frequency 0.10

  80% of problems   n = 16
  85% of problems   n = 19
  90% of problems   n = 22
  95% of problems   n = 29
  99% of problems   n = 44

Discovery by n at this frequency:
  n=5    41%
  n=10   65%
  n=20   88%
```

The five-session plan finds an expected 41% of the problems they care about. That is the conversation to have before the study runs, not after it ships.

Then, on the way out:

```
$ python scripts/sample_size.py interval 1 5
1 of 5 = 20%
  95% interval: 2.0% to 64.0%  (width 62 points)
```

Which is why the readout should say "one of five participants", and the `evidence-integrity-auditor` skill flags it when it does not.

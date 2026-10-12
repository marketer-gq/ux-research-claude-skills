# Screener benchmarks and where the numbers come from

Every threshold the checker applies is here with its source, so a researcher can argue
with the number rather than with the tool.

## Length and structure

| Measure | Benchmark | Source |
|---|---|---|
| Median question count | 7 | User Interviews, analysis of 42,756 screeners fielded Nov 2021–Nov 2023 (https://www.userinterviews.com/screener-dropoff-report) |
| Average drop-off | 6% | Same |
| Question-count limit | 10, warning only | Working default, unsourced |
| Open-ended limit | 2 | NN/g, https://www.nngroup.com/articles/screening-questions-select-research-participants/; Great Question, https://www.greatquestion.com/blog/participant-fraud-in-online-qualitative-ux-research |

The finding that matters most in the User Interviews analysis is not the median length.
It is that **drop-off stays roughly flat as closed questions are added**, while
open-ended questions cost completion. That is why exceeding `max_questions` is a
warning and not a blocker: a long screener of single-selects is not on its own a reason
to stop a launch. Check what the extra questions are before cutting them.

`max_open_ended` defaults to 2. For interview recruiting, include at least one
open-ended "articulation" question ("Tell us about the last time you…"). Both sources
above recommend one. It shows whether the person can talk about the topic in a session,
and it gives you something concrete to read when judging whether a respondent is
genuine. The checker warns when an interview screener has none.

## Question design

| Check | Source |
|---|---|
| Avoid yes/no screening questions: they tell the respondent which answer you want. Ask a multiple-choice question where the qualifying answer is one of several plausible options | NN/g, https://www.nngroup.com/articles/screening-questions-select-research-participants/ |
| Health, racial or ethnic origin, sex life or sexual orientation, religious or philosophical beliefs, political opinions, trade union membership, and biometric or genetic data are special-category data | GDPR Article 9 |
| Collect only what you need to keep. Tag answers needed only to qualify someone as `screener-only` | GDPR data-minimisation principle, Article 5(1)(c) |

The special-category check and the "Prefer not to say" check are keyword-based and
advisory. They flag a question for a person to look at. They are not legal advice. If a
special-category question is genuinely needed, the respondent has to give explicit
consent before answering, and the screener should say what the answer is for.

The privacy check passes when the file has a `privacy_notice` field or any question or
helper text mentions privacy, consent, personal data or data protection. Many tools
attach a consent form at study level instead of in the screener. In that case, confirm
it is attached and record it in `privacy_notice`.

## Performance targets

| Measure | Target | Reading |
|---|---|---|
| Show rate | ≥ 90% | Published no-show rates for moderated studies are 5–10% (MeasuringU, https://measuringu.com/typical-no-show-rate-for-moderated-studies/). Below 90%, look at the screener as well as the scheduling |
| Completion rate | ≥ 70% | Working default, unsourced. Below this, suspect the screener before the panel |
| Qualification rate | 20–50% | Working default, unsourced. Above 50%, it is not discriminating. Below 20%, you are burning panel goodwill |

These are post-launch measures. The checker cannot compute them from a draft; it flags
the structural causes of missing them. Pull the real rates after launch and compare.

## Completion-time estimate

The script assumes 15 seconds per closed question and 45 seconds per open-ended one.
These are working defaults, unsourced, for relative comparison between drafts, not
measured values for your panel. If you have real timing data, change `SECONDS_CLOSED` and
`SECONDS_OPEN` in `scripts/screener_io.py` and say so in your fork's changelog.

## Ordering

Qualifying questions come before demographic ones. A respondent who will not qualify
should find that out early, not after answering questions that do not matter. The
checker flags any demographic question appearing before the last question that carries
screening logic. A demographic question that has its own screening logic (country,
company size) is a qualifier, and is not flagged.

Demographic detection is keyword-based (age, gender, income, education, ethnicity,
location, country, company size, employee count). It will miss an unusually worded
demographic question. It is a prompt for the researcher to look, not a guarantee.

## Red herrings

A red herring is a question with an implausible option that a fraudulent or
professional respondent will claim anyway — "which of these tools have you used",
with one invented tool in the list.

They work exactly once per panel. After that, respondents have learned the answer.
The checker tracks this with a fingerprint of the normalised question text in
`.screener-fingerprints.json` and warns when a labelled red herring reappears inside
the reuse window. The default of 180 days is a heuristic, not a measured figure; set
`red_herring_reuse_days` to suit how often your panel is contacted.

The checker cannot infer which questions are red herrings from their wording. It relies
on the internal label carrying the marker (default `[RH]`). If your team does not label
them, this check reports nothing and the fingerprint file stays empty.

## What is deliberately not checked

Question wording quality beyond a short list of leading-language patterns. Wording is a
judgement call and a checker that pretends otherwise produces false confidence. The
leading-language flags are advisory and say so in the output.

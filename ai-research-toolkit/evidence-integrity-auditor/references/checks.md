# What each check does, and the evidence behind it

## Quote verification

**Why.** Looppanel tested ChatGPT on multi-interview synthesis and found it citing the
same participant supporting two contradictory themes, and in a separate case all three
"supporting quotes" for a finding traced back to a single sentence at one timestamp.
Mehta et al. (2025, *Scientific Reports* 15:34993,
https://doi.org/10.1038/s41598-025-18969-w) found GPT-4o's quote selection was low and
variable in accuracy, with altered, truncated and merged quotes.

Most differences between a report quote and a transcript are not that, though. Light
editing (dropping fillers, cutting with an ellipsis, adding a bracketed clarification) is
standard practice (Corden & Sainsbury 2006,
https://www.york.ac.uk/inst/spru/pubs/pdf/verb.pdf). The check is built so that a lightly
cleaned real quote verifies, and only a quote with nothing close to it is critical.

**How.** Each quote of 40 characters or more (a working default) has its attribution
(`(P1)`, `[P1]`, `— P1`, `— Participant 3`) stripped and recorded. It is then normalised:
lowercase, punctuation stripped, curly quotes folded, filler words (um, uh, er, like,
you know) dropped from both sides, and `[sic]` removed. The quote is split at each `...`
and `[bracketed insertion]`, and each part is matched on its own. Sources are read the
same way; WebVTT/SRT files have cue numbers, timestamps and `<v Name>` tags removed and
their cues joined. A report found inside `--sources` is skipped with a warning.

Each part is located with a word n-gram anchor search, then scored with
`difflib.SequenceMatcher` (with `autojunk=False`) against windows around each anchor.
The quote's score is the length-weighted average of its parts in the best source.

| Match | Status | Severity |
|---|---|---|
| ≥ 97% | verified | none, or a note if it was lightly edited |
| 70–97% | altered | warning. Present but changed, often a paraphrase |
| 50–70% | not located | warning. "Check for an edit, a translation, or a missing transcript" |
| < 50% | absent | critical. Nothing close in any source |

All bands are working defaults, not from the literature. On the synthetic 10,000-word
transcript in `tests/`, lightly edited quotes score 100%, a paraphrase about 75% and an
invented quote about 47%. Ellipsis parts that appear out of order or more than 250 words
apart (a working default) are marked altered: that is the shape of a merged quote.

**`--verbatim strict|intelligent`.** Under `intelligent` (the default) light edits verify
with a note. Under `strict` any edit, including removed fillers or minor wording
differences, makes the quote altered.

**What it cannot do.** Confirm the quote came from the participant named. It confirms the
words exist somewhere in the corpus. Check speaker labels in the transcripts first; the
`transcript-cleaner` skill can help but is optional. It also cannot tell a translation
or a missing transcript from an invented quote, which is why the message names those
first.

## Concentration

**Why.** A report that cites eight participants and is carried by two is overstating its
base, and prose hides this completely. Counting is the only way to see it.

**Thresholds.** One participant supplying more than 40% of attributed quotes is critical
when the study has at least 5 participants (`--n`, or the number quoted if `--n` is not
given), and a note below that. Both are working defaults, not from the literature. The
message asks the researcher to check whether quote selection reflects the evidence base,
because articulate participants are often over-quoted. With `--n`, participants never
quoted are reported as a warning.

**Note.** The threshold is a default, not a law. A study deliberately weighted toward one
extreme user may legitimately concentrate. The finding is a prompt to justify the
concentration, not proof of a defect.

## Claim linkage

**Why.** The sentences that assert the most tend to evidence the least. "Users always
abandon slow flows" is doing more work than any quote in the report supports.

**How.** A sentence must contain a claim marker (users, participants, customers, most,
many, everyone, all, consistently) *and* an unhedged generalisation pattern (users
want/need/prefer, everyone, nobody, always, never, all users) *and* have no quote within
three lines (a working default).

Deliberately narrow. A check that flagged every unevidenced sentence would flag the whole
report and be ignored.

## Small-sample numbers

**Why.** In a small qualitative study, a percentage implies a precision the sample cannot
carry. Counts are what NN/g and Maxwell recommend
(https://www.nngroup.com/videos/numbers-small-ux-studies/).

**How.** Raw counts ("3 of 8", "3 out of 8", "3/8") are never flagged. A percentage is a
warning when its n is under 10 (a working default, not from the literature), and the
message gives the count to use instead. The n is the denominator of an `x of y` in the
same sentence, otherwise `--n`. With no n at all the percentage gets a note. Dates
(`12/03/2026`) and `24/7` are not read as fractions. A sentence that already carries an
interval marker (±, +/-, confidence interval, CI, margin of error) is left alone.

**Intervals** are optional and only make sense for a random sample. If you need one,
`sample-size-planner` computes it.

## Recommendation basis

**Why.** A recommendation is where a finding becomes a decision someone acts on and
spends money against. It is the last place an unsupported claim should survive, and the
first place they accumulate, because recommendations get written last and fastest.

**How.** Sentences containing recommendation language (we should, we recommend, must,
needs to, prioritise, next steps) with no quote within five lines (a working default) and
no citation of a participant or a finding. "See" is not a citation: "see appendix" points
somewhere, it does not evidence anything. Reported as a warning.

## Disconfirming evidence

**Why.** Negative case analysis (Lincoln & Guba) asks the researcher to look for
participants who contradict a finding, and to revise the finding or report them. A
report that never mentions disagreement either looked and found none, or did not look.
Asking the question is what catches the Looppanel case above: a researcher checking
"did anyone contradict this?" goes back to the transcripts and finds the same participant
on both sides.

**How.** For each heading that cites at least one quote, the text under it is searched for
disagreement language (contradict, disagree, exception, counter-example, negative case, in
contrast, unlike, not everyone, pushed back, did not share/agree). If none is present, a
warning asks whether any participant contradicted the finding. Saying that no one did
clears it. It reads words, not meaning.

## Participant × theme matrix

**Why.** The Looppanel failure mode — one participant cited in support of two
contradictory themes — cannot be detected mechanically, because the tool cannot know
which of your themes contradict each other. What it can do is show you every participant
appearing under more than one theme, so a human can check.

Reported as a note, never as a warning. Appearing under several themes is normal in a
good study.

## Deliberately not checked

**Theme quality.** Whether "Onboarding" is a theme or a topic summary is a real and
valuable check, and it is the `theme-quality-auditor` skill.

**Tone, structure, readability.** Not integrity questions.

**Whether the finding is true.** No tool can do this. The audit checks that the report
says what its evidence supports — not that the evidence was gathered from the right
people, or that the study asked the right question.

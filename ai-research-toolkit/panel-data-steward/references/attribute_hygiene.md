# Attribute hygiene reference

## Why filtering silently under-returns

A candidate filter matches on the stored value. When the same role is stored five
ways, a filter for one of them returns a fifth of the people. Nothing errors. The
researcher sees a small number and concludes the panel is thin, which is the wrong
diagnosis and leads to the wrong fix — recruiting more people into an attribute set
that will scatter them the same way.

This is the most common reason a panel looks smaller than it is.

## How the clustering works

1. **Normalise.** Lowercase, strip punctuation except `+` and `#`, collapse
   whitespace, expand abbreviations from the list in `scripts/attribute_clean.py`.
2. **Group exact matches.** Values that normalise identically are the same value.
   This catches case and punctuation variants at no risk.
3. **Compare by similarity, with two thresholds.** Remaining groups are compared
   with `difflib.SequenceMatcher`. At or above the upper threshold they are
   proposed as one value. Between the lower and upper threshold they go to a
   clerical-review queue, as in Fellegi–Sunter record linkage, and only merge if
   a person approves them.
4. **Never merge opposites.** Values that differ by a negation (`un-`, `in-`,
   `non-`, `dis-`, `not`, and `im-`/`il-`/`ir-`), an antonym pair
   (`full-time`/`part-time`), their numbers (`100-500`/`1000-5000`), a `+` or `#`
   token (`C++`/`C#`), or that name two different countries are never merged,
   and `approve` refuses them.
5. **Hold on meaning-changing tokens.** A token present in one value and absent
   from the other holds the merge for review even when the similarity clears.
   The default list is in `DEFAULT_BLOCKING_TOKENS`.
6. **Pick the canonical.** The most frequent surface form in the cluster wins, on
   the grounds that the majority spelling is usually the house style.

## Choosing a threshold

Upper threshold `--threshold` defaults to 0.88; lower `--review-threshold`
defaults to 0.70. Both are working defaults, not from the literature.

| Upper threshold | Behaviour |
|---|---|
| 0.90+ | Case, punctuation and typos only. Very safe, misses abbreviations that did not expand. |
| 0.88 (default) | `Product Manager` / `product manager` / `PM` / `Product Mgr` merge, because they normalise to the same string. `Product Marketing Manager` stays separate. Near-misses go to the review queue. |
| 0.70 | Aggressive. Relies on the blocking tokens to hold apart values that are similar strings but different jobs. Review every cluster. |

Run it twice on a real export before picking. The difference between two thresholds
on your own data is more informative than any recommendation here.

## Geographic attributes

Country names are close strings: Austria/Australia, Niger/Nigeria,
Ireland/Iceland. An attribute whose name marks it as geographic (country,
region, city, state, location and similar) is never fuzzy-matched. Values group
only on exact spelling or on the same ISO 3166-1 alpha-2 code from a short
embedded list, so `UK` and `United Kingdom` meet and `Niger` and `Nigeria` don't.
Abbreviations are not expanded in these attributes. In any attribute, two values
that are both recognised country names with different codes never merge.

## The abbreviation list is an assumption

`pm` expands to `product manager`. On a panel of construction professionals it should
expand to `project manager`, and on a clinical panel it might mean neither. The
report prints the ambiguous expansions it applied. Override with `--abbreviations`
and keep the override in version control next to your canonical value lists.

## The blocking token list is a starting point

`research` blocks `ResearchOps` from merging with `Research Operations`, which is a
false hold. That is the cost of a token list that also correctly holds
`Data Analyst` apart from `Analyst`. Tune the list for your panel; expect to approve
a few merges by hand either way, with `approve --merge VALUE --into VALUE`.

## Approval

Approval is per variant. `approve --variant` records one stored spelling going
into its proposed canonical; approving one variant in a cluster approves nothing
else in it. `plan` refuses to run without an approval file written by `approve`,
and writes a reverse plan beside the forward one.

## Evidence standards for enrichment

| Source | Sufficient on its own? | What to attach |
|---|---|---|
| Direct screener answer | Yes | The question and the response |
| Direct statement in a transcript | Yes | The quote and its session reference |
| Inference across two sources | No | Propose it as a question for the researcher |
| Inference from role or company | No | Nothing. This is guessing. |

An attribute written without evidence is indistinguishable from one written with it
once it is on the profile. That is why the standard has to hold at write time.

## Consent comes before enrichment

Before filling attributes from transcripts or screener responses, confirm that
participants' consent covers adding that information to their profile. Reusing
study data for profile enrichment is a new purpose (GDPR purpose limitation,
Art 5(1)(b)).

## What never gets inferred

The GDPR Art 9 special categories: racial or ethnic origin, political opinions,
religious or philosophical beliefs, trade union membership, genetic data,
biometric data, health, sex life or sexual orientation
([ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/)).
Add the team's own list on top (pass it to `cluster` with `--sensitive`). Income
and employment status aren't Art 9, but many teams include them. If it was not
asked directly and answered, it does not go on the profile, however confident the
inference.

Any merge in one of these attributes needs manual review: `approve` refuses
without `--reviewer NAME`.

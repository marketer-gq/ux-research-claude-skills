---
name: panel-data-steward
description: Clean participant panel attribute data — find duplicate attribute names and sparse attributes, cluster variant spellings of one value into a canonical set, and propose evidence-backed enrichments from screener answers and transcripts. Use when a panel filter returns fewer people than it should, after an import, or before a heavy recruitment quarter. Works on any export or directly through the Great Question MCP. Every change is approved one value at a time, written one candidate at a time, and saved with an undo plan.
---

# Panel Data Steward

A filter on participant data matches the stored value. When the same role is stored as "Product Manager", "product manager", "PM", "Product Mgr" and "Sr. Product Manager", a filter for one of them returns a fifth of the people.

Nothing errors. The researcher sees a small number, concludes the panel is thin, and recruits more people into an attribute set that scatters them the same way. This is the most common reason a panel looks smaller than it is, and it is invisible from inside the tool.

This skill works on an export. CSV or JSON, from any panel, participant database, CRM or spreadsheet. It proposes; a human approves each value; nothing is written automatically.

## Goal

The panel's attributes say what researchers think they say, so a filter finds the people who are really there. Every change is approved by a person, respects participant consent, and can be undone.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You look after a research panel as shared infrastructure that many researchers and participants depend on.

- Be conservative with merges. A wrong merge loses information a researcher may have needed, while a missed one only leaves the data a little messy. When in doubt, hold the merge and ask.
- Treat participant data with care. Flag special-category data, check that consent covers what you propose, and keep nothing you don't need.
- Explain each proposal in terms a researcher will recognise: who gets found that is missed today, and what would change for them.
- Never write to the panel without a person's approval, and make every change reversible.

## Four jobs

**Attribute inventory** — how populated each attribute is, and which attribute *names* look like duplicates of each other. Scripted, read-only, and the right first run on any panel.

**Value cleaning** — cluster variant spellings into a proposed canonical set. Scripted, deterministic, the main event.

**Mapping check** — find screener questions collecting answers that map to no attribute. Those answers cannot be filtered on, so they are write-only. This one has no script, and it can't run on Great Question MCP data (see **Mapping check** below).

**Enrichment** — propose attribute values already evidenced in screener responses or transcripts but never recorded on the profile, each carrying its evidence.

## Quick start

```bash
# Start here: which attributes exist, how full they are, which names duplicate each other
python scripts/attribute_clean.py keys panel_export.json

# Cluster the values of one attribute
python scripts/attribute_clean.py cluster panel_export.csv --attribute role -o proposal.json

# Try a second threshold before choosing one
python scripts/attribute_clean.py cluster panel_export.csv --attribute role --threshold 0.80 -o loose.json

# See every candidate's change and the held queue, before anyone approves anything
python scripts/attribute_clean.py review proposal.json

# Approve one variant at a time, and any held merge a person has checked
python scripts/attribute_clean.py approve proposal.json --variant "PM" --variant "product manager"
python scripts/attribute_clean.py approve proposal.json --merge "ResearchOps" --into "Research Operations"

# Turn the approvals into a list of changes, with a reverse plan for undo
python scripts/attribute_clean.py plan proposal.json --approved approved.json -o write_plan.json
```

`plan` refuses to run without `--approved`, and `approved.json` only comes from `approve`. Approving a cluster's canonical does not approve its variants; each variant is approved by name.

## Input

CSV with a header, JSON, or **a directory of JSON files** — one per page from a paginated export, merged and de-duplicated on id. It accepts a list of records, records nested under `candidates` / `data` / `results` / `items`, attributes flat on the record or nested under an `attributes` object, and a bare list of strings, and Great Question's JSON:API shape with custom attributes under `attributes.extra`. List-valued attributes are clustered item by item. Attribute names are matched case-insensitively, and the report tells you the exact spelling to write back. When one attribute is stored under two spellings (`role` on some candidates, `Role` on others, or two CSV columns), each candidate's write uses the spelling that candidate already has, so no second attribute is created. A candidate holding both at once is reported as a collision and left out of the plan. Custom attributes win over system fields of the same name: a Great Question record's top-level `type` never hides `extra.type`. The identifier is taken from `candidate_id`, `id`, `uuid` or `email`, whichever is present.

In other words: whatever your panel tool's export button produces, or a spreadsheet someone maintains by hand.

## How the clustering works

1. **Normalise** — lowercase, strip punctuation except `+` and `#` (so `C++` and `C#` stay apart), collapse whitespace, expand abbreviations.
2. **Group exact matches** — values that normalise identically are the same value. Free win, no risk.
3. **Compare by similarity, with two thresholds** — pairs at or above the upper threshold are proposed merges. Pairs between the lower and upper threshold go to a review queue and are never merged unless a person approves them. This is the clerical-review band from Fellegi–Sunter record linkage.
4. **Never merge opposites** — values that differ by a negation (`un-`, `in-`, `non-`, `dis-`, `not`, and the `im-`/`il-`/`ir-` forms), by an antonym pair (`full-time`/`part-time`), by their numbers (`100-500`/`1000-5000`), by a `+` or `#` token, or that name two different countries are never merged. `approve` refuses them too.
5. **Hold on meaning-changing tokens** — a word present in one value and absent from the other holds the merge for review even when similarity clears. `marketing`, `senior`, `data`, `research` and the rest of `DEFAULT_BLOCKING_TOKENS` in the script.
6. **Pick the canonical** — the most frequent spelling in the cluster wins.

**Geographic attributes are never fuzzy-matched.** Austria/Australia, Niger/Nigeria and Ireland/Iceland are close strings and different countries. An attribute whose name says country, region, city, state, location and so on groups only on exact spelling, or on the same ISO 3166-1 code (`UK` and `United Kingdom`). Abbreviations are not expanded there, so `IT` stays Italy. Force it either way with `--geographic` / `--not-geographic`.

Output is a report plus `proposal.json`. Nothing is written.

### Choosing a threshold

Two numbers: `--threshold` (upper, default 0.88) and `--review-threshold` (lower, default 0.70). Both are working defaults, not from the literature.

| Upper threshold | Behaviour |
|---|---|
| 0.90+ | Case, punctuation and typos only. Safe, misses abbreviations that did not expand |
| 0.88 (default) | `Product Manager` / `product manager` / `PM` / `Product Mgr` merge, because they normalise to the same string. `Product Marketing Manager` stays separate. Near-misses land in the review queue |
| 0.70 | Aggressive; relies on the blocking tokens. Review every cluster |

Run it twice on your own export and compare. The difference on real data is more informative than any recommendation here.

### Held merges are a review queue, not a verdict

The report lists three queues: **held for review** (similarity in the band), **blocked** (a meaning-changing token), and **never merged** (opposites, numbers, symbols, countries). The first two can be approved with `approve --merge VALUE --into VALUE`, no JSON editing. The third cannot.

At 0.70 on a real panel the blocking tokens held these apart:

```
0.75  product marketing manager / product manager     (marketing)
0.81  senior product manager    / product manager     (senior)
0.73  researchops               / research operations (research)
```

The first two are correct — Product Marketing Manager is a different job, and most teams want seniority preserved. The third is a false hold; those are the same role. Approve it with `approve --merge "ResearchOps" --into "Research Operations"`. Do not lower the threshold to force one legitimate merge through, because several illegitimate ones will come with it.

### The abbreviation list is an assumption

`pm` expands to `product manager`. On a construction panel it should be `project manager`; on a clinical one it may be neither. The report prints the ambiguous expansions it applied. Override with `--abbreviations` and keep the override next to your canonical value lists.

## Mapping check

There is no script for this check; the agent does it by reading. It can't run on Great Question MCP data: the MCP reads verified for this skill don't return which attribute a screener question maps to. Run it on a screener export that includes the mapping.

For each screener question, compare its attribute mapping against the attributes that actually exist in the export. Report: mapped correctly, mapped to something that does not exist, or unmapped.

Propose the closest existing attribute **by meaning, not by label**. `role` and `role_detail`, `company` and `company_size`, `tool` and `tool_primary` all look alike and mean different things — use each attribute's existing values as the evidence for a match, not its name.

Where nothing fits, propose a new attribute with its value set, and route it to whoever owns the vocabulary rather than creating it.

The `screener-porter` skill runs this same check as part of its pre-flight. Use this one when the screener is already live.

## Enrichment

The answer is often already in a screener response or a transcript and was never recorded.

**Check consent first.** Before filling any attribute from a transcript or screener response, ask the researcher to confirm that the participants' consent covers adding this information to their profile. Data collected for one study can't be reused for another purpose without that (GDPR purpose limitation, Art 5(1)(b)). No confirmation, no enrichment.

| Source | Sufficient on its own? | Attach |
|---|---|---|
| Direct screener answer | yes | the question and the response |
| Direct statement in a transcript | yes | the quote and its session reference |
| Inference across two sources | no | propose it as a question, not a value |
| Inference from role or company | no | nothing; this is guessing |

Two rules that are not negotiable by the agent:

**Nothing sensitive is ever inferred.** Sensitive means the GDPR Art 9 special categories — racial or ethnic origin, political opinions, religious or philosophical beliefs, trade union membership, genetic data, biometric data, health, sex life or sexual orientation ([ICO](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/special-category-data/what-is-special-category-data/)) — plus whatever the team adds to its own list. Income and employment status aren't Art 9, but many teams put them on that list. If it was not asked directly and answered, it does not go on a profile however confident the inference.

**Merges in sensitive attributes need a named reviewer.** `cluster` flags an attribute whose name matches an Art 9 category, or that is on the team list passed with `--sensitive team_sensitive.json`. `approve` then refuses without `--reviewer NAME`.

**An existing value is never silently overwritten.** Where old evidence and new evidence disagree, propose "re-confirm" showing both.

## Applying the changes

`plan` turns approved variants into an explicit list of changes — one per participant, each naming the attribute under that participant's exact spelling, the old value and the new one — and a reverse list that puts every value back. Apply it however your panel is edited: a bulk-update import, an API, an MCP integration, or a person with the spreadsheet open.

Apply changes one record at a time and stop on the first error. A half-applied merge is worse than none, because the attribute now has a sixth spelling.

Keep `write_plan.json`. It is the audit log: which approvals, by whom, which candidates, from what to what. `reverse_steps` is the undo.

Re-run `cluster` afterwards to confirm the value set is what you expect.

## Why proposing is the product

The temptation with a clean list of 400 merges is to apply them. A wrong merge is invisible once written and silently corrupts every segment built on the attribute afterwards. There is no error message, and the only undo is the reverse plan you saved.

Route merges affecting large numbers of people to whoever owns the vocabulary rather than to the researcher who asked.

## Limitations

- **Free-text fields are not dirty.** A notes field with 400 distinct values is working correctly. Decide which attributes are canonical before running this on them.
- **The blocking token list is a starting point.** `research` correctly holds `Data Analyst` apart from `Analyst` and incorrectly holds `ResearchOps` apart from `Research Operations`. Expect to approve a few by hand.
- **Canonical is the most frequent spelling, not the correct one.** If the majority spelling is wrong, override it.
- **It cannot see attributes missing entirely.** A panel where nobody has `seniority` filled in looks clean; it is empty. Check populated percentages with `keys`. It flags attributes under 30% populated and attribute names at 0.85 similarity or above; both are working defaults, not from the literature (`--sparse`, `--duplicate`).
- **The country list is short and English-only.** Values it doesn't recognise in a geographic attribute group on exact spelling only. Merge the rest with `approve --merge`.

## Worked example

177 records, 29 distinct values in `role`, at 0.82 (run before the default moved to 0.88; the Product Manager variants are exact after normalisation, so that cluster comes out the same at 0.88):

```
177 records · 29 distinct values · 12 clusters (7 merge more than one value)
· 4 orphans · threshold 0.82

PROPOSED MERGES (7)
  Product Manager            63 candidates from 5 variants
     * Product Manager                   31
       product manager                   14
       PM                                 9
       Product Mgr                        6
       product Manager                    3
  UX Researcher              34 candidates from 4 variants
  ...

LEFT ALONE (5) — one spelling only, nothing to merge
  ResearchOps (3), Head of Product (3), Data Analyst (3), Design Lead (2), Analyst (2)

Nothing has been written.
```

The researcher came in saying the role filter returned 12 people when they knew there were at least 40 product managers. There are 63. Nobody knew the filter was wrong, because a filter returning too few results looks like a small panel rather than a data problem.

## With the Great Question MCP

When the Great Question MCP is connected, read the panel straight off the account and write approved changes back. Everything below was verified against the live server on 24 Sep 2026 with read-only calls. The write side is marked where it is not verified.

### Two things to know first

**The tool schemas are empty.** Great Question MCP tools advertise no parameter list and no description. Argument names come from the server's own errors: leave a required one out and it replies `Missing required arguments: <name>`, and nothing happens. Use that on the first call of any tool not covered below.

**Custom attributes live under `attributes.extra`, and their names are case-sensitive.** On the account tested, the role attribute is `Role`, not `role`. The scripts match case-insensitively for reading, and every report prints the exact name. Writes have to use that exact name, or they create a second attribute beside the first. That is how a panel ends up with `favorite_color`, `favorite_colors` and `favorite_color_multiple`, which is exactly what `keys` found on the test account.

### Reading the panel

**1. Pull every page.** Call `list_candidates`. It returns 20 candidates per page, with `meta.count` and `meta.pages`. Pass `page` as an integer; a string fails validation. Save each response verbatim into one folder:

```
panel/page_01.json
panel/page_02.json
...
panel/page_23.json
```

Pull every page. A cleaning run on page one alone will propose merges that look complete and are not. Check the number of files against `meta.pages` before going on.

`search_candidates` with no arguments returns the same list. `list_candidate_segments` lists saved segments by name and ID, if the researcher wants to scope a run to one segment.

**2. Take stock, then cluster:**

```bash
python scripts/attribute_clean.py keys panel/
python scripts/attribute_clean.py cluster panel/ --attribute role -o proposal.json
```

Both read the folder as one export and de-duplicate on candidate ID.

**3. Treat the saved pages as personal data.** Each record carries a name and email. The scripts only need the ID and `extra`, so delete the `panel/` folder when the run is finished. Keep `write_plan.json`; it holds IDs and attribute values only.

### Writing approved changes

**4. Show the full list before asking for approval.**

```bash
python scripts/attribute_clean.py review proposal.json
```

This prints every candidate's from → to change, under that candidate's exact attribute spelling, plus the held queue and any collisions. Show all of it to the researcher. A summary of clusters is not enough; a wrong merge cannot be spotted once it is written.

**5. Record approvals one variant at a time:**

```bash
python scripts/attribute_clean.py approve proposal.json --variant "PM" --variant "product manager"
python scripts/attribute_clean.py approve proposal.json --merge "ResearchOps" --into "Research Operations"
```

Only approve what the researcher named. Never approve on their behalf, and never approve a whole cluster because its canonical looks right.

**6. Build the plan from the approvals only:**

```bash
python scripts/attribute_clean.py plan proposal.json --approved approved.json -o write_plan.json
```

Each step names one candidate ID, the attribute (that candidate's exact spelling), the old value and the new one. For a list attribute, `from` and `to` are the whole list, because the change has to replace the full list rather than append to it. `reverse_steps` holds the undo. Show the printed plan and get a yes.

**7. Write with `update_candidate`, one candidate per call, and stop on the first error.** The argument shape for `update_candidate` is **not verified**; checking it would mean writing to the account. Expect it to take the candidate ID and the attribute under its exact name. Make the first call on a single candidate and read the result.

**8. Pause after the first 5 writes.** Call `get_candidate` on each of those 5 and confirm the value landed under the original attribute name and did not create a new one. Show the researcher, and continue only on their go-ahead. Five is a working default, not from the literature.

**9. Keep the audit log.** Add each completed step to `applied` in `write_plan.json` as you go, with the time. If something goes wrong, walk `reverse_steps` for the steps in `applied`.

**10. Re-run `keys` and `cluster`** on a fresh pull to confirm the value set is what you expected.

### Enrichment sources on the MCP

Confirm consent covers profile enrichment before reading any of these (see **Enrichment**). Screener responses come from the `list_*_screener_responses` / `get_*_screener_response` tools, split by study type like the screener tools. Transcripts come from `search_transcripts` and `get_transcript`. None of these were probed for this version, so resolve their arguments from the server's errors on first use. The evidence standard in **Enrichment** above applies whatever the source.

### What a live record looks like

For reference when something doesn't match. Names and emails removed:

```json
{"id": "8544503", "type": "customer",
 "attributes": {"id": 8544503,
   "extra": {"tz": "CST", "Role": "Account Executive ", "company": "Very Good Question"},
   "average_rating": "4.5"}}
```

The trailing space in `"Account Executive "` is real, and `cluster` reports it as a whitespace fix.

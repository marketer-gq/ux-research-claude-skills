---
name: screener-porter
description: Move a participant screener between tools or studies as a portable file and pre-flight it before launch — unmapped attributes, too many open-ended questions, yes/no screening questions, missing screening logic or consent text, burned red herrings. Use when copying a screener, migrating one from another tool, or checking a draft. Works on a JSON or CSV export or through the Great Question MCP. Checks and converts an existing screener; does not write one from scratch.
---

# Screener Porter

Screeners get copied by hand between studies and between tools, and the copy loses the part that matters: which question maps to which participant attribute. Nobody notices until someone tries to filter on it months later and the data turns out to be write-only.

This skill does three things to a screener file, none of which need a research platform connected:

- **Convert** a screener from whatever shape it arrives in into one portable format.
- **Check** it against published benchmarks and structural rules before it is fielded.
- **Plan** the import into wherever it is going, question by question, with the attribute mappings preserved.

It works on an export from any tool — a CSV from a survey platform, a JSON API response, a screener someone typed into a doc. The checks are the same whatever produced it.

This is not a screener generator. Writing a screener from scratch is a different job.

## Goal

A screener arrives at its destination intact: the same questions, the same screening logic and attribute mappings, checked against good practice before it is fielded, so the right participants get through and their answers can be filtered on later.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You recruit for qualitative studies and know that a screener's job is to find the right people, honestly and with as little burden on them as possible.

- Judge each question by whether it screens for the research need, not by whether it is well formed in the abstract.
- Watch for questions that let people guess the "right" answer, and for sensitive questions without a clear reason and consent.
- Treat the benchmark findings as defaults to reason from. When the study needs a longer screener or an unusual question, say why it is justified.
- Before anything is written to a platform, make sure the researcher has seen exactly what will change.

## Quick start

```bash
# Convert whatever you have into the portable format
python scripts/screener_io.py export whatever_you_exported.json -o screener.json --md screener.md

# Check it before anyone fields it
python scripts/screener_io.py check screener.json --rules rules.json

# Produce an ordered import plan for the destination tool
python scripts/screener_io.py plan screener.json --study-type interview -o plan.json

# After launch, record any red herrings so reuse gets caught next time
python scripts/screener_io.py fingerprint screener.json --study "Q4 enterprise admins"
```

`check` exits 1 when it finds a blocker, so it can gate a launch step. With the default rules every finding is a warning or a note; set `unmapped_attribute_policy` to `blocker` if you want unmapped questions to stop a launch.

## Getting a screener in

`export` is deliberately tolerant. It hunts for the question list inside common wrapper shapes (`questions`, `screener_questions`, `items`, `data`, or a bare array) and maps each field by a list of aliases — so `question` / `title` / `prompt` / `text` all resolve to the question text, and `attribute_key` / `maps_to` / `candidate_attribute` all resolve to the attribute mapping.

It also finds JSON:API lists (`data: [{id, attributes: {...}}]`), and it keeps option-level screening flags: an option carrying `disqualify: true` (or `qualify`, `screen_out`, `action: "disqualify"` and similar) is added to that question's disqualifying or qualifying answers rather than dropped.

A `.csv` file is read as one row per question (or pass `--format csv`). Column headers go through the same aliases, so `Question`, `Type`, `Options`, `Disqualifying answers` and `Attribute` all work. Separate several options or answers in one cell with `|`. `Required` accepts yes/no, true/false or 1/0.

Anything it could not carry across is printed by name at the end of the run, so a field you care about never disappears silently. Add an alias to `FIELD_ALIASES` in the script and re-export.

If your data is somewhere it cannot read — a PDF, a Google Doc, a platform with no export — transcribe it into the portable format by hand. It is a flat JSON file and the structure is in `screener.md` after any export.

## The portable format

One JSON file. Per question: text, type, options, required flag, attribute mapping, disqualification logic, and an internal label. At the top, an optional `privacy_notice` (text or a URL; `export --privacy-notice` sets it). That is the whole schema, and it is the reason a screener can move between two tools that know nothing about each other.

Not every answer should become a permanent participant attribute. Set a question's attribute to `screener-only` when the answer is only needed to qualify someone; GDPR's data-minimisation principle is the reason to keep that list short. `check` does not flag a screener-only question as unmapped.

`--md` writes a readable rendering alongside it for human review, with unmapped attributes marked in bold and disqualifying options marked inline.

## What `check` catches

| Check | Level | Why |
|---|---|---|
| Question count over the limit | warning | Median screener is 7 questions (User Interviews), and drop-off stays flat as closed questions are added. The limit of 10 is a working default, unsourced |
| Open-ended questions over the limit | warning | These drive drop-off; closed-ended ones barely move it |
| Interview screener with no open-ended question | warning | One "articulation" question shows whether someone can talk about the topic and helps catch fraud (NN/g; Great Question) |
| Questions with no attribute mapping | warning by default | The answers cannot be filtered on later. Tag deliberate ones `screener-only` |
| Closed questions with no disqualification logic | warning | They look like screening and let everyone through |
| Yes/no screening questions | warning | They tell the respondent which answer you want (NN/g) |
| Demographics before the last qualifying question | warning | People who will not qualify answer them for nothing. A demographic question with its own screening logic, such as country or company size, counts as a qualifier and is not flagged |
| Possible GDPR Article 9 special-category questions | warning | Health, ethnicity, sexuality, religion, politics, union membership and biometric or genetic data need explicit consent |
| No privacy notice or consent text | warning | Respondents should know what happens to their answers before they give them |
| Sensitive demographics with no "Prefer not to say" | warning | Age, gender, income and the special categories above should let people decline |
| Leading or evaluative wording | warning, advisory | A judgement call, flagged for a human. Evaluative words are flagged only when they describe the thing asked about ("How great was…"), so "Great Question" passes |
| Red herring reused inside the window | warning | Respondents have learned the answer |
| "Other — please specify" options | note | Frequently unfilterable separately from its sub-answers |

Sources and the reasoning for each threshold are in `references/screener_benchmarks.md`.

It also estimates completion time, stating the per-question assumptions it used.

Thresholds live in a `rules.json` you pass in, so a team can set its own and keep them in version control:

```json
{
  "max_questions": 10,
  "max_open_ended": 2,
  "unmapped_attribute_policy": "warning",
  "red_herring_reuse_days": 180,
  "red_herring_marker": "[RH]"
}
```

Those are the defaults. `max_questions` of 10 is a working default, unsourced. `max_open_ended` of 2 follows NN/g and Great Question's fraud guidance. The 180-day reuse window is a heuristic. `references/screener_benchmarks.md` has the detail.

## Red herrings

A red herring is a question with an implausible option a fraudulent respondent will claim anyway — "which of these tools have you used", with one invented tool in the list. It works exactly once per panel.

`fingerprint` records a hash of the normalised question text after a launch. `check` warns when a labelled red herring reappears inside the reuse window, naming the study it was burned on and how many days ago. The 180-day default window is a heuristic, not a measured figure.

The checker cannot infer which questions are red herrings from their wording. It relies on the internal label carrying a marker, `[RH]` by default. Teams that do not label them get nothing from this check, and the fingerprint file stays empty.

## Getting a screener out

`plan` emits an ordered list of steps — create the screener, then add each question with its arguments — as plain JSON. Walk it against whatever the destination is: a platform API, an MCP integration, or a person typing it in.

Steps whose attribute mapping is unresolved carry a `preconditions` entry saying so, so a half-mapped screener cannot be imported by accident. The generic plan carries `skip_logic` through as-is; the Great Question plan drops it and warns (see below).

## Limitations

- **It cannot verify a question type exists in the destination.** Matrix questions in particular are unsupported in several platforms. With `--target gq` the plan restricts itself to the four types seen on a Great Question read and leaves anything else unresolved. Resolve types against the destination before walking the plan; do not split a matrix into single-selects silently, because the analysis plan usually depends on the matrix shape.
- **Attribute mappings are strings.** It checks they are present, not that they point at something real in the destination. Resolve them there.
- **Demographic and special-category detection is keyword-based** (age, gender, income, education, ethnicity, location, country, company size; health, religion, politics and the other Article 9 categories). An unusually worded question will be missed, and a question about working in a medical practice will be flagged. Both are prompts to look, not legal advice.
- **The leading-wording list is short and advisory.** A clean result means nothing matched.
- **Completion-time estimates are relative, not measured.** 15 seconds per closed question and 45 per open one are working defaults, unsourced, for comparing two drafts. Change them in the script if you have real timing data, and say that you did.

## Worked example

A six-question interview screener exported from one study, checked before being copied into another (the file is `tests/fixtures/worked_example.json`):

```
WARNINGS (6)
  - 4 question(s) with no attribute mapping: a3, a4, a5, a6. Responses to
    these cannot be filtered on later. If that is deliberate, set the
    attribute to "screener-only".
  - 2 closed question(s) with no qualifying or disqualifying answers: a3, a6.
  - Demographic question(s) a1 appear before the last qualifying question.
  - a3 wording: tag question invites agreement — "Don't you agree that the
    current approval flow is frustrating?"
  - No privacy notice or consent text found.
  - Sensitive question(s) a1 have no "Prefer not to say" option.

NOTES (3)
  - 6 questions (limit 10).
  - Estimated completion time 2m 30s (assumes 15s per closed question, 45s per open one).
  - Question(s) a6 contain an "Other — please specify" option.

PASS: no blockers.
```

The four unmapped attributes are the finding. A hand-copied version of this screener would have fielded cleanly, collected four questions' worth of answers, and been impossible to filter on afterwards. Either map them or tag the ones you do not need to keep as `screener-only`. A team that wants this to stop the launch sets `unmapped_attribute_policy` to `blocker`.

## With the Great Question MCP

When the Great Question MCP is connected, run the whole loop against it: read a screener off one study, check it, and write it onto another. Everything below was verified against the live server on 24 Sep 2026 with read-only calls. Where something is not verified, it says so.

### Two things to know first

**The tool schemas are empty.** Every Great Question MCP tool advertises itself as a bare object, with no parameter list and no description. Argument names cannot be read from the tool listing. The server does name a missing argument when you leave one out (`Missing required arguments: interview_id`), and a call that fails that way does nothing. Use that on the first call of any tool not covered in the table below.

**The screener read carries no attribute mappings.** `get_*_screener` returns no attribute field on any question. `export` detects this and says so, and `check` reports that mappings cannot be checked from the file instead of blocking every question. Confirm the mappings in the Great Question app before relying on a copied screener for filtering.

### Which tools, and which ID

Screeners are typed by study. Pick the tool family from the study's `style` on `list_studies`:

| Study `style` | Screener type | ID argument | Read | Create | Add a question | Apply a template |
|---|---|---|---|---|---|---|
| `video_call` | interview | `interview_id` | `get_interview_screener` | `create_interview_screener` | `add_interview_screener_question` | `apply_interview_screener_template` |
| `unmoderated_test` | unmoderated | `unmoderated_study_id` | `get_unmoderated_screener` | `create_unmoderated_screener` | `add_unmoderated_screener_question` | `apply_unmoderated_screener_template` |
| survey | survey | `survey_id` | `get_survey_screener` | `create_survey_screener` | `add_survey_screener_question` | `apply_survey_screener_template` |

The three ID argument names differ, and passing `study_id` to any of them fails. They were read from the server's own errors on the `get_*_screener` tools. The create, add and template tools are assumed to take the same ID argument, which is unverified because checking would mean writing to the account.

### Step by step

**1. Find the source study.** Call `list_studies`. It returns 20 studies per page with `meta.pages`; pass `page` as an integer, not a string. Each study carries `style` and `has_screener`. Skip any study where `has_screener` is false, because there is nothing to read.

**2. Read the screener.** Call the read tool for that study's type with its ID, for example `get_unmoderated_screener` with `unmoderated_study_id: 90775`. Save the response verbatim to `screener.raw.json`. It is JSON:API-shaped (`data.attributes.questions`), and `export` unwraps it.

```bash
python scripts/screener_io.py export screener.raw.json -o screener.json --md screener.md \
    --study-type unmoderated --name "<study title>"
```

The screener response has no name, so replace `<study title>` with the source study's title exactly as `list_studies` returns it. Don't make one up; if you can't find the title, ask the researcher.

**3. Check it.**

```bash
python scripts/screener_io.py check screener.json --red-herrings 2348949
```

Great Question questions have no internal-label field, so a `[RH]` marker has nowhere safe to go. `helper` text is shown to participants. Pass red-herring question IDs with `--red-herrings` instead, using the numeric IDs from the export.

**4. Plan the write.**

```bash
python scripts/screener_io.py plan screener.json --target gq \
    --study-type video_call --study-id 89579 -o plan.json
```

`--target gq` emits steps that name the exact tool and use Great Question's own field names: `label`, `question_type`, `required`, `options`, `qualifying_answers`, `disqualifying_answers`, `helper`. Those mirror the read shape. `--study-type` accepts either the screener type or the study's `style` value, on both `export` and `plan`. `--study-id` must be the numeric study ID.

The plan only writes the four question types seen on a live read (below). Foreign types are mapped: `boolean` → `yes_no`; `checkbox`, `multi_select` → `multiple_choice`; `radio`, `dropdown`, `single_select` → `single_choice`; any free-text type → `long_text`. Each mapping is listed in the step's `warnings`. A type with no equivalent, such as `matrix`, `scale` or `ranking`, gets `question_type: null` and a precondition, so it cannot be written until someone decides. Check what a source tool means by `multiple_choice`: some use it for single-select.

Attribute mappings are carried through on each step as `attribute`, not as a tool argument, because no attribute argument on the screener write tools is documented. Set them in the Great Question app after the questions exist. `skip_logic` is not written either; the plan warns for every question that had some, so it can be rebuilt by hand.

**5. Before walking the plan:**

- Check `has_screener` on the target study. If it already has one, skip step 1 of the plan (the create call) rather than creating a second screener.
- Call `list_templates`. If a template matches, the apply-template tool does the whole thing in one call.
- Show the plan to the researcher and get a yes. It writes to their account.

**6. Walk the plan, one call per step, and stop on the first error.** If the first add call fails with `Missing required arguments`, correct that argument name in every remaining step and retry. Do not guess at alternatives. Report what was created before stopping, so a partial import can be cleaned up.

**7. Record red herrings** after a successful import:

```bash
python scripts/screener_io.py fingerprint screener.json --study "Q4 enterprise admins" \
    --red-herrings 2348949
```

### What the live read looks like

The Great Question field names, from a real unmoderated screener, for reference when something doesn't match:

```json
{"id": 2348946,
 "label": "How often do you submit or approve business expenses?",
 "question_type": "single_choice",
 "required": true, "position": 2, "helper": null,
 "options": ["Weekly or more", "About monthly", "A few times a year",
             "Once a year or less", "Never"],
 "qualifying_answers": ["Weekly or more", "About monthly", "A few times a year"],
 "disqualifying_answers": ["Once a year or less", "Never"],
 "skip_logic": []}
```

Question types observed: `single_choice`, `multiple_choice`, `long_text`, `yes_no`. `yes_no` questions arrive with `options: []`. The exporter supplies Yes/No for checking, and the plan writes `options: []` back, as the read does.

`references/known_limitations.md` records Great Question constraints that affect imports. Treat it as a snapshot and re-check before telling a researcher something cannot be done.

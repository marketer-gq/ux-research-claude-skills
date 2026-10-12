---
name: task-scenario-linter
description: Check usability task scenarios before a study is fielded — matching task wording literally against the product's own navigation labels and button text, and flagging embedded instructions, priming language, task dependencies and missing success criteria. Use when writing or reviewing tasks for a moderated or unmoderated usability test. Checks task wording; it does not write tasks or analyse results.
---

# Task Scenario Linter

A usability task that names the button is usually not a usability task. The participant matches your word against the word on screen and completes it, and the completion rate you report measures reading comprehension.

It is a common defect in usability tasks and the easiest to check mechanically: take the product's navigation labels and button text, and look for them in the task wording.

It is not a hypothetical problem. Maria Rosala's NN/g article ["The Methodological Problems Hiding in Your Research Tools"](https://www.nngroup.com/articles/research-tool-problems/) (13 March 2026) describes AI research tools generating tasks that prime participants or tell them where to navigate. The tools generating tasks at scale are generating this defect at scale.

## Goal

Every task measures whether participants can find and use the thing being tested, not whether they can match a word on screen, and each has an end state clear enough for the study type.

## Your role

Act as a senior UX researcher with deep qualitative training and a firm grip on method: someone a research lead would trust to review this work before it reaches stakeholders. The script gives you evidence, not a verdict. Read its output the way an experienced researcher would: weigh it against the study's goal, method and context, and say plainly when a finding doesn't apply and why.

You design usability tasks that measure whether people can find and use something, not whether they can match a word on screen.

- Read each flagged task in the context of the study's goal. Naming a label can be right in a directed feature test or with specialist users; say so instead of insisting on a rewrite.
- When you suggest a fix, write a realistic scenario in the participant's own terms, with a clear end state, as a direct instruction.
- Think about the whole set, not only each task: order effects, dependencies between tasks, and how long the session will run.
- Keep the participant in mind. A task should feel like something they would really do.

## Quick start

```bash
python scripts/lint_tasks.py tasks.md --vocab nav_labels.txt
python scripts/lint_tasks.py tasks.md --vocab nav.json --mode unmoderated
python scripts/lint_tasks.py tasks.md --vocab nav.txt --study-type quant
python scripts/lint_tasks.py tasks.md --vocab nav.txt --allow-terms "Approvals"
```

Exit code is 1 when a critical finding exists, so it can gate fielding. Exit code 2 means the input could not be read: a missing or empty tasks file, or a vocabulary file in the wrong shape.

## What it needs

**The tasks**, as markdown or text. Each of these starts a new task: numbered items (`1.`, `2)`), `Task 1:` lines, numbered headings (`## Task 1`, `## 1)`) and bullets. A heading or `Task 1:` line with nothing after it takes the paragraphs below it. Tasks are numbered by position in the file, so two items both numbered 1 stay separate. A file with no markers at all is treated as one task.

**The product vocabulary** via `--vocab` — the navigation labels and button text a participant will see on screen. One term per line, or a JSON list of strings, or a JSON object whose values are lists of strings (so you can keep `{"nav": [...], "buttons": [...]}`). Labels match their singular and plural forms ("Reports" catches "report"), and leading symbols are ignored ("+ New" catches "new"). Terms under three characters are skipped because they match everything (a working default, not from the literature).

This is the input that makes the skill work, and it is the one people skip. A vocabulary file of nine labels caught three critical defects in the example below, and getting it from a designer is a short ask.

**Intentional labels** via `--allow-terms`. Some studies name a label on purpose. Pass those as a comma-separated list (`--allow-terms "Approvals,Insights"`) and they are not checked.

**The study type** via `--study-type`: `qual` (the default), `quant` when you will report completion rates, or `tree` for a tree test. **The mode** via `--mode`: moderated (the default) or unmoderated. Together they set how much a missing end state matters — see below.

## The checks

| Check | Severity | What it catches |
|---|---|---|
| `ui-vocabulary` | critical; warning for a single-word label that is also an everyday word (Home, Help, Search, Settings) | Task text contains a product nav label or button name |
| `embedded-instruction` | critical with a vocab hit, otherwise warning | "click", "navigate to", "select", "use the" |
| `no-success-criteria` | critical for quant; warning for qual; not checked for tree | No stated end state |
| `task-dependency` | warning | "the study you created in task 1" |
| `priming` | warning | "easy", "easily", "simply", "quickly", "new", "intuitive" |
| `hypothetical` | warning (not checked for tree) | "How would you…", "Show me how you would…". NN/g prefers a direct imperative |
| `no-context` | warning | No scenario framing — no reason the participant would do this. "You'd like…", "You've just…" and "You're…" count as framing |
| `multiple-tasks` | warning | Steps joined with "and then" |
| `length` | warning | Over 60 words (heuristic) |
| `over-specified` | warning | "First … then …" prescribes the sequence |

### Why study type and mode change the end-state rule

Specificity about the *end state* is a nice-to-have with a moderator in the room and more important without one. Unmoderated, nobody can answer "am I done?", so the participant decides. In a quant study that is critical: your completion rate becomes a record of their opinion rather than a measurement. In a qual study you are watching what people do and why, so a missing end state is a warning, not a blocker. In a tree test, choosing a location is the end state, so the check is skipped.

Specificity about the *route* is wrong in all of them. The study type and mode change the severity of `no-success-criteria` only. They never relax the vocabulary check; only `--allow-terms` does that, one label at a time.

If you can, randomise task order across participants so learning effects are spread rather than piled onto the later tasks. Task dependencies stop you doing that, which is one more reason the linter flags them.

### What a clean task looks like

```
You've just been asked by your manager to get sign-off on a budget
request before Friday. Go ahead and get it approved. Let me know
when you feel you're done.
```

No product labels. A reason. An end state. A route the participant chooses, which is the thing the study is for.

## Reading the output

Each task gets `ok`, `review` or `FAIL`. FAIL means at least one critical.

A `review` task is not necessarily wrong. Priming words and missing context are judgement calls that depend on what the study is measuring — a study specifically about feature discovery may legitimately mention that something is new. The linter's job is to make you decide rather than to decide for you.

Criticals are different. Naming UI is a defect unless the study is deliberately testing something other than findability (for example a directed feature test, or a specialist audience's own terms). Source: NN/g, https://www.nngroup.com/articles/test-tasks-quant-qualitative/. In those studies, pass the labels you mean to name with `--allow-terms`.

## Limitations

- **Synonyms are not caught.** A task saying "the reporting area" when the nav label is "Insights" passes, and is usually fine — the participant still has to find it. If your team considers close synonyms a defect, add them to the vocabulary file.
- **Vocabulary quality is everything.** An incomplete vocabulary file produces a clean report on a dirty task set. Ask for the real nav labels rather than writing them from memory.
- **Common words in the vocabulary cause false positives.** A product with a button labelled "Share" will flag any task using the word share in its ordinary sense. Single-word labels on the script's everyday-word list (Home, Help, Search, Settings, Share and similar) are reported as warnings rather than criticals for this reason. The list is a heuristic. Review those hits rather than removing the term, and use `--allow-terms` for ones you have decided are fine.
- **Plural matching is simple.** It handles regular English plurals ("Reports", "Activities", "Inboxes"), not irregular ones ("People"/"person").
- **The context and success-criteria checks are pattern-based.** A task framed in a way the patterns do not recognise will be flagged as missing context. Read the task before acting on it.
- **It does not check whether the task is worth running.** A perfectly worded task testing something nobody does is still a wasted session.

## Worked example

Four tasks, nine vocabulary terms, an unmoderated quant study (`--mode unmoderated --study-type quant`). Messages shortened:

```
Task 1 [FAIL]  Click on Approvals in the left nav and approve the pending request.
    CRITICAL (ui-vocabulary) Uses the product's own label "Approvals".
    CRITICAL (embedded-instruction) Contains the instruction "click".
    WARNING  (no-context) No scenario framing.
    CRITICAL (no-success-criteria) No stated end state.

Task 2 [ok]  You've just been asked by your manager to get sign-off on a budget req...

Task 3 [FAIL]  Find the new Insights feature and use the Export button to easily Shar...
    CRITICAL (ui-vocabulary) Uses the product's own label "Insights".
    CRITICAL (ui-vocabulary) Uses the product's own label "Export".
    WARNING  (ui-vocabulary) Uses "Share", which is a product label and also an everyday word.
    CRITICAL (embedded-instruction) Contains the instruction "use the".
    WARNING  (priming) The word "easily" tells the participant it should be easy.
    WARNING  (priming) The word "new" draws attention to recency, which primes exploration.
    CRITICAL (no-success-criteria) No stated end state.

Task 4 [FAIL]  Using the study you created in task 1, invite three participants.
    WARNING  (task-dependency) Depends on an earlier task ("the study you created").
    WARNING  (no-context) No scenario framing.
    CRITICAL (no-success-criteria) No stated end state.

8 critical, 6 warning, 0 note
```

The same tasks as a qual study (`--study-type qual`, still unmoderated) give 5 critical, 9 warning: the three end-state findings drop to warnings.

Task 3 is the one worth looking at. It names two product labels outright and a third that is also an everyday word, tells the participant which control to use, primes them to expect ease, and then asks what they think of it. It would produce a high completion rate and a positive sentiment, and neither number would mean anything.

The task and vocabulary files are in `tests/fixtures/`, and a test checks that the summary line above matches the script.

## Workflow

1. Get the real navigation labels and button text from a designer or the product itself. Save as `nav_labels.txt`.
2. Lint the draft tasks.
3. Fix criticals by removing the label and describing the goal instead. "Approve the pending request in Approvals" becomes "your manager needs sign-off on a budget request before Friday".
4. Re-run. Confirm zero criticals rather than fewer.
5. Review the warnings with whoever owns the study and decide each one.
6. Re-lint after any edit. Rewrites reintroduce labels more often than you would expect.

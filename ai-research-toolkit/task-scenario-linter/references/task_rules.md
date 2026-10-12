# Task scenario rules

## The rule that matters

**Do not use the product's own words.** Navigation labels, button text, feature names,
menu items. If the participant can match a word in your task against a word on the
screen, you are measuring their ability to match words.

This is the most-named failure in both NN/g's and Optimal Workshop's guidance on task
writing, and it is the reason this skill is mechanical rather than advisory: it is the
one defect that can be checked by string match, and checking it by eye reliably misses
instances.

Maria Rosala, "The Methodological Problems Hiding in Your Research Tools" (NN/g,
13 March 2026, https://www.nngroup.com/articles/research-tool-problems/), describes AI
research tools generating tasks that prime participants or tell them where to
navigate. Tools that generate tasks generate this defect faster than a human can.

The rule has exceptions. Naming UI is a defect unless the study is deliberately testing
something other than findability (for example a directed feature test, or a specialist
audience's own terms). Source: https://www.nngroup.com/articles/test-tasks-quant-qualitative/.
The linter's `--allow-terms` flag exists for those cases.

### How the linter matches labels

- Singular and plural forms match each other ("Reports" catches "report"). Only regular
  English plurals are handled.
- Leading and trailing symbols are ignored, so "+ New" catches "new".
- A single-word label that is also an everyday word (Home, Help, Search, Settings, Share
  and similar) is reported as a warning, not a critical, because "search for the
  invoice" is usually ordinary language. The word list is a heuristic and lives in
  `COMMON_WORD_LABELS` in the script.

## Goal, not route

A scenario gives a participant a reason to act and lets them choose how.

| Instruction | Scenario |
|---|---|
| "Click Approvals and approve the request." | "Your manager needs sign-off on a budget request before Friday." |
| "Use the Export button to download the report." | "Your colleague can't log in but needs these numbers for a meeting." |
| "Navigate to Account Settings and change your notification preferences." | "You're getting too many emails from this tool." |

The right-hand column produces a route the participant chose, which is the finding.
The left-hand column produces a completion rate.

## Priming

Evaluative and minimising words set an expectation before the participant starts:
*easy*, *easily*, *simply*, *just*, *quickly*, *intuitive*, *handy*, *useful*, *new*,
*improved*.

"New" is the subtle one. Mentioning that a feature is new directs attention toward it
and inflates discovery. If the study is specifically about whether people notice a new
feature, saying it is new destroys the measurement.

## Direct, not hypothetical

"How would you…" and "Show me how you would…" ask the participant to describe or
imagine. NN/g's task-writing guidance prefers a direct imperative: "Find…", "Book…",
"Get sign-off on…". The linter flags hypothetical wording as a warning. Tree tests are
exempt, because "where would you look for…" is how a tree-test task is normally asked.

## Dependencies

A task that depends on the output of an earlier task loses two data points when the
first one fails, and the failure is correlated rather than independent. Where a
dependency is unavoidable, set the state up in advance so the second task can be
attempted regardless.

Independent tasks also let you randomise task order across participants, which spreads
learning effects instead of piling them onto the later tasks.

## Success criteria

The participant needs to know when they are finished.

Moderated, a moderator can answer that live, so the task can end open. Unmoderated, no
one can, so the participant decides — and completion data becomes self-reported.

What that costs depends on the study type, so the severity does too:

| Study type | Moderated | Unmoderated |
|---|---|---|
| `quant` (you report completion rates) | critical | critical |
| `qual` (default) | warning | warning |
| `tree` | not checked: choosing a location is the end state | not checked |

Good endings: "let me know when you feel you're done", "keep going until you've sent
it", "stop when you can see the confirmation".

## Length

As a heuristic (not from the literature), above roughly 60 words a participant
re-reads the task rather than attempting it, and the re-reading shows up in your
time-on-task data. Cut the scenario to the reason and the goal.

## Sequence

"First do X, then do Y" prescribes an order. The order a participant chooses is
usually more informative than whether they finished.

"Do X and then Y" is usually two tasks in one. If the first part fails you cannot see
the second, and a single completion result covers both. Split it.

## What to check that this linter cannot

- **Is this a task anyone actually performs?** A well-formed task testing an
  imaginary workflow is still a wasted session.
- **Is the starting state right?** Tasks frequently assume an account state the
  participant will not have.
- **Do the tasks together cover the thing you are studying?** Coverage is a study
  design question, not a wording question.
- **Is the task achievable?** Piloting catches this. Nothing else does.

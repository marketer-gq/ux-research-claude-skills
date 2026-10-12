# Platform constraints worth checking before an import

This file is optional context. The skill works on files and does not need any platform
connected; this is here because an import plan is only as good as the destination's
ability to accept it, and these are the constraints that most often stop one.

The examples below are Great Question's. Replace them with your own destination's
constraints when you fork.

## Great Question, as of autumn 2026

This section is a snapshot. Re-verify against the live MCP and with the Great Question
team before telling a researcher something is impossible; any of these may have changed.

### Constraints

**Screeners are typed, not shared objects.**
Survey, interview and unmoderated studies each have their own screener create, get,
add-question, update-question and delete-question tools. There is no generic screener.
Moving a screener between study types is a re-create, and anything the target type does
not support has to be resolved by hand.

**No native screener copy or import.**
Great Question has no built-in way to copy a screener from one study to another or to
import one from another tool. This skill fills that gap.

**No matrix question type.**
Do not silently split a matrix question into several single-selects on import — the
analysis plan usually depends on the matrix shape. The `--target gq` plan leaves matrix
questions unresolved for a person to decide.

**"Other — please specify" cannot be filtered separately from its sub-answers.**
A researcher filtering on "Other" gets the free-text sub-answers folded in rather than
the parent option on its own. Treat "Other — please specify" as a question that produces
hard-to-filter data, and map it to an attribute only if you have a plan for cleaning the
free text afterwards — see the `panel-data-steward` skill.

**Attribute mappings and skip logic are not part of the screener read.**
The MCP screener read returns no attribute field, and no attribute or skip-logic
argument is documented for the screener write tools. The import plan lists both for
setting by hand in the app.

### Supported, and often assumed not to be

**"And" / "or" conditions in candidate filtering.**
Reported as supported in the app's candidate filters. Not verified through the MCP, whose
candidate search takes no attribute filter. See the `candidate-recruiter` skill.

**Screener templates.**
The account can hold screener templates that apply in one call. Check for a matching
template before walking an import plan question by question.

## The constraints worth checking for any destination

Whatever tool you are importing into, check these before building a plan:

1. **Which question types exist.** Matrix questions are the usual casualty.
2. **Whether screeners are typed** by study or survey kind, which makes a cross-type move a re-create rather than a copy.
3. **Whether attribute mappings can be set at import**, or only afterwards by hand.
4. **Whether templates exist** — applying one is cheaper and more consistent than adding questions individually.
5. **How "Other - please specify" behaves under filtering.** It is frequently not filterable separately from its sub-answers, which makes it a question that produces unusable data.
6. **Whether skip logic can be written at import**, or has to be rebuilt by hand.

## How to keep this current

Before relying on any line here, run the check with the researcher present and confirm
the constraint still bites. When one is fixed, delete it from this file rather than
leaving it marked "resolved" — a stale limitations list costs more trust than a short one.

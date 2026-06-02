# Speaker Attribution Review Prompt

Use this prompt to have Claude review a cleaned transcript for speaker misattribution.

---

## The Prompt

```
Review this interview transcript for speaker misattribution errors. Automated transcription often puts words in the wrong speaker's mouth.

Look for these patterns:

1. **Orphaned acknowledgments**: Short phrases like "okay", "thanks", "makes sense", "got it", "right", "yeah" at the END of a speaker's turn that don't logically follow what they just said. These are often the next speaker's response incorrectly merged.

2. **Misplaced questions**: Questions appearing in the participant's turn that sound like interviewer follow-ups (e.g., "What do you mean by that?" or "Can you tell me more?").

3. **Abrupt topic shifts**: A speaker's turn that suddenly pivots to a new topic mid-sentence - often indicates a missed speaker change.

4. **Fragmented sentences**: A turn that starts with a sentence fragment that would make sense as a continuation of the OTHER speaker's previous statement.

5. **Response-before-prompt**: An answer that doesn't match the question that preceded it, but would match a question that comes AFTER.

For each issue found:
- Quote the problematic passage
- Explain what seems wrong
- Provide the corrected version with proper speaker attribution

Here's the transcript to review:

[PASTE TRANSCRIPT HERE]
```

---

## Example Usage

**Input transcript with error:**
```
**Interviewer:** How did you find the onboarding process?

**Participant:** It was confusing at first. I didn't know where to click to get started. The button was hidden at the bottom and I almost gave up...yeah that's really helpful to know.

**Interviewer:** about the button placement. Were there other issues?
```

**Claude's response:**
```
I found a speaker misattribution error:

**Issue:** The phrase "yeah that's really helpful to know" at the end of Participant's turn is an acknowledgment that doesn't fit their narrative. It sounds like the Interviewer responding. Additionally, Interviewer's next turn starts with "about the button placement" which is a fragment continuing a thought.

**Corrected version:**

**Interviewer:** How did you find the onboarding process?

**Participant:** It was confusing at first. I didn't know where to click to get started. The button was hidden at the bottom and I almost gave up.

**Interviewer:** Yeah, that's really helpful to know about the button placement. Were there other issues?
```

---

## Tips for Best Results

1. **Review in sections**: For long transcripts (60+ min), review in 10-15 minute chunks for better accuracy

2. **Trust your instincts**: If Claude's fix doesn't sound right, reject it - you know your interview better

3. **Check critical quotes**: If you plan to use a specific quote in your analysis, double-check its attribution

4. **Note systematic errors**: Some transcription tools consistently misattribute at certain points (e.g., when speakers talk quickly or overlap) - watch for patterns

---

## Quick Version (for shorter transcripts)

```
Review this transcript for speaker misattribution. Look for acknowledgment phrases ("okay", "thanks", "makes sense") at the end of turns that don't fit, questions in the wrong speaker's turn, and sentence fragments that should belong to the other speaker. Flag issues and provide corrections.

[PASTE TRANSCRIPT]
```

---
name: transcript-cleaner
description: Transform messy interview and research transcripts into clean, analysis-ready documents. Use when a PM or researcher has raw transcripts from Otter, Fireflies, Zoom, Rev, Grain, or other recording tools that need cleaning before analysis. Handles speaker normalization, filler removal, timestamp cleanup, and structural formatting.
---

# Transcript Cleaner

Transforms raw transcripts into clean, structured documents ready for analysis.

## Quick Start

1. Place transcript file(s) in working directory
2. Run: `python scripts/clean_transcript.py input.txt -o cleaned.md`
3. Review output and adjust speaker names if needed

## What It Does

**Removes noise:**
- Filler words (um, uh, like, you know, sort of, kind of)
- False starts and repetitions
- Timestamps (configurable - can preserve if needed)
- Platform artifacts (Otter confidence markers, Zoom auto-caption formatting)

**Normalizes speakers:**
- Detects speaker labels across formats (Speaker 1, SPEAKER_1, John Smith, etc.)
- Consolidates inconsistent naming (maps "John", "John Smith", "JS" → single identifier)
- Prompts for speaker role mapping (Interviewer, Participant, Observer)

**Structures output:**
- Groups utterances into logical paragraphs by speaker
- Preserves natural conversation flow
- Adds clear speaker attribution
- Outputs markdown ready for analysis tools

## Usage Options

```bash
# Basic cleaning
python scripts/clean_transcript.py interview.txt

# Preserve timestamps
python scripts/clean_transcript.py interview.txt --keep-timestamps

# Batch process folder
python scripts/clean_transcript.py ./raw_transcripts/ -o ./cleaned/

# Specify output format
python scripts/clean_transcript.py interview.txt --format md|txt|json
```

## Supported Formats

The script auto-detects source format. See `references/format_patterns.md` for details on:
- Otter.ai exports
- Fireflies.ai exports  
- Zoom auto-captions (VTT)
- Rev transcripts
- Grain exports
- Generic speaker-labeled transcripts

## Output Template

Clean transcripts follow the structure in `assets/output_template.md`:
- Header with metadata (date, participants, duration if available)
- Speaker-attributed paragraphs
- Clear visual separation between speakers

## Speaker Attribution Review (Critical Step)

Automated transcription frequently misattributes speaker turns - putting words in the wrong person's mouth. This corrupts downstream analysis. After running the cleaning script, use Claude to review and fix speaker attribution.

**Run this review for any transcript you plan to analyze.**

### How to Review

After cleaning, paste the transcript and ask Claude to review using the prompt in `references/speaker_review_prompt.md`. 

Key patterns Claude looks for:
- **Orphaned acknowledgments**: "okay", "thanks", "makes sense", "got it", "right" at the end of a turn that don't fit the speaker's flow
- **Misplaced questions**: Questions appearing in the participant's turn that sound like interviewer follow-ups
- **Abrupt topic shifts**: Mid-turn pivots that suggest a speaker change was missed
- **Response-before-prompt**: Answers that appear before the question that prompted them

### Example Fix

**Before (misattributed):**
```
Speaker 2: I had to test it out. It took longer than expected, so I went past the trial and had to pay...okay thanks makes sense.
Speaker 1: that happened. What exactly took longer?
```

**After (corrected):**
```
Speaker 2: I had to test it out. It took longer than expected, so I went past the trial and had to pay.
Speaker 1: Okay, thanks, makes sense that that happened. What exactly took longer?
```

### Workflow

1. Run `clean_transcript.py` for mechanical cleaning
2. Review output for obvious issues
3. Ask Claude to review speaker attribution using the prompt
4. Accept/reject Claude's suggested fixes
5. Final transcript is analysis-ready

## When to Use

- Before coding/tagging interview data
- Before feeding transcripts to analysis tools
- When consolidating transcripts from multiple sources
- When preparing transcripts for team review

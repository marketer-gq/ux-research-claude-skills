# Transcript Format Patterns

Reference for identifying and handling different transcript sources.

## Otter.ai

**Identifying markers:**
- Timestamps in brackets: `[00:01:23]`
- Confidence percentages: `<87%>`
- Inaudible markers: `[inaudible 00:01:45]`

**Example raw format:**
```
[00:00:05] Speaker 1
So <92%> I was thinking about the product and um you know <87%> the main issue is...

[00:00:15] Speaker 2  
Right, right. I mean [inaudible 00:00:18] that's exactly what we found.
```

**Cleaning notes:**
- Remove timestamp brackets
- Remove confidence markers entirely
- Convert `[inaudible]` to `[unclear]` or remove

---

## Fireflies.ai

**Identifying markers:**
- Timestamps in parentheses: `(00:01)`
- Auto-generated sections: `Action Items:`, `Key Points:`, `Outline:`
- Speaker labels with timestamps

**Example raw format:**
```
John Smith (00:01)
Yeah so basically the problem we're seeing is that users, you know, they don't really understand the flow.

Action Items:
- Review user flow
- Schedule follow-up

Key Points:
- Users confused by flow
```

**Cleaning notes:**
- Remove auto-generated summary sections (or preserve separately)
- Clean timestamp markers
- Preserve speaker attribution

---

## Zoom Auto-Captions (VTT)

**Identifying markers:**
- `WEBVTT` header
- Timestamp ranges: `00:00:01.234 --> 00:00:05.678`
- Sequential numbering

**Example raw format:**
```
WEBVTT
Kind: captions
Language: en

1
00:00:01.200 --> 00:00:04.150
so um I think the main thing is

2
00:00:04.200 --> 00:00:07.890
that we need to like focus on the user

3
00:00:08.100 --> 00:00:11.450
John: yeah exactly that's what I was saying
```

**Cleaning notes:**
- VTT often lacks speaker attribution - may need manual addition
- Captions are fragmented by timing, not meaning - merge aggressively
- Quality varies significantly by audio quality

---

## Rev

**Identifying markers:**
- Timestamps in parentheses
- Crosstalk markers: `[crosstalk 00:01:23]`
- Inaudible with timestamps: `[inaudible 00:01:45]`
- Professional formatting with speaker names

**Example raw format:**
```
John Smith: (00:01)
The main challenge we're facing is around the onboarding flow. Users are getting stuck at the-

Jane Doe: (00:08)
[crosstalk 00:00:08] Right, exactly.

John Smith: (00:10)
-at the verification step specifically.
```

**Cleaning notes:**
- Higher quality than auto-captions
- Crosstalk markers indicate interruption points
- May need to merge split utterances

---

## Grain

**Identifying markers:**
- Simple timestamps on own line: `1:23`
- Speaker labels followed by text
- Generally cleaner format

**Example raw format:**
```
1:23
John
I think we should focus on the core experience first.

1:45
Sarah
Agreed. The um the data shows that's where users drop off.
```

**Cleaning notes:**
- Timestamps on separate lines
- Speaker names without colons
- Usually cleaner but still has fillers

---

## Supernormal

**Identifying markers:**
- Timestamps in brackets before speaker: `[0:00]` or `[00:00]`
- Speaker name followed by colon on same line as timestamp
- Link to Supernormal.com in header

**Example raw format:**
```
Mini interview transcript
Monday, June 17th @ 10:06 AM | View on Supernormal.com

[0:00] Interviewer: Hello. Oh, I don't hear you. You're muted.
[0:02] James F.: There you go.
[0:03] Interviewer: Yeah, there we go. All my notetakers.
[0:34] Interviewer: Yeah, so let's make this fast, okay. Pretend you're still a freelancer or just tell me about how your experience was before.
[0:51] James F.: I'd say ebb and flow like, you know, when it rains it pours and then other times having to scramble to make ends meet.
```

**Cleaning notes:**
- Timestamps are inline with speaker labels (unique format)
- Speaker names often include initials (e.g., "James F.")
- May have fragmented utterances due to rapid speaker changes
- Header line with date/time and Supernormal link should be skipped

---

## Generic Speaker-Labeled

**Common patterns:**
- `Speaker 1:` or `SPEAKER 1:`
- `[Speaker Name]`
- `Name:` followed by text
- Initials: `JS:`

**Example raw format:**
```
Interviewer: Can you tell me about your experience?

Participant: Yeah, so um basically I started using the product like three months ago and uh it was kind of confusing at first.

Interviewer: What was confusing specifically?
```

**Cleaning notes:**
- Most flexible format
- May need speaker role mapping (Interviewer → I, Participant → P)
- Check for consistency in speaker labels

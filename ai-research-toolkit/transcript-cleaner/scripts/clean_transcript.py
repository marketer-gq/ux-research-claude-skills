#!/usr/bin/env python3
"""
Transcript Cleaner - Transform messy transcripts into analysis-ready documents.

Supports: Otter.ai, Fireflies.ai, Zoom VTT, Rev, Grain, and generic formats.
"""

import argparse
import re
import os
import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Utterance:
    speaker: str
    text: str
    timestamp: Optional[str] = None


@dataclass
class CleanedTranscript:
    utterances: list[Utterance] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    speaker_map: dict = field(default_factory=dict)


# Filler words and phrases to remove
FILLER_PATTERNS = [
    r'\b(um|uh|er|ah|eh)\b',
    r'\b(you know)\b',
    r'\b(i mean)\b',
    r'\b(sort of|kind of)\b',
    r'\b(like)\b(?=\s+(?:I|you|he|she|it|we|they|the|a|an|this|that|there))',  # "like" before common words
    r'\b(basically)\b',
    r'\b(literally)\b',
    r'\b(actually)\b(?=,)',  # "actually" followed by comma
    r'\b(right)\b(?=\??\s*$)',  # trailing "right" or "right?"
]

# Platform-specific artifacts
PLATFORM_ARTIFACTS = {
    'otter': [
        r'\[\d+:\d+:\d+\]',  # Otter timestamps
        r'\(\d+:\d+\)',  # Alternative timestamp format
        r'<\d+%>',  # Confidence markers
        r'\[inaudible\s*\d*:\d*\]',
    ],
    'fireflies': [
        r'\(\d{2}:\d{2}\)',  # Fireflies timestamps
        r'\[\d{2}:\d{2}\]',
        r'Action Items:.*$',  # Fireflies auto-generated sections
        r'Key Points:.*$',
    ],
    'zoom': [
        r'^\d+$',  # VTT sequence numbers
        r'\d{2}:\d{2}:\d{2}\.\d{3} --> \d{2}:\d{2}:\d{2}\.\d{3}',  # VTT timestamps
        r'WEBVTT',
        r'Kind: captions',
        r'Language: \w+',
    ],
    'rev': [
        r'\(\d{2}:\d{2}\)',
        r'\[crosstalk \d{2}:\d{2}:\d{2}\]',
        r'\[inaudible \d{2}:\d{2}:\d{2}\]',
    ],
    'grain': [
        r'^\d{1,2}:\d{2}$',  # Simple timestamps on their own line
        r'\[\d{1,2}:\d{2}\]',
    ],
    'supernormal': [
        # Timestamps are handled in parsing, not as artifacts
    ],
}

# Speaker label patterns
SPEAKER_PATTERNS = [
    r'^(Speaker\s*\d+)\s*[:]\s*',  # Speaker 1:
    r'^(SPEAKER[_\s]*\d+)\s*[:]\s*',  # SPEAKER_1:
    r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*[:]\s*',  # John Smith:
    r'^([A-Z]{2,})\s*[:]\s*',  # JS: or JOHN:
    r'^\[([^\]]+)\]\s*',  # [Speaker Name]
    r'^(\w+):\s+',  # Generic name:
]


def detect_format(content: str) -> str:
    """Detect the transcript source format."""
    if 'WEBVTT' in content or '-->' in content:
        return 'zoom'
    if re.search(r'<\d+%>', content):
        return 'otter'
    if re.search(r'Action Items:', content) or re.search(r'Key Points:', content):
        return 'fireflies'
    if re.search(r'\[crosstalk', content):
        return 'rev'
    # Supernormal format: [0:00] Speaker: or [00:00] Speaker:
    if re.search(r'^\[\d{1,2}:\d{2}\]\s*\w+.*:', content, re.MULTILINE):
        return 'supernormal'
    if re.search(r'Supernormal\.com', content, re.IGNORECASE):
        return 'supernormal'
    if re.search(r'^\d{1,2}:\d{2}$', content, re.MULTILINE):
        return 'grain'
    return 'generic'


def remove_fillers(text: str) -> str:
    """Remove filler words and phrases."""
    result = text
    for pattern in FILLER_PATTERNS:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    # Clean up extra spaces
    result = re.sub(r'\s+', ' ', result)
    result = re.sub(r'\s+([.,!?])', r'\1', result)
    # Clean up multiple commas/punctuation
    result = re.sub(r',\s*,+', ',', result)
    result = re.sub(r',\s+,', ',', result)
    # Clean up comma at start of sentence
    result = re.sub(r'^\s*,\s*', '', result)
    result = re.sub(r'\.\s*,', '.', result)
    return result.strip()


def remove_platform_artifacts(text: str, platform: str) -> str:
    """Remove platform-specific artifacts."""
    result = text
    patterns = PLATFORM_ARTIFACTS.get(platform, [])
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.MULTILINE)
    return result.strip()


def extract_speaker(line: str) -> tuple[Optional[str], str]:
    """Extract speaker name from line if present."""
    for pattern in SPEAKER_PATTERNS:
        match = re.match(pattern, line)
        if match:
            speaker = match.group(1).strip()
            text = line[match.end():].strip()
            return speaker, text
    return None, line


def normalize_speaker(speaker: str, speaker_map: dict) -> str:
    """Normalize speaker names to consistent identifiers."""
    # Check if we've seen a variant of this speaker
    speaker_lower = speaker.lower().strip()
    
    for canonical, variants in speaker_map.items():
        if speaker_lower in [v.lower() for v in variants]:
            return canonical
    
    # If not found, this is a new speaker
    return speaker


def clean_false_starts(text: str) -> str:
    """Remove false starts and repetitions."""
    # Pattern: word repeated immediately (I I, the the, etc.)
    text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    # Pattern: contraction repeated (It's it's, Let's let's)
    text = re.sub(r"\b(\w+'\w+)\s+\1\b", r'\1', text, flags=re.IGNORECASE)
    # Pattern: "I was going to-- I think" -> "I think"
    text = re.sub(r'[^.!?]*--\s*', '', text)
    return text.strip()


def parse_supernormal(content: str, keep_timestamps: bool = False) -> CleanedTranscript:
    """Parse Supernormal format: [0:00] Speaker Name: text"""
    result = CleanedTranscript()
    result.metadata['source_format'] = 'supernormal'

    lines = content.split('\n')
    current_speaker = None
    current_text = []
    current_timestamp = None

    # Pattern: [0:00] Speaker Name: text  or  [00:00] Speaker Name: text
    supernormal_pattern = re.compile(r'^\[(\d{1,2}:\d{2})\]\s*([^:]+):\s*(.*)$')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Skip header lines
        if 'Supernormal.com' in line or line.startswith('View on'):
            continue

        match = supernormal_pattern.match(line)
        if match:
            timestamp, speaker, text = match.groups()
            speaker = speaker.strip()
            text = text.strip()

            # Save previous utterance if speaker changed
            if current_speaker and current_speaker != speaker and current_text:
                combined = ' '.join(current_text)
                combined = remove_fillers(combined)
                combined = clean_false_starts(combined)
                if combined:
                    result.utterances.append(Utterance(
                        speaker=current_speaker,
                        text=combined,
                        timestamp=current_timestamp if keep_timestamps else None
                    ))
                current_text = []

            # If same speaker, just append text
            if current_speaker == speaker:
                if text:
                    current_text.append(text)
            else:
                # New speaker
                current_speaker = speaker
                current_timestamp = timestamp
                current_text = [text] if text else []

                # Track speaker
                if speaker not in result.speaker_map:
                    result.speaker_map[speaker] = [speaker]
        else:
            # Continuation line (no timestamp/speaker prefix)
            if current_speaker and line:
                current_text.append(line)

    # Don't forget last utterance
    if current_speaker and current_text:
        combined = ' '.join(current_text)
        combined = remove_fillers(combined)
        combined = clean_false_starts(combined)
        if combined:
            result.utterances.append(Utterance(
                speaker=current_speaker,
                text=combined,
                timestamp=current_timestamp if keep_timestamps else None
            ))

    return result


def parse_transcript(content: str, platform: str, keep_timestamps: bool = False) -> CleanedTranscript:
    """Parse raw transcript into structured utterances."""
    # Use specialized parser for Supernormal
    if platform == 'supernormal':
        return parse_supernormal(content, keep_timestamps)

    result = CleanedTranscript()
    result.metadata['source_format'] = platform

    # Remove platform artifacts
    content = remove_platform_artifacts(content, platform)

    lines = content.split('\n')
    current_speaker = None
    current_text = []
    pending_speaker = None  # For formats where speaker is on own line

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check if this line is JUST a speaker label (common in Otter, Grain)
        # Pattern: "Speaker 1" or "John Smith" alone on a line
        standalone_speaker = re.match(r'^(Speaker\s*\d+|[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)$', line)
        if standalone_speaker:
            # Save previous utterance before switching
            if current_speaker and current_text:
                combined = ' '.join(current_text)
                combined = remove_fillers(combined)
                combined = clean_false_starts(combined)
                if combined:
                    result.utterances.append(Utterance(
                        speaker=current_speaker,
                        text=combined
                    ))
                current_text = []

            current_speaker = standalone_speaker.group(1)
            if current_speaker not in result.speaker_map:
                result.speaker_map[current_speaker] = [current_speaker]
            continue

        # Try to extract speaker from line with colon format
        speaker, text = extract_speaker(line)

        if speaker:
            # Save previous utterance
            if current_speaker and current_text:
                combined = ' '.join(current_text)
                combined = remove_fillers(combined)
                combined = clean_false_starts(combined)
                if combined:
                    result.utterances.append(Utterance(
                        speaker=current_speaker,
                        text=combined
                    ))

            current_speaker = speaker
            current_text = [text] if text else []

            # Track speaker
            if speaker not in result.speaker_map:
                result.speaker_map[speaker] = [speaker]
        else:
            # Continuation of current speaker
            if line:
                current_text.append(line)

    # Don't forget last utterance
    if current_speaker and current_text:
        combined = ' '.join(current_text)
        combined = remove_fillers(combined)
        combined = clean_false_starts(combined)
        if combined:
            result.utterances.append(Utterance(
                speaker=current_speaker,
                text=combined
            ))

    return result


def merge_consecutive_utterances(transcript: CleanedTranscript) -> CleanedTranscript:
    """Merge consecutive utterances from the same speaker."""
    if not transcript.utterances:
        return transcript
    
    merged = CleanedTranscript()
    merged.metadata = transcript.metadata
    merged.speaker_map = transcript.speaker_map
    
    current = transcript.utterances[0]
    
    for utterance in transcript.utterances[1:]:
        if utterance.speaker == current.speaker:
            current.text = f"{current.text} {utterance.text}"
        else:
            merged.utterances.append(current)
            current = utterance
    
    merged.utterances.append(current)
    return merged


def format_output(transcript: CleanedTranscript, format: str = 'md') -> str:
    """Format cleaned transcript for output."""
    if format == 'json':
        return json.dumps({
            'metadata': transcript.metadata,
            'speakers': list(transcript.speaker_map.keys()),
            'utterances': [
                {'speaker': u.speaker, 'text': u.text}
                for u in transcript.utterances
            ]
        }, indent=2)
    
    # Markdown/text format
    lines = []
    lines.append('# Interview Transcript')
    lines.append('')
    
    if transcript.metadata:
        lines.append('## Metadata')
        for key, value in transcript.metadata.items():
            lines.append(f'- **{key}**: {value}')
        lines.append('')
    
    if transcript.speaker_map:
        lines.append('## Participants')
        for speaker in transcript.speaker_map.keys():
            lines.append(f'- {speaker}')
        lines.append('')
    
    lines.append('## Transcript')
    lines.append('')
    
    for utterance in transcript.utterances:
        lines.append(f'**{utterance.speaker}:** {utterance.text}')
        lines.append('')
    
    return '\n'.join(lines)


def process_file(input_path: str, output_path: Optional[str] = None, 
                 keep_timestamps: bool = False, format: str = 'md') -> str:
    """Process a single transcript file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Detect format
    platform = detect_format(content)
    print(f"Detected format: {platform}")
    
    # Parse and clean
    transcript = parse_transcript(content, platform, keep_timestamps)
    transcript = merge_consecutive_utterances(transcript)
    
    # Format output
    output = format_output(transcript, format)
    
    # Determine output path
    if not output_path:
        input_p = Path(input_path)
        ext = 'json' if format == 'json' else 'md'
        output_path = str(input_p.with_suffix(f'.cleaned.{ext}'))
    
    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(output)
    
    print(f"Cleaned transcript saved to: {output_path}")
    print(f"Speakers found: {list(transcript.speaker_map.keys())}")
    print(f"Utterances: {len(transcript.utterances)}")
    
    return output_path


def process_directory(input_dir: str, output_dir: Optional[str] = None,
                      keep_timestamps: bool = False, format: str = 'md') -> list[str]:
    """Process all transcript files in a directory."""
    input_path = Path(input_dir)
    output_path = Path(output_dir) if output_dir else input_path / 'cleaned'
    output_path.mkdir(exist_ok=True)
    
    processed = []
    extensions = ['.txt', '.vtt', '.srt', '.md']
    
    for file in input_path.iterdir():
        if file.suffix.lower() in extensions:
            out_file = output_path / f"{file.stem}.cleaned.{'json' if format == 'json' else 'md'}"
            process_file(str(file), str(out_file), keep_timestamps, format)
            processed.append(str(out_file))
    
    return processed


def main():
    parser = argparse.ArgumentParser(
        description='Clean and structure interview transcripts for analysis.'
    )
    parser.add_argument('input', help='Input transcript file or directory')
    parser.add_argument('-o', '--output', help='Output file or directory')
    parser.add_argument('--keep-timestamps', action='store_true',
                        help='Preserve timestamps in output')
    parser.add_argument('--format', choices=['md', 'txt', 'json'], default='md',
                        help='Output format (default: md)')
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_dir():
        process_directory(args.input, args.output, args.keep_timestamps, args.format)
    else:
        process_file(args.input, args.output, args.keep_timestamps, args.format)


if __name__ == '__main__':
    main()

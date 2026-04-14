#!/usr/bin/env python3
"""
Transcriber — converts audio to timestamped text.
Supports: pre-recorded WAV files, or raw text transcript input.
Whisper integration when available (faster-whisper or openai-whisper).

For MVP: accepts text transcripts directly. Audio support added when whisper is installed.
MOCHA Sprint — Apr 4, 2026
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional


def transcribe_audio(audio_path: str) -> List[Dict]:
    """Transcribe audio file using faster-whisper or openai-whisper."""
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path)
        return [
            {"start": s.start, "end": s.end, "text": s.text.strip(), "speaker": "Speaker"}
            for s in segments
        ]
    except ImportError:
        pass

    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(audio_path)
        return [
            {"start": s["start"], "end": s["end"], "text": s["text"].strip(), "speaker": "Speaker"}
            for s in result["segments"]
        ]
    except ImportError:
        pass

    raise RuntimeError(
        "No whisper library available. Install faster-whisper or openai-whisper, "
        "or use --text to provide a transcript directly."
    )


def load_text_transcript(text_path: str) -> List[Dict]:
    """Load a plain text transcript. Each line becomes a segment."""
    path = Path(text_path)
    content = path.read_text()
    segments = []
    for i, line in enumerate(content.strip().split('\n')):
        line = line.strip()
        if not line:
            continue
        # Try to parse "Speaker: text" format
        if ':' in line and len(line.split(':')[0]) < 30:
            speaker, text = line.split(':', 1)
            segments.append({
                "start": i * 30.0,  # approximate 30s per line
                "end": (i + 1) * 30.0,
                "text": text.strip(),
                "speaker": speaker.strip(),
            })
        else:
            segments.append({
                "start": i * 30.0,
                "end": (i + 1) * 30.0,
                "text": line,
                "speaker": "Speaker",
            })
    return segments


def format_timestamp(seconds: float) -> str:
    """Format seconds as MM:SS."""
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def get_full_transcript_text(segments: List[Dict]) -> str:
    """Combine all segments into a single text block for LLM input."""
    lines = []
    for s in segments:
        ts = format_timestamp(s["start"])
        speaker = s.get("speaker", "Speaker")
        lines.append(f"[{ts}] {speaker}: {s['text']}")
    return "\n".join(lines)

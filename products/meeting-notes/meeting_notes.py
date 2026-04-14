#!/usr/bin/env python3
"""
Meeting Notes Extractor — "What Did We Decide?"
Main CLI runner. Transcribes audio or processes text, extracts intelligence, generates report.

Usage:
    python3 meeting_notes.py --text transcript.txt           # Process text transcript
    python3 meeting_notes.py --file meeting.wav              # Transcribe audio + extract
    python3 meeting_notes.py --text transcript.txt --no-llm  # Transcript only, skip extraction
    python3 meeting_notes.py --text transcript.txt --output notes.html

MOCHA Sprint — Apr 4, 2026
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from transcriber import transcribe_audio, load_text_transcript, get_full_transcript_text, format_timestamp
from extractor import extract_meeting_intelligence, extract_without_llm


def generate_html_report(extraction: dict, transcript_text: str, output_path: str):
    """Generate single-file HTML meeting notes report."""

    summary = extraction.get("summary", "No summary available.")
    decisions = extraction.get("decisions", [])
    actions = extraction.get("action_items", [])
    topics = extraction.get("key_topics", [])
    followups = extraction.get("follow_ups", [])
    participants = extraction.get("participants", [])

    decisions_html = ""
    for d in decisions:
        decisions_html += f'''<div class="decision">
  <strong>{d.get("decision","")}</strong>
  <span class="meta">by {d.get("decided_by","?")} at {d.get("timestamp","?")}</span>
</div>\n'''

    actions_html = ""
    for a in actions:
        actions_html += f'''<div class="action">
  <span class="checkbox">☐</span>
  <div>
    <strong>{a.get("task","")}</strong>
    <span class="meta">{a.get("assigned_to","?")} — deadline: {a.get("deadline","not specified")}</span>
  </div>
</div>\n'''

    topics_html = ""
    for t in topics:
        sentiment_color = {"positive":"#68d391","negative":"#fc8181","mixed":"#f6ad55"}.get(t.get("sentiment",""),"#a0aec0")
        topics_html += f'''<div class="topic">
  <span class="topic-name">{t.get("topic","")}</span>
  <span class="topic-meta" style="color:{sentiment_color}">{t.get("sentiment","neutral")} · {t.get("duration_estimate","?")}</span>
</div>\n'''

    followups_html = "\n".join(f'<li>{f}</li>' for f in followups) if followups else "<li>None identified</li>"
    participants_html = ", ".join(participants) if participants else "Unknown"

    # Collapsible transcript
    transcript_escaped = transcript_text.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Meeting Notes — {datetime.now().strftime("%Y-%m-%d %H:%M")}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  :root{{--navy:#1a365d;--charcoal:#2d3748;--gold:#d4a843;--teal:#4fd1c5;--text:#e2e8f0;--muted:#a0aec0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--charcoal);color:var(--text);line-height:1.6}}
  a{{color:var(--teal);text-decoration:none}}
  .header{{background:var(--navy);padding:2rem;text-align:center;border-bottom:2px solid var(--gold)}}
  .header h1{{color:var(--gold);font-size:1.5rem}}
  .header .meta{{color:var(--muted);font-size:0.8rem;margin-top:0.3rem}}
  .content{{max-width:800px;margin:0 auto;padding:1rem}}
  .section-title{{color:var(--gold);font-weight:600;font-size:1.1rem;margin:1.5rem 0 0.5rem;padding-bottom:0.3rem;border-bottom:1px solid rgba(212,168,67,0.3)}}
  .summary{{background:rgba(26,54,93,0.4);padding:1rem;border-radius:8px;margin:0.5rem 0;font-size:0.9rem}}
  .decision{{background:rgba(26,54,93,0.6);border-left:3px solid var(--gold);padding:0.8rem;margin:0.4rem 0;border-radius:0 6px 6px 0}}
  .action{{display:flex;gap:0.8rem;align-items:flex-start;background:rgba(26,54,93,0.4);padding:0.8rem;margin:0.4rem 0;border-radius:6px}}
  .checkbox{{font-size:1.2rem;color:var(--teal)}}
  .topic{{display:flex;justify-content:space-between;padding:0.6rem 0.8rem;margin:0.3rem 0;background:rgba(26,54,93,0.3);border-radius:6px}}
  .topic-name{{font-weight:600}}
  .topic-meta{{font-size:0.8rem}}
  .meta{{color:var(--muted);font-size:0.8rem;display:block;margin-top:0.2rem}}
  .followups{{list-style:none;padding:0}}
  .followups li{{padding:0.4rem 0;border-bottom:1px solid rgba(255,255,255,0.05)}}
  .followups li:before{{content:"→ ";color:var(--teal)}}
  details{{margin:1rem 0}}
  summary{{cursor:pointer;color:var(--teal);font-weight:600;padding:0.5rem 0}}
  .transcript{{background:rgba(0,0,0,0.3);padding:1rem;border-radius:8px;font-size:0.8rem;white-space:pre-wrap;max-height:400px;overflow-y:auto;font-family:monospace}}
  .footer{{text-align:center;padding:2rem;color:var(--muted);font-size:0.8rem}}
</style>
</head>
<body>
<div class="header">
  <h1>Meeting Notes</h1>
  <div class="meta">{datetime.now().strftime("%A, %B %d, %Y at %H:%M")} · Participants: {participants_html}</div>
</div>
<div class="content">
  <div class="section-title">Summary</div>
  <div class="summary">{summary}</div>

  <div class="section-title">Decisions ({len(decisions)})</div>
  {decisions_html if decisions else '<div class="summary">No decisions identified.</div>'}

  <div class="section-title">Action Items ({len(actions)})</div>
  {actions_html if actions else '<div class="summary">No action items identified.</div>'}

  <div class="section-title">Key Topics</div>
  {topics_html if topics else '<div class="summary">No topics extracted.</div>'}

  <div class="section-title">Follow-ups</div>
  <ul class="followups">{followups_html}</ul>

  <details>
    <summary>Full Transcript ({len(transcript_text.split(chr(10)))} lines)</summary>
    <div class="transcript">{transcript_escaped}</div>
  </details>
</div>
<div class="footer">
  <p>Generated by <a href="https://ganuda.us">Meeting Notes Extractor</a> — your audio stays on your machine</p>
  <p>Cherokee AI Federation | For Seven Generations</p>
</div>
</body>
</html>'''

    Path(output_path).write_text(html)
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Meeting Notes Extractor — What Did We Decide?")
    parser.add_argument("--file", help="Audio file to transcribe (WAV, MP3)")
    parser.add_argument("--text", help="Text transcript file to process")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM extraction")
    parser.add_argument("--output", default=None, help="Output HTML path")
    parser.add_argument("--json", action="store_true", help="JSON output to stdout")
    args = parser.parse_args()

    if not args.file and not args.text:
        print("Error: provide --file (audio) or --text (transcript)")
        sys.exit(1)

    # Get transcript
    if args.text:
        print(f"Loading transcript from {args.text}...")
        segments = load_text_transcript(args.text)
    else:
        print(f"Transcribing {args.file}...")
        segments = transcribe_audio(args.file)

    transcript_text = get_full_transcript_text(segments)
    print(f"Transcript: {len(segments)} segments, {len(transcript_text)} chars")

    # Extract intelligence
    if args.no_llm:
        print("Skipping LLM extraction (--no-llm)")
        extraction = extract_without_llm(transcript_text)
    else:
        print("Extracting meeting intelligence via LLM...")
        extraction = extract_meeting_intelligence(transcript_text)
        if "error" in extraction:
            print(f"LLM extraction failed: {extraction['error']}")
            print("Falling back to basic extraction")
            extraction = extract_without_llm(transcript_text)

    # Output
    if args.json:
        extraction["transcript"] = transcript_text
        print(json.dumps(extraction, indent=2, default=str))
    else:
        output = args.output or f"meeting-notes-{datetime.now().strftime('%Y-%m-%d-%H%M')}.html"
        generate_html_report(extraction, transcript_text, output)
        d = len(extraction.get("decisions", []))
        a = len(extraction.get("action_items", []))
        t = len(extraction.get("key_topics", []))
        print(f"\nReport saved to: {output}")
        print(f"  Decisions: {d} | Action items: {a} | Topics: {t}")


if __name__ == '__main__':
    main()

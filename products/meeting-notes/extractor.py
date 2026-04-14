#!/usr/bin/env python3
"""
Extractor — sends transcript to local vLLM, extracts structured meeting intelligence.
Decisions, action items, topics, follow-ups.
MOCHA Sprint — Apr 4, 2026
"""

import json
import requests
from typing import Dict

VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "/ganuda/models/qwen2.5-72b-instruct-awq"

SYSTEM_PROMPT = """You are a meeting notes analyst. Given a meeting transcript, extract structured information.

Return ONLY valid JSON with no extra text:
{
  "summary": "2-3 paragraph summary of the meeting",
  "decisions": [
    {"decision": "what was decided", "decided_by": "who", "timestamp": "MM:SS"}
  ],
  "action_items": [
    {"task": "what needs to be done", "assigned_to": "who", "deadline": "when if mentioned", "timestamp": "MM:SS"}
  ],
  "key_topics": [
    {"topic": "topic name", "duration_estimate": "how long discussed", "sentiment": "positive/neutral/negative/mixed"}
  ],
  "follow_ups": ["next steps mentioned"],
  "participants": ["list of speakers detected"]
}

Rules:
- Extract EVERY decision, even small ones
- Extract EVERY action item with the clearest assignee you can identify
- If no deadline is mentioned, set deadline to "not specified"
- Timestamp should reference when in the transcript the item was discussed
- Be specific in the summary — names, numbers, concrete details
- Sentiment for topics should reflect the tone of discussion"""


def extract_meeting_intelligence(transcript_text: str) -> Dict:
    """Send transcript to local vLLM for structured extraction."""

    user_prompt = f"""Analyze this meeting transcript and extract all decisions, action items, key topics, and follow-ups.

TRANSCRIPT:
{transcript_text[:12000]}

Return the JSON extraction."""

    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.1,
                "max_tokens": 2000,
            },
            timeout=60
        )

        if response.status_code != 200:
            return {"error": f"vLLM returned {response.status_code}"}

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        # Extract JSON from response
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        return json.loads(content)

    except json.JSONDecodeError as e:
        return {"error": f"JSON parse failed: {e}", "_raw": content if 'content' in dir() else ""}
    except Exception as e:
        return {"error": str(e)}


def extract_without_llm(transcript_text: str) -> Dict:
    """Basic extraction without LLM — just structure the transcript."""
    lines = transcript_text.strip().split('\n')
    participants = set()
    for line in lines:
        if ':' in line and ']' in line:
            speaker = line.split(']')[1].split(':')[0].strip() if ']' in line else ""
            if speaker:
                participants.add(speaker)

    return {
        "summary": f"Meeting transcript with {len(lines)} exchanges from {len(participants)} participants.",
        "decisions": [],
        "action_items": [],
        "key_topics": [{"topic": "Full transcript available below", "duration_estimate": "full meeting", "sentiment": "neutral"}],
        "follow_ups": [],
        "participants": list(participants),
        "_note": "LLM extraction not available. Full transcript provided for manual review."
    }

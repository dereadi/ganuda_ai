#!/usr/bin/env python3
"""
Subscription Trimmer — LLM Classifier
Sends email signals to local vLLM for structured extraction.
Uses OpenAI-compatible API on localhost:8000 (Qwen2.5-72B).

MOCHA Sprint — Apr 2, 2026
"""

import json
import requests
from typing import List, Dict, Any


VLLM_URL = "http://localhost:8000/v1/chat/completions"
MODEL_NAME = "/ganuda/models/qwen2.5-72b-instruct-awq"

SYSTEM_PROMPT = """You are a subscription analyzer. Given an email signal (from, subject, date, snippet, amounts found), extract subscription information.

Return ONLY valid JSON with no extra text:
{
  "is_subscription": true or false,
  "service_name": "Human-readable service name (e.g. 'Claude Pro', 'Slack Pro', 'Apple iCloud')",
  "amount": 0.00,
  "currency": "USD",
  "frequency": "monthly",
  "charge_date": "YYYY-MM-DD",
  "category": "one of: ai_tools, cloud, productivity, entertainment, insurance, utilities, finance, fitness, news, shopping, other",
  "confidence": 0.0 to 1.0
}

Rules:
- If amounts_found has values, use the most likely charge amount (ignore tax, ignore totals)
- Frequency: infer from how often this sender appears or from context (monthly, annual, quarterly, weekly, one-time)
- Set is_subscription=false for: one-time purchases, marketing emails, income/payments received, declined transactions
- Set is_subscription=true for: recurring charges, auto-renewals, subscription receipts, failed recurring payments
- A failed payment for a subscription IS still a subscription (they'll try again)
- service_name should be the human-readable brand name, not the email domain"""


def classify_email(email_signal: Dict[str, Any]) -> Dict[str, Any]:
    """Classify a single email signal using local vLLM."""

    user_prompt = f"""Analyze this email signal:
From: {email_signal.get('from', '')}
Subject: {email_signal.get('subject', '')}
Date: {email_signal.get('date', '')}
Snippet: {email_signal.get('snippet', '')[:300]}
Amounts found: {email_signal.get('amounts_found', [])}
Sender domain: {email_signal.get('domain', '')}

Return the JSON classification."""

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
                "max_tokens": 300,
            },
            timeout=30
        )

        if response.status_code != 200:
            return {"is_subscription": False, "error": f"vLLM returned {response.status_code}"}

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        # Extract JSON from response (handle markdown code blocks)
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0].strip()
        elif '```' in content:
            content = content.split('```')[1].split('```')[0].strip()

        parsed = json.loads(content)

        # Carry forward the original email metadata
        parsed['_source_domain'] = email_signal.get('domain', '')
        parsed['_source_subject'] = email_signal.get('subject', '')
        parsed['_source_from'] = email_signal.get('from', '')

        return parsed

    except json.JSONDecodeError as e:
        return {
            "is_subscription": False,
            "error": f"JSON parse failed: {e}",
            "_raw_response": content if 'content' in dir() else ''
        }
    except Exception as e:
        return {"is_subscription": False, "error": str(e)}


def classify_batch(signals: List[Dict[str, Any]], verbose: bool = False) -> List[Dict[str, Any]]:
    """Classify a batch of email signals. Returns only confirmed subscriptions."""
    results = []
    for i, signal in enumerate(signals):
        if verbose:
            print(f"  [{i+1}/{len(signals)}] {signal.get('domain', '?')}: {signal.get('subject', '?')[:50]}")

        classified = classify_email(signal)
        results.append(classified)

        if verbose and classified.get('is_subscription'):
            print(f"    → {classified.get('service_name', '?')} | ${classified.get('amount', 0):.2f}/{classified.get('frequency', '?')}")

    subscriptions = [r for r in results if r.get('is_subscription')]
    errors = [r for r in results if r.get('error')]

    if verbose:
        print(f"\nClassified: {len(results)} total, {len(subscriptions)} subscriptions, {len(errors)} errors")

    return results


if __name__ == '__main__':
    # Test with sample data
    test_signal = {
        'from': 'Anthropic <noreply@mail.anthropic.com>',
        'domain': 'mail.anthropic.com',
        'subject': 'Your receipt from Anthropic, PBC #2823-2062-3274',
        'date': 'Sun, 8 Mar 2026',
        'snippet': 'Your receipt from Anthropic. Amount: $20.00. Plan: Claude Pro.',
        'amounts_found': ['$20.00'],
    }

    print("Testing classifier with Anthropic receipt...")
    result = classify_email(test_signal)
    print(json.dumps(result, indent=2))

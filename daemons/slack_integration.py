# /ganuda/daemons/slack_integration.py

import os
import requests
from typing import Dict, Optional

SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')

def notify_council_vote(vote_hash: str, topic: str, result: str, confidence: float) -> None:
    """
    Sends a Slack notification about a council vote.

    :param vote_hash: The unique hash of the vote.
    :param topic: The topic of the vote.
    :param result: The result of the vote (e.g., 'pass', 'fail').
    :param confidence: The confidence level of the vote result.
    """
    if not SLACK_WEBHOOK_URL:
        raise ValueError("SLACK_WEBHOOK_URL environment variable is not set")

    payload: Dict[str, str] = {
        "text": f"Council Vote:\n"
                f"Vote Hash: {vote_hash}\n"
                f"Topic: {topic}\n"
                f"Result: {result}\n"
                f"Confidence: {confidence:.2f}"
    }

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to send Slack notification: {e}")
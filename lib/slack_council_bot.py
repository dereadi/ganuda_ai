"""
Slack Council Discussion Bot — The Living Organism, Visible

Routes council deliberations through Slack in real-time so the tribe
can watch specialists think, argue, and reach consensus.

Usage:
    from lib.slack_council_bot import council_discuss

    # Ask the council a question, deliberation streams to Slack
    result = council_discuss("Should we open-source the governance layer?")

    # Quiet mode — vote happens, only the result posts to Slack
    result = council_discuss("Routine health check approval", quiet=True)

Leaders Meeting #1 (bb75fd4e3a693335), Mar 10 2026.
"The organism made visible" — Chief.
"""

import sys
import time
import logging
from datetime import datetime
from typing import Optional
from zoneinfo import ZoneInfo

if '/ganuda/lib' not in sys.path:
    sys.path.insert(0, '/ganuda/lib')
if '/ganuda' not in sys.path:
    sys.path.insert(0, '/ganuda')

from slack_federation import send, send_blocks, CHANNELS

logger = logging.getLogger("ganuda.slack_council_bot")
_TZ = ZoneInfo("America/Chicago")

# Specialist display config
SPECIALIST_EMOJI = {
    "raven": ":raven:",
    "turtle": ":turtle:",
    "coyote": ":wolf:",         # no coyote emoji, wolf is close
    "crawdad": ":lobster:",     # close enough
    "eagle_eye": ":eagle:",
    "spider": ":spider_web:",
    "gecko": ":lizard:",
    "peace_chief": ":peace_symbol:",
    "deer": ":deer:",
    "crane": ":crane:",
}

SPECIALIST_TITLE = {
    "raven": "Raven (War Chief)",
    "turtle": "Turtle (Seven Generations)",
    "coyote": "Coyote (Truth-Teller)",
    "crawdad": "Crawdad (Security)",
    "eagle_eye": "Eagle Eye (Observer)",
    "spider": "Spider (Integration)",
    "gecko": "Gecko (Performance)",
    "peace_chief": "Peace Chief (Consensus)",
    "deer": "Deer (Market/Business)",
    "crane": "Crane (Governance)",
}


def _post_question(question: str, channel: str = "council-votes") -> bool:
    """Post the opening question to Slack."""
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":fire: Council Session Convened",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Question before the Council:*\n>{question}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Specialists deliberating... | {datetime.now(_TZ).strftime('%H:%M CT')}",
                },
            ],
        },
    ]
    return send_blocks(channel, blocks, text_fallback=f"Council Session: {question[:100]}", urgent=True)


def _post_specialist_voice(
    specialist_id: str,
    response_text: str,
    has_concern: bool,
    channel: str = "council-votes",
) -> bool:
    """Post a single specialist's deliberation to Slack."""
    emoji = SPECIALIST_EMOJI.get(specialist_id, ":speech_balloon:")
    title = SPECIALIST_TITLE.get(specialist_id, specialist_id.title())
    concern_flag = "  :warning: *CONCERN*" if has_concern else ""

    # Truncate long responses for readability
    display_text = response_text[:500]
    if len(response_text) > 500:
        display_text += "..."

    text = f"{emoji} *{title}*{concern_flag}\n{display_text}"
    return send(channel, text, urgent=True)


def _post_verdict(
    recommendation: str,
    confidence: float,
    concerns: list,
    audit_hash: str,
    num_responses: int,
    channel: str = "council-votes",
) -> bool:
    """Post the final council verdict to Slack."""
    conf_pct = f"{confidence * 100:.1f}%"
    concern_count = len(concerns) if concerns else 0

    # Color-code by confidence
    if confidence >= 0.7:
        verdict_emoji = ":white_check_mark:"
    elif confidence >= 0.4:
        verdict_emoji = ":warning:"
    else:
        verdict_emoji = ":octagonal_sign:"

    blocks = [
        {"type": "divider"},
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{verdict_emoji} Council Verdict",
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Confidence:*\n{conf_pct}"},
                {"type": "mrkdwn", "text": f"*Concerns:*\n{concern_count} of {num_responses}"},
                {"type": "mrkdwn", "text": f"*Hash:*\n`{audit_hash}`"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Recommendation:*\n{recommendation[:800]}",
            },
        },
    ]

    if concerns:
        concern_text = "\n".join(f"• {c[:200]}" for c in concerns[:5])
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Concerns Raised:*\n{concern_text}",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": f"Cherokee AI Federation Council | {datetime.now(_TZ).strftime('%Y-%m-%d %H:%M CT')}",
            },
        ],
    })

    return send_blocks(
        channel, blocks,
        text_fallback=f"Council Verdict: {recommendation[:100]} (conf: {conf_pct})",
        urgent=True,
    )


def council_discuss(
    question: str,
    channel: str = "council-votes",
    quiet: bool = False,
    stream_delay: float = 0.5,
    max_tokens: int = 150,
) -> dict:
    """
    Run a council vote and stream the deliberation to Slack.

    Args:
        question: The question for the council.
        channel: Slack channel to post to (default: council-votes).
        quiet: If True, only post the final verdict (no individual voices).
        stream_delay: Seconds between posting each specialist's voice.
        max_tokens: Max tokens per specialist response.

    Returns:
        The council vote result dict.
    """
    from lib.specialist_council import council_vote

    # Post the opening question
    _post_question(question, channel)

    # Run the council vote
    result = council_vote(question, max_tokens=max_tokens, include_responses=True)

    # Stream each specialist's voice to Slack
    if not quiet and result.get("responses"):
        for resp in result["responses"]:
            _post_specialist_voice(
                specialist_id=resp.get("name", "unknown").lower().replace(" ", "_"),
                response_text=resp.get("response", ""),
                has_concern=resp.get("has_concern", False),
                channel=channel,
            )
            time.sleep(stream_delay)  # Pacing — don't flood the channel

    # Post the verdict
    _post_verdict(
        recommendation=result.get("recommendation", "No recommendation"),
        confidence=result.get("confidence", 0.0),
        concerns=result.get("concerns", []),
        audit_hash=result.get("audit_hash", "unknown"),
        num_responses=len(result.get("responses", [])),
        channel=channel,
    )

    logger.info(
        "Council discussion posted to #%s: %s (conf: %.2f)",
        channel, result.get("audit_hash", "?"), result.get("confidence", 0),
    )

    return result


# ===================================================================
# CLI — test it
# ===================================================================

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    test_q = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "What should the federation focus on this week?"
    print(f"Asking council: {test_q}")
    result = council_discuss(test_q)
    print(f"\nVerdict: {result.get('recommendation', 'none')}")
    print(f"Confidence: {result.get('confidence', 0):.2f}")
    print(f"Hash: {result.get('audit_hash', '?')}")

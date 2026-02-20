"""
Alert Manager - Push anomaly alerts to Telegram.
Cherokee AI Federation - For Seven Generations
"""

import os
import time
import logging
import requests
from datetime import datetime
from typing import Optional
from collections import defaultdict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
ALERT_CHAT_ID = os.environ.get(
    'TELEGRAM_ALERT_CHAT_ID',
    '-1003439875431'  # TPM group chat
)

# Rate limiting: alert_type -> last_sent_timestamp
_alert_cooldowns = defaultdict(float)
COOLDOWN_SECONDS = {
    'critical': 60,      # 1 min between same critical alerts
    'high': 300,         # 5 min between same high alerts
    'medium': 900,       # 15 min between same medium alerts
    'low': 3600,         # 1 hour between same low alerts
}

# Severity emojis
SEVERITY_EMOJI = {
    'critical': '🚨',
    'high': '🔴',
    'medium': '🟡',
    'low': '🔵',
    'info': 'ℹ️',
}


def send_alert(
    title: str,
    message: str,
    severity: str = 'medium',
    source: str = 'system',
    alert_type: str = None,
    context: dict = None
) -> bool:
    """
    Send alert to Telegram TPM channel.

    Args:
        title: Short alert title
        message: Alert details
        severity: critical, high, medium, low, info
        source: Which component raised the alert
        alert_type: For deduplication (e.g., 'vllm_timeout')
        context: Additional context dict

    Returns:
        True if sent, False if rate-limited or failed
    """
    alert_type = alert_type or f"{source}_{title}".lower().replace(' ', '_')

    # Check rate limit
    cooldown = COOLDOWN_SECONDS.get(severity, 300)
    last_sent = _alert_cooldowns.get(alert_type, 0)
    now = time.time()

    if now - last_sent < cooldown:
        logger.debug(f"Alert {alert_type} rate-limited")
        return False

    # Build message
    emoji = SEVERITY_EMOJI.get(severity, '⚠️')
    timestamp = datetime.now().strftime('%H:%M:%S')

    text = f"{emoji} *{title}*\n"
    text += f"_{severity.upper()} | {source} | {timestamp}_\n\n"
    text += f"{message}\n"

    if context:
        text += "\n*Context:*\n"
        for k, v in list(context.items())[:5]:
            text += f"• {k}: `{v}`\n"

    try:
        response = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": ALERT_CHAT_ID,
                "text": text,
                "parse_mode": "Markdown"
            },
            timeout=10
        )

        if response.status_code == 200:
            _alert_cooldowns[alert_type] = now
            logger.info(f"Alert sent: {title}")
            return True
        else:
            logger.error(f"Alert failed: {response.status_code}")
            return False

    except Exception as e:
        logger.error(f"Alert exception: {e}")
        return False


# Convenience functions for common alerts
def alert_critical(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'critical', source, **kwargs)

def alert_high(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'high', source, **kwargs)

def alert_medium(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'medium', source, **kwargs)

def alert_low(title: str, message: str, source: str = 'system', **kwargs):
    return send_alert(title, message, 'low', source, **kwargs)


# Pre-built alert types
def alert_service_down(service_name: str, error: str = None):
    """Alert when a service goes down."""
    return alert_critical(
        f"Service Down: {service_name}",
        f"{service_name} is not responding.\n\nError: {error or 'Connection failed'}",
        source='health-check',
        alert_type=f'service_down_{service_name}'
    )

def alert_high_latency(service_name: str, latency_ms: int, threshold_ms: int):
    """Alert when latency exceeds threshold."""
    return alert_medium(
        f"High Latency: {service_name}",
        f"Response time: {latency_ms}ms (threshold: {threshold_ms}ms)",
        source='performance',
        alert_type=f'high_latency_{service_name}',
        context={'latency_ms': latency_ms, 'threshold_ms': threshold_ms}
    )

def alert_job_failed(job_type: str, job_id: str, error: str):
    """Alert when a background job fails."""
    return alert_high(
        f"Job Failed: {job_type}",
        f"Job {job_id} failed.\n\nError: {error[:200]}",
        source=job_type,
        alert_type=f'job_failed_{job_type}',
        context={'job_id': job_id}
    )

def alert_security(title: str, details: str, context: dict = None):
    """Security-related alert (always high priority)."""
    return alert_high(
        f"Security: {title}",
        details,
        source='crawdad',
        alert_type=f'security_{title.lower().replace(" ", "_")}',
        context=context
    )

def alert_anomaly(title: str, details: str, metric: str = None, value: float = None):
    """Anomaly detection alert."""
    ctx = {}
    if metric:
        ctx['metric'] = metric
    if value is not None:
        ctx['value'] = value
    return alert_medium(
        f"Anomaly: {title}",
        details,
        source='eagle-eye',
        alert_type=f'anomaly_{title.lower().replace(" ", "_")}',
        context=ctx
    )


if __name__ == "__main__":
    # Test alert
    send_alert(
        "Alert System Test",
        "This is a test alert from the alert manager.",
        severity='info',
        source='test',
        context={'test': True, 'timestamp': datetime.now().isoformat()}
    )
    print("Test alert sent!")
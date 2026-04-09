#!/usr/bin/env python3
"""
Shield Agent — Consent Engine.
The agent WILL NOT START without recorded consent. Non-negotiable.
Council vote #7cfe224b87cb349f.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

CONSENT_DIR = os.path.expanduser("~/.ganuda-shield")
CONSENT_FILE = os.path.join(CONSENT_DIR, "consent.json")

CONSENT_TEXTS = {
    "standard": """GANUDA SHIELD — TRANSPARENT ENDPOINT MONITORING

This application monitors your work activity to protect company data.

WHAT IS CAPTURED:
• Application usage patterns (which apps you use, not what you type)
• Clipboard content types (URL, code, text — not the actual content)
• File access patterns (which files opened, not their contents)
• Network connection counts (how many connections, not where)
• USB device types (keyboard, mouse, storage — not data transferred)
• Idle time and session duration

WHAT IS NOT CAPTURED:
• Keystrokes or typed content
• Screen content or screenshots (unless a security anomaly triggers escalation, in which case you will be visibly notified)
• Personal messages, emails, or browsing history
• File contents

YOUR RIGHTS:
• You can view your own activity dashboard at any time
• You can report false alarms if you believe an anomaly is incorrect
• Your data stays on your company's server — it is never sent to any third party
• You will be visibly notified (red tray icon) if enhanced monitoring is ever activated

By clicking "I understand and consent," you acknowledge that you have read and understood this notice.""",

    "gdpr": """[All of the above, PLUS:]

GDPR RIGHTS:
• You have the right to withdraw this consent at any time
• You have the right to request access to your collected data
• You have the right to request deletion of your data (subject to legal retention requirements)
• Data Protection Officer contact: [configured per installation]
• Legal basis for processing: legitimate interest in data security + your consent""",

    "ccpa": """[All of the above, PLUS:]

CALIFORNIA PRIVACY RIGHTS (CCPA):
• You have the right to know what personal information is collected
• You have the right to request deletion of your personal information
• You will not be discriminated against for exercising these rights
• Categories of information collected: employment-related activity patterns"""
}


def get_consent_text(jurisdiction: str = "standard") -> str:
    """Get the full consent text for the jurisdiction."""
    base = CONSENT_TEXTS["standard"]
    if jurisdiction in CONSENT_TEXTS and jurisdiction != "standard":
        base += "\n\n" + CONSENT_TEXTS[jurisdiction]
    return base


def check_consent_exists() -> bool:
    """Check if consent has already been recorded."""
    return os.path.exists(CONSENT_FILE)


def load_consent() -> dict:
    """Load existing consent record."""
    if not os.path.exists(CONSENT_FILE):
        return {}
    with open(CONSENT_FILE) as f:
        return json.load(f)


def record_consent(employee_id: str, machine_id: str, jurisdiction: str, agent_version: str = "0.1.0") -> dict:
    """Record consent with full audit trail."""
    consent_text = get_consent_text(jurisdiction)
    consent_hash = hashlib.sha256(consent_text.encode()).hexdigest()

    record = {
        "employee_id": employee_id,
        "machine_id": machine_id,
        "jurisdiction": jurisdiction,
        "consent_timestamp": datetime.now().isoformat(),
        "consent_text_hash": consent_hash,
        "agent_version": agent_version,
        "consent_text": consent_text,
        "withdrawn": False,
    }

    os.makedirs(CONSENT_DIR, exist_ok=True)

    # Save consent record
    with open(CONSENT_FILE, 'w') as f:
        json.dump(record, f, indent=2)

    # Generate desktop receipt
    receipt_path = Path.home() / f"ganuda-shield-consent-{datetime.now().strftime('%Y-%m-%d')}.txt"
    with open(receipt_path, 'w') as f:
        f.write(f"GANUDA SHIELD CONSENT RECEIPT\n")
        f.write(f"{'='*40}\n")
        f.write(f"Employee: {employee_id}\n")
        f.write(f"Machine: {machine_id}\n")
        f.write(f"Jurisdiction: {jurisdiction}\n")
        f.write(f"Timestamp: {record['consent_timestamp']}\n")
        f.write(f"Consent Hash: {consent_hash}\n")
        f.write(f"\n{consent_text}\n")

    return record


def withdraw_consent() -> bool:
    """Withdraw consent (GDPR right). Stops the agent."""
    if not os.path.exists(CONSENT_FILE):
        return False
    with open(CONSENT_FILE) as f:
        record = json.load(f)
    record["withdrawn"] = True
    record["withdrawn_at"] = datetime.now().isoformat()
    with open(CONSENT_FILE, 'w') as f:
        json.dump(record, f, indent=2)
    return True


def request_consent_cli(employee_id: str, machine_id: str, jurisdiction: str) -> bool:
    """CLI consent flow — prints consent text, asks for confirmation."""
    consent_text = get_consent_text(jurisdiction)
    print("\n" + "="*60)
    print("GANUDA SHIELD — CONSENT REQUIRED")
    print("="*60)
    print(consent_text)
    print("="*60)

    response = input("\nType 'I understand and consent' to proceed: ").strip()
    if response.lower() == "i understand and consent":
        record = record_consent(employee_id, machine_id, jurisdiction)
        print(f"\nConsent recorded. Receipt saved to your desktop.")
        print(f"Hash: {record['consent_text_hash']}")
        return True
    else:
        print("\nConsent not given. Agent will not start.")
        return False

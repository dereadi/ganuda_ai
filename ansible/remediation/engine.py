#!/usr/bin/env python3
"""
Cherokee AI Federation — Self-Healing Remediation Engine

Receives alerts from EDA triage playbook, classifies them via Qwen 72B,
searches thermal memory for similar past remediations, selects a playbook
template, and generates a candidate remediation playbook.

Turtle's 7GEN: LLM fills TEMPLATES, never writes free-form YAML.
Crawdad's Gate: Generated playbooks go to validation pipeline before execution.

Usage:
    python engine.py --alert-id <id> --severity <level> --content <text>
"""

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

import requests
import psycopg2
import yaml

# Import sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from module_whitelist import validate_playbook_modules, KNOWN_SERVICES
from prompt_templates import CLASSIFY_ALERT_PROMPT, FILL_TEMPLATE_PROMPT

# Configuration
VLLM_URL = "http://192.168.132.223:8000/v1/chat/completions"
GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = os.environ.get("CHEROKEE_API_KEY", "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5")
DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"

TEMPLATE_DIR = Path("/ganuda/ansible/templates/remediation")
STAGING_DIR = Path("/ganuda/ansible/staging")
EMBEDDING_URL = "http://192.168.132.224:8003"

# Template mapping by alert category
CATEGORY_TEMPLATES = {
    "service_down": "restart_service.yml.j2",
    "config_drift": "config_drift.yml.j2",
    "resource_exhaustion": "resource_cleanup.yml.j2",
}


def get_db_password():
    """Load DB password from secrets_loader or environment."""
    try:
        sys.path.insert(0, "/ganuda/lib")
        from secrets_loader import get_secret
        return get_secret("DB_PASSWORD")
    except Exception:
        return os.environ.get("DB_PASSWORD", "")


def classify_alert(alert_content: str, severity: str) -> dict:
    """Use Qwen 72B to classify the alert into a remediation category."""
    prompt = CLASSIFY_ALERT_PROMPT.format(
        alert_content=alert_content,
        severity=severity,
    )

    try:
        resp = requests.post(
            VLLM_URL,
            json={
                "model": "Qwen/Qwen2.5-72B-Instruct-AWQ",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 256,
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Extract JSON from response
        # Handle markdown code blocks if present
        if "
#!/usr/bin/env python3
"""
Shield Agent — Encrypted transport to collection server.
Reference: subscription-trimmer/classifier.py (HTTP POST pattern).
"""

import json
import hashlib
import requests
import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

logger = logging.getLogger('shield.transport')


class ShieldTransport:
    """Encrypted batch transport to Shield collection server."""

    def __init__(self, server_url: str, machine_id: str, api_key: str = ""):
        self.server_url = server_url.rstrip('/')
        self.machine_id = machine_id
        self.api_key = api_key
        self.encryption_key = None

    def register(self, employee_id: str, consent_record: dict) -> Optional[str]:
        """Register agent with server. Returns API key."""
        try:
            resp = requests.post(
                f"{self.server_url}/api/v1/register",
                json={
                    "machine_id": self.machine_id,
                    "employee_id": employee_id,
                    "consent_record": consent_record,
                    "agent_version": "0.1.0",
                },
                timeout=10,
                verify=False,  # Allow self-signed certs for internal deployments
            )
            if resp.status_code == 200:
                data = resp.json()
                self.api_key = data.get("api_key", "")
                self.encryption_key = data.get("encryption_key")
                logger.info(f"Registered with server. API key received.")
                return self.api_key
            else:
                logger.error(f"Registration failed: {resp.status_code}")
                return None
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return None

    def send_heartbeat(self) -> bool:
        """Send heartbeat. Server tracks agent liveness."""
        try:
            resp = requests.post(
                f"{self.server_url}/api/v1/heartbeat",
                json={"machine_id": self.machine_id, "timestamp": datetime.now().isoformat()},
                headers={"X-API-Key": self.api_key},
                timeout=5,
                verify=False,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def send_batch(self, snapshots: List[Dict]) -> bool:
        """Send encrypted batch of activity snapshots."""
        if not snapshots:
            return True

        payload = json.dumps(snapshots, default=str).encode()

        # Encrypt if key available
        if CRYPTO_AVAILABLE and self.encryption_key:
            f = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
            payload = f.encrypt(payload)
            encrypted = True
        else:
            encrypted = False

        try:
            resp = requests.post(
                f"{self.server_url}/api/v1/report",
                data=payload,
                headers={
                    "X-API-Key": self.api_key,
                    "X-Machine-ID": self.machine_id,
                    "X-Encrypted": str(encrypted).lower(),
                    "X-Batch-Size": str(len(snapshots)),
                    "X-Timestamp": datetime.now().isoformat(),
                    "Content-Type": "application/octet-stream" if encrypted else "application/json",
                },
                timeout=15,
                verify=False,
            )
            if resp.status_code == 200:
                logger.debug(f"Batch sent: {len(snapshots)} snapshots")
                return True
            else:
                logger.warning(f"Batch rejected: {resp.status_code}")
                return False
        except Exception as e:
            logger.warning(f"Batch send failed: {e}")
            return False

    def check_config_update(self) -> Optional[Dict]:
        """Check if server has config updates (e.g., escalation)."""
        try:
            resp = requests.get(
                f"{self.server_url}/api/v1/config/{self.machine_id}",
                headers={"X-API-Key": self.api_key},
                timeout=5,
                verify=False,
            )
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return None

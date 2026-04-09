#!/usr/bin/env python3
"""
Shield Server — Evidence Vault.
Immutable, encrypted, chain-of-custody storage for escalated evidence.
DUPLO addition. Partner Apr 4 2026.

The moment an anomaly escalates to evidence, different rules apply:
- Append-only (no UPDATE, no DELETE)
- Encrypted with vault-specific key (separate from main DB)
- Chain of custody logged for every access
- Legal hold prevents any purge
- Forensic export with integrity verification

PRIVATE — Commercial License.
"""

import os
import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

try:
    from cryptography.fernet import Fernet
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

VAULT_KEY_PATH = os.path.expanduser("~/.ganuda-shield/evidence_vault.key")


def get_vault_key() -> Optional[object]:
    """Get or create the evidence vault encryption key. Separate from main key."""
    if not CRYPTO_AVAILABLE:
        return None
    if os.path.exists(VAULT_KEY_PATH):
        with open(VAULT_KEY_PATH, 'rb') as f:
            return Fernet(f.read().strip())
    else:
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(VAULT_KEY_PATH), exist_ok=True)
        with open(VAULT_KEY_PATH, 'wb') as f:
            f.write(key)
        os.chmod(VAULT_KEY_PATH, 0o600)
        return Fernet(key)


class EvidenceVault:
    """Immutable evidence storage with chain of custody."""

    def __init__(self):
        self.records = []  # In production: PostgreSQL evidence.records table
        self.custody_log = []  # In production: PostgreSQL evidence.custody_log table
        self.fernet = get_vault_key()

    def collect_evidence(
        self,
        case_id: str,
        anomaly_id: int,
        machine_id: str,
        employee_id: str,
        evidence_type: str,
        evidence_data: bytes,
        pii_classification: str = "none",
        authorized_by: str = "",
        authorization_reason: str = "",
    ) -> Dict:
        """
        Collect and store evidence. Requires authorization.
        Returns evidence record with capture hash.
        """
        if not authorized_by:
            raise ValueError("Evidence collection requires authorization. Provide authorized_by.")

        # Hash raw evidence at capture time (BEFORE encryption)
        capture_hash = hashlib.sha256(evidence_data).hexdigest()

        # Encrypt evidence
        if self.fernet:
            encrypted_data = self.fernet.encrypt(evidence_data)
        else:
            encrypted_data = evidence_data  # fallback: store unencrypted (log warning)

        record = {
            "id": len(self.records),
            "case_id": case_id,
            "anomaly_id": anomaly_id,
            "machine_id": machine_id,
            "employee_id": employee_id,
            "evidence_type": evidence_type,
            "evidence_data": encrypted_data,
            "pii_classification": pii_classification,
            "capture_timestamp": datetime.now().isoformat(),
            "capture_hash": capture_hash,
            "legal_hold": False,
            "created_at": datetime.now().isoformat(),
        }
        self.records.append(record)

        # Log the collection in custody log
        self._log_custody(
            evidence_id=record["id"],
            accessed_by=authorized_by,
            access_type="collect",
            access_reason=authorization_reason,
        )

        return {
            "evidence_id": record["id"],
            "capture_hash": capture_hash,
            "encrypted": self.fernet is not None,
        }

    def access_evidence(self, evidence_id: int, accessed_by: str, access_reason: str) -> Optional[Dict]:
        """Access evidence. Logged in custody chain. Returns metadata only (not decrypted content)."""
        if evidence_id >= len(self.records):
            return None

        record = self.records[evidence_id]

        self._log_custody(
            evidence_id=evidence_id,
            accessed_by=accessed_by,
            access_type="view",
            access_reason=access_reason,
        )

        # Return metadata, NOT decrypted content (content only via export)
        return {
            "id": record["id"],
            "case_id": record["case_id"],
            "evidence_type": record["evidence_type"],
            "pii_classification": record["pii_classification"],
            "capture_timestamp": record["capture_timestamp"],
            "capture_hash": record["capture_hash"],
            "legal_hold": record["legal_hold"],
            "data_size_bytes": len(record["evidence_data"]),
        }

    def set_legal_hold(self, evidence_id: int, admin_user: str, reason: str) -> bool:
        """Set legal hold — prevents any automated purge."""
        if evidence_id >= len(self.records):
            return False
        self.records[evidence_id]["legal_hold"] = True
        self._log_custody(evidence_id, admin_user, "legal_hold_set", reason)
        return True

    def release_legal_hold(self, evidence_id: int, admin_user: str, reason: str) -> bool:
        """Release legal hold."""
        if evidence_id >= len(self.records):
            return False
        self.records[evidence_id]["legal_hold"] = False
        self._log_custody(evidence_id, admin_user, "legal_hold_released", reason)
        return True

    def verify_integrity(self, evidence_id: int) -> Dict:
        """Verify evidence integrity by re-hashing and comparing to capture hash."""
        if evidence_id >= len(self.records):
            return {"valid": False, "error": "Evidence not found"}

        record = self.records[evidence_id]

        # Decrypt to get original data
        if self.fernet:
            try:
                decrypted = self.fernet.decrypt(record["evidence_data"])
            except Exception as e:
                return {"valid": False, "error": f"Decryption failed: {e}"}
        else:
            decrypted = record["evidence_data"]

        # Re-hash and compare
        current_hash = hashlib.sha256(decrypted).hexdigest()
        valid = current_hash == record["capture_hash"]

        return {
            "valid": valid,
            "capture_hash": record["capture_hash"],
            "current_hash": current_hash,
            "evidence_id": evidence_id,
            "verified_at": datetime.now().isoformat(),
        }

    def export_case(self, case_id: str, exported_by: str, export_reason: str) -> Dict:
        """Export all evidence for a case as a forensic package."""
        case_records = [r for r in self.records if r["case_id"] == case_id]
        if not case_records:
            return {"error": f"No evidence found for case {case_id}"}

        package = {
            "manifest": {
                "case_id": case_id,
                "export_timestamp": datetime.now().isoformat(),
                "exported_by": exported_by,
                "export_reason": export_reason,
                "evidence_count": len(case_records),
            },
            "evidence": [],
            "custody_chain": [],
            "integrity_checks": [],
        }

        for record in case_records:
            # Verify integrity
            integrity = self.verify_integrity(record["id"])
            package["integrity_checks"].append(integrity)

            # Log the export access
            self._log_custody(record["id"], exported_by, "export", export_reason)

            # Include metadata (decrypted content would be separate files in real export)
            package["evidence"].append({
                "id": record["id"],
                "evidence_type": record["evidence_type"],
                "pii_classification": record["pii_classification"],
                "capture_timestamp": record["capture_timestamp"],
                "capture_hash": record["capture_hash"],
                "legal_hold": record["legal_hold"],
                "integrity_valid": integrity["valid"],
            })

        # Include full custody chain for this case
        case_evidence_ids = {r["id"] for r in case_records}
        package["custody_chain"] = [
            entry for entry in self.custody_log
            if entry["evidence_id"] in case_evidence_ids
        ]

        # Hash the entire package for tamper detection
        package_json = json.dumps(package, default=str, sort_keys=True)
        package["manifest"]["package_hash"] = hashlib.sha256(package_json.encode()).hexdigest()

        return package

    def _log_custody(self, evidence_id: int, accessed_by: str, access_type: str, access_reason: str):
        """Append to custody log. IMMUTABLE — no updates, no deletes."""
        self.custody_log.append({
            "evidence_id": evidence_id,
            "accessed_by": accessed_by,
            "access_type": access_type,
            "access_reason": access_reason,
            "access_timestamp": datetime.now().isoformat(),
        })

    def get_custody_chain(self, evidence_id: int) -> List[Dict]:
        """Get full custody chain for a piece of evidence."""
        return [entry for entry in self.custody_log if entry["evidence_id"] == evidence_id]

    def canary_self_audit(self) -> Dict:
        """Security Canary self-audit of the evidence vault."""
        findings = []

        # Check vault key exists and has correct permissions
        if os.path.exists(VAULT_KEY_PATH):
            stat = os.stat(VAULT_KEY_PATH)
            perms = oct(stat.st_mode)[-3:]
            if perms != '600':
                findings.append({"severity": "critical", "check": "vault_key_permissions",
                    "description": f"Vault key has permissions {perms}, should be 600"})
            else:
                findings.append({"severity": "info", "check": "vault_key_permissions",
                    "description": "Vault key permissions correct (600)"})
        else:
            findings.append({"severity": "warning", "check": "vault_key_exists",
                "description": "No vault key found — evidence stored unencrypted"})

        # Verify all evidence integrity
        tampered = 0
        for record in self.records:
            result = self.verify_integrity(record["id"])
            if not result["valid"]:
                tampered += 1
        if tampered:
            findings.append({"severity": "critical", "check": "evidence_integrity",
                "description": f"{tampered} evidence records FAILED integrity check"})
        elif self.records:
            findings.append({"severity": "info", "check": "evidence_integrity",
                "description": f"All {len(self.records)} evidence records passed integrity check"})

        # Check custody log completeness
        evidence_ids_with_custody = {e["evidence_id"] for e in self.custody_log}
        evidence_ids_without = [r["id"] for r in self.records if r["id"] not in evidence_ids_with_custody]
        if evidence_ids_without:
            findings.append({"severity": "critical", "check": "custody_completeness",
                "description": f"{len(evidence_ids_without)} evidence records have NO custody log entries"})
        elif self.records:
            findings.append({"severity": "info", "check": "custody_completeness",
                "description": "All evidence records have custody log entries"})

        return {
            "audit_timestamp": datetime.now().isoformat(),
            "total_evidence": len(self.records),
            "total_custody_entries": len(self.custody_log),
            "findings": findings,
        }

# JR Instruction: Consent Framework Implementation

**Task ID:** CONSENT-FRAMEWORK-001
**Priority:** P1 - Foundation
**Type:** implementation
**Estimated Complexity:** Medium

---

## Objective

Implement a shared Consent Framework that all Ganuda services use to request, track, and respect user consent according to Cherokee principles.

---

## Context

From the tribal awareness assessment:
- **Gap identified:** No explicit consent mechanisms documented
- **Gap identified:** No consent withdrawal process defined
- **Cherokee principle:** Knowledge shared must be knowledge consented (Mitakuye Oyasin)

---

## Deliverables

### File 1: `/ganuda/lib/consent_framework.py`

```python
"""
Cherokee Consent Framework

Implements consent management according to tribal principles:
- Mitakuye Oyasin: All relations honored, including data relationships
- Seven Generations: Consent decisions logged for future auditors
- Gadugi: Cooperation requires mutual agreement

Reference: ULTRATHINK-TRIBAL-AWARENESS-INTEGRATION-JAN24-2026.md
"""

import json
import hashlib
import psycopg2
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from enum import Enum


class ConsentType(Enum):
    """Types of consent that can be requested."""
    DATA_COLLECTION = "data_collection"  # Can we collect this data?
    DATA_RETENTION = "data_retention"    # Can we keep this data?
    DATA_PROCESSING = "data_processing"  # Can we analyze this data?
    DATA_SHARING = "data_sharing"        # Can we share this? (default: NEVER external)
    DECISION_MAKING = "decision_making"  # Can we make decisions using this?
    CAMERA_RECORDING = "camera_recording"  # Can we record video?
    BIOMETRIC = "biometric"              # Can we process biometric data?


class ConsentStatus(Enum):
    """Current status of a consent."""
    PENDING = "pending"      # Consent requested but not yet given
    GRANTED = "granted"      # User explicitly consented
    DENIED = "denied"        # User explicitly denied
    WITHDRAWN = "withdrawn"  # User withdrew previous consent
    EXPIRED = "expired"      # Consent duration passed


@dataclass
class ConsentRequest:
    """A request for user consent."""
    consent_type: ConsentType
    purpose: str           # Plain-language explanation of why
    data_description: str  # What data is involved
    duration: str          # How long consent is valid ("session", "30_days", "indefinite")
    service: str           # Which service is requesting
    can_withdraw: bool = True  # Can user withdraw? (almost always True)
    alternatives: Optional[str] = None  # What happens if they decline


@dataclass
class ConsentRecord:
    """Record of a consent decision."""
    user_id: str
    consent_type: ConsentType
    status: ConsentStatus
    purpose: str
    service: str
    granted_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    withdrawn_at: Optional[datetime] = None
    withdrawal_reason: Optional[str] = None
    audit_hash: str = ""

    def is_valid(self) -> bool:
        """Check if consent is currently valid."""
        if self.status != ConsentStatus.GRANTED:
            return False
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


# Database configuration
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}


class ConsentManager:
    """
    Manages consent according to Cherokee principles.

    Key principles implemented:
    1. Explicit opt-in (no pre-checked boxes)
    2. Clear purpose explanation
    3. Easy withdrawal
    4. Complete audit trail (Seven Generations)
    5. No external sharing without explicit consent (Constitutional constraint)
    """

    def __init__(self, service_name: str):
        """
        Initialize consent manager for a specific service.

        Args:
            service_name: The service using this manager (e.g., "vetassist", "tribal-vision")
        """
        self.service = service_name
        self._ensure_table_exists()

    def _get_connection(self):
        """Get database connection."""
        return psycopg2.connect(**DB_CONFIG)

    def _ensure_table_exists(self):
        """Create consent_records table if not exists."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS consent_records (
                        id SERIAL PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        consent_type VARCHAR(50) NOT NULL,
                        status VARCHAR(20) NOT NULL,
                        purpose TEXT NOT NULL,
                        service VARCHAR(100) NOT NULL,
                        granted_at TIMESTAMP,
                        expires_at TIMESTAMP,
                        withdrawn_at TIMESTAMP,
                        withdrawal_reason TEXT,
                        audit_hash VARCHAR(64) NOT NULL,
                        created_at TIMESTAMP DEFAULT NOW(),
                        updated_at TIMESTAMP DEFAULT NOW(),

                        UNIQUE(user_id, consent_type, service)
                    );

                    CREATE INDEX IF NOT EXISTS idx_consent_user
                        ON consent_records(user_id);
                    CREATE INDEX IF NOT EXISTS idx_consent_service
                        ON consent_records(service);
                    CREATE INDEX IF NOT EXISTS idx_consent_status
                        ON consent_records(status);
                """)
                conn.commit()
        finally:
            conn.close()

    def _compute_audit_hash(self, record: ConsentRecord) -> str:
        """Compute audit hash for consent record (Seven Generations transparency)."""
        data = json.dumps({
            "user_id": record.user_id,
            "consent_type": record.consent_type.value,
            "status": record.status.value,
            "purpose": record.purpose,
            "service": record.service,
            "granted_at": record.granted_at.isoformat() if record.granted_at else None,
            "expires_at": record.expires_at.isoformat() if record.expires_at else None,
        }, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]

    def request_consent(self, user_id: str, request: ConsentRequest) -> ConsentRecord:
        """
        Request consent from a user.

        This creates a PENDING consent record. The UI must then
        present the request to the user for explicit confirmation.

        Args:
            user_id: The user to request consent from
            request: The consent request details

        Returns:
            ConsentRecord with PENDING status
        """
        record = ConsentRecord(
            user_id=user_id,
            consent_type=request.consent_type,
            status=ConsentStatus.PENDING,
            purpose=request.purpose,
            service=request.service,
        )
        record.audit_hash = self._compute_audit_hash(record)

        self._store_record(record)
        self._log_to_thermal_memory(record, "consent_requested")

        return record

    def grant_consent(self, user_id: str, consent_type: ConsentType,
                     duration: str = "30_days") -> ConsentRecord:
        """
        Record that user has granted consent.

        Args:
            user_id: The user granting consent
            consent_type: Type of consent being granted
            duration: How long consent is valid

        Returns:
            Updated ConsentRecord with GRANTED status
        """
        # Calculate expiration
        expires_at = None
        if duration == "session":
            expires_at = datetime.now() + timedelta(hours=24)  # Session = 24h max
        elif duration == "30_days":
            expires_at = datetime.now() + timedelta(days=30)
        elif duration == "90_days":
            expires_at = datetime.now() + timedelta(days=90)
        # "indefinite" = no expiration

        record = self._get_record(user_id, consent_type)
        if not record:
            # Create new record if none exists
            record = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                status=ConsentStatus.GRANTED,
                purpose="Direct grant",
                service=self.service,
            )

        record.status = ConsentStatus.GRANTED
        record.granted_at = datetime.now()
        record.expires_at = expires_at
        record.audit_hash = self._compute_audit_hash(record)

        self._store_record(record)
        self._log_to_thermal_memory(record, "consent_granted")

        return record

    def withdraw_consent(self, user_id: str, consent_type: ConsentType,
                        reason: Optional[str] = None) -> ConsentRecord:
        """
        Withdraw previously granted consent.

        Mitakuye Oyasin: Relations can be ended with dignity.

        Args:
            user_id: The user withdrawing consent
            consent_type: Type of consent being withdrawn
            reason: Optional reason for withdrawal

        Returns:
            Updated ConsentRecord with WITHDRAWN status
        """
        record = self._get_record(user_id, consent_type)
        if not record:
            raise ValueError(f"No consent record found for {user_id}/{consent_type.value}")

        record.status = ConsentStatus.WITHDRAWN
        record.withdrawn_at = datetime.now()
        record.withdrawal_reason = reason
        record.audit_hash = self._compute_audit_hash(record)

        self._store_record(record)
        self._log_to_thermal_memory(record, "consent_withdrawn")

        # Trigger any cleanup actions (service-specific)
        self._on_consent_withdrawn(user_id, consent_type)

        return record

    def check_consent(self, user_id: str, consent_type: ConsentType) -> bool:
        """
        Check if user has valid consent for an action.

        Args:
            user_id: The user to check
            consent_type: Type of consent needed

        Returns:
            True if consent is valid, False otherwise
        """
        record = self._get_record(user_id, consent_type)
        if not record:
            return False
        return record.is_valid()

    def get_all_consents(self, user_id: str) -> List[ConsentRecord]:
        """
        Get all consent records for a user.

        Seven Generations: Complete transparency for audit.

        Args:
            user_id: The user to query

        Returns:
            List of all ConsentRecords for this user
        """
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, consent_type, status, purpose, service,
                           granted_at, expires_at, withdrawn_at, withdrawal_reason, audit_hash
                    FROM consent_records
                    WHERE user_id = %s
                    ORDER BY created_at DESC
                """, (user_id,))

                records = []
                for row in cur.fetchall():
                    records.append(ConsentRecord(
                        user_id=row[0],
                        consent_type=ConsentType(row[1]),
                        status=ConsentStatus(row[2]),
                        purpose=row[3],
                        service=row[4],
                        granted_at=row[5],
                        expires_at=row[6],
                        withdrawn_at=row[7],
                        withdrawal_reason=row[8],
                        audit_hash=row[9]
                    ))
                return records
        finally:
            conn.close()

    def _get_record(self, user_id: str, consent_type: ConsentType) -> Optional[ConsentRecord]:
        """Get specific consent record."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT user_id, consent_type, status, purpose, service,
                           granted_at, expires_at, withdrawn_at, withdrawal_reason, audit_hash
                    FROM consent_records
                    WHERE user_id = %s AND consent_type = %s AND service = %s
                """, (user_id, consent_type.value, self.service))

                row = cur.fetchone()
                if row:
                    return ConsentRecord(
                        user_id=row[0],
                        consent_type=ConsentType(row[1]),
                        status=ConsentStatus(row[2]),
                        purpose=row[3],
                        service=row[4],
                        granted_at=row[5],
                        expires_at=row[6],
                        withdrawn_at=row[7],
                        withdrawal_reason=row[8],
                        audit_hash=row[9]
                    )
                return None
        finally:
            conn.close()

    def _store_record(self, record: ConsentRecord):
        """Store or update consent record."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO consent_records
                        (user_id, consent_type, status, purpose, service,
                         granted_at, expires_at, withdrawn_at, withdrawal_reason, audit_hash)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, consent_type, service)
                    DO UPDATE SET
                        status = EXCLUDED.status,
                        granted_at = EXCLUDED.granted_at,
                        expires_at = EXCLUDED.expires_at,
                        withdrawn_at = EXCLUDED.withdrawn_at,
                        withdrawal_reason = EXCLUDED.withdrawal_reason,
                        audit_hash = EXCLUDED.audit_hash,
                        updated_at = NOW()
                """, (
                    record.user_id,
                    record.consent_type.value,
                    record.status.value,
                    record.purpose,
                    record.service,
                    record.granted_at,
                    record.expires_at,
                    record.withdrawn_at,
                    record.withdrawal_reason,
                    record.audit_hash
                ))
                conn.commit()
        finally:
            conn.close()

    def _log_to_thermal_memory(self, record: ConsentRecord, event_type: str):
        """Log consent event to thermal memory for Seven Generations audit."""
        conn = self._get_connection()
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                        (keeper_type, content, source, temperature, is_sacred)
                    VALUES ('consent_audit', %s, %s, 70.0, false)
                """, (
                    json.dumps({
                        "event": event_type,
                        "user_id": record.user_id,
                        "consent_type": record.consent_type.value,
                        "status": record.status.value,
                        "service": record.service,
                        "audit_hash": record.audit_hash,
                        "timestamp": datetime.now().isoformat()
                    }),
                    self.service
                ))
                conn.commit()
        finally:
            conn.close()

    def _on_consent_withdrawn(self, user_id: str, consent_type: ConsentType):
        """
        Handle consent withdrawal - trigger cleanup.

        Override in service-specific subclasses.
        """
        # Default: log the withdrawal
        print(f"[{self.service}] Consent withdrawn: {user_id}/{consent_type.value}")

        # Service-specific cleanup should be implemented in subclasses
        # e.g., VetAssistConsentManager might purge user data


# Service-specific consent managers

class VetAssistConsentManager(ConsentManager):
    """VetAssist-specific consent management."""

    def __init__(self):
        super().__init__("vetassist")

    def _on_consent_withdrawn(self, user_id: str, consent_type: ConsentType):
        """Purge user data when consent withdrawn."""
        super()._on_consent_withdrawn(user_id, consent_type)

        if consent_type == ConsentType.DATA_RETENTION:
            # Purge all stored documents for this user
            self._purge_user_documents(user_id)

        if consent_type == ConsentType.DATA_COLLECTION:
            # Purge all data and close session
            self._purge_all_user_data(user_id)

    def _purge_user_documents(self, user_id: str):
        """Purge uploaded documents."""
        # Implementation: Delete from vetassist_wizard_files, vetassist_extracted_documents
        print(f"[vetassist] Purging documents for user {user_id}")

    def _purge_all_user_data(self, user_id: str):
        """Purge all user data."""
        # Implementation: Delete from all vetassist tables for this user
        print(f"[vetassist] Purging ALL data for user {user_id}")


class TribalVisionConsentManager(ConsentManager):
    """Tribal Vision camera consent management."""

    def __init__(self):
        super().__init__("tribal-vision")

    def request_camera_consent(self, household_id: str, camera_name: str) -> ConsentRecord:
        """Request consent for camera recording."""
        request = ConsentRequest(
            consent_type=ConsentType.CAMERA_RECORDING,
            purpose=f"Record video from {camera_name} for security monitoring",
            data_description="Video footage including persons in view",
            duration="indefinite",
            service="tribal-vision",
            alternatives="Camera can be disabled or masked"
        )
        return self.request_consent(household_id, request)
```

---

## Acceptance Criteria

1. `consent_records` table created in PostgreSQL
2. ConsentManager can request, grant, withdraw consent
3. Consent events logged to thermal_memory_archive
4. VetAssist-specific manager purges data on withdrawal
5. Seven Generations audit trail maintained

---

## Testing

```python
# Test consent flow
from lib.consent_framework import VetAssistConsentManager, ConsentType

mgr = VetAssistConsentManager()

# Grant consent
record = mgr.grant_consent("user123", ConsentType.DATA_COLLECTION, "30_days")
print(f"Consent valid: {mgr.check_consent('user123', ConsentType.DATA_COLLECTION)}")

# Withdraw consent
mgr.withdraw_consent("user123", ConsentType.DATA_COLLECTION, "No longer using service")
print(f"Consent valid: {mgr.check_consent('user123', ConsentType.DATA_COLLECTION)}")

# View audit trail
records = mgr.get_all_consents("user123")
for r in records:
    print(f"{r.consent_type.value}: {r.status.value}")
```

---

**Wado - Consent as sacred agreement, not legal checkbox**

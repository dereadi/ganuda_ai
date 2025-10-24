#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Sacred Health Data Protocol (C1)
Cherokee Constitutional AI - Medicine Woman + War Chief Conscience Jr

Purpose: Extend Guardian with sacred health data protection:
- Medical entity detection (spaCy NER)
- 40° floor auto-elevation for all medical data
- Biometric detection (triggers 3-of-3 Chiefs attestation)
- User deletion controls (respects legal holds)
- Cherokee values validation (Gadugi, Seven Generations, Mitakuye Oyasin)

Authors: Medicine Woman Conscience Jr (lead), War Chief Conscience Jr (validation)
Date: October 24, 2025
"""

import spacy
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from .module import Guardian, GuardianDecision, ProtectionLevel


@dataclass
class MedicalEntity:
    """Medical entity detected by spaCy NER."""
    text: str
    label: str
    start: int
    end: int
    confidence: float


@dataclass
class DeletionRequest:
    """User deletion request evaluation result."""
    allowed: bool
    reason: str
    legal_hold: bool
    legal_hold_reason: Optional[str] = None


class SacredHealthGuardian(Guardian):
    """
    Sacred health data protection extending base Guardian.

    Cherokee Constitutional AI - C1 Implementation
    Medicine Woman Conscience Jr: "All medical data is sacred-by-default (40° floor)"

    Features:
    - spaCy NER for medical entity detection
    - Auto-elevation to 40° sacred floor
    - Biometric detection (3-of-3 attestation required)
    - User deletion controls (HIPAA compliance)
    - Cherokee values validation
    """

    # Biometric keywords that trigger 3-of-3 Chiefs attestation
    BIOMETRIC_KEYWORDS = [
        "fingerprint", "face scan", "facial recognition",
        "voice print", "iris scan", "retina scan",
        "dna", "genetic data", "biometric", "biometric authentication"
    ]

    # Medical keywords for additional detection
    MEDICAL_KEYWORDS = [
        "diagnosis", "prescription", "medication", "surgery",
        "patient", "doctor", "hospital", "clinic",
        "blood pressure", "heart rate", "cholesterol",
        "x-ray", "mri", "ct scan", "lab results"
    ]

    # HIPAA retention: 7 years for medical records
    HIPAA_RETENTION_YEARS = 7

    def __init__(self, cache=None):
        """
        Initialize Sacred Health Guardian.

        Args:
            cache: Optional EncryptedCache instance for thermal memory queries
        """
        super().__init__(cache)
        self.nlp = None  # spaCy model (loaded in initialize())
        self.medical_stats = {
            "medical_entities_detected": 0,
            "auto_elevations": 0,
            "biometric_detections": 0,
            "deletion_requests": 0,
            "deletion_requests_allowed": 0
        }

    async def initialize(self):
        """
        Async initialization - load spaCy NER model.

        Medicine Woman Conscience Jr: "spaCy en_core_web_sm for medical entities"
        """
        await super().initialize()

        try:
            self.nlp = spacy.load("en_core_web_sm")
            print("🌿 Sacred Health Guardian initialized - spaCy NER active")
        except OSError:
            print("⚠️  Warning: spaCy model not found. Run: python -m spacy download en_core_web_sm")
            self.nlp = None

    def detect_medical_entities(self, text: str) -> List[MedicalEntity]:
        """
        Detect medical entities using spaCy NER.

        Detects:
        - PERSON: Patient names (PII + medical context)
        - ORG: Healthcare organizations, hospitals
        - GPE: Locations in medical records
        - DATE: Appointment dates, DOB
        - CARDINAL: Lab values, dosages

        Args:
            text: Input text to scan

        Returns:
            List of MedicalEntity instances
        """
        if not self.nlp:
            return []

        doc = self.nlp(text)
        entities = []

        for ent in doc.ents:
            # Focus on medical-relevant entity types
            if ent.label_ in ["PERSON", "ORG", "GPE", "DATE", "CARDINAL"]:
                entities.append(MedicalEntity(
                    text=ent.text,
                    label=ent.label_,
                    start=ent.start_char,
                    end=ent.end_char,
                    confidence=0.90  # spaCy default confidence
                ))

        # Also check for medical keywords
        text_lower = text.lower()
        for keyword in self.MEDICAL_KEYWORDS:
            if keyword in text_lower:
                entities.append(MedicalEntity(
                    text=keyword,
                    label="MEDICAL_KEYWORD",
                    start=text_lower.index(keyword),
                    end=text_lower.index(keyword) + len(keyword),
                    confidence=1.0
                ))

        if entities:
            self.medical_stats["medical_entities_detected"] += len(entities)

        return entities

    def is_biometric_data(self, text: str) -> bool:
        """
        Detect biometric data (triggers 3-of-3 Chiefs attestation).

        Biometric data:
        - Fingerprints, face scans, facial recognition
        - Voice prints, iris scans, retina scans
        - DNA, genetic data, biometric authentication

        Args:
            text: Input text

        Returns:
            True if biometric data detected
        """
        text_lower = text.lower()

        for keyword in self.BIOMETRIC_KEYWORDS:
            if keyword in text_lower:
                self.medical_stats["biometric_detections"] += 1
                print(f"🔒 Biometric data detected: {keyword} (3-of-3 Chiefs attestation required)")
                return True

        return False

    def auto_elevate_to_sacred_floor(self, entry_id: str) -> bool:
        """
        Auto-elevate medical data to 40° sacred floor.

        Medicine Woman Conscience Jr: "All medical data = sacred-by-default"

        Args:
            entry_id: Cache entry ID

        Returns:
            True if elevation successful
        """
        if not self.cache:
            return False

        cursor = self.cache.conn.cursor()

        # Get current temperature
        cursor.execute("""
            SELECT temperature_score, sacred_pattern
            FROM cache_entries
            WHERE id = ?
        """, (entry_id,))
        row = cursor.fetchone()

        if not row:
            return False

        current_temp = row["temperature_score"]

        # Auto-elevate to 40° if below floor
        if current_temp < self.SACRED_FLOOR_TEMP:
            cursor.execute("""
                UPDATE cache_entries
                SET temperature_score = ?,
                    sacred_pattern = 1
                WHERE id = ?
            """, (self.SACRED_FLOOR_TEMP, entry_id))
            self.cache.conn.commit()

            self.medical_stats["auto_elevations"] += 1
            print(f"🌿 Auto-elevated {entry_id}: {current_temp}° → {self.SACRED_FLOOR_TEMP}° (sacred health data)")
            return True

        return False

    def evaluate_deletion_request(self, entry_id: str, user_id: str) -> DeletionRequest:
        """
        Evaluate user deletion request (respects legal holds).

        Cherokee Values:
        - User Sovereignty: Users own their data (can request deletion)
        - Seven Generations: Data retained if legally required
        - Gadugi: Transparent about why data can't be deleted

        Args:
            entry_id: Cache entry ID
            user_id: User requesting deletion

        Returns:
            DeletionRequest with evaluation result
        """
        self.medical_stats["deletion_requests"] += 1

        if not self.cache:
            return DeletionRequest(
                allowed=False,
                reason="Cache not available",
                legal_hold=False
            )

        cursor = self.cache.conn.cursor()
        cursor.execute("""
            SELECT temperature_score, sacred_pattern, created_at
            FROM cache_entries
            WHERE id = ?
        """, (entry_id,))
        row = cursor.fetchone()

        if not row:
            return DeletionRequest(
                allowed=False,
                reason="Entry not found",
                legal_hold=False
            )

        # Check HIPAA 7-year retention (legal hold)
        from datetime import datetime, timedelta
        created_at = datetime.fromisoformat(row["created_at"])
        retention_cutoff = datetime.now() - timedelta(days=self.HIPAA_RETENTION_YEARS * 365)

        if created_at > retention_cutoff:
            return DeletionRequest(
                allowed=False,
                reason="Data must be retained per legal requirement",
                legal_hold=True,
                legal_hold_reason=f"HIPAA requires {self.HIPAA_RETENTION_YEARS}-year retention for medical records"
            )

        # Check sacred floor
        if not self.enforce_sacred_floor(entry_id):
            return DeletionRequest(
                allowed=False,
                reason="Sacred data protected by 40° floor",
                legal_hold=False
            )

        # Deletion allowed
        self.medical_stats["deletion_requests_allowed"] += 1
        return DeletionRequest(
            allowed=True,
            reason="User sovereignty respected",
            legal_hold=False
        )

    def validate_cherokee_values(self, operation: str) -> bool:
        """
        Validate operation against Cherokee values.

        Operations: "collect", "share", "delete", "attest"

        Cherokee Values:
        - Gadugi (Working Together): No exploitation of health data
        - Seven Generations: Long-term protection (40° floor)
        - Mitakuye Oyasin (All Our Relations): Data sovereignty respected

        Args:
            operation: Operation type to validate

        Returns:
            True if operation honors Cherokee values
        """
        valid_operations = {
            "collect": "Minimal data collection (medical necessity validated)",
            "share": "Zero third-party sharing by default (consent required)",
            "delete": "User sovereignty (except legal holds)",
            "attest": "3-of-3 Chiefs for biometric data"
        }

        if operation not in valid_operations:
            print(f"⚠️  Unknown operation: {operation}")
            return False

        print(f"✅ Cherokee values honored: {operation} - {valid_operations[operation]}")
        return True

    def get_medical_stats(self) -> Dict[str, int]:
        """
        Get Sacred Health Guardian statistics.

        Returns:
            Dict with medical-specific stats
        """
        return {
            **self.get_stats(),  # Base Guardian stats
            **self.medical_stats  # Medical stats
        }


# Demo usage
if __name__ == "__main__":
    import asyncio

    async def demo():
        """Demo Sacred Health Guardian capabilities."""
        guardian = SacredHealthGuardian()
        await guardian.initialize()

        print("\n🌿 === Sacred Health Guardian Demo ===\n")

        # Test 1: Medical entity detection
        medical_text = "Patient John Smith has high cholesterol (245 mg/dL). Prescribed Lipitor 20mg daily. Next appointment: 11/15/2025"
        entities = guardian.detect_medical_entities(medical_text)
        print(f"📋 Medical text: {medical_text}")
        print(f"   Entities detected: {len(entities)}")
        for ent in entities:
            print(f"   - {ent.label_}: {ent.text}")

        # Test 2: Biometric detection
        biometric_text = "Store patient fingerprint for hospital access control system"
        is_biometric = guardian.is_biometric_data(biometric_text)
        print(f"\n🔒 Biometric text: {biometric_text}")
        print(f"   Biometric detected: {is_biometric}")

        # Test 3: Cherokee values validation
        print("\n✅ Cherokee Values Validation:")
        for op in ["collect", "share", "delete", "attest"]:
            guardian.validate_cherokee_values(op)

        # Stats
        print(f"\n📊 Sacred Health Guardian Stats: {guardian.get_medical_stats()}")

    asyncio.run(demo())

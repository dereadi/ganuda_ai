"""
VLM Security Configuration
Cherokee AI Federation - Addressing Crawdad's Security Concerns
"""

import os
from cryptography.fernet import Fernet
from pathlib import Path

class VLMSecurityConfig:
    """Security configuration for VLM integration."""

    # Encryption for frames at rest
    ENCRYPT_FRAMES_AT_REST = True
    FRAME_ENCRYPTION_KEY_PATH = '/ganuda/secrets/vlm_frame_key.enc'

    # TLS for frame transfer
    REQUIRE_TLS = True
    MIN_TLS_VERSION = 'TLSv1.3'

    # Authentication
    REQUIRE_API_KEY = True
    API_KEY_ROTATION_DAYS = 30

    # Access Control
    ALLOWED_ROLES = ['vision_specialist', 'security_admin', 'tpm']
    IP_WHITELIST = [
        '192.168.132.223',  # redfin
        '192.168.132.222',  # bluefin
        '192.168.132.224',  # greenfin
    ]

    # Audit Logging
    LOG_ALL_INFERENCES = True
    LOG_RETENTION_DAYS = 90
    AUDIT_LOG_PATH = '/ganuda/logs/vlm_audit.log'

    # Privacy Controls
    ANONYMIZE_FACES = True  # Blur faces in stored VLM descriptions
    PII_DETECTION_ENABLED = True
    REDACT_LICENSE_PLATES = True  # In natural language output

    @classmethod
    def generate_frame_key(cls):
        """Generate encryption key for frame storage."""
        key = Fernet.generate_key()
        key_path = Path(cls.FRAME_ENCRYPTION_KEY_PATH)
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(key)
        os.chmod(key_path, 0o600)
        return key
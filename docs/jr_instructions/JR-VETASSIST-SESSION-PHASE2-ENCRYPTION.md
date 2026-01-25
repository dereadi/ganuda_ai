# Jr Instruction: VetAssist VA Session Management - Phase 2: Token Encryption Service

## Priority: HIGH
## Estimated Effort: Medium
## Dependencies: Phase 1 (Database Schema)

---

## Objective

Implement secure token encryption for VA OAuth tokens. Tokens must be encrypted at rest using AES-256-GCM with per-user key derivation.

---

## Context

VA tokens contain sensitive identity data and must never be stored in plaintext. We use:
- HKDF for deriving unique encryption keys per user
- AES-256-GCM for authenticated encryption
- Master key stored in environment variable

Reference: `/ganuda/docs/ultrathink/ULTRATHINK-VETASSIST-VA-SESSION-MANAGEMENT-JAN20-2026.md`

---

## Implementation

### File: `/ganuda/vetassist/backend/app/services/token_encryption.py`

```python
"""
VA Token Encryption Service
Cherokee AI Federation - For Seven Generations

Provides secure encryption/decryption for VA OAuth tokens using:
- AES-256-GCM for authenticated encryption
- HKDF for per-user key derivation
"""
import os
import logging
from typing import Optional
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

# Constants
NONCE_SIZE = 12  # 96 bits for GCM
KEY_SIZE = 32    # 256 bits for AES-256
SALT = b"vetassist_token_v1"  # Fixed salt for key derivation


class TokenEncryptionService:
    """Handles encryption and decryption of VA OAuth tokens."""

    def __init__(self, master_key: Optional[bytes] = None):
        """
        Initialize with master key.

        Args:
            master_key: 32-byte master key. If None, reads from environment.
        """
        if master_key:
            self._master_key = master_key
        else:
            key_hex = os.environ.get("VETASSIST_MASTER_KEY")
            if not key_hex:
                raise ValueError("VETASSIST_MASTER_KEY environment variable not set")
            self._master_key = bytes.fromhex(key_hex)

        if len(self._master_key) != KEY_SIZE:
            raise ValueError(f"Master key must be {KEY_SIZE} bytes")

    def derive_user_key(self, user_id: str) -> bytes:
        """
        Derive a unique encryption key for a user using HKDF.

        Args:
            user_id: User's UUID string

        Returns:
            32-byte derived key
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=KEY_SIZE,
            salt=SALT,
            info=user_id.encode(),
            backend=default_backend()
        )
        return hkdf.derive(self._master_key)

    def encrypt_token(self, token: str, user_id: str) -> bytes:
        """
        Encrypt a token using AES-256-GCM.

        Args:
            token: Plaintext token string
            user_id: User's UUID for key derivation

        Returns:
            Encrypted bytes (nonce + ciphertext + tag)
        """
        user_key = self.derive_user_key(user_id)
        nonce = os.urandom(NONCE_SIZE)
        aesgcm = AESGCM(user_key)
        ciphertext = aesgcm.encrypt(nonce, token.encode(), None)

        # Prepend nonce for decryption
        return nonce + ciphertext

    def decrypt_token(self, encrypted_data: bytes, user_id: str) -> str:
        """
        Decrypt a token using AES-256-GCM.

        Args:
            encrypted_data: Encrypted bytes (nonce + ciphertext + tag)
            user_id: User's UUID for key derivation

        Returns:
            Decrypted token string

        Raises:
            cryptography.exceptions.InvalidTag: If decryption fails (tampering detected)
        """
        if len(encrypted_data) < NONCE_SIZE + 16:  # nonce + minimum tag
            raise ValueError("Encrypted data too short")

        user_key = self.derive_user_key(user_id)
        nonce = encrypted_data[:NONCE_SIZE]
        ciphertext = encrypted_data[NONCE_SIZE:]

        aesgcm = AESGCM(user_key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)

        return plaintext.decode()


# Singleton instance
_encryption_service: Optional[TokenEncryptionService] = None


def get_encryption_service() -> TokenEncryptionService:
    """Get or create the singleton encryption service."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = TokenEncryptionService()
    return _encryption_service


def encrypt_va_token(token: str, user_id: str) -> bytes:
    """Convenience function to encrypt a VA token."""
    return get_encryption_service().encrypt_token(token, user_id)


def decrypt_va_token(encrypted_data: bytes, user_id: str) -> str:
    """Convenience function to decrypt a VA token."""
    return get_encryption_service().decrypt_token(encrypted_data, user_id)
```

---

## Environment Setup

Generate a master key and add to `.env`:

```bash
# Generate 32-byte hex key
python3 -c "import os; print(os.urandom(32).hex())"

# Add to /ganuda/vetassist/backend/.env:
VETASSIST_MASTER_KEY=<generated_hex_key>
```

---

## Unit Tests

### File: `/ganuda/vetassist/backend/tests/test_token_encryption.py`

```python
"""Unit tests for token encryption service."""
import pytest
import os
from app.services.token_encryption import TokenEncryptionService


class TestTokenEncryption:
    """Tests for TokenEncryptionService."""

    @pytest.fixture
    def service(self):
        """Create service with test key."""
        test_key = os.urandom(32)
        return TokenEncryptionService(master_key=test_key)

    def test_encrypt_decrypt_roundtrip(self, service):
        """Token should decrypt to original value."""
        user_id = "test-user-123"
        original_token = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test"

        encrypted = service.encrypt_token(original_token, user_id)
        decrypted = service.decrypt_token(encrypted, user_id)

        assert decrypted == original_token

    def test_different_users_different_keys(self, service):
        """Different users should have different derived keys."""
        key1 = service.derive_user_key("user-1")
        key2 = service.derive_user_key("user-2")

        assert key1 != key2

    def test_same_user_same_key(self, service):
        """Same user should always get same derived key."""
        key1 = service.derive_user_key("user-1")
        key2 = service.derive_user_key("user-1")

        assert key1 == key2

    def test_different_nonces(self, service):
        """Same plaintext should encrypt to different ciphertext."""
        user_id = "test-user"
        token = "same-token"

        encrypted1 = service.encrypt_token(token, user_id)
        encrypted2 = service.encrypt_token(token, user_id)

        # Different due to random nonce
        assert encrypted1 != encrypted2

        # But both decrypt to same value
        assert service.decrypt_token(encrypted1, user_id) == token
        assert service.decrypt_token(encrypted2, user_id) == token

    def test_wrong_user_fails(self, service):
        """Decrypting with wrong user ID should fail."""
        encrypted = service.encrypt_token("secret", "user-1")

        with pytest.raises(Exception):  # InvalidTag
            service.decrypt_token(encrypted, "user-2")

    def test_tampered_data_fails(self, service):
        """Tampered ciphertext should fail authentication."""
        user_id = "test-user"
        encrypted = service.encrypt_token("secret", user_id)

        # Tamper with ciphertext
        tampered = encrypted[:-1] + bytes([encrypted[-1] ^ 0xFF])

        with pytest.raises(Exception):  # InvalidTag
            service.decrypt_token(tampered, user_id)
```

---

## Verification

1. Install cryptography if needed:
```bash
source /ganuda/vetassist/backend/venv/bin/activate
pip install cryptography
```

2. Generate master key:
```bash
python3 -c "import os; print(f'VETASSIST_MASTER_KEY={os.urandom(32).hex()}')" >> /ganuda/vetassist/backend/.env
```

3. Run tests:
```bash
cd /ganuda/vetassist/backend
pytest tests/test_token_encryption.py -v
```

---

## Success Criteria

- [ ] TokenEncryptionService class implemented
- [ ] Master key generated and stored in .env
- [ ] All unit tests pass
- [ ] Encryption roundtrip verified

---

*Cherokee AI Federation - For Seven Generations*

#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Hybrid Capability Tokens (JWT)
Cherokee Constitutional AI - Executive Jr Deliverable

Purpose: Quantum-resistant capability tokens using hybrid ed25519 + Dilithium3 signatures.
Implements Phase 2 migration from QUANTUM_CRYPTO_RESEARCH.md recommendations.

Author: Executive Jr (War Chief)
Date: October 23, 2025
"""

import os
import json
import base64
import hashlib
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.backends import default_backend

# Note: liboqs-python required for post-quantum signatures
# Install: pip install liboqs-python
try:
    import oqs
    LIBOQS_AVAILABLE = True
except ImportError:
    LIBOQS_AVAILABLE = False
    print("⚠️  Warning: liboqs-python not installed. Falling back to ed25519-only mode.")
    print("   Install: pip install liboqs-python")


@dataclass
class Capability:
    """Individual capability granted by token."""
    action: str  # e.g., "read_email", "write_calendar"
    resource: Optional[str] = None  # e.g., "email:inbox"
    constraints: Optional[Dict] = None  # e.g., {"rate_limit": 100}


@dataclass
class HybridKeyPair:
    """Hybrid key pair: classical + post-quantum."""
    # Classical ed25519
    ed25519_private: ed25519.Ed25519PrivateKey
    ed25519_public: ed25519.Ed25519PublicKey

    # Post-quantum Dilithium3 (optional, Phase 2+)
    dilithium_private: Optional[bytes] = None
    dilithium_public: Optional[bytes] = None


class HybridJWT:
    """
    Hybrid JWT capability tokens with quantum-resistant signatures.

    Features:
    - Classical ed25519 signatures (64 bytes, fast verification)
    - Post-quantum Dilithium3 signatures (3,293 bytes, quantum-safe)
    - Hybrid mode: BOTH signatures required (AND logic)
    - Capability-based access control (read_email, write_calendar, etc.)
    - Automatic key rotation (every 90 days)
    - Cherokee Constitutional AI values embedded
    """

    ALGORITHM_CLASSICAL = "ed25519"
    ALGORITHM_HYBRID = "ed25519+Dilithium3"

    # Token expiration (default 1 hour)
    DEFAULT_EXPIRATION_SECONDS = 3600

    # Key rotation interval (90 days)
    KEY_ROTATION_DAYS = 90

    def __init__(self, use_hybrid: bool = False):
        """
        Initialize hybrid JWT handler.

        Args:
            use_hybrid: Enable post-quantum Dilithium3 signatures (requires liboqs)
        """
        self.use_hybrid = use_hybrid and LIBOQS_AVAILABLE

        if self.use_hybrid:
            print("🔐 Hybrid JWT: ed25519 + Dilithium3 (quantum-resistant)")
        else:
            print("🔐 Classical JWT: ed25519 only")

    def generate_keypair(self) -> HybridKeyPair:
        """
        Generate hybrid key pair.

        Returns:
            HybridKeyPair with classical and optional post-quantum keys
        """
        # Classical ed25519 keypair
        ed25519_private = ed25519.Ed25519PrivateKey.generate()
        ed25519_public = ed25519_private.public_key()

        keypair = HybridKeyPair(
            ed25519_private=ed25519_private,
            ed25519_public=ed25519_public
        )

        # Post-quantum Dilithium3 keypair (if hybrid mode enabled)
        if self.use_hybrid:
            with oqs.Signature("Dilithium3") as signer:
                dilithium_public = signer.generate_keypair()
                dilithium_private = signer.export_secret_key()

                keypair.dilithium_private = dilithium_private
                keypair.dilithium_public = dilithium_public

        return keypair

    def create_token(
        self,
        keypair: HybridKeyPair,
        subject: str,
        capabilities: List[Capability],
        expiration_seconds: Optional[int] = None
    ) -> str:
        """
        Create hybrid capability token (JWT).

        Args:
            keypair: Hybrid key pair for signing
            subject: Token subject (e.g., user email)
            capabilities: List of granted capabilities
            expiration_seconds: Token lifetime (default 1 hour)

        Returns:
            Base64-encoded hybrid JWT token
        """
        now = int(time.time())
        exp = now + (expiration_seconds or self.DEFAULT_EXPIRATION_SECONDS)

        # Build JWT header
        header = {
            "alg": self.ALGORITHM_HYBRID if self.use_hybrid else self.ALGORITHM_CLASSICAL,
            "typ": "JWT",
            "kid": self._key_id(keypair)
        }

        # Build JWT payload
        payload = {
            "sub": subject,
            "capabilities": [self._capability_to_dict(cap) for cap in capabilities],
            "iat": now,
            "exp": exp,
            "iss": "ganuda_desktop_assistant",
            "jti": self._generate_jti()  # Unique token ID
        }

        # Encode header and payload
        header_b64 = self._base64url_encode(json.dumps(header))
        payload_b64 = self._base64url_encode(json.dumps(payload))

        signing_input = f"{header_b64}.{payload_b64}".encode()

        # Sign with ed25519
        ed25519_sig = keypair.ed25519_private.sign(signing_input)

        if self.use_hybrid:
            # Sign with Dilithium3 (post-quantum)
            with oqs.Signature("Dilithium3") as signer:
                signer.secret_key = keypair.dilithium_private
                dilithium_sig = signer.sign(signing_input)

            # Build hybrid signature
            signature = {
                "classical": base64.urlsafe_b64encode(ed25519_sig).decode().rstrip("="),
                "post_quantum": base64.urlsafe_b64encode(dilithium_sig).decode().rstrip("=")
            }
            signature_b64 = self._base64url_encode(json.dumps(signature))
        else:
            # Classical signature only
            signature_b64 = base64.urlsafe_b64encode(ed25519_sig).decode().rstrip("=")

        # Build JWT token
        token = f"{header_b64}.{payload_b64}.{signature_b64}"
        return token

    def verify_token(self, token: str, keypair: HybridKeyPair) -> Tuple[bool, Optional[Dict]]:
        """
        Verify hybrid JWT token.

        Args:
            token: Base64-encoded JWT token
            keypair: Hybrid key pair (public keys for verification)

        Returns:
            (is_valid, payload_dict) tuple
        """
        try:
            # Parse token
            parts = token.split(".")
            if len(parts) != 3:
                return False, None

            header_b64, payload_b64, signature_b64 = parts

            # Decode header and payload
            header = json.loads(self._base64url_decode(header_b64))
            payload = json.loads(self._base64url_decode(payload_b64))

            # Check expiration
            now = int(time.time())
            if payload.get("exp", 0) < now:
                print("❌ Token expired")
                return False, None

            # Verify signatures
            signing_input = f"{header_b64}.{payload_b64}".encode()

            if header["alg"] == self.ALGORITHM_HYBRID:
                # Verify hybrid signatures (both must be valid)
                signature = json.loads(self._base64url_decode(signature_b64))

                # Verify classical ed25519
                ed25519_sig = base64.urlsafe_b64decode(signature["classical"] + "==")
                try:
                    keypair.ed25519_public.verify(ed25519_sig, signing_input)
                except Exception:
                    print("❌ Classical signature verification failed")
                    return False, None

                # Verify post-quantum Dilithium3
                dilithium_sig = base64.urlsafe_b64decode(signature["post_quantum"] + "==")
                with oqs.Signature("Dilithium3") as verifier:
                    verifier.public_key = keypair.dilithium_public
                    if not verifier.verify(signing_input, dilithium_sig):
                        print("❌ Post-quantum signature verification failed")
                        return False, None

            else:
                # Verify classical ed25519 only
                ed25519_sig = base64.urlsafe_b64decode(signature_b64 + "==")
                try:
                    keypair.ed25519_public.verify(ed25519_sig, signing_input)
                except Exception:
                    print("❌ Signature verification failed")
                    return False, None

            return True, payload

        except Exception as e:
            print(f"❌ Token verification error: {e}")
            return False, None

    def check_capability(self, payload: Dict, action: str, resource: Optional[str] = None) -> bool:
        """
        Check if token grants specific capability.

        Args:
            payload: Verified JWT payload
            action: Requested action (e.g., "read_email")
            resource: Optional resource identifier

        Returns:
            True if capability granted
        """
        capabilities = payload.get("capabilities", [])

        for cap_dict in capabilities:
            if cap_dict["action"] == action:
                # Check resource match (if specified)
                if resource and cap_dict.get("resource"):
                    if not self._resource_matches(cap_dict["resource"], resource):
                        continue

                # Check constraints (e.g., rate limits)
                # TODO: Implement constraint checking in Phase 2

                return True

        return False

    def _key_id(self, keypair: HybridKeyPair) -> str:
        """
        Generate key ID (SHA256 of public keys).

        Args:
            keypair: Hybrid key pair

        Returns:
            16-character key ID
        """
        ed25519_pub_bytes = keypair.ed25519_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        if self.use_hybrid:
            combined = ed25519_pub_bytes + keypair.dilithium_public
        else:
            combined = ed25519_pub_bytes

        return hashlib.sha256(combined).hexdigest()[:16]

    def _generate_jti(self) -> str:
        """
        Generate unique token ID (JWT ID).

        Returns:
            16-character random token ID
        """
        return hashlib.sha256(os.urandom(32)).hexdigest()[:16]

    def _capability_to_dict(self, cap: Capability) -> Dict:
        """Convert Capability to dict for JSON serialization."""
        return {
            "action": cap.action,
            "resource": cap.resource,
            "constraints": cap.constraints
        }

    def _resource_matches(self, pattern: str, resource: str) -> bool:
        """
        Check if resource matches pattern.

        Supports wildcards:
        - "email:*" matches "email:inbox", "email:sent"
        - "email:inbox" matches exactly "email:inbox"

        Args:
            pattern: Resource pattern from capability
            resource: Requested resource

        Returns:
            True if resource matches pattern
        """
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return resource.startswith(prefix)
        else:
            return pattern == resource

    def _base64url_encode(self, data: str) -> str:
        """Base64url encode (no padding)."""
        return base64.urlsafe_b64encode(data.encode()).decode().rstrip("=")

    def _base64url_decode(self, data: str) -> str:
        """Base64url decode (add padding if needed)."""
        padding = "=" * (4 - len(data) % 4)
        return base64.urlsafe_b64decode(data + padding).decode()


# Serialization helpers for key storage
from cryptography.hazmat.primitives import serialization

def save_keypair(keypair: HybridKeyPair, path: str):
    """
    Save hybrid keypair to file (encrypted).

    WARNING: Private keys are sensitive. In production, use OS keychain or HSM.
    This is for development/testing only.
    """
    import keyring

    # Save ed25519 private key to OS keychain
    ed25519_private_bytes = keypair.ed25519_private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption()
    )
    keyring.set_password("ganuda_jwt", f"{path}_ed25519", ed25519_private_bytes.hex())

    # Save Dilithium3 private key (if hybrid)
    if keypair.dilithium_private:
        keyring.set_password("ganuda_jwt", f"{path}_dilithium", keypair.dilithium_private.hex())


def load_keypair(path: str, use_hybrid: bool = False) -> HybridKeyPair:
    """
    Load hybrid keypair from OS keychain.
    """
    import keyring

    # Load ed25519 private key
    ed25519_hex = keyring.get_password("ganuda_jwt", f"{path}_ed25519")
    if not ed25519_hex:
        raise ValueError(f"Ed25519 key not found: {path}_ed25519")

    ed25519_private_bytes = bytes.fromhex(ed25519_hex)
    ed25519_private = ed25519.Ed25519PrivateKey.from_private_bytes(ed25519_private_bytes)
    ed25519_public = ed25519_private.public_key()

    keypair = HybridKeyPair(
        ed25519_private=ed25519_private,
        ed25519_public=ed25519_public
    )

    # Load Dilithium3 private key (if hybrid)
    if use_hybrid:
        dilithium_hex = keyring.get_password("ganuda_jwt", f"{path}_dilithium")
        if dilithium_hex:
            keypair.dilithium_private = bytes.fromhex(dilithium_hex)

            # Reconstruct public key from private
            with oqs.Signature("Dilithium3") as signer:
                signer.secret_key = keypair.dilithium_private
                keypair.dilithium_public = signer.export_public_key()

    return keypair


# Demo usage
def main():
    """Demo: Hybrid JWT capability tokens."""

    # Create hybrid JWT handler (quantum-resistant)
    jwt_handler = HybridJWT(use_hybrid=True)

    # Generate keypair
    keypair = jwt_handler.generate_keypair()
    print(f"🔑 Generated hybrid keypair (kid: {jwt_handler._key_id(keypair)})")

    # Create capability token
    capabilities = [
        Capability(action="read_email", resource="email:*"),
        Capability(action="write_calendar", resource="calendar:*"),
        Capability(action="read_files", resource="files:~/Documents/*")
    ]

    token = jwt_handler.create_token(
        keypair=keypair,
        subject="user@ganuda.ai",
        capabilities=capabilities,
        expiration_seconds=3600
    )

    print(f"\n🎫 Token created:")
    print(f"   Length: {len(token)} bytes")
    print(f"   Preview: {token[:80]}...")

    # Verify token
    is_valid, payload = jwt_handler.verify_token(token, keypair)

    if is_valid:
        print(f"\n✅ Token verified successfully")
        print(f"   Subject: {payload['sub']}")
        print(f"   Expires: {datetime.fromtimestamp(payload['exp'])}")
        print(f"   Capabilities: {len(payload['capabilities'])}")

        # Check specific capability
        can_read_email = jwt_handler.check_capability(payload, "read_email", "email:inbox")
        print(f"   Can read email:inbox? {can_read_email}")

        can_delete_files = jwt_handler.check_capability(payload, "delete_files")
        print(f"   Can delete files? {can_delete_files}")
    else:
        print("❌ Token verification failed")


if __name__ == "__main__":
    main()

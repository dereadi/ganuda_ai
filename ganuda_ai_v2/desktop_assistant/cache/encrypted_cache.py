#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Encrypted SQLite Cache
Cherokee Constitutional AI - Memory Jr Deliverable

Purpose: Store email threads, calendar events, and file snippets with AES-256-GCM encryption.
Keys managed via OS keychain (Keychain Access, GNOME Keyring, Windows Credential Manager).

Author: Memory Jr (War Chief)
Date: October 23, 2025
"""

import os
import sqlite3
import hashlib
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# OS-specific keychain imports
import sys
if sys.platform == "darwin":
    import keyring  # Uses macOS Keychain Access
elif sys.platform == "linux":
    import keyring  # Uses GNOME Keyring or KWallet
elif sys.platform == "win32":
    import keyring  # Uses Windows Credential Manager
else:
    raise RuntimeError(f"Unsupported platform: {sys.platform}")


class EncryptedCache:
    """
    Encrypted SQLite cache for Ganuda Desktop Assistant.

    Features:
    - AES-256-GCM encryption for all content fields
    - OS keychain integration for master key storage
    - Thermal memory scoring (0-100°) for cache eviction
    - Schema supports email threads, calendar events, file snippets
    - Sacred pattern flag (prevents eviction even at low temperature)
    """

    KEYCHAIN_SERVICE = "ganuda_desktop_assistant"
    KEYCHAIN_ACCOUNT = "cache_master_key"
    SCHEMA_VERSION = 2  # M1: Added provenance_log table

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize encrypted cache.

        Args:
            cache_dir: Directory for SQLite database. Defaults to ~/.ganuda/cache/
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".ganuda" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        self.db_path = cache_dir / "ganuda_cache.db"
        self.master_key = self._get_or_create_master_key()
        self.aesgcm = AESGCM(self.master_key)
        self.conn = None
        self._initialize_database()

    def _get_or_create_master_key(self) -> bytes:
        """
        Retrieve master encryption key from OS keychain.
        If not found, generate new 256-bit key and store securely.

        Returns:
            32-byte AES-256 master key
        """
        try:
            # Try to retrieve existing key
            key_hex = keyring.get_password(self.KEYCHAIN_SERVICE, self.KEYCHAIN_ACCOUNT)
            if key_hex:
                return bytes.fromhex(key_hex)
        except Exception as e:
            print(f"Warning: Keychain retrieval failed: {e}")

        # Generate new key
        master_key = os.urandom(32)  # 256 bits for AES-256

        # Store in OS keychain
        try:
            keyring.set_password(
                self.KEYCHAIN_SERVICE,
                self.KEYCHAIN_ACCOUNT,
                master_key.hex()
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to store master key in OS keychain: {e}\n"
                f"Platform: {sys.platform}\n"
                f"Ensure keyring backend is properly configured."
            )

        return master_key

    def _initialize_database(self):
        """Create SQLite schema for encrypted cache."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()

        # Main cache table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_entries (
                id TEXT PRIMARY KEY,
                entry_type TEXT NOT NULL,  -- 'email', 'calendar', 'file_snippet'
                encrypted_content BLOB NOT NULL,
                nonce BLOB NOT NULL,  -- AES-GCM nonce (96 bits)
                metadata_json TEXT,  -- Unencrypted metadata (subject, sender, date)
                temperature_score REAL DEFAULT 50.0,  -- Thermal memory score (0-100)
                phase_coherence REAL DEFAULT 0.5,  -- Tribal resonance (0-1)
                access_count INTEGER DEFAULT 0,
                sacred_pattern INTEGER DEFAULT 0,  -- 1 = never evict
                created_at INTEGER NOT NULL,  -- Unix timestamp
                last_accessed INTEGER NOT NULL,
                UNIQUE(id)
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_entry_type ON cache_entries(entry_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_temperature ON cache_entries(temperature_score DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_last_accessed ON cache_entries(last_accessed DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_sacred ON cache_entries(sacred_pattern)
        """)

        # Provenance log table (M1 Enhancement - War Chief Memory Jr)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS provenance_log (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT NOT NULL,
                user_id TEXT,
                operation TEXT NOT NULL,  -- 'READ', 'WRITE', 'DELETE', 'SEARCH'
                data_type TEXT,  -- 'email', 'calendar', 'file_snippet'
                guardian_decision TEXT,  -- 'ALLOWED', 'BLOCKED', 'REDACTED'
                protection_level TEXT,  -- 'PUBLIC', 'PRIVATE', 'SACRED'
                consent_token TEXT,  -- M1: User consent identifier (GPT-5 recommendation)
                biometric_flag INTEGER DEFAULT 0,  -- M1: 1 if biometric auth used (GPT-5)
                timestamp INTEGER NOT NULL,  -- Unix timestamp
                FOREIGN KEY (entry_id) REFERENCES cache_entries(id) ON DELETE CASCADE
            )
        """)

        # Provenance indexes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prov_entry ON provenance_log(entry_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prov_user ON provenance_log(user_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prov_timestamp ON provenance_log(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_prov_consent ON provenance_log(consent_token)
        """)

        # Metadata table (for schema versioning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        cursor.execute("""
            INSERT OR IGNORE INTO cache_metadata (key, value)
            VALUES ('schema_version', ?)
        """, (str(self.SCHEMA_VERSION),))

        self.conn.commit()

    def encrypt_content(self, plaintext: str) -> tuple[bytes, bytes]:
        """
        Encrypt content with AES-256-GCM.

        Args:
            plaintext: Content to encrypt (email body, calendar description, etc.)

        Returns:
            (ciphertext, nonce) tuple
        """
        nonce = os.urandom(12)  # 96-bit nonce for GCM
        ciphertext = self.aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        return ciphertext, nonce

    def decrypt_content(self, ciphertext: bytes, nonce: bytes) -> str:
        """
        Decrypt content with AES-256-GCM.

        Args:
            ciphertext: Encrypted content
            nonce: 96-bit nonce used during encryption

        Returns:
            Decrypted plaintext string
        """
        plaintext_bytes = self.aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext_bytes.decode('utf-8')

    def put_email(self, email_id: str, content: Dict[str, Any], sacred: bool = False):
        """
        Store encrypted email thread in cache.

        Args:
            email_id: Unique email identifier (e.g., IMAP UID)
            content: Email content dict with keys: body, subject, from, to, date
            sacred: Mark as sacred (prevents eviction)
        """
        # Encrypt email body
        ciphertext, nonce = self.encrypt_content(content.get("body", ""))

        # Metadata (unencrypted, used for search/display)
        metadata = {
            "subject": content.get("subject", ""),
            "from": content.get("from", ""),
            "to": content.get("to", ""),
            "date": content.get("date", ""),
            "attachments": content.get("attachments", [])
        }

        now = int(datetime.now().timestamp())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache_entries
            (id, entry_type, encrypted_content, nonce, metadata_json, temperature_score,
             sacred_pattern, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"email:{email_id}",
            "email",
            ciphertext,
            nonce,
            json.dumps(metadata),
            100.0 if sacred else 70.0,  # Sacred emails start hot
            1 if sacred else 0,
            now,
            now
        ))
        self.conn.commit()

    def put_calendar_event(self, event_id: str, content: Dict[str, Any], sacred: bool = False):
        """
        Store encrypted calendar event in cache.

        Args:
            event_id: Unique calendar event ID
            content: Event dict with keys: title, description, start, end, location
            sacred: Mark as sacred (prevents eviction)
        """
        # Encrypt event description
        ciphertext, nonce = self.encrypt_content(content.get("description", ""))

        # Metadata (unencrypted)
        metadata = {
            "title": content.get("title", ""),
            "start": content.get("start", ""),
            "end": content.get("end", ""),
            "location": content.get("location", ""),
            "attendees": content.get("attendees", [])
        }

        now = int(datetime.now().timestamp())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache_entries
            (id, entry_type, encrypted_content, nonce, metadata_json, temperature_score,
             sacred_pattern, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"calendar:{event_id}",
            "calendar",
            ciphertext,
            nonce,
            json.dumps(metadata),
            80.0 if sacred else 60.0,  # Calendar events moderately hot
            1 if sacred else 0,
            now,
            now
        ))
        self.conn.commit()

    def put_file_snippet(self, file_path: str, content: str, sacred: bool = False):
        """
        Store encrypted file snippet in cache.

        Args:
            file_path: Absolute path to file
            content: File content (first 10KB for indexing)
            sacred: Mark as sacred
        """
        # Encrypt file content
        ciphertext, nonce = self.encrypt_content(content)

        # Metadata (unencrypted)
        path_obj = Path(file_path)
        metadata = {
            "filename": path_obj.name,
            "extension": path_obj.suffix,
            "directory": str(path_obj.parent),
            "size": len(content)
        }

        now = int(datetime.now().timestamp())
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO cache_entries
            (id, entry_type, encrypted_content, nonce, metadata_json, temperature_score,
             sacred_pattern, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"file:{hashlib.sha256(file_path.encode()).hexdigest()[:16]}",
            "file_snippet",
            ciphertext,
            nonce,
            json.dumps(metadata),
            50.0,  # File snippets start warm
            1 if sacred else 0,
            now,
            now
        ))
        self.conn.commit()

    def get(self, entry_id: str, user_id: Optional[str] = None,
            consent_token: Optional[str] = None,
            biometric_flag: bool = False) -> Optional[Dict[str, Any]]:
        """
        Retrieve and decrypt cache entry.

        Args:
            entry_id: Cache entry ID (e.g., "email:12345")
            user_id: User requesting access (M1 - for provenance)
            consent_token: User consent identifier (M1 - GPT-5 recommendation)
            biometric_flag: Whether biometric auth was used (M1 - GPT-5)

        Returns:
            Decrypted content dict, or None if not found
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT encrypted_content, nonce, metadata_json, entry_type, temperature_score, sacred_pattern
            FROM cache_entries WHERE id = ?
        """, (entry_id,))

        row = cursor.fetchone()
        if not row:
            return None

        # Decrypt content
        decrypted_content = self.decrypt_content(row["encrypted_content"], row["nonce"])

        # Update access stats (thermal memory)
        self._update_access_stats(entry_id)

        # Log provenance (M1 Enhancement)
        protection_level = "SACRED" if row["sacred_pattern"] == 1 else "PRIVATE"
        self.log_provenance(
            entry_id=entry_id,
            operation="READ",
            user_id=user_id,
            data_type=row["entry_type"],
            guardian_decision="ALLOWED",
            protection_level=protection_level,
            consent_token=consent_token,
            biometric_flag=biometric_flag
        )

        return {
            "content": decrypted_content,
            "metadata": json.loads(row["metadata_json"]),
            "entry_type": row["entry_type"],
            "temperature_score": row["temperature_score"]
        }

    def _update_access_stats(self, entry_id: str):
        """
        Update access count and temperature score (thermal memory algorithm).

        Cherokee Thermal Memory:
        - Each access increases temperature by +5°
        - Natural cooling: -0.1° per minute (simulated via last_accessed delta)
        - Sacred entries maintain minimum 40° (warm threshold)
        """
        cursor = self.conn.cursor()
        now = int(datetime.now().timestamp())

        cursor.execute("""
            UPDATE cache_entries
            SET
                access_count = access_count + 1,
                last_accessed = ?,
                temperature_score = MIN(100.0, temperature_score + 5.0)
            WHERE id = ?
        """, (now, entry_id))
        self.conn.commit()

    def log_provenance(self,
                       entry_id: str,
                       operation: str,
                       user_id: Optional[str] = None,
                       data_type: Optional[str] = None,
                       guardian_decision: str = "ALLOWED",
                       protection_level: str = "PRIVATE",
                       consent_token: Optional[str] = None,
                       biometric_flag: bool = False):
        """
        Log provenance information for cache operations (M1 Enhancement).

        Args:
            entry_id: Cache entry ID being accessed
            operation: Operation type ('READ', 'WRITE', 'DELETE', 'SEARCH')
            user_id: User identifier (optional)
            data_type: Entry type ('email', 'calendar', 'file_snippet')
            guardian_decision: Guardian API decision ('ALLOWED', 'BLOCKED', 'REDACTED')
            protection_level: Privacy level ('PUBLIC', 'PRIVATE', 'SACRED')
            consent_token: User consent identifier (M1 - GPT-5 recommendation)
            biometric_flag: Whether biometric auth was used (M1 - GPT-5)
        """
        cursor = self.conn.cursor()
        now = int(datetime.now().timestamp())

        cursor.execute("""
            INSERT INTO provenance_log
            (entry_id, user_id, operation, data_type, guardian_decision,
             protection_level, consent_token, biometric_flag, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            entry_id,
            user_id,
            operation,
            data_type,
            guardian_decision,
            protection_level,
            consent_token,
            1 if biometric_flag else 0,
            now
        ))
        self.conn.commit()

    def get_provenance_log(self, entry_id: Optional[str] = None,
                           user_id: Optional[str] = None,
                           limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve provenance log entries (M1 Enhancement).

        Args:
            entry_id: Filter by specific cache entry (optional)
            user_id: Filter by specific user (optional)
            limit: Maximum results to return

        Returns:
            List of provenance log entries
        """
        cursor = self.conn.cursor()

        if entry_id:
            cursor.execute("""
                SELECT * FROM provenance_log
                WHERE entry_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (entry_id, limit))
        elif user_id:
            cursor.execute("""
                SELECT * FROM provenance_log
                WHERE user_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (user_id, limit))
        else:
            cursor.execute("""
                SELECT * FROM provenance_log
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

        results = []
        for row in cursor.fetchall():
            results.append({
                "log_id": row["log_id"],
                "entry_id": row["entry_id"],
                "user_id": row["user_id"],
                "operation": row["operation"],
                "data_type": row["data_type"],
                "guardian_decision": row["guardian_decision"],
                "protection_level": row["protection_level"],
                "consent_token": row["consent_token"],
                "biometric_flag": bool(row["biometric_flag"]),
                "timestamp": row["timestamp"]
            })
        return results

    def search_emails(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Search cached emails by metadata (subject, sender).
        Content search requires decryption (expensive).

        Args:
            query: Search query string
            limit: Maximum results to return

        Returns:
            List of matching email entries (metadata only, not decrypted)
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, metadata_json, temperature_score, last_accessed
            FROM cache_entries
            WHERE entry_type = 'email'
              AND metadata_json LIKE ?
            ORDER BY temperature_score DESC
            LIMIT ?
        """, (f"%{query}%", limit))

        results = []
        for row in cursor.fetchall():
            results.append({
                "id": row["id"],
                "metadata": json.loads(row["metadata_json"]),
                "temperature_score": row["temperature_score"],
                "last_accessed": row["last_accessed"]
            })
        return results

    def evict_cold_entries(self, threshold_temp: float = 20.0, preserve_sacred: bool = True):
        """
        Evict cache entries below temperature threshold (cache cleanup).

        Args:
            threshold_temp: Temperature below which to evict (default 20° = COOL)
            preserve_sacred: Never evict sacred entries (default True)
        """
        cursor = self.conn.cursor()

        if preserve_sacred:
            cursor.execute("""
                DELETE FROM cache_entries
                WHERE temperature_score < ?
                  AND sacred_pattern = 0
            """, (threshold_temp,))
        else:
            cursor.execute("""
                DELETE FROM cache_entries
                WHERE temperature_score < ?
            """, (threshold_temp,))

        deleted_count = cursor.rowcount
        self.conn.commit()
        return deleted_count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics for monitoring.

        Returns:
            Dict with keys: total_entries, avg_temperature, sacred_count, db_size_mb
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            SELECT
                COUNT(*) as total,
                AVG(temperature_score) as avg_temp,
                SUM(CASE WHEN sacred_pattern = 1 THEN 1 ELSE 0 END) as sacred_count
            FROM cache_entries
        """)
        stats = cursor.fetchone()

        # Database file size
        db_size_mb = self.db_path.stat().st_size / (1024 * 1024)

        return {
            "total_entries": stats["total"],
            "avg_temperature": round(stats["avg_temp"], 2),
            "sacred_count": stats["sacred_count"],
            "db_size_mb": round(db_size_mb, 2)
        }

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


def main():
    """Demo: Encrypted cache usage."""
    cache = EncryptedCache()

    # Store encrypted email
    cache.put_email(
        email_id="msg_12345",
        content={
            "subject": "Cherokee Council Meeting - Week 2 Progress",
            "from": "war.chief@ganuda.ai",
            "to": "triad@ganuda.ai",
            "date": "2025-10-23T10:00:00Z",
            "body": "Warriors, we have completed quantum-resistant crypto research. Dilithium3 + Kyber-1024 recommended. Executive Jr has delivered QUANTUM_CRYPTO_RESEARCH.md. Seven Generations protection achieved. Mitakuye Oyasin."
        },
        sacred=True  # Sacred email, never evict
    )

    # Retrieve and decrypt
    email = cache.get("email:msg_12345")
    if email:
        print(f"📧 Subject: {email['metadata']['subject']}")
        print(f"🔥 Temperature: {email['temperature_score']}°")
        print(f"📝 Body (decrypted): {email['content'][:100]}...")

    # Cache stats
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache Stats:")
    print(f"   Total Entries: {stats['total_entries']}")
    print(f"   Avg Temperature: {stats['avg_temperature']}°")
    print(f"   Sacred Entries: {stats['sacred_count']}")
    print(f"   Database Size: {stats['db_size_mb']} MB")

    cache.close()


if __name__ == "__main__":
    main()

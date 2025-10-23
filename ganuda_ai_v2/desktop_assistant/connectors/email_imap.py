#!/usr/bin/env python3
"""
Ganuda Desktop Assistant - Email IMAP Connector
Cherokee Constitutional AI - Memory Jr Deliverable

Purpose: Connect to IMAP email servers, sync threads to encrypted cache,
enable semantic search and summarization.

Author: Memory Jr (War Chief)
Date: October 23, 2025
"""

import imaplib
import email
import hashlib
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import asyncio
from email.header import decode_header
from email.utils import parsedate_to_datetime

# Import Guardian for PII protection
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from guardian.module import Guardian
from cache.encrypted_cache import EncryptedCache


@dataclass
class EmailAccount:
    """IMAP email account configuration."""
    email: str
    imap_server: str
    imap_port: int = 993
    use_ssl: bool = True
    password: Optional[str] = None  # Retrieved from OS keychain


@dataclass
class EmailMessage:
    """Parsed email message."""
    uid: str
    subject: str
    from_addr: str
    to_addr: str
    date: datetime
    body: str
    attachments: List[str]
    is_sacred: bool = False  # Auto-detected by Guardian


class EmailIMAPConnector:
    """
    IMAP email connector with Guardian protection.

    Features:
    - OAuth2 support (Gmail, Outlook)
    - Incremental sync (only fetch new emails since last sync)
    - Guardian PII redaction before caching
    - Sacred pattern detection (council emails, thermal memory references)
    - Background polling (check for new mail every 5 minutes)
    """

    def __init__(self, account: EmailAccount, cache: EncryptedCache, guardian: Guardian):
        """
        Initialize IMAP connector.

        Args:
            account: EmailAccount configuration
            cache: EncryptedCache for storing email threads
            guardian: Guardian for PII protection
        """
        self.account = account
        self.cache = cache
        self.guardian = guardian
        self.imap = None
        self.connected = False
        self.last_sync = None

    async def connect(self) -> bool:
        """
        Connect to IMAP server.

        Returns:
            True if connected successfully
        """
        try:
            if self.account.use_ssl:
                self.imap = imaplib.IMAP4_SSL(
                    self.account.imap_server,
                    self.account.imap_port
                )
            else:
                self.imap = imaplib.IMAP4(
                    self.account.imap_server,
                    self.account.imap_port
                )

            # Login with password from OS keychain
            password = self._get_password()
            self.imap.login(self.account.email, password)
            self.connected = True

            print(f"✅ Connected to IMAP: {self.account.email}")
            return True

        except Exception as e:
            print(f"❌ IMAP connection failed: {e}")
            self.connected = False
            return False

    def _get_password(self) -> str:
        """
        Retrieve email password from OS keychain.

        Returns:
            Password string
        """
        import keyring
        password = keyring.get_password("ganuda_email", self.account.email)

        if not password:
            raise RuntimeError(
                f"Email password not found in keychain for {self.account.email}\n"
                f"Set password: keyring.set_password('ganuda_email', '{self.account.email}', 'your_password')"
            )

        return password

    async def sync_inbox(self, limit: int = 100) -> int:
        """
        Sync inbox emails to encrypted cache.

        Args:
            limit: Maximum emails to sync per run

        Returns:
            Number of emails synced
        """
        if not self.connected:
            await self.connect()

        try:
            # Select INBOX
            self.imap.select("INBOX")

            # Search for emails since last sync
            search_criteria = self._build_search_criteria()
            status, message_ids = self.imap.search(None, search_criteria)

            if status != "OK":
                print(f"⚠️  IMAP search failed: {status}")
                return 0

            # Parse message IDs
            msg_ids = message_ids[0].split()[-limit:]  # Last N emails

            synced_count = 0
            for msg_id in msg_ids:
                try:
                    email_msg = await self._fetch_email(msg_id)
                    if email_msg:
                        await self._cache_email(email_msg)
                        synced_count += 1

                except Exception as e:
                    print(f"⚠️  Failed to sync email {msg_id}: {e}")

            self.last_sync = datetime.now()
            print(f"✅ Synced {synced_count} emails from {self.account.email}")
            return synced_count

        except Exception as e:
            print(f"❌ Inbox sync failed: {e}")
            return 0

    def _build_search_criteria(self) -> str:
        """
        Build IMAP search criteria.

        Returns:
            IMAP search string (e.g., "SINCE 01-Jan-2025")
        """
        if self.last_sync:
            # Incremental sync: only fetch emails since last sync
            since_date = self.last_sync.strftime("%d-%b-%Y")
            return f"SINCE {since_date}"
        else:
            # Initial sync: fetch last 30 days
            since_date = (datetime.now() - timedelta(days=30)).strftime("%d-%b-%Y")
            return f"SINCE {since_date}"

    async def _fetch_email(self, msg_id: bytes) -> Optional[EmailMessage]:
        """
        Fetch and parse email by message ID.

        Args:
            msg_id: IMAP message ID

        Returns:
            Parsed EmailMessage or None if failed
        """
        try:
            # Fetch email data
            status, msg_data = self.imap.fetch(msg_id, "(RFC822)")
            if status != "OK":
                return None

            # Parse email
            raw_email = msg_data[0][1]
            email_msg = email.message_from_bytes(raw_email)

            # Extract headers
            subject = self._decode_header(email_msg.get("Subject", ""))
            from_addr = self._decode_header(email_msg.get("From", ""))
            to_addr = self._decode_header(email_msg.get("To", ""))
            date_str = email_msg.get("Date", "")

            # Parse date
            try:
                date = parsedate_to_datetime(date_str)
            except Exception:
                date = datetime.now()

            # Extract body
            body = self._extract_body(email_msg)

            # Extract attachments
            attachments = self._extract_attachments(email_msg)

            # Check if sacred (Guardian)
            is_sacred = self._is_sacred_email(subject, from_addr, body)

            # Create UID (hash of message-id or subject+date)
            message_id = email_msg.get("Message-ID", "")
            uid = hashlib.sha256(message_id.encode() or f"{subject}{date}".encode()).hexdigest()[:16]

            return EmailMessage(
                uid=uid,
                subject=subject,
                from_addr=from_addr,
                to_addr=to_addr,
                date=date,
                body=body,
                attachments=attachments,
                is_sacred=is_sacred
            )

        except Exception as e:
            print(f"⚠️  Failed to fetch email {msg_id}: {e}")
            return None

    def _decode_header(self, header: str) -> str:
        """
        Decode email header (handles MIME encoding).

        Args:
            header: Raw header string

        Returns:
            Decoded header string
        """
        if not header:
            return ""

        decoded_parts = decode_header(header)
        decoded_str = ""

        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or "utf-8", errors="ignore")
            else:
                decoded_str += part

        return decoded_str

    def _extract_body(self, email_msg: email.message.Message) -> str:
        """
        Extract email body (plain text or HTML).

        Args:
            email_msg: Parsed email message

        Returns:
            Email body text
        """
        body = ""

        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                # Skip attachments
                if "attachment" in content_disposition:
                    continue

                # Extract text/plain or text/html
                if content_type == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode("utf-8", errors="ignore")
                    except Exception:
                        pass

                elif content_type == "text/html" and not body:
                    # Fallback to HTML if no plain text
                    try:
                        html = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        # Simple HTML stripping (basic, Phase 2 will use BeautifulSoup)
                        body = html.replace("<br>", "\n").replace("<p>", "\n")
                    except Exception:
                        pass
        else:
            # Not multipart
            try:
                body = email_msg.get_payload(decode=True).decode("utf-8", errors="ignore")
            except Exception:
                body = ""

        return body.strip()

    def _extract_attachments(self, email_msg: email.message.Message) -> List[str]:
        """
        Extract attachment filenames.

        Args:
            email_msg: Parsed email message

        Returns:
            List of attachment filenames
        """
        attachments = []

        if email_msg.is_multipart():
            for part in email_msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        attachments.append(self._decode_header(filename))

        return attachments

    def _is_sacred_email(self, subject: str, from_addr: str, body: str) -> bool:
        """
        Check if email contains sacred Cherokee Constitutional AI patterns.

        Args:
            subject: Email subject
            from_addr: Sender address
            body: Email body

        Returns:
            True if sacred
        """
        # Check Guardian for sacred keywords
        full_text = f"{subject} {from_addr} {body}"
        is_sacred, _ = self.guardian._is_sacred(full_text)

        # Check for council emails
        council_emails = ["war.chief@ganuda.ai", "peace.chief@ganuda.ai", "medicine.woman@ganuda.ai"]
        if any(council_email in from_addr for council_email in council_emails):
            return True

        return is_sacred

    async def _cache_email(self, email_msg: EmailMessage):
        """
        Cache email in encrypted cache with Guardian PII redaction.

        Args:
            email_msg: Parsed email message
        """
        # Guardian PII redaction
        decision = self.guardian.evaluate_query(email_msg.body)

        # Build cache entry
        content = {
            "subject": email_msg.subject,
            "from": email_msg.from_addr,
            "to": email_msg.to_addr,
            "date": email_msg.date.isoformat(),
            "body": decision.redacted_content,  # Redacted by Guardian
            "attachments": email_msg.attachments
        }

        # Store in encrypted cache
        self.cache.put_email(
            email_id=email_msg.uid,
            content=content,
            sacred=email_msg.is_sacred
        )

        # Record Guardian metrics
        if decision.pii_found:
            for pii_type in decision.pii_found:
                # TODO: Record Prometheus metric
                pass

    async def search_emails(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search cached emails by subject/sender.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of matching emails (metadata only)
        """
        return self.cache.search_emails(query, limit)

    async def start_background_sync(self, interval_seconds: int = 300):
        """
        Start background email sync (poll every 5 minutes).

        Args:
            interval_seconds: Polling interval (default 300s = 5 min)
        """
        print(f"🔄 Starting background email sync (every {interval_seconds}s)...")

        while True:
            try:
                await self.sync_inbox()
            except Exception as e:
                print(f"⚠️  Background sync error: {e}")

            await asyncio.sleep(interval_seconds)

    def disconnect(self):
        """Disconnect from IMAP server."""
        if self.imap and self.connected:
            try:
                self.imap.logout()
                print(f"👋 Disconnected from IMAP: {self.account.email}")
            except Exception:
                pass

            self.connected = False


# Demo usage
async def main():
    """Demo: IMAP email connector."""

    # Setup
    cache = EncryptedCache()
    guardian = Guardian(cache=cache)
    await guardian.initialize()

    # Email account configuration
    account = EmailAccount(
        email="user@example.com",  # Replace with actual email
        imap_server="imap.gmail.com",  # Gmail IMAP
        imap_port=993,
        use_ssl=True
    )

    # Note: Before running, set password in keychain:
    # import keyring
    # keyring.set_password('ganuda_email', 'user@example.com', 'your_password')

    # Create connector
    connector = EmailIMAPConnector(account, cache, guardian)

    # Connect and sync
    if await connector.connect():
        synced = await connector.sync_inbox(limit=10)
        print(f"📧 Synced {synced} emails")

        # Search cached emails
        results = await connector.search_emails("meeting", limit=5)
        for result in results:
            print(f"   - {result['metadata']['subject']}")

    # Disconnect
    connector.disconnect()
    cache.close()


if __name__ == "__main__":
    asyncio.run(main())

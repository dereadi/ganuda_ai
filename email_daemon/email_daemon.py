#!/usr/bin/env python3
"""
Cherokee Email Daemon
Polls IMAP, analyzes with AI, stores to PostgreSQL
"""

import imaplib
import email
from email.header import decode_header
import time
import logging
import psycopg2
from datetime import datetime
import json

class CherokeeEmailDaemon:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger("email_daemon")
        self.running = False

    def connect_imap(self):
        """Connect to IMAP server"""
        if self.config.get("ssl", True):
            self.mail = imaplib.IMAP4_SSL(
                self.config["server"],
                self.config.get("port", 993)
            )
        else:
            self.mail = imaplib.IMAP4(
                self.config["server"],
                self.config.get("port", 143)
            )
        self.mail.login(self.config["email"], self.config["password"])
        self.mail.select("INBOX")
        self.logger.info(f"Connected to {self.config['server']}")

    def fetch_new_emails(self, since_date=None):
        """Fetch emails since date"""
        if since_date:
            search_criteria = f'(SINCE "{since_date.strftime("%d-%b-%Y")}")'
        else:
            search_criteria = "ALL"

        _, messages = self.mail.search(None, search_criteria)
        email_ids = messages[0].split()

        emails = []
        for eid in email_ids[-50:]:  # Last 50
            _, msg_data = self.mail.fetch(eid, "(RFC822)")
            email_body = msg_data[0][1]
            msg = email.message_from_bytes(email_body)

            # Decode subject
            subject, encoding = decode_header(msg["Subject"])[0]
            if isinstance(subject, bytes):
                subject = subject.decode(encoding or "utf-8")

            # Extract body
            body_text = ""
            body_html = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    if ctype == "text/plain":
                        body_text = part.get_payload(decode=True).decode()
                    elif ctype == "text/html":
                        body_html = part.get_payload(decode=True).decode()
            else:
                body_text = msg.get_payload(decode=True).decode()

            emails.append({
                "message_id": msg["Message-ID"],
                "from_address": msg["From"],
                "to_addresses": msg["To"],
                "subject": subject,
                "body_text": body_text,
                "body_html": body_html,
                "received_at": msg["Date"]
            })

        return emails

    def analyze_email(self, email_data):
        """Run AI analysis on email"""
        # TODO: Integrate with Cherokee AI
        # For now, simple keyword analysis
        urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline']
        text = (email_data["subject"] + " " + email_data["body_text"]).lower()

        priority = 5  # Default medium
        action_required = False
        thermal_temp = 0.5

        for kw in urgent_keywords:
            if kw in text:
                priority = min(priority, 2)
                action_required = True
                thermal_temp = 0.8
                break

        return {
            "priority_score": priority,
            "action_required": action_required,
            "thermal_temp": thermal_temp,
            "sentiment": "neutral",  # TODO: AI sentiment
            "ai_summary": email_data["subject"][:200]  # TODO: AI summary
        }

    def store_email(self, email_data, analysis):
        """Store email and analysis to PostgreSQL"""
        conn = psycopg2.connect(
            host=self.config["db_host"],
            database=self.config["db_name"],
            user=self.config["db_user"],
            password=self.config["db_password"]
        )
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO emails (
                message_id, from_address, to_addresses, subject,
                body_text, body_html, received_at,
                thermal_temp, priority_score, sentiment,
                action_required, ai_summary
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (message_id) DO NOTHING
        """, (
            email_data["message_id"],
            email_data["from_address"],
            email_data.get("to_addresses"),
            email_data["subject"],
            email_data["body_text"],
            email_data.get("body_html"),
            email_data["received_at"],
            analysis["thermal_temp"],
            analysis["priority_score"],
            analysis["sentiment"],
            analysis["action_required"],
            analysis["ai_summary"]
        ))

        conn.commit()
        cur.close()
        conn.close()

    def run(self, poll_interval=300):
        """Main daemon loop"""
        self.running = True
        self.connect_imap()

        while self.running:
            try:
                emails = self.fetch_new_emails()
                self.logger.info(f"Fetched {len(emails)} emails")

                for email_data in emails:
                    analysis = self.analyze_email(email_data)
                    self.store_email(email_data, analysis)
                    self.logger.info(f"Stored: {email_data['subject'][:50]}")

            except Exception as e:
                self.logger.error(f"Daemon error: {e}")

            # Sleep with interrupt check
            for _ in range(poll_interval):
                if not self.running:
                    break
                time.sleep(1)

    def stop(self):
        """Stop the daemon"""
        self.running = False
        if hasattr(self, 'mail'):
            self.mail.logout()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="/ganuda/email_daemon/config.json")
    args = parser.parse_args()

    with open(args.config) as f:
        config = json.load(f)

    logging.basicConfig(level=logging.INFO)
    daemon = CherokeeEmailDaemon(config)
    daemon.run()
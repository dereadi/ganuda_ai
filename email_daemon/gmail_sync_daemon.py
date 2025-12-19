#!/usr/bin/env python3
"""
Cherokee Email Sync Daemon
Continuously syncs Gmail to PostgreSQL with AI analysis
"""

import pickle
import os
import time
import logging
import psycopg2
from datetime import datetime, timezone
import json
import base64
from email.utils import parsedate_to_datetime
import signal
from job_classifier import is_job_related, classify_job_email, extract_company_position
from telegram_alerts import send_job_alert

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('email_daemon')

class EmailSyncDaemon:
    def __init__(self, config_path='/ganuda/email_daemon/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)
        self.running = True
        self.service = None
        self.conn = None
        signal.signal(signal.SIGTERM, self._handle_shutdown)
        signal.signal(signal.SIGINT, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info('Shutdown signal received')
        self.running = False

    def connect_gmail(self):
        token_path = os.path.expanduser('~/.gmail_credentials/token.pickle')
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        if creds and creds.expired and creds.refresh_token:
            logger.info('Refreshing expired token')
            creds.refresh(Request())
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info('Connected to Gmail API')

    def connect_db(self):
        self.conn = psycopg2.connect(
            host=self.config['db_host'],
            database=self.config['db_name'],
            user=self.config['db_user'],
            password=self.config['db_password']
        )
        logger.info(f"Connected to PostgreSQL at {self.config['db_host']}")

    def fetch_and_sync_emails(self, max_results=50):
        cur = self.conn.cursor()
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX']
        ).execute()
        messages = results.get('messages', [])
        inserted = 0

        for msg in messages:
            try:
                full_msg = self.service.users().messages().get(
                    userId='me', id=msg['id'], format='full'
                ).execute()
                headers = {h['name']: h['value'] for h in full_msg['payload'].get('headers', [])}
                message_id = headers.get('Message-ID', msg['id'])
                subject = headers.get('Subject', '')[:1000]
                from_addr = headers.get('From', '')[:255]
                to_addrs = [headers.get('To', '')]
                thread_id = full_msg.get('threadId', '')
                labels = full_msg.get('labelIds', [])

                date_str = headers.get('Date', '')
                try:
                    date_received = parsedate_to_datetime(date_str)
                except:
                    date_received = datetime.now(timezone.utc)

                body_text = self._extract_body(full_msg['payload'])
                priority_score = self._calculate_priority(subject, from_addr, labels)
                action_required = self._detect_action_required(subject, body_text)
                thermal_temp = 0.5 + (priority_score * 0.3) + (0.2 if action_required else 0)

                cur.execute('''
                    INSERT INTO emails (message_id, thread_id, subject, from_address, to_addresses,
                                       date_received, body_text, labels, thermal_temp,
                                       priority_score, action_required, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (message_id) DO UPDATE SET
                        thermal_temp = EXCLUDED.thermal_temp,
                        priority_score = EXCLUDED.priority_score,
                        action_required = EXCLUDED.action_required,
                        updated_at = NOW()
                    RETURNING id
                ''', (message_id, thread_id, subject, from_addr, to_addrs,
                      date_received, body_text, labels, thermal_temp,
                      priority_score, action_required))
                if cur.fetchone():
                    inserted += 1
            except Exception as e:
                logger.error(f'Error processing message {msg["id"]}: {e}')

        self.conn.commit()
        cur.close()
        if inserted > 0:
            logger.info(f'Synced {inserted} emails')
        return inserted

    def _extract_body(self, payload, max_length=5000):
        body_text = ''
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                    body_text = base64.urlsafe_b64decode(
                        part['body']['data']
                    ).decode('utf-8', errors='ignore')[:max_length]
                    break
        elif 'body' in payload and payload['body'].get('data'):
            body_text = base64.urlsafe_b64decode(
                payload['body']['data']
            ).decode('utf-8', errors='ignore')[:max_length]
        return body_text

    def _calculate_priority(self, subject, from_addr, labels):
        score = 0.3
        if 'IMPORTANT' in labels:
            score += 0.3
        if 'STARRED' in labels:
            score += 0.2
        urgent_words = ['urgent', 'asap', 'immediately', 'action required', 'deadline', 'critical']
        subject_lower = subject.lower()
        for word in urgent_words:
            if word in subject_lower:
                score += 0.1
        priority_domains = ['fidelity.com', 'irs.gov', 'va.gov', 'bank']
        from_lower = from_addr.lower()
        for domain in priority_domains:
            if domain in from_lower:
                score += 0.2
                break
        return min(score, 1.0)

    def _detect_action_required(self, subject, body_text):
        action_keywords = ['action required', 'please respond', 'please reply',
                          'confirm', 'verify', 'review', 'sign', 'approve', 'deadline']
        text = (subject + ' ' + body_text[:500]).lower()
        return any(keyword in text for keyword in action_keywords)

    def run(self):
        logger.info('Starting Cherokee Email Sync Daemon')
        self.connect_gmail()
        self.connect_db()
        poll_interval = self.config.get('poll_interval', 300)
        logger.info(f'Poll interval: {poll_interval} seconds')

        while self.running:
            try:
                self.fetch_and_sync_emails()
            except Exception as e:
                logger.error(f'Sync error: {e}')
                try:
                    self.connect_gmail()
                    self.connect_db()
                except Exception as reconnect_error:
                    logger.error(f'Reconnect failed: {reconnect_error}')

            for _ in range(poll_interval):
                if not self.running:
                    break
                time.sleep(1)

        logger.info('Daemon stopped')
        if self.conn:
            self.conn.close()

if __name__ == '__main__':
    daemon = EmailSyncDaemon()
    daemon.run()
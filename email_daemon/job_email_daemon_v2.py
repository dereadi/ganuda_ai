#!/usr/bin/env python3
"""
Cherokee Job Email Monitor v2
With job matching/scoring and enhanced alerts
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

from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from job_classifier import is_job_related, classify_job_email, extract_company_position
from job_matcher import score_job, categorize_job, should_alert
from telegram_alerts import send_job_alert

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('job_email_daemon')

class JobEmailDaemon:
    def __init__(self):
        self.config = {
            'db_host': '192.168.132.222',
            'db_name': 'triad_federation', 
            'db_user': 'claude',
            'db_password': os.environ.get('CHEROKEE_DB_PASS', ''),
            'poll_interval': 300
        }
        self.running = True
        self.service = None
        self.conn = None
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _shutdown(self, *args):
        logger.info('Shutdown signal')
        self.running = False

    def connect_gmail(self):
        token_path = os.path.expanduser('~/.gmail_credentials/token.pickle')
        with open(token_path, 'rb') as f:
            creds = pickle.load(f)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'wb') as f:
                pickle.dump(creds, f)
        self.service = build('gmail', 'v1', credentials=creds)
        logger.info('Connected to Gmail')

    def connect_db(self):
        self.conn = psycopg2.connect(host=self.config["db_host"], database=self.config["db_name"], user=self.config["db_user"], password=self.config["db_password"])
        logger.info('Connected to database')

    def sync_and_classify(self, max_results=50):
        cur = self.conn.cursor()
        results = self.service.users().messages().list(
            userId='me', maxResults=max_results, labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        new_jobs = 0
        high_matches = 0

        for msg in messages:
            try:
                full_msg = self.service.users().messages().get(userId='me', id=msg['id'], format='full').execute()
                headers = {h['name']: h['value'] for h in full_msg['payload'].get('headers', [])}
                
                message_id = headers.get('Message-ID', msg['id'])
                subject = headers.get('Subject', '')[:1000]
                from_addr = headers.get('From', '')[:255]
                
                # Check if already processed
                cur.execute("SELECT job_alert_sent FROM emails WHERE message_id = %s", (message_id,))
                existing = cur.fetchone()
                
                if existing:
                    continue  # Skip already synced
                
                # Extract body
                body_text = ''
                payload = full_msg['payload']
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                            body_text = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8', errors='ignore')[:2000]
                            break
                elif payload['body'].get('data'):
                    body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')[:2000]

                # Classify email type
                job_class, priority = None, 5
                job_company, job_position = None, None
                match_score = 0.0
                match_category = None
                match_reasoning = None
                
                if is_job_related(from_addr, subject):
                    job_class, priority = classify_job_email(from_addr, subject, body_text)
                    job_company, job_position = extract_company_position(from_addr, subject, body_text)
                    
                    # Score against profile
                    job_data = {
                        'title': subject,
                        'body': body_text,
                        'company': job_company or from_addr
                    }
                    match_score, match_reasoning = score_job(job_data)
                    match_category = categorize_job(match_score)

                # Parse date
                try:
                    date_received = parsedate_to_datetime(headers.get('Date', ''))
                except:
                    date_received = datetime.now(timezone.utc)

                # Insert with match score
                cur.execute("""
                    INSERT INTO emails (message_id, thread_id, subject, from_address, 
                        date_received, body_text, labels, job_classification, 
                        job_company, job_position, match_score, match_category, 
                        match_reasoning, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (message_id) DO UPDATE SET
                        job_classification = EXCLUDED.job_classification,
                        job_company = EXCLUDED.job_company,
                        job_position = EXCLUDED.job_position,
                        match_score = EXCLUDED.match_score,
                        match_category = EXCLUDED.match_category,
                        match_reasoning = EXCLUDED.match_reasoning
                    RETURNING id
                """, (
                    message_id, full_msg.get('threadId'), subject, from_addr,
                    date_received, body_text, full_msg.get('labelIds', []),
                    job_class, job_company, job_position, match_score, 
                    match_category, match_reasoning
                ))
                
                email_id = cur.fetchone()
                
                # Send alert based on match score AND classification
                if job_class and should_alert(match_score, job_class):
                    email_data = {
                        'message_id': message_id,
                        'from_address': from_addr,
                        'subject': subject,
                        'job_company': job_company,
                        'job_position': job_position,
                        'body_text': body_text[:500],
                        'date_received': date_received,
                        'match_score': match_score,
                        'match_category': match_category,
                        'match_reasoning': match_reasoning
                    }
                    
                    # Override priority based on match score
                    if match_score >= 0.60:
                        priority = 1
                        high_matches += 1
                    elif match_score >= 0.35:
                        priority = 2
                    
                    alert_sent = send_job_alert_v2(email_data, job_class, priority)
                    
                    if alert_sent:
                        cur.execute("UPDATE emails SET job_alert_sent = TRUE WHERE id = %s", (email_id,))
                        logger.info(f"🔔 ALERT: [{match_category}] {match_score:.0%} - {subject[:50]}")
                        new_jobs += 1

            except Exception as e:
                logger.error(f"Error: {e}")

        self.conn.commit()
        if new_jobs:
            logger.info(f"Sent {new_jobs} job alerts ({high_matches} high matches)")

    def run(self):
        logger.info('Starting Job Email Monitor v2')
        self.connect_gmail()
        self.connect_db()
        
        while self.running:
            try:
                self.sync_and_classify()
            except Exception as e:
                logger.error(f"Sync error: {e}")
                try:
                    self.connect_gmail()
                    self.connect_db()
                except:
                    pass
            
            for _ in range(self.config['poll_interval']):
                if not self.running:
                    break
                time.sleep(1)
        
        logger.info('Daemon stopped')


def send_job_alert_v2(email: dict, classification: str, priority: int) -> bool:
    """Enhanced alert with match score."""
    import requests
    
    TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
    TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '8025375307')
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    score = email.get('match_score', 0)
    category = email.get('match_category', 'unknown')
    reasoning = email.get('match_reasoning', '')
    
    # Category emoji
    cat_emoji = {'high_match': '🎯', 'medium_match': '👀', 'low_match': '📋'}.get(category, '📧')
    class_emoji = {'offer': '💰', 'interview': '📅', 'next_steps': '➡️', 'recruiter': '👤', 'application': '📝'}.get(classification, '📧')
    
    # Escape HTML
    def esc(text):
        return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    message = f"{cat_emoji} {class_emoji} <b>Job Match: {score:.0%}</b> [{category}]\n\n"
    message += f"<b>Type:</b> {classification}\n"
    message += f"<b>From:</b> {esc(email.get('from_address', '')[:50])}\n"
    message += f"<b>Subject:</b> {esc(email.get('subject', '')[:80])}\n"
    
    if email.get('job_company'):
        message += f"<b>Company:</b> {esc(email.get('job_company'))}\n"
    if email.get('job_position'):
        message += f"<b>Position:</b> {esc(email.get('job_position'))}\n"
    
    if reasoning:
        message += f"\n<i>Match: {esc(reasoning[:100])}</i>\n"
    
    # Gmail link
    msg_id = email.get('message_id', '')
    if msg_id:
        message += f"\n<a href='https://mail.google.com/mail/u/0/#search/rfc822msgid:{msg_id}'>Open in Gmail</a>"
    
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'HTML', 'disable_web_page_preview': True},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f'Telegram error: {e}')
        return False


if __name__ == '__main__':
    JobEmailDaemon().run()

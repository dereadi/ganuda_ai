#!/usr/bin/env python3
"""
Cherokee Email Daemon - Gmail API Version
Uses OAuth token from ~/.gmail_credentials/token.pickle
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

from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GmailAPIDaemon:
    def __init__(self, config_path='/ganuda/email_daemon/config.json'):
        with open(config_path) as f:
            self.config = json.load(f)
        
        self.logger = logging.getLogger('gmail_daemon')
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s'))
        self.logger.addHandler(handler)
        
        self.running = False
        self.service = None
        self.last_history_id = None
        
    def connect_gmail(self):
        """Connect to Gmail using OAuth token"""
        token_path = os.path.expanduser('~/.gmail_credentials/token.pickle')
        
        if not os.path.exists(token_path):
            raise FileNotFoundError(f'Token not found at {token_path}. Run gmail_oauth_generate_url.py first.')
        
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('gmail', 'v1', credentials=creds)
        self.logger.info('Connected to Gmail API')
        
        # Get initial history ID
        profile = self.service.users().getProfile(userId='me').execute()
        self.last_history_id = profile.get('historyId')
        self.logger.info(f'Starting history ID: {self.last_history_id}')
        
    def fetch_recent_emails(self, max_results=20):
        """Fetch recent emails"""
        emails = []
        
        results = self.service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            labelIds=['INBOX']
        ).execute()
        
        messages = results.get('messages', [])
        
        for msg in messages:
            try:
                full_msg = self.service.users().messages().get(
                    userId='me', 
                    id=msg['id'],
                    format='full'
                ).execute()
                
                headers = {h['name']: h['value'] for h in full_msg['payload'].get('headers', [])}
                
                # Extract body
                body_text = ''
                body_html = ''
                payload = full_msg['payload']
                
                if 'parts' in payload:
                    for part in payload['parts']:
                        if part['mimeType'] == 'text/plain':
                            body_text = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8', errors='ignore')
                        elif part['mimeType'] == 'text/html':
                            body_html = base64.urlsafe_b64decode(part['body'].get('data', '')).decode('utf-8', errors='ignore')
                elif 'body' in payload and payload['body'].get('data'):
                    body_text = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8', errors='ignore')
                
                # Parse date
                date_str = headers.get('Date', '')
                try:
                    received_at = parsedate_to_datetime(date_str)
                except:
                    received_at = datetime.now(timezone.utc)
                
                emails.append({
                    'message_id': headers.get('Message-ID', msg['id']),
                    'gmail_id': msg['id'],
                    'from_address': headers.get('From', ''),
                    'to_addresses': headers.get('To', ''),
                    'subject': headers.get('Subject', '(no subject)'),
                    'body_text': body_text,
                    'body_html': body_html,
                    'received_at': received_at,
                    'labels': full_msg.get('labelIds', [])
                })
                
            except Exception as e:
                self.logger.error(f'Error fetching message {msg["id"]}: {e}')
                
        return emails
    
    def analyze_email(self, email_data):
        """LLM-backed email triage via federation gateway."""
        import requests as http_req

        subject = email_data.get('subject', '')
        body = email_data.get('body_text', '')[:1500]
        from_addr = email_data.get('from_address', '')

        # Fast keyword pre-filter for obvious spam/noise
        noise_signals = ['unsubscribe', 'no-reply', 'noreply', 'donotreply',
                         'marketing', 'newsletter', 'promotional']
        combined_lower = (subject + ' ' + body + ' ' + from_addr).lower()
        if any(sig in combined_lower for sig in noise_signals):
            return {
                'priority_score': 5,
                'action_required': False,
                'thermal_temp': 0.3,
                'sentiment': 'neutral',
                'classification': 'noise',
                'ai_summary': subject[:200],
                'action_deadline': None,
            }

        # LLM classification via gateway
        prompt = f"""Classify this email for triage. Respond in EXACTLY this format:
CLASSIFICATION: [ACTIONABLE|JEWEL|NOISE]
PRIORITY: [1-5] (1=respond today, 2=respond within 48h, 3=this week, 4=eventually, 5=ignore)
ACTION_DEADLINE: [date/time if mentioned, or NONE]
ACTION_REQUIRED: [one sentence describing what Chief needs to do, or NONE]
SUMMARY: [one sentence summary]

Email from: {from_addr}
Subject: {subject}
Body: {body}

ACTIONABLE means: scheduling a call, interview, meeting, deadline, someone waiting for a reply, calendar invite, payment due, contract to sign.
JEWEL means: interesting article, industry news, networking opportunity, job posting worth considering — no immediate action needed.
NOISE means: marketing, automated notifications, newsletters, spam, receipts."""

        try:
            resp = http_req.post(
                'http://localhost:8080/v1/chat/completions',
                json={
                    'model': 'qwen2.5-72b',
                    'messages': [{'role': 'user', 'content': prompt}],
                    'max_tokens': 200,
                    'temperature': 0.1,
                },
                timeout=30,
            )
            resp.raise_for_status()
            llm_text = resp.json()['choices'][0]['message']['content']

            # Parse LLM response
            classification = 'noise'
            priority = 5
            action_required_text = None
            action_deadline = None
            summary = subject[:200]

            for line in llm_text.strip().split('\n'):
                line = line.strip()
                if line.startswith('CLASSIFICATION:'):
                    raw = line.split(':', 1)[1].strip().upper()
                    if raw in ('ACTIONABLE', 'JEWEL', 'NOISE'):
                        classification = raw.lower()
                if line.startswith('PRIORITY:'):
                    try:
                        priority = int(line.split(':', 1)[1].strip()[0])
                        priority = max(1, min(5, priority))
                    except (ValueError, IndexError):
                        pass
                if line.startswith('ACTION_DEADLINE:'):
                    val = line.split(':', 1)[1].strip()
                    if val.upper() != 'NONE':
                        action_deadline = val
                if line.startswith('ACTION_REQUIRED:'):
                    val = line.split(':', 1)[1].strip()
                    if val.upper() != 'NONE':
                        action_required_text = val
                if line.startswith('SUMMARY:'):
                    summary = line.split(':', 1)[1].strip()[:200]

        except Exception as e:
            self.logger.warning(f'LLM triage failed, falling back to keyword: {e}')
            # Keyword fallback
            classification = 'noise'
            priority = 5
            action_required_text = None
            action_deadline = None
            summary = subject[:200]
            urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline',
                               'schedule', 'call', 'interview', 'meeting', 'calendar']
            for kw in urgent_keywords:
                if kw in combined_lower:
                    classification = 'actionable'
                    priority = 2
                    action_required_text = f'Email contains keyword: {kw}'
                    break

        # Gmail label boost
        labels = email_data.get('labels', [])
        if 'IMPORTANT' in labels:
            priority = min(priority, 3)
        if 'STARRED' in labels:
            priority = min(priority, 2)
            if classification == 'noise':
                classification = 'jewel'

        thermal_temp = {1: 0.9, 2: 0.8, 3: 0.7, 4: 0.5, 5: 0.3}.get(priority, 0.5)

        return {
            'priority_score': priority,
            'action_required': action_required_text is not None,
            'action_required_text': action_required_text,
            'thermal_temp': thermal_temp,
            'sentiment': 'neutral',
            'classification': classification,
            'ai_summary': summary,
            'action_deadline': action_deadline,
        }
    
    def store_email(self, email_data, analysis):
        """Store to PostgreSQL"""
        conn = psycopg2.connect(
            host=self.config.get('db_host', 'localhost'),
            database=self.config.get('db_name', 'bmasass_spoke'),
            user=self.config.get('db_user', 'claude'),
            password=self.config.get('db_password', os.environ.get('CHEROKEE_DB_PASS', ''))
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
            RETURNING id
        """, (
            email_data['message_id'],
            email_data['from_address'],
            email_data['to_addresses'],
            email_data['subject'],
            email_data['body_text'],
            email_data.get('body_html'),
            email_data['received_at'],
            analysis['thermal_temp'],
            analysis['priority_score'],
            analysis['sentiment'],
            analysis['action_required'],
            analysis['ai_summary']
        ))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        is_new = result is not None
        # Telegram alert for actionable emails
        if is_new and analysis.get('classification') == 'actionable':
            try:
                from telegram_alerts import send_plain_alert
                action = analysis.get('action_required_text', 'Action needed')
                deadline = analysis.get('action_deadline', '')
                deadline_str = f'\nDeadline: {deadline}' if deadline else ''
                alert_msg = (
                    f"ACTIONABLE EMAIL\n"
                    f"From: {email_data.get('from_address', '?')}\n"
                    f"Subject: {email_data.get('subject', '?')}\n"
                    f"Action: {action}{deadline_str}\n"
                    f"Priority: {analysis.get('priority_score', '?')}/5"
                )
                send_plain_alert(alert_msg)
                self.logger.info(f'Telegram alert sent for: {email_data["subject"][:50]}')
            except Exception as e:
                self.logger.warning(f'Telegram alert failed: {e}')

        return is_new
    
    def run(self, poll_interval=300):
        """Main daemon loop"""
        self.running = True
        self.connect_gmail()
        
        while self.running:
            try:
                self.logger.info('Polling for emails...')
                emails = self.fetch_recent_emails(max_results=20)
                
                new_count = 0
                for email_data in emails:
                    analysis = self.analyze_email(email_data)
                    if self.store_email(email_data, analysis):
                        new_count += 1
                        self.logger.info(f'Stored: {email_data["subject"][:50]}')
                
                self.logger.info(f'Poll complete. {new_count} new emails stored.')
                
            except Exception as e:
                self.logger.error(f'Daemon error: {e}')
            
            # Sleep with interrupt check
            for _ in range(poll_interval):
                if not self.running:
                    break
                time.sleep(1)
    
    def stop(self):
        self.running = False


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='/ganuda/email_daemon/config.json')
    parser.add_argument('--poll-interval', type=int, default=120)
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    args = parser.parse_args()
    
    daemon = GmailAPIDaemon(args.config)
    
    if args.once:
        daemon.connect_gmail()
        emails = daemon.fetch_recent_emails(20)
        for email in emails:
            analysis = daemon.analyze_email(email)
            if daemon.store_email(email, analysis):
                print(f'Stored: {email["subject"]}')
        print(f'Done. Processed {len(emails)} emails.')
    else:
        daemon.run(args.poll_interval)

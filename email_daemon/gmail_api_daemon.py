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
        """Simple priority analysis"""
        urgent_keywords = ['urgent', 'asap', 'immediately', 'deadline', 'critical', 'important']
        text = (email_data['subject'] + ' ' + email_data['body_text']).lower()
        
        priority = 5
        action_required = False
        thermal_temp = 0.5
        
        for kw in urgent_keywords:
            if kw in text:
                priority = min(priority, 2)
                action_required = True
                thermal_temp = 0.8
                break
        
        # Check Gmail labels
        if 'IMPORTANT' in email_data.get('labels', []):
            priority = min(priority, 3)
            thermal_temp = max(thermal_temp, 0.7)
        
        if 'STARRED' in email_data.get('labels', []):
            priority = min(priority, 2)
            action_required = True
            
        return {
            'priority_score': priority,
            'action_required': action_required,
            'thermal_temp': thermal_temp,
            'sentiment': 'neutral',
            'ai_summary': email_data['subject'][:200]
        }
    
    def store_email(self, email_data, analysis):
        """Store to PostgreSQL"""
        conn = psycopg2.connect(
            host=self.config.get('db_host', 'localhost'),
            database=self.config.get('db_name', 'bmasass_spoke'),
            user=self.config.get('db_user', 'claude'),
            password=self.config.get('db_password', 'jawaseatlasers2')
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
        
        return result is not None  # True if new email inserted
    
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
    parser.add_argument('--poll-interval', type=int, default=300)
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

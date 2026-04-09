```python
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
    def __init__(self, config_path: str = '/ganuda/email_daemon/config.json'):
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
        
    def connect_gmail(self) -> None:
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
        
    def fetch_subscription_emails(self, max_results: int = 100, query: str = '"your payment" OR "subscription" OR "invoice" OR "receipt" OR "renewal" OR "billing" OR "you\'ve been charged" OR "auto-pay"') -> list:
        """Fetch subscription-related emails"""
        emails = []
        
        results = self.service.users().messages().list(
            userId='me', 
            maxResults=max_results,
            q=query,
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
    
    def analyze_subscription_email(self, email_data: dict) -> dict:
        """LLM-backed email triage for subscription emails."""
        import requests as http_req

        subject = email_data.get('subject', '')
        body = email_data.get('body_text', '')[:1500]
        from_addr = email_data.get('from_address', '')

        # LLM classification via gateway
        prompt = f"""Analyze this email and extract subscription information.
Return JSON:
{{
  "is_subscription": true/false,
  "service_name": "Netflix",
  "amount": 15.99,
  "currency": "USD",
  "frequency": "monthly",  // monthly, annual, quarterly, weekly
  "charge_date": "2026-03-15",
  "category": "entertainment",  // entertainment, productivity, cloud, fitness, news, shopping, finance, other
  "confidence": 0.95
}}
If this is not a subscription charge, set is_subscription to false.

Email from: {from_addr}
Subject: {subject}
Body: {body}
"""

        try:
            resp = http_req.post(
                'http://localhost:8000/v1/chat/completions',
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
            classification = json.loads(llm_text)
            if not isinstance(classification, dict):
                self.logger.warning(f'LLM response not in expected format: {llm_text}')
                classification = {
                    'is_subscription': False,
                    'service_name': '',
                    'amount': 0.0,
                    'currency': '',
                    'frequency': '',
                    'charge_date': '',
                    'category': '',
                    'confidence': 0.0
                }

        except Exception as e:
            self.logger.warning(f'LLM triage failed, falling back to default: {e}')
            classification = {
                'is_subscription': False,
                'service_name': '',
                'amount': 0.0,
                'currency': '',
                'frequency': '',
                'charge_date': '',
                'category': '',
                'confidence': 0.0
            }

        return classification
    
    def store_subscription_email(self, email_data: dict, analysis: dict) -> None:
        """Store subscription email to PostgreSQL"""
        conn = psycopg2.connect(
            host=self.config.get('db_host', 'localhost'),
            database=self.config.get('db_name', 'bmasass_spoke'),
            user=self.config.get('db_user', 'claude'),
            password=self.config.get('db_password', os.environ.get('CHEROKEE_DB_PASS', ''))
        )
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO subscription_emails (
                message_id, from_address, to_addresses, subject,
                body_text, body_html, received_at,
                is_subscription, service_name, amount, currency,
                frequency, charge_date, category, confidence
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
            analysis['is_subscription'],
            analysis['service_name'],
            analysis['amount'],
            analysis['currency'],
            analysis['frequency'],
            analysis['charge_date'],
            analysis['category'],
            analysis['confidence']
        ))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()

        is_new = result is not None
        if is_new:
            self.logger.info(f'Stored subscription email: {email_data["subject"][:50]}')

    def run_subscription_scan(self, max_results: int = 100) -> None:
        """Run a subscription scan and store results"""
        self.connect_gmail()
        emails = self.fetch_subscription_emails(max_results)
        
        for email_data in emails:
            analysis = self.analyze_subscription_email(email_data)
            if analysis['is_subscription']:
                self.store_subscription_email(email_data, analysis)
                self.logger.info(f'Stored subscription: {email_data["subject"][:50]}')
        
        self.logger.info(f'Subscription scan complete. Processed {len(emails)} emails.')

if
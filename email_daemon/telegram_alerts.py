#!/usr/bin/env python3
"""Telegram Alert Module for Job Emails - Enhanced with links and context"""

import os
import re
import requests

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '8025375307')

CLASS_EMOJI = {'offer': '💰', 'interview': '📅', 'next_steps': '➡️', 'recruiter': '👤', 'application': '📝', 'rejection': '❌'}
PRIORITY_EMOJI = {1: '🔴', 2: '🟠', 3: '🟡', 4: '🔵', 5: '⚪'}

def escape_html(text: str) -> str:
    """Escape HTML special characters for Telegram HTML parse mode."""
    if not text:
        return ''
    return (text
        .replace('&', '&amp;')
        .replace('<', '&lt;')
        .replace('>', '&gt;'))

def clean_body_snippet(body: str, max_len: int = 200) -> str:
    """Extract a clean snippet from email body."""
    if not body:
        return ''
    # Remove excessive whitespace and newlines
    clean = re.sub(r'\s+', ' ', body).strip()
    # Truncate and add ellipsis if needed
    if len(clean) > max_len:
        clean = clean[:max_len].rsplit(' ', 1)[0] + '...'
    return escape_html(clean)

def get_gmail_url(message_id: str) -> str:
    """Generate Gmail deep link from message ID."""
    if not message_id:
        return ''
    # Gmail message IDs in URL need the <> stripped and may need encoding
    clean_id = message_id.strip('<>').split('@')[0] if '@' in message_id else message_id.strip('<>')
    return f'https://mail.google.com/mail/u/0/#search/rfc822msgid:{message_id}'

def send_job_alert(email: dict, classification: str, priority: int) -> bool:
    """Send job alert via Telegram with link and context."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    emoji = CLASS_EMOJI.get(classification, '📧')
    prio = PRIORITY_EMOJI.get(priority, '⚪')

    # Escape user content
    from_addr = escape_html(email.get('from_address', 'Unknown'))
    subject = escape_html(email.get('subject', 'No subject'))
    company = escape_html(email.get('job_company', ''))
    position = escape_html(email.get('job_position', ''))
    
    # Get body snippet
    body_snippet = clean_body_snippet(email.get('body_text', ''))
    
    # Get date
    date_received = email.get('date_received', '')
    if hasattr(date_received, 'strftime'):
        date_received = date_received.strftime('%b %d, %Y %I:%M %p')
    else:
        date_received = str(date_received)[:19] if date_received else ''
    
    # Build message
    message = f"{emoji} {prio} <b>Job Alert: {classification.replace('_', ' ').title()}</b>\n\n"
    message += f"<b>From:</b> {from_addr}\n"
    message += f"<b>Subject:</b> {subject}\n"
    if company:
        message += f"<b>Company:</b> {company}\n"
    if position:
        message += f"<b>Position:</b> {position}\n"
    if date_received:
        message += f"<b>Date:</b> {date_received}\n"
    
    # Add body snippet
    if body_snippet:
        message += f"\n<i>{body_snippet}</i>\n"
    
    # Add Gmail link if message_id available
    message_id = email.get('message_id', '')
    if message_id:
        gmail_url = get_gmail_url(message_id)
        message += f"\n<a href='{gmail_url}'>Open in Gmail</a>"

    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={
                'chat_id': TELEGRAM_CHAT_ID,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': True
            },
            timeout=10
        )
        if response.status_code != 200:
            print(f'Telegram API error: {response.status_code} - {response.text}')
        return response.status_code == 200
    except Exception as e:
        print(f'Telegram error: {e}')
        return False

def send_plain_alert(message: str) -> bool:
    """Send a plain text alert (no formatting) - guaranteed to work."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    try:
        response = requests.post(
            f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage',
            json={'chat_id': TELEGRAM_CHAT_ID, 'text': message},
            timeout=10
        )
        return response.status_code == 200
    except Exception as e:
        print(f'Telegram error: {e}')
        return False

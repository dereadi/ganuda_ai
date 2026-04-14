#!/usr/bin/env python3
"""
Subscription Trimmer — Gmail Scanner
Scans for recurring charges, receipts, and subscription signals.
Uses existing Gmail OAuth token at ~/.gmail_credentials/token.pickle

MOCHA Sprint — Apr 2, 2026
"""

import os
import pickle
import re
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from typing import List, Dict, Any
from collections import defaultdict

# Use the federation's existing Gmail token
TOKEN_PATH = os.path.expanduser('~/.gmail_credentials/token.pickle')


def load_credentials():
    """Load Gmail OAuth credentials from federation token."""
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f'Gmail token not found at {TOKEN_PATH}. Run gmail_oauth_setup first.')

    with open(TOKEN_PATH, 'rb') as f:
        creds = pickle.load(f)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_PATH, 'wb') as f:
            pickle.dump(creds, f)

    return creds


def scan_subscriptions(months_back: int = 6, max_results: int = 200) -> List[Dict[str, Any]]:
    """
    Scan Gmail for subscription-related emails.
    Returns raw email signals for classification.
    """
    creds = load_credentials()
    service = build('gmail', 'v1', credentials=creds)

    # Two-pronged search: charge confirmations + known subscription senders
    queries = [
        # Actual charge confirmations
        '("your receipt" OR "payment confirmation" OR "you\'ve been charged" '
        'OR "your bill" OR "statement is ready" OR "payment was unsuccessful" '
        'OR "auto-renewal" OR "subscription renewed")',
        # Known subscription patterns
        'from:(apple.com OR anthropic.com OR slack.com OR google.com OR '
        'openai.com OR github.com OR digitalocean.com OR cloudflare.com OR '
        'spotify.com OR netflix.com OR plex.tv OR hulu.com OR expressvpn.com OR '
        'paddle.com OR invoicecloud.net) '
        'subject:(receipt OR payment OR invoice OR bill OR charge OR renewal)',
    ]

    all_signals = []
    seen_ids = set()

    for q in queries:
        full_q = f'newer_than:{months_back * 30}d AND ({q})'
        try:
            results = service.users().messages().list(
                userId='me', q=full_q, maxResults=max_results
            ).execute()
        except Exception as e:
            print(f"Query failed: {e}")
            continue

        for msg in results.get('messages', []):
            if msg['id'] in seen_ids:
                continue
            seen_ids.add(msg['id'])

            try:
                full = service.users().messages().get(
                    userId='me', id=msg['id'], format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()

                headers = {h['name']: h['value'] for h in full['payload']['headers']}
                snippet = full.get('snippet', '')[:500]

                # Extract dollar amounts from snippet
                amounts = re.findall(r'\$[\d,]+\.?\d*', snippet)

                # Extract sender domain
                frm = headers.get('From', '')
                if '<' in frm:
                    email_addr = frm.split('<')[1].split('>')[0]
                    domain = email_addr.split('@')[-1]
                    sender_name = frm.split('<')[0].strip().strip('"')
                else:
                    domain = frm
                    sender_name = frm

                all_signals.append({
                    'from': frm,
                    'sender_name': sender_name,
                    'domain': domain,
                    'subject': headers.get('Subject', ''),
                    'date': headers.get('Date', ''),
                    'snippet': snippet,
                    'amounts_found': amounts,
                    'message_id': msg['id'],
                })
            except Exception as e:
                print(f"Failed to fetch message {msg['id']}: {e}")
                continue

    # Sort by date descending
    all_signals.sort(key=lambda x: x['date'], reverse=True)

    return all_signals


def group_by_service(signals: List[Dict]) -> Dict[str, List[Dict]]:
    """Group signals by sender domain for dedup."""
    groups = defaultdict(list)
    for s in signals:
        groups[s['domain']].append(s)
    return dict(groups)


# Filter out known non-subscription senders
NON_SUBSCRIPTION_DOMAINS = {
    'upwork.com',           # income, not expense
    'lendingtree.com',      # marketing spam
    'savings.lendingtree.com',
    'alerts.lendingtree.com',
    'trans.lendingtree.com',
    'dollarshaveclub.com',  # mostly marketing, need actual charge confirmation
    'e.academy.com',        # marketing
    'coinbase.com',
    'mail.coinbase.com',    # marketing
    'robinhood.com',        # investment, not subscription
    'affirm.com',
    'e.affirm.com',         # marketing
    'heatonist.com',        # one-time purchase
    'email.whisker.com',    # marketing
    'em.samsclub.com',      # marketing
    'easeus.com',           # marketing
    'shop.zennioptical.com',# marketing
    'mail.yelp.com',        # marketing
    'cbco.org',             # blood drive
    'mail.marvel.com',      # marketing
    'e.longhornsteakhouse.com',  # one-time
    'uber.com',             # ride-hailing, not subscription (dogfood fix Apr 4)
    'eat.grubhub.com',      # food delivery, not subscription
    'orders.grubhub.com',   # food delivery
    'creditkarma.com',      # marketing/credit monitoring promos
    'news.mlops.community', # newsletter, not charge
    'no-reply@hilton.com',  # one-time hotel stay
    'digital.costco.com',   # marketing
    'steampowered.com',     # one-time game purchase
    'kraken.com',           # crypto marketing
    'email.kraken.com',     # crypto marketing
}


def filter_noise(signals: List[Dict]) -> List[Dict]:
    """Remove known non-subscription signals."""
    return [s for s in signals if s['domain'] not in NON_SUBSCRIPTION_DOMAINS]


if __name__ == '__main__':
    import json

    print("Scanning Gmail for subscriptions...")
    signals = scan_subscriptions(months_back=6)
    print(f"Found {len(signals)} raw signals")

    filtered = filter_noise(signals)
    print(f"After noise filter: {len(filtered)} signals")

    groups = group_by_service(filtered)
    print(f"\nGrouped into {len(groups)} services:")
    for domain, entries in sorted(groups.items(), key=lambda x: -len(x[1])):
        amounts = []
        for e in entries:
            amounts.extend(e['amounts_found'])
        print(f"  {len(entries):3d}x | {domain:40s} | amounts: {', '.join(amounts[:5]) if amounts else 'none found'}")

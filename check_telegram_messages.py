#!/usr/bin/env python3
"""
CHECK TELEGRAM MESSAGES - Claude's interface to the Eternal Bridge
Flying Squirrel can run this to see what messages arrived via Telegram
"""

import psycopg2
import json
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def check_messages():
    """Check for pending Telegram messages"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    with conn.cursor() as cur:
        # Get pending messages
        cur.execute("""
            SELECT id, chat_id, user_name, message_text, received_at
            FROM telegram_bridge
            WHERE status = 'pending'
            ORDER BY received_at DESC
            LIMIT 10
        """)
        
        messages = cur.fetchall()
        
        if not messages:
            print("📭 No pending messages from Telegram")
            return
        
        print("🔥 PENDING TELEGRAM MESSAGES:")
        print("=" * 50)
        
        for msg_id, chat_id, user, text, received in messages:
            time_ago = (datetime.now() - received).total_seconds() / 60
            print(f"\n📱 From: {user}")
            print(f"⏰ {time_ago:.1f} minutes ago")
            print(f"💬 Message: {text}")
            print(f"🆔 ID: {msg_id} (Chat: {chat_id})")
            print("-" * 40)
    
    conn.close()
    return len(messages)

def send_response(bridge_id, response_text):
    """Send Claude's response back through the bridge"""
    conn = psycopg2.connect(**DB_CONFIG)
    
    with conn.cursor() as cur:
        cur.execute("""
            UPDATE telegram_bridge
            SET claude_response = %s,
                responded_at = NOW(),
                status = 'responded'
            WHERE id = %s
        """, (response_text, bridge_id))
        
        conn.commit()
        print(f"✅ Response queued for bridge ID {bridge_id}")
    
    conn.close()

if __name__ == "__main__":
    print("🔥 Checking Eternal Bridge for messages...")
    count = check_messages()
    
    if count > 0:
        print(f"\n💡 To respond, use: send_response(bridge_id, 'your message')")
        print("The Eternal Bridge will deliver your response to Telegram!")
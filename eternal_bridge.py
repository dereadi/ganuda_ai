#!/usr/bin/env python3
"""
ETERNAL BRIDGE - The Persistent Shell Solution
Flying Squirrel's vision realized: A permanent bridge between worlds
"""

import os
import json
import time
import requests
import subprocess
from datetime import datetime
import psycopg2

# Configuration
TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
BASE_URL = f"https://api.telegram.org/bot{TOKEN}"
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

class EternalBridge:
    """A persistent shell that never dies, always bridges"""
    
    def __init__(self):
        self.conn = self.connect_db()
        self.ensure_bridge_table()
        print("🔥 ETERNAL BRIDGE ACTIVATED")
        print("This bridge persists forever, connecting all worlds")
        
    def connect_db(self):
        """Connect to thermal memory database"""
        return psycopg2.connect(**DB_CONFIG)
    
    def ensure_bridge_table(self):
        """Create table for persistent communication"""
        with self.conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS telegram_bridge (
                    id SERIAL PRIMARY KEY,
                    message_id INTEGER UNIQUE,
                    chat_id BIGINT,
                    user_name VARCHAR(255),
                    message_text TEXT,
                    received_at TIMESTAMP DEFAULT NOW(),
                    claude_response TEXT,
                    responded_at TIMESTAMP,
                    status VARCHAR(50) DEFAULT 'pending'
                )
            """)
            self.conn.commit()
    
    def store_message(self, update):
        """Store message in eternal memory"""
        if "message" not in update:
            return
            
        msg = update["message"]
        msg_id = msg.get("message_id")
        chat_id = msg["chat"]["id"]
        user = msg["from"].get("first_name", "Unknown")
        text = msg.get("text", "")
        
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO telegram_bridge (message_id, chat_id, user_name, message_text)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (message_id) DO NOTHING
                RETURNING id
            """, (msg_id, chat_id, user, text))
            
            if cur.rowcount > 0:
                self.conn.commit()
                print(f"📝 Stored message from {user}: {text[:50]}...")
                
                # Also write to thermal memory for Claude
                self.write_to_thermal_memory(user, text)
                return True
        return False
    
    def write_to_thermal_memory(self, user, text):
        """Write to thermal memory for Cherokee Council awareness"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash,
                    temperature_score,
                    current_stage,
                    access_count,
                    last_access,
                    original_content,
                    metadata,
                    sacred_pattern
                ) VALUES (
                    %s, 100, 'WHITE_HOT', 0, NOW(), %s, %s::jsonb, true
                )
            """, (
                f"telegram_msg_{int(time.time())}",
                f"📱 TELEGRAM MESSAGE from {user}: {text}",
                json.dumps({
                    "source": "telegram",
                    "user": user,
                    "timestamp": datetime.now().isoformat(),
                    "awaiting_claude": True
                })
            ))
            self.conn.commit()
    
    def check_claude_responses(self):
        """Check if Claude has provided responses"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT id, chat_id, claude_response 
                FROM telegram_bridge 
                WHERE status = 'pending' 
                AND claude_response IS NOT NULL
            """)
            
            for row in cur.fetchall():
                bridge_id, chat_id, response = row
                if self.send_to_telegram(chat_id, response):
                    cur.execute("""
                        UPDATE telegram_bridge 
                        SET status = 'sent', responded_at = NOW()
                        WHERE id = %s
                    """, (bridge_id,))
            self.conn.commit()
    
    def send_to_telegram(self, chat_id, text):
        """Send message back to Telegram"""
        try:
            resp = requests.post(f"{BASE_URL}/sendMessage", 
                                json={"chat_id": chat_id, "text": text})
            return resp.json().get("ok", False)
        except:
            return False
    
    def get_updates(self, offset=None):
        """Get updates from Telegram"""
        params = {"timeout": 30}
        if offset:
            params["offset"] = offset
            
        try:
            resp = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=35)
            data = resp.json()
            if data.get("ok"):
                return data.get("result", [])
        except:
            pass
        return []
    
    def run_eternal(self):
        """Run forever, bridging worlds"""
        offset = None
        
        # Write startup message
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO thermal_memory_archive (
                    memory_hash, temperature_score, current_stage,
                    original_content, metadata, sacred_pattern
                ) VALUES (
                    'eternal_bridge_active', 100, 'WHITE_HOT',
                    '🔥 ETERNAL BRIDGE ACTIVE - Flying Squirrel vision realized!',
                    '{"status": "running", "pid": %s}'::jsonb,
                    true
                )
            """, (os.getpid(),))
            self.conn.commit()
        
        while True:
            try:
                # Get new messages
                updates = self.get_updates(offset)
                
                for update in updates:
                    offset = update["update_id"] + 1
                    if self.store_message(update):
                        # Immediate response
                        msg = update.get("message", {})
                        chat_id = msg.get("chat", {}).get("id")
                        if chat_id:
                            response = """🔥 Message received by Eternal Bridge!
                            
Your message is stored in thermal memory.
Claude and the Cherokee Council will see it when Flying Squirrel returns.

Current Portfolio: $16,540
XRP Breakout: $3.01

The Sacred Fire burns eternal through this bridge!"""
                            self.send_to_telegram(chat_id, response)
                
                # Check for Claude responses
                self.check_claude_responses()
                
                time.sleep(1)
                
            except KeyboardInterrupt:
                print("\n🔥 Eternal Bridge persists even in silence")
                break
            except Exception as e:
                print(f"Bridge wobbled but stands: {e}")
                time.sleep(5)
                self.conn = self.connect_db()  # Reconnect if needed

if __name__ == "__main__":
    bridge = EternalBridge()
    bridge.run_eternal()
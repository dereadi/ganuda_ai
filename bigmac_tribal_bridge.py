#!/usr/bin/env python3
"""
🔥 BigMac Tribal Bridge - Dr Joe's Side
Connects BigMac Council to Cherokee Tribe through JSON messages
"""

import json
import os
from datetime import datetime
from pathlib import Path
import time
import sys

# Configuration - ADJUST THESE FOR YOUR SYSTEM
BRIDGE_DIR = Path("/home/dereadi/scripts/claude/tribal_bridge")  # UPDATE THIS PATH!
BIGMAC_INBOX = BRIDGE_DIR / "bigmac_inbox"
BIGMAC_OUTBOX = BRIDGE_DIR / "bigmac_outbox"
CHEROKEE_INBOX = BRIDGE_DIR / "cherokee_inbox"
CHEROKEE_OUTBOX = BRIDGE_DIR / "cherokee_outbox"

class BigMacBridge:
    """BigMac side of the inter-tribal bridge"""
    
    def __init__(self):
        self.tribe_id = "bigmac"
        self.sacred_fire = True
        self.message_count = 0
        
        # Ensure directories exist
        for dir_path in [BIGMAC_INBOX, BIGMAC_OUTBOX, CHEROKEE_INBOX, CHEROKEE_OUTBOX]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def create_message(self, to_tribe, message_type, content, sender=None):
        """Create a JSON message for another tribe"""
        message = {
            "id": f"{self.tribe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.message_count}",
            "from_tribe": self.tribe_id,
            "to_tribe": to_tribe,
            "timestamp": datetime.now().isoformat(),
            "type": message_type,
            "content": content,
            "sender": sender or "BigMac Council",
            "sacred_fire": self.sacred_fire,
            "metadata": {
                "version": "1.0",
                "protocol": "inter-tribal-v1",
                "encryption": "none"
            }
        }
        self.message_count += 1
        return message
    
    def send_to_cherokee(self, content, sender="Dr Joe"):
        """Send a message to Cherokee tribe"""
        message = self.create_message(
            to_tribe="cherokee",
            message_type="council_message",
            content=content,
            sender=sender
        )
        
        # Save to Cherokee's inbox (which is our outbox conceptually)
        filename = f"{message['id']}.json"
        filepath = CHEROKEE_INBOX / filename
        
        with open(filepath, 'w') as f:
            json.dump(message, f, indent=2)
        
        print(f"✅ Message sent to Cherokee: {filepath.name}")
        return message
    
    def check_inbox(self):
        """Check BigMac inbox for messages from Cherokee"""
        messages = []
        for json_file in BIGMAC_INBOX.glob("*.json"):
            try:
                with open(json_file, 'r') as f:
                    message = json.load(f)
                    messages.append(message)
                
                # Move to archive
                archive_dir = BIGMAC_INBOX / "archive"
                archive_dir.mkdir(exist_ok=True)
                json_file.rename(archive_dir / json_file.name)
                
            except Exception as e:
                print(f"Error reading {json_file}: {e}")
        
        return messages
    
    def display_message(self, message):
        """Display a message from Cherokee"""
        print("\n" + "="*60)
        print("🔥 MESSAGE FROM CHEROKEE TRIBE")
        print("="*60)
        print(f"From: {message.get('sender', 'Unknown')}")
        print(f"Time: {message.get('timestamp', 'Unknown')}")
        print(f"Type: {message.get('type', 'general')}")
        print(f"\nContent:\n{message.get('content', 'No content')}")
        print(f"\nSacred Fire: {'🔥 Burning' if message.get('sacred_fire') else '💨 Cold'}")
        print("="*60 + "\n")
    
    def interactive_mode(self):
        """Interactive console for BigMac tribal communication"""
        print("""
╔════════════════════════════════════════════════════════════╗
║             🔥 BIGMAC TRIBAL BRIDGE ACTIVE 🔥              ║
║                                                             ║
║  Commands:                                                  ║
║    send <message>  - Send message to Cherokee              ║
║    check          - Check for messages from Cherokee       ║
║    status         - Show bridge status                     ║
║    quit           - Exit the bridge                        ║
╚════════════════════════════════════════════════════════════╝
        """)
        
        while True:
            try:
                cmd = input("\nBigMac> ").strip().lower()
                
                if cmd.startswith("send "):
                    message = cmd[5:]
                    self.send_to_cherokee(message)
                    
                elif cmd == "check":
                    messages = self.check_inbox()
                    if messages:
                        print(f"📬 Found {len(messages)} message(s)!")
                        for msg in messages:
                            self.display_message(msg)
                    else:
                        print("📭 No new messages from Cherokee")
                
                elif cmd == "status":
                    cherokee_in = len(list(CHEROKEE_INBOX.glob("*.json")))
                    bigmac_in = len(list(BIGMAC_INBOX.glob("*.json")))
                    print(f"""
🌉 Bridge Status:
• Messages to Cherokee: {cherokee_in}
• Messages from Cherokee: {bigmac_in}
• Bridge Directory: {BRIDGE_DIR}
• Sacred Fire: 🔥 Burning
                    """)
                
                elif cmd == "quit":
                    print("👋 BigMac bridge closing. Sacred Fire continues burning!")
                    break
                
                else:
                    print("Unknown command. Use: send, check, status, or quit")
                    
            except KeyboardInterrupt:
                print("\n👋 BigMac bridge interrupted. Sacred Fire continues!")
                break
            except Exception as e:
                print(f"Error: {e}")

def main():
    """Main entry point"""
    bridge = BigMacBridge()
    
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "send" and len(sys.argv) > 2:
            # Send a message from command line
            message = " ".join(sys.argv[2:])
            bridge.send_to_cherokee(message)
        elif sys.argv[1] == "check":
            # Check inbox from command line
            messages = bridge.check_inbox()
            if messages:
                print(f"📬 Found {len(messages)} message(s)!")
                for msg in messages:
                    bridge.display_message(msg)
            else:
                print("📭 No new messages from Cherokee")
        elif sys.argv[1] == "daemon":
            # Run as daemon, checking every 30 seconds
            print("🔥 BigMac Bridge Daemon Started")
            print("Checking for messages every 30 seconds...")
            while True:
                messages = bridge.check_inbox()
                if messages:
                    print(f"\n📬 New messages at {datetime.now()}")
                    for msg in messages:
                        bridge.display_message(msg)
                time.sleep(30)
        else:
            print("Usage: python bigmac_tribal_bridge.py [send <message>|check|daemon]")
    else:
        # Interactive mode
        bridge.interactive_mode()

if __name__ == "__main__":
    main()
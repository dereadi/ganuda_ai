#!/usr/bin/env python3
"""
Test the temporal flat file system end-to-end
"""
import json
import time
from pathlib import Path

def send_test_message(message_text, user="TestUser"):
    """Send a test message through the flat file system"""
    inbox_path = Path("/home/dereadi/scripts/claude/TRIBAL_INBOX.txt")
    outbox_path = Path("/home/dereadi/scripts/claude/TRIBAL_OUTBOX.txt")
    
    # Create test message
    test_message = {
        "epoch": time.time(),
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "user": user,
        "chat_id": 123456789,
        "message": message_text
    }
    
    print(f"📤 Sending: {message_text}")
    print(f"⏰ Epoch: {test_message['epoch']}")
    
    # Write to inbox
    with open(inbox_path, 'w') as f:
        json.dump(test_message, f)
    
    # Wait for response (max 5 seconds)
    for i in range(10):
        time.sleep(0.5)
        if outbox_path.exists() and outbox_path.stat().st_size > 0:
            try:
                with open(outbox_path, 'r') as f:
                    content = f.read().strip()
                    if content:
                        # Parse the entire content as JSON
                        response = json.loads(content)
                        print(f"📥 Response received!")
                        print(f"⏰ Response epoch: {response.get('epoch', 'unknown')}")
                        print(f"📝 Response:\n{response.get('response', 'No response text')}")
                        
                        # Clear outbox after reading
                        open(outbox_path, 'w').close()
                        return response
            except json.JSONDecodeError:
                # Try reading as multiple JSON objects (one per line)
                with open(outbox_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                response = json.loads(line)
                                print(f"📥 Response received!")
                                print(f"⏰ Response epoch: {response.get('epoch', 'unknown')}")
                                print(f"📝 Response:\n{response.get('response', 'No response text')}")
                                open(outbox_path, 'w').close()
                                return response
                            except:
                                continue
    
    print("❌ No response received within 5 seconds")
    return None

def run_tests():
    """Run a series of test messages"""
    test_messages = [
        "What's my portfolio value?",
        "Show me current prices",
        "What time is it?",
        "Where's the kanban board?",
        "Should I buy ETH?",
        "Hello tribe!",
    ]
    
    print("🔥 TESTING TEMPORAL FLAT FILE SYSTEM")
    print("=" * 50)
    
    for msg in test_messages:
        print(f"\n🧪 Test: {msg}")
        print("-" * 30)
        response = send_test_message(msg)
        if response:
            # Calculate round-trip time
            sent_epoch = float(msg_epoch) if 'msg_epoch' in locals() else time.time()
            response_epoch = float(response.get('epoch', time.time()))
            rtt = response_epoch - sent_epoch
            print(f"⚡ Round-trip time: {rtt:.2f} seconds")
        print("=" * 50)
        time.sleep(1)  # Small delay between tests

if __name__ == "__main__":
    run_tests()
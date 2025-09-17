#!/bin/bash
# 🔥 SETUP PERSISTENT CLAUDE SESSION FOR CANADA

echo "🔥 CHEROKEE PERSISTENT SESSION SETUP"
echo "===================================="
echo ""

# Step 1: Install screen if needed
echo "Step 1: Checking for screen..."
if ! command -v screen &> /dev/null; then
    echo "Screen not found. Please run:"
    echo "  sudo apt-get update && sudo apt-get install -y screen"
    echo ""
    echo "Then run this script again!"
    exit 1
else
    echo "✅ Screen is installed!"
fi

# Step 2: Kill any existing Python processes using our bot token
echo ""
echo "Step 2: Cleaning up old bot processes..."
pkill -f "7913555407" 2>/dev/null
pkill -f "telegram" 2>/dev/null
pkill -f "simple_telegram" 2>/dev/null
sleep 2
echo "✅ Old processes cleaned up!"

# Step 3: Create the persistent Telegram handler
echo ""
echo "Step 3: Creating persistent Telegram handler..."

cat > /home/dereadi/scripts/claude/persistent_canada_bot.py << 'EOF'
#!/usr/bin/env python3
"""
🔥 PERSISTENT CANADA BOT - Runs 24/7 in screen session
Watches for your Telegram messages and logs them for Claude to see
"""
import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from telegram import Bot
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
MESSAGE_LOG = Path("/home/dereadi/scripts/claude/CANADA_MESSAGES.log")
RESPONSE_QUEUE = Path("/home/dereadi/scripts/claude/CANADA_RESPONSES.json")

class CanadaBot:
    def __init__(self):
        self.message_count = 0
        
    async def handle_message(self, update, context):
        """Log messages for Claude and send acknowledgment"""
        if not update.message or not update.message.text:
            return
            
        user = update.message.from_user.first_name or "User"
        text = update.message.text
        chat_id = update.message.chat.id
        timestamp = datetime.now()
        
        # Log for Claude to see
        self.message_count += 1
        log_entry = f"""
{'='*60}
🔥 MESSAGE #{self.message_count} FROM CANADA
Time: {timestamp.strftime('%Y-%m-%d %H:%M:%S CDT')}
User: {user}
Chat ID: {chat_id}
Message: {text}
{'='*60}
CLAUDE: Analyze this and respond with full tribal intelligence!
"""
        
        # Append to log file
        with open(MESSAGE_LOG, 'a') as f:
            f.write(log_entry + "\n")
        
        # Print to screen so Claude sees it
        print(log_entry)
        
        # Send immediate acknowledgment
        ack_message = f"""🔥 Cherokee Council received your message!

Message #{self.message_count}: "{text}"

Claude is analyzing with full tribal intelligence...
Response coming soon!

(You're connected from Canada! 🇨🇦)"""
        
        await update.message.reply_text(ack_message)
        
        # Save message for Claude to process
        message_data = {
            "id": self.message_count,
            "timestamp": timestamp.isoformat(),
            "user": user,
            "chat_id": chat_id,
            "text": text,
            "status": "pending"
        }
        
        # Append to response queue
        queue = []
        if RESPONSE_QUEUE.exists():
            with open(RESPONSE_QUEUE, 'r') as f:
                try:
                    queue = json.load(f)
                except:
                    queue = []
        
        queue.append(message_data)
        
        with open(RESPONSE_QUEUE, 'w') as f:
            json.dump(queue, f, indent=2)
        
        print(f"✅ Message #{self.message_count} logged and queued for response")

def main():
    print("🔥 PERSISTENT CANADA BOT STARTING...")
    print("="*60)
    print("This bot will run 24/7 in your screen session")
    print("It logs all messages for Claude to analyze")
    print("You can check messages at: CANADA_MESSAGES.log")
    print("="*60)
    print("")
    
    bot = CanadaBot()
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    print("🔥 Ready to receive messages from Canada!")
    print("Send messages to @ganudabot")
    print("")
    
    app.run_polling()

if __name__ == "__main__":
    main()
EOF

chmod +x /home/dereadi/scripts/claude/persistent_canada_bot.py
echo "✅ Persistent bot created!"

# Step 4: Create response sender for Claude
echo ""
echo "Step 4: Creating response sender..."

cat > /home/dereadi/scripts/claude/send_canada_response.py << 'EOF'
#!/usr/bin/env python3
"""
Send a response back to Canada
Usage: ./send_canada_response.py <message_id> "Your response text"
"""
import sys
import json
import asyncio
from telegram import Bot

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
RESPONSE_QUEUE = "/home/dereadi/scripts/claude/CANADA_RESPONSES.json"

async def send_response(message_id, response_text):
    # Load the queue
    with open(RESPONSE_QUEUE, 'r') as f:
        queue = json.load(f)
    
    # Find the message
    for msg in queue:
        if msg["id"] == int(message_id):
            chat_id = msg["chat_id"]
            
            # Send the response
            bot = Bot(token=TOKEN)
            await bot.send_message(
                chat_id=chat_id,
                text=f"🔥 **Cherokee Council Response to Message #{message_id}**\n\n{response_text}",
                parse_mode='Markdown'
            )
            
            # Mark as responded
            msg["status"] = "responded"
            msg["response"] = response_text
            
            # Save updated queue
            with open(RESPONSE_QUEUE, 'w') as f:
                json.dump(queue, f, indent=2)
            
            print(f"✅ Response sent for message #{message_id}")
            return
    
    print(f"❌ Message #{message_id} not found")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: ./send_canada_response.py <message_id> \"Your response\"")
        sys.exit(1)
    
    message_id = sys.argv[1]
    response_text = " ".join(sys.argv[2:])
    
    asyncio.run(send_response(message_id, response_text))
EOF

chmod +x /home/dereadi/scripts/claude/send_canada_response.py
echo "✅ Response sender created!"

# Step 5: Create the screen startup script
echo ""
echo "Step 5: Creating screen session manager..."

cat > /home/dereadi/scripts/claude/start_canada_session.sh << 'EOF'
#!/bin/bash
# Start the Canada persistent session

echo "🔥 Starting Cherokee Canada Persistent Session"
echo "=============================================="

# Check if session already exists
if screen -list | grep -q "claude-canada"; then
    echo "⚠️  Session 'claude-canada' already exists!"
    echo "To reattach: screen -r claude-canada"
    echo "To kill it: screen -X -S claude-canada quit"
    exit 1
fi

# Start new screen session
echo "Starting screen session 'claude-canada'..."
screen -dmS claude-canada bash -c '
echo "🔥 CHEROKEE CANADA SESSION ACTIVE"
echo "================================="
echo ""
echo "Starting Telegram bot..."
cd /home/dereadi/scripts/claude
/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3 persistent_canada_bot.py
'

sleep 2

# Check if it started
if screen -list | grep -q "claude-canada"; then
    echo "✅ Session started successfully!"
    echo ""
    echo "To view the session: screen -r claude-canada"
    echo "To detach: Press Ctrl-A, then D"
    echo "To see messages: cat CANADA_MESSAGES.log"
    echo ""
    echo "🔥 The bot is now running 24/7!"
    echo "Send messages to @ganudabot from Canada!"
else
    echo "❌ Failed to start session"
fi
EOF

chmod +x /home/dereadi/scripts/claude/start_canada_session.sh
echo "✅ Screen session manager created!"

# Step 6: Create helper script to check status
cat > /home/dereadi/scripts/claude/check_canada_status.sh << 'EOF'
#!/bin/bash
# Check status of Canada persistent session

echo "🔥 CANADA SESSION STATUS"
echo "======================="
echo ""

# Check if screen session exists
if screen -list | grep -q "claude-canada"; then
    echo "✅ Screen session 'claude-canada' is RUNNING"
    
    # Count messages
    if [ -f "/home/dereadi/scripts/claude/CANADA_MESSAGES.log" ]; then
        MSG_COUNT=$(grep -c "MESSAGE #" /home/dereadi/scripts/claude/CANADA_MESSAGES.log 2>/dev/null || echo 0)
        echo "📊 Total messages received: $MSG_COUNT"
    fi
    
    # Check pending responses
    if [ -f "/home/dereadi/scripts/claude/CANADA_RESPONSES.json" ]; then
        PENDING=$(python3 -c "import json; data=json.load(open('/home/dereadi/scripts/claude/CANADA_RESPONSES.json')); print(sum(1 for m in data if m['status']=='pending'))" 2>/dev/null || echo 0)
        echo "⏳ Pending responses: $PENDING"
    fi
else
    echo "❌ Screen session 'claude-canada' is NOT running"
    echo "Start it with: ./start_canada_session.sh"
fi

echo ""
echo "Commands:"
echo "  View session:   screen -r claude-canada"
echo "  Detach:         Ctrl-A, then D"
echo "  Check messages: cat CANADA_MESSAGES.log"
echo "  Send response:  ./send_canada_response.py <id> \"message\""
EOF

chmod +x /home/dereadi/scripts/claude/check_canada_status.sh
echo "✅ Status checker created!"

echo ""
echo "===================================="
echo "🔥 SETUP COMPLETE!"
echo ""
echo "To start the persistent session:"
echo "  ./start_canada_session.sh"
echo ""
echo "To check status:"
echo "  ./check_canada_status.sh"
echo ""
echo "To attach to the session:"
echo "  screen -r claude-canada"
echo ""
echo "Ready for Canada! 🇨🇦"
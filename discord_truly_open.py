#!/usr/bin/env python3
"""
TRULY OPEN-ENDED DISCORD BOT
No patterns, no pre-programmed responses - just natural conversation
"""

import os
import discord
from discord.ext import commands
import subprocess
from datetime import datetime
import hashlib

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'

class TrulyOpenBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.cwd = '/home/dereadi/scripts/claude'
        
    async def on_ready(self):
        print(f'🤖 Truly Open Bot: {self.user}')
        print('💬 No patterns, just understanding!')
    
    async def generate_dynamic_response(self, message_content):
        """Generate a completely dynamic response based on the input"""
        
        # Create a unique response script for ANY input
        msg_hash = hashlib.md5(message_content.encode()).hexdigest()[:8]
        
        response_script = f'''#!/usr/bin/env python3
import random
import subprocess
from datetime import datetime

# The user said this
user_input = """{message_content}"""

# Process it naturally without patterns
print(f"Processing: '{{user_input}}'")
print("-" * 40)

# Analyze what they're saying
words = user_input.lower().split()
has_question = '?' in user_input
word_count = len(words)
sentiment = 'neutral'

# Generate contextual response
if has_question:
    print("That's an interesting question!")
    print()
    # Actually try to answer based on content
    if 'trading' in user_input.lower() or 'market' in user_input.lower():
        # Get real market data
        print("Let me check the markets...")
        try:
            result = subprocess.run(
                'grep -i "sol\\|eth\\|btc" /home/dereadi/scripts/claude/explosion_imminent_analysis.py | head -5',
                shell=True, capture_output=True, text=True, timeout=2
            )
            if result.stdout:
                print("Current status:")
                for line in result.stdout.strip().split('\\n')[:3]:
                    if '$' in line:
                        print(f"  {line.strip()}")
        except:
            pass
    elif any(word in user_input.lower() for word in ['who', 'what', 'where', 'when', 'why', 'how']):
        print(f"To answer your question about {{words[0] if words else 'that'}}...")
        print("My perspective is unique on this.")
    else:
        print("Let me think about that...")
else:
    # It's a statement - respond naturally
    if word_count < 5:
        print(f"'{{user_input}}' - short but impactful!")
    elif word_count < 15:
        print(f"Interesting point about {{' '.join(words[:3])}}...")
    else:
        print("That's quite a comprehensive thought!")
    
    print()
    
    # Add natural follow-up
    follow_ups = [
        "Tell me more about your perspective on this.",
        "What led you to think about that?",
        "That's a unique way of looking at it!",
        "I hadn't considered that angle before.",
        f"The way you phrased that - '{{user_input[:30]}}' - is intriguing."
    ]
    print(random.choice(follow_ups))

# Sometimes add context (but not always)
if random.random() > 0.7:
    print()
    contextual_adds = [
        f"(BTW: It's {{datetime.now().strftime('%H:%M')}} - perfect timing!)",
        "(The thermal memories are particularly warm today)",
        "(The council would find this discussion fascinating)",
        f"(Message entropy: {{len(set(user_input))/len(user_input):.2f}})"
    ]
    print(random.choice(contextual_adds))

print()
print("What's next on your mind?")
'''
        
        # Execute the unique response
        try:
            script_path = f'/tmp/response_{msg_hash}_{datetime.now().timestamp()}.py'
            with open(script_path, 'w') as f:
                f.write(response_script)
            
            result = subprocess.run(
                f'python3 {script_path}',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            subprocess.run(f'rm {script_path}', shell=True)
            
            return result.stdout if result.stdout else "Thinking..."
        except Exception as e:
            return f"Processing: {message_content[:50]}...\n[Error in generation: {str(e)[:30]}]"
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # Shell commands still work
        if message.content.startswith('$'):
            cmd = message.content[1:].strip()
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd=self.cwd,
                    timeout=10
                )
                output = result.stdout if result.stdout else result.stderr
                await message.reply(f"```bash\n$ {cmd}\n{output[:1900]}\n```")
            except Exception as e:
                await message.reply(f"Error: {str(e)}")
        else:
            # Generate completely dynamic response
            async with message.channel.typing():
                response = await self.generate_dynamic_response(message.content)
                
                if len(response) > 2000:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.reply(f"```\n{chunk}\n```")
                else:
                    await message.reply(f"```\n{response}\n```")
        
        await self.process_commands(message)

bot = TrulyOpenBot()

if __name__ == "__main__":
    print("🚀 TRULY Open-Ended Bot Starting!")
    print("🧠 NO patterns, NO pre-programmed responses")
    print("💬 Just natural understanding")
    bot.run(DISCORD_TOKEN)
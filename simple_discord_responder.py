#!/usr/bin/env python3
"""
🔥 SIMPLE DISCORD RESPONDER
Minimal bot that will definitely respond
"""

import discord
import os
import sys
import asyncio
from datetime import datetime

# Load token
TOKEN = None
token_path = '/home/dereadi/scripts/claude/pathfinder/test/.discord_token'
if os.path.exists(token_path):
    with open(token_path, 'r') as f:
        TOKEN = f.read().strip()
    print(f"✅ Token loaded: {len(TOKEN)} chars")
else:
    print("❌ No token found!")
    sys.exit(1)

class SimpleBot(discord.Client):
    async def on_ready(self):
        print(f'✅ Logged in as {self.user}')
        print(f'📍 ID: {self.user.id}')
        print('-------------------')
        print('Guilds:')
        for guild in self.guilds:
            print(f'  - {guild.name} (id: {guild.id})')
            # List channels
            for channel in guild.text_channels:
                print(f'    #{channel.name}')
        print('-------------------')
        print('🔥 Ready to respond!')
        print('Say anything and I will respond!')

    async def on_message(self, message):
        # Don't respond to ourselves
        if message.author == self.user:
            return
        
        # Log EVERYTHING
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f'[{timestamp}] Message from {message.author} in #{message.channel}: "{message.content}"')
        
        # Respond to EVERYTHING (except our own messages)
        response = f'🔥 Cherokee Council heard you say: "{message.content}"\n'
        response += f'Current Status: Liquidity $9.10 (CRITICAL), Sacred Fire BURNING ETERNAL'
        
        try:
            await message.channel.send(response)
            print(f'  ✅ Responded')
        except Exception as e:
            print(f'  ❌ Could not respond: {e}')

# Create client with all intents
intents = discord.Intents.all()  # Use ALL intents to make sure we get messages
client = SimpleBot(intents=intents)

print('🔥 STARTING SIMPLE DISCORD RESPONDER')
print('=====================================')
print('This bot will respond to EVERY message')
print('Starting...')

try:
    client.run(TOKEN)
except discord.LoginFailure:
    print('❌ Invalid token!')
except Exception as e:
    print(f'❌ Error: {e}')
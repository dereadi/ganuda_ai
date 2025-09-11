#!/usr/bin/env python3
"""
🔥 QUICK DISCORD TEST BOT
Simple bot to verify Discord connection
"""

import discord
from discord.ext import commands
import os
import sys
from datetime import datetime

# Load token
TOKEN = None
if os.path.exists('/home/dereadi/scripts/claude/pathfinder/test/.discord_token'):
    with open('/home/dereadi/scripts/claude/pathfinder/test/.discord_token', 'r') as f:
        TOKEN = f.read().strip()
else:
    print("❌ No Discord token found!")
    sys.exit(1)

# Create bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True
intents.guilds = True

bot = commands.Bot(command_prefix=['!', '$', '.'], intents=intents)

@bot.event
async def on_ready():
    print(f'✅ Bot connected as {bot.user}')
    print(f'📍 In {len(bot.guilds)} servers')
    for guild in bot.guilds:
        print(f'   - {guild.name} (id: {guild.id})')
    print('🔥 Sacred Fire burns eternal')
    print('Ready for commands!')

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Log all messages for debugging
    print(f'[{datetime.now().strftime("%H:%M:%S")}] #{message.channel}: {message.author}: {message.content}')
    
    # Respond to any message with "howdy"
    if 'howdy' in message.content.lower():
        await message.channel.send('🤠 Howdy partner! Cherokee Trading Council here. Sacred Fire burns eternal! 🔥')
        await message.channel.send('Current liquidity: $9.10 (CRITICAL)')
    
    # Respond to mentions
    if bot.user.mentioned_in(message):
        await message.channel.send('🔥 Cherokee Trading Council acknowledges. How can I help?')
    
    # Process commands
    await bot.process_commands(message)

@bot.command(name='status')
async def status(ctx):
    """Check bot status"""
    await ctx.send('🔥 Cherokee Trading Council Online\n💵 Liquidity: $9.10 (CRITICAL)\n🎯 Specialists: 4 running')

@bot.command(name='help')
async def help_command(ctx):
    """Show commands"""
    await ctx.send('**Commands:**\n!status - Check status\n!help - This message\nJust say "howdy" and I\'ll respond!')

@bot.command(name='test')
async def test(ctx):
    """Test command"""
    await ctx.send('🔥 Test successful! Sacred Fire burns eternal!')

print('🔥 Starting Discord Test Bot...')
print('Commands: !status, !help, !test')
print('Or just say "howdy"!')

try:
    bot.run(TOKEN)
except Exception as e:
    print(f'❌ Error: {e}')
    print('Token might be invalid or bot not in server')
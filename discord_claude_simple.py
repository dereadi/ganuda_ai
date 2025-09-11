#!/usr/bin/env python3
"""
SIMPLE DISCORD CLAUDE BOT
========================
Clean implementation based on Pipedream patterns
"""

import os
import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime
import requests

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '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')

class ClaudeBot(commands.Bot):
    """Simple Claude Discord bot using direct API calls"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.conversation_history = {}
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
    
    async def on_ready(self):
        """Bot is ready"""
        print(f'✅ {self.user} connected!')
        print(f'🤖 Claude bot ready. Commands: !ask, !clear, !help')
    
    async def query_claude(self, prompt: str, channel_id: int) -> str:
        """Query Claude using direct API call (Pipedream pattern)"""
        
        # Build conversation history
        if channel_id not in self.conversation_history:
            self.conversation_history[channel_id] = []
        
        # Add current message
        messages = self.conversation_history[channel_id][-10:]  # Keep last 10
        messages.append({"role": "user", "content": prompt})
        
        # Prepare request
        data = {
            "model": "claude-3-sonnet-20240229",  # Using Sonnet for better speed
            "messages": messages,
            "max_tokens": 1000,
            "temperature": 0.7
        }
        
        try:
            # Make API call
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result['content'][0]['text']
                
                # Save to history
                self.conversation_history[channel_id].append({"role": "assistant", "content": assistant_message})
                
                return assistant_message
            else:
                return f"❌ API Error {response.status_code}: {response.text[:200]}"
                
        except Exception as e:
            return f"❌ Error: {str(e)[:200]}"
    
    async def on_message(self, message):
        """Handle messages"""
        # Ignore bot's own messages
        if message.author == self.user:
            return
        
        # Respond to mentions
        if self.user.mentioned_in(message) and not message.mention_everyone:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if content:
                async with message.channel.typing():
                    response = await self.query_claude(content, message.channel.id)
                
                # Split if too long
                if len(response) > 2000:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)
        
        # Process commands
        await self.process_commands(message)

# Create bot instance
bot = ClaudeBot()

# Remove default help command
bot.remove_command('help')

@bot.command(name='ask')
async def ask_claude(ctx, *, question: str):
    """Ask Claude a question"""
    await ctx.send("🤔 Thinking...")
    
    async with ctx.typing():
        response = await bot.query_claude(question, ctx.channel.id)
    
    # Send response
    if len(response) > 2000:
        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(response)

@bot.command(name='clear')
async def clear_history(ctx):
    """Clear conversation history"""
    if ctx.channel.id in bot.conversation_history:
        bot.conversation_history[ctx.channel.id] = []
    await ctx.send("✅ Conversation history cleared!")

@bot.command(name='help')
async def help_command(ctx):
    """Show help"""
    help_text = """
**🤖 Claude Discord Bot Commands:**

`!ask [question]` - Ask Claude anything
`!clear` - Clear conversation history
`@mention` - Chat with Claude

The bot maintains conversation context per channel.
Using Claude 3 Sonnet for fast responses.
"""
    await ctx.send(help_text)

def main():
    """Launch the bot"""
    print("""
    🤖 SIMPLE CLAUDE DISCORD BOT 🤖
    ================================
    Using direct API calls (Pipedream pattern)
    
    Starting bot...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    if not ANTHROPIC_API_KEY:
        print("❌ No Anthropic API key!")
        return
    
    print(f"✅ Discord token: {DISCORD_TOKEN[:20]}...")
    print(f"✅ Anthropic key: {ANTHROPIC_API_KEY[:20]}...")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
UNIFIED DISCORD AI BOT
======================
Claude + Gemini in one clean implementation
"""

import os
import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime
import requests
import google.generativeai as genai

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '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')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc')

# Configure Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class UnifiedBot(commands.Bot):
    """Unified AI Discord bot with multiple models"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.current_model = 'claude'
        self.models = {
            'claude': 'Claude 3.5 Sonnet',
            'gemini': 'Gemini Pro'
        }
        
        self.conversation_history = {}
        
        # Claude API setup
        self.claude_api_url = "https://api.anthropic.com/v1/messages"
        self.claude_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        # Gemini model
        self.gemini_model = genai.GenerativeModel('gemini-pro') if GEMINI_API_KEY else None
    
    async def on_ready(self):
        """Bot is ready"""
        print(f'✅ {self.user} connected!')
        print(f'🤖 Current model: {self.models[self.current_model]}')
        print(f'📝 Commands: !model, !ask, !clear, !help')
    
    async def query_ai(self, prompt: str, channel_id: int) -> str:
        """Query the current AI model"""
        
        # Get or create conversation history
        if channel_id not in self.conversation_history:
            self.conversation_history[channel_id] = []
        
        history = self.conversation_history[channel_id][-10:]  # Keep last 10
        
        try:
            if self.current_model == 'claude':
                # Claude API call
                messages = history + [{"role": "user", "content": prompt}]
                
                data = {
                    "model": "claude-3-5-sonnet-20241022",  # Updated to latest Sonnet
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
                
                response = requests.post(
                    self.claude_api_url,
                    headers=self.claude_headers,
                    json=data,
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    assistant_message = result['content'][0]['text']
                    
                    # Save to history
                    self.conversation_history[channel_id].append({"role": "user", "content": prompt})
                    self.conversation_history[channel_id].append({"role": "assistant", "content": assistant_message})
                    
                    return assistant_message
                else:
                    return f"❌ Claude API Error {response.status_code}: {response.text[:200]}"
            
            elif self.current_model == 'gemini' and self.gemini_model:
                # Gemini API call
                # Convert history to Gemini format
                chat = self.gemini_model.start_chat(history=[])
                response = chat.send_message(prompt)
                
                # Save to history
                self.conversation_history[channel_id].append({"role": "user", "content": prompt})
                self.conversation_history[channel_id].append({"role": "assistant", "content": response.text})
                
                return response.text
            
            else:
                return f"❌ Model {self.current_model} not available"
                
        except Exception as e:
            return f"❌ Error with {self.current_model}: {str(e)[:200]}"
    
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
                    response = await self.query_ai(content, message.channel.id)
                
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
bot = UnifiedBot()

# Remove default help command
bot.remove_command('help')

@bot.command(name='model')
async def switch_model(ctx, model_name: str = None):
    """Switch between AI models"""
    if not model_name:
        models_list = "\n".join([f"• **{k}**: {v}" for k, v in bot.models.items()])
        current = f"**Current:** {bot.models[bot.current_model]}"
        await ctx.send(f"{current}\n\n**Available models:**\n{models_list}\n\nUse `!model <name>` to switch")
        return
    
    if model_name.lower() in bot.models:
        bot.current_model = model_name.lower()
        await ctx.send(f"✅ Switched to **{bot.models[bot.current_model]}**")
    else:
        await ctx.send(f"❌ Unknown model. Choose from: {', '.join(bot.models.keys())}")

@bot.command(name='ask')
async def ask_ai(ctx, *, question: str):
    """Ask the current AI model"""
    model_name = bot.models[bot.current_model]
    await ctx.send(f"🤔 Asking {model_name}...")
    
    async with ctx.typing():
        response = await bot.query_ai(question, ctx.channel.id)
    
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

@bot.command(name='status')
async def check_status(ctx):
    """Check bot and model status"""
    status = "**🤖 Bot Status:**\n\n"
    status += f"**Current Model:** {bot.models[bot.current_model]}\n\n"
    status += "**Model Availability:**\n"
    status += f"• Claude: {'✅' if ANTHROPIC_API_KEY else '❌'}\n"
    status += f"• Gemini: {'✅' if bot.gemini_model else '❌'}\n\n"
    status += f"**Bot Latency:** {round(bot.latency * 1000)}ms"
    
    await ctx.send(status)

@bot.command(name='help')
async def help_command(ctx):
    """Show help"""
    help_text = """
**🤖 Unified AI Discord Bot Commands:**

`!model [claude/gemini]` - Switch AI models
`!ask [question]` - Ask the current model
`!clear` - Clear conversation history
`!status` - Check bot status
`@mention` - Chat with the bot

Currently supports Claude 3 Sonnet and Gemini Pro.
The bot maintains conversation context per channel.
"""
    await ctx.send(help_text)

def main():
    """Launch the bot"""
    print("""
    🤖 UNIFIED AI DISCORD BOT 🤖
    ============================
    Claude + Gemini
    
    Starting bot...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    print(f"✅ Discord token: {DISCORD_TOKEN[:20]}...")
    print(f"✅ Claude API: {'Available' if ANTHROPIC_API_KEY else 'Not configured'}")
    print(f"✅ Gemini API: {'Available' if GEMINI_API_KEY else 'Not configured'}")
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()
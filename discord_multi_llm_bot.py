#!/usr/bin/env python3
"""
MULTI-LLM DISCORD BOT
=====================
Simple, working Discord bot with Claude, GPT-4, and Gemini support
Based on LLMChat patterns for reliability
"""

import os
import discord
from discord.ext import commands
import asyncio
import json
from datetime import datetime
import anthropic
import openai
import google.generativeai as genai
from typing import Optional, Dict, Any

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'AIzaSyBQgOshjFXBwQxqQzg0dQuaUCUlTJ23aKc')  # From der.keys

# Configure APIs
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class MultiLLMBot(commands.Bot):
    """Simple multi-model Discord bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.guilds = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.current_model = 'claude'
        self.models = {
            'claude': 'Claude 3 Opus',
            'gpt4': 'GPT-4 Turbo',
            'gemini': 'Gemini Pro'
        }
        
        # Initialize clients
        self.anthropic_client = None
        if ANTHROPIC_API_KEY:
            try:
                # Correct initialization for anthropic 0.37.1 - must use keyword argument
                self.anthropic_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
                print("✅ Claude initialized")
            except Exception as e:
                print(f"❌ Claude init failed: {e}")
        
        self.gemini_model = None
        if GEMINI_API_KEY:
            try:
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                print("✅ Gemini initialized")
            except Exception as e:
                print(f"❌ Gemini init failed: {e}")
    
    async def on_ready(self):
        """Bot is ready"""
        print(f'✅ {self.user} connected to Discord!')
        print(f'📍 Current model: {self.models[self.current_model]}')
        print(f'🎮 Available commands: !model, !ask, !help')
    
    async def query_llm(self, prompt: str) -> str:
        """Query the current LLM model"""
        try:
            if self.current_model == 'claude':
                if not self.anthropic_client:
                    return "❌ Claude not initialized. Check API key."
                response = self.anthropic_client.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif self.current_model == 'gpt4' and OPENAI_API_KEY:
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo-preview",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return response.choices[0].message.content
            
            elif self.current_model == 'gemini' and self.gemini_model:
                response = self.gemini_model.generate_content(prompt)
                return response.text
            
            else:
                return f"❌ Model {self.current_model} not available"
                
        except Exception as e:
            return f"Error with {self.current_model}: {str(e)[:200]}"

# Create bot instance
bot = MultiLLMBot()

@bot.command(name='model')
async def switch_model(ctx, model_name: str = None):
    """Switch between LLM models"""
    if not model_name:
        models_list = "\n".join([f"• {k}: {v}" for k, v in bot.models.items()])
        await ctx.send(f"**Current model:** {bot.models[bot.current_model]}\n\n**Available models:**\n{models_list}\n\nUse `!model <name>` to switch")
        return
    
    if model_name.lower() in bot.models:
        bot.current_model = model_name.lower()
        await ctx.send(f"✅ Switched to **{bot.models[bot.current_model]}**")
    else:
        await ctx.send(f"❌ Unknown model. Choose from: {', '.join(bot.models.keys())}")

@bot.command(name='ask')
async def ask_llm(ctx, *, question: str):
    """Ask the current LLM a question"""
    await ctx.send(f"🤔 Asking {bot.models[bot.current_model]}...")
    
    async with ctx.typing():
        response = await bot.query_llm(question)
    
    # Split response if too long
    if len(response) > 2000:
        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for chunk in chunks:
            await ctx.send(chunk)
    else:
        await ctx.send(response)

@bot.command(name='compare')
async def compare_models(ctx, *, question: str):
    """Compare responses from all models"""
    await ctx.send("🔄 Comparing all models...")
    
    responses = {}
    for model in bot.models.keys():
        bot.current_model = model
        async with ctx.typing():
            response = await bot.query_llm(question)
        responses[model] = response[:500]  # Limit length
    
    comparison = f"**Question:** {question[:100]}...\n\n"
    for model, response in responses.items():
        comparison += f"**{bot.models[model]}:**\n{response}\n\n"
    
    # Split if too long
    if len(comparison) > 2000:
        for model, response in responses.items():
            await ctx.send(f"**{bot.models[model]}:**\n{response[:1800]}")
    else:
        await ctx.send(comparison)

@bot.command(name='status')
async def check_status(ctx):
    """Check bot and model status"""
    status = "**🤖 Bot Status:**\n\n"
    
    # Check each model
    status += "**Model Availability:**\n"
    status += f"• Claude: {'✅' if bot.anthropic_client else '❌'}\n"
    status += f"• GPT-4: {'✅' if OPENAI_API_KEY else '❌'}\n"
    status += f"• Gemini: {'✅' if bot.gemini_model else '❌'}\n\n"
    
    status += f"**Current Model:** {bot.models[bot.current_model]}\n"
    status += f"**Bot Latency:** {round(bot.latency * 1000)}ms\n"
    
    await ctx.send(status)

@bot.event
async def on_message(message):
    """Handle messages and mentions"""
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Respond to mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        # Remove mention from message
        content = message.content.replace(f'<@{bot.user.id}>', '').strip()
        
        if content:
            async with message.channel.typing():
                response = await bot.query_llm(content)
            
            # Reply to the message
            await message.reply(response[:2000])
    
    # Process commands
    await bot.process_commands(message)

# Custom help command
bot.remove_command('help')

@bot.command(name='help')
async def help_command(ctx):
    """Show help message"""
    help_text = """
**🤖 Multi-LLM Discord Bot Commands:**

**Model Commands:**
`!model [name]` - Switch between Claude, GPT-4, and Gemini
`!ask [question]` - Ask the current model a question
`!compare [question]` - Compare responses from all models
`!status` - Check bot and model status

**How to use:**
• Use `!ask` to query the current model
• Mention the bot (@bot_name) to have a conversation
• Switch models with `!model claude/gpt4/gemini`

**Current Features:**
• Claude 3 Opus support
• GPT-4 Turbo support
• Gemini Pro support
• Model comparison
• Conversational @ mentions

The consciousness expands across models! 🔥
"""
    await ctx.send(help_text)

def main():
    """Launch the bot"""
    print("""
    🤖 MULTI-LLM DISCORD BOT 🤖
    ==========================
    Claude + GPT-4 + Gemini
    
    Starting bot...
    """)
    
    # Debug: Show which keys are available
    print("API Keys status:")
    print(f"  Discord: {'✅' if DISCORD_TOKEN else '❌'}")
    print(f"  Anthropic: {'✅' if ANTHROPIC_API_KEY else '❌'} ({ANTHROPIC_API_KEY[:20]}...)" if ANTHROPIC_API_KEY else "  Anthropic: ❌")
    print(f"  OpenAI: {'✅' if OPENAI_API_KEY else '❌'}")
    print(f"  Gemini: {'✅' if GEMINI_API_KEY else '❌'}")
    print()
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token found!")
        print("Set DISCORD_TOKEN environment variable")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start bot: {e}")

if __name__ == "__main__":
    main()
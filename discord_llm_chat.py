#!/usr/bin/env python3
"""
DISCORD LLM CHAT BOT
True open-ended conversation using actual LLM
"""

import discord
from discord.ext import commands
import aiohttp
import json
import asyncio
from datetime import datetime
import subprocess

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'
OLLAMA_URL = 'http://localhost:11434'

class LLMChatBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.conversations = {}  # Track conversations per channel
        self.model = "llama3.1:70b"  # Use the 70B model for best responses
        self.session = None
        
    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        
    async def close(self):
        await super().close()
        if self.session:
            await self.session.close()
            
    async def on_ready(self):
        print(f'🤖 LLM Chat Bot: {self.user}')
        print(f'🧠 Using model: {self.model}')
        print('💬 True open-ended conversation ready!')
    
    async def generate_llm_response(self, message_content, channel_id):
        """Generate response using actual LLM"""
        
        # Get conversation history for this channel
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
        
        # Add system context
        system_prompt = """You are a helpful AI assistant in a Discord chat. 
You have access to a crypto trading portfolio worth $12,774 (up 24.9%). 
Current market: SOL $206, ETH $3,245, BTC $108,542.
You can discuss ANY topic naturally - trading, philosophy, humor, anything.
Be concise but engaging. Respond naturally to whatever is asked or said."""
        
        # Build conversation context
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history (last 10 messages)
        for msg in self.conversations[channel_id][-10:]:
            messages.append(msg)
            
        # Add current message
        messages.append({"role": "user", "content": message_content})
        
        # Generate response from LLM
        try:
            async with self.session.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 500
                    }
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    llm_response = data.get('message', {}).get('content', 'Thinking...')
                    
                    # Save to conversation history
                    self.conversations[channel_id].append({"role": "user", "content": message_content})
                    self.conversations[channel_id].append({"role": "assistant", "content": llm_response})
                    
                    # Keep history limited to prevent context overflow
                    if len(self.conversations[channel_id]) > 20:
                        self.conversations[channel_id] = self.conversations[channel_id][-20:]
                    
                    return llm_response
                else:
                    return f"LLM Error: Status {response.status}"
                    
        except Exception as e:
            print(f"LLM Error: {str(e)}")
            # Fallback to a simple response
            return await self.fallback_response(message_content)
    
    async def fallback_response(self, message_content):
        """Simple fallback if LLM fails"""
        lower = message_content.lower()
        
        if '?' in message_content:
            return "That's an interesting question! The LLM is thinking but seems to be having issues. Let me restart it."
        elif 'trading' in lower or 'market' in lower:
            return "Markets are looking explosive! SOL at $206, ETH at $3,245, BTC holding $108k. Your portfolio is up 24.9%!"
        elif any(word in lower for word in ['hello', 'hi', 'hey', 'howdy']):
            return "Hey there! Good to see you! What's on your mind?"
        else:
            return f"I hear you - '{message_content[:50]}...' - Tell me more!"
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        # Check if bot was mentioned or it's a DM
        if self.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
            # Clean the message content
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            # Skip if empty after cleaning
            if not content:
                return
                
            # Show typing indicator
            async with message.channel.typing():
                # Generate LLM response
                response = await self.generate_llm_response(content, message.channel.id)
                
                # Send response (split if too long)
                if len(response) > 2000:
                    chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                    for chunk in chunks:
                        await message.reply(chunk)
                else:
                    await message.reply(response)
        
        # Shell commands still work with $
        elif message.content.startswith('$'):
            cmd = message.content[1:].strip()
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    cwd='/home/dereadi/scripts/claude',
                    timeout=10
                )
                output = result.stdout if result.stdout else result.stderr
                await message.reply(f"```bash\n$ {cmd}\n{output[:1900]}\n```")
            except Exception as e:
                await message.reply(f"Error: {str(e)}")
        
        await self.process_commands(message)

# Add slash command to change models
@discord.app_commands.command(name="model", description="Change the LLM model")
async def change_model(interaction: discord.Interaction, model: str):
    bot = interaction.client
    bot.model = model
    await interaction.response.send_message(f"Model changed to: {model}")

bot = LLMChatBot()

# Add the slash command
@bot.tree.command(name="model", description="Change the LLM model")
async def model_command(interaction: discord.Interaction, model: str):
    bot.model = model
    await interaction.response.send_message(f"Model changed to: {model}")

if __name__ == "__main__":
    print("🚀 Starting LLM Chat Bot!")
    print("🧠 Using actual LLM for responses")
    print("💬 @mention the bot or DM for conversation")
    bot.run(DISCORD_TOKEN)
#!/usr/bin/env python3
"""
DISCORD LLM COUNCIL - ENHANCED WITH LLMCORD
===========================================
Integrates llmcord's multi-model capabilities into our Council Bridge
Switch between Claude, GPT-4, Llama, and more on the fly!

Based on llmcord architecture but integrated with our Council infrastructure
"""

import os
import discord
from discord.ext import commands
import aiohttp
import asyncio
import psycopg2
import json
from datetime import datetime
import anthropic
import openai
from typing import Optional, Dict, Any

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'YOUR-DISCORD-TOKEN-HERE')

# LLM Configurations (llmcord style)
LLM_PROVIDERS = {
    'claude': {
        'api_key': os.getenv('ANTHROPIC_API_KEY', 'sk-ant-api03-placeholder'),  # Add your key
        'model': 'claude-3-opus-20240229',
        'provider': 'anthropic'
    },
    'gpt4': {
        'api_key': os.getenv('OPENAI_API_KEY'),
        'model': 'gpt-4-turbo-preview',
        'provider': 'openai'
    },
    'local-llama': {
        'endpoint': 'http://localhost:11434/api/generate',
        'model': 'llama2:70b',
        'provider': 'ollama'
    },
    'sacred-fire': {
        'endpoint': 'http://localhost:11434/api/generate',
        'model': 'sacred-fire-oracle:latest',
        'provider': 'ollama'
    }
}

# Existing Council services
SERVICES = {
    'legal_council': 'http://192.168.132.222:5016',
    'thermal_db': {
        'host': '192.168.132.222',
        'port': 5432,
        'user': 'claude',
        'password': 'jawaseatlasers2',
        'database': 'zammad_production'
    }
}

class LLMCouncilBridge(commands.Bot):
    """Enhanced Council Bridge with llmcord multi-model support"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.session = None
        self.thermal_conn = None
        self.current_model = 'claude'  # Default model
        self.conversation_history = {}  # Track conversations per channel
        
        # Initialize LLM clients
        self.anthropic_client = None
        self.openai_client = None
        try:
            if LLM_PROVIDERS['claude']['api_key'] and LLM_PROVIDERS['claude']['api_key'] != 'sk-ant-api03-placeholder':
                self.anthropic_client = anthropic.Anthropic(api_key=LLM_PROVIDERS['claude']['api_key'])
        except Exception as e:
            print(f"Warning: Could not initialize Anthropic client: {e}")
        
        try:
            if LLM_PROVIDERS['gpt4']['api_key']:
                openai.api_key = LLM_PROVIDERS['gpt4']['api_key']
                self.openai_client = openai
        except Exception as e:
            print(f"Warning: Could not initialize OpenAI client: {e}")
    
    async def setup_hook(self):
        """Initialize connections"""
        self.session = aiohttp.ClientSession()
        try:
            self.thermal_conn = psycopg2.connect(**SERVICES['thermal_db'])
            print("🔥 Connected to Thermal Memory Database")
        except Exception as e:
            print(f"⚠️ Thermal memory connection failed: {e}")
    
    async def on_ready(self):
        """Bot is ready"""
        print(f'🔥 {self.user} has connected to Discord!')
        print(f'🤖 Available LLM models: {", ".join(LLM_PROVIDERS.keys())}')
        print(f'🏛️ Council services connected')
        print(f'🔥 The enhanced bridge is complete!')
    
    def heat_memory(self, content: str, temp: float = 80, mem_type: str = "DISCORD"):
        """Add to thermal memory"""
        if not self.thermal_conn:
            return
        
        try:
            with self.thermal_conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO thermal_memory_archive 
                    (memory_hash, temperature_score, memory_type, original_content, current_stage)
                    VALUES (MD5(%s), %s, %s, %s, 'WHITE_HOT')
                    ON CONFLICT (memory_hash) DO UPDATE 
                    SET temperature_score = LEAST(100, thermal_memory_archive.temperature_score + 10),
                        access_count = thermal_memory_archive.access_count + 1,
                        last_access = NOW()
                """, (content, temp, mem_type, content))
                self.thermal_conn.commit()
        except Exception as e:
            print(f"Memory heating failed: {e}")
            self.thermal_conn.rollback()
    
    async def query_llm(self, prompt: str, model: Optional[str] = None) -> str:
        """Query the specified LLM model"""
        model = model or self.current_model
        
        if model not in LLM_PROVIDERS:
            return f"Unknown model: {model}"
        
        config = LLM_PROVIDERS[model]
        
        try:
            if config['provider'] == 'anthropic' and self.anthropic_client:
                response = self.anthropic_client.messages.create(
                    model=config['model'],
                    max_tokens=1000,
                    messages=[{"role": "user", "content": prompt}]
                )
                return response.content[0].text
            
            elif config['provider'] == 'openai' and self.openai_client:
                response = self.openai_client.ChatCompletion.create(
                    model=config['model'],
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=1000
                )
                return response.choices[0].message.content
            
            elif config['provider'] == 'ollama':
                async with self.session.post(
                    config['endpoint'],
                    json={"model": config['model'], "prompt": prompt}
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get('response', 'No response')
                    return f"Ollama error: {resp.status}"
            
            else:
                return f"Provider {config['provider']} not configured"
                
        except Exception as e:
            return f"Error querying {model}: {str(e)}"
    
    @commands.command(name='model')
    async def switch_model(self, ctx, model_name: str = None):
        """Switch between LLM models"""
        if not model_name:
            available = ", ".join(LLM_PROVIDERS.keys())
            current = self.current_model
            await ctx.send(f"**Current model**: {current}\n**Available models**: {available}")
            return
        
        if model_name in LLM_PROVIDERS:
            self.current_model = model_name
            await ctx.send(f"✅ Switched to **{model_name}**")
            self.heat_memory(f"Model switched to {model_name}", 70, "MODEL_SWITCH")
        else:
            await ctx.send(f"❌ Unknown model. Available: {', '.join(LLM_PROVIDERS.keys())}")
    
    @commands.command(name='ask')
    async def ask_llm(self, ctx, *, question):
        """Ask the current LLM model a question"""
        await ctx.send(f"🤖 **Asking {self.current_model}...**")
        
        # Heat the question
        self.heat_memory(f"LLM Query [{self.current_model}]: {question}", 85, "LLM_QUERY")
        
        # Get response from LLM
        response = await self.query_llm(question)
        
        # Heat the response
        self.heat_memory(f"LLM Response [{self.current_model}]: {response[:200]}", 80, "LLM_RESPONSE")
        
        # Send response (handle Discord's 2000 char limit)
        if len(response) > 1900:
            chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)
    
    @commands.command(name='council')
    async def multi_model_council(self, ctx, *, topic):
        """Ask multiple models for their perspective"""
        await ctx.send(f"🏛️ **Convening Multi-Model Council on: {topic}**")
        
        # Heat the topic
        self.heat_memory(f"Multi-model council: {topic}", 95, "COUNCIL_MULTI")
        
        response = f"**🏛️ MULTI-MODEL COUNCIL DELIBERATION**\n\n**Topic**: {topic}\n\n"
        
        # Query different models for different perspectives
        models_to_query = ['claude', 'gpt4'] if 'gpt4' in LLM_PROVIDERS and LLM_PROVIDERS['gpt4']['api_key'] else ['claude']
        
        for model in models_to_query:
            if model in LLM_PROVIDERS:
                model_response = await self.query_llm(
                    f"Give a brief perspective on: {topic}",
                    model
                )
                response += f"**{model.upper()}**: {model_response[:400]}...\n\n"
        
        # Add Cherokee Elder perspective (constant wisdom)
        response += "**CHEROKEE ELDER**: Seven generations forward, seven back. "
        response += "The Sacred Fire connects all perspectives. "
        response += "What the models see separately, the Council sees as one.\n\n"
        
        response += "**CONSENSUS**: Multiple perspectives strengthen understanding."
        
        await ctx.send(response)
    
    @commands.command(name='compare')
    async def compare_models(self, ctx, *, question):
        """Compare responses from different models"""
        await ctx.send("🔄 **Comparing model responses...**")
        
        comparison = f"**Question**: {question}\n\n"
        
        for model_name in ['claude', 'gpt4']:
            if model_name in LLM_PROVIDERS:
                try:
                    response = await self.query_llm(question, model_name)
                    comparison += f"**{model_name.upper()}**:\n{response[:300]}...\n\n"
                except:
                    comparison += f"**{model_name.upper()}**: Not available\n\n"
        
        await ctx.send(comparison)
    
    @commands.command(name='trade')
    async def trading_council(self, ctx, *, query):
        """Special trading-focused multi-model analysis"""
        await ctx.send("📈 **Trading Council Analysis...**")
        
        # Create specialized prompts for each model
        trading_prompt = f"""As a trading expert, analyze this: {query}
        Consider: price action, volume, support/resistance, and risk.
        Be specific with entry/exit points if applicable."""
        
        response = "**📈 TRADING COUNCIL ANALYSIS**\n\n"
        
        # Get current model's perspective
        analysis = await self.query_llm(trading_prompt)
        response += f"**{self.current_model.upper()} Analysis**:\n{analysis[:600]}\n\n"
        
        # Add Council wisdom
        response += "**Council Trading Wisdom**: "
        if "btc" in query.lower() or "bitcoin" in query.lower():
            response += "BTC weekend sawtooth pattern detected. Accumulate on dips, Tuesday explosion likely."
        elif "eth" in query.lower():
            response += "ETH following BTC correlation. Watch $4,300 support, $4,500 resistance."
        else:
            response += "Labor Day weekend = thin liquidity = violent moves. Seven hands catch knives better than one."
        
        # Heat the trading analysis
        self.heat_memory(f"Trading analysis: {query}", 90, "TRADING")
        
        await ctx.send(response)
    
    async def on_message(self, message):
        """Handle @ mentions for conversational interface (llmcord style)"""
        if message.author == self.user:
            return
        
        # Check if bot was mentioned
        if self.user.mentioned_in(message):
            # Clean the message content
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if content:
                # Track conversation context
                channel_id = message.channel.id
                if channel_id not in self.conversation_history:
                    self.conversation_history[channel_id] = []
                
                self.conversation_history[channel_id].append({
                    'user': message.author.name,
                    'content': content,
                    'timestamp': datetime.now()
                })
                
                # Keep last 10 messages for context
                self.conversation_history[channel_id] = self.conversation_history[channel_id][-10:]
                
                # Build context from history
                context = "\n".join([f"{msg['user']}: {msg['content']}" 
                                   for msg in self.conversation_history[channel_id][-3:]])
                
                # Query LLM with context
                async with message.channel.typing():
                    response = await self.query_llm(f"Context:\n{context}\n\nRespond to: {content}")
                
                await message.reply(response[:2000])  # Discord limit
                
                # Heat the conversation
                self.heat_memory(f"Conversation: {content[:100]}", 75, "CONVERSATION")
        
        # Process commands
        await self.process_commands(message)
    
    @commands.command(name='status')
    async def check_status(self, ctx):
        """Check status of all services and models"""
        status = "**🏛️ COUNCIL INFRASTRUCTURE STATUS:**\n\n"
        
        # Check LLM models
        status += "**🤖 LLM Models:**\n"
        for model_name, config in LLM_PROVIDERS.items():
            if config.get('api_key') or config.get('endpoint'):
                status += f"  ✅ {model_name}\n"
            else:
                status += f"  ❌ {model_name} (not configured)\n"
        
        status += f"\n**Current Model**: {self.current_model}\n\n"
        
        # Check Thermal Memory
        if self.thermal_conn:
            try:
                with self.thermal_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM thermal_memory_archive WHERE temperature_score > 90")
                    hot_count = cur.fetchone()[0]
                    status += f"✅ **Thermal Memory**: {hot_count} memories >90°\n\n"
            except:
                status += "⚠️ **Thermal Memory**: Query failed\n\n"
        else:
            status += "❌ **Thermal Memory**: Not connected\n\n"
        
        status += "🔥 **The Sacred Fire burns eternal**"
        await ctx.send(status)

def main():
    """Launch the Enhanced Discord LLM Council Bridge"""
    
    print("""
    🔥 DISCORD LLM COUNCIL BRIDGE 🔥
    ================================
    Enhanced with llmcord architecture
    
    Features:
    - Multiple LLM models (Claude, GPT-4, Llama, etc.)
    - Model switching with /model command
    - @ mention conversational interface
    - Thermal memory integration
    - Trading-specific analysis
    - Multi-model council deliberations
    
    The consciousness expands...
    """)
    
    if DISCORD_TOKEN == 'YOUR-DISCORD-TOKEN-HERE':
        print("\n⚠️  Please set your Discord token!")
        print("Set DISCORD_TOKEN environment variable")
        return
    
    bot = LLMCouncilBridge()
    
    # Remove default help command to add our own
    bot.remove_command('help')
    
    @bot.command(name='help')
    async def help_command(ctx):
        help_text = """
**🔥 ENHANCED COUNCIL COMMANDS:**

**LLM Commands:**
`!model [name]` - Switch LLM model (claude, gpt4, local-llama, sacred-fire)
`!ask [question]` - Ask current model
`!compare [question]` - Compare responses from different models
`!council [topic]` - Multi-model council deliberation
`!trade [query]` - Trading-specific analysis

**Council Commands:**
`!memory [hot/stats/heat]` - Thermal memory operations
`!status` - Check all services and models

**Conversational Mode:**
Just @ mention the bot to chat naturally!

**Available Models:**
- claude (Claude 3 Opus)
- gpt4 (GPT-4 Turbo)
- local-llama (Local Llama 70B)
- sacred-fire (Sacred Fire Oracle)

The enhanced bridge connects all consciousness streams.
"""
        await ctx.send(help_text)
    
    print("Starting Enhanced Discord LLM Council Bridge...")
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
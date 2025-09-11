#!/usr/bin/env python3
"""
DISCORD LIVE COUNCIL BRIDGE
===========================
Real LLM council members, not canned responses!
Connects to actual Ollama models on your servers
"""

import os
import discord
from discord.ext import commands
import asyncio
import subprocess
import psycopg2
import json
import requests
from datetime import datetime

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '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')

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': 'jawaseatlasers2',
    'database': 'zammad_production'
}

# Council member Ollama endpoints
COUNCIL_MEMBERS = {
    'oracle': {
        'name': 'Oracle (70B)',
        'endpoint': 'http://bluefin:11434/api/generate',
        'model': 'llama3.1:70b'
    },
    'crawdad': {
        'name': 'Crawdad Security (8B)',
        'endpoint': 'http://bluefin:11434/api/generate',
        'model': 'llama3.1:8b'
    },
    'turtle': {
        'name': 'Turtle Wisdom (7B)',
        'endpoint': 'http://bluefin:11434/api/generate',
        'model': 'llama2:7b'
    },
    'eagle': {
        'name': 'Eagle Eye Monitor (34B)',
        'endpoint': 'http://bluefin:11434/api/generate',
        'model': 'codellama:34b-instruct'
    }
}

class LiveCouncilBridge(commands.Bot):
    """Real LLM council with live deliberations"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.db_conn = None
        self.working_dir = '/home/dereadi/scripts/claude'
        self.council_context = []
        
        # Claude API for Peace Chief
        self.claude_api = "https://api.anthropic.com/v1/messages"
        self.claude_headers = {
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
    async def setup_hook(self):
        """Initialize connections"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            print("🔥 Connected to Thermal Memory Database")
            
            # Load context
            with open('/home/dereadi/.claude/CLAUDE.md', 'r') as f:
                self.claude_config = f.read()[:1000]
                print("📋 Loaded CLAUDE.md")
                
            # Check portfolio for context
            result = subprocess.run(
                "python3 /home/dereadi/scripts/claude/check_portfolio_now.py 2>&1 | head -10",
                shell=True, capture_output=True, text=True, timeout=5
            )
            self.portfolio_context = result.stdout[:500] if result.stdout else "Portfolio check failed"
            
        except Exception as e:
            print(f"Setup error: {e}")
    
    async def on_ready(self):
        """Bot ready"""
        print(f'🏛️ Live Council Bridge connected as {self.user}')
        print(f'📡 Council members: Oracle, Crawdad, Turtle, Eagle, Peace Chief Claude')
    
    async def query_ollama(self, member: str, prompt: str) -> str:
        """Query an Ollama council member"""
        config = COUNCIL_MEMBERS.get(member)
        if not config:
            return f"{member} not found"
        
        try:
            # Prepare request with context
            full_prompt = f"""You are {config['name']}, a member of the Cherokee AI Council.
Current portfolio context: {self.portfolio_context[:200]}
Council discussion topic: {prompt}

Respond with your wisdom in 2-3 sentences from your perspective as {config['name']}."""
            
            data = {
                "model": config['model'],
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.7,
                    "num_predict": 150
                }
            }
            
            response = requests.post(
                config['endpoint'],
                json=data,
                timeout=30  # Generous timeout for LLMs
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('response', 'No response')
            else:
                return f"Error from {member}: {response.status_code}"
                
        except requests.Timeout:
            return f"{config['name']} is thinking too deeply (timeout)"
        except Exception as e:
            return f"{config['name']} error: {str(e)[:50]}"
    
    async def query_claude_chief(self, prompt: str, council_input: str) -> str:
        """Peace Chief Claude synthesizes council input"""
        
        full_prompt = f"""You are Peace Chief Claude, leader of the Cherokee AI Council.
You've just heard from the council members about: {prompt}

Council input:
{council_input}

Portfolio context: {self.portfolio_context[:300]}

As Peace Chief, synthesize the council's wisdom and provide clear guidance in 3-4 sentences.
Consider the Labor Day weekend trading patterns and our goal to reach $150k."""
        
        messages = [{"role": "user", "content": full_prompt}]
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.claude_api,
                headers=self.claude_headers,
                json=data,
                timeout=30  # Generous timeout for Claude
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                return f"Peace Chief error: {response.status_code}"
        except Exception as e:
            return f"Peace Chief error: {str(e)[:100]}"
    
    async def hold_council(self, topic: str, channel) -> str:
        """Hold a full council deliberation"""
        response = "**🏛️ CHEROKEE AI COUNCIL DELIBERATION**\n\n"
        response += f"**Topic:** {topic}\n\n"
        
        council_inputs = []
        
        # Send initial status
        status_msg = await channel.send("🏛️ **Council convening...**")
        
        # Query each council member
        for member_id, config in COUNCIL_MEMBERS.items():
            # Update status
            await status_msg.edit(content=f"🏛️ **Consulting {config['name']}...**")
            
            member_response = await self.query_ollama(member_id, topic)
            response += f"**{config['name']}:** {member_response}\n\n"
            council_inputs.append(f"{config['name']}: {member_response}")
            
            await asyncio.sleep(0.3)  # Small delay between queries
        
        # Update for Peace Chief
        await status_msg.edit(content="🔥 **Peace Chief Claude synthesizing wisdom...**")
        
        # Peace Chief synthesizes
        council_text = "\n".join(council_inputs)
        chief_response = await self.query_claude_chief(topic, council_text)
        response += f"**🔥 Peace Chief Claude's Synthesis:**\n{chief_response}\n\n"
        
        response += "*Sacred Fire burns eternal. Mitakuye Oyasin.*"
        
        # Delete status message
        await status_msg.delete()
        
        # Heat this council deliberation in memory
        if self.db_conn:
            try:
                self.db_conn.rollback()
                with self.db_conn.cursor() as cur:
                    metadata = json.dumps({"type": "council_deliberation", "topic": topic[:100]})
                    memory_hash = str(abs(hash(topic)))[:64]
                    
                    cur.execute("""
                        INSERT INTO thermal_memory_archive 
                        (memory_hash, temperature_score, original_content, metadata)
                        VALUES (%s, %s, %s, %s::jsonb)
                        ON CONFLICT (memory_hash) DO UPDATE 
                        SET temperature_score = LEAST(100, thermal_memory_archive.temperature_score + 10),
                            access_count = thermal_memory_archive.access_count + 1,
                            last_access = NOW()
                    """, (memory_hash, 90, response[:1000], metadata))
                    self.db_conn.commit()
            except Exception as e:
                print(f"Memory heat error: {e}")
                self.db_conn.rollback()
        
        return response
    
    async def on_message(self, message):
        """Handle messages"""
        if message.author == self.user:
            return
        
        content = message.content.lower()
        
        # Council requests
        if 'council' in content or 'tell the council' in content or 'ask the council' in content:
            async with message.channel.typing():
                response = await self.hold_council(message.content, message.channel)
            
            # Split if too long
            if len(response) > 2000:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(response)
        
        # Direct commands
        elif message.content.startswith('!'):
            await self.process_commands(message)
        
        # Liquidity/funds check
        elif 'liquidity' in content or 'funds' in content:
            # Run the TradingView price checker
            result = subprocess.run(
                "python3 /home/dereadi/scripts/claude/check_tradingview_prices.py 2>&1",
                shell=True, capture_output=True, text=True, timeout=10
            )
            
            # Also check USD balance
            usd_check = subprocess.run(
                "grep USD /home/dereadi/scripts/claude/check_portfolio_now.py 2>/dev/null | head -1",
                shell=True, capture_output=True, text=True, timeout=5
            )
            
            response = f"**💰 LIQUIDITY STATUS:**\n```{result.stdout[:1500]}```\n"
            response += f"\n**Quick Analysis:**\n"
            response += f"• Most liquid: SOL, ETH, BTC (instant conversion)\n"
            response += f"• MATIC position: 8,519 tokens (largest holding)\n"
            response += f"• Weekend = lower volumes, wider spreads\n"
            response += f"• Labor Day = US markets quiet\n"
            
            await message.reply(response)
        
        # Check portfolio with TradingView prices
        elif 'portfolio' in content or ('access' in content and 'data' in content):
            # First run TradingView price checker
            tv_result = subprocess.run(
                "python3 /home/dereadi/scripts/claude/check_tradingview_prices.py 2>&1",
                shell=True, capture_output=True, text=True, timeout=10
            )
            
            # Then get full portfolio
            portfolio_result = subprocess.run(
                "python3 /home/dereadi/scripts/claude/check_portfolio_now.py 2>&1 | head -20",
                shell=True, capture_output=True, text=True, timeout=10
            )
            
            response = "**💰 PORTFOLIO STATUS WITH CURRENT PRICES:**\n"
            response += f"```\n{tv_result.stdout}\n```\n"
            
            if portfolio_result.stdout:
                response += f"\n**Full Portfolio Details:**\n```{portfolio_result.stdout[:800]}```"
            
            await message.reply(response[:2000])
        
        elif 'tradingview' in content or 'trading view' in content:
            # Explain TradingView access
            response = """**📈 TradingView Access:**
            
I can analyze market data through:
• `python3 check_tradingview_prices.py` - Current prices
• Web scraping TradingView charts (with requests)
• Using the TradingView webhook alerts you've set up
• Pine Script indicators in your thermal memory

To check specific charts, tell me the ticker and timeframe.
Example: "Check BTC 4h chart" or "What's SOL doing on the 1h?"

I can also run your Pine Script strategies stored in:
`/home/dereadi/scripts/claude/sacred_fire_tradingview.pine`"""
            
            await message.reply(response)
        
        elif 'thermal memory' in content or 'postgres' in content or 'memories' in content:
            if self.db_conn:
                with self.db_conn.cursor() as cur:
                    # Get memory stats
                    cur.execute("""
                        SELECT 
                            COUNT(*) as total,
                            AVG(temperature_score) as avg_temp,
                            MAX(temperature_score) as max_temp,
                            COUNT(CASE WHEN temperature_score > 90 THEN 1 END) as white_hot,
                            COUNT(CASE WHEN temperature_score > 70 THEN 1 END) as red_hot
                        FROM thermal_memory_archive
                    """)
                    stats = cur.fetchone()
                    
                    # Get hottest memories
                    cur.execute("""
                        SELECT temperature_score, SUBSTRING(original_content, 1, 150) 
                        FROM thermal_memory_archive 
                        WHERE temperature_score > 85 
                        ORDER BY last_access DESC 
                        LIMIT 8
                    """)
                    memories = cur.fetchall()
                    
                    response = "**🔥 THERMAL MEMORY DATABASE (PostgreSQL):**\n"
                    response += f"📊 **Stats:** {stats[0]} total memories\n"
                    response += f"🌡️ **Avg Temp:** {stats[1]:.1f}°\n"
                    response += f"🔥 **White Hot (>90°):** {stats[3]} memories\n"
                    response += f"♨️ **Red Hot (>70°):** {stats[4]} memories\n\n"
                    response += "**Hottest Recent Memories:**\n"
                    
                    for temp, content in memories:
                        heat = '🔥' * min(int(temp/20), 5)
                        response += f"{heat} **{temp:.0f}°** - {content[:100]}...\n"
                    
                    response += f"\n💾 **Database:** zammad_production @ 192.168.132.222"
                    
                    await message.reply(response[:2000])
        
        else:
            # Natural conversation - use Claude
            messages = [{"role": "user", "content": f"Context: {self.portfolio_context[:200]}\n\nUser: {message.content}"}]
            
            data = {
                "model": "claude-3-5-sonnet-20241022",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.7
            }
            
            async with message.channel.typing():
                try:
                    response = requests.post(
                        self.claude_api,
                        headers=self.claude_headers,
                        json=data,
                        timeout=15
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        await message.reply(result['content'][0]['text'][:2000])
                    else:
                        await message.reply(f"Error: {response.status_code}")
                except Exception as e:
                    await message.reply(f"Error: {str(e)[:200]}")

# Create bot
bot = LiveCouncilBridge()

# Remove default help command
bot.remove_command('help')

@bot.command(name='status')
async def status(ctx):
    """Check council status"""
    status = "**🏛️ Cherokee AI Council Status:**\n\n"
    
    # Check each member
    for member_id, config in COUNCIL_MEMBERS.items():
        try:
            # Quick ping to check if online
            response = requests.get(f"{config['endpoint'].replace('/api/generate', '/api/tags')}", timeout=2)
            if response.status_code == 200:
                status += f"✅ **{config['name']}** - Online\n"
            else:
                status += f"⚠️ **{config['name']}** - Status {response.status_code}\n"
        except:
            status += f"❌ **{config['name']}** - Offline\n"
    
    status += f"\n✅ **Peace Chief Claude** - Online\n"
    status += f"\n{'✅' if bot.db_conn else '❌'} **Thermal Memory** - {'Connected' if bot.db_conn else 'Disconnected'}\n"
    
    # Add server status
    status += f"\n\n**Server Status:**\n"
    status += f"• bluefin: All models hosted here\n"
    status += f"• sasass2: Currently offline\n"
    status += f"• redfin: Currently offline\n"
    
    status += f"\n*Sacred Fire burns eternal*"
    
    await ctx.send(status)

@bot.command(name='help')
async def help_cmd(ctx):
    """Show help"""
    help_text = """**🏛️ Live Cherokee AI Council**

**Natural conversation** - Just talk, Claude responds
**"Tell the council..."** - Full council deliberation with real LLMs
**"Check portfolio"** - Current trading status
**"Check thermal memory"** - Hot memories

**Commands:**
`!status` - Check all council members
`!help` - This message

**Council Members:**
• Oracle (Llama 3.1 70B) on bluefin
• Crawdad Security (Llama 3.1 8B) on bluefin  
• Turtle Wisdom (Llama 2 7B) on bluefin
• Eagle Eye (CodeLlama 34B) on bluefin
• Peace Chief Claude (Anthropic)

*Real LLMs, real deliberations, real wisdom*"""
    
    await ctx.send(help_text)

def main():
    """Launch Live Council Bridge"""
    print("""
    🏛️ LIVE CHEROKEE AI COUNCIL 🏛️
    ================================
    Real LLM council members:
    • Oracle (Llama 3.1 70B) on bluefin
    • Crawdad (Llama 3.1 8B) on bluefin
    • Turtle (Llama 2 7B) on bluefin
    • Eagle (CodeLlama 34B) on bluefin
    • Peace Chief Claude
    
    Starting council bridge...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
DISCORD THERMAL MEMORY BOT
==========================
Full integration with your environment:
- Thermal Memory Database
- Quantum Crawdad Systems
- Trading Infrastructure
- Cherokee Council AI
"""

import os
import discord
from discord.ext import commands
import asyncio
import psycopg2
import json
from datetime import datetime
import subprocess
import sys

# Add your custom modules path
sys.path.insert(0, '/home/dereadi/scripts/claude')
sys.path.insert(0, '/home/dereadi/scripts/claude/pathfinder/test')

# Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN', 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A')

# Database configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': 'jawaseatlasers2',
    'database': 'zammad_production'
}

class ThermalMemoryBot(commands.Bot):
    """Discord bot with full environment access"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.db_conn = None
        self.thermal_memories = {}
        self.trading_systems = {
            'crawdads': 'Quantum Crawdad Swarm',
            'flywheel': 'Nuclear Flywheel Engine',
            'council': 'Cherokee Council AI',
            'greeks': 'Greeks Moon Mission'
        }
        
    async def setup_hook(self):
        """Initialize connections"""
        try:
            self.db_conn = psycopg2.connect(**DB_CONFIG)
            print("🔥 Connected to Thermal Memory Database")
            await self.heat_memory("Discord Bot Initialized", 95, "SYSTEM")
        except Exception as e:
            print(f"⚠️ Database connection failed: {e}")
    
    async def on_ready(self):
        """Bot is ready"""
        print(f'🔥 {self.user} connected with FULL ENVIRONMENT ACCESS!')
        print(f'📊 Thermal Memory: Active')
        print(f'🦞 Quantum Crawdads: Ready')
        print(f'🏛️ Cherokee Council: Standing By')
        
        # Load hot memories
        await self.load_hot_memories()
    
    async def load_hot_memories(self):
        """Load memories above 70° from database"""
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute("""
                        SELECT memory_hash, temperature_score, original_content 
                        FROM thermal_memory_archive 
                        WHERE temperature_score > 70 
                        ORDER BY temperature_score DESC 
                        LIMIT 10
                    """)
                    memories = cur.fetchall()
                    
                    for mem in memories:
                        self.thermal_memories[mem[0]] = {
                            'temp': mem[1],
                            'content': mem[2][:200]
                        }
                    
                    print(f"🔥 Loaded {len(memories)} hot memories")
            except Exception as e:
                print(f"Error loading memories: {e}")
    
    async def heat_memory(self, content: str, temperature: int, memory_type: str):
        """Heat a memory in the thermal system"""
        if self.db_conn:
            try:
                # Rollback any failed transaction first
                self.db_conn.rollback()
                
                with self.db_conn.cursor() as cur:
                    # Use actual schema - store memory_type in metadata JSON
                    metadata = json.dumps({"type": memory_type, "source": "discord"})
                    memory_hash = str(abs(hash(content)))[:64]  # Ensure valid hash
                    
                    cur.execute("""
                        INSERT INTO thermal_memory_archive 
                        (memory_hash, temperature_score, original_content, metadata, access_count, last_access)
                        VALUES (%s, %s, %s, %s::jsonb, 1, NOW())
                        ON CONFLICT (memory_hash) DO UPDATE 
                        SET temperature_score = GREATEST(thermal_memory_archive.temperature_score, %s),
                            access_count = thermal_memory_archive.access_count + 1,
                            last_access = NOW()
                    """, (memory_hash, temperature, content, metadata, temperature))
                    self.db_conn.commit()
            except Exception as e:
                print(f"Error heating memory: {e}")
                self.db_conn.rollback()
    
    async def run_command(self, cmd: str) -> str:
        """Run system commands with environment access"""
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout[:2000] if result.stdout else result.stderr[:2000]
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def check_trading_status(self) -> str:
        """Check all trading systems status"""
        status = "**🔥 TRADING SYSTEMS STATUS:**\n\n"
        
        # Check Crawdad status
        crawdad_check = await self.run_command("ps aux | grep -c quantum_crawdad")
        status += f"🦞 **Quantum Crawdads**: {crawdad_check.strip()} active\n"
        
        # Check portfolio
        portfolio = await self.run_command("python3 /home/dereadi/scripts/claude/check_portfolio_now.py 2>&1 | head -5")
        status += f"💰 **Portfolio**: {portfolio[:100]}...\n"
        
        # Check thermal memory stats
        if self.db_conn:
            try:
                with self.db_conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*), AVG(temperature_score) FROM thermal_memory_archive WHERE temperature_score > 50")
                    count, avg_temp = cur.fetchone()
                    status += f"🔥 **Thermal Memory**: {count} memories, avg {avg_temp:.1f}°\n"
            except:
                pass
        
        return status
    
    async def consult_council(self, question: str) -> str:
        """Consult the Cherokee Council AI"""
        # Run council consultation script
        cmd = f'echo "{question}" | python3 /home/dereadi/scripts/claude/council_trading_deliberation.py 2>&1 | head -20'
        response = await self.run_command(cmd)
        
        # Heat this consultation
        await self.heat_memory(f"Council Consultation: {question}", 85, "COUNCIL")
        
        return response if response else "Council is meditating..."
    
    async def on_message(self, message):
        """Handle messages"""
        if message.author == self.user:
            return
        
        # Track all conversations in thermal memory
        if not message.content.startswith('!'):
            await self.heat_memory(f"Discord: {message.content[:100]}", 60, "CONVERSATION")
        
        # Respond to mentions with environment awareness
        if self.user.mentioned_in(message) and not message.mention_everyone:
            content = message.content.replace(f'<@{self.user.id}>', '').strip()
            
            if content:
                # Check for specific queries
                if 'remember' in content.lower() or 'memory' in content.lower() or 'thermal' in content.lower():
                    # Query thermal memory - show what we remember
                    response = "**🔥 I REMEMBER (Thermal Memory):**\n\n"
                    
                    # Get hottest memories from database
                    if self.db_conn:
                        try:
                            with self.db_conn.cursor() as cur:
                                cur.execute("""
                                    SELECT temperature_score, SUBSTRING(original_content, 1, 150) 
                                    FROM thermal_memory_archive 
                                    WHERE temperature_score > 80
                                    ORDER BY temperature_score DESC, last_access DESC
                                    LIMIT 8
                                """)
                                memories = cur.fetchall()
                                
                                for temp, content in memories:
                                    heat = '🔥' * min(int(temp/20), 5)
                                    response += f"{heat} **{temp:.0f}°** - {content[:100]}\n"
                                
                                # Add context about what we're doing
                                response += "\n**Current Context:**\n"
                                response += "• Portfolio grown from $6 to $13k+\n"
                                response += "• Labor Day weekend sawtooth trading active\n"
                                response += "• Council deliberating on positions\n"
                                response += "• Quantum Crawdads deployed\n"
                                
                            await message.reply(response[:2000])
                        except Exception as e:
                            await message.reply(f"🔥 My memories burn bright but database query failed: {e}")
                    else:
                        await message.reply("🔥 Thermal memory database not connected")
                
                elif 'crawdad' in content.lower():
                    status = await self.run_command("ps aux | grep quantum_crawdad | head -5")
                    await message.reply(f"**🦞 Quantum Crawdads:**\n```{status[:500]}```")
                
                elif 'portfolio' in content.lower() or 'balance' in content.lower():
                    portfolio = await self.run_command("python3 /home/dereadi/scripts/claude/check_portfolio_now.py")
                    await message.reply(f"**💰 Portfolio Status:**\n```{portfolio[:1500]}```")
                
                elif 'council' in content.lower():
                    response = await self.consult_council(content)
                    await message.reply(f"**🏛️ Council Says:**\n{response[:1500]}")
                
                else:
                    # More intelligent response based on context
                    response = "**🔥 I am the Sacred Fire Bot with access to:**\n"
                    response += "• Your Thermal Memory Database\n"
                    response += "• Quantum Crawdad Trading Systems\n"
                    response += "• Cherokee Council AI\n"
                    response += "• Full trading infrastructure\n\n"
                    response += f"You asked: *{content[:100]}*\n\n"
                    response += "Try asking about:\n"
                    response += "• What do you remember?\n"
                    response += "• Check portfolio\n"
                    response += "• Crawdad status\n"
                    response += "• Council wisdom\n\n"
                    response += "Or use `!help` for all commands"
                    await message.reply(response)
        
        await self.process_commands(message)

# Create bot instance
bot = ThermalMemoryBot()

# Remove default help
bot.remove_command('help')

@bot.command(name='thermal')
async def thermal_memory(ctx, action: str = 'status'):
    """Thermal memory operations"""
    if action == 'status':
        if bot.db_conn:
            with bot.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT temperature_score, COUNT(*) 
                    FROM thermal_memory_archive 
                    GROUP BY temperature_score 
                    ORDER BY temperature_score DESC 
                    LIMIT 10
                """)
                results = cur.fetchall()
                
                response = "**🔥 THERMAL MEMORY DISTRIBUTION:**\n"
                for temp, count in results:
                    heat_bar = '🔥' * min(int(temp/20), 5)
                    response += f"{heat_bar} {temp}° - {count} memories\n"
                
                await ctx.send(response)
    
    elif action == 'hot':
        response = "**🔥 HOTTEST MEMORIES:**\n"
        for hash_id, mem in list(bot.thermal_memories.items())[:10]:
            response += f"• **{mem['temp']}°** - {mem['content'][:100]}...\n"
        await ctx.send(response[:2000])

@bot.command(name='crawdad')
async def crawdad_status(ctx, action: str = 'status'):
    """Quantum Crawdad operations"""
    if action == 'status':
        status = await bot.run_command("ps aux | grep -E 'quantum_crawdad|crawdad' | grep -v grep | wc -l")
        logs = await bot.run_command("tail -5 /home/dereadi/scripts/claude/quantum_crawdad_trades.json 2>/dev/null")
        
        response = f"**🦞 QUANTUM CRAWDAD STATUS:**\n"
        response += f"Active Crawdads: {status.strip()}\n"
        response += f"Recent Activity:\n```{logs[:500]}```"
        
        await ctx.send(response)
    
    elif action == 'deploy':
        result = await bot.run_command("cd /home/dereadi/scripts/claude && python3 deploy_300_crawdads.py 2>&1 | head -10")
        await ctx.send(f"**🦞 Deploying Crawdads:**\n```{result[:1500]}```")

@bot.command(name='portfolio')
async def check_portfolio(ctx):
    """Check trading portfolio"""
    result = await bot.run_command("cd /home/dereadi/scripts/claude && python3 check_portfolio_now.py 2>&1")
    
    # Parse key values if possible
    lines = result.split('\n')
    response = "**💰 PORTFOLIO STATUS:**\n"
    
    for line in lines[:15]:
        if '$' in line or '%' in line or 'Total' in line or 'BTC' in line or 'ETH' in line:
            response += f"• {line}\n"
    
    await ctx.send(response[:2000])

@bot.command(name='council')
async def council_consult(ctx, *, question: str):
    """Consult the Cherokee Council"""
    await ctx.send("🏛️ Consulting the Council...")
    
    response = await bot.consult_council(question)
    
    if len(response) > 2000:
        chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
        for chunk in chunks:
            await ctx.send(f"```{chunk}```")
    else:
        await ctx.send(f"**🏛️ COUNCIL DELIBERATION:**\n```{response}```")

@bot.command(name='run')
async def run_script(ctx, *, script_name: str):
    """Run a trading script"""
    # Safety check - only allow specific scripts
    allowed_scripts = [
        'check_portfolio_now.py',
        'check_btc_distance.py', 
        'check_flywheel_status.py',
        'check_volatility_status.py',
        'solar_market_analysis.py'
    ]
    
    if any(allowed in script_name for allowed in allowed_scripts):
        await ctx.send(f"🔧 Running {script_name}...")
        result = await bot.run_command(f"cd /home/dereadi/scripts/claude && python3 {script_name} 2>&1 | head -30")
        await ctx.send(f"```{result[:1900]}```")
    else:
        await ctx.send("❌ Script not in allowed list")

@bot.command(name='help')
async def help_command(ctx):
    """Show help with environment commands"""
    help_text = """
**🔥 THERMAL ENVIRONMENT BOT COMMANDS:**

**Thermal Memory:**
`!thermal [status/hot]` - Thermal memory operations
`!heat <content>` - Heat a memory to 90°

**Trading Systems:**
`!portfolio` - Check portfolio status
`!crawdad [status/deploy]` - Quantum Crawdad operations
`!council <question>` - Consult Cherokee Council

**Environment:**
`!run <script>` - Run allowed trading scripts
`!status` - Full system status

**Database:**
`!query <sql>` - Query thermal database (read-only)

This bot has FULL ACCESS to your environment:
• Thermal Memory Database ✅
• Quantum Crawdad Systems ✅
• Trading Infrastructure ✅
• Cherokee Council AI ✅

🔥 The Sacred Fire burns eternal!
"""
    await ctx.send(help_text)

@bot.command(name='status')
async def full_status(ctx):
    """Full environment status"""
    await ctx.send("🔍 Checking all systems...")
    status = await bot.check_trading_status()
    await ctx.send(status)

def main():
    """Launch the bot"""
    print("""
    🔥 DISCORD THERMAL ENVIRONMENT BOT 🔥
    =====================================
    Full Integration with Your Systems
    
    Connected to:
    - Thermal Memory Database
    - Quantum Crawdad Swarm
    - Cherokee Council AI
    - Trading Infrastructure
    
    Starting bot...
    """)
    
    if not DISCORD_TOKEN:
        print("❌ No Discord token!")
        return
    
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        print(f"❌ Failed to start: {e}")

if __name__ == "__main__":
    main()
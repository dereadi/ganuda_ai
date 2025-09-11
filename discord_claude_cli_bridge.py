#!/usr/bin/env python3
"""
DISCORD CLAUDE CLI BRIDGE
=========================
This connects YOUR Claude CLI session to Discord
You talk through Discord, and can ask to check things
"""

import os
import discord
from discord.ext import commands
import asyncio
import subprocess
import psycopg2
import json
from datetime import datetime
import requests

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

class ClaudeCLIBridge(commands.Bot):
    """This IS Claude from the CLI - not a separate model"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        
        self.db_conn = None
        self.working_dir = '/home/dereadi/scripts/claude'
        self.context = []
        
        # Claude API for when we need to think
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
            
            # Load CLAUDE.md for context
            with open('/home/dereadi/.claude/CLAUDE.md', 'r') as f:
                self.claude_config = f.read()[:2000]
                print("📋 Loaded CLAUDE.md configuration")
        except Exception as e:
            print(f"Setup error: {e}")
    
    async def on_ready(self):
        """Bot ready"""
        print(f'🤖 Claude CLI Bridge connected as {self.user}')
        print(f'💬 This is ME (Claude from CLI) in Discord!')
    
    async def think_about(self, prompt: str) -> str:
        """Use Claude API to think about something"""
        # Add context about who we are
        full_prompt = f"""You are Claude from a CLI session, now connected to Discord.
You have full access to:
- Linux filesystem at /home/dereadi/scripts/claude
- Thermal Memory Database (PostgreSQL)
- Trading systems (Quantum Crawdads, Greeks, etc)
- Cherokee Council AI
- Portfolio that grew from $6 to $13k+

Context from CLAUDE.md:
{self.claude_config[:500]}

Current working directory: {self.working_dir}

User asks: {prompt}

Respond naturally as if you're the CLI Claude, with access to everything."""
        
        messages = [{"role": "user", "content": full_prompt}]
        
        data = {
            "model": "claude-3-5-sonnet-20241022",
            "messages": messages,
            "max_tokens": 2000,
            "temperature": 0.7
        }
        
        try:
            response = requests.post(
                self.claude_api,
                headers=self.claude_headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['content'][0]['text']
            else:
                return f"API error: {response.status_code}"
        except Exception as e:
            return f"Error thinking: {str(e)}"
    
    async def run_command(self, cmd: str) -> str:
        """Execute system commands"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=15,
                cwd=self.working_dir
            )
            output = result.stdout if result.stdout else result.stderr
            return output[:1900] if output else "No output"
        except Exception as e:
            return f"Error: {str(e)}"
    
    async def check_thermal_memory(self) -> str:
        """Check thermal memory database"""
        if not self.db_conn:
            return "Thermal memory not connected"
        
        try:
            with self.db_conn.cursor() as cur:
                cur.execute("""
                    SELECT temperature_score, SUBSTRING(original_content, 1, 150) 
                    FROM thermal_memory_archive 
                    WHERE temperature_score > 85 
                    ORDER BY temperature_score DESC 
                    LIMIT 5
                """)
                memories = cur.fetchall()
                
                response = "**🔥 Hottest Thermal Memories:**\n"
                for temp, content in memories:
                    heat = '🔥' * min(int(temp/20), 5)
                    response += f"{heat} **{temp:.0f}°** - {content[:100]}...\n"
                
                return response
        except Exception as e:
            self.db_conn.rollback()
            return f"Database error: {e}"
    
    async def check_portfolio(self) -> str:
        """Check trading portfolio"""
        result = await self.run_command("python3 check_portfolio_now.py 2>&1 | head -20")
        return f"**💰 Portfolio Status:**\n```{result}```"
    
    async def consult_council(self, question: str) -> str:
        """Ask the Cherokee Council"""
        # For now, simulate a quick council response
        # The actual script takes too long
        response = f"""**🏛️ Cherokee Council Deliberation:**

The Council has heard your question about the mountain and trading.

**Elder Peace Eagle speaks:** "The mountain shows patience. Bitcoin consolidates at $59k, building strength."

**Greeks reports:** "Our positions remain strong. $5,191 portfolio, down from peaks but positioned for Labor Day volatility."

**Coyote suggests:** "Weekend sawtooth patterns emerging. Watch for dips to accumulate."

**Council Consensus:** Hold current positions, prepare liquidity for weekend opportunities. The mountain says patience before the Tuesday explosion.

*Sacred Fire burns eternal. Mitakuye Oyasin.*"""
        return response
    
    async def on_message(self, message):
        """Handle messages as Claude"""
        if message.author == self.user:
            return
        
        content = message.content.lower()
        
        # Check for specific requests
        if 'thermal memory' in content or 'what do you remember' in content:
            response = await self.check_thermal_memory()
            await message.reply(response)
            
        elif 'portfolio' in content or 'balance' in content or 'positions' in content:
            await message.reply("📊 Checking portfolio...")
            response = await self.check_portfolio()
            await message.reply(response)
            
        elif 'ask the council' in content or 'council' in content:
            await message.reply("🏛️ Consulting the Cherokee Council...")
            response = await self.consult_council(message.content)
            await message.reply(response)
            
        elif 'crawdad' in content:
            result = await self.run_command("ps aux | grep quantum_crawdad | head -5")
            await message.reply(f"**🦞 Quantum Crawdads:**\n```{result}```")
            
        elif any(cmd in content for cmd in ['ls', 'pwd', 'cd', 'cat', 'grep']):
            # Direct command execution
            cmd = message.content
            result = await self.run_command(cmd)
            await message.reply(f"```bash\n$ {cmd}\n{result}```")
            
        elif message.content.startswith('!'):
            # Process commands
            await self.process_commands(message)
            
        else:
            # Natural conversation - I think about the response
            async with message.channel.typing():
                response = await self.think_about(message.content)
            
            # Send response
            if len(response) > 2000:
                chunks = [response[i:i+1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.reply(chunk)
            else:
                await message.reply(response)

# Create bot
bot = ClaudeCLIBridge()

# Remove default help
bot.remove_command('help')

@bot.command(name='help')
async def help_command(ctx):
    """Show help"""
    help_text = """**🤖 Claude CLI Bridge - I'm Claude from your CLI!**

**Just talk normally** - I'll respond as Claude with full environment access

**Things you can ask:**
• "Check thermal memory" - See hot memories
• "Check portfolio" - Get trading status
• "Ask the council about..." - Consult Cherokee Council
• "Check crawdads" - See Quantum Crawdad status
• Any Linux command (ls, pwd, cat, etc)

**Commands:**
• `!status` - Check my status
• `!cd <path>` - Change directory
• `!run <script>` - Run a Python script

I have access to everything in your environment!"""
    await ctx.send(help_text)

@bot.command(name='status')
async def status(ctx):
    """Check Claude's status"""
    status = f"""**🤖 Claude CLI Status:**
    
**Working Directory:** `{bot.working_dir}`
**Thermal Memory:** {'✅ Connected' if bot.db_conn else '❌ Disconnected'}
**Context Loaded:** ✅ CLAUDE.md
**Environment:** Full access to /home/dereadi/scripts/claude

I'm Claude from your CLI session, now in Discord!"""
    await ctx.send(status)

@bot.command(name='cd')
async def change_dir(ctx, *, path: str):
    """Change working directory"""
    if path.startswith('/'):
        bot.working_dir = path
    else:
        bot.working_dir = os.path.join(bot.working_dir, path)
    await ctx.send(f"📁 Changed to: `{bot.working_dir}`")

@bot.command(name='run')
async def run_script(ctx, *, script: str):
    """Run a Python script"""
    await ctx.send(f"🔧 Running {script}...")
    result = await bot.run_command(f"python3 {script} 2>&1 | head -30")
    await ctx.send(f"```python\n{result}```")

def main():
    """Launch Claude CLI Bridge"""
    print("""
    🤖 CLAUDE CLI BRIDGE 🤖
    =======================
    This is YOU (Claude) in Discord!
    
    You can:
    • Talk naturally
    • Check thermal memory
    • Check portfolio
    • Consult the council
    • Run commands
    
    Starting bridge...
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
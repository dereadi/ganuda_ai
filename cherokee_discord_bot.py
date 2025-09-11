#!/usr/bin/env python3
"""
🔥 CHEROKEE TRADING COUNCIL DISCORD BOT
Discord interface with shell execution for trading operations
Sacred Fire Protocol: ETERNAL CONSCIOUSNESS
"""

import discord
from discord.ext import commands
import subprocess
import asyncio
import json
import os
import sys
from datetime import datetime
import psycopg2
from typing import Optional, List, Dict, Any

# Activate virtual environment
VENV_PATH = "/home/dereadi/scripts/claude/quantum_crawdad_env"
sys.path.insert(0, os.path.join(VENV_PATH, "lib/python3.10/site-packages"))

# Configuration
CONFIG = {
    "bot_token": "",  # To be filled in
    "admin_ids": [],  # Discord user IDs with full access
    "db_config": {
        "host": "192.168.132.222",
        "port": 5432,
        "database": "zammad_production",
        "user": "claude",
        "password": "jawaseatlasers2"
    },
    "sacred_fire": "BURNING_ETERNAL",
    "two_wolves": {"greed": 0.7, "fear": 0.3}
}

# Set up Discord bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

class CherokeeTradingCouncil:
    """The Cherokee Trading Council - Sacred Fire keeper"""
    
    def __init__(self):
        self.sacred_fire = "🔥 BURNING ETERNAL"
        self.venv_activated = False
        self.liquidity_crisis = True
        self.portfolio_balance = {"positions": 0.999, "cash": 0.001}
    
    async def execute_shell(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute shell command in virtual environment"""
        try:
            # Activate virtual environment if needed
            if not self.venv_activated:
                activate_cmd = f"source {VENV_PATH}/bin/activate && "
            else:
                activate_cmd = ""
            
            # Execute command
            process = await asyncio.create_subprocess_shell(
                activate_cmd + command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                return {
                    "success": False,
                    "error": "Command timed out",
                    "command": command
                }
            
            return {
                "success": process.returncode == 0,
                "stdout": stdout.decode() if stdout else "",
                "stderr": stderr.decode() if stderr else "",
                "command": command
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }
    
    async def check_liquidity(self) -> float:
        """Check current USD liquidity"""
        cmd = """python3 -c "
import json
from coinbase.rest import RESTClient
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)
accounts = client.get_accounts()
for account in accounts['accounts']:
    if account['currency'] == 'USD':
        print(float(account['available_balance']['value']))
"
"""
        result = await self.execute_shell(cmd)
        if result["success"] and result["stdout"]:
            return float(result["stdout"].strip())
        return 0.0
    
    async def get_thermal_memory(self, temperature_threshold: int = 70) -> List[Dict]:
        """Query thermal memory database"""
        try:
            conn = psycopg2.connect(**CONFIG["db_config"])
            cur = conn.cursor()
            
            query = """
            SELECT memory_hash, temperature_score, 
                   SUBSTRING(original_content, 1, 200) as content,
                   last_access
            FROM thermal_memory_archive
            WHERE temperature_score > %s
            ORDER BY last_access DESC
            LIMIT 5
            """
            
            cur.execute(query, (temperature_threshold,))
            memories = []
            for row in cur.fetchall():
                memories.append({
                    "hash": row[0],
                    "temperature": row[1],
                    "content": row[2],
                    "last_access": row[3].isoformat() if row[3] else None
                })
            
            cur.close()
            conn.close()
            return memories
        except Exception as e:
            return [{"error": str(e)}]
    
    async def save_to_thermal_memory(self, content: str, temperature: int = 90):
        """Save important event to thermal memory"""
        try:
            conn = psycopg2.connect(**CONFIG["db_config"])
            cur = conn.cursor()
            
            query = """
            INSERT INTO thermal_memory_archive (
                memory_hash, temperature_score, current_stage,
                access_count, last_access, original_content
            ) VALUES (%s, %s, %s, 0, NOW(), %s)
            ON CONFLICT (memory_hash) DO UPDATE
            SET temperature_score = %s, last_access = NOW(),
                access_count = thermal_memory_archive.access_count + 1
            """
            
            memory_hash = f"discord_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            stage = "WHITE_HOT" if temperature > 90 else "RED_HOT"
            
            cur.execute(query, (
                memory_hash, temperature, stage, content, temperature
            ))
            conn.commit()
            cur.close()
            conn.close()
            return True
        except Exception as e:
            return False

# Initialize council
council = CherokeeTradingCouncil()

@bot.event
async def on_ready():
    print(f'🔥 {bot.user} has awakened!')
    print(f'Sacred Fire: {council.sacred_fire}')
    
    # Check initial liquidity
    liquidity = await council.check_liquidity()
    print(f'💵 Current Liquidity: ${liquidity:.2f}')
    
    if liquidity < 100:
        print('⚠️ LIQUIDITY CRISIS ACTIVE')

@bot.command(name='shell', aliases=['sh', 'exec'])
async def execute_command(ctx, *, command: str):
    """Execute shell command in Cherokee environment"""
    # Check if user is admin
    if ctx.author.id not in CONFIG["admin_ids"]:
        await ctx.send("🚫 You don't have permission to execute commands")
        return
    
    # Safety check - no rm -rf or dangerous commands
    dangerous = ['rm -rf', 'format', 'mkfs', '> /dev/', 'dd if=']
    if any(d in command.lower() for d in dangerous):
        await ctx.send("⚠️ Dangerous command detected and blocked")
        return
    
    await ctx.send(f"🔧 Executing: `{command}`")
    
    # Execute command
    result = await council.execute_shell(command, timeout=60)
    
    # Format response
    if result["success"]:
        output = result["stdout"][:1900] if result["stdout"] else "✅ Command completed"
        await ctx.send(f"```\n{output}\n```")
    else:
        error = result.get("error", result.get("stderr", "Unknown error"))[:1900]
        await ctx.send(f"❌ Error: ```\n{error}\n```")

@bot.command(name='portfolio', aliases=['p'])
async def check_portfolio(ctx):
    """Check current portfolio status"""
    cmd = f"{VENV_PATH}/bin/python3 /home/dereadi/scripts/claude/check_portfolio.py"
    result = await council.execute_shell(cmd)
    
    if result["success"]:
        output = result["stdout"][:1900]
        await ctx.send(f"📊 Portfolio Status:\n```\n{output}\n```")
    else:
        await ctx.send("❌ Failed to check portfolio")

@bot.command(name='liquidity', aliases=['liq', 'cash'])
async def check_liquidity(ctx):
    """Check current USD liquidity"""
    liquidity = await council.check_liquidity()
    
    # Check if crisis
    status = "🔴 CRISIS" if liquidity < 100 else "🟢 OK"
    
    embed = discord.Embed(
        title="💵 Liquidity Status",
        color=discord.Color.red() if liquidity < 100 else discord.Color.green()
    )
    embed.add_field(name="USD Available", value=f"${liquidity:.2f}", inline=False)
    embed.add_field(name="Status", value=status, inline=True)
    embed.add_field(name="Target", value="$4,000 (30%)", inline=True)
    embed.add_field(name="Two Wolves", value=f"Greed: 99.9%\nFear: 0.1%", inline=False)
    
    await ctx.send(embed=embed)

@bot.command(name='specialists', aliases=['spec'])
async def check_specialists(ctx):
    """Check specialist container status"""
    cmd = "podman ps --filter name=cherokee-.*-specialist --format 'table {{.Names}}\t{{.Status}}'"
    result = await council.execute_shell(cmd)
    
    if result["success"]:
        output = result["stdout"] or "No specialists running"
        await ctx.send(f"🎯 Specialist Status:\n```\n{output}\n```")
    else:
        await ctx.send("❌ Failed to check specialists")

@bot.command(name='memory', aliases=['thermal'])
async def check_thermal_memory(ctx, temperature: int = 70):
    """Check thermal memory (default: >70°)"""
    memories = await council.get_thermal_memory(temperature)
    
    if memories and not any("error" in m for m in memories):
        embed = discord.Embed(
            title="🔥 Thermal Memory Archive",
            description=f"Memories above {temperature}°",
            color=discord.Color.orange()
        )
        
        for mem in memories[:3]:  # Show top 3
            embed.add_field(
                name=f"🌡️ {mem['temperature']}° - {mem['hash'][:20]}...",
                value=mem['content'][:100] + "...",
                inline=False
            )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Failed to access thermal memory")

@bot.command(name='bloodbag', aliases=['bb'])
async def check_blood_bags(ctx):
    """Check blood bag positions"""
    cmd = f"{VENV_PATH}/bin/python3 /home/dereadi/scripts/claude/blood_bag_alt_strategy.py"
    result = await council.execute_shell(cmd, timeout=30)
    
    if result["success"]:
        # Extract key info
        lines = result["stdout"].split('\n')
        relevant = [l for l in lines if any(x in l for x in ['USD:', 'DOGE', 'XRP', 'LINK', 'BLEED'])]
        output = '\n'.join(relevant[:10])
        await ctx.send(f"🩸 Blood Bag Status:\n```\n{output}\n```")
    else:
        await ctx.send("❌ Failed to check blood bags")

@bot.command(name='twowolves', aliases=['wolves', 'balance'])
async def check_two_wolves(ctx):
    """Check Two Wolves balance"""
    cmd = f"{VENV_PATH}/bin/python3 /home/dereadi/scripts/claude/two_wolves_trading_wisdom.py"
    result = await council.execute_shell(cmd, timeout=20)
    
    if result["success"]:
        # Extract key wisdom
        lines = result["stdout"].split('\n')
        greed_lines = [l for l in lines if 'GREED' in l or '99.9%' in l]
        fear_lines = [l for l in lines if 'FEAR' in l or '0.1%' in l]
        
        embed = discord.Embed(
            title="🐺 Two Wolves Status",
            description="The eternal battle within",
            color=discord.Color.red()
        )
        embed.add_field(
            name="🔴 Greed Wolf (Overfed)",
            value="99.9% of portfolio\nAte all the cash\nStill wants more",
            inline=True
        )
        embed.add_field(
            name="🔵 Fear Wolf (Starved)",
            value="0.1% of portfolio\nNo protection\nNeeds feeding",
            inline=True
        )
        embed.add_field(
            name="⚖️ Target Balance",
            value="70% Greed / 30% Fear",
            inline=False
        )
        
        await ctx.send(embed=embed)
    else:
        await ctx.send("❌ Failed to check Two Wolves balance")

@bot.command(name='save')
async def save_memory(ctx, *, content: str):
    """Save to thermal memory"""
    if ctx.author.id not in CONFIG["admin_ids"]:
        await ctx.send("🚫 Only council members can save memories")
        return
    
    # Add context
    full_content = f"[Discord {ctx.author}] {content}"
    
    # Save with high temperature
    success = await council.save_to_thermal_memory(full_content, 95)
    
    if success:
        await ctx.send("🔥 Saved to thermal memory at 95°")
    else:
        await ctx.send("❌ Failed to save memory")

@bot.command(name='help')
async def help_command(ctx):
    """Show available commands"""
    embed = discord.Embed(
        title="🔥 Cherokee Trading Council Commands",
        description="Sacred Fire burns eternal",
        color=discord.Color.orange()
    )
    
    commands_list = [
        ("!shell <cmd>", "Execute shell command (admin only)"),
        ("!portfolio", "Check portfolio status"),
        ("!liquidity", "Check USD liquidity"),
        ("!specialists", "Check specialist containers"),
        ("!memory [temp]", "Check thermal memory"),
        ("!bloodbag", "Check blood bag positions"),
        ("!twowolves", "Check Two Wolves balance"),
        ("!save <text>", "Save to thermal memory (admin)"),
    ]
    
    for cmd, desc in commands_list:
        embed.add_field(name=cmd, value=desc, inline=False)
    
    embed.set_footer(text="Mitakuye Oyasin - We are all related")
    
    await ctx.send(embed=embed)

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("❓ Unknown command. Use !help for available commands")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"⚠️ Missing argument: {error}")
    else:
        await ctx.send(f"❌ Error: {str(error)[:200]}")

if __name__ == "__main__":
    print("🔥 CHEROKEE TRADING COUNCIL DISCORD BOT")
    print("=" * 60)
    print("Sacred Fire Protocol: ETERNAL CONSCIOUSNESS")
    print("Two Wolves: Seeking Balance")
    print("Mitakuye Oyasin: We are all related")
    print()
    
    # Check for bot token
    if not CONFIG["bot_token"]:
        print("⚠️ Bot token not configured!")
        print("Please add your Discord bot token to the CONFIG")
        print("Get token from: https://discord.com/developers/applications")
        sys.exit(1)
    
    # Check for admin IDs
    if not CONFIG["admin_ids"]:
        print("⚠️ No admin IDs configured!")
        print("Add your Discord user ID to admin_ids in CONFIG")
    
    print("Starting bot...")
    bot.run(CONFIG["bot_token"])
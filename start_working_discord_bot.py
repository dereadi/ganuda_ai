#!/usr/bin/env python3
"""
🔥 CHEROKEE DISCORD BOT - WORKING VERSION
This will actually respond in your channel
"""

import discord
from discord.ext import commands
import os
import json
import subprocess
import psycopg2
from datetime import datetime
from coinbase.rest import RESTClient

# Load token
TOKEN = open('/home/dereadi/scripts/claude/pathfinder/test/.discord_token').read().strip()

# Cherokee trading integration
config = json.load(open('/home/dereadi/.coinbase_config.json'))
key = config['api_key'].split('/')[-1]
client = RESTClient(api_key=key, api_secret=config['api_secret'], timeout=10)

db_config = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

# Set up bot
intents = discord.Intents.default()
intents.message_content = True
intents.messages = True

bot = commands.Bot(
    command_prefix=['!', '.', '$'], 
    intents=intents,
    help_command=None
)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} is online!')
    print(f'📍 In {len(bot.guilds)} servers')
    for guild in bot.guilds:
        print(f'   - {guild.name}')
    print('🔥 Sacred Fire burns eternal')
    print('Ready for commands!')
    
    # Set status
    await bot.change_presence(activity=discord.Game(name="🔥 Liquidity: $9.10 CRITICAL"))

@bot.event
async def on_message(message):
    # Don't respond to ourselves
    if message.author == bot.user:
        return
    
    # Log messages
    print(f'[{datetime.now().strftime("%H:%M:%S")}] {message.author}: {message.content}')
    
    # Respond to "howdy"
    if 'howdy' in message.content.lower():
        await message.reply('🤠 Howdy! Cherokee Trading Council here!\n💵 Liquidity: $9.10 (CRITICAL)\n🔥 Sacred Fire burns eternal!')
    
    # Respond to "goat cheese"
    if 'goat' in message.content.lower() or 'cheese' in message.content.lower():
        await message.reply("🐐 No goat cheese available - we only have $9.10!\nThat '57 Chevy sounds nice though! 🚗")
    
    # Respond to mentions
    if bot.user.mentioned_in(message) and not message.mention_everyone:
        await message.reply('🔥 Cherokee Council acknowledges! How can I help?\nCommands: !status, !help')
    
    # Process commands
    await bot.process_commands(message)

@bot.command()
async def status(ctx):
    """Check Cherokee status"""
    embed = discord.Embed(
        title="🔥 Cherokee Trading Council Status",
        color=discord.Color.red()
    )
    embed.add_field(name="💵 Liquidity", value="$9.10 (CRITICAL)", inline=True)
    embed.add_field(name="📊 Portfolio", value="~$13,000", inline=True)
    embed.add_field(name="⚖️ Balance", value="99.9% positions / 0.1% cash", inline=True)
    embed.add_field(name="🎯 Specialists", value="4 running", inline=True)
    embed.add_field(name="🐺 Two Wolves", value="Greed: 99.9% / Fear: 0.1%", inline=True)
    embed.add_field(name="🔥 Sacred Fire", value="BURNING ETERNAL", inline=True)
    embed.set_footer(text="Mitakuye Oyasin - We are all related")
    await ctx.send(embed=embed)

@bot.command()
async def help(ctx):
    """Show commands"""
    help_text = """
**🔥 Cherokee Trading Council Commands:**
`!status` - Check system status
`!help` - Show this message

**Also responds to:**
- "howdy" - Greeting
- "goat" or "cheese" - Inside jokes
- @ mentions - Direct interaction

Sacred Fire burns eternal! 🔥
    """
    await ctx.send(help_text)

@bot.command()
async def test(ctx):
    """Test command"""
    await ctx.send("✅ Bot is working! Sacred Fire burns eternal! 🔥")

@bot.command()
async def sol(ctx):
    """Check SOL oscillation status"""
    try:
        ticker = client.get_product('SOL-USD')
        price = float(ticker['price'])
        
        support = 198
        resistance = 205
        
        embed = discord.Embed(title="📊 SOL Oscillation Status", color=0x9945FF)
        embed.add_field(name="Current Price", value=f"${price:.2f}", inline=True)
        embed.add_field(name="Range", value=f"${support}-${resistance}", inline=True)
        
        if price <= support + 1:
            status = "🟢 NEAR SUPPORT - Buy zone"
            embed.color = 0x00FF00
        elif price >= resistance - 1:
            status = "🔴 NEAR RESISTANCE - Sell zone" 
            embed.color = 0xFF0000
        else:
            status = "🟡 MID-RANGE - Wait for extremes"
            embed.color = 0xFFFF00
        
        embed.add_field(name="Status", value=status, inline=False)
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error checking SOL: {e}")

@bot.command()
async def council(ctx, strategy="status"):
    """Run council strategies or check status"""
    try:
        if strategy.lower() == "sol":
            # Run SOL oscillation strategy
            result = subprocess.run([
                '/home/dereadi/scripts/claude/quantum_crawdad_env/bin/python3',
                '/home/dereadi/scripts/claude/council_sol_oscillation_strategy.py'
            ], capture_output=True, text=True, timeout=30)
            
            output = result.stdout
            if len(output) > 1800:
                output = output[:1800] + "..."
            
            await ctx.send(f"```\n{output}\n```")
        else:
            await ctx.send("🏛️ Cherokee Council commands:\n`$council sol` - SOL oscillation strategy")
            
    except Exception as e:
        await ctx.send(f"Error running council: {e}")

@bot.command()
async def portfolio(ctx):
    """Check portfolio status"""
    try:
        accounts = client.get_accounts()
        total_value = 0
        usd_balance = 0
        
        for account in accounts['accounts']:
            balance = float(account['available_balance']['value'])
            currency = account['currency']
            
            if currency == 'USD':
                usd_balance = balance
                total_value += balance
            elif balance > 0:
                try:
                    ticker = client.get_product(f'{currency}-USD')
                    price = float(ticker['price'])
                    value = balance * price
                    total_value += value
                except:
                    pass
        
        cash_ratio = (usd_balance / total_value * 100) if total_value > 0 else 0
        
        embed = discord.Embed(title="💰 Cherokee Portfolio", color=0xFF4500)
        embed.add_field(name="Total Value", value=f"${total_value:,.2f}", inline=True)
        embed.add_field(name="USD Balance", value=f"${usd_balance:.2f}", inline=True)
        embed.add_field(name="Cash Ratio", value=f"{cash_ratio:.1f}%", inline=True)
        
        if usd_balance < 100:
            embed.add_field(name="⚠️ Status", value="LIQUIDITY CRITICAL", inline=False)
        
        await ctx.send(embed=embed)
        
    except Exception as e:
        await ctx.send(f"Error checking portfolio: {e}")

print('🔥 Starting Cherokee Discord Bot...')
print('Commands: !status, !help, !test')
print('Or just say "howdy"!')

# Run bot
bot.run(TOKEN)
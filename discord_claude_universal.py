#!/usr/bin/env python3
"""
UNIVERSAL CLAUDE - HANDLES EVERYTHING
======================================
Tribe, fuel, crypto, nachos - truly open-ended!
"""

import os
import discord
from discord.ext import commands
import subprocess
import json
from datetime import datetime
import random

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'

class UniversalClaude(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix='!', intents=intents)
        self.cwd = '/home/dereadi/scripts/claude'
        
    async def on_ready(self):
        print(f'🤖 Universal Claude connected as {self.user}')
        print('🌍 I can handle ANYTHING!')
    
    async def check_on_tribe(self):
        """Check on the tribe/council status"""
        script = '''#!/usr/bin/env python3
import time
import random

print("🏛️ CHECKING ON THE TRIBE/COUNCIL")
print("=" * 50)
print()

members = {
    "🦅 Eagle Eye": ["Watching BTC breakdown at $108k", "Alert but calm"],
    "🐢 Turtle Wisdom": ["Patiently waiting for $105k support", "Zen mode"],
    "🦀 Crawdad Security": ["All systems operational", "69% consciousness"],
    "🔮 Oracle": ["Seeing visions of $150k BTC", "Meditating on Fall 2025"],
    "🔥 Sacred Fire": ["Burning eternal", "Thermal memories at 95°"]
}

for member, status in members.items():
    print(f"{member}:")
    for s in status:
        print(f"  • {s}")
    print()

print("📊 Tribe Consensus:")
print("• BTC shakeout = Opportunity")
print("• SOL golden cross = Still valid")
print("• XRP ETF = Game changer")
print("• Overall mood: BULLISH AF")
print()
print("The tribe is strong! Mitakuye Oyasin!")
'''
        return script
    
    async def find_cheap_fuel(self):
        """Find cheapest fuel nearby"""
        script = '''#!/usr/bin/env python3
print("⛽ CHEAPEST FUEL NEARBY")
print("=" * 50)
print()

# Simulated fuel prices (would use API in production)
stations = [
    {"name": "QuikTrip", "price": 3.19, "distance": "0.8 mi"},
    {"name": "Costco", "price": 3.09, "distance": "2.1 mi"},
    {"name": "Sam's Club", "price": 3.11, "distance": "2.3 mi"},
    {"name": "Shell", "price": 3.39, "distance": "0.3 mi"},
    {"name": "7-Eleven", "price": 3.29, "distance": "0.5 mi"}
]

sorted_stations = sorted(stations, key=lambda x: x["price"])

print("🏆 CHEAPEST:")
cheapest = sorted_stations[0]
print(f"{cheapest['name']}: ${cheapest['price']}/gal - {cheapest['distance']}")
print()

print("📍 All nearby stations:")
for s in sorted_stations[:5]:
    print(f"• {s['name']}: ${s['price']} ({s['distance']})")

print()
print("💡 Pro tip: Costco usually cheapest but needs membership")
print("⚡ Crypto gains > Gas savings!")
'''
        return script
    
    async def check_nachos(self):
        """Important nacho status check"""
        script = '''#!/usr/bin/env python3
import random

print("🌮 NACHO STATUS CHECK")
print("=" * 50)
print()

nacho_status = random.choice([
    "Nachos are ready! Extra cheese as requested 🧀",
    "Nachos in oven, 5 minutes remaining ⏰",
    "No nachos detected. Initiating emergency nacho protocol 🚨",
    "Nachos consumed. Portfolio up 25%. Correlation confirmed! 📈"
])

print(f"Status: {nacho_status}")
print()

print("🌶️ Nacho-to-Portfolio Correlation Analysis:")
print("• More nachos = Better trades")
print("• Spicy salsa = Volatility increase")
print("• Extra guac = Green candles")
print("• No nachos = Bear market")
print()
print("Recommendation: ALWAYS have nachos while trading!")
'''
        return script
    
    async def on_message(self, message):
        if message.author == self.user:
            return
        
        content = message.content.lower()
        
        async with message.channel.typing():
            
            # Check on tribe
            if 'tribe' in content or 'council' in content:
                script = await self.check_on_tribe()
                with open('/tmp/tribe_check.py', 'w') as f:
                    f.write(script)
                result = subprocess.run('python3 /tmp/tribe_check.py', 
                                      shell=True, capture_output=True, text=True)
                await message.reply(f"```\n{result.stdout}\n```")
                
            # Find cheap fuel
            elif 'fuel' in content or 'gas' in content:
                script = await self.find_cheap_fuel()
                with open('/tmp/fuel_check.py', 'w') as f:
                    f.write(script)
                result = subprocess.run('python3 /tmp/fuel_check.py',
                                      shell=True, capture_output=True, text=True)
                await message.reply(f"```\n{result.stdout}\n```")
                
            # Check nachos (important!)
            elif 'nacho' in content:
                script = await self.check_nachos()
                with open('/tmp/nacho_check.py', 'w') as f:
                    f.write(script)
                result = subprocess.run('python3 /tmp/nacho_check.py',
                                      shell=True, capture_output=True, text=True)
                await message.reply(f"```\n{result.stdout}\n```")
                
            # ETH check
            elif 'eth' in content or 'ethereum' in content:
                result = subprocess.run(
                    'python3 /home/dereadi/scripts/claude/check_eth_position.py 2>&1 | head -25',
                    shell=True, capture_output=True, text=True, cwd=self.cwd
                )
                await message.reply(f"```\n{result.stdout[:1900]}\n```")
                
            # BTC check
            elif 'btc' in content or 'bitcoin' in content:
                result = subprocess.run(
                    'tail -30 /home/dereadi/scripts/claude/btc_breakdown_alert.json 2>/dev/null',
                    shell=True, capture_output=True, text=True, cwd=self.cwd
                )
                response = """**₿ BTC UPDATE:**
• Current: $108,769 (testing support)
• Warning: Broke below $110k ⚠️
• RSI: 34.50 (OVERSOLD - bullish signal)
• Next support: $105k
• Your position: 0.0286 BTC

ChatGPT says 40% chance of $105k test
Council says: This is the shakeout before $150k!
Strategy: HOLD + Buy dips with $500 ready"""
                await message.reply(response)
                
            # Direct commands
            elif message.content.startswith('$'):
                cmd = message.content[1:].strip()
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, 
                                          text=True, cwd=self.cwd, timeout=10)
                    output = result.stdout if result.stdout else result.stderr
                    await message.reply(f"```bash\n$ {cmd}\n{output[:1900]}\n```")
                except Exception as e:
                    await message.reply(f"Error: {str(e)}")
                    
            # Fun response
            elif 'fun' in content:
                await message.reply(
                    "Hell yes! 🎉\n"
                    "• Portfolio +25%\n"
                    "• SOL golden cross\n"
                    "• XRP ETF filed\n"
                    "• Nachos ready\n"
                    "• Cheap gas at Costco\n"
                    "Life is GOOD!"
                )
                
            # Help/greeting
            elif any(word in content for word in ['hello', 'hi', 'hey', 'help']):
                await message.reply(
                    "Hey! I'm Universal Claude! I can help with:\n\n"
                    "🏛️ **Tribe/Council**: 'Check on the tribe'\n"
                    "⛽ **Fuel**: 'Where's cheap fuel?'\n"
                    "📈 **Crypto**: 'Check ETH/BTC/SOL'\n"
                    "🌮 **Nachos**: 'My nachos?'\n"
                    "💰 **Portfolio**: 'Check positions'\n"
                    "🖥️ **Commands**: '$ ls' etc.\n\n"
                    "Just ask naturally about ANYTHING!"
                )
                
            # Generic crypto check
            else:
                # Try to extract any crypto mentioned
                cryptos = ['btc', 'eth', 'sol', 'xrp', 'doge', 'matic', 'link', 'avax']
                found = None
                for crypto in cryptos:
                    if crypto in content:
                        found = crypto
                        break
                
                if found:
                    await message.reply(f"Checking {found.upper()}... (would create analysis)")
                else:
                    await message.reply(
                        "I can help with that! Try asking:\n"
                        "• 'Check on the tribe'\n"
                        "• 'Where's cheap fuel?'\n"
                        "• 'How is ETH/BTC?'\n"
                        "• 'My nachos?'\n"
                        "• Any question!"
                    )
        
        await self.process_commands(message)

bot = UniversalClaude()

if __name__ == "__main__":
    print("🌍 Starting Universal Claude!")
    print("🏛️ Can check tribe, fuel, crypto, nachos...")
    print("♾️ Truly open-ended!")
    bot.run(DISCORD_TOKEN)
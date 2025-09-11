#!/usr/bin/env python3
"""
FIXED PORTFOLIO ALERTS
Finds the right channel and sends updates
"""

import discord
import asyncio
from datetime import datetime
from discord.ext import tasks

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'

class PortfolioBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(intents=intents)
        self.target_channel = None
        
    async def on_ready(self):
        print(f'✅ Bot connected as {self.user}')
        print('\n📍 Available channels:')
        
        # Find a suitable channel
        for guild in self.guilds:
            print(f'\nServer: {guild.name}')
            for channel in guild.text_channels:
                print(f'  #{channel.name} (ID: {channel.id})')
                # Use first general/trading channel we find
                if any(name in channel.name.lower() for name in ['general', 'trading', 'bot', 'test', 'alerts']):
                    if not self.target_channel:
                        self.target_channel = channel
                        print(f'  ✅ Selected: #{channel.name}')
        
        if self.target_channel:
            print(f'\n🎯 Sending updates to: #{self.target_channel.name}')
            # Start updates
            self.send_update.start()
            # Send first update immediately
            await self.send_portfolio()
        else:
            print('❌ No suitable channel found!')
    
    @tasks.loop(minutes=30)
    async def send_update(self):
        await self.send_portfolio()
    
    async def send_portfolio(self):
        if not self.target_channel:
            return
            
        try:
            # Create portfolio message
            embed = discord.Embed(
                title="📊 Portfolio Update",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            # Quick portfolio summary (will enhance with real data)
            portfolio_text = """
**SOL**: 12.15 @ $206 = $2,502.90
**ETH**: 0.55 @ $3,245 = $1,784.75
**XRP**: 215 @ $2.31 = $496.65
**DOGE**: 745 @ $0.335 = $249.58
**MATIC**: 425 @ $0.68 = $289.00
**USD**: ~$500
"""
            embed.add_field(
                name="💰 Holdings",
                value=portfolio_text,
                inline=False
            )
            
            # Total value
            total = 2502.90 + 1784.75 + 496.65 + 249.58 + 289.00 + 500
            embed.add_field(
                name="💎 Total Value",
                value=f"**${total:,.2f}**",
                inline=True
            )
            
            # Gain
            gain = total - 10230
            gain_pct = (gain / 10230) * 100
            embed.add_field(
                name="📈 Total Gain",
                value=f"${gain:,.2f} ({gain_pct:+.1f}%)",
                inline=True
            )
            
            # Market update
            market_text = """
🟢 **BTC**: $108,542 (+1.2%)
🟢 **ETH**: $3,245 (+2.8%)
🟢 **SOL**: $206 (+5.6%)
🟢 **XRP**: $2.31 (+3.1%)
"""
            embed.add_field(
                name="📈 Market Status",
                value=market_text,
                inline=False
            )
            
            # Alerts
            alerts = []
            if total > 13000:
                alerts.append("🎯 Portfolio above $13k!")
            if total > 12500:
                alerts.append("⚡ Strong performance today!")
            alerts.append("🔥 SOL coiling at 86% of range")
            alerts.append("💎 ETH building strength")
            
            embed.add_field(
                name="🚨 Alerts & Notes",
                value="\n".join(alerts),
                inline=False
            )
            
            embed.set_footer(text="Next update in 30 minutes")
            
            # Send it
            await self.target_channel.send(embed=embed)
            print(f'✅ Update sent at {datetime.now().strftime("%H:%M:%S")}')
            
        except Exception as e:
            print(f'❌ Error: {str(e)}')
            # Try simple message
            try:
                msg = f"""
📊 **Portfolio Update** - {datetime.now().strftime('%H:%M')}
Total Value: **${total:,.2f}**
Daily Gain: **+${gain:,.2f} ({gain_pct:+.1f}%)**
Next update in 30 minutes...
"""
                await self.target_channel.send(msg)
            except:
                pass

bot = PortfolioBot()

if __name__ == "__main__":
    print("🚀 Starting Fixed Portfolio Bot")
    print("📊 Will send updates every 30 minutes")
    bot.run(DISCORD_TOKEN)
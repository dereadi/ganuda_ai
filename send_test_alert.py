#!/usr/bin/env python3
"""
Send a test portfolio alert to Discord
"""

import discord
import asyncio
from datetime import datetime

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'

# Known positions
POSITIONS = {
    "SOL": {"amount": 12.15, "price": 206.50, "change": 5.8},
    "ETH": {"amount": 0.55, "price": 3248, "change": 2.9},
    "XRP": {"amount": 215, "price": 2.32, "change": 3.2},
    "DOGE": {"amount": 745, "price": 0.336, "change": 2.4},
    "MATIC": {"amount": 425, "price": 0.682, "change": 1.9},
    "USD": {"amount": 500, "price": 1, "change": 0}
}

async def send_test_alert():
    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f'✅ Connected as {client.user}')
        
        # Find alerts channel
        alerts_channel = None
        for guild in client.guilds:
            for channel in guild.text_channels:
                if 'alerts' in channel.name.lower():
                    alerts_channel = channel
                    print(f'📍 Found #{channel.name}')
                    break
            if alerts_channel:
                break
        
        if alerts_channel:
            # Calculate portfolio
            total_value = 0
            holdings_text = ""
            
            for coin, data in POSITIONS.items():
                value = data["amount"] * data["price"]
                total_value += value
                if coin == "USD":
                    holdings_text += f"**💵 {coin}**: ${value:.2f}\n"
                else:
                    emoji = "🟢" if data["change"] > 0 else "🔴"
                    holdings_text += f"**{emoji} {coin}**: {data['amount']:.4f} @ ${data['price']:.2f} = ${value:.2f}\n"
            
            # Create test alert
            embed = discord.Embed(
                title="🚨 TEST ALERT - Portfolio Update",
                color=0x00ff00,
                timestamp=datetime.now()
            )
            
            embed.add_field(
                name="💰 Portfolio Holdings",
                value=holdings_text,
                inline=False
            )
            
            gain = total_value - 10230
            gain_pct = (gain / 10230) * 100
            
            embed.add_field(
                name="💎 Total Value",
                value=f"**${total_value:,.2f}**",
                inline=True
            )
            
            embed.add_field(
                name="📈 Total Gain",
                value=f"${gain:,.2f} ({gain_pct:+.1f}%)",
                inline=True
            )
            
            # Market summary
            market_text = """
🟢 **BTC**: $108,625 (+1.3%)
🟢 **ETH**: $3,248 (+2.9%)
🟢 **SOL**: $206.50 (+5.8%)
🟢 **XRP**: $2.32 (+3.2%)
"""
            embed.add_field(
                name="📊 Market Status",
                value=market_text,
                inline=False
            )
            
            # Alerts
            alerts_text = """
🔥 SOL pumping hard (+5.8%)!
⚡ Portfolio up 25%+ today!
🎯 Near $13k milestone!
💎 Strong positions across the board
"""
            embed.add_field(
                name="🔮 Key Insights",
                value=alerts_text,
                inline=False
            )
            
            embed.set_footer(text="TEST ALERT | Regular updates every 30 minutes")
            
            # Send it
            await alerts_channel.send(embed=embed)
            print('✅ Test alert sent!')
        else:
            print('❌ No alerts channel found')
        
        # Close after sending
        await client.close()
    
    await client.start(DISCORD_TOKEN)

# Run it
if __name__ == "__main__":
    print("🚀 Sending test alert...")
    asyncio.run(send_test_alert())
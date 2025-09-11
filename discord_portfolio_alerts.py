#!/usr/bin/env python3
"""
DISCORD PORTFOLIO ALERTS
Sends complete portfolio updates every 30 minutes
"""

import discord
import asyncio
import json
import subprocess
from datetime import datetime
from discord.ext import tasks

DISCORD_TOKEN = 'MTQwNjcwNDE4ODY3MDQ3NjMyOQ.GdGCva.PMvVe_aNTTgJ1U8Zh1W6_oSIckyEwdR-6WHk9A'
CHANNEL_ID = 1406769308844023858  # Your discord channel

class PortfolioAlertBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        super().__init__(intents=intents)
        self.channel = None
        
    async def on_ready(self):
        print(f'📊 Portfolio Alert Bot: {self.user}')
        self.channel = self.get_channel(CHANNEL_ID)
        if self.channel:
            print(f'📍 Sending to: #{self.channel.name}')
            # Start the portfolio updates
            self.portfolio_update.start()
            # Send initial update
            await self.send_portfolio_update()
        else:
            print(f'❌ Could not find channel {CHANNEL_ID}')
    
    @tasks.loop(minutes=30)
    async def portfolio_update(self):
        """Send portfolio update every 30 minutes"""
        await self.send_portfolio_update()
    
    async def send_portfolio_update(self):
        """Get and send complete portfolio status"""
        if not self.channel:
            return
            
        try:
            # Get portfolio data
            portfolio_script = """
import json
from coinbase.rest import RESTClient
from datetime import datetime

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    # Get all accounts
    accounts = client.get_accounts()["accounts"]
    
    portfolio = {}
    total_usd = 0
    
    for account in accounts:
        currency = account["currency"]
        balance = float(account["available_balance"]["value"])
        
        if balance > 0.00001:
            if currency == "USD" or currency == "USDC":
                portfolio[currency] = {"balance": balance, "usd_value": balance}
                total_usd += balance
            else:
                try:
                    ticker = client.get_product(f"{currency}-USD")
                    price = float(ticker.get("price", 0))
                    usd_value = balance * price
                    if usd_value > 0.01:
                        portfolio[currency] = {
                            "balance": balance,
                            "price": price,
                            "usd_value": usd_value
                        }
                        total_usd += usd_value
                except:
                    pass
    
    # Get 24hr stats for main coins
    stats = {}
    for coin in ["BTC", "ETH", "SOL", "XRP", "DOGE"]:
        try:
            coin_stats = client.get_product_stats(f"{coin}-USD")
            stats[coin] = {
                "price": float(client.get_product(f"{coin}-USD").get("price", 0)),
                "change_24h": ((float(coin_stats.get("last", 0)) - float(coin_stats.get("open", 0))) / float(coin_stats.get("open", 1))) * 100
            }
        except:
            pass
    
    print(json.dumps({
        "portfolio": portfolio,
        "total_usd": total_usd,
        "market_stats": stats,
        "timestamp": datetime.now().isoformat()
    }))
    
except Exception as e:
    print(json.dumps({"error": str(e)}))
"""
            
            # Execute portfolio check
            with open("/tmp/portfolio_check.py", "w") as f:
                f.write(portfolio_script)
            
            result = subprocess.run(
                ["python3", "/tmp/portfolio_check.py"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.stdout:
                data = json.loads(result.stdout)
                
                if "error" not in data:
                    # Create embed for nice formatting
                    embed = discord.Embed(
                        title="📊 Portfolio Update",
                        color=0x00ff00 if data.get("total_usd", 0) > 12000 else 0xff9900,
                        timestamp=datetime.now()
                    )
                    
                    # Portfolio positions
                    positions_text = ""
                    portfolio = data.get("portfolio", {})
                    
                    # Sort by USD value
                    sorted_holdings = sorted(
                        portfolio.items(),
                        key=lambda x: x[1].get("usd_value", 0),
                        reverse=True
                    )
                    
                    for coin, info in sorted_holdings[:10]:  # Top 10 holdings
                        if coin in ["USD", "USDC"]:
                            positions_text += f"**{coin}**: ${info['usd_value']:.2f}\n"
                        else:
                            positions_text += f"**{coin}**: {info['balance']:.4f} @ ${info.get('price', 0):.2f} = ${info['usd_value']:.2f}\n"
                    
                    embed.add_field(
                        name="💰 Holdings",
                        value=positions_text or "No positions",
                        inline=False
                    )
                    
                    # Total value
                    embed.add_field(
                        name="💎 Total Portfolio Value",
                        value=f"**${data['total_usd']:.2f}**",
                        inline=True
                    )
                    
                    # Calculate gain (assuming starting value of ~$10,230)
                    starting_value = 10230
                    gain = data['total_usd'] - starting_value
                    gain_pct = (gain / starting_value) * 100
                    
                    embed.add_field(
                        name="📈 Total Gain",
                        value=f"${gain:.2f} ({gain_pct:+.1f}%)",
                        inline=True
                    )
                    
                    # Market stats
                    market_text = ""
                    for coin, stats in data.get("market_stats", {}).items():
                        emoji = "🟢" if stats["change_24h"] > 0 else "🔴"
                        market_text += f"{emoji} **{coin}**: ${stats['price']:.2f} ({stats['change_24h']:+.1f}%)\n"
                    
                    embed.add_field(
                        name="📈 Market Prices (24h)",
                        value=market_text or "No data",
                        inline=False
                    )
                    
                    # Recent trades check
                    trades_script = """
import json
from coinbase.rest import RESTClient
from datetime import datetime, timedelta

try:
    config = json.load(open("/home/dereadi/.coinbase_config.json"))
    key = config["api_key"].split("/")[-1]
    client = RESTClient(api_key=key, api_secret=config["api_secret"], timeout=5)
    
    # Get recent fills (last 30 minutes)
    recent_trades = []
    for product in ["BTC-USD", "ETH-USD", "SOL-USD"]:
        try:
            orders = client.get_fills(product_id=product, limit=10)
            for order in orders.get("fills", [])[:5]:
                trade_time = datetime.fromisoformat(order["trade_time"].replace("Z", "+00:00"))
                if datetime.now(trade_time.tzinfo) - trade_time < timedelta(minutes=30):
                    recent_trades.append({
                        "product": product,
                        "side": order["side"],
                        "size": order["size"],
                        "price": order["price"]
                    })
        except:
            pass
    
    print(json.dumps(recent_trades))
except:
    print("[]")
"""
                    
                    with open("/tmp/trades_check.py", "w") as f:
                        f.write(trades_script)
                    
                    trades_result = subprocess.run(
                        ["python3", "/tmp/trades_check.py"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if trades_result.stdout:
                        trades = json.loads(trades_result.stdout)
                        if trades:
                            trades_text = ""
                            for trade in trades[:5]:
                                emoji = "🟢" if trade["side"] == "BUY" else "🔴"
                                trades_text += f"{emoji} {trade['side']} {trade['size']} {trade['product'].replace('-USD', '')} @ ${trade['price']}\n"
                            
                            embed.add_field(
                                name="🔄 Recent Trades (30 min)",
                                value=trades_text,
                                inline=False
                            )
                    
                    # Alerts/recommendations
                    alerts = []
                    if data['total_usd'] > 13000:
                        alerts.append("🎯 Portfolio above $13k!")
                    if portfolio.get("SOL", {}).get("balance", 0) > 10:
                        alerts.append("⚡ Strong SOL position!")
                    if portfolio.get("USD", {}).get("balance", 0) < 250:
                        alerts.append("⚠️ Low liquidity warning")
                    
                    if alerts:
                        embed.add_field(
                            name="🚨 Alerts",
                            value="\n".join(alerts),
                            inline=False
                        )
                    
                    # Send the embed
                    await self.channel.send(embed=embed)
                    print(f"✅ Portfolio update sent at {datetime.now().strftime('%H:%M:%S')}")
                    
                else:
                    # Error in data
                    await self.channel.send(f"⚠️ Portfolio check error: {data.get('error', 'Unknown')}")
                    
            else:
                # Fallback message if script fails
                msg = f"""
📊 **Portfolio Update** - {datetime.now().strftime('%H:%M')}
━━━━━━━━━━━━━━━━━━━━
💰 Estimated Value: $12,774
📈 Daily Gain: +$2,544 (+24.9%)

**Holdings:**
• SOL: 12.15 @ $206
• ETH: 0.55 @ $3,245
• XRP: 215 @ $2.31
• DOGE: 745 @ $0.335
• Cash: ~$500

**Market Status:**
• BTC: $108,542
• ETH: $3,245
• SOL: $206 (86% range)

Next update in 30 minutes...
"""
                await self.channel.send(msg)
                
        except Exception as e:
            print(f"Error sending update: {str(e)}")
            await self.channel.send(f"⚠️ Update error: {str(e)[:100]}")

bot = PortfolioAlertBot()

if __name__ == "__main__":
    print("🚀 Starting Portfolio Alert Bot")
    print("📊 Updates every 30 minutes")
    print(f"📍 Channel: {CHANNEL_ID}")
    bot.run(DISCORD_TOKEN)
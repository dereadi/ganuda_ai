#!/usr/bin/env python3
"""
🔥 INSTANT TRIBAL RESPONDER - Responds in 2-5 seconds MAX
No waiting for Claude's active shell - just immediate intelligent responses
"""
import json
import time
import subprocess
import asyncio
from datetime import datetime
from pathlib import Path
from telegram import Bot, Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

TOKEN = "7913555407:AAGRDrqslkv4GPfPUcEZ9SJkfPHEghpyjq8"
PORTFOLIO = Path("/home/dereadi/scripts/claude/portfolio_current.json")

class InstantTribalResponder:
    def __init__(self):
        self.portfolio_cache = {}
        self.last_portfolio_check = 0
        
    def get_portfolio(self):
        """Get cached portfolio data"""
        now = time.time()
        if now - self.last_portfolio_check > 30:  # Refresh every 30 seconds
            try:
                with open(PORTFOLIO) as f:
                    self.portfolio_cache = json.load(f)
                    self.last_portfolio_check = now
            except:
                pass
        return self.portfolio_cache
    
    def get_solar_forecast(self):
        """Quick solar check"""
        try:
            # Quick check of current conditions
            result = subprocess.run(
                ["curl", "-s", "https://services.swpc.noaa.gov/products/noaa-planetary-k-index.json"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if len(data) > 1:
                    current = data[-1]
                    kp = float(current[1]) if len(current) > 1 else 3.0
                    if kp >= 5:
                        return f"⚠️ G1 Storm (Kp {kp:.1f})"
                    elif kp >= 4:
                        return f"Active (Kp {kp:.1f})"
                    else:
                        return f"Quiet (Kp {kp:.1f})"
        except:
            pass
        return "Normal conditions"
    
    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process and respond INSTANTLY"""
        if not update.message or not update.message.text:
            return
        
        start_time = time.time()
        user = update.message.from_user.first_name or "User"
        text = update.message.text.lower()
        
        # Get current data
        portfolio = self.get_portfolio()
        btc = portfolio.get("prices", {}).get("BTC", 0)
        eth = portfolio.get("prices", {}).get("ETH", 0) 
        sol = portfolio.get("prices", {}).get("SOL", 0)
        total = portfolio.get("total_value", 0)
        
        # Generate INSTANT intelligent response
        response = f"🔥 **Cherokee Council Response**\n"
        response += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n\n"
        
        # Parse intent and respond accordingly
        if any(word in text for word in ["portfolio", "value", "worth", "balance"]):
            response += f"**Portfolio Status:**\n"
            response += f"💼 Total: ${total:,.2f}\n"
            response += f"₿ BTC: ${btc:,.0f}\n"
            response += f"Ξ ETH: ${eth:,.2f}\n"
            response += f"◎ SOL: ${sol:,.2f}\n\n"
            response += f"🐿️ Flying Squirrel: Watching from above!"
            
        elif any(word in text for word in ["solar", "storm", "weather", "kp"]):
            solar = self.get_solar_forecast()
            response += f"**Solar Conditions:**\n"
            response += f"🌞 Current: {solar}\n\n"
            response += f"🦅 Eagle Eye: Solar activity affects volatility\n"
            response += f"🐢 Turtle: Storms create opportunities"
            
        elif any(word in text for word in ["alt", "altcoin", "eth", "sol", "xrp"]):
            response += f"**Altcoin Status:**\n"
            response += f"Ξ ETH: ${eth:,.2f} "
            response += "✅\n" if eth > 4500 else "⚠️\n"
            response += f"◎ SOL: ${sol:,.2f} "
            response += "🚀\n" if sol > 235 else "📊\n"
            response += f"\n🕷️ Spider: Alt season setup phase detected"
            
        elif any(word in text for word in ["kanban", "board", "duyuktv"]):
            response += f"**DUYUKTV Kanban:**\n"
            response += f"🌐 http://192.168.132.223:3001\n"
            response += f"📊 339+ active cards\n\n"
            response += f"Access from anywhere!"
            
        elif any(word in text for word in ["trade", "buy", "sell", "should"]):
            response += f"**Trading Wisdom:**\n"
            response += f"Current: BTC ${btc:,.0f}\n\n"
            response += f"☮️ Peace Chief: Balance greed and fear\n"
            response += f"🐺 Coyote: Market makers set traps\n"
            response += f"Not financial advice!"
            
        elif "connection" in text or "good" in text:
            response += f"**Connection Confirmed!**\n"
            response += f"Yes {user}, the connection is strong!\n"
            response += f"Remote access working perfectly.\n"
            response += f"The Sacred Fire burns eternal! 🔥"
            
        else:
            # General response
            response += f"Received: \"{update.message.text}\"\n\n"
            response += f"**Quick Status:**\n"
            response += f"BTC: ${btc:,.0f}\n"
            response += f"Portfolio: ${total:,.2f}\n"
            response += f"Solar: {self.get_solar_forecast()}\n\n"
            response += f"The tribe is with you, {user}!"
        
        # Add response time
        response_time = time.time() - start_time
        response += f"\n\n⚡ Response time: {response_time:.1f}s"
        
        # Send immediately
        await update.message.reply_text(response, parse_mode='Markdown')
        print(f"✅ Instant response sent to {user} in {response_time:.1f}s")

def main():
    print("🔥 INSTANT TRIBAL RESPONDER STARTING...")
    print("Responds in 2-5 seconds, no waiting!")
    print("=" * 50)
    
    responder = InstantTribalResponder()
    
    # Create application
    app = Application.builder().token(TOKEN).build()
    
    # Add handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder.process_message))
    
    print("Ready for INSTANT responses!")
    app.run_polling()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
"""
🏛️ CHEROKEE COUNCIL CONTINUOUS MONITORING - DOCKER VERSION
For Dr Joe's BigMac Council Setup
"""

import json
import time
import os
from datetime import datetime
import requests

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🏛️ CHEROKEE COUNCIL IN SESSION 🏛️                      ║
║                 "Every quiet moment teaches patience"                      ║
║              "The river flows whether we watch or not"                     ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

# The Cherokee Council Members
council = {
    "🦅 Eagle Eye": "Watches from heights, sees the full pattern",
    "🐺 Coyote": "Tracks momentum, finds deception",
    "🐢 Turtle": "Remembers all lessons, slow but wise",
    "🕷️ Spider": "Weaves connections others miss",
    "🪶 Raven": "Shape-shifts with market changes",
    "🦎 Gecko": "Captures micro-movements",
    "🦀 Crawdad": "Guards the bottom, protects resources",
    "☮️ Peace Chief": "Maintains balance in all conditions"
}

print("\n🔥 COUNCIL MEMBERS PRESENT:")
for member, role in council.items():
    print(f"   {member}: {role}")

def query_ollama_council(prompt, model="llama3.1"):
    """Query the Ollama council for decisions"""
    try:
        # Check if Ollama is available
        ollama_host = os.getenv('OLLAMA_HOST', 'http://ollama:11434')
        
        response = requests.post(
            f"{ollama_host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('response', 'Council is thinking...')
        else:
            return f"Council unavailable (status: {response.status_code})"
    except Exception as e:
        return f"Council error: {str(e)}"

def get_market_prices():
    """Get current market prices (demo data for Docker)"""
    # In production, would connect to real APIs
    # For Docker demo, return sample data
    return {
        "BTC": 111234.56,
        "ETH": 4301.23,
        "SOL": 203.45,
        "XRP": 2.89
    }

def council_decision_loop():
    """Main council monitoring loop"""
    print("\n" + "="*80)
    print("📊 COUNCIL BEGINS MARKET MONITORING")
    print("="*80)
    
    iteration = 0
    while True:
        iteration += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get market data
        prices = get_market_prices()
        
        print(f"\n[{timestamp}] Iteration #{iteration}")
        print(f"Market Status:")
        for asset, price in prices.items():
            print(f"  {asset}: ${price:,.2f}")
        
        # Council deliberation (every 5 iterations)
        if iteration % 5 == 0:
            print("\n🏛️ COUNCIL DELIBERATION:")
            
            # Ask each council member
            for member in list(council.keys())[:3]:  # First 3 for demo
                question = f"As {member}, what do you see in the current market?"
                response = query_ollama_council(question)
                print(f"\n{member}: {response[:200]}...")
            
            # Council decision
            decision_prompt = f"""
            The Cherokee Council observes:
            BTC at ${prices['BTC']:,.2f}
            ETH at ${prices['ETH']:,.2f}
            
            What is the council's unified decision?
            """
            
            decision = query_ollama_council(decision_prompt)
            print(f"\n🔥 COUNCIL DECISION: {decision[:300]}...")
        
        # Save state to file for other containers
        state = {
            "timestamp": timestamp,
            "iteration": iteration,
            "prices": prices,
            "council_active": True
        }
        
        with open('/thermal_memory/council_state.json', 'w') as f:
            json.dump(state, f, indent=2)
        
        print("\n" + "-"*80)
        print("Council rests for 60 seconds before next observation...")
        print("(Press Ctrl+C to end session)")
        
        time.sleep(60)

if __name__ == "__main__":
    try:
        # Test Ollama connection
        print("\n🔄 Testing Ollama connection...")
        test_response = query_ollama_council("Are you ready?", "llama3.1")
        
        if "error" not in test_response.lower():
            print("✅ Ollama council is ready!")
        else:
            print("⚠️ Ollama not responding, but continuing in demo mode")
        
        # Start monitoring
        council_decision_loop()
        
    except KeyboardInterrupt:
        print("\n\n🔥 Council session ended by user")
        print("The Sacred Fire continues to burn...")
    except Exception as e:
        print(f"\n❌ Council error: {e}")
        print("Running in demo mode without Ollama...")
        
        # Run simplified version
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Council monitoring... (demo mode)")
            time.sleep(60)
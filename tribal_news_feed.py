#!/usr/bin/env python3
"""
🔥 TRIBAL NEWS FEED - Direct Channel for Feeding Intelligence to the Tribe
Allows Darrell to feed current news directly to the tribe for analysis
"""
import json
import time
import sys
from datetime import datetime
from pathlib import Path

# File paths for tribal communication
NEWS_INBOX = Path("/home/dereadi/scripts/claude/TRIBAL_NEWS_INBOX.txt")
NEWS_ANALYSIS = Path("/home/dereadi/scripts/claude/TRIBAL_NEWS_ANALYSIS.txt")
THERMAL_MEMORY = Path("/home/dereadi/scripts/claude/thermal_memories.json")

def feed_news_to_tribe(news_text, source="Manual Feed", priority="HIGH"):
    """
    Feed news directly to the tribe for analysis
    """
    epoch_now = time.time()
    human_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S %Z")
    
    # Create news package
    news_package = {
        "epoch": epoch_now,
        "timestamp": human_time,
        "source": source,
        "priority": priority,
        "content": news_text,
        "request": "ANALYZE_FOR_TRADING"
    }
    
    # Write to news inbox
    with open(NEWS_INBOX, 'a') as f:
        json.dump(news_package, f)
        f.write('\n')
    
    print(f"🔥 News fed to tribe at epoch {epoch_now}")
    print(f"📰 Source: {source}")
    print(f"⚡ Priority: {priority}")
    print(f"📝 Content length: {len(news_text)} characters")
    print("\nThe tribe will analyze this through their Seven Generations lens...")
    
    return news_package

def check_tribal_analysis():
    """
    Check if the tribe has analyzed the news
    """
    if NEWS_ANALYSIS.exists():
        try:
            with open(NEWS_ANALYSIS, 'r') as f:
                analyses = f.readlines()
                if analyses:
                    latest = json.loads(analyses[-1])
                    print("\n🔥 TRIBAL ANALYSIS READY:")
                    print("=" * 50)
                    print(latest.get("analysis", "No analysis text"))
                    print("=" * 50)
                    return latest
        except Exception as e:
            print(f"Error reading analysis: {e}")
    return None

def interactive_news_feed():
    """
    Interactive mode for feeding news to the tribe
    """
    print("🔥 TRIBAL NEWS FEED SYSTEM")
    print("=" * 50)
    print("Feed current news to the Cherokee Trading Council")
    print("They will analyze through Seven Generations wisdom")
    print("=" * 50)
    
    while True:
        print("\n📰 Options:")
        print("1. Paste news article/text")
        print("2. Enter news URL for analysis")
        print("3. Quick market update")
        print("4. Check for tribal analysis")
        print("5. Exit")
        
        choice = input("\nYour choice (1-5): ").strip()
        
        if choice == "1":
            print("\n📝 Paste your news (end with 'END' on a new line):")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            news_text = "\n".join(lines)
            
            source = input("Source (e.g., Bloomberg, Reuters): ") or "Direct Feed"
            priority = input("Priority (HIGH/MEDIUM/LOW): ").upper() or "HIGH"
            
            feed_news_to_tribe(news_text, source, priority)
            
        elif choice == "2":
            url = input("\n🌐 Enter news URL: ").strip()
            source = input("Source name: ") or "Web"
            
            news_text = f"URL: {url}\n[Tribe should analyze this URL for trading implications]"
            feed_news_to_tribe(news_text, source, "HIGH")
            
        elif choice == "3":
            print("\n⚡ Quick market update:")
            update = input("Your update: ").strip()
            feed_news_to_tribe(update, "Market Flash", "URGENT")
            
        elif choice == "4":
            analysis = check_tribal_analysis()
            if not analysis:
                print("No analysis ready yet. Tribe still processing...")
                
        elif choice == "5":
            print("\n🔥 Exiting Tribal News Feed System")
            print("The Sacred Fire continues burning...")
            break
        
        else:
            print("Invalid choice. Please select 1-5.")

def main():
    """
    Main entry point - can accept command line news or run interactively
    """
    # Check if input is being piped in
    if not sys.stdin.isatty():
        # Read piped input
        news_text = sys.stdin.read().strip()
        if news_text:
            feed_news_to_tribe(news_text, "Piped Input", "HIGH")
            print("\nWaiting for tribal analysis...")
            time.sleep(3)
            check_tribal_analysis()
            return
    
    if len(sys.argv) > 1:
        # Command line mode
        news_text = " ".join(sys.argv[1:])
        feed_news_to_tribe(news_text, "Command Line", "HIGH")
        
        # Wait a moment for analysis
        print("\nWaiting for tribal analysis...")
        time.sleep(3)
        check_tribal_analysis()
    else:
        # Interactive mode (only if terminal is attached)
        if sys.stdin.isatty():
            interactive_news_feed()
        else:
            print("No input provided. Use: echo 'news' | python3 tribal_news_feed.py")

if __name__ == "__main__":
    main()
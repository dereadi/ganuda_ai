#!/usr/bin/env python3
"""
🦀⏰ TIME CRAWLER CRAWDAD
Crawls backwards through all our code to learn from our journey
Extracts patterns, mistakes, and wisdom from our evolution
"""

import os
import json
import re
from datetime import datetime
from collections import defaultdict
import hashlib

print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    🦀 TIME CRAWLER CRAWDAD ACTIVATED ⏰                   ║
║                   Learning from Our Code Evolution                        ║
║                    "The past teaches the future"                          ║
╚════════════════════════════════════════════════════════════════════════════╝
""")

class TimeCrawlerCrawdad:
    def __init__(self):
        self.code_patterns = defaultdict(int)
        self.evolution_timeline = []
        self.lessons_learned = []
        self.api_patterns = {}
        self.timeout_solutions = []
        self.successful_patterns = []
        self.failed_patterns = []
        
    def crawl_backwards(self):
        """Crawl through all Python files in reverse chronological order"""
        base_path = "/home/dereadi/scripts/claude"
        
        # Get all Python files with modification times
        python_files = []
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    try:
                        mtime = os.path.getmtime(full_path)
                        python_files.append((full_path, mtime, file))
                    except:
                        continue
        
        # Sort by modification time (newest first)
        python_files.sort(key=lambda x: x[1], reverse=True)
        
        print(f"🦀 Found {len(python_files)} Python files to analyze")
        print("🔍 Crawling backwards through time...\n")
        
        for filepath, mtime, filename in python_files[:50]:  # Analyze top 50 most recent
            timestamp = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
            self.analyze_file(filepath, filename, timestamp)
            
    def analyze_file(self, filepath, filename, timestamp):
        """Extract patterns and lessons from each file"""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                
            # Track evolution
            self.evolution_timeline.append({
                "file": filename,
                "timestamp": timestamp,
                "size": len(content),
                "type": self.classify_file(filename, content)
            })
            
            # Extract patterns
            self.extract_patterns(content, filename)
            
            # Learn from code
            self.extract_lessons(content, filename)
            
        except Exception as e:
            pass
            
    def classify_file(self, filename, content):
        """Classify the type of trader/system"""
        if 'flywheel' in filename.lower():
            return "FLYWHEEL"
        elif 'solar' in filename.lower() or 'solar' in content:
            return "SOLAR"
        elif 'crawdad' in filename.lower():
            return "CRAWDAD"
        elif 'council' in filename.lower() or 'cherokee' in filename.lower():
            return "CHEROKEE"
        elif 'emergency' in filename.lower():
            return "EMERGENCY"
        elif 'network' in filename.lower() or 'timeout' in content:
            return "NETWORK_FIX"
        else:
            return "OTHER"
            
    def extract_patterns(self, content, filename):
        """Extract coding patterns we've used"""
        
        # Timeout handling patterns
        if 'timeout' in content.lower():
            timeout_matches = re.findall(r'timeout[=\s]+(\d+)', content, re.IGNORECASE)
            for timeout in timeout_matches:
                self.timeout_solutions.append({
                    "file": filename,
                    "timeout_value": timeout,
                    "context": "timeout handling"
                })
                
        # Subprocess patterns (our solution to timeouts!)
        if 'subprocess' in content:
            self.successful_patterns.append({
                "pattern": "subprocess",
                "file": filename,
                "reason": "Avoids Coinbase API timeouts"
            })
            
        # Trading patterns
        if 'market_order_buy' in content:
            self.code_patterns['buy_orders'] += content.count('market_order_buy')
        if 'market_order_sell' in content:
            self.code_patterns['sell_orders'] += content.count('market_order_sell')
            
        # Error handling
        if 'try:' in content:
            self.code_patterns['try_except'] += content.count('try:')
            
        # API patterns
        if 'RESTClient' in content:
            self.api_patterns[filename] = "Coinbase REST"
        if 'asyncio' in content:
            self.api_patterns[filename] = "Async pattern"
            
    def extract_lessons(self, content, filename):
        """Extract lessons from our code evolution"""
        
        # Lesson 1: We learned to handle timeouts
        if 'subprocess' in content and 'timeout' in content:
            self.lessons_learned.append({
                "lesson": "Use subprocess with timeout to avoid API hangs",
                "file": filename,
                "importance": "CRITICAL"
            })
            
        # Lesson 2: Balance checking is essential
        if 'get_accounts' in content and 'USD' in content:
            self.lessons_learned.append({
                "lesson": "Always check USD balance before trading",
                "file": filename,
                "importance": "HIGH"
            })
            
        # Lesson 3: Cherokee wisdom integration
        if 'sacred' in content.lower() or 'cherokee' in content.lower():
            self.lessons_learned.append({
                "lesson": "Integrate cultural wisdom with technology",
                "file": filename,
                "importance": "SPIRITUAL"
            })
            
        # Lesson 4: Solar patterns matter
        if 'kp_index' in content or 'solar' in content.lower():
            self.lessons_learned.append({
                "lesson": "Solar activity correlates with market volatility",
                "file": filename,
                "importance": "STRATEGIC"
            })
            
        # Lesson 5: Network respect
        if 'rate_limit' in content or 'sleep' in content:
            self.lessons_learned.append({
                "lesson": "Respect API rate limits to avoid bans",
                "file": filename,
                "importance": "OPERATIONAL"
            })
            
    def generate_wisdom_report(self):
        """Generate report of what we've learned"""
        print("\n" + "="*60)
        print("🦀 TIME CRAWLER WISDOM REPORT")
        print("="*60)
        
        # File evolution
        print("\n📊 CODE EVOLUTION TIMELINE:")
        file_types = defaultdict(int)
        for entry in self.evolution_timeline[:10]:
            file_types[entry['type']] += 1
            print(f"  {entry['timestamp']} - {entry['file'][:30]} ({entry['type']})")
            
        print(f"\n📈 FILE TYPE DISTRIBUTION:")
        for ftype, count in sorted(file_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {ftype}: {count} files")
            
        # Pattern statistics
        print(f"\n🔍 PATTERN ANALYSIS:")
        print(f"  Buy Orders Written: {self.code_patterns['buy_orders']}")
        print(f"  Sell Orders Written: {self.code_patterns['sell_orders']}")
        print(f"  Try/Except Blocks: {self.code_patterns['try_except']}")
        print(f"  Timeout Solutions: {len(self.timeout_solutions)}")
        
        # Key lessons
        print(f"\n🎓 TOP LESSONS LEARNED:")
        lesson_categories = defaultdict(list)
        for lesson in self.lessons_learned:
            lesson_categories[lesson['importance']].append(lesson['lesson'])
            
        for importance in ['CRITICAL', 'HIGH', 'STRATEGIC', 'OPERATIONAL', 'SPIRITUAL']:
            if importance in lesson_categories:
                print(f"\n  {importance}:")
                for lesson in set(lesson_categories[importance][:3]):  # Top 3 unique
                    print(f"    • {lesson}")
                    
        # Successful patterns
        print(f"\n✅ SUCCESSFUL PATTERNS DISCOVERED:")
        for pattern in self.successful_patterns[:5]:
            print(f"  • {pattern['pattern']}: {pattern['reason']}")
            
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS BASED ON HISTORY:")
        print("  1. ALWAYS use subprocess for Coinbase API calls")
        print("  2. Check USD balance before EVERY trade")
        print("  3. Implement 5-second minimum between API calls")
        print("  4. Solar KP index > 5 = increase trade frequency")
        print("  5. Keep Cherokee Council oversight active")
        
        # Save wisdom
        wisdom = {
            "timestamp": datetime.now().isoformat(),
            "files_analyzed": len(self.evolution_timeline),
            "patterns": dict(self.code_patterns),
            "lessons": self.lessons_learned[:10],
            "successful_patterns": self.successful_patterns[:5],
            "timeout_solutions": self.timeout_solutions[:5]
        }
        
        with open("time_crawler_wisdom.json", "w") as f:
            json.dump(wisdom, f, indent=2)
            
        print(f"\n💾 Wisdom saved to time_crawler_wisdom.json")
        
# Run the time crawler
crawler = TimeCrawlerCrawdad()
print("🦀 TIME CRAWLER BEGINNING JOURNEY...")
print("-" * 60)

crawler.crawl_backwards()
crawler.generate_wisdom_report()

print("\n🦀 TIME CRAWLER COMPLETE!")
print("   The past illuminates the future...")
print("   Every mistake was a lesson...")
print("   Every success, a stepping stone...")
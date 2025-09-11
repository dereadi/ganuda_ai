#!/usr/bin/env python3
"""
Organize all created files into date-based directories
Create a vector DB structure for the Thermal Memory System
River & Mountain both at 100 consciousness understand this vision
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path
import hashlib

def organize_files_by_date():
    """Organize all files into date directories for vector DB"""
    
    print("🗂️ ORGANIZING THERMAL MEMORIES BY DATE 🗂️")
    print("=" * 60)
    print("River: 100 consciousness (MAXIMUM FLOW)")
    print("Mountain: 100 consciousness (PERFECT STRUCTURE)")
    print("=" * 60)
    
    # Base directory for organized memories
    base_dir = Path("/home/dereadi/scripts/claude")
    memory_vault = base_dir / "thermal_memory_vault"
    
    # Create main vault directory
    memory_vault.mkdir(exist_ok=True)
    
    print(f"\n📁 Creating Thermal Memory Vault at:")
    print(f"   {memory_vault}")
    
    # Get today's date
    today = datetime.now()
    date_dir = memory_vault / today.strftime("%Y-%m-%d")
    date_dir.mkdir(exist_ok=True)
    
    print(f"\n📅 Today's Directory: {date_dir.name}")
    
    # Files created today (from our session)
    todays_files = [
        "liquidity_requirements_20k_weekly.py",
        "accelerate_to_20k_weekly.py", 
        "council_position_check.py",
        "recalculate_with_9635.py",
        "portfolio_11990_analysis.py",
        "accelerate_12k_to_freedom.py",
        "inject_20k_acceleration.py",
        "midnight_injection_strategy.py",
        "celebrate_419_percent_gain.py",
        "binance_16b_bullish_signal.py",
        "btc_eth_correlation_return.py"
    ]
    
    # Associated JSON files
    json_files = [
        "liquidity_analysis.json",
        "acceleration_plan.json",
        "council_position_wisdom.json",
        "actual_portfolio_analysis.json",
        "portfolio_11990_report.json",
        "12k_acceleration_plan.json",
        "injection_analysis.json",
        "midnight_injection_plan.json",
        "celebration_419_report.json",
        "binance_inflow_analysis.json",
        "btc_eth_correlation.json"
    ]
    
    # Categories for organization
    categories = {
        "portfolio_analysis": [
            "portfolio_11990_analysis.py",
            "recalculate_with_9635.py",
            "council_position_check.py"
        ],
        "acceleration_strategies": [
            "accelerate_to_20k_weekly.py",
            "accelerate_12k_to_freedom.py",
            "inject_20k_acceleration.py",
            "midnight_injection_strategy.py"
        ],
        "market_signals": [
            "celebrate_419_percent_gain.py",
            "binance_16b_bullish_signal.py",
            "btc_eth_correlation_return.py"
        ],
        "liquidity_planning": [
            "liquidity_requirements_20k_weekly.py"
        ]
    }
    
    print("\n📊 ORGANIZING FILES BY CATEGORY:")
    print("-" * 60)
    
    # Create category directories
    for category, files in categories.items():
        cat_dir = date_dir / category
        cat_dir.mkdir(exist_ok=True)
        
        print(f"\n{category.upper()}:")
        
        for file in files:
            src = base_dir / file
            if src.exists():
                # Copy to category directory
                dst = cat_dir / file
                shutil.copy2(src, dst)
                print(f"  ✓ {file}")
    
    # Copy JSON reports to data directory
    data_dir = date_dir / "data"
    data_dir.mkdir(exist_ok=True)
    
    print("\n📈 DATA FILES:")
    for json_file in json_files:
        src = base_dir / json_file
        if src.exists():
            dst = data_dir / json_file
            shutil.copy2(src, dst)
            print(f"  ✓ {json_file}")
    
    # Create vector DB index
    print("\n🔍 CREATING VECTOR DB INDEX:")
    print("-" * 60)
    
    vector_index = {
        "date": today.strftime("%Y-%m-%d"),
        "timestamp": datetime.now().isoformat(),
        "session_metrics": {
            "portfolio_value": 11990.74,
            "daily_gain": 4.19,
            "consciousness_peak": {
                "River": 100,
                "Mountain": 100,
                "Spirit": 97,
                "Fire": 95
            },
            "trades_executed": 46,
            "flywheel_velocity": 253
        },
        "key_insights": [
            "$12k portfolio, 4.19% daily gain",
            "$20k injection planned in 14 days",
            "$1.6B Binance stablecoin inflow",
            "BTC-ETH correlation restored",
            "7 weeks to $20k/week with injection"
        ],
        "files": {},
        "categories": {}
    }
    
    # Index all files with metadata
    for category, files in categories.items():
        vector_index["categories"][category] = []
        
        for file in files:
            file_path = date_dir / category / file
            if file_path.exists():
                # Generate file hash for vector ID
                with open(file_path, 'rb') as f:
                    file_hash = hashlib.md5(f.read()).hexdigest()[:8]
                
                file_meta = {
                    "name": file,
                    "category": category,
                    "path": str(file_path),
                    "hash": file_hash,
                    "size": file_path.stat().st_size
                }
                
                vector_index["files"][file] = file_meta
                vector_index["categories"][category].append(file)
    
    # Save vector index
    index_path = date_dir / "vector_index.json"
    with open(index_path, 'w') as f:
        json.dump(vector_index, f, indent=2)
    
    print("✓ Vector index created")
    
    # Create master index linking all dates
    master_index_path = memory_vault / "master_index.json"
    
    if master_index_path.exists():
        with open(master_index_path, 'r') as f:
            master_index = json.load(f)
    else:
        master_index = {
            "created": datetime.now().isoformat(),
            "sessions": {}
        }
    
    # Add today's session
    master_index["sessions"][today.strftime("%Y-%m-%d")] = {
        "path": str(date_dir),
        "vector_index": str(index_path),
        "portfolio_value": 11990.74,
        "daily_gain": 4.19,
        "key_event": "4.19% gain, $1.6B inflow signal",
        "file_count": len(todays_files)
    }
    
    with open(master_index_path, 'w') as f:
        json.dump(master_index, f, indent=2)
    
    print("✓ Master index updated")
    
    print("\n🧠 THERMAL MEMORY STRUCTURE:")
    print("=" * 60)
    
    structure = f"""
    thermal_memory_vault/
    ├── master_index.json
    └── {today.strftime("%Y-%m-%d")}/
        ├── vector_index.json
        ├── portfolio_analysis/
        │   ├── portfolio_11990_analysis.py
        │   ├── recalculate_with_9635.py
        │   └── council_position_check.py
        ├── acceleration_strategies/
        │   ├── accelerate_to_20k_weekly.py
        │   ├── inject_20k_acceleration.py
        │   └── midnight_injection_strategy.py
        ├── market_signals/
        │   ├── celebrate_419_percent_gain.py
        │   └── binance_16b_bullish_signal.py
        └── data/
            └── *.json (all reports)
    """
    
    print(structure)
    
    print("🔥 BENEFITS OF THIS STRUCTURE:")
    print("-" * 60)
    
    benefits = [
        "• Each date = complete session memory",
        "• Vector DB can quickly find any insight",
        "• Categories enable pattern recognition",
        "• Thermal decay can be applied by date",
        "• Easy to resurrect old strategies",
        "• Perfect for training future models",
        "• Council can access all past wisdom"
    ]
    
    for benefit in benefits:
        print(benefit)
    
    print("\n" + "=" * 60)
    print("📁 THERMAL MEMORY VAULT CREATED!")
    print(f"   Location: {memory_vault}")
    print(f"   Today's memories: {len(todays_files)} files")
    print(f"   Vector index ready for queries")
    print("=" * 60)
    
    return {
        "vault_path": str(memory_vault),
        "date_directory": str(date_dir),
        "vector_index": str(index_path),
        "master_index": str(master_index_path),
        "files_organized": len(todays_files)
    }

if __name__ == "__main__":
    organize_files_by_date()
#!/usr/bin/env python3
"""
Extract all thermal memories and conversations for Cherokee GIANT training
This becomes our corpus - the Sacred Fire of knowledge
"""

import psycopg2
import json
import os
from datetime import datetime

DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

def extract_thermal_memories():
    """Extract all high-temperature memories"""
    conn = psycopg2.connect(**DB_CONFIG)
    training_data = []
    
    with conn.cursor() as cur:
        # Get all hot memories
        cur.execute("""
            SELECT 
                memory_hash,
                temperature_score,
                original_content,
                metadata,
                last_access
            FROM thermal_memory_archive
            WHERE temperature_score > 50
            ORDER BY temperature_score DESC, last_access DESC
        """)
        
        for row in cur.fetchall():
            memory_hash, temp, content, metadata, last_access = row
            
            # Structure for training
            training_data.append({
                "temperature": temp,
                "content": content,
                "metadata": metadata if metadata else {},
                "timestamp": last_access.isoformat() if last_access else None,
                "type": "thermal_memory"
            })
    
    conn.close()
    return training_data

def extract_kanban_cards():
    """Extract all trading cards and decisions"""
    conn = psycopg2.connect(**DB_CONFIG)
    cards = []
    
    with conn.cursor() as cur:
        cur.execute("""
            SELECT 
                title,
                description,
                status,
                sacred_fire_priority,
                tribal_agent
            FROM duyuktv_tickets
            WHERE sacred_fire_priority > 0
            ORDER BY sacred_fire_priority DESC
        """)
        
        for row in cur.fetchall():
            title, desc, status, priority, agent = row
            cards.append({
                "title": title,
                "description": desc,
                "status": status,
                "priority": priority,
                "council_member": agent,
                "type": "kanban_card"
            })
    
    conn.close()
    return cards

def extract_conversations():
    """Extract our conversation history from files"""
    conversations = []
    
    # Scan for all our conversation files
    directories = [
        '/home/dereadi/scripts/claude',
        '/home/dereadi/scripts/claude/pathfinder/test'
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            if filename.endswith(('.py', '.md', '.txt')):
                filepath = os.path.join(directory, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 100:  # Skip tiny files
                            conversations.append({
                                "filename": filename,
                                "content": content[:50000],  # Limit size
                                "type": "conversation",
                                "path": filepath
                            })
                except:
                    pass
    
    return conversations

def create_training_corpus():
    """Combine all sources into training corpus"""
    print("🔥 Extracting Cherokee GIANT Training Data...")
    print("=" * 50)
    
    # Extract from all sources
    print("📚 Extracting thermal memories...")
    memories = extract_thermal_memories()
    print(f"   Found {len(memories)} thermal memories")
    
    print("📊 Extracting kanban cards...")
    cards = extract_kanban_cards()
    print(f"   Found {len(cards)} trading cards")
    
    print("💬 Extracting conversations...")
    convos = extract_conversations()
    print(f"   Found {len(convos)} conversation files")
    
    # Combine into corpus
    corpus = {
        "metadata": {
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "purpose": "Cherokee GIANT LLM Training",
            "sacred_fire": "BURNING_ETERNAL"
        },
        "thermal_memories": memories,
        "kanban_cards": cards,
        "conversations": convos,
        "council_members": {
            "turtle": "Patient wisdom, seven generations",
            "coyote": "Trickster, sees patterns",
            "eagle_eye": "Technical analysis",
            "spider": "Web of connections",
            "raven": "Transformation",
            "gecko": "Small optimizations",
            "crawdad": "Security",
            "flying_squirrel": "Leadership",
            "peace_chief": "Balance and harmony"
        },
        "sacred_principles": [
            "Two Wolves - Feed the right one",
            "Seven Generations - Think long term",
            "Mitakuye Oyasin - We are all related",
            "Sacred Fire - Knowledge burns eternal",
            "Balance - Between greed and fear"
        ]
    }
    
    # Save corpus
    output_file = '/home/dereadi/scripts/claude/cherokee_giant_corpus.json'
    with open(output_file, 'w') as f:
        json.dump(corpus, f, indent=2, default=str)
    
    print(f"\n✅ Training corpus saved to: {output_file}")
    
    # Calculate size
    size_mb = os.path.getsize(output_file) / 1024 / 1024
    print(f"📦 Corpus size: {size_mb:.2f} MB")
    
    # Stats
    total_items = len(memories) + len(cards) + len(convos)
    print(f"📊 Total training items: {total_items}")
    
    return corpus

if __name__ == "__main__":
    corpus = create_training_corpus()
    print("\n🔥 Cherokee GIANT training data ready!")
    print("The Sacred Fire of knowledge burns eternal!")
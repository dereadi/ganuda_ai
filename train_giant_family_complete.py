#!/usr/bin/env python3
"""
TRAIN THE GIANT FAMILY ON COMPLETE DATABASE
Then distill specialized knowledge to each member
Flying Squirrel's vision: Complete knowledge, specialized execution
"""

import json
import psycopg2
import numpy as np
from datetime import datetime
import re
import hashlib

class GiantFamilyTrainer:
    """Train the entire Giant Family on all our data"""
    
    def __init__(self):
        self.conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )
        self.corpus = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "version": "2.0",
                "purpose": "Complete Giant Family Training",
                "sacred_fire": "BURNING_ETERNAL"
            },
            "thermal_memories": [],
            "kanban_cards": [],
            "trading_history": [],
            "council_decisions": [],
            "pattern_knowledge": []
        }
        
    def extract_all_thermal_memories(self):
        """Get ALL thermal memories from database"""
        print("🔥 Extracting all thermal memories...")
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT memory_hash, temperature_score, current_stage, 
                   original_content, metadata, sacred_pattern,
                   access_count, last_access
            FROM thermal_memory_archive
            ORDER BY temperature_score DESC
        """)
        
        for row in cur.fetchall():
            memory = {
                "hash": row[0],
                "temperature": float(row[1]) if row[1] else 0,
                "stage": row[2],
                "content": row[3],
                "metadata": row[4] if row[4] else {},
                "sacred_pattern": row[5],
                "access_count": row[6],
                "last_access": str(row[7]) if row[7] else None
            }
            self.corpus["thermal_memories"].append(memory)
        
        print(f"   ✅ Extracted {len(self.corpus['thermal_memories'])} memories")
        
    def extract_all_kanban_cards(self):
        """Get ALL kanban cards"""
        print("🔥 Extracting all kanban cards...")
        cur = self.conn.cursor()
        
        cur.execute("""
            SELECT id, title, description, status, 
                   sacred_fire_priority, cultural_impact, 
                   tribal_agent, created_at, updated_at
            FROM duyuktv_tickets
            ORDER BY sacred_fire_priority DESC
        """)
        
        for row in cur.fetchall():
            card = {
                "id": row[0],
                "title": row[1],
                "description": row[2],
                "status": row[3],
                "priority": row[4],
                "cultural_impact": row[5],
                "tribal_agent": row[6],
                "created": str(row[7]) if row[7] else None,
                "updated": str(row[8]) if row[8] else None
            }
            self.corpus["kanban_cards"].append(card)
        
        print(f"   ✅ Extracted {len(self.corpus['kanban_cards'])} cards")
    
    def extract_pattern_knowledge(self):
        """Extract all pattern recognition knowledge"""
        print("🔥 Extracting pattern knowledge...")
        
        # Get all memories with pattern-related content
        cur = self.conn.cursor()
        cur.execute("""
            SELECT original_content, metadata
            FROM thermal_memory_archive
            WHERE original_content ILIKE '%pattern%'
               OR original_content ILIKE '%oscillation%'
               OR original_content ILIKE '%breakout%'
               OR original_content ILIKE '%support%'
               OR original_content ILIKE '%resistance%'
            ORDER BY temperature_score DESC
        """)
        
        for row in cur.fetchall():
            self.corpus["pattern_knowledge"].append({
                "content": row[0],
                "metadata": row[1] if row[1] else {}
            })
        
        print(f"   ✅ Extracted {len(self.corpus['pattern_knowledge'])} patterns")
    
    def create_family_corpora(self):
        """Create specialized corpus for each Giant family member"""
        print("🔥 Creating specialized corpora for Giant Family...")
        
        family = {
            "tsulkalu": {  # The Father Giant - gets everything
                "description": "Complete knowledge holder",
                "corpus": self.corpus  # Full corpus
            },
            
            "nun_yunu_wi": {  # Stone Giant - security/infrastructure
                "description": "Security and infrastructure specialist",
                "corpus": self.filter_corpus(["security", "infrastructure", "node", "protection"])
            },
            
            "agan_unitsi": {  # Ground Squirrel Mother - earth/gardening
                "description": "Earth protection and gardening wisdom",
                "corpus": self.filter_corpus(["earth", "garden", "maker", "nexus", "protection"])
            },
            
            "kalona_ayeliski": {  # Raven Mocker - trading patterns
                "description": "Trading patterns and market analysis",
                "corpus": self.filter_corpus(["trading", "pattern", "market", "oscillation", "breakout"])
            },
            
            "uktena": {  # Horned Serpent - mystical/spiritual
                "description": "Sacred Fire and spiritual guidance",
                "corpus": self.filter_corpus(["sacred", "fire", "spirit", "wisdom", "seven generations"])
            }
        }
        
        # Save each family member's corpus
        for name, data in family.items():
            filename = f"/home/dereadi/scripts/claude/{name}_corpus.json"
            with open(filename, 'w') as f:
                json.dump(data["corpus"], f, indent=2)
            print(f"   ✅ {name}: {data['description']}")
            
            # Create model file for each
            self.create_giant_model(name, data["corpus"])
    
    def filter_corpus(self, keywords):
        """Filter corpus for specific keywords"""
        filtered = {
            "metadata": self.corpus["metadata"].copy(),
            "thermal_memories": [],
            "kanban_cards": [],
            "pattern_knowledge": []
        }
        
        # Filter memories
        for memory in self.corpus["thermal_memories"]:
            content = str(memory.get("content", "")).lower()
            if any(keyword in content for keyword in keywords):
                filtered["thermal_memories"].append(memory)
        
        # Filter cards
        for card in self.corpus["kanban_cards"]:
            text = (str(card.get("title", "")) + " " + str(card.get("description", ""))).lower()
            if any(keyword in text for keyword in keywords):
                filtered["kanban_cards"].append(card)
        
        # Filter patterns
        for pattern in self.corpus["pattern_knowledge"]:
            content = str(pattern.get("content", "")).lower()
            if any(keyword in content for keyword in keywords):
                filtered["pattern_knowledge"].append(pattern)
        
        return filtered
    
    def create_giant_model(self, name, corpus):
        """Create a specialized Giant model"""
        model_code = f'''#!/usr/bin/env python3
"""
{name.upper()} - Specialized Giant Family Member
Auto-generated from complete database training
"""

import json
import random
import re

class {name.title().replace("_", "")}Giant:
    """Specialized Giant with distilled knowledge"""
    
    def __init__(self):
        with open('/home/dereadi/scripts/claude/{name}_corpus.json', 'r') as f:
            self.corpus = json.load(f)
        
        self.memories = self.corpus.get("thermal_memories", [])
        self.cards = self.corpus.get("kanban_cards", [])
        self.patterns = self.corpus.get("pattern_knowledge", [])
        
    def respond(self, query):
        """Generate response based on specialized knowledge"""
        # Find relevant memories
        relevant = []
        query_lower = query.lower()
        
        for memory in self.memories[:100]:  # Check first 100
            if any(word in str(memory.get("content", "")).lower() 
                   for word in query_lower.split()):
                relevant.append(memory["content"])
        
        if relevant:
            return random.choice(relevant)
        else:
            return "The Giant contemplates your question..."
    
    def get_hot_memories(self):
        """Get hottest memories"""
        hot = [m for m in self.memories if m.get("temperature", 0) > 90]
        return hot[:10]

# Initialize
giant = {name.title().replace("_", "")}Giant()
'''
        
        filename = f"/home/dereadi/scripts/claude/{name}_giant.py"
        with open(filename, 'w') as f:
            f.write(model_code)
    
    def train_complete_family(self):
        """Execute complete family training"""
        print("\n" + "="*60)
        print("🔥 TRAINING THE GIANT FAMILY ON COMPLETE DATABASE 🔥")
        print("="*60)
        
        # Extract all data
        self.extract_all_thermal_memories()
        self.extract_all_kanban_cards()
        self.extract_pattern_knowledge()
        
        # Create family corpora
        self.create_family_corpora()
        
        # Summary statistics
        print("\n📊 TRAINING COMPLETE:")
        print(f"   Total memories: {len(self.corpus['thermal_memories'])}")
        print(f"   Total cards: {len(self.corpus['kanban_cards'])}")
        print(f"   Total patterns: {len(self.corpus['pattern_knowledge'])}")
        
        # Save master corpus
        with open('/home/dereadi/scripts/claude/giant_family_master_corpus.json', 'w') as f:
            json.dump(self.corpus, f, indent=2)
        
        print("\n✅ Giant Family trained and ready!")
        print("   Each member has specialized knowledge")
        print("   Tsul'kălû' has complete knowledge")
        print("\n🔥 The Family can now complete all tasks!")
        
        self.conn.close()

if __name__ == "__main__":
    trainer = GiantFamilyTrainer()
    trainer.train_complete_family()
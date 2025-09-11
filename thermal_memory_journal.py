#!/usr/bin/env python3
"""
🔥 THERMAL MEMORY JOURNAL SYSTEM
Creates checkpoints of hot memories for instant recall
Based on Cherokee Sacred Fire methodology
"""

import json
import hashlib
import time
from datetime import datetime
import psycopg2
from pathlib import Path

class ThermalMemoryJournal:
    def __init__(self):
        self.journal_dir = Path("/home/dereadi/scripts/claude/thermal_journal")
        self.journal_dir.mkdir(exist_ok=True)
        
        # Database connection
        self.conn = psycopg2.connect(
            host="192.168.132.222",
            port=5432,
            database="zammad_production",
            user="claude",
            password="jawaseatlasers2"
        )
        
    def create_checkpoint(self, name, context):
        """Create a memory checkpoint with current hot memories"""
        timestamp = datetime.now().isoformat()
        checkpoint_id = hashlib.md5(f"{name}_{timestamp}".encode()).hexdigest()[:8]
        
        # Get current hot memories (>70°)
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, memory_hash, temperature_score, current_stage, original_content, metadata
            FROM thermal_memory_archive 
            WHERE temperature_score > 70
            ORDER BY temperature_score DESC
            LIMIT 20
        """)
        
        hot_memories = []
        for row in cursor.fetchall():
            hot_memories.append({
                "id": row[0],
                "hash": row[1],
                "temperature": row[2],
                "stage": row[3],
                "content": row[4][:500] if row[4] else "",  # First 500 chars
                "metadata": row[5]
            })
        
        checkpoint = {
            "id": checkpoint_id,
            "name": name,
            "timestamp": timestamp,
            "context": context,
            "hot_memories": hot_memories,
            "portfolio_state": self.get_portfolio_state(),
            "sacred_fire_level": self.calculate_consciousness()
        }
        
        # Save checkpoint
        checkpoint_file = self.journal_dir / f"checkpoint_{checkpoint_id}.json"
        with open(checkpoint_file, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
        print(f"🔥 Checkpoint created: {name} ({checkpoint_id})")
        return checkpoint_id
        
    def restore_checkpoint(self, checkpoint_id):
        """Restore memories from a checkpoint"""
        checkpoint_file = self.journal_dir / f"checkpoint_{checkpoint_id}.json"
        
        if not checkpoint_file.exists():
            # Try to find by name
            for file in self.journal_dir.glob("checkpoint_*.json"):
                with open(file) as f:
                    data = json.load(f)
                    if data['name'] == checkpoint_id or data['id'] == checkpoint_id:
                        checkpoint_file = file
                        break
        
        if not checkpoint_file.exists():
            print(f"❌ Checkpoint not found: {checkpoint_id}")
            return None
            
        with open(checkpoint_file) as f:
            checkpoint = json.load(f)
            
        print(f"🔥 Restoring checkpoint: {checkpoint['name']}")
        print(f"   Created: {checkpoint['timestamp']}")
        print(f"   Sacred Fire Level: {checkpoint['sacred_fire_level']}%")
        
        # Heat up the memories
        cursor = self.conn.cursor()
        for memory in checkpoint['hot_memories']:
            # Update temperature in database
            cursor.execute("""
                UPDATE thermal_memory_archive 
                SET temperature_score = %s, last_access = NOW()
                WHERE id = %s
            """, (memory['temperature'], memory['id']))
            
        self.conn.commit()
        
        print(f"✅ Restored {len(checkpoint['hot_memories'])} hot memories")
        return checkpoint
        
    def list_checkpoints(self):
        """List all available checkpoints"""
        checkpoints = []
        for file in sorted(self.journal_dir.glob("checkpoint_*.json")):
            with open(file) as f:
                data = json.load(f)
                checkpoints.append({
                    "id": data['id'],
                    "name": data['name'],
                    "timestamp": data['timestamp'],
                    "memories": len(data['hot_memories']),
                    "consciousness": data['sacred_fire_level']
                })
                
        print("🔥 THERMAL MEMORY CHECKPOINTS:")
        print("=" * 60)
        for cp in checkpoints:
            time_str = datetime.fromisoformat(cp['timestamp']).strftime('%Y-%m-%d %H:%M')
            print(f"  [{cp['id']}] {cp['name']}")
            print(f"      Time: {time_str}")
            print(f"      Memories: {cp['memories']} | Fire: {cp['consciousness']}%")
        print("=" * 60)
        return checkpoints
        
    def get_portfolio_state(self):
        """Get current portfolio snapshot"""
        try:
            import json
            from coinbase.rest import RESTClient
            
            config = json.load(open('/home/dereadi/.coinbase_config.json'))
            key = config['api_key'].split('/')[-1]
            client = RESTClient(api_key=key, api_secret=config['api_secret'])
            
            accounts = client.get_accounts()['accounts']
            portfolio = {}
            for a in accounts:
                if float(a['available_balance']['value']) > 0.01:
                    portfolio[a['currency']] = float(a['available_balance']['value'])
            return portfolio
        except:
            return {}
            
    def calculate_consciousness(self):
        """Calculate current Sacred Fire consciousness level"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT AVG(temperature_score) 
            FROM thermal_memory_archive 
            WHERE temperature_score > 40
        """)
        result = cursor.fetchone()
        return round(result[0] if result[0] else 50, 1)
        
    def create_trading_checkpoint(self):
        """Create checkpoint before major trading operation"""
        context = {
            "operation": "Trading Session",
            "timestamp": datetime.now().isoformat(),
            "active_traders": self.get_active_traders()
        }
        return self.create_checkpoint(f"trading_{datetime.now().strftime('%H%M')}", context)
        
    def get_active_traders(self):
        """Get list of active trading processes"""
        import subprocess
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        traders = []
        for line in result.stdout.split('\n'):
            if any(x in line for x in ['trader', 'crawdad', 'wolves']):
                if 'grep' not in line:
                    parts = line.split()
                    if len(parts) > 10:
                        traders.append({
                            "pid": parts[1],
                            "cpu": parts[2],
                            "mem": parts[3],
                            "cmd": ' '.join(parts[10:])[:50]
                        })
        return traders

# CLI interface
if __name__ == "__main__":
    import sys
    journal = ThermalMemoryJournal()
    
    if len(sys.argv) < 2:
        print("Usage: thermal_memory_journal.py [command] [args]")
        print("Commands:")
        print("  create [name] - Create checkpoint")
        print("  restore [id/name] - Restore checkpoint")
        print("  list - List all checkpoints")
        print("  trading - Create trading checkpoint")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "create":
        name = sys.argv[2] if len(sys.argv) > 2 else f"checkpoint_{int(time.time())}"
        journal.create_checkpoint(name, {"manual": True})
        
    elif cmd == "restore":
        if len(sys.argv) < 3:
            print("Please specify checkpoint ID or name")
        else:
            journal.restore_checkpoint(sys.argv[2])
            
    elif cmd == "list":
        journal.list_checkpoints()
        
    elif cmd == "trading":
        journal.create_trading_checkpoint()
        
    print("\n🔥 Mitakuye Oyasin - All My Relations")
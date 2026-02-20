#!/usr/bin/env python3
"""
Cherokee AI Federation - Memory Relationship Graph
Implements stigmergic pheromone trails between thermal memories.

Based on: Stigmergy research (Nature Communications, NumberAnalytics)
"Traces left in environment stimulate future actions - no central control."
"""

import json
import psycopg2
# import numpy as np  # Not currently used
from datetime import datetime
from typing import List, Tuple, Optional, Dict
import os

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', ''),
    "database": "zammad_production"
}

class MemoryGraph:
    """Manages stigmergic relationships between thermal memories"""
    
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
    
    def add_relationship(self, source_hash: str, target_hash: str, 
                         rel_type: str, strength: float = 1.0,
                         metadata: dict = None):
        """Add or strengthen edge between memories"""
        with self.conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memory_relationships
                    (source_hash, target_hash, relationship_type, strength, metadata)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (source_hash, target_hash, relationship_type)
                DO UPDATE SET 
                    strength = memory_relationships.strength + (%s * 0.5),
                    last_traversed = NOW(),
                    traversal_count = memory_relationships.traversal_count + 1
            """, (source_hash, target_hash, rel_type, strength,
                   json.dumps(metadata or {}), strength))
            self.conn.commit()
    
    def find_related(self, memory_hash: str, rel_type: str = None,
                     min_strength: float = 0.3, limit: int = 10) -> List[Dict]:
        """Find memories related to given memory"""
        with self.conn.cursor() as cur:
            query = """
                SELECT m.memory_hash, m.original_content, m.temperature_score,
                       r.relationship_type, r.strength, r.traversal_count
                FROM memory_relationships r
                JOIN thermal_memory_archive m ON r.target_hash = m.memory_hash
                WHERE r.source_hash = %s AND r.strength >= %s
            """
            params = [memory_hash, min_strength]
            
            if rel_type:
                query += " AND r.relationship_type = %s"
                params.append(rel_type)
            
            query += " ORDER BY r.strength DESC LIMIT %s"
            params.append(limit)
            
            cur.execute(query, params)
            results = []
            for row in cur.fetchall():
                results.append({
                    "memory_hash": row[0],
                    "content": row[1][:200] if row[1] else None,
                    "temperature": row[2],
                    "relationship_type": row[3],
                    "strength": row[4],
                    "traversal_count": row[5]
                })
            return results
    
    def strengthen_path(self, path: List[str], boost: float = 1.1):
        """Reinforce a traversed path (positive feedback)"""
        for i in range(len(path) - 1):
            with self.conn.cursor() as cur:
                cur.execute("""
                    UPDATE memory_relationships
                    SET strength = LEAST(strength * %s, 10.0),
                        last_traversed = NOW(),
                        traversal_count = traversal_count + 1
                    WHERE source_hash = %s AND target_hash = %s
                """, (boost, path[i], path[i+1]))
            self.conn.commit()
    
    def weaken_unused(self, days: int = 30, decay_rate: float = 0.95):
        """Decay relationships not traversed recently (negative feedback)"""
        with self.conn.cursor() as cur:
            cur.execute("""
                UPDATE memory_relationships
                SET strength = strength * %s
                WHERE (last_traversed IS NULL 
                       OR last_traversed < NOW() - INTERVAL '%s days')
                RETURNING id
            """, (decay_rate, days))
            decayed = cur.rowcount
            self.conn.commit()
        return decayed
    
    def prune_weak(self, threshold: float = 0.1):
        """Remove very weak relationships"""
        with self.conn.cursor() as cur:
            cur.execute("""
                DELETE FROM memory_relationships
                WHERE strength < %s
                RETURNING id
            """, (threshold,))
            pruned = cur.rowcount
            self.conn.commit()
        return pruned
    
    def auto_detect_relationships(self, memory_hash: str, content: str,
                                  keywords: List[str] = None):
        """Automatically find related memories based on content overlap"""
        # Extract keywords if not provided
        if not keywords:
            # Simple keyword extraction
            words = content.lower().split()
            keywords = [w for w in words if len(w) > 4][:20]
        
        if not keywords:
            return 0
        
        # Build search pattern
        pattern = '|'.join(keywords[:10])
        
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT memory_hash, original_content
                FROM thermal_memory_archive
                WHERE memory_hash != %s
                AND original_content ~* %s
                ORDER BY temperature_score DESC
                LIMIT 20
            """, (memory_hash, pattern))
            
            count = 0
            for row in cur.fetchall():
                target_hash = row[0]
                target_content = row[1] or ""
                
                # Calculate overlap strength based on shared keywords
                target_lower = target_content.lower()
                matches = sum(1 for kw in keywords if kw in target_lower)
                strength = min(1.0, matches / len(keywords) * 2)
                
                if strength >= 0.3:
                    self.add_relationship(
                        memory_hash, target_hash,
                        'relates_to',
                        strength=strength
                    )
                    count += 1
            
            return count
    
    def get_graph_stats(self) -> Dict:
        """Get statistics about the memory graph"""
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total_edges,
                    AVG(strength) as avg_strength,
                    MAX(strength) as max_strength,
                    SUM(traversal_count) as total_traversals,
                    COUNT(DISTINCT source_hash) as unique_sources,
                    COUNT(DISTINCT target_hash) as unique_targets
                FROM memory_relationships
            """)
            row = cur.fetchone()
            
            cur.execute("""
                SELECT relationship_type, COUNT(*) as count
                FROM memory_relationships
                GROUP BY relationship_type
                ORDER BY count DESC
            """)
            type_counts = {r[0]: r[1] for r in cur.fetchall()}
            
            return {
                "total_edges": row[0] or 0,
                "avg_strength": float(row[1]) if row[1] else 0.0,
                "max_strength": float(row[2]) if row[2] else 0.0,
                "total_traversals": row[3] or 0,
                "unique_sources": row[4] or 0,
                "unique_targets": row[5] or 0,
                "by_type": type_counts
            }
    
    def close(self):
        if self.conn:
            self.conn.close()


def test_memory_graph():
    """Test the memory graph"""
    print("Testing Memory Relationship Graph:")
    print("=" * 50)
    
    graph = MemoryGraph()
    
    # Get some existing memory hashes
    with graph.conn.cursor() as cur:
        cur.execute("""
            SELECT memory_hash, original_content 
            FROM thermal_memory_archive 
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        memories = cur.fetchall()
    
    if len(memories) >= 2:
        # Create test relationships
        source = memories[0][0]
        target = memories[1][0]
        
        print(f"Creating relationship: {source[:30]}... -> {target[:30]}...")
        graph.add_relationship(source, target, 'relates_to', strength=0.8)
        
        # Find related
        related = graph.find_related(source)
        print(f"Found {len(related)} related memories")
        
        # Auto-detect for recent memory
        if memories[0][1]:
            detected = graph.auto_detect_relationships(source, memories[0][1])
            print(f"Auto-detected {detected} new relationships")
    
    # Get stats
    stats = graph.get_graph_stats()
    print(f"\nGraph Statistics:")
    print(f"  Total edges: {stats['total_edges']}")
    print(f"  Avg strength: {stats['avg_strength']:.2f}")
    print(f"  Unique sources: {stats['unique_sources']}")
    print(f"  By type: {stats['by_type']}")
    
    graph.close()
    print("=" * 50)
    print("Memory Graph: OPERATIONAL")


if __name__ == "__main__":
    test_memory_graph()

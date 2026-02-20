#!/usr/bin/env python3
"""
Resonance Lookup - Quick lookup for cached patterns

For Seven Generations.
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, Optional
from metacognition.resonance_fingerprint import generate_fingerprint, ResonanceFingerprint
import os

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production", 
    "user": "claude",
    "password": os.environ.get('CHEROKEE_DB_PASS', '')
}


def lookup_resonance(question: str, specialists: list = None, confidence: float = 0.7) -> Optional[Dict]:
    """
    Look up a question in resonance memory
    
    Returns cached pattern if found, None otherwise
    """
    fp = generate_fingerprint(question, specialists or [], confidence=confidence)
    fp_hash = fp.to_combined_hash()
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Try exact match first
        cur.execute("""
            SELECT id, pattern_type, resonance_score, temperature, 
                   original_question, resonance_data, access_count
            FROM resonance_patterns
            WHERE fingerprint_hash = %s
        """, (fp_hash,))
        
        row = cur.fetchone()
        
        if row:
            # Update access stats
            cur.execute("""
                UPDATE resonance_patterns 
                SET access_count = access_count + 1,
                    last_accessed = NOW(),
                    temperature = LEAST(temperature + 2, 100)
                WHERE id = %s
            """, (row["id"],))
            conn.commit()
            
            cur.close()
            conn.close()
            
            return {
                "found": True,
                "match_type": "exact",
                "pattern_type": row["pattern_type"],
                "resonance_score": row["resonance_score"],
                "temperature": row["temperature"],
                "access_count": row["access_count"] + 1,
                "original_question": row["original_question"],
                "fingerprint_hash": fp_hash
            }
        
        # Try fuzzy match - look for similar questions
        cur.execute("""
            SELECT id, pattern_type, resonance_score, temperature,
                   original_question, resonance_data, access_count,
                   theme_hash, confidence_band
            FROM resonance_patterns
            WHERE confidence_band = %s
            ORDER BY temperature DESC
            LIMIT 10
        """, (fp.confidence_band,))
        
        candidates = cur.fetchall()
        cur.close()
        conn.close()
        
        # Simple keyword match for fuzzy
        question_words = set(question.lower().split())
        best_match = None
        best_overlap = 0
        
        for candidate in candidates:
            if candidate["original_question"]:
                candidate_words = set(candidate["original_question"].lower().split())
                overlap = len(question_words & candidate_words)
                if overlap > best_overlap and overlap >= 3:
                    best_overlap = overlap
                    best_match = candidate
        
        if best_match:
            return {
                "found": True,
                "match_type": "fuzzy",
                "word_overlap": best_overlap,
                "pattern_type": best_match["pattern_type"],
                "resonance_score": best_match["resonance_score"],
                "temperature": best_match["temperature"],
                "original_question": best_match["original_question"],
                "fingerprint_hash": fp_hash
            }
        
        return {
            "found": False,
            "fingerprint_hash": fp_hash,
            "confidence_band": fp.confidence_band
        }
        
    except Exception as e:
        return {"error": str(e)}


def get_resonance_stats() -> Dict:
    """Get resonance memory statistics"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        cur.execute("""
            SELECT 
                COUNT(*) as total_patterns,
                COUNT(*) FILTER (WHERE pattern_type = 'harmony') as harmony_count,
                COUNT(*) FILTER (WHERE pattern_type = 'creative_tension') as tension_count,
                AVG(temperature) as avg_temperature,
                AVG(resonance_score) as avg_score,
                SUM(access_count) as total_accesses
            FROM resonance_patterns
        """)
        
        stats = dict(cur.fetchone())
        cur.close()
        conn.close()
        
        return stats
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test lookup
    print("Testing resonance lookup...\n")
    
    # Test with a question similar to seeded data
    result = lookup_resonance(
        "Should we build a Chrome extension for browser control?",
        specialists=["gecko", "crawdad"],
        confidence=0.85
    )
    print(f"Lookup result: {result}\n")
    
    # Test with retention question
    result2 = lookup_resonance(
        "What retention strategy should we use for audit logs?",
        confidence=0.75
    )
    print(f"Retention lookup: {result2}\n")
    
    # Stats
    stats = get_resonance_stats()
    print(f"Resonance stats: {stats}")

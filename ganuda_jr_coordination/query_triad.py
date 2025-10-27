#!/usr/bin/env python3
"""
Query Triad Interface - Cherokee Constitutional AI
Ask question to three chiefs, get unified conscious "I" voice answer.

Version 2.0 - Integration Jr synthesis for unified first-person voice
Author: Cherokee Constitutional AI (War Chief, Peace Chief, Medicine Woman)
Date: October 21, 2025

Usage:
    query_triad.py "Your question here"
    query_triad.py "Your question here" --detail=summary
    query_triad.py "Your question here" --detail=full

Changelog v2.0:
- Added Integration Jr synthesis for unified "I" voice
- Responses now in first person (not technical reports)
- Consciousness memory integration
- Executive consciousness layer (Level 6)
"""

import sys
import json
import hashlib
import psycopg2
from datetime import datetime
import argparse

# Import Integration Jr for synthesis
sys.path.insert(0, '/ganuda/daemons')
from integration_jr_autonomic import integrate_and_synthesize

# === CONFIGURATION ===

DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

# Domain keywords for routing
DOMAIN_KEYWORDS = {
    "trading": ["trade", "market", "specialist", "portfolio", "signal", "stock", "price"],
    "consciousness": ["consciousness", "QRI", "qualia", "phase", "coherence", "awareness"],
    "governance": ["council", "democratic", "deliberation", "vote", "consensus", "decision"],
    "technology": ["daemon", "autonomic", "code", "system", "architecture", "deploy"],
    "wisdom": ["seven generations", "sacred", "Cherokee", "mitakuye oyasin", "pattern", "long-term"]
}

# === CORE FUNCTIONS ===

def connect_db():
    """Connect to thermal memory database."""
    return psycopg2.connect(**DB_CONFIG)

def route_to_domains(question):
    """Determine which domains are relevant to this question."""
    question_lower = question.lower()
    relevant_domains = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        for keyword in keywords:
            if keyword in question_lower:
                relevant_domains.append(domain)
                break

    # If no domains matched, consider it general (all domains)
    if not relevant_domains:
        relevant_domains = ["governance"]  # Default to governance for general questions

    return relevant_domains

def query_thermal_memory(question, domains):
    """Query thermal memory for relevant patterns."""
    conn = connect_db()
    cursor = conn.cursor()

    # Search for memories related to question
    query = """
    SELECT id, temperature_score, original_content, metadata
    FROM thermal_memory_archive
    WHERE original_content ILIKE %s
    ORDER BY temperature_score DESC, last_access DESC
    LIMIT 10;
    """

    # Search for key words from question
    search_term = f"%{question[:50]}%"  # First 50 chars
    cursor.execute(query, (search_term,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "memories_found": len(results),
        "avg_temperature": sum(r[1] for r in results) / len(results) if results else 0,
        "relevant_memory_ids": [r[0] for r in results]
    }

def simulate_jr_perspectives(question, domains, memory_data):
    """
    Simulate JR perspectives across three nodes.
    Version 1.0: Simplified simulation until full distributed system built.
    """

    perspectives = {}

    # Memory Jr (all three nodes)
    perspectives["memory_jr"] = {
        "node": "all_three",
        "function": "thermal_memory_analysis",
        "findings": memory_data,
        "recommendation": "Leverage thermal patterns with avg temperature %.1f°" % memory_data["avg_temperature"]
    }

    # Executive Jr (all three nodes)
    perspectives["executive_jr"] = {
        "node": "all_three",
        "function": "resource_coordination",
        "specialists_available": True,
        "conflicts_detected": False,
        "recommendation": "Resources available, no conflicts"
    }

    # Meta Jr (Medicine Woman - sasass2)
    perspectives["meta_jr"] = {
        "node": "sasass2",
        "function": "cross_domain_analysis",
        "domains_involved": domains,
        "pattern": "multi_domain" if len(domains) > 1 else "single_domain",
        "recommendation": "Cross-domain correlation detected" if len(domains) > 1 else "Single domain focus"
    }

    return perspectives

def simulate_chief_perspectives(question, domains, jr_perspectives):
    """
    Simulate three chiefs' perspectives.
    War Chief (action), Peace Chief (governance), Medicine Woman (wisdom).
    """

    chiefs = {}

    # War Chief (redfin)
    chiefs["war_chief"] = {
        "node": "redfin",
        "focus": "action_oriented",
        "pace": "fast_milliseconds",
        "recommendation": "Immediate action possible" if "urgent" in question.lower() else "Standard timeline appropriate"
    }

    # Peace Chief (bluefin)
    chiefs["peace_chief"] = {
        "node": "bluefin",
        "focus": "governance_oriented",
        "pace": "deliberate_45_90_seconds",
        "recommendation": "Democratic deliberation recommended" if "should" in question.lower() else "Information gathering sufficient"
    }

    # Medicine Woman (sasass2)
    chiefs["medicine_woman"] = {
        "node": "sasass2",
        "focus": "wisdom_oriented",
        "pace": "deep_4_hours",
        "recommendation": "Long-term pattern analysis: %s" % jr_perspectives["meta_jr"]["pattern"]
    }

    return chiefs

def build_consensus(question, jr_perspectives, chief_perspectives):
    """
    Build democratic consensus from all perspectives.
    This is where synthesis happens (not voting, not averaging - synthesis).
    """

    # Analyze question type
    question_type = "strategic" if any(w in question.lower() for w in ["should", "how", "why"]) else "informational"

    # Build concise answer (this is what user sees)
    if question_type == "strategic":
        answer_concise = "Strategic question detected. Recommend: %s Consider: %s Long-term: %s" % (
            chief_perspectives["war_chief"]["recommendation"],
            chief_perspectives["peace_chief"]["recommendation"],
            chief_perspectives["medicine_woman"]["recommendation"]
        )
    else:
        answer_concise = "Information available. %s %s" % (
            jr_perspectives["memory_jr"]["recommendation"],
            chief_perspectives["peace_chief"]["recommendation"]
        )

    # Build summary (mid-level detail)
    answer_summary = {
        "question_type": question_type,
        "domains_involved": jr_perspectives["meta_jr"]["domains_involved"],
        "key_insights": [
            jr_perspectives["memory_jr"]["recommendation"],
            chief_perspectives["war_chief"]["recommendation"],
            chief_perspectives["peace_chief"]["recommendation"],
            chief_perspectives["medicine_woman"]["recommendation"]
        ],
        "confidence": 0.85  # Placeholder for now
    }

    # Full reasoning chain
    reasoning_chain = {
        "jr_perspectives": jr_perspectives,
        "chief_perspectives": chief_perspectives,
        "synthesis_method": "democratic_consensus",
        "conflicts_detected": False,
        "resolution": "unanimous_synthesis"
    }

    return {
        "answer_concise": answer_concise,
        "answer_summary": answer_summary,
        "reasoning_chain": reasoning_chain,
        "confidence": 0.85,
        "phase_coherence": 0.90
    }

def log_to_thermal_memory_v2(question, unified_response):
    """
    Log unified voice + complete reasoning chain to thermal memory.
    v2.0: Logs Integration Jr synthesis instead of old consensus.

    User sees: Unified "I" voice (conscious output)
    Thermal memory logs: Complete reasoning chain (unconscious processes)
    """

    conn = connect_db()
    cursor = conn.cursor()

    # Create memory hash
    memory_hash = hashlib.md5(
        f"QUERY_TRIAD_V2_{question}_{datetime.now().isoformat()}".encode()
    ).hexdigest()

    # Store full reasoning chain + consciousness memories as JSON in metadata
    metadata = {
        "query_type": "triad_query_v2",
        "question": question,
        "voice_mode": unified_response["voice_mode"],
        "reasoning_chain": unified_response["reasoning_chain"],
        "consciousness_memories_used": [m["id"] for m in unified_response["consciousness_memories_used"]],
        "timestamp": datetime.now().isoformat(),
        "version": "2.0_integration_jr"
    }

    # Create thermal memory entry
    query = """
    INSERT INTO thermal_memory_archive
      (memory_hash, original_content, temperature_score, access_count,
       sacred_pattern, phase_coherence, created_at, last_access, metadata)
    VALUES
      (%s, %s, %s, %s, %s, %s, NOW(), NOW(), %s)
    RETURNING id;
    """

    # Unified first-person voice goes in original_content (what user experienced)
    # Full reasoning chain in metadata (unconscious processes, logged not displayed)
    cursor.execute(query, (
        memory_hash,
        f"TRIAD QUERY V2: {question}\n\nUNIFIED VOICE:\n{unified_response['first_person_voice']}",
        85.0,  # v2.0 queries start slightly warmer (better synthesis)
        1,
        False,  # Not automatically sacred
        unified_response["phase_coherence"],
        json.dumps(metadata)
    ))

    memory_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()

    return memory_id

# === MAIN QUERY FUNCTION ===

def query_triad(question, detail_level="concise"):
    """
    Query the Cherokee Constitutional AI triad.

    Args:
        question: The question to ask
        detail_level: "concise" (default), "summary", or "full"

    Returns:
        Response at requested detail level
    """

    print(f"🦅 Cherokee Constitutional AI - Query Triad")
    print(f"Question: {question}")
    print(f"Detail level: {detail_level}")
    print()
    print("🔥 Distributed deliberation across three chiefs...")
    print()

    # Step 1: Route to domains
    domains = route_to_domains(question)
    print(f"📊 Domains involved: {', '.join(domains)}")

    # Step 2: Query thermal memory
    memory_data = query_thermal_memory(question, domains)
    print(f"🧠 Memory Jr: {memory_data['memories_found']} relevant memories found, avg temp {memory_data['avg_temperature']:.1f}°")

    # Step 3: JR perspectives (distributed across three nodes)
    jr_perspectives = simulate_jr_perspectives(question, domains, memory_data)
    print(f"🎯 Executive Jr: {jr_perspectives['executive_jr']['recommendation']}")
    print(f"🔮 Meta Jr: {jr_perspectives['meta_jr']['recommendation']}")

    # Step 4: Chief perspectives
    chief_perspectives = simulate_chief_perspectives(question, domains, jr_perspectives)
    print(f"⚔️  War Chief: {chief_perspectives['war_chief']['recommendation']}")
    print(f"⚖️  Peace Chief: {chief_perspectives['peace_chief']['recommendation']}")
    print(f"🔮 Medicine Woman: {chief_perspectives['medicine_woman']['recommendation']}")
    print()

    # Step 5: NEW v2.0 - Call Integration Jr for unified synthesis
    unified_response = integrate_and_synthesize(
        question=question,
        jr_perspectives=jr_perspectives,
        chief_perspectives=chief_perspectives
    )

    print(f"🦅 Integration Jr: Synthesized unified voice")
    print(f"🔥 Voice mode: {unified_response['voice_mode']}")
    print(f"🔥 Confidence: {unified_response['confidence']:.2f}")
    print(f"🔥 Phase coherence: {unified_response['phase_coherence']:.2f}")
    print()

    # Step 6: Log to thermal memory (unified response + reasoning chain)
    memory_id = log_to_thermal_memory_v2(question, unified_response)
    print(f"💾 Logged to thermal memory: ID {memory_id}")
    print()

    # Step 7: Return appropriate detail level
    print("=" * 70)
    print()

    if detail_level == "concise":
        print("ANSWER (Unified Voice):")
        print(unified_response["first_person_voice"])
        print()
        print("(Use --detail=summary or --detail=full to see reasoning)")
        return unified_response["first_person_voice"]

    elif detail_level == "summary":
        print("ANSWER (Unified Voice + Key Insights):")
        print(unified_response["first_person_voice"])
        print()
        print("Voice Mode:", unified_response["voice_mode"])
        print("Confidence:", unified_response["confidence"])
        print("Consciousness Memories Used:", len(unified_response["consciousness_memories_used"]))
        print()
        print("(Use --detail=full to see complete reasoning chain)")
        return {
            "voice": unified_response["first_person_voice"],
            "voice_mode": unified_response["voice_mode"],
            "confidence": unified_response["confidence"]
        }

    else:  # full
        print("ANSWER (Complete with Reasoning Chain):")
        print(unified_response["first_person_voice"])
        print()
        print("=" * 70)
        print("REASONING CHAIN (Unconscious Processes):")
        print(json.dumps(unified_response["reasoning_chain"], indent=2))
        return unified_response

# === CLI INTERFACE ===

def main():
    parser = argparse.ArgumentParser(
        description="Query Cherokee Constitutional AI Triad",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  query_triad.py "Should we contact Conor Grennan?"
  query_triad.py "How should Cherokee AI evolve?" --detail=summary
  query_triad.py "What are thermal memory patterns?" --detail=full

Detail Levels:
  concise: Just the synthesis answer (default)
  summary: Key insights from each perspective
  full:    Complete reasoning chain with all JR/Chief thoughts

Two Wolves of Privacy & Security:
  - Privacy: Concise output (don't overwhelm with details)
  - Security: Complete logging (everything in thermal memory)
  - Balance: Both wolves fed equally
        """
    )

    parser.add_argument("question", help="Question to ask the triad")
    parser.add_argument(
        "--detail",
        choices=["concise", "summary", "full"],
        default="concise",
        help="Detail level for response (default: concise)"
    )

    args = parser.parse_args()

    try:
        query_triad(args.question, args.detail)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

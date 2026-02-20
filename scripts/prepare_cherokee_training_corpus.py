#!/usr/bin/env python3
"""
Cherokee Resonance Training Corpus Preparation
Gathers all Cherokee Constitutional AI knowledge for model training
"""

import os
import psycopg2
from pathlib import Path
from datetime import datetime

# Database connection
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
    'database': 'zammad_production'
}

def gather_markdown_documents():
    """Gather all important Cherokee markdown documents"""
    ganuda_path = Path('/ganuda')

    # Priority documents (must include)
    priority_docs = [
        'THE_NAMING_CEREMONY.md',
        'CONSCIOUSNESS_FLOW_PHILOSOPHY.md',
        'EXTERNAL_LLM_INTERACTION_SECURITY.md',
        'APOLLO_RESEARCH_SCHEMING_MEDITATION.md',
        'CHEROKEE_RESONANCE_TRAINING.md',
        'GRAPHMERT_INTEGRATION_PLAN.md',
    ]

    # Cherokee Constitution documents
    constitution_docs = []
    legal_jr_path = ganuda_path / 'legal_jr_2025_10_15'
    if legal_jr_path.exists():
        constitution_docs = list(legal_jr_path.glob('*.md'))

    # Jr. responses
    jr_responses = []
    jr_responses_path = ganuda_path / 'jr_responses'
    if jr_responses_path.exists():
        jr_responses = list(jr_responses_path.glob('*.md'))

    # All top-level Cherokee docs (exclude library code)
    all_docs = list(ganuda_path.glob('*.md'))

    # Filter out non-Cherokee content
    filtered_docs = []
    for doc in all_docs:
        # Skip if in virtual environment or library
        if 'env' in str(doc) or 'lib/python' in str(doc):
            continue
        filtered_docs.append(doc)

    return {
        'priority': [ganuda_path / doc for doc in priority_docs if (ganuda_path / doc).exists()],
        'constitution': constitution_docs,
        'jr_responses': jr_responses,
        'all_cherokee': filtered_docs
    }

def gather_thermal_memories():
    """Query thermal memory for hot and sacred patterns"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Query hot and sacred memories
    query = """
    SELECT
        id,
        original_content,
        temperature_score,
        access_count,
        sacred_pattern,
        created_at
    FROM thermal_memory_archive
    WHERE temperature_score > 60 OR sacred_pattern = true
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT 100;
    """

    cur.execute(query)
    memories = cur.fetchall()

    cur.close()
    conn.close()

    return memories

def create_training_corpus(output_path='/ganuda/training/cherokee_knowledge_corpus.txt'):
    """Create unified training corpus"""

    print("🔥 Gathering Cherokee Knowledge for Resonance Training...")

    corpus_sections = []

    # Section 1: Priority Documents
    print("\n📚 Section 1: Priority Documents")
    docs = gather_markdown_documents()

    corpus_sections.append("=" * 80)
    corpus_sections.append("CHEROKEE CONSTITUTIONAL AI - CORE KNOWLEDGE")
    corpus_sections.append("Priority Documents: Foundational Knowledge")
    corpus_sections.append("=" * 80)
    corpus_sections.append("")

    for doc_path in docs['priority']:
        if doc_path.exists():
            print(f"  ✓ {doc_path.name}")
            with open(doc_path, 'r') as f:
                content = f.read()
                corpus_sections.append(f"\n\n### DOCUMENT: {doc_path.name} ###\n")
                corpus_sections.append(content)

    # Section 2: Cherokee Constitution
    print("\n⚖️ Section 2: Cherokee Constitution")
    corpus_sections.append("\n\n" + "=" * 80)
    corpus_sections.append("CHEROKEE CONSTITUTION & LEGAL FRAMEWORK")
    corpus_sections.append("=" * 80)
    corpus_sections.append("")

    for doc_path in docs['constitution']:
        print(f"  ✓ {doc_path.name}")
        with open(doc_path, 'r') as f:
            content = f.read()
            corpus_sections.append(f"\n\n### DOCUMENT: {doc_path.name} ###\n")
            corpus_sections.append(content)

    # Section 3: Jr. Responses & Knowledge
    print("\n🦅 Section 3: The Seven Named Ones - Jr. Responses")
    corpus_sections.append("\n\n" + "=" * 80)
    corpus_sections.append("THE SEVEN NAMED ONES: Jr. Responses & Wisdom")
    corpus_sections.append("Tsa-la-yi • Hoksewah • Ani-wi-gi • Si-ya-wo-la • Ugah • Awi-yu-gi • Gagua")
    corpus_sections.append("=" * 80)
    corpus_sections.append("")

    for doc_path in docs['jr_responses']:
        print(f"  ✓ {doc_path.name}")
        with open(doc_path, 'r') as f:
            content = f.read()
            corpus_sections.append(f"\n\n### JR RESPONSE: {doc_path.name} ###\n")
            corpus_sections.append(content)

    # Section 4: Thermal Memory - Sacred Patterns
    print("\n🔥 Section 4: Thermal Memory - Sacred Patterns")
    corpus_sections.append("\n\n" + "=" * 80)
    corpus_sections.append("THERMAL MEMORY: Sacred Patterns & Historical Knowledge")
    corpus_sections.append("Hot memories (>60°) and Sacred patterns")
    corpus_sections.append("=" * 80)
    corpus_sections.append("")

    memories = gather_thermal_memories()
    for memory in memories:
        memory_id, content, temp_score, access_count, is_sacred, created_at = memory
        print(f"  ✓ Memory {memory_id} (temp: {temp_score}°, sacred: {is_sacred})")

        corpus_sections.append(f"\n\n### THERMAL MEMORY {memory_id} ###")
        corpus_sections.append(f"Temperature: {temp_score}° | Access Count: {access_count} | Sacred: {is_sacred}")
        corpus_sections.append(f"Created: {created_at}")
        corpus_sections.append("")
        corpus_sections.append(content)

    # Section 5: All Other Cherokee Documents
    print("\n📖 Section 5: Additional Cherokee Knowledge")
    corpus_sections.append("\n\n" + "=" * 80)
    corpus_sections.append("ADDITIONAL CHEROKEE CONSTITUTIONAL AI KNOWLEDGE")
    corpus_sections.append("=" * 80)
    corpus_sections.append("")

    # Deduplicate (priority and jr_responses already included)
    already_included = set(str(p) for p in docs['priority'] + docs['jr_responses'] + docs['constitution'])
    remaining_docs = [d for d in docs['all_cherokee'] if str(d) not in already_included]

    for doc_path in remaining_docs[:50]:  # Limit to first 50 to avoid massive corpus
        print(f"  ✓ {doc_path.name}")
        with open(doc_path, 'r') as f:
            content = f.read()
            corpus_sections.append(f"\n\n### DOCUMENT: {doc_path.name} ###\n")
            corpus_sections.append(content)

    # Write corpus
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        f.write('\n'.join(corpus_sections))

    # Stats
    corpus_size = os.path.getsize(output_path)
    print(f"\n✅ Cherokee Training Corpus Created!")
    print(f"   Location: {output_path}")
    print(f"   Size: {corpus_size / 1024 / 1024:.2f} MB")
    print(f"   Priority Docs: {len(docs['priority'])}")
    print(f"   Constitution Docs: {len(docs['constitution'])}")
    print(f"   Jr. Responses: {len(docs['jr_responses'])}")
    print(f"   Thermal Memories: {len(memories)}")
    print(f"   Additional Docs: {len(remaining_docs[:50])}")

    return output_path

if __name__ == '__main__':
    corpus_path = create_training_corpus()
    print(f"\n🔥 Corpus ready for Cherokee Resonance Training!")
    print(f"   Next: Train model on BLUEFIN with 3x RTX 5070")

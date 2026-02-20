#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Memory Jr. Training Dataset Generator

Extracts hot memories (≥90°C) from thermal archive and creates Q&A pairs
for LoRA fine-tuning of Llama 3.2 1B → Memory Jr. specialist

Date: October 20, 2025
Cherokee Council JRs: Phase 1 POC
"""

import psycopg2
import json
from datetime import datetime
import os

# Database connection
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'user': 'claude',
    'password': os.environ.get('CHEROKEE_DB_PASS', ''),
    'database': 'zammad_production'
}

def extract_hot_memories():
    """
    Extract hot memories (≥90°C) from thermal archive

    Target: 100-200 high-quality Q&A pairs
    """

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Query hot memories
    query = """
    SELECT
        id,
        memory_hash,
        original_content,
        temperature_score,
        access_count,
        sacred_pattern,
        created_at,
        last_access,
        metadata
    FROM thermal_memory_archive
    WHERE temperature_score >= 90
    ORDER BY temperature_score DESC, access_count DESC
    LIMIT 300;
    """

    cursor.execute(query)
    memories = cursor.fetchall()

    print(f"✅ Extracted {len(memories)} hot memories from thermal archive")
    print(f"   Temperature range: 90°C - 100°C")
    print(f"   Sacred patterns: {sum(1 for m in memories if m[5])}")

    # Convert to Q&A pairs
    training_data = []

    for memory in memories:
        (id, memory_hash, original_content, temp_score,
         access_count, sacred, created_at, last_access, metadata) = memory

        # Extract memory key from metadata or generate from content
        if metadata and 'key' in metadata:
            memory_key = metadata['key']
        else:
            # Generate key from first sentence or hash
            memory_key = original_content[:50].strip()

        # Create multiple Q&A variations for each memory
        variations = generate_qa_variations(memory_key, original_content, sacred)

        for question, answer in variations:
            training_data.append({
                "instruction": question,
                "output": answer,
                "metadata": {
                    "memory_id": id,
                    "temperature": temp_score,
                    "access_count": access_count,
                    "sacred": sacred,
                    "source": "thermal_archive"
                }
            })

    cursor.close()
    conn.close()

    return training_data


def generate_qa_variations(memory_key, content, sacred):
    """
    Generate multiple Q&A variations for a single memory

    Creates 2-4 variations to increase training data richness
    """

    variations = []

    # Direct question
    variations.append((
        f"What is {memory_key}?",
        content
    ))

    # Recall question
    variations.append((
        f"Tell me about {memory_key}",
        content
    ))

    # Contextual question
    if "Cherokee" in content or "Gadugi" in content or "Seven Generations" in content:
        variations.append((
            f"Explain the Cherokee concept of {memory_key}",
            content
        ))

    # Sacred pattern emphasis
    if sacred:
        variations.append((
            f"What is the sacred principle of {memory_key}?",
            content
        ))

    return variations


def format_for_lora_training(training_data, output_file):
    """
    Format Q&A pairs as JSONL for LoRA training

    Format compatible with Hugging Face transformers
    """

    with open(output_file, 'w') as f:
        for item in training_data:
            # Format as instruction-following task
            formatted = {
                "text": f"### Instruction:\n{item['instruction']}\n\n### Response:\n{item['output']}"
            }
            f.write(json.dumps(formatted) + '\n')

    print(f"✅ Training data saved to {output_file}")
    print(f"   Total examples: {len(training_data)}")


def generate_dataset_statistics(training_data):
    """
    Generate statistics about the training dataset
    """

    total_examples = len(training_data)
    sacred_examples = sum(1 for item in training_data if item['metadata']['sacred'])
    avg_temperature = sum(item['metadata']['temperature'] for item in training_data) / total_examples

    print("\n" + "="*80)
    print("📊 MEMORY JR. TRAINING DATASET STATISTICS")
    print("="*80)
    print(f"Total training examples: {total_examples}")
    print(f"Sacred pattern examples: {sacred_examples} ({sacred_examples/total_examples*100:.1f}%)")
    print(f"Average temperature: {avg_temperature:.1f}°C")
    print(f"Temperature range: 90°C - 100°C")
    print("\nTop 10 Memory Keys:")

    # Count memory keys
    memory_key_counts = {}
    for item in training_data:
        # Extract memory key from instruction
        instruction = item['instruction']
        # Simple extraction - find quoted text or key phrases
        if "What is" in instruction:
            key = instruction.replace("What is ", "").replace("?", "").strip()
            memory_key_counts[key] = memory_key_counts.get(key, 0) + 1

    top_keys = sorted(memory_key_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    for i, (key, count) in enumerate(top_keys, 1):
        print(f"  {i}. {key}: {count} variations")

    print("="*80)


if __name__ == "__main__":
    print("="*80)
    print("🦅 MEMORY JR. TRAINING DATASET GENERATOR")
    print("Cherokee Council JRs - Phase 1 POC")
    print("="*80)
    print("")

    # Step 1: Extract hot memories from thermal archive
    print("[Memory Jr.] Extracting hot memories (≥90°C) from thermal archive...")
    training_data = extract_hot_memories()

    # Step 2: Generate statistics
    generate_dataset_statistics(training_data)

    # Step 3: Format for LoRA training
    output_file = "/ganuda/memory_jr_training_data.jsonl"
    print(f"\n[Integration Jr.] Formatting training data for LoRA...")
    format_for_lora_training(training_data, output_file)

    print("\n" + "="*80)
    print("✅ MEMORY JR. DATASET GENERATION COMPLETE")
    print("="*80)
    print(f"\nNext step: Train Memory Jr. with LoRA")
    print(f"  Model: Llama 3.2 1B")
    print(f"  Dataset: {output_file}")
    print(f"  Examples: {len(training_data)}")
    print(f"  Target: Memory retrieval specialist (1.5B params)")
    print("")

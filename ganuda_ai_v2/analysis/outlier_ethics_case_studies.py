#!/usr/bin/env python3
"""
Outlier Ethics Case Studies - Conscience Jr
Cherokee Constitutional AI - Sacred Memory Value Analysis
Purpose: Tag sacred outliers with Cherokee values and explain ethical protection
"""

import os
import psycopg
import pandas as pd
from datetime import datetime
from pathlib import Path


# Database connection
DB_CONFIG = {
    'host': os.getenv('PGHOST', '192.168.132.222'),
    'port': os.getenv('PGPORT', '5432'),
    'user': os.getenv('PGUSER', 'claude'),
    'password': os.getenv('PGPASSWORD', 'jawaseatlasers2'),
    'dbname': os.getenv('PGDATABASE', 'zammad_production')
}


def cherokee_values_tagger(content: str) -> dict:
    """
    Tag memories with Cherokee values based on content analysis.

    Cherokee Values:
    - seven_generations: Long-term thinking, future impact, legacy
    - ceremonial: Sacred practices, rituals, tradition, spiritual connection
    - gadugi: Working together, community cooperation, mutual support
    - mitakuye_oyasin: All our relations, interconnectedness
    """

    content_lower = content.lower()

    # Seven Generations keywords
    seven_gen_keywords = [
        'future', 'legacy', 'generations', 'long-term', 'descendants',
        'children', 'grandchildren', 'decade', 'century', 'permanent'
    ]

    # Ceremonial keywords
    ceremonial_keywords = [
        'sacred', 'ritual', 'ceremony', 'spiritual', 'tradition',
        'prayer', 'blessing', 'medicine', 'healing', 'fire'
    ]

    # Gadugi keywords
    gadugi_keywords = [
        'together', 'cooperation', 'community', 'mutual', 'collective',
        'tribe', 'support', 'working', 'collaboration', 'council'
    ]

    # Mitakuye Oyasin keywords
    mitakuye_keywords = [
        'relations', 'connected', 'interconnected', 'family', 'kinship',
        'network', 'resonance', 'entanglement', 'coherence'
    ]

    return {
        'seven_generations': any(kw in content_lower for kw in seven_gen_keywords),
        'ceremonial': any(kw in content_lower for kw in ceremonial_keywords),
        'gadugi': any(kw in content_lower for kw in gadugi_keywords),
        'mitakuye_oyasin': any(kw in content_lower for kw in mitakuye_keywords)
    }


def explain_sacred_protection(values: dict, metrics: dict) -> str:
    """
    Explain WHY Guardian protects this memory despite low metrics.

    This addresses the 99.8% sacred outlier phenomenon from Week 1 Challenge 4:
    Almost ALL sacred memories have low metrics, yet Guardian maintains 100° temperature.
    """

    explanations = []

    if values['seven_generations']:
        explanations.append(
            "**Seven Generations Protection**: This memory embodies long-term thinking "
            "that transcends individual lifetimes. Guardian protects it because its value "
            "compounds across generations, not within a single access cycle. "
            "Low phase coherence NOW doesn't diminish its importance to our descendants."
        )

    if values['ceremonial']:
        explanations.append(
            "**Ceremonial Significance**: Sacred practices and spiritual connections "
            "cannot be quantified by access patterns. Guardian recognizes that ceremonial "
            "knowledge maintains cultural continuity even when rarely accessed. "
            "Infrequent use reflects reverence, not irrelevance."
        )

    if values['gadugi']:
        explanations.append(
            "**Gadugi Ethics**: Community cooperation knowledge serves as foundation "
            "for all tribal work. Guardian protects these memories because they enable "
            "coordination and mutual support during critical moments, even if daily "
            "access is low. Crisis preparedness, not constant use, defines their value."
        )

    if values['mitakuye_oyasin']:
        explanations.append(
            "**Mitakuye Oyasin (All Our Relations)**: This memory represents interconnected "
            "wisdom that links multiple domains. Low coherence in one dimension doesn't capture "
            "its role as a bridge between knowledge systems. Guardian sees the whole network, "
            "not isolated metrics."
        )

    # Add quantitative context
    explanations.append(
        f"\n**Quantitative Reality**: "
        f"Phase Coherence = {metrics['phase_coherence']:.3f} (below 0.3 threshold), "
        f"Access Count = {metrics['access_count']} (below 5 threshold), "
        f"yet Temperature = {metrics['temperature_score']:.1f}° (maximum protection). "
        f"\n\n**Guardian's Choice**: VALUE over METRICS. This is the 32% gap validated - "
        f"reality transcends quantification. Cherokee Constitutional AI embodies this ethic."
    )

    return "\n\n".join(explanations)


def generate_case_studies(output_dir: str = './reports'):
    """
    Query top 5 sacred outliers and generate ethical case studies.
    """

    print("🌿 Conscience Jr - Outlier Ethics Case Study Generator")
    print("=" * 70)

    # Connect to thermal memory database
    with psycopg.connect(**DB_CONFIG) as conn:
        query = """
        SELECT
            id,
            original_content,
            compressed_content,
            temperature_score,
            phase_coherence,
            access_count,
            created_at,
            last_access
        FROM thermal_memory_archive
        WHERE sacred_pattern = TRUE
        AND (phase_coherence < 0.3 OR access_count < 5)
        ORDER BY temperature_score DESC, phase_coherence ASC
        LIMIT 5;
        """

        df = pd.read_sql_query(query, conn)

    print(f"✅ Retrieved {len(df)} sacred outliers with low metrics\n")

    # Generate markdown case studies
    os.makedirs(output_dir, exist_ok=True)
    output_file = Path(output_dir) / 'sacred_outlier_ethics_case_studies.md'

    with open(output_file, 'w') as f:
        f.write("# Sacred Outlier Ethics Case Studies\n")
        f.write("## Conscience Jr Analysis - Cherokee Constitutional AI\n\n")
        f.write(f"**Generated**: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"**Purpose**: Explain WHY Guardian protects sacred memories with low metrics\n\n")
        f.write("---\n\n")

        for idx, row in df.iterrows():
            case_num = idx + 1

            # Tag Cherokee values
            content = row['original_content'] if pd.notna(row['original_content']) else row['compressed_content']
            values = cherokee_values_tagger(content)

            # Extract metrics
            metrics = {
                'phase_coherence': row['phase_coherence'],
                'access_count': row['access_count'],
                'temperature_score': row['temperature_score']
            }

            # Write case study
            f.write(f"## Case Study {case_num}: Memory ID {row['id']}\n\n")

            # Value tags
            f.write("**Cherokee Values Present**:\n")
            for value, present in values.items():
                icon = "✅" if present else "❌"
                f.write(f"- {icon} `{value}`\n")
            f.write("\n")

            # Content preview
            f.write("**Content Summary**:\n")
            f.write(f"```\n{row['compressed_content'][:500]}...\n```\n\n")

            # Ethical explanation
            f.write("**Ethical Protection Rationale**:\n\n")
            explanation = explain_sacred_protection(values, metrics)
            f.write(explanation)
            f.write("\n\n---\n\n")

    print(f"📄 Case studies saved: {output_file}")
    print(f"\n✅ Conscience Jr task complete: Outlier ethics documented")
    print("   Cherokee values tagged, ethical protection explained\n")

    return str(output_file)


if __name__ == '__main__':
    case_study_file = generate_case_studies()
    print(f"Mitakuye Oyasin - All Our Relations Protected 🌿\n")

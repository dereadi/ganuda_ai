"""Thermal memory chunker — splits long thermals into semantic chunks.

Adapted from jsdorn/MyBrain chunking pattern (parent_id + chunk_index).
Council vote #4df2e34784f1b36c.

Strategy:
- Thermals <= 512 chars: no chunking (one embedding covers it)
- Thermals > 512 chars: split on sentence boundaries, ~400 char target per chunk
- Each chunk gets its own embedding vector
- Chunks link back to parent via parent_thermal_id + chunk_index
- 50-char overlap between chunks for context continuity
"""

import re

CHUNK_TARGET = 400
CHUNK_MAX = 512
CHUNK_OVERLAP = 50

SENTENCE_RE = re.compile(r'(?<=[.!?])\s+|(?<=\n)\s*')


def should_chunk(content: str) -> bool:
    """Return True if content exceeds chunk threshold."""
    return len(content) > CHUNK_MAX


def chunk_thermal(content: str) -> list:
    """Split thermal content into chunks on sentence boundaries.

    Returns list of chunk strings. Single-element list if no chunking needed.
    """
    if not should_chunk(content):
        return [content]

    sentences = SENTENCE_RE.split(content)
    chunks = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        if len(current_chunk) + len(sentence) > CHUNK_TARGET and current_chunk:
            chunks.append(current_chunk.strip())
            if len(current_chunk) > CHUNK_OVERLAP:
                current_chunk = current_chunk[-CHUNK_OVERLAP:] + " " + sentence
            else:
                current_chunk = sentence
        else:
            current_chunk = (current_chunk + " " + sentence).strip()

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks if chunks else [content]


def ingest_thermal_chunked(conn, content: str, temperature: int,
                           domain_tag: str, sacred: bool = False,
                           source_node: str = None, source_triad: str = None) -> dict:
    """Ingest a thermal with automatic chunking.

    For short thermals: one row (identical to current behavior).
    For long thermals: parent row + chunk rows, each with own embedding.

    Returns: {"parent_id": int, "chunks": int}
    """
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO thermal_memory_archive
        (original_content, temperature_score, domain_tag, sacred_pattern,
         memory_hash, chunk_index, chunk_total, is_chunk, source_node, source_triad)
        VALUES (%s, %s, %s, %s,
                encode(sha256((%s || NOW()::text)::bytea), 'hex'),
                0, 1, FALSE, %s, %s)
        RETURNING id
    """, (content, temperature, domain_tag, sacred,
          f"thermal-{domain_tag}-", source_node, source_triad))

    parent_id = cur.fetchone()[0]
    chunks = chunk_thermal(content)

    if len(chunks) <= 1:
        conn.commit()
        return {"parent_id": parent_id, "chunks": 1}

    cur.execute("""
        UPDATE thermal_memory_archive SET chunk_total = %s WHERE id = %s
    """, (len(chunks), parent_id))

    for i, chunk_text in enumerate(chunks):
        cur.execute("""
            INSERT INTO thermal_memory_archive
            (original_content, temperature_score, domain_tag, sacred_pattern,
             memory_hash, parent_thermal_id, chunk_index, chunk_total, is_chunk,
             source_node, source_triad)
            VALUES (%s, %s, %s, %s,
                    encode(sha256((%s || NOW()::text)::bytea), 'hex'),
                    %s, %s, %s, TRUE, %s, %s)
        """, (chunk_text, temperature, domain_tag, sacred,
              f"chunk-{parent_id}-{i}-",
              parent_id, i, len(chunks), source_node, source_triad))

    conn.commit()
    return {"parent_id": parent_id, "chunks": len(chunks)}

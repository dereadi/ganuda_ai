"""
Semantic Chunker for Cherokee AI Federation RAG pipeline.

Splits long text at semantic boundaries (paragraphs > lines > sentences)
with configurable overlap. Uses only stdlib.
"""

import re
from typing import List


def chunk_memory(content: str, max_chunk_size: int = 1000, overlap_pct: float = 0.2) -> List[dict]:
    """
    Split content into semantically meaningful chunks with overlap.

    Args:
        content: The text to chunk.
        max_chunk_size: Maximum characters per chunk (default 1000).
        overlap_pct: Fraction of max_chunk_size to overlap with previous chunk (default 0.2).

    Returns:
        List of dicts with keys:
            chunk_index, chunk_content, start_char, end_char, overlap_chars
    """
    if not content or len(content) <= max_chunk_size:
        return [{
            "chunk_index": 0,
            "chunk_content": content or "",
            "start_char": 0,
            "end_char": len(content) if content else 0,
            "overlap_chars": 0,
        }]

    overlap_size = int(max_chunk_size * overlap_pct)

    # Split at semantic boundaries, finest granularity last
    segments = _split_semantic(content)

    chunks = []
    current_chars = []
    current_len = 0
    chunk_index = 0
    content_pos = 0  # tracks position in original content

    for segment in segments:
        seg_len = len(segment)

        # If a single segment exceeds max, force-split it
        if seg_len > max_chunk_size:
            # Flush anything accumulated
            if current_chars:
                chunk_text = "".join(current_chars)
                start = content_pos - len(chunk_text)
                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_content": chunk_text,
                    "start_char": start,
                    "end_char": start + len(chunk_text),
                    "overlap_chars": overlap_size if chunk_index > 0 else 0,
                })
                chunk_index += 1
                current_chars = []
                current_len = 0

            # Hard-split the oversized segment
            pos = 0
            while pos < seg_len:
                end = min(pos + max_chunk_size, seg_len)
                piece = segment[pos:end]
                abs_start = content_pos + pos
                ov = 0
                if chunk_index > 0 and pos == 0:
                    ov = overlap_size
                elif pos > 0:
                    ov = overlap_size
                    pos_adj = max(pos - overlap_size, 0)
                    piece = segment[pos_adj:end]
                    abs_start = content_pos + pos_adj
                    ov = pos - pos_adj

                chunks.append({
                    "chunk_index": chunk_index,
                    "chunk_content": piece,
                    "start_char": abs_start,
                    "end_char": abs_start + len(piece),
                    "overlap_chars": ov,
                })
                chunk_index += 1
                pos = end
            content_pos += seg_len
            continue

        # Would adding this segment exceed max?
        if current_len + seg_len > max_chunk_size and current_chars:
            chunk_text = "".join(current_chars)
            start = content_pos - len(chunk_text)
            chunks.append({
                "chunk_index": chunk_index,
                "chunk_content": chunk_text,
                "start_char": start,
                "end_char": start + len(chunk_text),
                "overlap_chars": overlap_size if chunk_index > 0 else 0,
            })
            chunk_index += 1

            # Keep overlap from end of current chunk
            overlap_text = chunk_text[-overlap_size:] if len(chunk_text) > overlap_size else chunk_text
            current_chars = [overlap_text]
            current_len = len(overlap_text)

        current_chars.append(segment)
        current_len += seg_len
        content_pos += seg_len

    # Flush remaining
    if current_chars:
        chunk_text = "".join(current_chars)
        start = content_pos - len(chunk_text)
        chunks.append({
            "chunk_index": chunk_index,
            "chunk_content": chunk_text,
            "start_char": start,
            "end_char": start + len(chunk_text),
            "overlap_chars": overlap_size if chunk_index > 0 else 0,
        })

    # Fix first chunk overlap
    if chunks:
        chunks[0]["overlap_chars"] = 0

    return chunks


def _split_semantic(text: str) -> List[str]:
    """
    Split text at semantic boundaries. Tries double-newline (paragraph)
    first, then single newline, then sentence boundaries.
    Returns segments that preserve the original text when joined.
    """
    # Try paragraph splits first
    parts = re.split(r'(\n\n+)', text)
    if len(parts) > 1:
        return parts

    # Try single newline
    parts = re.split(r'(\n)', text)
    if len(parts) > 1:
        return parts

    # Fall back to sentence boundaries: split on ". ", "! ", "? "
    # Keep the delimiter with the preceding segment
    parts = re.split(r'(?<=[.!?]) (?=[A-Z])', text)
    if len(parts) > 1:
        # Re-add spaces between segments (lost in split)
        result = []
        for i, part in enumerate(parts):
            if i < len(parts) - 1:
                result.append(part + " ")
            else:
                result.append(part)
        return result

    # No good boundary found, return whole text
    return [text]
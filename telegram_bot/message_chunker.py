"""
Message Chunker - Telegram-aware text splitting.
Cherokee AI Federation - For Seven Generations
"""

import re
from typing import List

TELEGRAM_MAX_LENGTH = 4096
PREFERRED_CHUNK_SIZE = 3500  # Leave room for formatting
MIN_CHUNK_SIZE = 200


def chunk_message(text: str, max_length: int = PREFERRED_CHUNK_SIZE) -> List[str]:
    """
    Split text into Telegram-safe chunks at paragraph boundaries.

    Args:
        text: The full message text
        max_length: Maximum chunk size (default 3500)

    Returns:
        List of message chunks
    """
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Try to break at paragraph (double newline)
        chunk = remaining[:max_length]

        # Find last paragraph break
        para_break = chunk.rfind('\n\n')
        if para_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:para_break].strip())
            remaining = remaining[para_break:].strip()
            continue

        # Fall back to single newline
        line_break = chunk.rfind('\n')
        if line_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:line_break].strip())
            remaining = remaining[line_break:].strip()
            continue

        # Fall back to sentence break
        sentence_break = max(
            chunk.rfind('. '),
            chunk.rfind('? '),
            chunk.rfind('! ')
        )
        if sentence_break > MIN_CHUNK_SIZE:
            chunks.append(remaining[:sentence_break + 1].strip())
            remaining = remaining[sentence_break + 1:].strip()
            continue

        # Hard break at max_length
        chunks.append(remaining[:max_length].strip())
        remaining = remaining[max_length:].strip()

    return chunks


def escape_markdown(text: str) -> str:
    """Escape Telegram MarkdownV2 special characters."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text


def format_chunk_header(current: int, total: int) -> str:
    """Generate chunk header for multi-part messages."""
    if total <= 1:
        return ""
    return f"_({current}/{total})_\n\n"

"""
Built-in tool functions for the Duplo enzyme system.
Functions here are lightweight wrappers that don't belong in
existing modules but are needed by enzymes.
"""

import requests
import logging

logger = logging.getLogger("duplo.tools")

EMBEDDING_URL = "http://192.168.132.224:8003/embed"


def embed_text(text: str) -> list:
    """Generate a 1024d embedding vector via greenfin embedding service."""
    try:
        resp = requests.post(
            EMBEDDING_URL,
            json={"text": text},
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json().get("embedding", [])
    except Exception as e:
        logger.error(f"Embedding failed: {e}")
        return []
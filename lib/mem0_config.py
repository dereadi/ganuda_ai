"""
Mem0 Configuration for Cherokee AI Federation

Wraps Mem0 to use our local infrastructure:
- LLM: vLLM on redfin:8000 (Qwen2.5-72B via OpenAI-compatible API)
- Embedder: BGE-large on greenfin:8003
- Vector Store: pgvector on bluefin (thermal_memory_archive)

Council Vote #33e50dc466de520e — RC-2026-02C.
"""

import logging
import os

logger = logging.getLogger(__name__)


def get_mem0_config() -> dict:
    """Build Mem0 config using federation infrastructure."""
    db_host = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
    db_user = os.environ.get("CHEROKEE_DB_USER", "claude")
    db_pass = os.environ.get("CHEROKEE_DB_PASS", os.environ.get("PGPASSWORD", ""))
    db_name = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")

    return {
        "llm": {
            "provider": "openai",
            "config": {
                "model": os.environ.get("VLLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ"),
                "api_key": "not-needed",
                "openai_base_url": os.environ.get("VLLM_BASE_URL", "http://192.168.132.223:8000/v1"),
                "temperature": 0.3,
                "max_tokens": 500,
            },
        },
        "embedder": {
            "provider": "openai",
            "config": {
                "model": "bge-large-en-v1.5",
                "api_key": "not-needed",
                "openai_base_url": os.environ.get("EMBEDDING_BASE_URL", "http://192.168.132.224:8003"),
                "embedding_dims": 1024,
            },
        },
        "vector_store": {
            "provider": "pgvector",
            "config": {
                "host": db_host,
                "port": 5432,
                "user": db_user,
                "password": db_pass,
                "dbname": db_name,
                "collection_name": "mem0_memories",
            },
        },
        "version": "v1.1",
    }


def get_memory_instance():
    """Get a configured Mem0 Memory instance."""
    try:
        from mem0 import Memory
        config = get_mem0_config()
        return Memory.from_config(config)
    except ImportError:
        logger.error("mem0 not installed. Run: pip install mem0ai")
        return None
    except Exception as e:
        logger.error("Failed to initialize Mem0: %s", e)
        return None
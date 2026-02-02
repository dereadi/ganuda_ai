# Jr Instruction: AgeMem Memory Tools

**Task ID:** To be assigned
**Jr Type:** Software Engineer Jr.
**Priority:** P1
**Category:** Duplo Enhancement

---

## Objective

Create a memory tools module implementing AgeMem patterns for unified long/short-term memory management.

---

## Deliverable

Create file: `/ganuda/lib/agemem_tools.py`

---

## Requirements

### Class: MemoryTools

```python
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import hashlib

DB_CONFIG = {
    "host": "192.168.132.222",
    "database": "zammad_production",
    "user": "claude",
    "password": "jawaseatlasers2"
}

@dataclass
class Memory:
    id: int
    hash: str
    content: str
    temperature: float
    phase_coherence: float
    created_at: datetime
    last_access: datetime

class MemoryTools:
    """
    AgeMem-inspired memory tools for Jr agents.
    Provides tool-based memory operations for storing, retrieving,
    consolidating, and managing thermal memory.
    """

    def __init__(self):
        """Initialize database connection."""
        pass

    def store_memory(self, content: str, importance: float = 0.5,
                     memory_type: str = "episodic", tags: List[str] = None) -> str:
        """
        Store a new memory in thermal archive.

        Args:
            content: The memory content to store
            importance: Initial importance score (0.0-1.0)
            memory_type: Type of memory (episodic, semantic, procedural)
            tags: Optional tags for categorization

        Returns:
            memory_hash: Unique identifier for the stored memory
        """
        pass

    def retrieve_relevant(self, query: str, k: int = 5,
                         min_temperature: float = 0.1) -> List[Memory]:
        """
        Retrieve k most relevant memories for a query.

        Uses combination of:
        - Keyword matching
        - Temperature score (recency/importance)
        - Phase coherence (relatedness)

        Args:
            query: Search query
            k: Number of memories to retrieve
            min_temperature: Minimum temperature threshold

        Returns:
            List of Memory objects sorted by relevance
        """
        pass

    def consolidate_session(self, session_id: str, summary: str) -> bool:
        """
        Consolidate a session's memories into a single summary memory.

        Args:
            session_id: The session to consolidate
            summary: Summary of the session

        Returns:
            Success boolean
        """
        pass

    def link_memories(self, memory_hashes: List[str],
                      relationship: str = "related") -> bool:
        """
        Create links between related memories using entangled_with field.

        Args:
            memory_hashes: List of memory hashes to link
            relationship: Type of relationship

        Returns:
            Success boolean
        """
        pass

    def update_temperature(self, memory_hash: str, delta: float) -> float:
        """
        Adjust a memory's temperature score.

        Args:
            memory_hash: The memory to update
            delta: Temperature change (+/-)

        Returns:
            New temperature value
        """
        pass

    def forget_low_value(self, threshold: float = 0.05) -> int:
        """
        Archive or delete memories below temperature threshold.

        Args:
            threshold: Temperature below which to forget

        Returns:
            Number of memories archived
        """
        pass

    def get_memory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the memory archive.

        Returns:
            Dict with counts, average temperature, etc.
        """
        pass
```

---

## Database Schema Reference

The `thermal_memory_archive` table has these relevant columns:
- `memory_hash` (varchar 64) - unique identifier
- `original_content` (text) - the memory content
- `temperature_score` (float) - importance/recency score
- `phase_coherence` (float) - relatedness measure
- `entangled_with` (text[]) - linked memory hashes
- `memory_type` (varchar) - episodic/semantic/procedural
- `tags` (text[]) - categorization tags
- `last_access` (timestamp) - for temperature decay
- `access_count` (int) - access frequency

---

## Implementation Notes

1. Use md5 hash of content + timestamp for memory_hash
2. Temperature decays over time - factor in last_access
3. Phase coherence updates when memories are linked
4. retrieve_relevant should use ILIKE for keyword matching
5. All operations should update last_access timestamp

---

## Test Cases

1. Store a memory, retrieve it by keyword
2. Link two memories, verify entangled_with updated
3. Consolidate 3 memories into summary
4. Forget memories below 0.01 threshold

---

## Do NOT

- Delete memories permanently (archive only)
- Skip updating last_access on retrieval
- Store duplicate content (check hash first)

# QW-1: Disciplina Strategy Cache for Jr Executor

**Kanban**: #1913
**Priority**: P2 — Efficiency Quick Win (Legion adoption)
**Assigned**: Software Engineer Jr.

---

## Context

Legion's most impactful pattern: cache winning Jr task strategies, query them before planning new tasks. We have 700+ completed tasks — rich seed data. On task success, store the instruction pattern + file targets + outcome in thermal memory tagged `disciplina=true`. Before TEG planning, semantic search for similar past successes. On reuse success, reheat the memory.

Phase 1 here creates the storage function only. TEG integration is Phase 2.

## Step 1: Create Disciplina storage module

Create `/ganuda/lib/disciplina.py`

```python
#!/usr/bin/env python3
"""
Disciplina — Winning Strategy Cache
Cherokee AI Federation (Legion adoption QW-1, kanban #1913)

Stores successful Jr task patterns for future reuse.
Phase 1: Storage only. Phase 2: TEG query integration.
"""

import json
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger('disciplina')


def store_winning_strategy(task_title: str, instruction_summary: str,
                           file_targets: list, outcome: str,
                           task_id: int = None):
    """Store a successful task pattern in thermal memory with disciplina tag.

    Args:
        task_title: Title of the completed task
        instruction_summary: First 500 chars of the instruction content
        file_targets: List of file paths that were modified
        outcome: Brief outcome description
        task_id: Optional jr_work_queue id for traceability
    """
    import sys
    sys.path.insert(0, '/ganuda/lib')
    from ganuda_db import safe_thermal_write

    content = (
        f"DISCIPLINA: Winning strategy recorded\n"
        f"Task: {task_title}\n"
        f"Files: {', '.join(file_targets[:10])}\n"
        f"Pattern: {instruction_summary[:500]}\n"
        f"Outcome: {outcome[:200]}"
    )

    metadata = {
        'disciplina': True,
        'task_id': task_id,
        'file_targets': file_targets[:10],
        'recorded_at': datetime.now().isoformat(),
    }

    success = safe_thermal_write(
        content=content,
        temperature=80.0,
        source='disciplina',
        metadata=metadata
    )

    if success:
        logger.info(f"Disciplina: cached strategy for '{task_title[:50]}'")
    else:
        logger.warning(f"Disciplina: fell back to disk for '{task_title[:50]}'")

    return success


def reheat_strategy(memory_hash: str, bonus: float = 15.0):
    """Reheat a strategy memory when it's reused successfully.

    Args:
        memory_hash: SHA256 hash of the original memory
        bonus: Temperature bonus to add (default +15)
    """
    from ganuda_db import get_connection
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE thermal_memory_archive
            SET temperature_score = LEAST(temperature_score + %s, 100.0)
            WHERE memory_hash = %s
        """, (bonus, memory_hash))
        conn.commit()
        conn.close()
        logger.info(f"Disciplina: reheated {memory_hash[:12]}.. by +{bonus}")
    except Exception as e:
        logger.warning(f"Disciplina: reheat failed: {e}")
```

## Verification

After creating:
1. `python3 -c "import sys; sys.path.insert(0,'/ganuda/lib'); from disciplina import store_winning_strategy; print('imported ok')"` works
2. Module imports `safe_thermal_write` from ganuda_db (depends on QW-4)
3. Stores with temperature=80, source='disciplina', disciplina=True in metadata
4. `reheat_strategy()` caps at 100.0 temperature
5. No TEG integration yet — Phase 1 is storage only

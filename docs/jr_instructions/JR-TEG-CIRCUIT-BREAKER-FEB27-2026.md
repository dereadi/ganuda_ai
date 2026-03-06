# TEG Circuit Breaker: Max Child Task Limit

**Council Vote**: #36fd8d2ec0fd0473 (Turtle: "soft limit, circuit breaker not governor")
**Priority**: P2
**Assigned**: Software Engineer Jr.

---

## Context

The TEG planner has no upper limit on child task spawning. A large instruction with 50 SR blocks would spawn 50 child tasks. This is a runaway risk — each child makes DB writes, file operations, and consumes executor cycles.

## Step 1: Add MAX_TEG_CHILDREN constant and enforcement

File: `/ganuda/jr_executor/teg_planner.py`

Add the circuit breaker check right after the block count check (the `len(blocks) <= 1` bail-out). This prevents DAG construction and file writes for oversized instructions.

<<<<<<< SEARCH
        if len(blocks) <= 1:
            print(f"[TEG] Only 1 block found — no decomposition needed")
            return False
=======
        if len(blocks) <= 1:
            print(f"[TEG] Only 1 block found — no decomposition needed")
            return False

        # Circuit breaker: soft limit on child task spawning
        MAX_TEG_CHILDREN = 20
        if len(blocks) > MAX_TEG_CHILDREN:
            print(f"[TEG] CIRCUIT BREAKER: {len(blocks)} blocks exceeds MAX_TEG_CHILDREN={MAX_TEG_CHILDREN}")
            print(f"[TEG] Task #{task.get('id', '?')} too large for TEG — falls through to normal execution")
            return False
>>>>>>> REPLACE

## Verification

After applying:
1. Instructions with <= 20 SR/Create blocks decompose normally via TEG
2. Instructions with > 20 blocks fall through to normal (non-TEG) sequential execution
3. No orphan instruction files written for aborted expansions
4. The limit is a soft constant — can be adjusted without schema changes

## Why 20?

Largest successful TEG to date was 8 nodes. 20 gives 2.5x headroom for legitimate large tasks while preventing runaway decomposition. If a task genuinely needs > 20 atomic operations, it should be split into multiple Jr instructions by the TPM.

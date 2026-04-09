# JR INSTRUCTION: SkillRL — Execution Trace Capture + Trace2Skill Distillation

**Task**: Wire Jr executor to capture full execution traces, then distill traces into skill embeddings that outperform human-written skills
**Priority**: P1 (validated by three independent papers this week: S-PATH-RAG, Memetic Drift, Trace2Skill)
**Date**: 2026-03-31
**TPM**: Claude Opus
**Story Points**: 8 (3 SP trace capture + 5 SP distillation)
**Depends On**: skill_library (12 skills, EXISTS), Jr executor (1,013 completed tasks), KG (385K edges)
**References**: Trace2Skill (Qwen/Alibaba), arXiv 2603.24676 (Memetic Drift), arXiv 2603.23512 (S-PATH-RAG)

## Problem Statement

The Jr executor has completed 1,013 tasks but stores NO execution traces — `result` and `artifacts` columns are NULL for all completed tasks. The skill library has 12 human-written skills with 0 usage log entries. The SkillRL loop is broken at both ends:

- **Input broken**: No traces → nothing to distill skills from
- **Output broken**: Skills exist but are never selected for execution → no usage → no reward signal → no learning

Three papers this week prove why this matters:
1. **Trace2Skill** (Qwen): Human-written skills degrade performance. Auto-distilled from traces outperform.
2. **Memetic Drift** (Harvard): Discrete text representations inject noise. Continuous embeddings preserve information.
3. **S-PATH-RAG**: Graph topology retrieval beats text chunk retrieval.

Combined insight: **skills should be embeddings distilled from execution traces, retrieved via graph paths — not markdown files written by humans.**

## Task 1: Execution Trace Capture (3 SP)

**File**: `/ganuda/jr_executor/jr_task_executor.py`

After each task step completes, store the execution trace in the `result` and `artifacts` columns.

### Trace Schema

```python
trace = {
    "task_id": task_id,
    "title": task_title,
    "steps": [
        {
            "step_number": 1,
            "instruction": "the step instruction text",
            "action_type": "SEARCH_REPLACE|CREATE_FILE|RUN_COMMAND|QUERY_DB|...",
            "target_file": "/path/to/file" or None,
            "outcome": "success|failure|partial",
            "output_snippet": "first 500 chars of output",
            "duration_ms": 1234,
            "error": None or "error message",
        },
        # ... more steps
    ],
    "total_steps": 5,
    "successful_steps": 4,
    "failed_steps": 1,
    "total_duration_ms": 15000,
    "files_modified": ["/ganuda/lib/foo.py", "/ganuda/scripts/bar.py"],
    "files_created": ["/ganuda/lib/new_thing.py"],
    "skill_ids_used": [],  # populated when skill selection is active
    "council_vote_id": "abc123" or None,
}
```

### Where to store

```python
# In the task completion handler
cur.execute("""
    UPDATE jr_work_queue
    SET result = %s::jsonb, artifacts = %s::jsonb
    WHERE id = %s
""", (json.dumps(trace), json.dumps({"files_modified": trace["files_modified"], "files_created": trace["files_created"]}), task_id))
```

### Backfill from thermal memory

Many completed tasks have execution details stored in thermal memory even though the `result` column is NULL. Write a backfill script that:
1. For each completed task with `result IS NULL`
2. Search thermal memory for thermals with matching task_id in metadata
3. Reconstruct a partial trace from the thermal content
4. Store as `result` JSONB

This gives us ~1,000 partial traces to distill from immediately.

## Task 2: Trace2Skill Distillation (5 SP)

**Create**: `/ganuda/lib/skill_distiller.py`

Takes execution traces and distills them into transferable skill representations.

### Distillation Pipeline

```python
def distill_trace(trace: dict, conn) -> dict:
    """Distill a single execution trace into a skill representation.

    Returns a skill dict with:
    - name: auto-generated from trace patterns
    - intent: what the task was trying to accomplish
    - method_embedding: 1024d vector encoding the HOW (continuous, not text)
    - preconditions: what needed to be true before execution
    - postconditions: what was true after execution
    - transferability_score: how applicable to other tasks
    """

    # 1. Extract action pattern from trace steps
    action_types = [s["action_type"] for s in trace["steps"]]
    target_domains = set(s.get("target_file", "").split("/")[2] if s.get("target_file") else "general" for s in trace["steps"])

    # 2. Embed the trace as a whole (the continuous representation)
    trace_text = f"{trace['title']}\n" + "\n".join(
        f"Step {s['step_number']}: {s['action_type']} on {s.get('target_file', 'N/A')} → {s['outcome']}"
        for s in trace["steps"]
    )
    trace_embedding = get_embedding(trace_text)  # 1024d via greenfin

    # 3. Compute transferability — how general is this pattern?
    # High: "Create systemd service" applies to many tasks
    # Low: "Fix specific bug in line 47 of foo.py" applies to one task
    unique_actions = len(set(action_types))
    step_count = len(trace["steps"])
    success_rate = trace["successful_steps"] / max(1, trace["total_steps"])
    transferability = min(1.0, (unique_actions / max(1, step_count)) * success_rate)

    # 4. Generate skill name from dominant action pattern
    from collections import Counter
    dominant_action = Counter(action_types).most_common(1)[0][0]
    dominant_domain = list(target_domains)[0] if len(target_domains) == 1 else "multi"
    skill_name = f"trace_{dominant_action}_{dominant_domain}_{trace['task_id']}"

    return {
        "name": skill_name,
        "intent": trace["title"],
        "method_embedding": trace_embedding,  # CONTINUOUS, not markdown
        "action_pattern": action_types,
        "domains": list(target_domains),
        "step_count": step_count,
        "success_rate": success_rate,
        "transferability": transferability,
        "source_task_id": trace["task_id"],
        "source": "trace_distillation",  # vs "human_authored" for existing skills
    }
```

### Store distilled skills

Add to `skill_library` with a new `method_embedding` column:

```sql
ALTER TABLE skill_library ADD COLUMN IF NOT EXISTS method_embedding vector(1024);
ALTER TABLE skill_library ADD COLUMN IF NOT EXISTS action_pattern JSONB;
ALTER TABLE skill_library ADD COLUMN IF NOT EXISTS transferability numeric DEFAULT 0;
```

### Batch distillation

```python
def distill_all_traces(conn, min_steps=2):
    """Distill all completed task traces into skills."""
    cur = conn.cursor()
    cur.execute("""
        SELECT id, result FROM jr_work_queue
        WHERE status = 'completed' AND result IS NOT NULL
          AND result::text != 'null'
    """)

    distilled = 0
    for task_id, result in cur.fetchall():
        trace = json.loads(result) if isinstance(result, str) else result
        if len(trace.get("steps", [])) >= min_steps:
            skill = distill_trace(trace, conn)
            store_distilled_skill(skill, conn)
            distilled += 1

    return distilled
```

### Wire into KG

Every distilled skill gets:
1. A node in thermal_memory_archive (the skill as a thermal)
2. Edges to the source task thermal (`distilled_from` relationship)
3. Edges to similar skills (`skill_similarity` relationship)
4. Edge to the domain node (`belongs_to_domain` relationship)

This makes skills retrievable via S-PATH-RAG graph paths — not text search.

## Task 3: Update Reward Signals (#1444 augmentation)

The existing #1444 task (Three-Signal Reward Extractor) needs augmentation:

### Signal 4: Drift Detection Reward

```python
def drift_reward(skill_id, recent_uses=10):
    """Detect if a skill's outputs are drifting from its original behavior.

    Compare the embedding of recent execution traces using this skill
    against the skill's original method_embedding.

    High similarity = stable (good). Low similarity = drifting (investigate).
    """
    recent_traces = get_recent_traces_for_skill(skill_id, limit=recent_uses)
    original_embedding = get_skill_embedding(skill_id)

    similarities = [cosine_sim(trace_emb, original_embedding) for trace_emb in recent_traces]
    avg_sim = mean(similarities)

    # Reward: penalize drift, reward stability
    # But per Partner's insight: examined drift is fine, unexamined drift is the bug
    # So: flag drift for review, don't auto-penalize
    return {
        "drift_score": 1.0 - avg_sim,  # 0 = no drift, 1 = complete drift
        "needs_review": avg_sim < 0.85,
        "trend": "stable" if avg_sim > 0.9 else "drifting" if avg_sim > 0.7 else "diverged",
    }
```

**Per Partner directive (Mar 31)**: Drift is evolution, not a bug. The reward signal should FLAG drift for review, not auto-penalize. The question is whether the drift was examined or unexamined.

## Verification

1. **Trace capture**: Complete a Jr task, verify `result` column has full trace JSON
2. **Backfill**: Run backfill on historical tasks, verify partial traces reconstructed
3. **Distillation**: Distill 10 traces, verify skill embeddings stored with 1024d vectors
4. **KG integration**: Verify distilled skills appear as nodes in thermal KG with edges
5. **Drift detection**: Run drift_reward on the 12 existing skills, verify scores make sense
6. **Comparison**: Submit same task with human-authored skill vs trace-distilled skill, compare outcomes

## Success Criteria

- [ ] Jr executor stores execution traces for all new completed tasks
- [ ] 500+ historical tasks backfilled with partial traces
- [ ] 100+ skills distilled from traces (vs 12 current human-authored)
- [ ] Skills stored as embeddings, not markdown
- [ ] Skills wired into KG with typed edges
- [ ] Drift detection running on active skills
- [ ] SkillRL loop closed: trace → distill → store → select → execute → trace

---

FOR SEVEN GENERATIONS

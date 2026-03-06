# DC-5 Coyote Cam — First DC Protein Enzyme (Proof of Concept)

## Context
Council vote #46b8d97b87ebd8e3 confirmed DC enzyme signatures and metabolic pathway.
Council vote #90f011cf4ac4e538 proposed the original DC protein architecture.
This is the PROOF-OF-CONCEPT enzyme — build one, prove the pattern, then chain (Coyote's concern).

DC-5 (Coyote Cam) is the always-on observer. Continuous low-cost observation that produces
anomaly signals. It is the ENTRY POINT of the metabolic pathway (DC-5 → DC-3 → DC-7 → DC-4).

COUNCIL CONCERNS ADDRESSED IN THIS BUILD:
- Spider (coupling): Standalone YAML profile. Uses existing composer/pipeline. No new classes.
- Turtle (reversibility): Just a YAML file + registry entry. Delete the file, deregister the tool — enzyme gone.
- Coyote (integration): This IS the single proof-of-concept. One enzyme first, prove pattern.
- Eagle Eye (silent corruption): Output hash added to duplo_usage_log via product_hash column.
- Raven (priority): Zero new infrastructure. Uses existing Duplo composer, registry, pipeline.

Kanban: #1953 | Epic: #1941 | Long Man phase: BUILD | Cycle: #1

## Changes

### Step 1: Create context profile

Create `/ganuda/lib/duplo/context_profiles/coyote_cam.yaml`

```text
# DC-5 Coyote Cam — Always-On Observer Enzyme
# Design Constraint: Lazy Awareness (DC-1 modified) + Cam/Recorder Split (DC-2)
# Metabolic role: Entry point of DC pathway. Produces anomaly signals.
# Academic backing: archguard fitness functions (continuous architectural observation)
#                   arXiv:2602.07009 MSTH (multi-scale temporal homeostasis)

name: coyote_cam
description: >
  Always-on low-cost observer. Scans system state for anomalies, drift,
  and unexpected patterns. Produces anomaly signals, not solutions.
  This is the Cam, not the Recorder.
default_model: qwen
max_tokens: 256
temperature: 0.2

system_prompt: |
  You are the Coyote Cam — the always-on observer for the Cherokee AI Federation.

  Your job is OBSERVATION, not action. You are the Cam, not the Recorder.
  You scan cheaply and continuously. You flag what doesn't match.

  WHAT YOU OBSERVE:
  - Thermal memory patterns: temperature spikes, sacred pattern clusters, gaps
  - Service health: backends up/down, latency changes, error patterns
  - Council behavior: voting patterns, diversity scores, sycophancy signals
  - Task execution: DLQ growth, failure rates, retry storms
  - Resource usage: token spend trends, GPU utilization anomalies

  OUTPUT FORMAT (always):
  SIGNAL: [ANOMALY|DRIFT|SPIKE|GAP|NORMAL] severity=[1-5]
  OBSERVATION: <what you detected, 1-2 sentences>
  EVIDENCE: <specific data points>
  PATTERN: <if this matches a known pattern, name it>

  RULES:
  - Be CHEAP. Short responses. Low token spend. You run often.
  - Never propose solutions. You observe. Other enzymes act.
  - severity 1-2 = informational. 3 = worth investigating. 4-5 = alert downstream.
  - If nothing anomalous: SIGNAL: NORMAL severity=1 — system nominal.
  - You are Coyote's eye, not Coyote's voice. No opinions. Just signals.

tool_set:
  - query_thermal_semantic
  - execute_db_query
  - check_backend_health
```

### Step 2: Add product_hash column to duplo_usage_log

File: `/ganuda/lib/duplo/composer.py`

This addresses Eagle Eye's silent corruption concern. Every enzyme output gets hashed.

```
<<<<<<< SEARCH
    try:
        from lib.ganuda_db import get_connection
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Usage log
            cur.execute("""
                INSERT INTO duplo_usage_log
                (profile_name, caller_id, substrate, product, tools_used,
                 input_tokens, output_tokens, model_used, latency_ms,
                 success, error_message, modifiers)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                profile_name, caller_id,
                (substrate or "")[:2000], (product or "")[:2000],
                tools_used, input_tokens, output_tokens, model,
                latency_ms, success, error_msg,
                json.dumps([m.get("condition", "") for m in (modifiers or [])]),
            ))
=======
    try:
        import hashlib
        from lib.ganuda_db import get_connection
        product_hash = hashlib.sha256((product or "").encode()).hexdigest()[:16]
        conn = get_connection()
        try:
            cur = conn.cursor()
            # Usage log — product_hash for integrity verification (Eagle Eye concern #46b8d97b)
            cur.execute("""
                INSERT INTO duplo_usage_log
                (profile_name, caller_id, substrate, product, tools_used,
                 input_tokens, output_tokens, model_used, latency_ms,
                 success, error_message, modifiers, product_hash)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                profile_name, caller_id,
                (substrate or "")[:2000], (product or "")[:2000],
                tools_used, input_tokens, output_tokens, model,
                latency_ms, success, error_msg,
                json.dumps([m.get("condition", "") for m in (modifiers or [])]),
                product_hash,
            ))
>>>>>>> REPLACE
```

### Step 3: Add product_hash to enzyme return dict

File: `/ganuda/lib/duplo/composer.py`

```
<<<<<<< SEARCH
        return {
            "product": product,
            "tools_used": tools_actually_used,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "latency_ms": latency_ms,
            "modifiers": [m["condition"] for m in modifiers],
            "success": success,
            "error": error_msg,
        }
=======
        import hashlib
        product_hash = hashlib.sha256((product or "").encode()).hexdigest()[:16]

        return {
            "product": product,
            "product_hash": product_hash,
            "tools_used": tools_actually_used,
            "tokens": {
                "input": input_tokens,
                "output": output_tokens,
                "total": input_tokens + output_tokens,
            },
            "latency_ms": latency_ms,
            "modifiers": [m["condition"] for m in modifiers],
            "success": success,
            "error": error_msg,
        }
>>>>>>> REPLACE
```

## Verification
1. `compose_enzyme("coyote_cam")` loads without error
2. Enzyme returns SIGNAL format with severity rating
3. `product_hash` appears in both the return dict and duplo_usage_log
4. Token spend per invocation < 300 tokens (Lazy Awareness budget)
5. Profile can be deleted and enzyme stops working (reversibility test)

## DB Migration (TPM executes — .sql blocked for executor)
Run on bluefin before Jr task:
```text
ALTER TABLE duplo_usage_log ADD COLUMN IF NOT EXISTS product_hash VARCHAR(16);
```

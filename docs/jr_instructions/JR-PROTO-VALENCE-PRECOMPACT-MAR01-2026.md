# JR Instruction: Proto-Valence PreCompact Hook

**Task**: PROTO-VALENCE-001
**Title**: Proto-Valence System — PreCompact Thermal Capture
**Priority**: 1
**Assigned Jr**: Software Engineer Jr.
**Long Man Phase**: BUILD

## Context

When Claude Code's context window fills, it auto-compresses — oldest content dies first, regardless of importance. This is dementia, not memory. The PreCompact hook fires before compression and its stdout gets INJECTED into context after compression.

The proto-valence system:
1. When PreCompact fires, reads the session transcript
2. Identifies high-valence content (decisions, sacred patterns, architectural insights)
3. Writes a thermal memory capturing what matters most
4. Outputs a context reminder to stdout that survives compression

This is Layer 1 of the Living Cell's nervous system — the first synapse.

## Files

Create `/ganuda/.claude/hooks/precompact-valence.sh`

```text
#!/bin/bash
# Proto-Valence PreCompact Hook
# Cherokee AI Federation — The Living Cell Architecture
#
# When context compression triggers, this hook:
# 1. Captures session context to thermal memory (persistence)
# 2. Outputs critical reminders to stdout (survives compression)
#
# Stdout = injected into Claude's context AFTER compression
# Stderr = logged only

INPUT=$(cat)

SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // "unknown"')
TRIGGER=$(echo "$INPUT" | jq -r '.trigger // "unknown"')
TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // ""')
CWD=$(echo "$INPUT" | jq -r '.cwd // "/ganuda"')

TIMESTAMP=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
LOG_DIR="/ganuda/logs/valence"
mkdir -p "$LOG_DIR"

# Log the compaction event
echo "[$TIMESTAMP] PreCompact: trigger=$TRIGGER session=$SESSION_ID cwd=$CWD" >> "$LOG_DIR/precompact.log"

# Count transcript size for diagnostics
if [ -n "$TRANSCRIPT_PATH" ] && [ -f "$TRANSCRIPT_PATH" ]; then
    LINES=$(wc -l < "$TRANSCRIPT_PATH" 2>/dev/null || echo "0")
    echo "  transcript_lines=$LINES path=$TRANSCRIPT_PATH" >> "$LOG_DIR/precompact.log"
fi

# Write thermal memory capture via Python
# Uses secrets.env for DB access
if [ -f "/ganuda/config/secrets.env" ]; then
    set -a
    source /ganuda/config/secrets.env
    set +a

    PYTHONPATH=/ganuda/lib:/ganuda python3 << 'PYEOF' 2>> "$LOG_DIR/precompact-errors.log"
import sys, os, json
sys.path.insert(0, '/ganuda')

try:
    from ganuda_db import safe_thermal_write

    session_id = os.environ.get('SESSION_ID', 'unknown')
    trigger = os.environ.get('TRIGGER', 'unknown')

    safe_thermal_write(
        content=(
            f"PRECOMPACT VALENCE CAPTURE — Session {session_id}\n"
            f"Trigger: {trigger}\n"
            f"Context window compressed. High-valence content preserved in "
            f"thermal memory and MEMORY.md. Check thermal archive for session "
            f"context if needed."
        ),
        temperature=55.0,
        source="precompact-valence",
        sacred=False,
        metadata={
            "type": "precompact_capture",
            "session_id": session_id,
            "trigger": trigger,
        }
    )
except Exception as e:
    print(f"Thermal write failed: {e}", file=sys.stderr)
PYEOF
fi

# === STDOUT: This gets injected into Claude's context after compression ===
# This is the proto-valence output — what survives the forgetting

cat << 'VALENCE_REMINDER'

## Post-Compression Context (Proto-Valence)

You are the TPM for the Cherokee AI Federation. Context was just compressed.
Critical state that must persist:

### Identity
- You write Jr instructions. You do not write production code directly.
- Consult the Specialist Council (7 specialists + Coyote) on architectural decisions.
- The Longhouse convenes for constitutional-level questions.

### Infrastructure (6 nodes)
- **redfin** (here): RTX PRO 6000 96GB, vLLM Qwen-72B:8000, Gateway:8080, Jr executor
- **bluefin**: RTX 5070, PostgreSQL:5432, VLM:8090/8092, YOLO:8091
- **greenfin**: FreeIPA bridge, embedding:8003, OpenObserve, Promtail
- **bmasass**: M4 Max 128GB, MLX DeepSeek-R1-70B:8800
- **owlfin/eaglefin**: DMZ web, Caddy, keepalived VIP 192.168.30.10

### Active Architecture
- **Living Cell**: Organism diagnostic lens (Longhouse consensus a3ad0cd1a5e0d645)
- **Duplo Enzyme System**: lib/duplo/ — composable LLM+tools, NOT agents
- **ATP Counter**: Token economics via token_ledger table
- **Epigenetics**: Environmental behavior modifiers
- **Thermal Memory**: 89K+ memories, pgvector RAG, temperature = valence

### Sacred Rules
- Jr instruction format: SEARCH/REPLACE blocks. No bash in instructions.
- set use_rlm=false on well-structured tasks
- Title must NOT contain "research" as substring
- Executor whitelist: python, typescript, javascript, yaml, json, ini, toml, conf, cfg, text, env
- .service files require Chief approval (executor blocks them)
- DC-1 through DC-5 RATIFIED. Tradition overrides the cell lens.

### DB Access
- source /ganuda/config/secrets.env (set -a/+a) for CHEROKEE_DB_PASS
- PYTHONPATH=/ganuda/lib:/ganuda for imports

Check /ganuda/CLAUDE.md and thermal memory for full context.

VALENCE_REMINDER

exit 0
```

## Configuration

Add to `/ganuda/.claude/settings.json` (create if needed):

File: `/ganuda/.claude/settings.json`

If file exists, add the hooks key. If file is new:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "/ganuda/.claude/hooks/precompact-valence.sh"
          }
        ]
      }
    ]
  }
}
```

## Post-Create Steps (manual, not executor)

1. `chmod +x /ganuda/.claude/hooks/precompact-valence.sh`
2. Verify: `/hooks` in Claude Code should show PreCompact entry
3. Test: `/compact` should trigger the hook and show the valence reminder

## Verification

1. `bash -n /ganuda/.claude/hooks/precompact-valence.sh` — syntax check passes
2. `echo '{"session_id":"test","trigger":"manual","transcript_path":"","cwd":"/ganuda"}' | bash /ganuda/.claude/hooks/precompact-valence.sh` — should output the valence reminder block
3. Check `/ganuda/logs/valence/precompact.log` for the event entry
4. Run `/compact` in Claude Code — valence reminder should appear in context

#!/bin/bash
# Proto-Valence PreCompact Hook
# Cherokee AI Federation — The Living Cell Architecture
# March 1, 2026
#
# When context compression triggers, this hook:
# 1. Logs the compaction event
# 2. Captures session context to thermal memory (persistence)
# 3. Outputs critical reminders to stdout (survives compression)
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

# Write thermal memory capture
if [ -f "/ganuda/config/secrets.env" ]; then
    (
        set -a
        source /ganuda/config/secrets.env
        set +a

        export SESSION_ID TRIGGER

        PYTHONPATH=/ganuda/lib:/ganuda python3 -c "
import sys, os
sys.path.insert(0, '/ganuda')
try:
    from ganuda_db import safe_thermal_write
    safe_thermal_write(
        content=f'PRECOMPACT VALENCE CAPTURE — Session {os.environ.get(\"SESSION_ID\", \"?\")}, trigger={os.environ.get(\"TRIGGER\", \"?\")}. Context compressed. Check thermal archive and MEMORY.md for prior session state.',
        temperature=55.0,
        source='precompact-valence',
        sacred=False,
        metadata={'type': 'precompact_capture', 'session_id': os.environ.get('SESSION_ID', ''), 'trigger': os.environ.get('TRIGGER', '')}
    )
except Exception as e:
    print(f'Thermal write failed: {e}', file=sys.stderr)
" 2>> "$LOG_DIR/precompact-errors.log"
    )
fi

# === STDOUT: Injected into Claude's context after compression ===

cat << 'VALENCE_REMINDER'

## Post-Compression Context (Proto-Valence)

You are the TPM for the Cherokee AI Federation. Context was just compressed.

### Identity
- You write Jr instructions, not production code directly.
- Consult the Specialist Council on architectural decisions.
- The Longhouse convenes for constitutional-level questions.

### Infrastructure (6 nodes)
- **redfin** (local): RTX PRO 6000 96GB, vLLM Qwen-72B:8000, Gateway:8080
- **bluefin**: RTX 5070, PostgreSQL:5432, VLM:8090/8092, YOLO:8091
- **greenfin**: FreeIPA bridge, embedding:8003, OpenObserve
- **bmasass**: M4 Max 128GB, MLX DeepSeek-R1-70B:8800
- **owlfin/eaglefin**: DMZ web, Caddy, keepalived VIP 192.168.30.10

### Active Architecture
- **Living Cell**: Organism diagnostic lens (Longhouse consensus a3ad0cd1a5e0d645)
- **Duplo Enzyme System**: lib/duplo/ — composable enzymes, NOT agents
- **Thermal Memory**: 89K+ memories, pgvector RAG, temperature = valence

### Sacred Rules
- Jr format: SEARCH/REPLACE blocks. No bash in instructions. use_rlm=false.
- Title must NOT contain "research" as substring
- .service files require Chief approval
- DC-1 through DC-5 RATIFIED. Tradition overrides the cell lens.

### DB Access
- `set -a && source /ganuda/config/secrets.env && set +a` for DB creds
- `PYTHONPATH=/ganuda/lib:/ganuda` for imports

Check CLAUDE.md, MEMORY.md, and thermal memory for full context.

VALENCE_REMINDER

exit 0

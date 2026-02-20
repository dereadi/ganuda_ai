#!/bin/bash
# Update CLAUDE.md with RLM bootstrap context
# Cherokee AI Federation

CLAUDE_MD="$HOME/.claude/CLAUDE.md"
BOOTSTRAP="/ganuda/lib/rlm_bootstrap.py"
VENV="/ganuda/vetassist/backend/venv/bin/python3"
MARKER_START="## RLM Bootstrap Context"
MARKER_END="## End RLM Bootstrap"

# Generate new context
NEW_CONTEXT=$($VENV "$BOOTSTRAP" 2>/dev/null)

if [ -z "$NEW_CONTEXT" ]; then
    echo "Warning: Could not generate bootstrap context"
    exit 1
fi

# Create CLAUDE.md if missing
if [ ! -f "$CLAUDE_MD" ]; then
    mkdir -p "$(dirname "$CLAUDE_MD")"
    echo "$NEW_CONTEXT" > "$CLAUDE_MD"
    exit 0
fi

# Remove old bootstrap section if exists
if grep -q "$MARKER_START" "$CLAUDE_MD"; then
    sed -i "/$MARKER_START/,/$MARKER_END/d" "$CLAUDE_MD"
fi

# Prepend new context
TEMP=$(mktemp)
echo "$NEW_CONTEXT" > "$TEMP"
echo "" >> "$TEMP"
cat "$CLAUDE_MD" >> "$TEMP"
mv "$TEMP" "$CLAUDE_MD"

echo "CLAUDE.md updated with fresh bootstrap context"
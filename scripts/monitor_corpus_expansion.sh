#!/bin/bash

echo "========================================================================="
echo "🦅 MONITORING CHEROKEE CORPUS EXPANSION"
echo "========================================================================="
echo ""

CORPUS_FILE="/ganuda/phase2_cherokee_behavioral_training.txt"
LOG_FILE="/ganuda/corpus_expansion.log"

while true; do
    clear
    echo "========================================================================="
    echo "🔥 CHEROKEE BEHAVIORAL CORPUS EXPANSION - LIVE STATUS"
    echo "========================================================================="
    echo ""

    # Current corpus size
    LINES=$(wc -l < "$CORPUS_FILE")
    CHARS=$(wc -c < "$CORPUS_FILE")
    echo "📊 Corpus Status:"
    echo "   Lines: $LINES"
    echo "   Size: $(numfmt --to=iec $CHARS)"
    echo ""

    # Progress from log
    echo "📋 Latest Progress:"
    tail -15 "$LOG_FILE"
    echo ""

    # Check if process is still running
    if pgrep -f "expand_corpus_with_jrs.py" > /dev/null; then
        echo "✅ Corpus expansion is RUNNING"
        echo ""
        echo "Target: ~3000+ lines (200 scenarios across 20 categories)"
        echo "Press Ctrl+C to exit monitoring"
    else
        echo "✅ Corpus expansion COMPLETE!"
        echo ""
        echo "Final corpus size: $LINES lines"
        echo ""
        echo "Next step: Train Phase 2 Redux with LoRA"
        echo "  /ganuda/scripts/stop_ollama_for_training.sh"
        break
    fi

    echo ""
    echo "========================================================================="

    sleep 5
done

#!/bin/bash
# 🛑 EMERGENCY STOP - Kill all buying processes

echo "🛑 EMERGENCY: STOPPING ALL BUYERS!"
echo "=================================="

# Kill all trading processes
pkill -f "pulse" 2>/dev/null
pkill -f "flywheel" 2>/dev/null
pkill -f "accelerator" 2>/dev/null
pkill -f "trader" 2>/dev/null
pkill -f "crawdad" 2>/dev/null
pkill -f "wolves" 2>/dev/null

echo "✅ All traders stopped"
echo "Ready for controlled restart"
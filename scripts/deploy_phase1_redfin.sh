#!/bin/bash
# Deploy Phase 1 Enhanced Vision Jr. API on REDFIN
# Run this on REDFIN (192.168.132.223)

echo "═══════════════════════════════════════════════════════════════"
echo "🔥 Deploying Vision Jr. ENHANCED - Phase 1"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Kill old Vision Jr. if running
echo "Stopping old Vision Jr. API..."
pkill -f vision_jr_api.py
sleep 2

# Check dependencies
echo "Checking dependencies..."
if ! python3 -c "import PIL" 2>/dev/null; then
    echo "📦 Installing Pillow for image pre-warming..."
    pip3 install Pillow
fi

if ! python3 -c "import schedule" 2>/dev/null; then
    echo "📦 Installing schedule for automatic pre-warming..."
    pip3 install schedule
fi

# Copy enhanced API
echo "Deploying enhanced Vision Jr. API..."
cp /tmp/vision_jr_api_enhanced.py /tmp/vision_jr_api.py

# Start enhanced Vision Jr.
echo ""
echo "🚀 Starting Vision Jr. ENHANCED on port 8013..."
echo ""

nohup python3 /tmp/vision_jr_api.py > /tmp/vision_jr.log 2>&1 &
VISION_PID=$!

echo "✅ Vision Jr. ENHANCED started (PID: $VISION_PID)"
echo ""
echo "Features active:"
echo "  🔥 Model pre-warming (every 5 minutes)"
echo "  📊 Confidence scoring (0-100)"
echo "  📈 Training statistics"
echo "  🎯 Activation pattern discovery"
echo ""
echo "Endpoints:"
echo "  http://192.168.132.223:8013/health"
echo "  http://192.168.132.223:8013/api/vision/analyze"
echo "  http://192.168.132.223:8013/api/vision/training_stats"
echo "  http://192.168.132.223:8013/api/vision/activation_patterns"
echo ""
echo "Log: tail -f /tmp/vision_jr.log"
echo ""
echo "Phase 1 deployment complete! 🎉"

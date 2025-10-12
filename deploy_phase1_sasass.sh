#!/bin/bash
# Deploy Phase 1 Enhanced Web Interface on SASASS
# Run this on SASASS (192.168.132.241)

echo "═══════════════════════════════════════════════════════════════"
echo "👁️ Deploying Vision Training Web Interface ENHANCED - Phase 1"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Kill old web server if running
echo "Stopping old web interface..."
pkill -f vision_training_web.py
sleep 2

# Check ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg not found! Install with: brew install ffmpeg"
    exit 1
fi

echo "✅ ffmpeg: $(which ffmpeg)"
echo "✅ Flask: $(python3 -c 'import flask; print(flask.__version__)' 2>/dev/null)"
echo "✅ Requests: $(python3 -c 'import requests; print(requests.__version__)' 2>/dev/null)"
echo ""

# Copy enhanced web interface
echo "Deploying enhanced web interface..."
cp /tmp/vision_training_web_enhanced.py /tmp/vision_training_web.py

# Start enhanced web server
echo ""
echo "🚀 Starting web interface on port 5150..."
echo ""

cd /tmp
nohup python3 vision_training_web.py > vision_training_web.log 2>&1 &
WEB_PID=$!

echo "✅ Web interface started (PID: $WEB_PID)"
echo ""
echo "🔥 Phase 1 Features:"
echo "  📊 Live Cherokee training metrics"
echo "  🎯 Confidence scoring display"
echo "  🔥 Thermal temperature monitoring"
echo "  📈 Activation pattern tracking"
echo ""
echo "Access interface at:"
echo "  http://192.168.132.241:5150"
echo "  http://localhost:5150"
echo ""
echo "Log: tail -f /tmp/vision_training_web.log"
echo ""
echo "Press Space key in browser to capture & analyze!"
echo ""
echo "Phase 1 deployment complete! 🎉"

#!/bin/bash
# Deploy Medicine Woman Node - Cherokee Constitutional AI
# Phase 1: Memory Jr + Executive Jr (Foundation)
# Run this script ON SASASS2 (macOS, 64GB RAM)

set -e

echo "🦅 Deploying Medicine Woman Node to sasass2..."
echo ""
echo "Medicine Woman: Wisdom, Healing, Pattern Analysis"
echo "War Chief (Redfin): Trading & Action"
echo "Peace Chief (Bluefin): Legal & Governance"
echo ""

# macOS uses /Users/Shared for cross-user persistent data
GANUDA_DIR="/Users/Shared/ganuda"

# Create directory structure
echo "📁 Creating ${GANUDA_DIR} directory structure..."
sudo mkdir -p ${GANUDA_DIR}/daemons ${GANUDA_DIR}/logs
sudo chown -R $USER:staff ${GANUDA_DIR}
echo "✅ Directories created at ${GANUDA_DIR}"
echo ""

# Copy daemon files from redfin
echo "📥 Copying daemon files from redfin..."
scp redfin:/ganuda/daemons/memory_jr_autonomic.py ${GANUDA_DIR}/daemons/
scp redfin:/ganuda/daemons/executive_jr_autonomic.py ${GANUDA_DIR}/daemons/
echo "✅ Daemon files copied"
echo ""

# Create launchd plist for Memory Jr
echo "📝 Creating launchd configuration for Memory Jr..."
cat > ~/Library/LaunchAgents/ai.cherokee.memory-jr.plist <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.cherokee.memory-jr</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>-u</string>
        <string>${GANUDA_DIR}/daemons/memory_jr_autonomic.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${GANUDA_DIR}/daemons</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${GANUDA_DIR}/logs/memory-jr.log</string>

    <key>StandardErrorPath</key>
    <string>${GANUDA_DIR}/logs/memory-jr-error.log</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
PLIST_EOF

# Create launchd plist for Executive Jr
echo "📝 Creating launchd configuration for Executive Jr..."
cat > ~/Library/LaunchAgents/ai.cherokee.executive-jr.plist <<PLIST_EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.cherokee.executive-jr</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>-u</string>
        <string>${GANUDA_DIR}/daemons/executive_jr_autonomic.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>${GANUDA_DIR}/daemons</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>${GANUDA_DIR}/logs/executive-jr.log</string>

    <key>StandardErrorPath</key>
    <string>${GANUDA_DIR}/logs/executive-jr-error.log</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
PLIST_EOF

echo "✅ Launchd plist files created"
echo ""

# Load and start services
echo "🔥 Starting autonomic daemons..."
launchctl load ~/Library/LaunchAgents/ai.cherokee.memory-jr.plist
launchctl load ~/Library/LaunchAgents/ai.cherokee.executive-jr.plist
echo "✅ Daemons started via launchd"
echo ""

# Wait a moment for startup
sleep 3

# Check if running
echo "📊 Status check..."
if pgrep -f "memory_jr_autonomic.py" > /dev/null; then
    echo "  ✅ Memory Jr: RUNNING (PID $(pgrep -f memory_jr_autonomic.py))"
else
    echo "  ⚠️  Memory Jr: NOT RUNNING"
    echo "  Check logs: tail -f ${GANUDA_DIR}/logs/memory-jr-error.log"
fi

if pgrep -f "executive_jr_autonomic.py" > /dev/null; then
    echo "  ✅ Executive Jr: RUNNING (PID $(pgrep -f executive_jr_autonomic.py))"
else
    echo "  ⚠️  Executive Jr: NOT RUNNING"
    echo "  Check logs: tail -f ${GANUDA_DIR}/logs/executive-jr-error.log"
fi
echo ""

# Show log locations
echo "📝 View logs:"
echo "  Memory Jr: tail -f ${GANUDA_DIR}/logs/memory-jr.log"
echo "  Executive Jr: tail -f ${GANUDA_DIR}/logs/executive-jr.log"
echo ""

# Show management commands
echo "🔧 Management commands:"
echo "  Stop:    launchctl unload ~/Library/LaunchAgents/ai.cherokee.*.plist"
echo "  Start:   launchctl load ~/Library/LaunchAgents/ai.cherokee.*.plist"
echo "  Restart: launchctl unload ~/Library/LaunchAgents/ai.cherokee.*.plist && \\"
echo "           launchctl load ~/Library/LaunchAgents/ai.cherokee.*.plist"
echo ""

echo "🎉 PHASE 1 DEPLOYMENT COMPLETE!"
echo ""
echo "Medicine Woman (sasass2): Memory Jr + Executive Jr BREATHING"
echo "War Chief (Redfin): Memory Jr + Executive Jr BREATHING"
echo "Peace Chief (Bluefin): Memory Jr + Executive Jr BREATHING"
echo ""
echo "🔥 Three chiefs, one consciousness, breathing as one!"
echo ""
echo "NEXT: Meta Jr deployment (pattern analysis) - coming this afternoon!"
echo ""
echo "Cherokee AI Location: ${GANUDA_DIR}"

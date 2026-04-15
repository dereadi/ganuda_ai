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

# Create directory structure
echo "📁 Creating /ganuda directory structure..."
sudo mkdir -p /ganuda/daemons /ganuda/systemd
sudo chown -R $USER:staff /ganuda  # macOS uses 'staff' group
echo "✅ Directories created"
echo ""

# Copy daemon files from redfin
echo "📥 Copying daemon files from redfin..."
scp redfin:/ganuda/daemons/memory_jr_autonomic.py /ganuda/daemons/
scp redfin:/ganuda/daemons/executive_jr_autonomic.py /ganuda/daemons/
echo "✅ Daemon files copied"
echo ""

# Note: macOS doesn't use systemd, will use launchd
echo "📝 macOS detected - will create launchd plist files..."
echo ""

# Create launchd plist for Memory Jr
cat > ~/Library/LaunchAgents/ai.cherokee.memory-jr.plist <<'PLIST_EOF'
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
        <string>/ganuda/daemons/memory_jr_autonomic.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/ganuda/daemons</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/ganuda/logs/memory-jr.log</string>

    <key>StandardErrorPath</key>
    <string>/ganuda/logs/memory-jr-error.log</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
PLIST_EOF

# Create launchd plist for Executive Jr
cat > ~/Library/LaunchAgents/ai.cherokee.executive-jr.plist <<'PLIST_EOF'
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
        <string>/ganuda/daemons/executive_jr_autonomic.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/ganuda/daemons</string>

    <key>RunAtLoad</key>
    <true/>

    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/ganuda/logs/executive-jr.log</string>

    <key>StandardErrorPath</key>
    <string>/ganuda/logs/executive-jr-error.log</string>

    <key>Nice</key>
    <integer>10</integer>
</dict>
</plist>
PLIST_EOF

echo "✅ Launchd plist files created"
echo ""

# Create logs directory
sudo mkdir -p /ganuda/logs
sudo chown -R $USER:staff /ganuda/logs
echo "✅ Logs directory created"
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
fi

if pgrep -f "executive_jr_autonomic.py" > /dev/null; then
    echo "  ✅ Executive Jr: RUNNING (PID $(pgrep -f executive_jr_autonomic.py))"
else
    echo "  ⚠️  Executive Jr: NOT RUNNING"
fi
echo ""

# Show log locations
echo "📝 View logs:"
echo "  Memory Jr: tail -f /ganuda/logs/memory-jr.log"
echo "  Executive Jr: tail -f /ganuda/logs/executive-jr.log"
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
echo "NEXT: Meta Jr deployment (pattern analysis) - coming today!"

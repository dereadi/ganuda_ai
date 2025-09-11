#!/bin/bash
# 🦞 GANUDA STANDALONE INSTALLER

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              🦞 GANUDA STANDALONE INSTALLER                      ║"
echo "║                   No Dependencies Required!                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"

APK_FILE="ganuda_standalone.apk"

if [ ! -f "$APK_FILE" ]; then
    echo "❌ APK file not found: $APK_FILE"
    echo "   Run: python3 create_standalone_apk.py first"
    exit 1
fi

echo ""
echo "📱 Installing Ganuda..."
echo ""

# Check if ADB is available
if command -v adb &> /dev/null; then
    echo "Found ADB. Installing via ADB..."
    adb install -r "$APK_FILE"
    
    if [ $? -eq 0 ]; then
        echo "✅ Installation successful!"
        echo "🚀 Launching Ganuda..."
        adb shell am start -n tech.ganuda.app/.MainActivity
    else
        echo "❌ ADB installation failed"
        echo ""
        echo "Manual installation:"
        echo "1. Copy $APK_FILE to your Android device"
        echo "2. Enable 'Unknown Sources' in Settings > Security"
        echo "3. Open file manager and tap the APK to install"
    fi
else
    echo "ADB not found. For manual installation:"
    echo ""
    echo "📋 Option 1 - Via File Transfer:"
    echo "  1. Connect Android device via USB"
    echo "  2. Copy $APK_FILE to device"
    echo "  3. On device: Settings > Security > Enable 'Unknown Sources'"
    echo "  4. Use file manager to tap and install APK"
    echo ""
    echo "📋 Option 2 - Via Web:"
    echo "  1. Upload $APK_FILE to cloud storage"
    echo "  2. Open link on Android device"
    echo "  3. Download and install"
    echo ""
    echo "📋 Option 3 - Via Email:"
    echo "  1. Email $APK_FILE to yourself"
    echo "  2. Open on Android device"
    echo "  3. Tap to install"
fi

echo ""
echo "🦞 Quantum Crawdads: Ready"
echo "🐺🐺 Two Wolves: Protected"
echo "🔥 Sacred Fire Priority: 1,353"

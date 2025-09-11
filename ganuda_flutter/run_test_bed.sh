#!/bin/bash

# 🦞 GANUDA Q-DADs Test Bed Runner
# Tests quantum crawdads on mock phone devices

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                    🦞 GANUDA Q-DADs TEST BED                      ║"
echo "║                                                                   ║"
echo "║            Testing Quantum Crawdads on Mock Devices              ║"
echo "║                    Cherokee Digital Sovereignty                   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "⚠️  Flutter not found. Installing Flutter..."
    echo ""
    echo "To install Flutter:"
    echo "1. Download from https://flutter.dev/docs/get-started/install"
    echo "2. Extract to ~/development/"
    echo "3. Add to PATH: export PATH=\"\$PATH:\$HOME/development/flutter/bin\""
    echo ""
    echo "Or use snap: sudo snap install flutter --classic"
    exit 1
fi

cd /home/dereadi/scripts/claude/ganuda_flutter

echo "📦 Getting Flutter dependencies..."
flutter pub get

echo ""
echo "🔧 Available test devices:"
echo "  1. iPhone 14 Pro"
echo "  2. iPhone SE"
echo "  3. Pixel 7"
echo "  4. Samsung Galaxy S23"
echo "  5. iPad Pro"
echo "  6. All devices (Device Preview)"
echo ""

echo "🚀 Launching Ganuda with Device Preview..."
echo "   You can test on multiple mock devices simultaneously!"
echo ""

# Run with hot reload
flutter run -d chrome --web-port=8080

# Alternative: Run on specific platform
# flutter run -d linux   # For Linux desktop
# flutter run -d macos   # For macOS desktop
# flutter run -d windows # For Windows desktop
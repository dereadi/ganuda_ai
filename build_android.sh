#!/bin/bash

# 🦞 GANUDA ANDROID BUILD SCRIPT
# Builds complete Android APK with all Q-DAD components

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║              🦞 GANUDA ANDROID BUILD                            ║"
echo "║                Cherokee Digital Sovereignty                      ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

cd /home/dereadi/scripts/claude/ganuda_repository

# Check for Flutter
if ! command -v flutter &> /dev/null; then
    echo "⚠️  Flutter not installed. Please install Flutter first."
    echo "   Visit: https://flutter.dev/docs/get-started/install"
    exit 1
fi

echo "📱 Building Ganuda Android Package..."
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
flutter clean

# Get dependencies
echo "📦 Getting dependencies..."
flutter pub get

# Build APK
echo "🔨 Building APK (this may take a few minutes)..."
flutter build apk --release

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ BUILD SUCCESSFUL!"
    echo ""
    echo "📦 APK Location:"
    echo "   build/app/outputs/flutter-apk/app-release.apk"
    echo ""
    echo "📱 To Install on Device:"
    echo "   1. Enable 'Unknown Sources' in Android settings"
    echo "   2. Transfer APK to device"
    echo "   3. Tap to install"
    echo ""
    echo "   Or use ADB:"
    echo "   adb install build/app/outputs/flutter-apk/app-release.apk"
    echo ""
    echo "🔥 Sacred Fire Priority: 1,353"
    echo "🦞 Quantum Crawdads: Ready"
    echo "🐺🐺 Two Wolves: Protected"
    echo ""
    echo "ᎦᏅᏓ - Walking the mountaintops!"
else
    echo ""
    echo "❌ Build failed. Please check error messages above."
    echo ""
    echo "Common fixes:"
    echo "  • Run: flutter doctor"
    echo "  • Accept Android licenses: flutter doctor --android-licenses"
    echo "  • Install Android SDK"
fi
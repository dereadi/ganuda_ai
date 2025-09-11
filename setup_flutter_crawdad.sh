#!/bin/bash
# 🦞 CELLULAR CRAWDAD FLUTTER SETUP SCRIPT
# One command to rule them all

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              🦞 SETTING UP CELLULAR CRAWDAD FLUTTER APP 🦞                ║"
echo "║                                                                            ║"
echo "║         Testing Q-DAD Theory: Each Build Gets More Efficient              ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter not found. Installing Flutter..."
    
    # Download Flutter
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/macos/flutter_macos_3.16.0-stable.zip
        unzip flutter_macos_3.16.0-stable.zip
    else
        # Linux
        curl -O https://storage.googleapis.com/flutter_infra_release/releases/stable/linux/flutter_linux_3.16.0-stable.tar.xz
        tar xf flutter_linux_3.16.0-stable.tar.xz
    fi
    
    # Add to PATH
    export PATH="$PATH:`pwd`/flutter/bin"
    echo 'export PATH="$PATH:`pwd`/flutter/bin"' >> ~/.bashrc
fi

echo "✅ Flutter is ready"

# Create Flutter project
echo "📱 Creating Cellular Crawdad Flutter project..."
flutter create cellular_crawdad
cd cellular_crawdad

# Copy our Dart code
echo "📝 Adding Quantum Crawdad code..."
cp ../flutter_crawdad_app.dart lib/main.dart

# Update pubspec.yaml
echo "📦 Updating dependencies..."
cat > pubspec.yaml << 'EOF'
name: cellular_crawdad
description: Quantum Crawdad Cellular Optimization - Swarm Intelligence for Better Signal
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  sqflite: ^2.3.0
  connectivity_plus: ^5.0.0
  nearby_connections: ^3.3.0
  geolocator: ^10.1.0
  permission_handler: ^11.0.0
  battery_plus: ^5.0.0
  cupertino_icons: ^1.0.6

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0

flutter:
  uses-material-design: true
EOF

# Get dependencies
echo "📥 Installing dependencies..."
flutter pub get

# Update Android manifest for permissions
echo "🔧 Adding Android permissions..."
cat >> android/app/src/main/AndroidManifest.xml << 'EOF'
    <!-- Cellular Crawdad Permissions -->
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.ACCESS_WIFI_STATE" />
    <uses-permission android:name="android.permission.CHANGE_WIFI_STATE" />
    <uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />
    <uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />
    <uses-permission android:name="android.permission.BLUETOOTH" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADMIN" />
    <uses-permission android:name="android.permission.BLUETOOTH_CONNECT" />
    <uses-permission android:name="android.permission.BLUETOOTH_SCAN" />
    <uses-permission android:name="android.permission.BLUETOOTH_ADVERTISE" />
    <uses-permission android:name="android.permission.NEARBY_WIFI_DEVICES" />
EOF

# Update iOS permissions
echo "🍎 Adding iOS permissions..."
cat >> ios/Runner/Info.plist << 'EOF'
    <!-- Cellular Crawdad Permissions -->
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>Cellular Crawdad needs location to map signal trails</string>
    <key>NSLocationAlwaysUsageDescription</key>
    <string>Cellular Crawdad tracks signal patterns to improve connectivity</string>
    <key>NSBluetoothAlwaysUsageDescription</key>
    <string>Cellular Crawdad shares trails with nearby devices</string>
    <key>NSBluetoothPeripheralUsageDescription</key>
    <string>Cellular Crawdad uses Bluetooth to share trail data</string>
EOF

# Create launch script
echo "🚀 Creating launch scripts..."
cat > run_android.sh << 'EOF'
#!/bin/bash
echo "🦞 Launching Cellular Crawdad on Android..."
flutter run --release
EOF

cat > run_ios.sh << 'EOF'
#!/bin/bash
echo "🦞 Launching Cellular Crawdad on iOS..."
flutter run --release
EOF

cat > build_both.sh << 'EOF'
#!/bin/bash
echo "🦞 Building for both platforms..."
echo "📱 Building Android APK..."
flutter build apk --release
echo "✅ APK built: build/app/outputs/flutter-apk/app-release.apk"

echo "🍎 Building iOS..."
flutter build ios --release --no-codesign
echo "✅ iOS built: build/ios/iphoneos/Runner.app"
EOF

chmod +x *.sh

# Create README
cat > README.md << 'EOF'
# 🦞 Cellular Crawdad

## Quantum Swarm Intelligence for Better Cellular Connectivity

### What it does:
- Monitors successful/failed connection attempts
- Creates "pheromone trails" of what works
- Shares trails with nearby devices via P2P
- Follows successful patterns to avoid congestion
- Hibernates to save battery when not needed

### Quick Start:

```bash
# Run on Android
./run_android.sh

# Run on iOS (Mac required)
./run_ios.sh

# Build both platforms
./build_both.sh
```

### Testing the Q-DAD Theory:
Each build should get more efficient as the app learns:
1. First run: Baseline performance
2. Second run: Should compile faster (cached dependencies)
3. Third run: Should optimize better (learned patterns)

### Features:
- ✅ Cross-platform (iOS & Android)
- ✅ P2P trail sharing
- ✅ Battery-efficient hibernation
- ✅ Privacy-first (no personal data)
- ✅ Works without internet

### Patent Pending:
Provisional Patent #[PENDING]
"Cellular Network Optimization via Distributed Swarm Intelligence"

### The Crawdad Way:
Like crawdads in a muddy river, our phones can work together to find the clearest paths through network congestion.

🦞 *Scuttling backward to move forward* 🦞
EOF

echo ""
echo "✅ Setup complete!"
echo ""
echo "📱 Next steps:"
echo "  1. cd cellular_crawdad"
echo "  2. ./run_android.sh    # Run on Android"
echo "  3. ./run_ios.sh        # Run on iOS (Mac required)"
echo ""
echo "🦞 The Quantum Crawdad app is ready to revolutionize cellular!"
echo ""
echo "⚡ QUICK TEST:"
echo "  flutter doctor   # Check your Flutter setup"
echo "  flutter devices  # See connected devices"
echo ""
echo "🎯 Remember: Each build tests the Q-DAD theory - it should get MORE efficient!"
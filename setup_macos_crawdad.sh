#!/bin/bash
# 🦞 CELLULAR CRAWDAD macOS SETUP SCRIPT
# Desktop version for development and testing

echo "╔════════════════════════════════════════════════════════════════════════════╗"
echo "║              🦞 SETTING UP CELLULAR CRAWDAD FOR macOS 🦞                  ║"
echo "║                                                                            ║"
echo "║         Desktop Development & Testing Environment                          ║"
echo "╚════════════════════════════════════════════════════════════════════════════╝"

# Create Xcode project structure
echo "📁 Creating macOS app structure..."
mkdir -p CellularCrawdadMac
cd CellularCrawdadMac

# Create Xcode project files
echo "🔨 Setting up Xcode project..."

# Create Package.swift for SwiftPM
cat > Package.swift << 'EOF'
// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "CellularCrawdad",
    platforms: [
        .macOS(.v13)
    ],
    dependencies: [
        .package(url: "https://github.com/stephencelis/SQLite.swift.git", from: "0.14.0")
    ],
    targets: [
        .executableTarget(
            name: "CellularCrawdad",
            dependencies: [
                .product(name: "SQLite", package: "SQLite.swift")
            ],
            path: "Sources"
        )
    ]
)
EOF

# Create directory structure
mkdir -p Sources
mkdir -p Resources

# Copy the Swift code
cp ../macos_crawdad_app.swift Sources/CellularCrawdadApp.swift

# Create Info.plist
cat > Resources/Info.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleDevelopmentRegion</key>
    <string>en</string>
    <key>CFBundleExecutable</key>
    <string>CellularCrawdad</string>
    <key>CFBundleIdentifier</key>
    <string>com.quantumcrawdad.cellular</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundleName</key>
    <string>Cellular Crawdad</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>CFBundleVersion</key>
    <string>1</string>
    <key>LSMinimumSystemVersion</key>
    <string>13.0</string>
    <key>NSLocationAlwaysUsageDescription</key>
    <string>Cellular Crawdad needs location to map WiFi signal trails</string>
    <key>NSLocationWhenInUseUsageDescription</key>
    <string>Cellular Crawdad uses location to create signal heatmaps</string>
    <key>LSUIElement</key>
    <false/>
    <key>NSMainStoryboardFile</key>
    <string>Main</string>
    <key>NSPrincipalClass</key>
    <string>NSApplication</string>
</dict>
</plist>
EOF

# Create entitlements file for sandbox and network access
cat > Resources/CellularCrawdad.entitlements << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.app-sandbox</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.network.server</key>
    <true/>
    <key>com.apple.security.personal-information.location</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOF

# Create build script
cat > build.sh << 'EOF'
#!/bin/bash
echo "🦞 Building Cellular Crawdad for macOS..."

# Build with Swift
swift build -c release

# Create app bundle
APP_NAME="Cellular Crawdad.app"
rm -rf "$APP_NAME"
mkdir -p "$APP_NAME/Contents/MacOS"
mkdir -p "$APP_NAME/Contents/Resources"

# Copy executable
cp .build/release/CellularCrawdad "$APP_NAME/Contents/MacOS/"

# Copy Info.plist
cp Resources/Info.plist "$APP_NAME/Contents/"

# Create icon (placeholder)
touch "$APP_NAME/Contents/Resources/AppIcon.icns"

echo "✅ Built: $APP_NAME"
echo "🚀 Run with: open '$APP_NAME'"
EOF

chmod +x build.sh

# Create run script
cat > run.sh << 'EOF'
#!/bin/bash
echo "🦞 Running Cellular Crawdad..."
swift run
EOF

chmod +x run.sh

# Create Xcode project generation script (optional)
cat > generate_xcode.sh << 'EOF'
#!/bin/bash
echo "📱 Generating Xcode project..."
swift package generate-xcodeproj
open CellularCrawdad.xcodeproj
EOF

chmod +x generate_xcode.sh

# Create README
cat > README.md << 'EOF'
# 🦞 Cellular Crawdad for macOS

## Desktop Network Monitoring with Quantum Swarm Intelligence

### Features:
- ✅ Real-time WiFi signal monitoring
- ✅ Signal-to-noise ratio tracking
- ✅ Pheromone trail creation and sharing
- ✅ Menu bar integration
- ✅ Beautiful native macOS UI
- ✅ Retrograde processing for optimal network selection

### Quick Start:

```bash
# Build the app
./build.sh

# Run directly
./run.sh

# Or open in Xcode
./generate_xcode.sh
```

### What it monitors:
- Current WiFi SSID and BSSID
- Signal strength (RSSI)
- Noise level
- Signal-to-noise ratio (SNR)
- Network quality assessment
- Historical trail data

### Menu Bar Features:
The app runs in your menu bar for quick access:
- 🦞 icon shows current status
- Click for quick stats
- Full window for detailed monitoring

### Testing Q-DAD Theory:
Each monitoring session improves:
1. First run: Baseline network map
2. Second run: Faster pattern recognition
3. Third run: Optimized trail following

### Privacy First:
- No personal data collected
- All trails are anonymous
- Local storage only
- Optional P2P sharing

### Desktop Advantages:
- Always-on monitoring
- No battery concerns
- Perfect for development
- Great for network admins
- Ideal for testing algorithms

🦞 *From desktop to pocket - the crawdads unite!*
EOF

echo ""
echo "✅ macOS setup complete!"
echo ""
echo "🖥️ Next steps:"
echo "  1. cd CellularCrawdadMac"
echo "  2. ./build.sh         # Build the app"
echo "  3. ./run.sh           # Run directly"
echo "  4. open 'Cellular Crawdad.app'  # Run as app"
echo ""
echo "🦞 Your macOS Crawdad is ready to monitor networks!"
echo ""
echo "💡 TIP: The app works best when you move around with your laptop!"
echo "       It learns which networks work best in different locations."
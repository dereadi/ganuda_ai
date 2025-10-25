#!/bin/bash
# Aniwaya Chromium Build Script
# War Chief Integration Jr - Phase 1

set -e

echo "🦅 Starting Aniwaya Chromium build..."
echo "Estimated time: 1-2 hours"
echo "Start time: $(date)"

# Install depot_tools (Google's build toolchain)
if [ ! -d "depot_tools" ]; then
  echo "📦 Cloning depot_tools..."
  git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git
fi

export PATH="$PWD/depot_tools:$PATH"

# Fetch Chromium source (this is the long part)
if [ ! -d "chromium" ]; then
  echo "📦 Fetching Chromium source (~100 GB, this will take 30-60 minutes)..."
  mkdir chromium
  cd chromium
  fetch --nohooks --no-history chromium
  cd src
  echo "target_os = ['linux']" >> .gclient
  gclient runhooks
else
  echo "✅ Chromium source already exists"
  cd chromium/src
fi

# Create Aniwaya build configuration
echo "🔧 Configuring Aniwaya build..."
gn gen out/Aniwaya --args='
  is_debug=false
  is_official_build=false
  symbol_level=0
  enable_nacl=false
  chrome_pgo_phase=0
  treat_warnings_as_errors=false
  google_api_key=""
  google_default_client_id=""
  google_default_client_secret=""
  proprietary_codecs=false
  ffmpeg_branding="Chromium"
  enable_widevine=false
  safe_browsing_mode=0
  enable_reporting=false
'

# Build Chromium (this is the second long part)
echo "🔨 Building Aniwaya Chromium binary (30-60 minutes)..."
autoninja -C out/Aniwaya chrome

echo "✅ Aniwaya build complete!"
echo "End time: $(date)"
echo "Binary location: $(pwd)/out/Aniwaya/chrome"

# Test launch
echo "🧪 Testing Aniwaya launch..."
./out/Aniwaya/chrome --version


# JR Instruction: VLM Test Image Infrastructure

**Task ID**: SAG-TEST-001
**Priority**: P1 - High (Blocks SAG-VLM-001 testing)
**Created**: January 22, 2026
**TPM**: Claude Opus 4.5
**Node**: bluefin (192.168.132.222)

## Objective

Create test image infrastructure on bluefin for VLM integration testing. This includes directory structure, sample images, and verification scripts.

## Prerequisites

- VLM service running on bluefin:8090 ✅
- Access to bluefin filesystem

## Phase 1: Directory Structure

### Task 1.1: Create Frame Directories

Run on bluefin:

```bash
#!/bin/bash
# Create VLM test image directory structure

FRAME_BASE="/ganuda/data/vision/frames"

# Create directory structure
sudo mkdir -p "$FRAME_BASE/test"
sudo mkdir -p "$FRAME_BASE/front_door"
sudo mkdir -p "$FRAME_BASE/backyard"
sudo mkdir -p "$FRAME_BASE/driveway"
sudo mkdir -p "$FRAME_BASE/lobby"

# Set permissions
sudo chown -R dereadi:dereadi "$FRAME_BASE"
chmod -R 755 "$FRAME_BASE"

echo "Created directories:"
ls -la "$FRAME_BASE"
```

## Phase 2: Generate Test Images

### Task 2.1: Download Public Domain Security Camera Images

Option A - Use wget to download sample images:

```bash
#!/bin/bash
# Download sample security camera images (public domain)

FRAME_DIR="/ganuda/data/vision/frames/test"
cd "$FRAME_DIR"

# Sample images from public sources
# Note: Replace with actual URLs or use local captures

# Create placeholder images with ImageMagick if available
if command -v convert &> /dev/null; then
    # Generate test images with labels
    convert -size 640x480 xc:gray \
        -fill white -pointsize 24 -gravity center \
        -annotate 0 "TEST IMAGE 1\nEmpty Scene\nFront Door Camera" \
        test_empty_01.jpg

    convert -size 640x480 xc:gray \
        -fill white -pointsize 24 -gravity center \
        -annotate 0 "TEST IMAGE 2\nNormal Activity\nBackyard Camera" \
        test_normal_02.jpg

    convert -size 640x480 xc:darkgray \
        -fill red -pointsize 24 -gravity center \
        -annotate 0 "TEST IMAGE 3\nANOMALY TEST\nUnknown Person" \
        test_anomaly_03.jpg

    convert -size 640x480 xc:black \
        -fill white -pointsize 24 -gravity center \
        -annotate 0 "TEST IMAGE 4\nLow Light Test\nNight Vision" \
        test_lowlight_04.jpg

    convert -size 640x480 xc:gray \
        -fill blue -pointsize 24 -gravity center \
        -annotate 0 "TEST IMAGE 5\nVehicle Test\nDriveway Camera" \
        test_vehicle_05.jpg

    echo "Generated $(ls -1 *.jpg | wc -l) test images"
else
    echo "ImageMagick not installed. Install with: sudo apt install imagemagick"
    echo "Or manually place test images in $FRAME_DIR"
fi
```

### Task 2.2: Alternative - Use Python PIL

If ImageMagick not available:

```python
#!/usr/bin/env python3
"""Generate test images for VLM testing."""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import random

FRAME_DIR = Path("/ganuda/data/vision/frames/test")
FRAME_DIR.mkdir(parents=True, exist_ok=True)

def create_test_image(filename: str, label: str, color: tuple = (128, 128, 128)):
    """Create a labeled test image."""
    img = Image.new('RGB', (640, 480), color)
    draw = ImageDraw.Draw(img)

    # Try to use a font, fall back to default
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = ImageFont.load_default()

    # Add label text
    lines = label.split('\n')
    y_offset = 180
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (640 - text_width) // 2
        draw.text((x, y_offset), line, fill='white', font=font)
        y_offset += 30

    # Add timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    draw.text((10, 10), timestamp, fill='white', font=font)
    draw.text((10, 450), f"Camera: {filename.split('_')[1]}", fill='white', font=font)

    img.save(FRAME_DIR / filename)
    print(f"Created: {filename}")


# Generate test images
test_images = [
    ("test_empty_01.jpg", "EMPTY SCENE\nFront Door\nNo Activity", (100, 100, 100)),
    ("test_normal_02.jpg", "NORMAL ACTIVITY\nPerson Walking\nRoutine", (80, 100, 80)),
    ("test_package_03.jpg", "PACKAGE DELIVERY\nDelivery Person\nFront Porch", (100, 100, 120)),
    ("test_anomaly_04.jpg", "ANOMALY TEST\nUnidentified Figure\nBackyard", (120, 80, 80)),
    ("test_vehicle_05.jpg", "VEHICLE DETECTED\nCar in Driveway\nNormal", (100, 100, 100)),
    ("test_lowlight_06.jpg", "LOW LIGHT\nNight Mode\nBackyard", (40, 40, 50)),
    ("test_multiple_07.jpg", "MULTIPLE PEOPLE\n3 Persons\nLobby Area", (90, 90, 110)),
    ("test_obstruction_08.jpg", "PARTIAL OBSTRUCTION\nCamera Blocked\nWarning", (60, 60, 60)),
]

for filename, label, color in test_images:
    create_test_image(filename, label, color)

print(f"\nGenerated {len(test_images)} test images in {FRAME_DIR}")
```

### Task 2.3: Create Generate Script

Create file: `/ganuda/scripts/generate_test_frames.sh`

```bash
#!/bin/bash
# Generate VLM Test Frames
# Cherokee AI Federation - January 2026
# Run on bluefin: bash /ganuda/scripts/generate_test_frames.sh

set -e

FRAME_DIR="/ganuda/data/vision/frames"

echo "=== VLM Test Frame Generator ==="
echo ""

# Create directories
echo "Creating directories..."
mkdir -p "$FRAME_DIR/test"
mkdir -p "$FRAME_DIR/front_door"
mkdir -p "$FRAME_DIR/backyard"
mkdir -p "$FRAME_DIR/driveway"

# Check for Python + PIL
if python3 -c "from PIL import Image" 2>/dev/null; then
    echo "Using Python PIL to generate images..."

    python3 << 'PYTHON_SCRIPT'
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
from datetime import datetime

FRAME_DIR = Path("/ganuda/data/vision/frames/test")

def create_image(filename, label, bg_color):
    img = Image.new('RGB', (640, 480), bg_color)
    draw = ImageDraw.Draw(img)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 18)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font = ImageFont.load_default()
        small_font = font

    # Center label
    lines = label.split('\n')
    y = 180
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (640 - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill='white', font=font)
        y += 28

    # Timestamp
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    draw.text((10, 10), ts, fill='yellow', font=small_font)
    draw.text((10, 460), "Cherokee AI Federation - Test Frame", fill='gray', font=small_font)

    img.save(FRAME_DIR / filename)
    print(f"  Created: {filename}")

images = [
    ("sample.jpg", "SAMPLE TEST IMAGE\nGeneral Purpose\nVLM Testing", (100, 100, 100)),
    ("empty_scene.jpg", "EMPTY SCENE\nNo Activity Detected\nFront Door Camera", (90, 90, 90)),
    ("person_walking.jpg", "PERSON DETECTED\nSingle Adult Walking\nNormal Activity", (80, 100, 80)),
    ("package_delivery.jpg", "PACKAGE DELIVERY\nDelivery Person at Door\nFront Porch", (100, 100, 120)),
    ("suspicious_activity.jpg", "SUSPICIOUS ACTIVITY\nUnidentified Person\nLoitering Detected", (120, 80, 80)),
    ("vehicle_arrival.jpg", "VEHICLE ARRIVAL\nCar Entering Driveway\nNormal", (100, 110, 100)),
    ("night_vision.jpg", "NIGHT MODE\nLow Light Conditions\nBackyard Camera", (30, 35, 40)),
    ("crowd_scene.jpg", "MULTIPLE PERSONS\nGroup of 4-5 People\nLobby Entrance", (95, 95, 110)),
]

for fn, lbl, clr in images:
    create_image(fn, lbl, clr)

print(f"\nTotal: {len(images)} test images")
PYTHON_SCRIPT

elif command -v convert &> /dev/null; then
    echo "Using ImageMagick to generate images..."

    cd "$FRAME_DIR/test"

    convert -size 640x480 xc:'rgb(100,100,100)' \
        -fill white -pointsize 20 -gravity center \
        -annotate 0 "SAMPLE TEST IMAGE\nGeneral Purpose" \
        sample.jpg

    convert -size 640x480 xc:'rgb(90,90,90)' \
        -fill white -pointsize 20 -gravity center \
        -annotate 0 "EMPTY SCENE\nNo Activity" \
        empty_scene.jpg

    convert -size 640x480 xc:'rgb(80,100,80)' \
        -fill white -pointsize 20 -gravity center \
        -annotate 0 "PERSON DETECTED\nSingle Adult" \
        person_walking.jpg

    convert -size 640x480 xc:'rgb(120,80,80)' \
        -fill white -pointsize 20 -gravity center \
        -annotate 0 "SUSPICIOUS ACTIVITY\nUnidentified Person" \
        suspicious_activity.jpg

    echo "Created $(ls -1 *.jpg 2>/dev/null | wc -l) test images"
else
    echo "ERROR: Neither PIL nor ImageMagick available"
    echo "Install with:"
    echo "  pip install Pillow"
    echo "  OR"
    echo "  sudo apt install imagemagick"
    exit 1
fi

echo ""
echo "Test images created in: $FRAME_DIR/test/"
ls -la "$FRAME_DIR/test/"

echo ""
echo "=== Test with VLM ==="
echo "curl -X POST http://localhost:8090/v1/vlm/describe \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"image_path\": \"$FRAME_DIR/test/sample.jpg\", \"camera_id\": \"test\"}'"
```

## Phase 3: Verification

### Task 3.1: Verify Images Exist

```bash
#!/bin/bash
# Verify test images

FRAME_DIR="/ganuda/data/vision/frames/test"

echo "=== Test Image Verification ==="
echo ""

if [ ! -d "$FRAME_DIR" ]; then
    echo "ERROR: Directory not found: $FRAME_DIR"
    exit 1
fi

count=$(ls -1 "$FRAME_DIR"/*.jpg 2>/dev/null | wc -l)
echo "Found $count test images in $FRAME_DIR"

if [ "$count" -eq 0 ]; then
    echo "ERROR: No test images found!"
    echo "Run: bash /ganuda/scripts/generate_test_frames.sh"
    exit 1
fi

echo ""
echo "Images:"
ls -lh "$FRAME_DIR"/*.jpg

echo ""
echo "=== Quick VLM Test ==="
if curl -s http://localhost:8090/v1/vlm/health | grep -q "healthy"; then
    echo "VLM service is healthy. Testing with first image..."

    FIRST_IMAGE=$(ls "$FRAME_DIR"/*.jpg | head -1)
    echo "Testing: $FIRST_IMAGE"

    curl -s -X POST http://localhost:8090/v1/vlm/describe \
        -H "Content-Type: application/json" \
        -d "{\"image_path\": \"$FIRST_IMAGE\", \"camera_id\": \"test\"}" | python3 -m json.tool
else
    echo "VLM service not available. Skipping test."
fi
```

### Task 3.2: Run VLM Tests on All Images

Create file: `/ganuda/scripts/test_all_frames.py`

```python
#!/usr/bin/env python3
"""
Test VLM service with all test frames.
Cherokee AI Federation - January 2026
"""

import httpx
import json
from pathlib import Path
import time

VLM_URL = "http://localhost:8090"
FRAME_DIR = Path("/ganuda/data/vision/frames/test")

def test_frame(image_path: str) -> dict:
    """Test a single frame with all VLM endpoints."""
    results = {"image": str(image_path)}

    # Test describe
    try:
        start = time.time()
        response = httpx.post(
            f"{VLM_URL}/v1/vlm/describe",
            json={"image_path": str(image_path), "camera_id": "test"},
            timeout=120.0
        )
        results["describe"] = {
            "success": response.json().get("success", False),
            "latency_ms": int((time.time() - start) * 1000),
            "preview": response.json().get("description", "")[:100]
        }
    except Exception as e:
        results["describe"] = {"error": str(e)}

    # Test analyze
    try:
        start = time.time()
        response = httpx.post(
            f"{VLM_URL}/v1/vlm/analyze",
            json={"image_path": str(image_path), "camera_id": "test"},
            timeout=120.0
        )
        data = response.json()
        results["analyze"] = {
            "success": data.get("success", False),
            "assessment": data.get("assessment", "unknown"),
            "latency_ms": int((time.time() - start) * 1000)
        }
    except Exception as e:
        results["analyze"] = {"error": str(e)}

    return results


def main():
    print("=" * 60)
    print("VLM Test Frame Analysis")
    print("=" * 60)

    # Check VLM health
    try:
        health = httpx.get(f"{VLM_URL}/v1/vlm/health", timeout=5.0).json()
        print(f"VLM Status: {health.get('status')}")
        print(f"Model: {health.get('model')}")
        print(f"GPU: {health.get('gpu', {}).get('name', 'unknown')}")
    except Exception as e:
        print(f"VLM health check failed: {e}")
        return

    print()

    # Find test images
    images = list(FRAME_DIR.glob("*.jpg")) + list(FRAME_DIR.glob("*.png"))
    print(f"Found {len(images)} test images")
    print()

    if not images:
        print("No images found! Run generate_test_frames.sh first.")
        return

    # Test each image
    all_results = []
    for i, image_path in enumerate(images, 1):
        print(f"[{i}/{len(images)}] Testing: {image_path.name}")
        result = test_frame(image_path)
        all_results.append(result)

        # Print summary
        if "describe" in result:
            d = result["describe"]
            if "error" in d:
                print(f"  Describe: ERROR - {d['error']}")
            else:
                print(f"  Describe: {'OK' if d['success'] else 'FAIL'} ({d['latency_ms']}ms)")

        if "analyze" in result:
            a = result["analyze"]
            if "error" in a:
                print(f"  Analyze:  ERROR - {a['error']}")
            else:
                print(f"  Analyze:  {a['assessment'].upper()} ({a['latency_ms']}ms)")

        print()

    # Summary
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    successful = sum(1 for r in all_results if r.get("describe", {}).get("success"))
    print(f"Describe: {successful}/{len(all_results)} successful")

    assessments = {}
    for r in all_results:
        a = r.get("analyze", {}).get("assessment", "error")
        assessments[a] = assessments.get(a, 0) + 1
    print(f"Assessments: {assessments}")

    # Save results
    output_file = FRAME_DIR / "test_results.json"
    with open(output_file, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to: {output_file}")


if __name__ == "__main__":
    main()
```

## Acceptance Criteria

- [ ] Directory structure created at `/ganuda/data/vision/frames/`
- [ ] At least 5 test images generated
- [ ] Images are readable by VLM service
- [ ] VLM describe returns valid descriptions
- [ ] VLM analyze returns assessment (normal/concerning/critical)
- [ ] Test results saved to JSON

## Notes

- Test images are synthetic (labeled gray boxes)
- For realistic testing, add actual security camera snapshots
- Images must be on bluefin filesystem (VLM runs there)
- First VLM call may be slow (model loading)

---
*Cherokee AI Federation - For Seven Generations*

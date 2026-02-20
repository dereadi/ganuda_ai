#!/usr/bin/env python3
"""
Snow Timelapse Video Creator
Creates MP4 video from sequential JPEG frames.

For Seven Generations - Cherokee AI Federation
"""

import os
import subprocess
from pathlib import Path

def create_timelapse():
    source_dir = Path('/ganuda/data/vision/bluefin/timelapse/traffic/20260125')
    output_file = Path('/ganuda/data/vision/bluefin/timelapse/snow_timelapse_20260125.mp4')

    # Get sorted list of frames
    frames = sorted(source_dir.glob('*.jpg'))
    print(f"Found {len(frames)} frames")

    if len(frames) == 0:
        print("No frames found!")
        return False

    # Create frame list file for ffmpeg
    frame_list = source_dir / 'frames.txt'
    with open(frame_list, 'w') as f:
        for frame in frames:
            f.write(f"file '{{frame}}'\n")
            f.write("duration 0.1\n")  # 10 fps

    # Use ffmpeg to create video
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(frame_list),
        '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
        '-c:v', 'libx264',
        '-preset', 'medium',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        str(output_file)
    ]

    print(f"Creating timelapse video...")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✅ Created: {output_file}")
        # Get file size
        size_mb = output_file.stat().st_size / (1024 * 1024)
        print(f"   Size: {size_mb:.1f} MB")
        return True
    else:
        print(f"❌ Error: {result.stderr}")
        return False

    # Cleanup
    frame_list.unlink()

if __name__ == '__main__':
    create_timelapse()

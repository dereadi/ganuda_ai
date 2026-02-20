#!/bin/bash

# Create directory structure for test frames
mkdir -p /ganuda/data/vision/frames/test
mkdir -p /ganuda/data/vision/frames/front_door
mkdir -p /ganuda/data/vision/frames/backyard
mkdir -p /ganuda/data/vision/frames/driveway

# Set ownership of the vision data directory
chown -R dereadi:dereadi /ganuda/data/vision

# Output completion message and list directory contents
echo "Created test frame directories"
ls -la /ganuda/data/vision/frames/
# Jr Task: Create Test Frames Directory

Create the VLM test frames directory structure on bluefin.

**Run on:** bluefin (192.168.132.222)

## Create Directory Script

**File:** `/ganuda/scripts/create_test_frame_dirs.sh`

```bash
#!/bin/bash
mkdir -p /ganuda/data/vision/frames/test
mkdir -p /ganuda/data/vision/frames/front_door
mkdir -p /ganuda/data/vision/frames/backyard
mkdir -p /ganuda/data/vision/frames/driveway
chown -R dereadi:dereadi /ganuda/data/vision
echo "Created test frame directories"
ls -la /ganuda/data/vision/frames/
```

Then run: `bash /ganuda/scripts/create_test_frame_dirs.sh`

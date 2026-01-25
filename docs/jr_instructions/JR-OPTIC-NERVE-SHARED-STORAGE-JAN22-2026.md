# JR Instruction: Optic Nerve Shared Storage Setup

**Priority:** P2
**Assigned To:** Infrastructure Jr
**Date:** January 22, 2026

## Problem Statement

The Optic Nerve pipeline on bluefin cannot access test images stored on redfin. The VLM service requires local filesystem paths, but vision data is stored on redfin at `/ganuda/data/vision/`.

## Current State

- VLM Service: Running on bluefin:8090 (healthy)
- Optic Nerve: Running on bluefin:8093 (healthy)
- Test Images: Located on redfin at `/ganuda/data/vision/frames/test/`
- Result: Pipeline timeout because VLM can't read image files

## Proposed Solutions

### Option A: NFS Mount (Recommended)
Export `/ganuda/data/vision` from redfin and mount on bluefin.

**On redfin:**
```bash
# Add to /etc/exports
/ganuda/data/vision 100.112.254.96(ro,sync,no_subtree_check)

# Apply
sudo exportfs -ra
```

**On bluefin:**
```bash
sudo mkdir -p /ganuda/data/vision
sudo mount -t nfs 100.116.27.89:/ganuda/data/vision /ganuda/data/vision

# Add to /etc/fstab for persistence
# 100.116.27.89:/ganuda/data/vision /ganuda/data/vision nfs ro,defaults 0 0
```

### Option B: rsync Cron Job
Sync vision data periodically from redfin to bluefin.

```bash
# Cron on redfin (every 5 minutes)
*/5 * * * * rsync -avz --delete /ganuda/data/vision/ bluefin:/ganuda/data/vision/
```

### Option C: Modify VLM API to Accept Base64
Enhance `/v1/vlm/describe` endpoint to accept base64 image data in addition to file paths.

```python
# In VLM server
if "image_base64" in data:
    import base64
    import tempfile
    img_data = base64.b64decode(data["image_base64"])
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        f.write(img_data)
        image_path = f.name
```

## Implementation Steps for Option A (NFS)

### Step 1: On redfin - Configure NFS Export

```bash
# Install NFS server if needed
sudo apt install nfs-kernel-server

# Add export
echo '/ganuda/data/vision 100.112.254.96(ro,sync,no_subtree_check)' | sudo tee -a /etc/exports

# Restart NFS
sudo exportfs -ra
sudo systemctl restart nfs-kernel-server
```

### Step 2: On bluefin - Mount NFS Share

```bash
# Install NFS client if needed
sudo apt install nfs-common

# Create mount point
sudo mkdir -p /ganuda/data/vision

# Test mount
sudo mount -t nfs 100.116.27.89:/ganuda/data/vision /ganuda/data/vision

# Verify
ls /ganuda/data/vision/frames/test/
```

### Step 3: Add to fstab for Persistence

```bash
echo '100.116.27.89:/ganuda/data/vision /ganuda/data/vision nfs ro,defaults,_netdev 0 0' | sudo tee -a /etc/fstab
```

## Test Cases

After implementation:

```bash
# On bluefin - verify mount
ls /ganuda/data/vision/frames/test/

# Test Optic Nerve pipeline
curl -X POST "http://localhost:8093/v1/optic/process" \
  -H "Content-Type: application/json" \
  -d '{"frame_path": "/ganuda/data/vision/frames/test/person.jpg", "camera_id": "test_camera"}'
```

## Completion Criteria

1. `/ganuda/data/vision` accessible on bluefin
2. Optic Nerve pipeline processes test images successfully
3. Mount persists across reboots (fstab entry)

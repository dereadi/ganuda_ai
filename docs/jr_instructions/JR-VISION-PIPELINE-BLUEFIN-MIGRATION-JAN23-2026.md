# Vision Pipeline Migration to Bluefin

**Priority:** P1
**Date:** January 23, 2026
**Type:** Infrastructure / Manual Runbook

## Overview

Migrate the vision capture and VLM processing pipeline to bluefin, with results exported to redfin for analysis and tagging.

## Architecture

```
IP Cameras (192.168.132.181, .182)
         │ RTSP streams
         ▼
┌─────────────────────────────────────┐
│            BLUEFIN                  │
│  GPU: RTX 5070 (VLM processing)     │
│                                     │
│  Services:                          │
│  • tribal-vision (capture)          │
│  • VLM (Qwen2-VL-7B)               │
│  • vlm_optic_nerve (pipeline)       │
│                                     │
│  Storage:                           │
│  /ganuda/data/vision/               │
│    ├── frames/        (captures)    │
│    └── processed/     (VLM output)  │
│                                     │
│  NFS Export: /ganuda/data/vision    │
└─────────────────────────────────────┘
                    │
                    │ NFS mount (read-only for safety)
                    ▼
┌─────────────────────────────────────┐
│            REDFIN                   │
│  Brain / Analysis / Council         │
│                                     │
│  Mount:                             │
│  /ganuda/data/vision/bluefin/       │
│    (mirrors bluefin's export)       │
│                                     │
│  Processing:                        │
│  • Thermal memory storage           │
│  • Entity/relationship analysis     │
│  • Council deliberation             │
│  • Anomaly escalation               │
└─────────────────────────────────────┘
```

---

## Phase 1: Bluefin NFS Server Setup

**Run on BLUEFIN (via SSH or direct):**

```bash
# 1. Install NFS server
sudo apt update && sudo apt install -y nfs-kernel-server

# 2. Create vision data directories
sudo mkdir -p /ganuda/data/vision/{frames,processed,known_faces}
sudo chown -R dereadi:dereadi /ganuda/data/vision

# 3. Configure NFS export
# Allow redfin (100.116.27.89 via Tailscale) read-write access
echo '/ganuda/data/vision 100.116.27.89(rw,sync,no_subtree_check,no_root_squash)' | sudo tee -a /etc/exports

# 4. Apply exports and start NFS
sudo exportfs -ra
sudo systemctl enable nfs-kernel-server
sudo systemctl restart nfs-kernel-server

# 5. Verify export
showmount -e localhost
```

---

## Phase 2: Redfin NFS Client Setup

**Run on REDFIN:**

```bash
# 1. Install NFS client
sudo apt update && sudo apt install -y nfs-common

# 2. Create mount point (different path to avoid confusion)
sudo mkdir -p /ganuda/data/vision/bluefin

# 3. Test mount (bluefin's Tailscale IP)
sudo mount -t nfs 100.112.254.96:/ganuda/data/vision /ganuda/data/vision/bluefin

# 4. Verify mount
ls /ganuda/data/vision/bluefin/
df -h | grep vision

# 5. Add to fstab for persistence
echo '100.112.254.96:/ganuda/data/vision /ganuda/data/vision/bluefin nfs rw,defaults,_netdev 0 0' | sudo tee -a /etc/fstab
```

---

## Phase 3: Migrate Tribal Vision to Bluefin

**On BLUEFIN:**

```bash
# 1. Copy tribal vision service and dependencies
rsync -avz redfin:/ganuda/services/vision/ /ganuda/services/vision/

# 2. Copy known faces for recognition
rsync -avz redfin:/ganuda/data/vision/known_faces/ /ganuda/data/vision/known_faces/

# 3. Install Python dependencies (if not present)
source /home/dereadi/cherokee_venv/bin/activate
pip install opencv-python-headless ultralytics

# 4. Test camera connectivity
python3 -c "
import cv2
cap = cv2.VideoCapture('rtsp://admin:jawaseatlasers2@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0')
print('Camera 181:', 'Connected' if cap.isOpened() else 'FAILED')
cap.release()

cap = cv2.VideoCapture('rtsp://admin:jawaseatlasers2@192.168.132.182:554/cam/realmonitor?channel=1&subtype=1')
print('Camera 182:', 'Connected' if cap.isOpened() else 'FAILED')
cap.release()
"

# 5. Update tribal-vision output directory (edit tribal_vision.py)
# Change: self.output_dir = Path('/ganuda/data/vision/frames')
# Ensure it writes to local bluefin storage

# 6. Install systemd service
sudo cp /ganuda/scripts/systemd/tribal-vision.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tribal-vision
sudo systemctl start tribal-vision

# 7. Check status
sudo systemctl status tribal-vision
```

---

## Phase 4: Update Optic Nerve Pipeline

**On BLUEFIN:**

The vlm_optic_nerve.py is already on bluefin at port 8093. Update it to:
- Read from local `/ganuda/data/vision/frames/`
- Write processed results to `/ganuda/data/vision/processed/`

```bash
# Verify VLM is running
curl http://localhost:8090/v1/vlm/health

# Verify Optic Nerve is running
curl http://localhost:8093/v1/optic/health

# Test end-to-end (after a frame is captured)
curl -X POST http://localhost:8093/v1/optic/process \
  -H "Content-Type: application/json" \
  -d '{"frame_path": "/ganuda/data/vision/frames/office_pii_latest.jpg", "camera_id": "office_pii"}'
```

---

## Phase 5: Redfin Analysis Integration

**On REDFIN:**

Update the analysis services to read from the mounted bluefin export:

```python
# In analysis code, read processed results from:
VISION_PROCESSED_DIR = "/ganuda/data/vision/bluefin/processed/"

# Watch for new files and process
import watchdog  # or use inotify
```

Alternatively, bluefin's Optic Nerve can POST results directly to redfin's API for thermal memory storage (already implemented in vlm_relationship_storer.py which writes to PostgreSQL on 192.168.132.222).

---

## Phase 6: Disable Old Services on Redfin

**On REDFIN:**

```bash
# Stop tribal-vision on redfin (now runs on bluefin)
sudo systemctl stop tribal-vision
sudo systemctl disable tribal-vision

# Keep the old frames for reference but don't write new ones
mv /ganuda/data/vision/frames /ganuda/data/vision/frames_archive_redfin
```

---

## Verification Checklist

- [ ] NFS export visible from redfin: `showmount -e 100.112.254.96`
- [ ] Mount working: `ls /ganuda/data/vision/bluefin/`
- [ ] Cameras accessible from bluefin (test RTSP)
- [ ] tribal-vision running on bluefin: `systemctl status tribal-vision`
- [ ] VLM healthy: `curl bluefin:8090/v1/vlm/health`
- [ ] Optic Nerve healthy: `curl bluefin:8093/v1/optic/health`
- [ ] Frames appearing in `/ganuda/data/vision/frames/`
- [ ] Processed results appearing in `/ganuda/data/vision/processed/`
- [ ] Redfin can read bluefin's output via NFS mount

---

## Rollback

If issues occur:

```bash
# On redfin - unmount and re-enable local capture
sudo umount /ganuda/data/vision/bluefin
sudo systemctl start tribal-vision

# On bluefin - stop services
sudo systemctl stop tribal-vision
```

---

## Data Flow Summary

```
1. Camera .181/.182 → RTSP stream
2. Bluefin tribal-vision → captures frame → /ganuda/data/vision/frames/
3. Bluefin VLM → processes frame → extracts description
4. Bluefin Optic Nerve → extracts entities/relationships
5. Results → PostgreSQL (thermal_memory_archive) on 192.168.132.222
6. Results → /ganuda/data/vision/processed/ (NFS exported)
7. Redfin mounts → reads processed/ → further analysis
8. Redfin council → anomaly review → escalation decisions
```

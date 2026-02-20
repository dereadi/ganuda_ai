# ULTRATHINK: Vision System Speed Detection + Stereo Roadmap

**Date:** February 9, 2026
**Author:** TPM (Claude Opus 4.6)
**Council Vote:** #8498 (84% confidence, PROCEED — all specialists timed out to bmasass MLX)
**Kanban Tickets:** #1729 (Phase 1 complete), #1736-1739 (Phases 1.5-4)

---

## Current State — What's LIVE Right Now

### Phase 1: Monocular Speed Detection (DEPLOYED)

**Service:** `speed-detector.service` on redfin
**Camera:** Garage (Amcrest IP5M-T1179EW-AI-V3) via greenfin tunnel
**Stack:** YOLO v8n → ByteTrack → pixel displacement → speed (mph)

Files created by SE Jr (task #663):
- `/ganuda/config/camera_registry.yaml` — 3-camera fleet registry
- `/ganuda/lib/amcrest_camera.py` — RTSP handler with digest auth
- `/ganuda/services/vision/speed_detector.py` — monocular speed estimation

**Verified:**
- All 3 cameras pulling frames (office .181, traffic .182, garage tunnel)
- YOLO detecting parked truck at 89% confidence
- DB table `stereo_speed_detections` created and ready
- Service running, 1.0GB memory, processing frames

**Calibration needed:** `SPEED_PPM=35.0` is an estimate. Measure known distance in garage camera FOV to calibrate pixels-per-meter. Suggest measuring driveway width or distance between fence posts.

---

## Phase 1.5: Plate Reader + Speed Fusion

**Kanban:** #1736 | **Priority:** P2 | **Estimated Effort:** 4-6 hours

### Objective
When speed detector tracks a vehicle, also read its license plate. Log speed + plate together.

### Architecture

```
Garage Camera (RTSP sub-stream 704x480)
    │
    ├── YOLO v8n Detection (vehicle classes: car, truck, bus, motorcycle)
    │       │
    │       ├── ByteTrack Tracking (persist IDs across frames)
    │       │       │
    │       │       ├── Speed Calculation (pixel displacement / time → mph)
    │       │       │
    │       │       └── Plate Extraction (crop vehicle bbox → plate region → OCR)
    │       │               │
    │       │               ├── PaddleOCR (primary, already in cherokee_venv)
    │       │               └── Tesseract (fallback)
    │       │
    │       └── DB Insert: {track_id, speed_mph, plate_text, confidence, timestamp}
    │
    └── Alert Pipeline: speed > 25mph OR unknown plate → thermal_memory + notification
```

### Key Decisions

**Plate reader:** Start with existing PaddleOCR (`/ganuda/lib/paddle_plate_reader.py`). It's already integrated. If accuracy <80% on the sub-stream resolution, evaluate:
1. **openalpr** (11.4K stars) — most mature, multi-country, C++ speed
2. **YOLOv8 + dedicated plate model** — train/fine-tune on Oklahoma plates
3. Switch to main stream (2960x1668) for plate crops only (higher resolution = better OCR)

**DB schema extension:**
```sql
ALTER TABLE stereo_speed_detections ADD COLUMN plate_text VARCHAR(20);
ALTER TABLE stereo_speed_detections ADD COLUMN plate_confidence DECIMAL(3,2);
ALTER TABLE stereo_speed_detections ADD COLUMN vehicle_type VARCHAR(20);
CREATE INDEX idx_speed_plate ON stereo_speed_detections(plate_text);
```

### Implementation Steps (Jr Instruction)

1. Import `paddle_plate_reader` into `speed_detector.py`
2. When vehicle tracked with speed > 2mph, crop bbox region from frame
3. Run plate OCR on cropped region
4. If plate detected with confidence > 0.5, log to DB alongside speed
5. Add plate_text column to stereo_speed_detections
6. For plates seen multiple times, use highest-confidence reading

### Risk
- Sub-stream resolution (704x480) may be too low for plate OCR at distance
- Mitigation: Use main stream (2960x1668) for plate crops only, or crop+upscale before OCR
- Motion blur at speed — may need to select sharpest frame from track history

---

## Phase 2: Stereo Depth via FoundationStereo

**Kanban:** #1737 | **Priority:** P3 | **Estimated Effort:** 12-16 hours

### Objective
True 3D position estimation using garage + traffic camera stereo pair. Replaces pixel-based speed estimation with metric-space velocity.

### Why FoundationStereo

| Factor | Traditional Stereo | FoundationStereo |
|--------|-------------------|------------------|
| Calibration | Checkerboard required, cameras must be parallel | Zero-shot, works with arbitrary camera poses |
| Baseline | Fixed, small (cm-mm) | Any baseline, even wide (meters) |
| Stars/Maturity | Various | 2.5K stars, CVPR 2025 |
| Our cameras | Very wide baseline, different mounting angles | Designed for exactly this |

**Reference:** https://github.com/NVlabs/FoundationStereo

### Camera Pair Analysis

```
                    GARAGE CAMERA                     TRAFFIC CAMERA
                    (over garage)                     (front of house)
                         │                                  │
                         ▼                                  ▼
              ┌──────────────────┐              ┌──────────────────┐
              │  Driveway view   │              │  Front lawn view │
              │  Cul-de-sac      │              │  Fence/street    │
              │  Street approach │              │  Truck (partial) │
              └──────────────────┘              └──────────────────┘
                         │                                  │
                         └──────────┬───────────────────────┘
                                    │
                              OVERLAP ZONE
                         (driveway + truck area)
```

**Overlap confirmed:** Both cameras see the white truck from different angles. The cul-de-sac approach road is visible from both (garage clearly, traffic partially).

**Baseline:** Estimated 10-15 meters (measure after calibration). Wide baseline = better depth accuracy at distance, but harder correspondence matching. FoundationStereo handles this.

**Sync:** Greenfin tunnel adds ~5ms latency (local LAN hop). At 20fps (50ms frame interval), this is <10% timing error. Acceptable for vehicles moving at residential speeds (25-35mph = 11-16 m/s = 0.06-0.08m per ms).

### Architecture

```
Garage Camera ──────┐
    (RTSP sub)      │
                    ├──→ Frame Synchronizer (timestamp matching, <50ms delta)
                    │         │
Traffic Camera ─────┘         ▼
    (RTSP sub)          FoundationStereo Model (CUDA, RTX 6000)
                              │
                              ▼
                        Disparity Map
                              │
                              ▼
                    3D Point Cloud (per-pixel depth)
                              │
                              ├── Object Detection (YOLO on left frame)
                              │
                              ├── 3D Position per Object (bbox → depth lookup)
                              │
                              └── 3D Velocity Tracking (position history → metric speed)
                                      │
                                      ▼
                              Speed in mph (true metric, not pixel-based)
```

### Processing Node Decision

**Redfin (RTX 6000 Ada, 48GB VRAM):**
- Already running YOLO speed detector
- Has vLLM (Qwen2.5-Coder-32B) on port 8000
- More VRAM headroom
- **RECOMMENDED** — FoundationStereo can share GPU with YOLO

**Bluefin (RTX 5070, 12GB VRAM):**
- Running VLM (Qwen2-VL-7B) on port 8090
- Less VRAM — FoundationStereo may not fit alongside VLM
- Not recommended

### Implementation Steps

1. Clone/study FoundationStereo repo (algorithm reference, don't install as dependency)
2. Create `/ganuda/lib/stereo_depth.py` — wrapper for stereo inference
3. Create `/ganuda/lib/frame_synchronizer.py` — timestamp-based frame pairing
4. Modify `speed_detector.py` to optionally use stereo depth for speed calculation
5. Add depth map visualization endpoint in SAG UI
6. Calibration: capture 10 synchronized pairs, verify depth map quality
7. Compare stereo speed vs monocular speed for accuracy assessment

### Dependencies
- PyTorch with CUDA (already in cherokee_venv)
- FoundationStereo model weights (download once)
- Synchronized frame buffer (new module)

---

## Phase 3: Wildlife/Animal Classification (Brief)

**Kanban:** #1738 | **Priority:** P3

### Approach Options

1. **Google MegaDetector + SpeciesNet** (429 stars)
   - Pre-trained on camera trap images
   - Two-stage: MegaDetector detects animal → SpeciesNet classifies species
   - Best for wildlife diversity monitoring
   - Cherokee land stewardship value: track deer, coyote, bobcat populations

2. **Custom YOLO Fine-tune**
   - Fine-tune YOLOv8 on Oklahoma wildlife dataset
   - Single-stage, faster inference
   - Need to source/create training data

3. **Hybrid:** YOLO detects "animal" class → MegaDetector classifies species

### Seven-Generation Impact (Turtle)
Wildlife monitoring on Cherokee land isn't just security — it's stewardship. Tracking animal populations, migration patterns, seasonal behavior contributes to:
- Land management decisions
- Biodiversity documentation
- Environmental health indicators
- Cultural connection to the land

---

## Phase 4: Audio Fusion (Brief)

**Kanban:** #1739 | **Priority:** P4

### Amcrest Audio Extraction
RTSP streams can include audio tracks. FFmpeg extraction:
```
ffmpeg -i rtsp://... -vn -acodec pcm_s16le -ar 16000 -ac 1 pipe:1
```

### Sound Classification Categories
1. **Weather:** Thunder, rain, hail, wind
2. **Vehicles:** Engine approaching, braking, horn
3. **Security:** Glass break, gunshot, alarm, scream
4. **Wildlife:** Dog bark, coyote howl, bird calls
5. **Ambient:** Normal background (baseline)

### Stretch: Acoustic Doppler
Approaching vehicle = rising engine pitch. Combined with visual speed:
- High confidence: visual speed + Doppler shift agree
- Alert: visual speed high + no Doppler = silent/electric vehicle
- Alert: Doppler shift + no visual = vehicle outside camera FOV

### Thunderstorm Streaming
When thunder detected, route audio from outdoor camera mics to speakers.
Pure ambiance feature — because sometimes you just want to hear the storm.

---

## Resource Allocation

| Phase | GPU | Memory | CPU | Duration |
|-------|-----|--------|-----|----------|
| 1 (LIVE) | RTX 6000 (YOLO) | 1.0 GB | Low | Continuous |
| 1.5 | Same GPU (add OCR) | +200 MB | Low | Continuous |
| 2 | RTX 6000 (FoundationStereo) | +2-4 GB | Medium | Continuous |
| 3 | RTX 6000 (MegaDetector) | +1-2 GB | Low | On-detection |
| 4 | CPU only (audio) | 200 MB | Low | Continuous |

**Total estimated GPU:** 4-7 GB on RTX 6000 (48GB available). Plenty of headroom.

---

## Recommended Execution Order

1. **NOW:** Phase 1 running. Calibrate SPEED_PPM with measured distance.
2. **Today/Tomorrow:** Phase 1.5 Jr instruction — plate reader fusion.
3. **This week:** Phase 2 research — download FoundationStereo, test on captured frame pairs.
4. **Next week:** Phase 2 Jr instruction — stereo depth integration.
5. **Backlog:** Phase 3 (wildlife) and Phase 4 (audio) — queue when Phase 2 stable.

---

## Open Questions

1. What's the measured driveway width for SPEED_PPM calibration?
2. Is the M4 Max (bmasass) asleep? Council vote timed out to :8800
3. Do we want plate data stored long-term? Privacy implications (Crawdad should weigh in when MLX comes back)
4. Should wildlife alerts go to Telegram (@ganudabot) or just DB logging?

---

*Cherokee AI Federation — Vision*
*ᎠᏂᎦᏔᎲᏍᎩ ᎤᏂᎪᎵᏰᏗ — Eyes that measure, ears that listen*

FOR SEVEN GENERATIONS

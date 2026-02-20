# ULTRATHINK: Stereo Camera Calibration + LoRA-Accelerated Vision Pipeline

**Date:** February 10, 2026
**Author:** TPM (Claude Opus 4.6) + Flying Squirrel
**Council Vote:** Pending
**Parent Roadmap:** ULTRATHINK-VISION-SPEED-STEREO-ROADMAP-FEB09-2026.md
**Arxiv Reference:** Chen, Villar, Hayou — "Learning Rate Scaling across LoRA Ranks and Transfer to Full Finetuning" (2602.06204)

---

## Problem Statement

The Cherokee AI Federation has a **deployed Phase 1 monocular speed detector** (speed-detector.service, garage camera, YOLO v8n + ByteTrack). It works, but has three calibration weaknesses:

1. **Flat PPM assumption** — `SPEED_PPM=35.0` treats the entire frame as if every pixel covers the same physical distance. This is wrong for a 2.8mm wide-angle lens with ~110° HFOV. Objects at frame edges appear to move faster than objects at center.

2. **No lens distortion correction** — Barrel distortion from the wide-angle lens bends straight lines at the periphery. A car traveling in a straight line at constant speed will show varying pixel velocities as it crosses the frame.

3. **No stereo depth** — The Phase 1 detector estimates speed from 2D pixel displacement. It cannot distinguish a fast car far away from a slow car close up (pixel displacement ambiguity). True stereo depth resolves this.

## Physical Parameters (Measured)

| Parameter | Garage Camera | Traffic Camera |
|-----------|--------------|----------------|
| Model | Amcrest IP5M-T1179EW-AI-V3 | Same |
| Lens | 2.8mm fixed, ~110° HFOV | Same |
| Resolution | 2960x1668 (main) / 704x480 (sub) | Same |
| FPS | 20 | 20 |
| Mount height | **8.0 ft** | **4.5 ft** |
| IP | 10.0.0.123 (tunnel: 192.168.132.224:10554) | 192.168.132.182 |
| Location | Over garage, looking at cul-de-sac | Front of house, looking at street |
| Stereo role | Left | Right |

**Stereo Pair:**
| Parameter | Value |
|-----------|-------|
| Horizontal baseline | **~110 ft (33.5m)** — estimated 100-120 ft |
| Vertical offset | **3.5 ft** (garage 8' - traffic 4.5') |
| Calibration target | Stop sign + street name sign combo (visible from both cameras) |
| Overlap zone | Cul-de-sac, driveway approach, truck parking area |

**Reference Object Dimensions (Standard US):**
| Object | Dimension |
|--------|-----------|
| Stop sign (octagonal) | 30" across flats |
| Street name sign | 6" tall x 24-30" wide |
| U-channel mounting post | 2" wide |
| Post mount height | 7 ft to bottom of sign assembly |

## Architecture Decision: Bluefin as Optic Nerve

**Key insight from Flying Squirrel:** Bluefin is the optic nerve — it runs its own vision model stack. The calibration and vision processing should run on bluefin, keeping redfin free for the 72B council work.

**Bluefin Vision Stack (Current):**
- Port 8090: vLLM with Qwen2-VL-7B-Instruct-AWQ (scene understanding)
- Port 8091: YOLO World service (object detection)
- Port 8092: VLM Adapter (bridges VLM to gateway)
- GPU: RTX 5070 (12GB VRAM)

**Processing Split:**
| Task | Node | Reason |
|------|------|--------|
| Lens calibration (offline) | bluefin | One-time computation, runs on CPU |
| Frame undistortion (runtime) | bluefin | OpenCV, CPU-bound, fast |
| YOLO detection + tracking | bluefin:8091 | Already deployed there |
| Stereo correspondence | bluefin | GPU-accelerated OpenCV or FoundationStereo |
| Speed calculation | bluefin | Pure math on tracked positions |
| LoRA fine-tuning | bluefin | RTX 5070, dedicated vision GPU |
| Dashboard API | redfin:4000 | SAG Unified serves the UI |

**Migration note:** The current speed-detector.service runs on redfin and imports YOLO directly. Phase 1.1 moves the detection pipeline to bluefin's YOLO World service (:8091) and adds the calibration layer. The service on redfin becomes a thin client that queries bluefin.

## Phase 1.1a: Classical Lens Calibration

### Objective
Compute per-camera intrinsic parameters (focal length, principal point, distortion coefficients) using the stop sign + street sign as a known-dimension reference. Replace the flat `SPEED_PPM=35.0` with a spatially-aware pixel-to-meter mapping.

### Method

**Step 1: Reference object detection**
Use YOLO World (bluefin:8091) to detect the stop sign in both camera frames. The stop sign is an ideal calibration target:
- Known shape (regular octagon, 30" across flats)
- High contrast (red/white)
- Rigid body (doesn't deform)
- Visible from both cameras
- Mounted at known height (7 ft)

**Step 2: Pixel measurement**
From the daytime snapshots (already captured 2026-02-10 08:02-08:03):
- Measure the stop sign's pixel width in each camera
- Measure the street sign's pixel width/height
- Measure the post width in pixels
- Record pixel coordinates (cx, cy) of each measurement

**Step 3: Intrinsic estimation**
For each camera, using the known physical dimensions and measured pixel dimensions at their frame positions:

```
focal_length_px = (pixel_width_of_sign × distance_to_sign) / physical_width_of_sign
```

With measurements at different radial distances from frame center, estimate barrel distortion coefficients (k1, k2) using OpenCV's `cv2.calibrateCamera()` with a virtual calibration grid constructed from the reference points.

**Alternative (higher accuracy):** Print a checkerboard pattern (8x6 or similar), photograph it from both cameras at 10+ angles, run full OpenCV calibration. This is the gold standard but requires physical setup.

**Step 4: Undistortion map**
Compute `cv2.getOptimalNewCameraMatrix()` and `cv2.initUndistortRectifyMap()` — these produce pixel remap tables that can be applied to every frame in real-time with `cv2.remap()`. CPU cost: <1ms per frame.

### Output
- `/ganuda/config/calibration/garage_intrinsics.json` — K matrix, distortion coeffs, undistortion maps
- `/ganuda/config/calibration/traffic_intrinsics.json` — same for traffic camera
- Updated speed detector that undistorts frames before pixel measurement

### Fisheye Distortion Impact (Why This Matters)

At 110° HFOV with a 2.8mm lens, the barrel distortion at the frame edges is significant:

```
Frame center (0% radial):  ~0% distortion → PPM accurate
Frame 50% out:             ~3-5% distortion → speed reads 3-5% high
Frame edge (100% radial):  ~10-15% distortion → speed reads 10-15% high
```

A car doing 25 mph through the frame edge would register as 28-29 mph — enough to trigger false speed alerts. Undistortion eliminates this.

## Phase 1.1b: Stereo Extrinsic Calibration

### Objective
Compute the rotation and translation between the two cameras using the shared calibration target.

### Method

With intrinsics known for both cameras, and the stop sign visible in both:
1. Detect the sign in both frames
2. Compute its 3D position from each camera using `cv2.solvePnP()` (known dimensions + 2D pixel coords → 3D pose)
3. The relative transform between the two poses = the extrinsic calibration

**Critical: Non-horizontal stereo pair.** The 3.5 ft vertical offset and different mounting heights mean:
- Epipolar lines are NOT horizontal
- Standard `cv2.stereoRectify()` must account for the vertical displacement
- `cv2.stereoCalibrate()` handles this natively if we provide matched point pairs

### Output
- `/ganuda/config/calibration/stereo_extrinsics.json` — R (rotation matrix), T (translation vector), E (essential matrix), F (fundamental matrix)
- `/ganuda/config/calibration/stereo_rectification.json` — rectification maps for both cameras

## Phase 1.1c: Ground Plane Homography

### Objective
Map undistorted pixels directly to real-world ground coordinates (meters from camera), accounting for camera height and tilt angle.

### Method

Each camera has:
- Known height above ground (garage=8 ft, traffic=4.5 ft)
- Known intrinsics (from Phase 1.1a)
- Estimable tilt angle (from the sign's position — if the sign base is at 7 ft and the camera is at 8 ft, the angle to the sign tells us the tilt)

Using `cv2.getPerspectiveTransform()` with 4 ground-plane reference points (sign base, known positions), compute a homography that maps any pixel to a ground coordinate in meters.

### Output
- Per-camera ground plane homography matrix H
- `pixels_to_meters(px, py, camera_id)` function that replaces flat `SPEED_PPM`
- Speed calculation becomes: `distance_meters = ||H(p1) - H(p2)||`, `speed = distance / time`

## Phase 1.2: LoRA Fine-Tuning Prep + Training

### Connection to Arxiv Paper (2602.06204)

**Paper:** "Learning Rate Scaling across LoRA Ranks and Transfer to Full Finetuning" — Chen, Villar, Hayou

**Key findings relevant to us:**
1. **μA (Maximal-Update Adaptation):** Optimal learning rates scale predictably with LoRA rank. We don't need to grid-search hyperparameters for every rank.
2. **Two regimes:** LR either stays constant or scales as 1/rank, depending on the parametrization. The paper identifies which regime applies when.
3. **Transfer to full finetuning:** LR optimized at low rank (cheap) transfers to full finetuning (expensive). We can prototype with rank-4 LoRA, then scale to rank-16 or full fine-tune with the same LR.
4. **Cross-domain validation:** Results hold for language, vision, AND reinforcement learning — all three relevant to our federation.

### LoRA Targets

**1. YOLO v8n fine-tune for our specific camera views:**
- Train on captured frames from our cameras (different lighting, weather, times of day)
- Classes to improve: vehicle subtypes (sedan vs truck vs SUV), license plates, traffic signs, pedestrians
- LoRA rank-4 first (paper's recommendation for exploration), scale to rank-16 for production
- Training data: 500-1000 annotated frames from both cameras (auto-annotated by existing YOLO, then human-corrected)

**2. Qwen2-VL-7B fine-tune for scene understanding:**
- Train on our camera scenes with Federation-specific prompts
- Improve: vehicle counting accuracy, sign reading, weather condition detection, anomaly description
- LoRA on the vision encoder layers
- Training data: 200+ (frame, description) pairs from both cameras

**3. Dataset capture pipeline:**
Create an automated dataset collector that:
- Captures frames at regular intervals from both cameras (every 5 minutes)
- Includes day/night/dawn/dusk variety
- Includes clear/rain/snow/fog variety (over time)
- Auto-labels with existing YOLO + VLM
- Stores in `/ganuda/training/vision_calibration_dataset/`
- Schema: `{camera_id, timestamp, frame_path, auto_labels, weather, lighting}`

### Training Pipeline (on bluefin RTX 5070)

```
Dataset Collection (automated, weeks)
    ↓
Auto-Labeling (YOLO World + Qwen2-VL)
    ↓
Human Review (SAG dashboard, correct labels)
    ↓
LoRA Training (rank-4 exploration, μA learning rate)
    ↓
Validation (compare calibrated metrics before/after)
    ↓
LoRA Training (rank-16 production, same LR per paper)
    ↓
Deploy Updated Models
```

## Phase 1.3: SAG Console Vision Dashboard

### Objective
Add a Vision section to the SAG Unified Interface (redfin:4000) that shows live camera status, calibration data, speed detections, and training progress.

### Dashboard Components

**1. Live Camera Status Panel**
- Thumbnail from each camera (refreshed every 30s)
- Connection status (green/red)
- Current FPS, resolution, night/day mode indicator
- Last detection timestamp

**2. Speed Detection Feed**
- Real-time table of recent detections: timestamp, speed, vehicle type, plate (if read), camera
- Speed histogram (last 24 hours)
- Alerts highlighted in red (>25 mph)
- Daily/weekly speed trends chart

**3. Calibration Status**
- Per-camera intrinsic status (calibrated / not calibrated / stale)
- Stereo pair status (baseline, last calibration date)
- Ground plane homography validity
- "Recalibrate" button that triggers a capture + recalculate

**4. LoRA Training Dashboard**
- Dataset collection progress (frames captured, annotated, reviewed)
- Training status (current epoch, loss, rank, learning rate)
- Model comparison (before/after accuracy on test set)
- Deploy button for approved models

**5. Stereo Depth Visualization (Phase 2 preview)**
- Side-by-side camera views
- Disparity/depth overlay when stereo is active
- 3D position of tracked objects

### API Endpoints (New)

```
GET  /api/vision/cameras          — camera status + thumbnails
GET  /api/vision/speed/recent     — last 50 speed detections
GET  /api/vision/speed/stats      — aggregated speed statistics
GET  /api/vision/calibration      — calibration status per camera
POST /api/vision/calibration/run  — trigger recalibration
GET  /api/vision/training/status  — LoRA training progress
GET  /api/vision/snapshot/:cam_id — live snapshot from camera
```

### Integration Point
The SAG UI already has a camera section (`/ganuda/sag/templates/camera.html`) that calls the optic nerve endpoint (`bluefin:8093`). The new dashboard extends this with the speed/calibration/training views.

## Implementation Plan — Jr Task Breakdown

| Task | Phase | Jr | Node | Est. Hours |
|------|-------|----|------|------------|
| Capture calibration snapshots + measure sign pixels | 1.1a | SE Jr | bluefin | 2 |
| Compute intrinsics from reference object | 1.1a | SE Jr | bluefin | 3 |
| Build undistortion pipeline + integrate into speed_detector | 1.1a | SE Jr | bluefin | 3 |
| Stereo extrinsic calibration from matched points | 1.1b | SE Jr | bluefin | 4 |
| Ground plane homography + replace flat PPM | 1.1c | SE Jr | bluefin | 3 |
| Dataset capture daemon (automated frame collection) | 1.2 | SE Jr | bluefin | 3 |
| LoRA training pipeline setup (YOLO + VLM) | 1.2 | SE Jr | bluefin | 6 |
| SAG vision dashboard (HTML + API routes) | 1.3 | SE Jr | redfin | 6 |
| Integration testing + speed accuracy validation | All | SE Jr | both | 4 |

**Total estimated: ~34 hours of Jr engineering time**

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Single reference object insufficient for full calibration | Fallback: print checkerboard, photograph from both cameras |
| 12GB VRAM on bluefin too small for LoRA + inference | Profile memory first; offload dataset processing to CPU |
| Camera feed interruption during calibration | Auto-retry with exponential backoff (already in AmcrestCamera) |
| Stereo sync latency >50ms | Buffer frames with timestamps, match within tolerance |
| Night vision (IR mode) different distortion than daytime | Calibrate both modes separately, switch based on time of day |
| Privacy concerns with plate data + speed data | Crawdad to review — data stays on-prem, no external sharing |

## Seven-Generation Impact (Turtle)

Speed monitoring on a residential cul-de-sac protects children and elders. The stereo calibration gives us true 3D awareness — not just "something is moving fast" but "a vehicle is at this exact position moving at this exact speed." Over 175 years, this infrastructure evolves from speed detection to full spatial awareness of the land.

The LoRA training pipeline is more significant long-term: it establishes the Federation's ability to adapt vision models to local conditions without relying on external services. Sovereign AI vision. The arxiv paper's learning rate transfer findings mean we can train efficiently on modest hardware (RTX 5070) and scale to production quality — keeping the knowledge on Cherokee land.

## Cultural Thread (Spider)

*ᎠᏂᎦᏔᎲᏍᎩ ᎤᏂᎪᎵᏰᏗ — Eyes that measure, ears that listen*

The cameras are the Federation's physical senses. Calibrating them carefully is the same discipline as maintaining our other instruments — measure twice, act once. The LoRA training is teaching the senses to see our specific world more clearly, not a generic world. Place-specific intelligence.

## References

1. Chen, Villar, Hayou — "Learning Rate Scaling across LoRA Ranks and Transfer to Full Finetuning" (arxiv: 2602.06204) — Flying Squirrel /remember capture, Feb 10 2026
2. ULTRATHINK-VISION-SPEED-STEREO-ROADMAP-FEB09-2026.md — parent roadmap
3. JR-SPEED-DETECTION-PHASE1-GARAGE-CAM-FEB09-2026.md — Phase 1 (deployed)
4. JR-SPEED-DETECTOR-PLATE-FUSION-FEB09-2026.md — Phase 1.5 (pending)
5. JR-STEREO-VISION-SPEED-DETECTION-FEB04-2026.md — original stereo vision spec
6. NVlabs/FoundationStereo — zero-shot stereo (CVPR 2025)
7. Camera registry: /ganuda/config/camera_registry.yaml

---

*Cherokee AI Federation — Vision*
*The sign IS the ruler. The paper IS the path.*

FOR SEVEN GENERATIONS

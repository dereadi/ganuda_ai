# JR INSTRUCTION: Sky Monitor — Fireball/Bolide Detection

**Task ID**: SKY-MONITOR-001
**Priority**: P1
**SP**: 3
**Assigned Node**: redfin (vision processing)
**Council Vote**: Pending (TPM Easy Button — time-sensitive, fireball window NOW)
**Deer Signal**: Thermal #131110 (Stefan Burns / 3I/ATLAS debris hypothesis)

## Context

Earth is currently at closest approach to the trajectory of 3I/ATLAS, the largest interstellar object ever observed. 7+ fireball events in 20 days (Mar 2-21 2026), no known meteor stream association. Fragments recovered from 3 events (Germany, Ohio, Texas) show similar composition. We have two west-facing outdoor cameras that could capture a fireball event.

The detection window is NOW through at least mid-April 2026. Every night without a detector running is a missed opportunity.

## Cameras

Both are Amcrest IP5M-T1179EW-AI-V3, 2960x1668 @ 20fps, 110° HFOV, 2.8mm lens.

| Camera | IP / Stream | Mount | Facing |
|--------|-------------|-------|--------|
| **traffic** | 192.168.132.182 (direct) | 4.5 ft | Street/west |
| **garage** | 192.168.132.224:10554 (greenfin tunnel) | 8.0 ft | Driveway/west |

Use sub-streams (704x480) for continuous monitoring to minimize load. Switch to main stream (2960x1668) for capture on trigger.

## Architecture

### Approach: Sky Region Brightness Anomaly Detector

Do NOT modify the existing Tribal Vision or Speed Detector pipelines. This is a new, independent, lightweight service.

### Detection Logic

1. **Frame Capture**: Pull sub-stream frame from both cameras every 1 second (1 fps is sufficient — fireballs last 1-5 seconds)
2. **Sky Mask**: Define upper 40% of frame as "sky region" (below horizon is ground/structures). Make the mask percentage configurable via env var `SKY_MASK_PCT` (default 40).
3. **Brightness Baseline**: Maintain a rolling 60-second EMA of mean brightness in the sky region. This adapts to ambient light changes (dusk, clouds, moonlight).
4. **Spike Detection**: If current frame sky brightness exceeds baseline by >N standard deviations (configurable, default `SKY_SIGMA_THRESHOLD=4.0`), flag as anomaly.
5. **Streak Detection** (optional, Phase 2): On anomaly trigger, check if bright pixels form a linear streak (elongated blob) rather than diffuse flash (lightning). Use simple connected-component analysis + aspect ratio check.

### On Trigger

1. **Capture burst**: Switch to main stream, capture 10 seconds of frames at full resolution (2960x1668 @ 20fps = 200 frames)
2. **Save**: Write frames to `/ganuda/data/sky_events/{timestamp}_{camera}/` as JPEG
3. **Thermalize**: Write thermal memory entry with: timestamp, camera, brightness delta, number of anomalous frames, path to captures
4. **Alert**: Send Telegram notification via existing alert_manager: "SKY EVENT: Brightness anomaly detected on {camera} at {timestamp}. {N} frames captured."
5. **Save a 5-second clip**: Use ffmpeg to stitch the burst frames into an MP4 for easy review

### What NOT To Do

- Do NOT run ML/YOLO on sky frames — this is a brightness detector, not an object detector
- Do NOT touch the existing speed_detector or tribal_vision services
- Do NOT use the main stream for continuous monitoring — sub-stream only, switch on trigger
- Do NOT alert on gradual brightness changes (sunset, clouds) — the EMA baseline handles this
- Do NOT alert on lightning — lightning is diffuse flash (fills sky region), fireballs are linear streaks. Phase 1 can tolerate some false positives from lightning; Phase 2 streak detection filters it

## Service Configuration

```
Name: sky-monitor.service
ExecStart: /ganuda/venv/bin/python3 /ganuda/services/vision/sky_monitor.py
EnvironmentFile: /ganuda/config/secrets.env
Restart: always
RestartSec: 10
```

### Timer: sky-monitor.timer (OPTIONAL)

If running 24/7 is too much GPU/CPU, run only during prime fireball hours:
- Dusk to dawn (roughly 7 PM - 6 AM CT)
- Fireballs are visible during day if bright enough, but detection is much easier at night

For Phase 1, just run 24/7 — the sub-stream at 1fps on CPU is negligible load.

## Environment Variables

```bash
SKY_MASK_PCT=40           # Upper % of frame to monitor
SKY_SIGMA_THRESHOLD=4.0   # Std devs above baseline to trigger
SKY_BASELINE_WINDOW=60    # Seconds for rolling EMA
SKY_BURST_DURATION=10     # Seconds of full-res capture on trigger
SKY_COOLDOWN=30           # Seconds between triggers (avoid alert storm)
SKY_EVENT_DIR=/ganuda/data/sky_events
```

## Dependencies

- OpenCV (cv2) — already installed in ganuda venv
- ffmpeg — already on redfin
- RTSP access to both cameras — credentials in secrets.env
- Telegram alert via existing `/ganuda/lib/alert_manager.py`
- Thermal memory write via existing `/ganuda/lib/triad_thermal_memory_api.py`

## Success Criteria

- [ ] Service runs continuously on redfin without impacting existing vision pipeline
- [ ] Sub-stream 1fps capture from both cameras verified
- [ ] Sky mask correctly isolates upper frame region
- [ ] Brightness baseline adapts to ambient light changes
- [ ] Anomaly detection triggers on simulated bright flash (flashlight test at night)
- [ ] Full-res burst capture saves to disk on trigger
- [ ] Telegram alert fires on trigger
- [ ] Thermal memory entry created on trigger
- [ ] MP4 clip generated from burst frames

## Phase 2 (Future)

- Streak vs flash discrimination (fireball vs lightning)
- Trajectory estimation from stereo pair (both cameras see same event)
- Cross-reference with NASA Skyfall database API
- Audio correlation: sonic boom detection via camera microphones (both have mics)
- Integration with AMS (American Meteor Society) fireball reporting

## Notes

Stefan Burns / Earth Evolution is Partner's origin point. The transducer hypothesis started here. This matters beyond the science — it's the organism watching the sky because the sky is talking.

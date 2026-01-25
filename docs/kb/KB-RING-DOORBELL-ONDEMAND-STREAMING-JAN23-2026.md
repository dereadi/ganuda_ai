# KB: Ring Doorbell On-Demand Streaming Limitations

**KB ID:** KB-RING-ONDEMAND-001
**Created:** January 23, 2026
**Author:** TPM / Council
**Status:** Active

## Summary

Ring doorbell cameras are **on-demand by design** and cannot support 24/7 continuous streaming without significant negative effects. This impacts stereo vision architecture planning.

## Key Findings

### Ring Camera Design Philosophy

Ring cameras are designed primarily for:
1. On-demand streaming from detected events (motion/ding)
2. Short-term (10 minute) interactive viewing/recording
3. Cloud-based delivery (all streams route through Ring servers, never local)

### Negative Effects of Continuous 24/7 Streaming

| Effect | Impact | Severity |
|--------|--------|----------|
| Battery drain | Rapid depletion on battery-powered models | High |
| Overheating | Device thermal throttling or damage | Medium |
| **Loss of motion notifications** | Ring won't send alerts while streaming | **Critical** |

The loss of motion notifications is the most significant issue - continuous streaming defeats the core purpose of the doorbell as a security device.

### 24/7 Support Status

Ring is "rolling out 24x7 streaming support for some specific camera models" but this remains limited to particular devices. Most consumer Ring doorbells do not support it.

## Architectural Implications for Tribal Vision

### Recommended: Event-Triggered Stereo Mode

```
Amcrest Traffic Camera (continuous) ──► Motion Detected ──► Trigger Ring Stream
                                                │
                                                ▼
                                    Triangulation Window (10-60 sec)
                                                │
                                                ▼
                                    Release Ring Stream
```

**Benefits:**
- Preserves Ring motion notifications
- Conserves battery/thermal budget
- Activates stereo only when needed

### Implementation with go2rtc

go2rtc bridge (running on bluefin:8555) automatically:
- Starts Ring stream when RTSP client connects
- Stops stream ~5-10 seconds after client disconnects
- Preserves Ring's intended operation model

**RTSP URL:** `rtsp://ring:tribal_vision_2026@bluefin:8555/ring_doorbell`

### Alternative: Periodic Depth Sampling

For depth calibration without continuous streaming:
1. Request Ring frame every 5-15 minutes briefly
2. Capture single frame for depth reference
3. Immediately disconnect
4. Update depth map/calibration data

## Configuration Reference

**ring-mqtt on bluefin (WORKING CONFIG):**
- Container: `ring-mqtt` (podman, host network)
- RTSP Port: 8554
- RTSP URL: `rtsp://ring:tribal_vision_2026@localhost:8554/d436398fc2b8_live`
- Device ID: `d436398fc2b8` (Front Door doorbell_v4)
- Resolution: 1920x1080

**MQTT Broker:**
- Container: `mqtt` (EMQX, host network)
- Port: 1883
- WebSocket disabled to avoid port conflicts

**Ring Token Location:**
- `/ganuda/services/ring-mqtt/data/ring-state.json`
- Token auto-refreshes via ring-mqtt

**Startup Commands:**
```bash
# Start MQTT broker (disable WebSocket to avoid 8083 conflict)
podman run -d --name mqtt --network host --restart unless-stopped \
  -e EMQX_LISTENERS__WS__DEFAULT__BIND=0 \
  -e EMQX_LISTENERS__WSS__DEFAULT__BIND=0 \
  docker.io/emqx/emqx:latest

# Start ring-mqtt
podman run -d --name ring-mqtt --network host --restart unless-stopped \
  -v /ganuda/services/ring-mqtt/data:/data \
  tsightler/ring-mqtt
```

## Related Documentation

- [JR-RING-MQTT-STEREO-VISION-JAN23-2026.md](/ganuda/docs/jr_instructions/JR-RING-MQTT-STEREO-VISION-JAN23-2026.md)
- [JR-TRIBAL-VISION-STEREO-HUB-JAN23-2026.md](/ganuda/docs/jr_instructions/JR-TRIBAL-VISION-STEREO-HUB-JAN23-2026.md)
- [ULTRATHINK-TRIBAL-VISION-STEREO-ARCHITECTURE-JAN23-2026.md](/ganuda/docs/ultrathink/ULTRATHINK-TRIBAL-VISION-STEREO-ARCHITECTURE-JAN23-2026.md)

## References

- https://github.com/tsightler/ring-mqtt/wiki/Video-Streaming
- https://github.com/AlexxIT/go2rtc

---

**FOR SEVEN GENERATIONS** - This KB preserves operational knowledge to prevent repeated discovery cycles.

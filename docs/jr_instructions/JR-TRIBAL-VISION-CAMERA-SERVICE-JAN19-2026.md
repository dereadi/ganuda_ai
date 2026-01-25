# JR Instruction: Tribal Vision Camera Service Installation

## Metadata
```yaml
task_id: tribal_vision_service
priority: 2
assigned_to: it_triad_jr
target: redfin
estimated_effort: small
```

## Background

Tribal Vision camera intelligence system has been built and tested. Two Amcrest IP cameras are integrated:
- **192.168.132.181** - Office PII Monitor (detects people entering sensitive area)
- **192.168.132.182** - Traffic Monitor (detects and learns vehicles)

YOLOv8 detection tested successfully:
- Office: person (58%), laptop (60%), chair, tv detected
- Traffic: car (54%) detected

## Tasks

### 1. Install Systemd Service

```bash
# On redfin as root
sudo ln -sf /ganuda/scripts/systemd/tribal-vision.service /etc/systemd/system/tribal-vision.service
sudo systemctl daemon-reload
sudo systemctl enable tribal-vision.service
sudo systemctl start tribal-vision.service
```

### 2. Verify Service Running

```bash
systemctl status tribal-vision.service
journalctl -u tribal-vision.service -f
```

### 3. Check Detection Output

```bash
# Verify frames being captured
ls -la /ganuda/data/vision/
# Should see new .jpg files every 60 seconds
```

### 4. Test Manual Capture

```bash
cd /ganuda/services/vision
/home/dereadi/cherokee_venv/bin/python3 tribal_vision.py --once --camera both
```

## Files

| File | Purpose |
|------|---------|
| `/ganuda/services/vision/tribal_vision.py` | Main vision service |
| `/ganuda/scripts/systemd/tribal-vision.service` | Systemd unit file |
| `/ganuda/data/vision/` | Output directory for annotated frames |

## Integration Points

- **Crawdad Specialist**: Receives SECURITY_ALERT when person detected in PII area
- **Eagle Eye Specialist**: Receives vehicle tracking data for learning
- **Thermal Memory**: Detections logged to thermal_memory_archive

## Success Criteria

- [ ] Service running: `systemctl is-active tribal-vision.service` returns "active"
- [ ] Frames captured every 60 seconds in `/ganuda/data/vision/`
- [ ] Detections logged to thermal_memory_archive
- [ ] No errors in `journalctl -u tribal-vision.service`

## Future Enhancements (Vehicle Learning)

Phase 2 will add:
- DeepSORT for vehicle tracking across frames
- License plate recognition (if cameras support it)
- Vehicle fingerprinting (color, size, make/model estimation)
- Alert on unknown vehicles vs learned household vehicles

---

*Cherokee AI Federation - For the Seven Generations*
*"Eagle Eye sees all who approach. Crawdad guards what must be protected."*

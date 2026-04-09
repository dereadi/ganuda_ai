# KB: Tribal Vision Config Refactor — YAML Registry + Alert Webhooks

## Date: April 2, 2026
## Service: tribal-vision.service (redfin)
## Kanban: PRODUCT-SOVEREIGN-SURVEILLANCE / Long Man P-3

---

## What Changed

Tribal Vision was refactored from hardcoded camera IPs to a YAML config-driven architecture with webhook alerts. This is the Long Man P-3 (Harden Core) deliverable.

### Before (hardcoded)
```python
CAMERAS = {
    'office_pii': {
        'ip': '192.168.132.181',
        'rtsp': f'rtsp://admin:{password}@192.168.132.181:554/...',
        ...
    }
}
```

### After (YAML registry)
```python
CAMERAS = load_cameras_from_registry('/ganuda/config/camera_registry.yaml')
```

The camera registry at `/ganuda/config/camera_registry.yaml` defines all cameras with:
- IP, port, RTSP URLs (main + sub stream)
- Purpose (security, vehicle_identification, general)
- Specialist assignment (crawdad, eagle_eye)
- Password via env var (not in YAML — `password_env: CAMERA_OFFICE_PII_PASSWORD`)
- Microphone flag, resolution, FPS

Falls back to hardcoded config if YAML unavailable.

### Alert Webhook

New function `send_alert_webhook()` fires when security alerts are detected (unknown person in PII area). Configure via environment variable:

```bash
TRIBAL_VISION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/HOOK/URL
```

Supports Slack, Telegram (via bot API), or any generic webhook that accepts JSON POST.

## Adding a New Camera

1. Add entry to `/ganuda/config/camera_registry.yaml`:
```yaml
cameras:
  garage:
    type: amcrest
    ip: 192.168.132.183
    port: 554
    username: admin
    password_env: CAMERA_GARAGE_PASSWORD
    rtsp_main: "rtsp://admin:{password}@192.168.132.183:554/cam/realmonitor?channel=1&subtype=0"
    purpose: security
    specialist: crawdad
```

2. Set the password env var in `/ganuda/config/secrets.env`:
```bash
CAMERA_GARAGE_PASSWORD=your_password_here
```

3. Restart the service:
```bash
sudo systemctl restart tribal-vision
```

No code changes needed. The registry is read at startup.

## Testing

```bash
# Single capture from all cameras
python3 /ganuda/services/vision/tribal_vision.py --once --camera both

# Test webhook (set env var first)
TRIBAL_VISION_WEBHOOK_URL=https://httpbin.org/post python3 -c "
from services.vision.tribal_vision import send_alert_webhook
send_alert_webhook({'type': 'TEST', 'message': 'Webhook test from Tribal Vision'})
"
```

## Service Configuration

The systemd service at `/etc/systemd/system/tribal-vision.service` should include the webhook URL in the Environment line:

```ini
Environment=TRIBAL_VISION_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/HOOK
```

## P-3 Complete Checklist (All Done Apr 2 2026)

- [x] YAML config loading from camera_registry.yaml
- [x] Alert webhook (Slack/Telegram/generic)
- [x] Fire Guard integration — camera RTSP ports (554) checked every 2 min
- [x] Encrypted local storage — Fernet AES for saved frames (.jpg.enc)
- [x] Face recognition consent flag — disabled by default, requires TRIBAL_VISION_FACE_CONSENT=true
- [x] Hardcoded fallback if YAML unavailable

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `TRIBAL_VISION_WEBHOOK_URL` | (none) | Alert webhook endpoint |
| `TRIBAL_VISION_FACE_CONSENT` | `false` | Enable face recognition (requires documentation) |
| `TRIBAL_VISION_ENCRYPT_FRAMES` | `true` | Encrypt saved detection frames |
| `CAMERA_OFFICE_PII_PASSWORD` | (secrets.env) | Office camera RTSP password |
| `CAMERA_TRAFFIC_PASSWORD` | (secrets.env) | Traffic camera RTSP password |

### Encryption Key

Auto-generated at `/ganuda/config/.vision_frame_key` on first run. Permissions 600. Back this up — without it, encrypted frames are unrecoverable.

## What's Still Needed (Long Man P-2 and P-1)

- **Dashboard on DMZ**: API endpoints for /api/vision/status, /api/vision/alerts, /api/vision/faces — deploy to owlfin alongside stoneclad_demo_api
- **Client deployment package**: Install script, config template, README

---

*For Seven Generations.*

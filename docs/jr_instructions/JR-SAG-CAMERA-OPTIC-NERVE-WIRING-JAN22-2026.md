# JR: Wire SAG Camera UI to Optic Nerve Endpoint

**Date:** January 22, 2026
**Priority:** High
**Type:** Frontend Integration
**Assigned To:** Software Engineer Jr

## Objective

Connect the SAG Camera UI to the VLM Optic Nerve pipeline endpoint on bluefin, enabling real-time vision processing with entity extraction, relationship storage, and clause evaluation.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   SAG Camera    │────▶│  Optic Nerve    │────▶│  Thermal Memory │
│   UI (redfin)   │     │  (bluefin:8093) │     │  (bluefin DB)   │
│   Port 4000     │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        │   POST /v1/optic/     │   Entities +          │
        │   process             │   Relationships       │
        │   {frame_path,        │   stored in           │
        │    camera_id}         │   thermal_memory      │
        └───────────────────────┴───────────────────────┘
```

## Endpoints

### Optic Nerve API (bluefin:8093)

**Process Frame:**
```
POST http://192.168.132.222:8093/v1/optic/process
Content-Type: application/json

{
  "frame_path": "/ganuda/data/vision/frames/camera_01/frame_001.jpg",
  "camera_id": "front_door"
}
```

**Response:**
```json
{
  "camera_id": "front_door",
  "frame_path": "/ganuda/data/vision/frames/camera_01/frame_001.jpg",
  "timestamp": "2026-01-22T10:30:00",
  "vlm_description": "A person in a red jacket standing near the front door...",
  "vlm_latency_ms": 1250,
  "entities_found": 2,
  "relationships_found": 1,
  "anomaly_detected": false,
  "entity_memory_ids": {"Person_001": 1234, "Front_Door": 1235},
  "relationship_ids": [5678],
  "clauses_triggered": 0,
  "escalated_to_brain": false,
  "processing_time_ms": 2100,
  "success": true,
  "error": null
}
```

**Health Check:**
```
GET http://192.168.132.222:8093/v1/optic/health
```

## Implementation Steps

### Step 1: Start Optic Nerve Service on Bluefin

First, ensure the optic nerve service is running:

```bash
ssh 192.168.132.222 "cd /ganuda/lib && source /home/dereadi/cherokee_venv/bin/activate && nohup python3 vlm_optic_nerve.py --serve > /ganuda/logs/optic_nerve.log 2>&1 &"
```

Or create a systemd service:
```bash
# /etc/systemd/system/optic-nerve.service
[Unit]
Description=Cherokee AI Optic Nerve Pipeline
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/lib
Environment="PATH=/home/dereadi/cherokee_venv/bin:/usr/bin"
ExecStart=/home/dereadi/cherokee_venv/bin/python3 vlm_optic_nerve.py --serve
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

### Step 2: Update SAG Camera UI

Locate the SAG Camera component and add optic nerve integration.

**File:** `/ganuda/sag/templates/camera.html` or similar

Add JavaScript to call the optic nerve endpoint:

```javascript
async function processFrame(framePath, cameraId) {
    const response = await fetch('http://192.168.132.222:8093/v1/optic/process', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            frame_path: framePath,
            camera_id: cameraId
        })
    });

    const result = await response.json();

    if (result.success) {
        displayEntities(result.entities_found, result.entity_memory_ids);
        displayRelationships(result.relationships_found, result.relationship_ids);

        if (result.anomaly_detected) {
            showAnomalyAlert(result);
        }

        if (result.escalated_to_brain) {
            showEscalationBadge();
        }
    } else {
        showError(result.error);
    }

    return result;
}
```

### Step 3: Add UI Components

Add display components for:
1. **Entity List** - Show detected entities with confidence
2. **Relationship Graph** - Visualize entity relationships
3. **Anomaly Indicator** - Red badge when anomaly detected
4. **Escalation Status** - Show when escalated to redfin brain
5. **Processing Stats** - VLM latency, total time

### Step 4: Frame Capture Integration

Connect the camera frame capture to the processing pipeline:

```javascript
// When new frame is captured
cameraFeed.onFrameCapture = async (frameBlob, cameraId) => {
    // Save frame to disk (or send as base64)
    const framePath = await saveFrame(frameBlob, cameraId);

    // Process through optic nerve
    const result = await processFrame(framePath, cameraId);

    // Update UI with results
    updateVisionPanel(result);
};
```

### Step 5: Add Optic Nerve Status to Dashboard

Add health monitoring widget:

```javascript
async function checkOpticNerveHealth() {
    try {
        const response = await fetch('http://192.168.132.222:8093/v1/optic/health');
        const health = await response.json();
        updateHealthIndicator('optic-nerve', health.status === 'healthy');
    } catch (e) {
        updateHealthIndicator('optic-nerve', false);
    }
}

// Check every 30 seconds
setInterval(checkOpticNerveHealth, 30000);
```

## Files to Modify

| File | Change |
|------|--------|
| `/ganuda/sag/templates/camera.html` | Add optic nerve integration |
| `/ganuda/sag/static/js/vision.js` | Add processFrame function |
| `/ganuda/sag/static/css/vision.css` | Add entity/relationship styles |
| `/ganuda/sag/app.py` | Add proxy route if needed for CORS |

## Testing

### Manual Test
```bash
# Test optic nerve directly
curl -X POST http://192.168.132.222:8093/v1/optic/process \
  -H "Content-Type: application/json" \
  -d '{"frame_path": "/ganuda/data/vision/frames/test/sample.jpg", "camera_id": "test"}'
```

### Integration Test
1. Open SAG Camera UI at http://192.168.132.223:4000/
2. Navigate to Camera section
3. Capture or upload a test frame
4. Verify entities appear in UI
5. Check thermal_memory_archive for new entries

## CORS Considerations

If SAG runs on redfin (192.168.132.223) and optic nerve on bluefin (192.168.132.222), add CORS headers to optic nerve:

```python
# In vlm_optic_nerve.py create_app()
from flask_cors import CORS
CORS(app, origins=['http://192.168.132.223:4000'])
```

Or add a proxy route in SAG:
```python
@app.route('/api/optic/process', methods=['POST'])
def proxy_optic_process():
    response = requests.post('http://192.168.132.222:8093/v1/optic/process', json=request.json)
    return jsonify(response.json())
```

## Success Criteria

- [ ] Optic nerve service running on bluefin:8093
- [ ] SAG Camera UI can submit frames for processing
- [ ] Entities displayed in UI after processing
- [ ] Relationships visible in UI
- [ ] Anomaly alerts shown when detected
- [ ] Health status shown in dashboard
- [ ] No CORS errors in browser console

## For Seven Generations

This integration brings visual understanding to the Cherokee AI Federation, allowing the system to perceive and remember what it sees - building knowledge across generations of observations.

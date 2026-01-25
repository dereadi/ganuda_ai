# Jr Task: Add VLM Fetch to SAG Camera Tab

Add a JavaScript function to fetch VLM analysis in the SAG Camera UI.

**Run on:** redfin (192.168.132.223)

## Edit File
**File:** `/ganuda/sag/static/js/camera.js`

Add this function:

```javascript
async function analyzeFrame(imagePath, cameraId) {
    const response = await fetch('/api/vlm/describe', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({image_path: imagePath, camera_id: cameraId})
    });
    return response.json();
}
```

## Verify
Check the file was updated:
```bash
grep -n "analyzeFrame" /ganuda/sag/static/js/camera.js
```

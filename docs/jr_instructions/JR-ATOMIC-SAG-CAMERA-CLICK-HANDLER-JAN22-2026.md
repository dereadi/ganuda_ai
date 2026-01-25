# Jr Task: Add Click Handler for Analyze Button

Wire the analyze button click to call VLM API.

**Run on:** redfin (192.168.132.223)

## Edit File
**File:** `/ganuda/sag/static/js/camera.js`

Add this click handler:

```javascript
document.querySelectorAll('.analyze-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        const cameraId = this.dataset.cameraId;
        const framePath = this.dataset.framePath;
        const resultDiv = document.getElementById('vlm-result-' + cameraId);
        
        this.disabled = true;
        this.textContent = 'Analyzing...';
        resultDiv.innerHTML = '<span class="loading">Processing frame...</span>';
        
        try {
            const result = await analyzeFrame(framePath, cameraId);
            resultDiv.innerHTML = result.success 
                ? '<p class="vlm-description">' + result.description + '</p>'
                : '<p class="error">Error: ' + result.error + '</p>';
        } catch(e) {
            resultDiv.innerHTML = '<p class="error">Failed: ' + e.message + '</p>';
        }
        
        this.disabled = false;
        this.textContent = 'Analyze Frame';
    });
});
```

## Verify
```bash
grep -n "analyze-btn" /ganuda/sag/static/js/camera.js
```

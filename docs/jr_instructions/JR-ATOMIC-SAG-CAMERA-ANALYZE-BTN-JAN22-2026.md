# Jr Task: Add Analyze Button to Camera Card

Add an "Analyze" button to each camera card in SAG UI.

**Run on:** redfin (192.168.132.223)

## Edit File
**File:** `/ganuda/sag/templates/cameras.html`

In the camera card template, add after the camera image:

```html
<button class="btn btn-sm btn-primary analyze-btn" 
        data-camera-id="{{ camera.id }}"
        data-frame-path="{{ camera.last_frame }}">
    Analyze Frame
</button>
<div class="vlm-result" id="vlm-result-{{ camera.id }}"></div>
```

## Verify
```bash
grep -n "analyze-btn" /ganuda/sag/templates/cameras.html
```

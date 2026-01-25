# JR Instruction: SAG Camera Tab VLM Integration

**Task ID**: SAG-VLM-001
**Priority**: P1 - High
**Created**: January 22, 2026
**TPM**: Claude Opus 4.5
**Council Audit Hash**: 36c8b402ffe658fe
**Ultrathink**: `/ganuda/docs/ultrathink/ULTRATHINK-SAG-CAMERA-VLM-INTEGRATION-JAN22-2026.md`

## Objective

Wire the SAG Camera UI tab to VLM endpoints, enabling AI-powered security camera frame analysis through the web interface.

## Council Concerns (Must Address)

| Specialist | Concern | Required Action |
|------------|---------|-----------------|
| **Crawdad** | SECURITY | Server-side API key proxy, path validation, TLS |
| **Raven** | STRATEGY | Privacy disclosure, audit logging |
| **Turtle** | 7GEN | AI disclosure in responses, human review for critical |

## Prerequisites

- VLM service running on bluefin:8090 ✅
- LLM Gateway v1.5.0 with VLM proxy on redfin:8080 ✅
- SAG UI running on redfin:4000 ✅
- Test images in `/ganuda/data/vision/frames/test/` (see JR-SAG-TEST-IMAGES)

## Phase 1: SAG Backend VLM Routes

### Task 1.1: Create VLM Routes Module

Create file: `/ganuda/sag/routes/vlm_routes.py`

```python
"""
SAG VLM Routes - Proxy to LLM Gateway VLM endpoints
Cherokee AI Federation - January 2026

Security: Server-side API key (never exposed to browser)
"""

from flask import Blueprint, request, jsonify
import httpx
import os
import logging

logger = logging.getLogger(__name__)

vlm_bp = Blueprint('vlm', __name__, url_prefix='/api/vlm')

# Configuration
GATEWAY_URL = os.getenv('LLM_GATEWAY_URL', 'http://localhost:8080')
API_KEY = os.getenv('LLM_GATEWAY_API_KEY', 'ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5')
VLM_TIMEOUT = 120.0  # VLM inference can take ~17 seconds

# Security: Allowed base path for images
ALLOWED_IMAGE_BASE = '/ganuda/data/vision/frames'


def validate_image_path(path: str) -> bool:
    """Prevent path traversal attacks."""
    if not path:
        return False
    # Normalize and check
    real_path = os.path.realpath(path)
    return real_path.startswith(ALLOWED_IMAGE_BASE)


def log_vlm_request(endpoint: str, camera_id: str, success: bool):
    """Audit log for VLM requests (Crawdad requirement)."""
    logger.info(f"VLM_AUDIT: endpoint={endpoint} camera={camera_id} success={success}")


@vlm_bp.route('/health', methods=['GET'])
def vlm_health():
    """Check VLM service health."""
    try:
        response = httpx.get(
            f"{GATEWAY_URL}/v1/vlm/health",
            timeout=5.0
        )
        return jsonify(response.json())
    except Exception as e:
        logger.error(f"VLM health check failed: {e}")
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "node": "bluefin"
        })


@vlm_bp.route('/describe', methods=['POST'])
def vlm_describe():
    """Describe a camera frame."""
    data = request.json or {}
    image_path = data.get('image_path', '')
    camera_id = data.get('camera_id', 'unknown')

    # Security validation
    if not validate_image_path(image_path):
        log_vlm_request('describe', camera_id, False)
        return jsonify({
            "success": False,
            "error": "Invalid image path"
        }), 400

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/v1/vlm/describe",
            json={"image_path": image_path, "camera_id": camera_id},
            headers={"X-API-Key": API_KEY},
            timeout=VLM_TIMEOUT
        )
        result = response.json()

        # Add AI disclosure (Turtle 7GEN requirement)
        result['ai_disclosure'] = "Analysis performed by Qwen2-VL-7B AI model"

        log_vlm_request('describe', camera_id, result.get('success', False))
        return jsonify(result)

    except httpx.TimeoutException:
        log_vlm_request('describe', camera_id, False)
        return jsonify({
            "success": False,
            "error": "VLM service timeout (try again)"
        }), 504
    except Exception as e:
        log_vlm_request('describe', camera_id, False)
        logger.error(f"VLM describe error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 502


@vlm_bp.route('/analyze', methods=['POST'])
def vlm_analyze():
    """Analyze frame for anomalies."""
    data = request.json or {}
    image_path = data.get('image_path', '')
    camera_id = data.get('camera_id', 'unknown')

    if not validate_image_path(image_path):
        log_vlm_request('analyze', camera_id, False)
        return jsonify({
            "success": False,
            "error": "Invalid image path"
        }), 400

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/v1/vlm/analyze",
            json={"image_path": image_path, "camera_id": camera_id},
            headers={"X-API-Key": API_KEY},
            timeout=VLM_TIMEOUT
        )
        result = response.json()

        # Add AI disclosure
        result['ai_disclosure'] = "Analysis performed by Qwen2-VL-7B AI model"

        # Flag critical assessments for human review (Turtle requirement)
        if result.get('assessment') == 'critical':
            result['human_review_required'] = True

        log_vlm_request('analyze', camera_id, result.get('success', False))
        return jsonify(result)

    except httpx.TimeoutException:
        log_vlm_request('analyze', camera_id, False)
        return jsonify({
            "success": False,
            "error": "VLM service timeout"
        }), 504
    except Exception as e:
        log_vlm_request('analyze', camera_id, False)
        logger.error(f"VLM analyze error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 502


@vlm_bp.route('/ask', methods=['POST'])
def vlm_ask():
    """Answer a question about a frame."""
    data = request.json or {}
    image_path = data.get('image_path', '')
    question = data.get('question', '')
    camera_id = data.get('camera_id', 'unknown')

    if not validate_image_path(image_path):
        log_vlm_request('ask', camera_id, False)
        return jsonify({
            "success": False,
            "error": "Invalid image path"
        }), 400

    if not question.strip():
        return jsonify({
            "success": False,
            "error": "Question is required"
        }), 400

    try:
        response = httpx.post(
            f"{GATEWAY_URL}/v1/vlm/ask",
            json={
                "image_path": image_path,
                "question": question,
                "camera_id": camera_id
            },
            headers={"X-API-Key": API_KEY},
            timeout=VLM_TIMEOUT
        )
        result = response.json()
        result['ai_disclosure'] = "Answer generated by Qwen2-VL-7B AI model"

        log_vlm_request('ask', camera_id, result.get('success', False))
        return jsonify(result)

    except httpx.TimeoutException:
        log_vlm_request('ask', camera_id, False)
        return jsonify({
            "success": False,
            "error": "VLM service timeout"
        }), 504
    except Exception as e:
        log_vlm_request('ask', camera_id, False)
        logger.error(f"VLM ask error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 502


@vlm_bp.route('/frames', methods=['GET'])
def list_frames():
    """List available frames for analysis."""
    import glob

    frames = []
    base_path = ALLOWED_IMAGE_BASE

    # Get all jpg/png files
    for pattern in ['**/*.jpg', '**/*.png', '**/*.jpeg']:
        for path in glob.glob(f"{base_path}/{pattern}", recursive=True):
            rel_path = path.replace(base_path + '/', '')
            frames.append({
                "path": path,
                "relative": rel_path,
                "camera_id": rel_path.split('/')[0] if '/' in rel_path else 'unknown'
            })

    # Sort by modification time (newest first)
    frames.sort(key=lambda x: os.path.getmtime(x['path']), reverse=True)

    return jsonify({
        "frames": frames[:50],  # Limit to 50 most recent
        "total": len(frames),
        "base_path": base_path
    })
```

### Task 1.2: Register VLM Routes in SAG App

Modify: `/ganuda/sag/app.py`

Add import and register blueprint:

```python
# Near top of file, with other imports
from routes.vlm_routes import vlm_bp

# After app creation, with other blueprint registrations
app.register_blueprint(vlm_bp)
```

## Phase 2: Camera Tab Frontend

### Task 2.1: Create Camera Tab HTML

Create file: `/ganuda/sag/templates/partials/camera_tab.html`

```html
<!-- Camera Analysis Tab Content -->
<div id="camera-tab" class="tab-content" style="display: none;">
    <div class="camera-container">
        <!-- Header with VLM Status -->
        <div class="camera-header">
            <h2>Tribal Vision - Camera Analysis</h2>
            <div class="vlm-status" id="vlm-status">
                <span class="status-dot"></span>
                <span class="status-text">Checking VLM...</span>
            </div>
        </div>

        <!-- Privacy Disclosure (Raven/Turtle requirement) -->
        <div class="privacy-notice">
            <i class="icon-info"></i>
            <span>AI-powered analysis using Qwen2-VL-7B. Results are logged for security audit.</span>
        </div>

        <!-- Frame Selection -->
        <div class="frame-selection">
            <div class="frame-input-group">
                <label for="frame-select">Select Frame:</label>
                <select id="frame-select" class="form-control">
                    <option value="">-- Select a frame --</option>
                </select>
                <button id="refresh-frames" class="btn btn-secondary" title="Refresh frame list">
                    ↻
                </button>
            </div>

            <div class="frame-input-group">
                <label for="camera-id">Camera ID:</label>
                <input type="text" id="camera-id" class="form-control" placeholder="e.g., front_door" value="test">
            </div>

            <div class="frame-input-group">
                <label for="manual-path">Or enter path:</label>
                <input type="text" id="manual-path" class="form-control" placeholder="/ganuda/data/vision/frames/...">
            </div>
        </div>

        <!-- Frame Preview -->
        <div class="frame-preview" id="frame-preview">
            <div class="preview-placeholder">
                <span>Select a frame to preview</span>
            </div>
        </div>

        <!-- Analysis Controls -->
        <div class="analysis-controls">
            <button id="btn-describe" class="btn btn-primary" disabled>
                <span class="btn-icon">📝</span> Describe
            </button>
            <button id="btn-analyze" class="btn btn-warning" disabled>
                <span class="btn-icon">🔍</span> Analyze Anomalies
            </button>
            <button id="btn-ask" class="btn btn-info" disabled>
                <span class="btn-icon">❓</span> Ask Question
            </button>
        </div>

        <!-- Question Input (for Ask) -->
        <div class="question-input" id="question-input" style="display: none;">
            <input type="text" id="question-text" class="form-control" placeholder="What would you like to know about this frame?">
            <button id="btn-submit-question" class="btn btn-primary">Submit</button>
        </div>

        <!-- Results Panel -->
        <div class="results-panel" id="results-panel">
            <div class="results-header">
                <h3>Analysis Results</h3>
                <span class="results-time" id="results-time"></span>
            </div>
            <div class="results-content" id="results-content">
                <p class="results-placeholder">Run an analysis to see results</p>
            </div>
        </div>

        <!-- Loading Overlay -->
        <div class="loading-overlay" id="loading-overlay" style="display: none;">
            <div class="spinner"></div>
            <p>Analyzing frame... (~17 seconds)</p>
        </div>
    </div>
</div>
```

### Task 2.2: Create VLM JavaScript Client

Create file: `/ganuda/sag/static/js/vlm-client.js`

```javascript
/**
 * VLM Client - SAG Camera Tab Integration
 * Cherokee AI Federation - January 2026
 */

const VLMClient = {
    apiBase: '/api/vlm',
    currentFrame: null,

    /**
     * Initialize the VLM client
     */
    init: function() {
        this.checkHealth();
        this.loadFrames();
        this.bindEvents();

        // Refresh health every 30 seconds
        setInterval(() => this.checkHealth(), 30000);
    },

    /**
     * Check VLM service health
     */
    checkHealth: async function() {
        const statusDot = document.querySelector('#vlm-status .status-dot');
        const statusText = document.querySelector('#vlm-status .status-text');

        try {
            const response = await fetch(`${this.apiBase}/health`);
            const data = await response.json();

            if (data.status === 'healthy') {
                statusDot.className = 'status-dot healthy';
                statusText.textContent = `VLM Ready (${data.model || 'Qwen2-VL-7B'})`;
                this.enableControls(true);
            } else {
                statusDot.className = 'status-dot unhealthy';
                statusText.textContent = 'VLM Unavailable';
                this.enableControls(false);
            }
        } catch (error) {
            statusDot.className = 'status-dot unhealthy';
            statusText.textContent = 'VLM Connection Error';
            this.enableControls(false);
        }
    },

    /**
     * Load available frames
     */
    loadFrames: async function() {
        const select = document.getElementById('frame-select');

        try {
            const response = await fetch(`${this.apiBase}/frames`);
            const data = await response.json();

            select.innerHTML = '<option value="">-- Select a frame --</option>';

            data.frames.forEach(frame => {
                const option = document.createElement('option');
                option.value = frame.path;
                option.textContent = `${frame.relative} (${frame.camera_id})`;
                select.appendChild(option);
            });

            if (data.total > 50) {
                const option = document.createElement('option');
                option.disabled = true;
                option.textContent = `... and ${data.total - 50} more`;
                select.appendChild(option);
            }
        } catch (error) {
            console.error('Failed to load frames:', error);
        }
    },

    /**
     * Bind UI event handlers
     */
    bindEvents: function() {
        // Frame selection
        document.getElementById('frame-select').addEventListener('change', (e) => {
            this.selectFrame(e.target.value);
        });

        document.getElementById('manual-path').addEventListener('blur', (e) => {
            if (e.target.value) {
                this.selectFrame(e.target.value);
            }
        });

        document.getElementById('refresh-frames').addEventListener('click', () => {
            this.loadFrames();
        });

        // Analysis buttons
        document.getElementById('btn-describe').addEventListener('click', () => {
            this.describe();
        });

        document.getElementById('btn-analyze').addEventListener('click', () => {
            this.analyze();
        });

        document.getElementById('btn-ask').addEventListener('click', () => {
            this.showQuestionInput();
        });

        document.getElementById('btn-submit-question').addEventListener('click', () => {
            const question = document.getElementById('question-text').value;
            if (question.trim()) {
                this.ask(question);
            }
        });

        // Enter key for question
        document.getElementById('question-text').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                const question = e.target.value;
                if (question.trim()) {
                    this.ask(question);
                }
            }
        });
    },

    /**
     * Select a frame for analysis
     */
    selectFrame: function(path) {
        this.currentFrame = path;
        const preview = document.getElementById('frame-preview');

        if (path) {
            // For security, we can't directly show file:// paths
            // Show path info instead
            preview.innerHTML = `
                <div class="frame-info">
                    <p><strong>Selected:</strong> ${path}</p>
                    <p class="frame-hint">Frame will be analyzed on the server</p>
                </div>
            `;
            this.enableAnalysisButtons(true);
        } else {
            preview.innerHTML = '<div class="preview-placeholder"><span>Select a frame to preview</span></div>';
            this.enableAnalysisButtons(false);
        }
    },

    /**
     * Enable/disable controls based on VLM health
     */
    enableControls: function(enabled) {
        // Will be further controlled by frame selection
        if (!enabled) {
            this.enableAnalysisButtons(false);
        }
    },

    /**
     * Enable/disable analysis buttons
     */
    enableAnalysisButtons: function(enabled) {
        document.getElementById('btn-describe').disabled = !enabled;
        document.getElementById('btn-analyze').disabled = !enabled;
        document.getElementById('btn-ask').disabled = !enabled;
    },

    /**
     * Show loading overlay
     */
    showLoading: function(show) {
        document.getElementById('loading-overlay').style.display = show ? 'flex' : 'none';
    },

    /**
     * Display results
     */
    showResults: function(results, type) {
        const content = document.getElementById('results-content');
        const timeEl = document.getElementById('results-time');

        timeEl.textContent = new Date().toLocaleTimeString();

        if (!results.success) {
            content.innerHTML = `
                <div class="result-error">
                    <strong>Error:</strong> ${results.error || 'Unknown error'}
                </div>
            `;
            return;
        }

        let html = '';

        if (type === 'describe') {
            html = `
                <div class="result-description">
                    <h4>Frame Description</h4>
                    <p>${results.description}</p>
                    <div class="result-meta">
                        <span>Camera: ${results.camera_id}</span>
                        <span>Latency: ${results.latency_ms?.toFixed(0) || '?'}ms</span>
                    </div>
                </div>
            `;
        } else if (type === 'analyze') {
            const assessmentClass = {
                'normal': 'assessment-normal',
                'concerning': 'assessment-concerning',
                'critical': 'assessment-critical'
            }[results.assessment] || 'assessment-unknown';

            html = `
                <div class="result-analysis">
                    <h4>Anomaly Analysis</h4>
                    <div class="assessment ${assessmentClass}">
                        <span class="assessment-label">${(results.assessment || 'unknown').toUpperCase()}</span>
                        <span class="assessment-confidence">Confidence: ${results.confidence || 'unknown'}</span>
                    </div>
                    <p class="assessment-reason">${results.reason || 'No details provided'}</p>
                    ${results.human_review_required ? '<div class="human-review-alert">⚠️ Human review required for critical assessment</div>' : ''}
                </div>
            `;
        } else if (type === 'ask') {
            html = `
                <div class="result-answer">
                    <h4>Q&A</h4>
                    <p class="question"><strong>Q:</strong> ${results.question}</p>
                    <p class="answer"><strong>A:</strong> ${results.answer}</p>
                </div>
            `;
        }

        // Add AI disclosure
        if (results.ai_disclosure) {
            html += `<div class="ai-disclosure">${results.ai_disclosure}</div>`;
        }

        content.innerHTML = html;
    },

    /**
     * Describe the current frame
     */
    describe: async function() {
        if (!this.currentFrame) return;

        this.showLoading(true);
        const cameraId = document.getElementById('camera-id').value || 'unknown';

        try {
            const response = await fetch(`${this.apiBase}/describe`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    image_path: this.currentFrame,
                    camera_id: cameraId
                })
            });
            const results = await response.json();
            this.showResults(results, 'describe');
        } catch (error) {
            this.showResults({success: false, error: error.message}, 'describe');
        } finally {
            this.showLoading(false);
        }
    },

    /**
     * Analyze frame for anomalies
     */
    analyze: async function() {
        if (!this.currentFrame) return;

        this.showLoading(true);
        const cameraId = document.getElementById('camera-id').value || 'unknown';

        try {
            const response = await fetch(`${this.apiBase}/analyze`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    image_path: this.currentFrame,
                    camera_id: cameraId
                })
            });
            const results = await response.json();
            this.showResults(results, 'analyze');
        } catch (error) {
            this.showResults({success: false, error: error.message}, 'analyze');
        } finally {
            this.showLoading(false);
        }
    },

    /**
     * Show question input
     */
    showQuestionInput: function() {
        const input = document.getElementById('question-input');
        input.style.display = input.style.display === 'none' ? 'flex' : 'none';
        if (input.style.display === 'flex') {
            document.getElementById('question-text').focus();
        }
    },

    /**
     * Ask a question about the frame
     */
    ask: async function(question) {
        if (!this.currentFrame || !question) return;

        this.showLoading(true);
        const cameraId = document.getElementById('camera-id').value || 'unknown';

        try {
            const response = await fetch(`${this.apiBase}/ask`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    image_path: this.currentFrame,
                    question: question,
                    camera_id: cameraId
                })
            });
            const results = await response.json();
            this.showResults(results, 'ask');

            // Clear question input
            document.getElementById('question-text').value = '';
            document.getElementById('question-input').style.display = 'none';
        } catch (error) {
            this.showResults({success: false, error: error.message}, 'ask');
        } finally {
            this.showLoading(false);
        }
    }
};

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
    // Only init if camera tab exists
    if (document.getElementById('camera-tab')) {
        VLMClient.init();
    }
});
```

### Task 2.3: Create Camera Tab CSS

Create file: `/ganuda/sag/static/css/camera-tab.css`

```css
/* Camera Tab Styles - Cherokee AI Federation */

.camera-container {
    padding: 20px;
    max-width: 1200px;
    margin: 0 auto;
}

.camera-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 10px;
    border-bottom: 2px solid var(--border-color, #e0e0e0);
}

.camera-header h2 {
    margin: 0;
    color: var(--text-primary, #333);
}

/* VLM Status Indicator */
.vlm-status {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 16px;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 20px;
}

.status-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    background: #999;
}

.status-dot.healthy {
    background: #4caf50;
    box-shadow: 0 0 8px rgba(76, 175, 80, 0.5);
}

.status-dot.unhealthy {
    background: #f44336;
    box-shadow: 0 0 8px rgba(244, 67, 54, 0.5);
}

.status-text {
    font-size: 0.9em;
    color: var(--text-secondary, #666);
}

/* Privacy Notice */
.privacy-notice {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: #e3f2fd;
    border-left: 4px solid #2196f3;
    border-radius: 4px;
    margin-bottom: 20px;
    font-size: 0.9em;
    color: #1565c0;
}

/* Frame Selection */
.frame-selection {
    display: grid;
    grid-template-columns: 2fr 1fr 2fr;
    gap: 16px;
    margin-bottom: 20px;
}

.frame-input-group {
    display: flex;
    flex-direction: column;
    gap: 4px;
}

.frame-input-group label {
    font-size: 0.85em;
    font-weight: 500;
    color: var(--text-secondary, #666);
}

.frame-input-group select,
.frame-input-group input {
    padding: 8px 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
    font-size: 0.95em;
}

#refresh-frames {
    margin-top: 20px;
    padding: 8px 12px;
}

/* Frame Preview */
.frame-preview {
    min-height: 200px;
    background: var(--bg-secondary, #f5f5f5);
    border: 2px dashed var(--border-color, #ddd);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 20px;
}

.preview-placeholder {
    color: var(--text-secondary, #999);
    font-style: italic;
}

.frame-info {
    text-align: center;
    padding: 20px;
}

.frame-info p {
    margin: 8px 0;
}

.frame-hint {
    font-size: 0.85em;
    color: var(--text-secondary, #999);
}

/* Analysis Controls */
.analysis-controls {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
}

.analysis-controls .btn {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 20px;
    font-size: 1em;
}

.btn-icon {
    font-size: 1.2em;
}

/* Question Input */
.question-input {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.question-input input {
    flex: 1;
    padding: 12px;
    border: 1px solid var(--border-color, #ddd);
    border-radius: 4px;
}

/* Results Panel */
.results-panel {
    background: var(--bg-primary, #fff);
    border: 1px solid var(--border-color, #e0e0e0);
    border-radius: 8px;
    overflow: hidden;
}

.results-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background: var(--bg-secondary, #f5f5f5);
    border-bottom: 1px solid var(--border-color, #e0e0e0);
}

.results-header h3 {
    margin: 0;
    font-size: 1em;
}

.results-time {
    font-size: 0.85em;
    color: var(--text-secondary, #666);
}

.results-content {
    padding: 20px;
    min-height: 150px;
}

.results-placeholder {
    color: var(--text-secondary, #999);
    font-style: italic;
    text-align: center;
}

/* Result Types */
.result-description h4,
.result-analysis h4,
.result-answer h4 {
    margin: 0 0 12px 0;
    color: var(--text-primary, #333);
}

.result-meta {
    display: flex;
    gap: 20px;
    margin-top: 12px;
    font-size: 0.85em;
    color: var(--text-secondary, #666);
}

.result-error {
    padding: 12px;
    background: #ffebee;
    border-left: 4px solid #f44336;
    border-radius: 4px;
    color: #c62828;
}

/* Assessment Badges */
.assessment {
    display: inline-flex;
    flex-direction: column;
    padding: 12px 20px;
    border-radius: 8px;
    margin-bottom: 12px;
}

.assessment-normal {
    background: #e8f5e9;
    border: 1px solid #4caf50;
}

.assessment-concerning {
    background: #fff3e0;
    border: 1px solid #ff9800;
}

.assessment-critical {
    background: #ffebee;
    border: 1px solid #f44336;
}

.assessment-label {
    font-weight: bold;
    font-size: 1.1em;
}

.assessment-confidence {
    font-size: 0.85em;
    opacity: 0.8;
}

.assessment-reason {
    margin-top: 12px;
    line-height: 1.5;
}

.human-review-alert {
    margin-top: 12px;
    padding: 10px;
    background: #fff3e0;
    border-radius: 4px;
    color: #e65100;
    font-weight: 500;
}

/* Q&A */
.question {
    margin-bottom: 8px;
    color: var(--text-secondary, #666);
}

.answer {
    line-height: 1.6;
}

/* AI Disclosure */
.ai-disclosure {
    margin-top: 16px;
    padding: 8px 12px;
    background: var(--bg-secondary, #f5f5f5);
    border-radius: 4px;
    font-size: 0.8em;
    color: var(--text-secondary, #888);
    font-style: italic;
}

/* Loading Overlay */
.loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    z-index: 1000;
    color: white;
}

.spinner {
    width: 50px;
    height: 50px;
    border: 4px solid rgba(255, 255, 255, 0.3);
    border-top-color: white;
    border-radius: 50%;
    animation: spin 1s linear infinite;
    margin-bottom: 16px;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Responsive */
@media (max-width: 768px) {
    .frame-selection {
        grid-template-columns: 1fr;
    }

    .analysis-controls {
        flex-direction: column;
    }

    .analysis-controls .btn {
        width: 100%;
        justify-content: center;
    }
}
```

### Task 2.4: Integrate Camera Tab into SAG UI

Modify: `/ganuda/sag/templates/base.html` (or main template)

Add to navigation:

```html
<!-- Add to nav tabs -->
<li class="nav-item">
    <a class="nav-link" href="#" onclick="showTab('camera')">
        <span class="nav-icon">📷</span> Camera
    </a>
</li>
```

Add CSS include:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='css/camera-tab.css') }}">
```

Add JS include:

```html
<script src="{{ url_for('static', filename='js/vlm-client.js') }}"></script>
```

Include the camera tab partial:

```html
{% include 'partials/camera_tab.html' %}
```

## Phase 3: Testing

### Task 3.1: Create Test Script

Create file: `/ganuda/scripts/test_sag_vlm.sh`

```bash
#!/bin/bash
# Test SAG VLM Integration
# Run from redfin

SAG_URL="http://localhost:4000"
TEST_IMAGE="/ganuda/data/vision/frames/test/sample.jpg"

echo "=== SAG VLM Integration Tests ==="
echo ""

# Test 1: Health check
echo "1. VLM Health Check:"
curl -s "$SAG_URL/api/vlm/health" | python3 -m json.tool
echo ""

# Test 2: List frames
echo "2. List Frames:"
curl -s "$SAG_URL/api/vlm/frames" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Found {d[\"total\"]} frames')"
echo ""

# Test 3: Describe (if test image exists)
if [ -f "$TEST_IMAGE" ]; then
    echo "3. Describe Frame:"
    curl -s -X POST "$SAG_URL/api/vlm/describe" \
        -H "Content-Type: application/json" \
        -d "{\"image_path\": \"$TEST_IMAGE\", \"camera_id\": \"test\"}" | python3 -m json.tool
    echo ""

    echo "4. Analyze Frame:"
    curl -s -X POST "$SAG_URL/api/vlm/analyze" \
        -H "Content-Type: application/json" \
        -d "{\"image_path\": \"$TEST_IMAGE\", \"camera_id\": \"test\"}" | python3 -m json.tool
    echo ""

    echo "5. Ask Question:"
    curl -s -X POST "$SAG_URL/api/vlm/ask" \
        -H "Content-Type: application/json" \
        -d "{\"image_path\": \"$TEST_IMAGE\", \"question\": \"What do you see?\", \"camera_id\": \"test\"}" | python3 -m json.tool
else
    echo "3-5. Skipped (no test image at $TEST_IMAGE)"
    echo "    Create test images first with JR-SAG-TEST-IMAGES"
fi

echo ""
echo "=== Tests Complete ==="
```

## Acceptance Criteria

- [ ] VLM routes registered in SAG backend (`/api/vlm/*`)
- [ ] Path validation prevents directory traversal
- [ ] AI disclosure added to all VLM responses
- [ ] Human review flag for critical assessments
- [ ] Camera tab visible in SAG navigation
- [ ] Frame dropdown populates from server
- [ ] Describe button works and shows results
- [ ] Analyze button works and shows assessment badge
- [ ] Ask button works with question input
- [ ] Loading overlay shows during inference
- [ ] Error states handled gracefully
- [ ] VLM health status indicator works

## Rollback

If issues occur:

```bash
# Remove VLM routes
# Edit sag/app.py and remove vlm_bp registration
# Restart SAG
sudo systemctl restart sag.service
```

## Notes

- VLM inference takes ~17 seconds - loading overlay is important
- Images must exist on bluefin filesystem (path-based, not upload yet)
- API key is server-side only (Crawdad security requirement)
- Critical assessments flagged for human review (Turtle 7GEN requirement)

---
*Cherokee AI Federation - For Seven Generations*

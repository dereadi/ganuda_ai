#!/usr/bin/env python3
"""
Vision Training Web Interface ENHANCED - Phase 1
Cherokee Constitutional AI - Interactive Vision Training with Metrics

Phase 1 Features:
- Live training stats dashboard
- Confidence scoring display
- Activation pattern tracking
- Cherokee thermal metrics
"""
from flask import Flask, render_template, Response, jsonify, request
import subprocess
import requests
import base64
import time
from datetime import datetime
from pathlib import Path
import json

app = Flask(__name__)

# Configuration
VISION_JR_URL = "http://192.168.132.223:8013"
CAPTURE_DIR = Path.home() / "camera_captures"
CAPTURE_DIR.mkdir(exist_ok=True)

# Store recent analyses
recent_analyses = []

def capture_frame():
    """Capture single frame from camera"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    img_path = CAPTURE_DIR / f"frame_{timestamp}.jpg"

    try:
        result = subprocess.run([
            'ffmpeg', '-f', 'avfoundation',
            '-video_size', '1920x1080',
            '-framerate', '30',
            '-i', '0:none',  # Device 0, no audio
            '-frames:v', '1', '-y', str(img_path)
        ], capture_output=True, timeout=10, text=True)

        if img_path.exists():
            return img_path
        return None
    except Exception as e:
        print(f"Capture error: {e}")
        return None

def analyze_with_vision_jr(image_path, prompt="What object is this? Describe it in detail."):
    """Send image to Vision Jr. ENHANCED for analysis"""
    try:
        with open(image_path, 'rb') as f:
            response = requests.post(
                f"{VISION_JR_URL}/api/vision/analyze",
                files={'file': f},
                data={'prompt': prompt},
                timeout=60
            )

        if response.status_code == 200:
            result = response.json()
            # Enhanced API returns confidence, response_time, primary_object
            return {
                'analysis': result.get('response', result.get('analysis', 'No response')),
                'confidence': result.get('confidence', 0),
                'response_time': result.get('response_time', 0),
                'primary_object': result.get('primary_object', 'unknown')
            }
        else:
            return {'analysis': f"Error: {response.status_code}", 'confidence': 0, 'response_time': 0, 'primary_object': 'error'}

    except Exception as e:
        return {'analysis': f"Error: {str(e)}", 'confidence': 0, 'response_time': 0, 'primary_object': 'error'}

@app.route('/')
def index():
    """Main page with enhanced training interface"""
    return render_template('vision_training_enhanced.html')

@app.route('/capture_and_analyze', methods=['POST'])
def capture_and_analyze():
    """Capture image and get Vision Jr. ENHANCED analysis"""
    data = request.get_json()
    prompt = data.get('prompt', 'What object is this? Describe it in detail.')

    # Capture frame
    img_path = capture_frame()
    if not img_path:
        return jsonify({
            'success': False,
            'error': 'Failed to capture image from camera'
        })

    # Analyze with Vision Jr. ENHANCED
    analysis_result = analyze_with_vision_jr(img_path, prompt)

    # Read image as base64 for display
    with open(img_path, 'rb') as f:
        img_base64 = base64.b64encode(f.read()).decode('utf-8')

    result = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'image': f"data:image/jpeg;base64,{img_base64}",
        'analysis': analysis_result['analysis'],
        'confidence': analysis_result['confidence'],
        'response_time': analysis_result['response_time'],
        'primary_object': analysis_result['primary_object'],
        'image_path': str(img_path)
    }

    # Store recent analysis
    recent_analyses.insert(0, result)
    if len(recent_analyses) > 20:
        recent_analyses.pop()

    return jsonify(result)

@app.route('/video_feed')
def video_feed():
    """Capture a single preview frame"""
    img_path = capture_frame()
    if img_path and img_path.exists():
        with open(img_path, 'rb') as f:
            img_data = f.read()
        return Response(img_data, mimetype='image/jpeg')
    else:
        return jsonify({'error': 'No camera feed'}), 404

@app.route('/preview_frame')
def preview_frame():
    """Get a fresh preview frame"""
    img_path = capture_frame()
    if img_path and img_path.exists():
        with open(img_path, 'rb') as f:
            img_base64 = base64.b64encode(f.read()).decode('utf-8')
        return jsonify({'image': f"data:image/jpeg;base64,{img_base64}"})
    return jsonify({'error': 'Camera capture failed'}), 500

@app.route('/recent_analyses')
def get_recent_analyses():
    """Get recent analyses"""
    return jsonify(recent_analyses[:10])

@app.route('/training_stats')
def get_training_stats():
    """Get training statistics from Vision Jr. ENHANCED"""
    try:
        response = requests.get(f"{VISION_JR_URL}/api/vision/training_stats", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Stats unavailable'}), 500
    except:
        return jsonify({'error': 'Cannot connect to Vision Jr.'}), 500

@app.route('/activation_patterns')
def get_activation_patterns():
    """Get discovered activation patterns"""
    try:
        response = requests.get(f"{VISION_JR_URL}/api/vision/activation_patterns", timeout=5)
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': 'Patterns unavailable'}), 500
    except:
        return jsonify({'error': 'Cannot connect to Vision Jr.'}), 500

@app.route('/health')
def health():
    """Health check"""
    return jsonify({
        'status': 'healthy',
        'vision_jr': VISION_JR_URL,
        'capture_dir': str(CAPTURE_DIR),
        'recent_count': len(recent_analyses),
        'version': 'Enhanced Phase 1'
    })

# Create templates directory
templates_dir = Path(__file__).parent / 'templates'
templates_dir.mkdir(exist_ok=True)

# Create ENHANCED HTML template with live Cherokee metrics
html_template = '''<!DOCTYPE html>
<html>
<head>
    <title>👁️ Vision Jr. Training ENHANCED - Cherokee AI</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            padding: 20px;
        }
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            color: white;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }

        /* Stats Dashboard - NEW! */
        .stats-dashboard {
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        .thermal-bar {
            height: 30px;
            background: #ddd;
            border-radius: 15px;
            overflow: hidden;
            margin-top: 10px;
        }
        .thermal-fill {
            height: 100%;
            background: linear-gradient(90deg, #4ade80 0%, #f59e0b 50%, #ef4444 100%);
            transition: width 0.5s;
        }

        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        @media (max-width: 768px) {
            .main-content {
                grid-template-columns: 1fr;
            }
        }
        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }
        .card h2 {
            margin-bottom: 15px;
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        #cameraPreview {
            width: 100%;
            height: auto;
            border-radius: 10px;
            background: #f0f0f0;
            min-height: 300px;
            object-fit: contain;
        }
        .controls {
            margin-top: 15px;
        }
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 10px;
            margin-bottom: 10px;
        }
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .prompt-input {
            width: 100%;
            padding: 10px;
            border: 2px solid #667eea;
            border-radius: 8px;
            font-size: 1em;
            margin-bottom: 10px;
        }
        #analysisResult {
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            min-height: 150px;
            white-space: pre-wrap;
            line-height: 1.6;
        }
        .confidence-badge {
            display: inline-block;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
            margin: 10px 0;
        }
        .confidence-high { background: #4ade80; color: white; }
        .confidence-medium { background: #f59e0b; color: white; }
        .confidence-low { background: #ef4444; color: white; }

        .status {
            text-align: center;
            padding: 10px;
            background: rgba(255,255,255,0.2);
            border-radius: 8px;
            color: white;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>👁️ Vision Jr. Training ENHANCED</h1>
            <p class="subtitle">Cherokee Constitutional AI - Phase 1: Pre-warming + Confidence + Stats</p>
        </header>

        <div class="status" id="status">
            <span id="statusText">Loading Cherokee metrics...</span>
        </div>

        <!-- NEW: Stats Dashboard -->
        <div class="stats-dashboard">
            <h2 style="color: #667eea; margin-bottom: 15px;">🔥 Cherokee Training Metrics</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Total Analyses</div>
                    <div class="stat-value" id="statTotal">0</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Avg Confidence</div>
                    <div class="stat-value" id="statConfidence">0%</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Response Time</div>
                    <div class="stat-value" id="statTime">0s</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Thermal Temp 🔥</div>
                    <div class="stat-value" id="statThermal">0°</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Top Object</div>
                    <div class="stat-value" style="font-size: 1.2em;" id="statTopObject">—</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Learning Rate</div>
                    <div class="stat-value" id="statImprovement">0%</div>
                </div>
            </div>
            <div style="margin-top: 15px;">
                <div class="stat-label" style="color: #333;">Activation Switches Found: <span id="statPatterns">0</span></div>
                <div class="thermal-bar">
                    <div class="thermal-fill" id="thermalBar" style="width: 0%"></div>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="card">
                <h2>📷 Camera Feed</h2>
                <img id="cameraPreview" src="/video_feed" alt="Camera feed">
                <div class="controls">
                    <input type="text" class="prompt-input" id="promptInput"
                           placeholder="What should Vision Jr. look for?"
                           value="What object is this? Describe it in detail.">
                    <button onclick="captureAndAnalyze()" id="captureBtn">
                        📸 Capture & Analyze
                    </button>
                    <button onclick="quickIdentify()">
                        🔍 Quick Identify
                    </button>
                </div>
            </div>

            <div class="card">
                <h2>🧠 Vision Jr. Analysis</h2>
                <div id="analysisResult">
                    <p style="color: #999;">Hold up an object and click "Capture & Analyze"</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        let analysisCount = 0;

        function setStatus(text, isLoading = false) {
            const statusEl = document.getElementById('statusText');
            statusEl.textContent = text;
            document.getElementById('status').style.background =
                isLoading ? 'rgba(255, 165, 0, 0.3)' : 'rgba(255,255,255,0.2)';
        }

        function updateStats() {
            fetch('/training_stats')
                .then(r => r.json())
                .then(stats => {
                    document.getElementById('statTotal').textContent = stats.total_analyses || 0;
                    document.getElementById('statConfidence').textContent = (stats.avg_confidence || 0) + '%';
                    document.getElementById('statTime').textContent = (stats.avg_response_time || 0) + 's';
                    document.getElementById('statThermal').textContent = (stats.thermal_temperature || 0) + '°';
                    document.getElementById('statTopObject').textContent = stats.top_object || '—';
                    document.getElementById('statImprovement').textContent =
                        (stats.improvement_trend > 0 ? '+' : '') + (stats.improvement_trend || 0) + '%';
                    document.getElementById('statPatterns').textContent = stats.high_confidence_patterns || 0;

                    // Update thermal bar
                    const thermalPct = Math.min(100, stats.thermal_temperature || 0);
                    document.getElementById('thermalBar').style.width = thermalPct + '%';
                })
                .catch(e => console.error('Stats fetch failed:', e));
        }

        async function captureAndAnalyze() {
            const btn = document.getElementById('captureBtn');
            const resultDiv = document.getElementById('analysisResult');
            const prompt = document.getElementById('promptInput').value;

            btn.disabled = true;
            setStatus('📸 Capturing and analyzing...', true);
            resultDiv.innerHTML = '<div style="text-align: center; padding: 20px; color: #667eea;"><p>Vision Jr. is analyzing...</p></div>';

            try {
                const response = await fetch('/capture_and_analyze', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({prompt: prompt})
                });

                const data = await response.json();

                if (data.success) {
                    analysisCount++;

                    // Display with confidence badge
                    const confidence = data.confidence || 0;
                    let badgeClass = 'confidence-low';
                    if (confidence >= 80) badgeClass = 'confidence-high';
                    else if (confidence >= 60) badgeClass = 'confidence-medium';

                    resultDiv.innerHTML = `
                        <div class="confidence-badge ${badgeClass}">
                            Confidence: ${confidence}%
                        </div>
                        <p><strong>Object:</strong> ${data.primary_object}</p>
                        <p><strong>Time:</strong> ${data.response_time}s</p>
                        <hr style="margin: 10px 0;">
                        <p>${data.analysis}</p>
                    `;

                    setStatus(`✅ Analysis complete! Total: ${analysisCount}`);

                    // Update preview with captured image
                    document.getElementById('cameraPreview').src = data.image;

                    // Update stats
                    updateStats();
                } else {
                    resultDiv.textContent = '❌ Error: ' + data.error;
                    setStatus('❌ Error during analysis');
                }
            } catch (error) {
                resultDiv.textContent = '❌ Error: ' + error;
                setStatus('❌ Connection error');
            }

            btn.disabled = false;
        }

        function quickIdentify() {
            document.getElementById('promptInput').value = 'What object is this? Be specific.';
            captureAndAnalyze();
        }

        // Keyboard shortcut: Space to capture
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !e.target.matches('input')) {
                e.preventDefault();
                captureAndAnalyze();
            }
        });

        // Update stats every 5 seconds
        setInterval(updateStats, 5000);

        // Initial stats load
        updateStats();

        // Check health
        fetch('/health').then(r => r.json()).then(data => {
            setStatus(`✅ Connected to Vision Jr. ENHANCED`);
        });
    </script>
</body>
</html>''';

# Write HTML template
with open(templates_dir / 'vision_training_enhanced.html', 'w') as f:
    f.write(html_template)

if __name__ == '__main__':
    print("="*70)
    print("👁️ Vision Jr. Training Web Interface ENHANCED")
    print("="*70)
    print(f"Vision Jr. API: {VISION_JR_URL}")
    print(f"Capture directory: {CAPTURE_DIR}")
    print("")
    print("🔥 Phase 1 Features:")
    print("  ✅ Live Cherokee training metrics")
    print("  ✅ Confidence scoring display")
    print("  ✅ Activation pattern tracking")
    print("  ✅ Thermal temperature monitoring")
    print("")
    print("Starting server on http://0.0.0.0:5150")
    print("Access from any device on your network!")
    print("")
    print("Keyboard shortcuts:")
    print("  Space - Capture and analyze")
    print("")

    app.run(host='0.0.0.0', port=5150, debug=False)

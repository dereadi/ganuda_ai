# JR Instruction: Cherokee Audio Studio AI Enhancement
## Task ID: AUDIO-AI-001
## Priority: P2
## Target: sasass, sasass2, bmasass (Mac Studios + M4 Max)

---

## Objective

Upgrade Cherokee Audio Studio from FFmpeg-based processing to state-of-the-art AI audio separation and restoration using Demucs, MLX, and diffusion models.

---

## Current State

The Cherokee Audio Studio at `/ganuda/pathfinder/pathfinder-audio-studio/` uses:
- FFmpeg for noise reduction, EQ, dynamics
- Basic highpass/lowpass filters
- afftdn for noise removal
- compand for compression

**Limitation**: No true source separation - just filtering.

---

## Enhancement Goals

### 1. Demucs Integration (Primary)

Add HT-Demucs (Hybrid Transformer Demucs) for 6-source separation:
- Vocals
- Drums
- Bass
- Guitar
- Piano
- Other

**Research**: [Stemuc Audio Forge Paper (SBrT 2025)](https://www.researchgate.net/publication/396205016_Stemuc_Audio_Forge_AI-based_Music_Source_Separation_Using_Demucs_and_CUDA_Acceleration)

### 2. MLX for Apple Silicon

Deploy audio models using Apple's MLX framework on:
- bmasass (M4 Max, 128GB) - Primary
- sasass (M2 Ultra, 64GB) - Secondary
- sasass2 (M2 Ultra, 64GB) - Backup

**Research**: [Apple WWDC 2025 MLX Session](https://developer.apple.com/videos/play/wwdc2025/298/)

### 3. Diffusion-Based Restoration

Implement diffusion models for:
- Noise removal from bootleg recordings
- Bandwidth extension (restore lost frequencies)
- Artifact removal

**Research**: [Diffusion Models for Audio Restoration (arXiv)](https://arxiv.org/abs/2402.09821)

---

## Implementation Steps

### Step 1: Install Demucs on sasass

```bash
# SSH to sasass
ssh sasass

# Create audio processing environment
cd /Users/Shared/ganuda
python3 -m venv audio_ai_env
source audio_ai_env/bin/activate

# Install demucs
pip install demucs torch torchaudio
```

### Step 2: Test Demucs Separation

```bash
# Separate a test file into stems
demucs --two-stems=vocals /path/to/test.mp3

# Full 6-stem separation
demucs -n htdemucs_6s /path/to/test.mp3
```

### Step 3: Create Enhanced Audio Processor

Create `/Users/Shared/ganuda/services/cherokee_demucs_processor.py`:

```python
#!/usr/bin/env python3
"""
Cherokee AI Audio Studio - Demucs Integration
AI-powered source separation for Beatles Black Album remastering
"""

import subprocess
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CherokeeDemucsProcessor:
    def __init__(self, workspace: Path = None):
        self.workspace = workspace or Path("/Users/Shared/ganuda/audio_workspace")
        self.workspace.mkdir(exist_ok=True)

        # Demucs models
        self.models = {
            "htdemucs": "4 stems (vocals, drums, bass, other)",
            "htdemucs_ft": "4 stems fine-tuned (slower, better)",
            "htdemucs_6s": "6 stems (+ guitar, piano)"
        }

    def separate_stems(self, audio_path: Path, model: str = "htdemucs") -> dict:
        """
        Separate audio into stems using Demucs

        Returns dict with paths to separated stems
        """
        output_dir = self.workspace / "separated" / audio_path.stem

        cmd = [
            "demucs",
            "-n", model,
            "-o", str(output_dir),
            str(audio_path)
        ]

        logger.info(f"Separating {audio_path.name} with {model}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"Demucs failed: {result.stderr}")
            return {"error": result.stderr}

        # Find separated files
        stems_dir = output_dir / model / audio_path.stem
        stems = {}
        for stem_file in stems_dir.glob("*.wav"):
            stems[stem_file.stem] = str(stem_file)

        return {
            "success": True,
            "model": model,
            "stems": stems,
            "output_dir": str(stems_dir)
        }

    def isolate_vocals(self, audio_path: Path) -> str:
        """Quick vocal isolation for Beatles tracks"""
        result = self.separate_stems(audio_path, "htdemucs")
        if result.get("success"):
            return result["stems"].get("vocals", "")
        return ""

    def remaster_with_stems(self, audio_path: Path) -> dict:
        """
        Full remastering workflow:
        1. Separate into stems
        2. Process each stem (EQ, compression)
        3. Remix with balanced levels
        """
        # Step 1: Separate
        stems = self.separate_stems(audio_path, "htdemucs_6s")
        if not stems.get("success"):
            return stems

        # Step 2: Process each stem (to be enhanced)
        # For now, just return separated stems

        return {
            "original": str(audio_path),
            "separated_stems": stems["stems"],
            "ready_for_mixing": True
        }


if __name__ == "__main__":
    processor = CherokeeDemucsProcessor()
    print("Cherokee Demucs Processor initialized")
    print(f"Available models: {processor.models}")
```

### Step 4: Create Flask API Service

Create `/Users/Shared/ganuda/services/audio_ai_api.py`:

```python
#!/usr/bin/env python3
"""
Cherokee Audio AI API - REST endpoints for stem separation
"""

from flask import Flask, request, jsonify, send_file
from pathlib import Path
from cherokee_demucs_processor import CherokeeDemucsProcessor

app = Flask(__name__)
processor = CherokeeDemucsProcessor()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status": "ok",
        "service": "Cherokee Audio AI",
        "models": processor.models
    })

@app.route('/api/v1/separate', methods=['POST'])
def separate_audio():
    """
    POST /api/v1/separate
    Body: multipart/form-data with 'audio' file
    Optional: model (htdemucs, htdemucs_ft, htdemucs_6s)
    """
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    model = request.form.get('model', 'htdemucs')

    # Save uploaded file
    upload_path = Path("/tmp") / audio_file.filename
    audio_file.save(upload_path)

    # Process
    result = processor.separate_stems(upload_path, model)

    return jsonify(result)

@app.route('/api/v1/vocals', methods=['POST'])
def isolate_vocals():
    """Quick vocal isolation endpoint"""
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    upload_path = Path("/tmp") / audio_file.filename
    audio_file.save(upload_path)

    vocal_path = processor.isolate_vocals(upload_path)

    if vocal_path:
        return send_file(vocal_path, as_attachment=True)
    return jsonify({"error": "Vocal isolation failed"}), 500

if __name__ == '__main__':
    print("Starting Cherokee Audio AI API on port 8002")
    app.run(host='0.0.0.0', port=8002)
```

---

## Performance Expectations

| Operation | Hardware | Time (3-min song) |
|-----------|----------|-------------------|
| 4-stem separation | GPU (CUDA) | ~10 seconds |
| 4-stem separation | CPU | ~5 minutes |
| 4-stem separation | M4 Max | ~1 minute (estimate) |
| 6-stem separation | M4 Max | ~2 minutes (estimate) |

---

## Integration with Existing Studio

Update `cherokee_multi_llm_audio_processor.py` to:
1. First separate with Demucs
2. Then apply FFmpeg processing to individual stems
3. Remix stems for final output

---

## Beatles Black Album Remaster Workflow

1. **Input**: Original bootleg recording
2. **Separate**: Demucs 6-stem separation
3. **Process per stem**:
   - Vocals: De-noise, clarity enhancement
   - Drums: Transient shaping, punch
   - Bass: Low-end EQ, compression
   - Guitar: Presence, stereo widening
   - Piano: Clean-up, sustain
4. **Remix**: Balance stems, stereo imaging
5. **Master**: Final limiting, loudness normalization

---

## Verification

```bash
# Test Demucs installation
demucs --help

# Test on sample file
demucs -n htdemucs_6s /path/to/beatles_sample.mp3

# Check output
ls separated/htdemucs_6s/beatles_sample/
# Should see: vocals.wav, drums.wav, bass.wav, guitar.wav, piano.wav, other.wav
```

---

## Sources

- [Demucs GitHub](https://github.com/facebookresearch/demucs)
- [HT-Demucs Paper](https://arxiv.org/pdf/1911.13254)
- [Stemuc Audio Forge (SBrT 2025)](https://www.researchgate.net/publication/396205016)
- [Apple MLX Framework](https://github.com/ml-explore/mlx)
- [Diffusion Models for Audio (arXiv)](https://arxiv.org/abs/2402.09821)

---

*Cherokee AI Federation - For Seven Generations*
*Enhancing the Sacred Sound of the Beatles Black Album*

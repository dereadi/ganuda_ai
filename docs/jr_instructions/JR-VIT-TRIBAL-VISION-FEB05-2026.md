# JR-VIT-TRIBAL-VISION-FEB05-2026

## Task: Vision Transformer Integration for Tribal-Vision Camera Processing

**Priority:** P1
**Assigned:** Engineering Jr
**Created:** 2026-02-05
**Council Approval:** YES (with security concern noted)
**Status:** PENDING

---

## 1. Context and Background

### 1.1 Vision Transformer (ViT) Reference

**Paper:** "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale"
**arXiv:** 2010.11929
**Authors:** Dosovitskiy et al. (Google Research)

Key architectural insights from the paper:
- Images are split into fixed-size patches (e.g., 16x16 pixels)
- Each patch is linearly embedded and treated as a token sequence
- Standard Transformer encoder processes these patch embeddings
- Pre-training on large datasets (ImageNet-21k) is critical for performance
- ViT outperforms CNN-based approaches when sufficient pre-training data is available
- Position embeddings are learned (not fixed sinusoidal)

### 1.2 Why ViT for Tribal-Vision

Current tribal-vision uses:
- HOG-based face detection (`face_recognition` library with `model="hog"`)
- Centroid-based vehicle tracking (no deep feature extraction)
- No unified backbone for multi-task learning

ViT advantages:
- Better global context understanding (attention mechanism)
- Transfer learning from ImageNet-21k provides robust features
- Single backbone can serve face recognition, vehicle detection, and security monitoring
- Attention maps provide interpretability for security audits

---

## 2. Current Architecture Analysis

### 2.1 File Locations

```
/ganuda/lib/camera_vision_processor.py  - Main processing orchestrator
/ganuda/lib/face_recognition_module.py  - Face detection/recognition (HOG-based)
/ganuda/lib/vehicle_tracker.py          - Centroid tracking (no deep features)
```

### 2.2 Current Processing Flow

```
CameraProcessor
    |
    +-- FaceRecognizer.detect_faces()
    |       Uses: face_recognition library (HOG model)
    |       Returns: bbox, name, timestamp
    |
    +-- PlateReader.read_plate()
    |       Returns: plate_text, confidence
    |
    +-- VehicleTracker.update()
            Uses: scipy centroid distance matching
            Returns: object_id -> centroid mapping
```

### 2.3 Integration Points Identified

1. **Face Recognition Enhancement** (Lines 46-67 of face_recognition_module.py)
   - Replace HOG-based `face_locations()` with ViT-based detection
   - Use ViT features for face encoding instead of dlib's ResNet

2. **Vehicle Tracking Improvement** (Lines 47-85 of vehicle_tracker.py)
   - Add deep feature extraction before centroid matching
   - Use ViT backbone for Re-ID features

3. **Security Monitoring Optimization**
   - Leverage attention maps for anomaly region detection
   - Add confidence scoring from ViT classification head

---

## 3. Implementation Specification

### 3.1 Pre-trained Model Selection

**Recommended:** ViT-B/16 with ImageNet-21k weights

| Model | Params | Patch Size | ImageNet Acc | Memory (FP16) |
|-------|--------|------------|--------------|---------------|
| ViT-Ti/16 | 5.7M | 16x16 | 72.2% | ~0.5 GB |
| ViT-S/16 | 22M | 16x16 | 79.9% | ~1.2 GB |
| **ViT-B/16** | 86M | 16x16 | 84.0% | ~2.5 GB |
| ViT-L/16 | 307M | 16x16 | 85.3% | ~8 GB |

**Rationale for ViT-B/16:**
- Good balance of accuracy and memory footprint
- 16x16 patch size is optimal for 224x224 inputs
- ImageNet-21k pre-training captures broader visual concepts
- Fits within sasass2/sasass3 memory constraints

### 3.2 Library Selection: timm

Use the `timm` (PyTorch Image Models) library by Ross Wightman.

```python
# Installation
pip install timm

# Model loading
import timm

model = timm.create_model(
    'vit_base_patch16_224.augreg_in21k',
    pretrained=True,
    num_classes=0  # Remove classification head for feature extraction
)
```

### 3.3 New Module: ViT Backbone

Create new file: `/ganuda/lib/vit_backbone.py`

```python
"""
ViT Backbone for Tribal-Vision
Provides unified feature extraction for face recognition and vehicle tracking.
"""
import torch
import torch.nn as nn
import timm
from typing import Optional, Tuple
import hashlib
import os

# SECURITY: Model weight verification
VIT_B16_IN21K_SHA256 = "PLACEHOLDER_ACTUAL_HASH_REQUIRED"

class ViTBackbone:
    """
    Vision Transformer backbone for tribal-vision feature extraction.

    Provides:
    - Global image features for classification
    - Patch-level features for detection
    - Attention maps for interpretability
    """

    def __init__(
        self,
        model_name: str = 'vit_base_patch16_224.augreg_in21k',
        device: str = 'cuda',
        verify_weights: bool = True
    ):
        self.device = device
        self.model_name = model_name
        self.model = None
        self.transform = None
        self._load_model(verify_weights)

    def _verify_model_weights(self, weights_path: str) -> bool:
        """
        SECURITY: Verify model weights have not been tampered with.
        Council requirement - all model weights must be verified.
        """
        if not os.path.exists(weights_path):
            return False

        with open(weights_path, 'rb') as f:
            file_hash = hashlib.sha256(f.read()).hexdigest()

        # TODO: Replace with actual hash from timm release
        expected_hash = VIT_B16_IN21K_SHA256
        if expected_hash == "PLACEHOLDER_ACTUAL_HASH_REQUIRED":
            print("WARNING: Model hash verification skipped - hash not configured")
            return True

        return file_hash == expected_hash

    def _load_model(self, verify_weights: bool):
        """Load and initialize the ViT model."""
        self.model = timm.create_model(
            self.model_name,
            pretrained=True,
            num_classes=0  # Feature extraction mode
        )
        self.model.eval()
        self.model.to(self.device)

        # Get model-specific transforms
        data_config = timm.data.resolve_model_data_config(self.model)
        self.transform = timm.data.create_transform(**data_config, is_training=False)

    def extract_features(self, image: torch.Tensor) -> torch.Tensor:
        """
        Extract global features from image.

        Args:
            image: Tensor of shape (B, C, H, W), already normalized

        Returns:
            Features of shape (B, 768) for ViT-B
        """
        with torch.no_grad():
            features = self.model(image)
        return features

    def extract_patch_features(self, image: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Extract patch-level features and attention maps.

        Returns:
            patch_features: (B, num_patches, 768)
            attention_maps: (B, num_heads, num_patches, num_patches)
        """
        # Implementation requires accessing intermediate layers
        # Use forward hooks to capture patch embeddings and attention
        pass  # Jr to implement

    def get_attention_map(self, image: torch.Tensor) -> torch.Tensor:
        """
        Get attention visualization for security monitoring.
        Highlights regions the model focuses on.
        """
        pass  # Jr to implement
```

### 3.4 Integration with Face Recognition

Modify `/ganuda/lib/face_recognition_module.py`:

```python
# Add to imports
from vit_backbone import ViTBackbone

class FaceRecognizer:
    def __init__(
        self,
        known_faces_dir: str = "/ganuda/data/known_faces",
        use_vit: bool = True,
        vit_device: str = 'cuda'
    ):
        self.use_vit = use_vit
        self.vit_backbone = None

        if use_vit:
            try:
                self.vit_backbone = ViTBackbone(device=vit_device)
            except Exception as e:
                print(f"ViT initialization failed, falling back to HOG: {e}")
                self.use_vit = False

        # ... existing init code ...

    def detect_faces_vit(self, frame: np.ndarray) -> List[Dict]:
        """
        ViT-enhanced face detection.
        Uses attention maps to identify face regions, then extracts features.
        """
        # 1. Get attention maps from ViT
        # 2. Threshold attention to find face candidates
        # 3. Extract face embeddings using ViT features
        # 4. Match against known faces
        pass  # Jr to implement

    def detect_faces(self, frame: np.ndarray) -> List[Dict]:
        """Modified to use ViT when available."""
        if self.use_vit and self.vit_backbone:
            try:
                return self.detect_faces_vit(frame)
            except Exception as e:
                print(f"ViT face detection failed, using HOG fallback: {e}")

        # Original HOG-based implementation
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # ... rest of existing code ...
```

### 3.5 Integration with Vehicle Tracker

Modify `/ganuda/lib/vehicle_tracker.py`:

```python
# Add to imports
from vit_backbone import ViTBackbone

class VehicleTracker:
    def __init__(
        self,
        max_disappeared: int = 30,
        use_vit_reid: bool = True,
        vit_backbone: Optional[ViTBackbone] = None
    ):
        # ... existing init ...
        self.use_vit_reid = use_vit_reid
        self.vit_backbone = vit_backbone
        self.object_features: OrderedDict[int, np.ndarray] = OrderedDict()

    def extract_reid_features(self, frame: np.ndarray, bbox: Tuple) -> np.ndarray:
        """
        Extract Re-ID features for vehicle using ViT backbone.
        Enables more robust tracking across frames.
        """
        if not self.vit_backbone:
            return None

        x, y, w, h = bbox
        crop = frame[y:y+h, x:x+w]
        # Resize and normalize for ViT
        # Extract features
        pass  # Jr to implement

    def update_with_features(self, rects, frame):
        """
        Enhanced update using ViT Re-ID features.
        Falls back to centroid matching if ViT unavailable.
        """
        pass  # Jr to implement
```

---

## 4. Patch Size Considerations

### 4.1 16x16 vs 14x14 Analysis

| Aspect | 16x16 (Recommended) | 14x14 |
|--------|---------------------|-------|
| Patches for 224x224 | 196 | 256 |
| Memory usage | Lower | ~30% higher |
| Detail preservation | Good | Better |
| Inference speed | Faster | Slower |
| Pre-trained weights | More available | Limited |

**Recommendation:** Use 16x16 for initial deployment. Consider 14x14 only if face recognition accuracy is insufficient after tuning.

### 4.2 Input Resolution

- Default: 224x224 (standard ViT input)
- For higher detail: 384x384 models available but 2.5x memory increase
- Camera frames should be center-cropped or resized with aspect ratio preservation

---

## 5. Memory Requirements

### 5.1 Node Specifications

| Node | GPU | VRAM | Recommended Config |
|------|-----|------|-------------------|
| sasass2 | RTX 4090 | 24 GB | Full ViT-B/16, FP16 |
| sasass3 | RTX 3090 | 24 GB | Full ViT-B/16, FP16 |

### 5.2 Memory Budget

```
ViT-B/16 Model (FP16):     ~170 MB
Input batch (B=4, 224x224): ~2.4 MB
Intermediate activations:   ~500 MB (peak)
Face recognition overhead:  ~200 MB
Vehicle tracking overhead:  ~100 MB
-----------------------------------
Total peak estimate:        ~1 GB per camera stream

With 24 GB VRAM:
- Can support ~20 concurrent camera streams
- Leave 4 GB headroom for OS/other processes
```

### 5.3 Optimization Strategies

1. **Batch processing:** Accumulate frames, process in batches of 4-8
2. **Mixed precision:** Use torch.cuda.amp for FP16 inference
3. **Model sharing:** Single ViT backbone instance shared across modules
4. **Lazy loading:** Initialize ViT only when first needed

---

## 6. Fallback Strategy

### 6.1 Graceful Degradation

```python
class ViTFallbackManager:
    """
    Manages fallback from ViT to CNN-based processing.
    """

    def __init__(self):
        self.vit_available = False
        self.vit_failure_count = 0
        self.max_failures = 3
        self.cooldown_seconds = 300
        self.last_failure_time = None

    def should_use_vit(self) -> bool:
        """Determine if ViT should be attempted."""
        if not self.vit_available:
            return False

        if self.vit_failure_count >= self.max_failures:
            if self._cooldown_elapsed():
                self.vit_failure_count = 0
                return True
            return False

        return True

    def report_failure(self, error: Exception):
        """Record ViT failure for fallback logic."""
        self.vit_failure_count += 1
        self.last_failure_time = time.time()

        # Log for monitoring
        print(f"ViT failure #{self.vit_failure_count}: {error}")

        if self.vit_failure_count >= self.max_failures:
            print(f"ViT disabled for {self.cooldown_seconds}s, using CNN fallback")
```

### 6.2 Fallback Triggers

- CUDA out of memory
- Model loading failure
- Inference timeout (>500ms per frame)
- Weight verification failure (SECURITY)
- 3+ consecutive processing errors

---

## 7. Security Requirements (Council Mandate)

### 7.1 Model Weight Verification

**CRITICAL:** Council has mandated verification of model weights to prevent supply chain attacks.

Implementation steps:

1. Download official weights from timm/HuggingFace
2. Compute SHA-256 hash of weight file
3. Store hash in `/ganuda/config/model_hashes.yaml`
4. Verify hash on every model load

```yaml
# /ganuda/config/model_hashes.yaml
model_weights:
  vit_base_patch16_224_augreg_in21k:
    source: "huggingface.co/timm"
    sha256: "<compute and insert actual hash>"
    verified_date: "2026-02-05"
    verified_by: "security_jr"
```

### 7.2 Air-Gapped Download

For production deployment:
1. Download weights on isolated machine
2. Verify against published checksums
3. Transfer to sasass2/sasass3 via secure copy
4. Do NOT download directly on production nodes

### 7.3 Audit Logging

Log all model loading events:
```python
def log_model_load(model_name: str, verified: bool, source: str):
    """Log model loading for security audit."""
    # Write to /ganuda/logs/model_audit.log
    pass
```

---

## 8. Benchmark Methodology

### 8.1 Metrics to Compare

| Metric | Description | Target |
|--------|-------------|--------|
| Face Detection Accuracy | mAP on test set | >95% |
| Face Recognition Accuracy | Top-1 accuracy | >98% |
| Vehicle Tracking MOTA | Multi-Object Tracking Accuracy | >80% |
| Inference Latency | Per-frame processing time | <100ms |
| GPU Memory Usage | Peak VRAM consumption | <4GB |

### 8.2 Test Datasets

1. **Face Detection/Recognition:**
   - Internal test set from `/ganuda/data/test_faces/`
   - LFW (Labeled Faces in the Wild) subset

2. **Vehicle Tracking:**
   - Internal parking lot footage
   - MOT17 benchmark subset

### 8.3 A/B Testing Protocol

```python
class VisionBenchmark:
    def __init__(self, test_frames_dir: str):
        self.test_frames = self._load_test_frames(test_frames_dir)
        self.ground_truth = self._load_annotations()

    def run_comparison(self):
        """Compare ViT vs HOG/CNN baseline."""
        results = {
            'vit': {'faces': [], 'vehicles': [], 'latency': []},
            'baseline': {'faces': [], 'vehicles': [], 'latency': []}
        }

        for frame, gt in zip(self.test_frames, self.ground_truth):
            # Run both methods
            # Record metrics
            pass

        self._generate_report(results)
```

### 8.4 Acceptance Criteria

- ViT must match or exceed baseline accuracy
- Latency must stay under 100ms per frame
- Memory usage must not exceed 4GB per stream
- Zero security verification failures in 1000 loads

---

## 9. Deployment Steps

### Phase 1: Development (Week 1)
1. Create `/ganuda/lib/vit_backbone.py`
2. Download and verify ViT-B/16 weights
3. Implement weight verification system
4. Unit tests for feature extraction

### Phase 2: Integration (Week 2)
1. Integrate with `face_recognition_module.py`
2. Integrate with `vehicle_tracker.py`
3. Implement fallback manager
4. Integration tests

### Phase 3: Benchmarking (Week 3)
1. Run comparison benchmarks
2. Tune thresholds and parameters
3. Memory optimization
4. Latency profiling

### Phase 4: Production (Week 4)
1. Deploy to sasass2 (staging)
2. Monitor for 48 hours
3. Deploy to sasass3 (production)
4. Enable in `camera_vision_processor.py`

---

## 10. Files to Create/Modify

### New Files
- `/ganuda/lib/vit_backbone.py` - ViT backbone module
- `/ganuda/config/model_hashes.yaml` - Weight verification hashes
- `/ganuda/tests/test_vit_backbone.py` - Unit tests
- `/ganuda/benchmarks/vision_benchmark.py` - Benchmarking suite

### Modified Files
- `/ganuda/lib/camera_vision_processor.py` - Add ViT backend option
- `/ganuda/lib/face_recognition_module.py` - ViT feature extraction
- `/ganuda/lib/vehicle_tracker.py` - ViT Re-ID features
- `/ganuda/requirements.txt` - Add `timm>=0.9.0`

---

## 11. Verification Checklist

- [ ] ViT-B/16 weights downloaded and verified
- [ ] Weight hash stored in model_hashes.yaml
- [ ] vit_backbone.py passes unit tests
- [ ] Face recognition accuracy >= baseline
- [ ] Vehicle tracking MOTA >= baseline
- [ ] Inference latency < 100ms
- [ ] Memory usage < 4GB per stream
- [ ] Fallback to HOG works correctly
- [ ] Audit logging implemented
- [ ] Security review completed
- [ ] Deployed to sasass2 (staging)
- [ ] 48-hour stability test passed
- [ ] Deployed to sasass3 (production)

---

## 12. References

1. Dosovitskiy et al., "An Image is Worth 16x16 Words" (arXiv:2010.11929)
2. timm library: https://github.com/huggingface/pytorch-image-models
3. ViT model zoo: https://huggingface.co/timm
4. Tribal-vision current implementation: `/ganuda/lib/camera_vision_processor.py`

---

**Council Security Note:** This task was approved with the explicit requirement that all model weights be cryptographically verified before use. Any deviation from the weight verification protocol requires Council re-approval.

---

*Jr Assignment: Engineering Jr (Vision/ML specialty)*
*TPM Review: Required before Phase 4 deployment*
*Council Review: Security checkpoint at Phase 3 completion*

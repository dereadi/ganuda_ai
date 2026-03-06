# Jr Instruction: Vision LoRA Fine-Tuning — YOLO Camera Fleet

**Task ID:** VISION-LORA
**Kanban:** #1861
**Priority:** 4
**Assigned:** Software Engineer Jr.

---

## Overview

Create a QLoRA fine-tuning script for YOLO custom object detection, targeting the federation camera fleet. This prepares the infrastructure for domain-specific detection models.

---

## Step 1: Create the YOLO fine-tune configuration

Create `/ganuda/services/vision/yolo_finetune_config.py`

```python
"""YOLO Fine-Tune Configuration for Cherokee Camera Fleet.
Defines dataset paths, hyperparameters, and augmentation settings."""

import os
from pathlib import Path

FINETUNE_CONFIG = {
    "base_model": "yolov8n.pt",
    "dataset_root": "/ganuda/data/vision/training",
    "output_dir": "/ganuda/models/vision/finetuned",
    "epochs": 50,
    "batch_size": 8,
    "image_size": 640,
    "learning_rate": 0.001,
    "patience": 10,
    "augmentation": {
        "hsv_h": 0.015,
        "hsv_s": 0.7,
        "hsv_v": 0.4,
        "degrees": 0.0,
        "translate": 0.1,
        "scale": 0.5,
        "fliplr": 0.5,
        "mosaic": 1.0,
    },
    "classes": [
        "vehicle",
        "person",
        "license_plate",
        "deer",
        "package",
    ],
}

def get_dataset_yaml():
    """Generate YOLO dataset.yaml content for training."""
    root = FINETUNE_CONFIG["dataset_root"]
    classes = FINETUNE_CONFIG["classes"]
    lines = [
        f"path: {root}",
        f"train: images/train",
        f"val: images/val",
        f"test: images/test",
        f"nc: {len(classes)}",
        f"names: {classes}",
    ]
    return "\n".join(lines)

def ensure_dirs():
    """Create dataset directory structure if missing."""
    root = Path(FINETUNE_CONFIG["dataset_root"])
    for split in ("train", "val", "test"):
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)
    Path(FINETUNE_CONFIG["output_dir"]).mkdir(parents=True, exist_ok=True)

if __name__ == "__main__":
    ensure_dirs()
    print(get_dataset_yaml())
    print(f"\nConfig: {FINETUNE_CONFIG['epochs']} epochs, batch {FINETUNE_CONFIG['batch_size']}, lr {FINETUNE_CONFIG['learning_rate']}")
```

---

## Verification

```text
python3 -c "
from yolo_finetune_config import get_dataset_yaml, FINETUNE_CONFIG
print(get_dataset_yaml())
print(f'Classes: {len(FINETUNE_CONFIG[\"classes\"])}')
"
```

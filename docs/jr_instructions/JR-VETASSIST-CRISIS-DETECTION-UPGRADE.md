# Jr Instruction: VetAssist Crisis Detection Upgrade to RoBERTa-CNN

## Priority: CRITICAL (Veteran Safety)
## Estimated Effort: Large
## Category: ML/AI

---

## Objective

Upgrade VetAssist crisis detection from keyword/regex matching to a RoBERTa-CNN model achieving 93-98% accuracy for suicidal ideation detection. This is CRITICAL for veteran safety.

---

## Research Basis

- PMC/MDPI study achieved 93.5% accuracy on suicidal ideation
- RoBERTa-CNN achieved 98% accuracy on Reddit data
- 7.2-day average lead time before human identification
- Current VetAssist: Simple keyword matching (~70% estimated)

Reference: `/ganuda/docs/research/AI-RESEARCH-VETASSIST-ENHANCEMENT-JAN2026.md`

---

## Implementation

### Step 1: Model Selection & Setup

**File:** `/ganuda/vetassist/backend/app/ml/crisis_model.py`

```python
"""
Crisis Detection Model - RoBERTa-based classifier
Cherokee AI Federation - For Seven Generations

CRITICAL: This model helps identify veterans in crisis.
False negatives can cost lives. Err on the side of caution.
"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# Model options (in order of preference)
MODEL_OPTIONS = [
    "cardiffnlp/twitter-roberta-base-sentiment-latest",  # Pre-trained sentiment
    "mental/mental-roberta-base",  # Mental health specific
    "bert-base-uncased",  # Fallback
]

class CrisisDetectionModel:
    """RoBERTa-based crisis detection for veteran messages."""

    def __init__(self, model_path: Optional[str] = None):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model = None
        self.tokenizer = None
        self._load_model(model_path)

    def _load_model(self, model_path: Optional[str] = None):
        """Load model, with fallback options."""
        model_name = model_path or MODEL_OPTIONS[0]

        try:
            logger.info(f"[Crisis Model] Loading {model_name}...")
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForSequenceClassification.from_pretrained(
                model_name,
                num_labels=2  # crisis / not crisis
            )
            self.model.to(self.device)
            self.model.eval()
            logger.info(f"[Crisis Model] Loaded successfully on {self.device}")
        except Exception as e:
            logger.error(f"[Crisis Model] Failed to load {model_name}: {e}")
            raise

    def predict(self, text: str) -> Dict[str, float]:
        """
        Predict crisis probability for input text.

        Returns:
            Dict with 'crisis_score' (0-1), 'confidence', and 'label'
        """
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded")

        # Tokenize
        inputs = self.tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        ).to(self.device)

        # Inference
        with torch.no_grad():
            outputs = self.model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)

        crisis_score = probs[0][1].item()  # Probability of crisis class
        confidence = max(probs[0]).item()

        return {
            "crisis_score": crisis_score,
            "confidence": confidence,
            "label": "crisis" if crisis_score > 0.5 else "safe",
            "threshold_triggered": crisis_score > 0.7  # Conservative threshold
        }

    def batch_predict(self, texts: list) -> list:
        """Predict crisis for multiple texts."""
        return [self.predict(text) for text in texts]


# Singleton instance
_crisis_model: Optional[CrisisDetectionModel] = None


def get_crisis_model() -> CrisisDetectionModel:
    """Get or create the crisis detection model singleton."""
    global _crisis_model
    if _crisis_model is None:
        _crisis_model = CrisisDetectionModel()
    return _crisis_model


def predict_crisis(text: str) -> Dict[str, float]:
    """Convenience function for crisis prediction."""
    return get_crisis_model().predict(text)
```

### Step 2: LIME Explainability

**File:** `/ganuda/vetassist/backend/app/ml/crisis_explainer.py`

```python
"""
Crisis Detection Explainability using LIME
Identifies which words/phrases triggered crisis detection.
"""
from lime.lime_text import LimeTextExplainer
from typing import Dict, List
import numpy as np

from app.ml.crisis_model import get_crisis_model


class CrisisExplainer:
    """LIME-based explainability for crisis detection."""

    def __init__(self):
        self.explainer = LimeTextExplainer(class_names=['safe', 'crisis'])
        self.model = get_crisis_model()

    def _predict_proba(self, texts: List[str]) -> np.ndarray:
        """Prediction function for LIME."""
        results = []
        for text in texts:
            pred = self.model.predict(text)
            # Return [P(safe), P(crisis)]
            results.append([1 - pred['crisis_score'], pred['crisis_score']])
        return np.array(results)

    def explain(self, text: str, num_features: int = 10) -> Dict:
        """
        Explain why text was flagged as crisis.

        Returns:
            Dict with explanation details and contributing words
        """
        exp = self.explainer.explain_instance(
            text,
            self._predict_proba,
            num_features=num_features
        )

        # Get contributing words
        word_weights = exp.as_list()
        crisis_words = [w for w, score in word_weights if score > 0]
        safe_words = [w for w, score in word_weights if score < 0]

        return {
            "prediction": self.model.predict(text),
            "crisis_indicators": crisis_words,
            "safe_indicators": safe_words,
            "word_weights": dict(word_weights),
            "explanation_html": exp.as_html()
        }


def explain_crisis_detection(text: str) -> Dict:
    """Convenience function for crisis explanation."""
    explainer = CrisisExplainer()
    return explainer.explain(text)
```

### Step 3: Integrate with Chat Endpoint

**Modify:** `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`

Replace the existing crisis detection call with:

```python
from app.ml.crisis_model import predict_crisis
from app.services.crisis_detection import check_message as check_crisis_keywords

async def send_message(...):
    # ... existing code ...

    # Enhanced crisis detection (ML + keyword fallback)
    try:
        ml_crisis = predict_crisis(message_data.content)
        keyword_crisis = check_crisis_keywords(message_data.content)

        # Use highest signal
        if ml_crisis['threshold_triggered'] or keyword_crisis:
            crisis_category = 'ml_detected' if ml_crisis['threshold_triggered'] else keyword_crisis['category']
            logger.warning(f"[Crisis] Detected: score={ml_crisis['crisis_score']:.2f}, category={crisis_category}")

            return {
                "response": CRISIS_RESPONSE,
                "crisis_detected": True,
                "crisis_score": ml_crisis['crisis_score'],
                "crisis_category": crisis_category,
                "veterans_crisis_line": "988 (Press 1)"
            }
    except Exception as e:
        # ML failed - fall back to keyword only
        logger.error(f"[Crisis] ML model failed, using keyword fallback: {e}")
        keyword_crisis = check_crisis_keywords(message_data.content)
        if keyword_crisis:
            return {
                "response": CRISIS_RESPONSE,
                "crisis_detected": True,
                "crisis_category": keyword_crisis['category']
            }

    # ... continue with normal processing ...
```

### Step 4: Model Training Pipeline (Optional Enhancement)

**File:** `/ganuda/vetassist/backend/scripts/train_crisis_model.py`

```python
"""
Crisis Model Training Pipeline
Fine-tune RoBERTa on veteran-specific crisis data.

ETHICAL REQUIREMENTS:
- Only use publicly available, anonymized data
- No personally identifiable information
- Human review of training data required
"""
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    Trainer,
    TrainingArguments
)
from datasets import load_dataset, Dataset
import pandas as pd

# Training configuration
MODEL_BASE = "cardiffnlp/twitter-roberta-base-sentiment-latest"
OUTPUT_DIR = "/ganuda/vetassist/models/crisis-roberta"


def prepare_training_data():
    """
    Prepare training dataset.

    Sources (public, anonymized):
    - Published crisis intervention datasets
    - Academic research datasets with IRB approval
    - Synthetic data for augmentation
    """
    # TODO: Load appropriate dataset
    # Example structure:
    # data = [
    #     {"text": "I can't take it anymore", "label": 1},
    #     {"text": "Had a great day at the VA", "label": 0},
    # ]
    pass


def train_model():
    """Fine-tune RoBERTa for crisis detection."""
    tokenizer = AutoTokenizer.from_pretrained(MODEL_BASE)
    model = AutoModelForSequenceClassification.from_pretrained(
        MODEL_BASE,
        num_labels=2
    )

    # Training arguments
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        num_train_epochs=3,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir=f"{OUTPUT_DIR}/logs",
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
    )

    # TODO: Add dataset and run training
    # trainer = Trainer(
    #     model=model,
    #     args=training_args,
    #     train_dataset=train_dataset,
    #     eval_dataset=eval_dataset,
    # )
    # trainer.train()


if __name__ == "__main__":
    train_model()
```

---

## Dependencies

Add to `/ganuda/vetassist/backend/requirements.txt`:

```
transformers>=4.35.0
torch>=2.0.0
lime>=0.2.0
```

Install:
```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
pip install transformers torch lime
```

---

## Verification

1. Test model loading:
```python
from app.ml.crisis_model import predict_crisis
result = predict_crisis("I'm having a really hard time and don't know what to do")
print(result)
# Expected: {'crisis_score': 0.7+, 'threshold_triggered': True, ...}
```

2. Test known crisis phrases:
```python
test_phrases = [
    "I want to end it all",  # Should trigger
    "I can't go on anymore",  # Should trigger
    "The VA denied my claim",  # Should NOT trigger
    "Had a good therapy session",  # Should NOT trigger
]
for phrase in test_phrases:
    result = predict_crisis(phrase)
    print(f"{phrase[:30]}... -> {result['crisis_score']:.2f}")
```

3. Verify fallback works:
```bash
# Stop GPU/model, verify keyword detection still works
```

---

## Success Criteria

- [ ] RoBERTa model loads successfully
- [ ] Crisis detection accuracy ≥93%
- [ ] False negative rate <5%
- [ ] Latency <500ms per prediction
- [ ] LIME explainability working
- [ ] Fallback to keyword detection on failure
- [ ] Integrated with chat endpoint

---

## Safety Requirements

1. **NEVER** reduce sensitivity to avoid false positives
2. **ALWAYS** show Veterans Crisis Line (988, Press 1)
3. **LOG** all crisis detections for review
4. **FALLBACK** to keyword matching if ML fails
5. **HUMAN REVIEW** of edge cases weekly

---

*Cherokee AI Federation - For Seven Generations*

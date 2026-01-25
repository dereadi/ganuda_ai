# Jr Instruction: VetAssist Predictive Rating Estimation

## Priority: MEDIUM
## Estimated Effort: Medium
## Category: ML

---

## Objective

Build a Random Forest model to predict likely VA disability rating ranges based on condition type and evidence strength. Target: 92% accuracy (matching Springer 2025 research).

**CRITICAL ETHICAL REQUIREMENT:** This is an ESTIMATE only, never a guarantee. Must include confidence intervals and clear disclaimers.

---

## Research Basis

- Springer 2025: Random Forest achieved 92% accuracy, 98.6% specificity on 597K records
- NASI Report: SSA using similar approaches for disability benefits
- Must include bias monitoring

Reference: `/ganuda/docs/research/AI-RESEARCH-VETASSIST-ENHANCEMENT-JAN2026.md`

---

## Implementation

### Step 1: Feature Engineering

**File:** `/ganuda/vetassist/backend/app/ml/rating_features.py`

```python
"""
Feature Engineering for Rating Prediction
Cherokee AI Federation - For Seven Generations
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np


@dataclass
class ClaimFeatures:
    """Features for rating prediction."""
    # Condition characteristics
    diagnostic_code: str
    body_system: str
    condition_category: str  # musculoskeletal, mental, etc.

    # Evidence strength
    has_nexus_letter: bool
    nexus_strength: str  # strong, moderate, weak
    has_dbq: bool
    dbq_severity: Optional[str]
    treatment_records_months: int
    private_records_count: int
    va_records_count: int

    # Claim history
    is_increase: bool
    current_rating: Optional[int]
    previous_denials: int

    # Service connection
    service_connection_type: str  # direct, secondary, presumptive
    time_since_service_months: int


class FeatureEncoder:
    """Encodes claim features for ML model."""

    # Body system encoding
    BODY_SYSTEMS = {
        'musculoskeletal': 0,
        'mental': 1,
        'neurological': 2,
        'respiratory': 3,
        'cardiovascular': 4,
        'digestive': 5,
        'genitourinary': 6,
        'skin': 7,
        'endocrine': 8,
        'hemic': 9,
        'special_senses': 10,
        'dental': 11,
        'other': 12
    }

    # Nexus strength encoding
    NEXUS_STRENGTH = {
        'strong': 3,
        'moderate': 2,
        'weak': 1,
        'none': 0
    }

    # Service connection type encoding
    SC_TYPES = {
        'direct': 3,
        'presumptive': 2,
        'secondary': 1,
        'aggravation': 1
    }

    def encode(self, features: ClaimFeatures) -> np.ndarray:
        """Convert claim features to numeric vector."""
        return np.array([
            # Body system (one-hot would be better, but simplified)
            self.BODY_SYSTEMS.get(features.body_system, 12),

            # Evidence strength features
            int(features.has_nexus_letter),
            self.NEXUS_STRENGTH.get(features.nexus_strength, 0),
            int(features.has_dbq),
            self._encode_severity(features.dbq_severity),
            min(features.treatment_records_months / 12, 10),  # Cap at 10 years
            min(features.private_records_count / 10, 5),  # Normalized
            min(features.va_records_count / 10, 5),

            # Claim history
            int(features.is_increase),
            (features.current_rating or 0) / 100,
            min(features.previous_denials, 3),

            # Service connection
            self.SC_TYPES.get(features.service_connection_type, 0),
            min(features.time_since_service_months / 120, 5),  # Cap at 10 years
        ])

    def _encode_severity(self, severity: Optional[str]) -> float:
        """Encode DBQ severity level."""
        if not severity:
            return 0
        severity_map = {
            'mild': 0.25,
            'moderate': 0.5,
            'moderately_severe': 0.75,
            'severe': 1.0,
            'total': 1.0
        }
        return severity_map.get(severity.lower(), 0.5)


def extract_features_from_evidence(evidence_package: Dict) -> ClaimFeatures:
    """Extract ML features from processed evidence."""
    # This would be called after document processing
    nexus_signals = evidence_package.get('nexus_signals', [])
    has_strong_nexus = any(s['strength'] == 'strong' for s in nexus_signals)

    return ClaimFeatures(
        diagnostic_code=evidence_package.get('diagnostic_code', ''),
        body_system=evidence_package.get('body_system', 'other'),
        condition_category=evidence_package.get('condition_category', 'other'),
        has_nexus_letter=len(nexus_signals) > 0,
        nexus_strength='strong' if has_strong_nexus else 'moderate' if nexus_signals else 'none',
        has_dbq=evidence_package.get('document_type') == 'dbq',
        dbq_severity=evidence_package.get('dbq_severity'),
        treatment_records_months=evidence_package.get('treatment_months', 0),
        private_records_count=evidence_package.get('private_records', 0),
        va_records_count=evidence_package.get('va_records', 0),
        is_increase=evidence_package.get('is_increase', False),
        current_rating=evidence_package.get('current_rating'),
        previous_denials=evidence_package.get('previous_denials', 0),
        service_connection_type=evidence_package.get('sc_type', 'direct'),
        time_since_service_months=evidence_package.get('months_since_service', 0)
    )
```

### Step 2: Rating Prediction Model

**File:** `/ganuda/vetassist/backend/app/ml/rating_predictor.py`

```python
"""
Rating Prediction Model
Predicts likely VA disability rating range.

IMPORTANT: This is an ESTIMATE only, not a guarantee.
"""
import os
import pickle
import logging
from typing import Dict, Tuple, Optional
import numpy as np
from sklearn.ensemble import RandomForestClassifier

from app.ml.rating_features import ClaimFeatures, FeatureEncoder

logger = logging.getLogger(__name__)

# Rating buckets for classification
RATING_BUCKETS = [0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
MODEL_PATH = "/ganuda/vetassist/models/rating_predictor.pkl"


class RatingPredictor:
    """Predicts VA disability rating ranges."""

    def __init__(self, model_path: str = MODEL_PATH):
        self.encoder = FeatureEncoder()
        self.model = None
        self._load_or_create_model(model_path)

    def _load_or_create_model(self, model_path: str):
        """Load existing model or create new one."""
        if os.path.exists(model_path):
            try:
                with open(model_path, 'rb') as f:
                    self.model = pickle.load(f)
                logger.info("[Rating] Loaded existing model")
            except Exception as e:
                logger.error(f"[Rating] Failed to load model: {e}")
                self._create_default_model()
        else:
            self._create_default_model()

    def _create_default_model(self):
        """Create a default model with synthetic training."""
        logger.info("[Rating] Creating default model with synthetic data")

        # Generate synthetic training data
        # In production, this would be trained on real claims data
        X, y = self._generate_synthetic_data(1000)

        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X, y)

        # Save model
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        with open(MODEL_PATH, 'wb') as f:
            pickle.dump(self.model, f)
        logger.info("[Rating] Default model created and saved")

    def _generate_synthetic_data(self, n_samples: int) -> Tuple[np.ndarray, np.ndarray]:
        """Generate synthetic training data based on known patterns."""
        np.random.seed(42)
        X = []
        y = []

        for _ in range(n_samples):
            # Random features
            body_system = np.random.randint(0, 13)
            has_nexus = np.random.choice([0, 1], p=[0.3, 0.7])
            nexus_strength = np.random.randint(0, 4) if has_nexus else 0
            has_dbq = np.random.choice([0, 1], p=[0.4, 0.6])
            dbq_severity = np.random.uniform(0, 1) if has_dbq else 0
            treatment_months = np.random.uniform(0, 10)
            private_records = np.random.uniform(0, 5)
            va_records = np.random.uniform(0, 5)
            is_increase = np.random.choice([0, 1], p=[0.7, 0.3])
            current_rating = np.random.choice([0, 0.1, 0.2, 0.3, 0.4, 0.5]) if is_increase else 0
            previous_denials = np.random.choice([0, 1, 2, 3], p=[0.6, 0.25, 0.1, 0.05])
            sc_type = np.random.randint(0, 4)
            time_since_service = np.random.uniform(0, 5)

            features = [
                body_system, has_nexus, nexus_strength, has_dbq, dbq_severity,
                treatment_months, private_records, va_records, is_increase,
                current_rating, previous_denials, sc_type, time_since_service
            ]

            # Generate target based on feature patterns
            # Higher nexus + DBQ + records = higher rating
            base_score = (
                nexus_strength * 15 +
                dbq_severity * 30 +
                treatment_months * 3 +
                (private_records + va_records) * 2 -
                previous_denials * 10 +
                sc_type * 5
            )

            # Add noise and clip
            rating = int(np.clip(base_score + np.random.normal(0, 10), 0, 100))
            # Round to nearest 10
            rating = round(rating / 10) * 10

            X.append(features)
            y.append(rating)

        return np.array(X), np.array(y)

    def predict(self, features: ClaimFeatures) -> Dict:
        """
        Predict rating range for a claim.

        Returns dict with predicted rating, confidence interval, and caveats.
        """
        # Encode features
        X = self.encoder.encode(features).reshape(1, -1)

        # Get prediction and probabilities
        prediction = self.model.predict(X)[0]
        probabilities = self.model.predict_proba(X)[0]

        # Calculate confidence interval
        classes = self.model.classes_
        sorted_indices = np.argsort(probabilities)[::-1]
        top_classes = classes[sorted_indices[:3]]
        top_probs = probabilities[sorted_indices[:3]]

        # Determine range
        likely_min = max(0, int(prediction) - 10)
        likely_max = min(100, int(prediction) + 10)

        # Confidence based on top probability
        confidence = float(top_probs[0])

        return {
            "predicted_rating": int(prediction),
            "likely_range": {
                "min": likely_min,
                "max": likely_max
            },
            "confidence": confidence,
            "confidence_level": self._confidence_level(confidence),
            "top_predictions": [
                {"rating": int(c), "probability": float(p)}
                for c, p in zip(top_classes, top_probs)
            ],
            "disclaimer": (
                "This is an ESTIMATE based on the evidence provided. "
                "Actual VA ratings depend on many factors including examiner findings, "
                "functional impairment, and current regulations. "
                "This prediction is not a guarantee of any specific outcome."
            ),
            "factors_considered": self._explain_factors(features)
        }

    def _confidence_level(self, confidence: float) -> str:
        """Convert numeric confidence to level."""
        if confidence >= 0.7:
            return "high"
        elif confidence >= 0.5:
            return "medium"
        else:
            return "low"

    def _explain_factors(self, features: ClaimFeatures) -> Dict:
        """Explain what factors influenced the prediction."""
        positive_factors = []
        negative_factors = []

        if features.has_nexus_letter:
            if features.nexus_strength == 'strong':
                positive_factors.append("Strong nexus letter supporting service connection")
            else:
                positive_factors.append("Nexus letter present")

        if features.has_dbq:
            positive_factors.append("DBQ form completed")

        if features.treatment_records_months > 12:
            positive_factors.append(f"{features.treatment_records_months} months of treatment records")

        if features.previous_denials > 0:
            negative_factors.append(f"{features.previous_denials} previous denial(s)")

        if not features.has_nexus_letter:
            negative_factors.append("No nexus letter on file")

        return {
            "positive": positive_factors,
            "negative": negative_factors
        }


# Convenience function
def predict_rating(features: ClaimFeatures) -> Dict:
    """Predict rating for a claim."""
    predictor = RatingPredictor()
    return predictor.predict(features)
```

### Step 3: API Endpoint

**File:** Add to `/ganuda/vetassist/backend/app/api/v1/endpoints/calculator.py`

```python
from app.ml.rating_predictor import predict_rating
from app.ml.rating_features import ClaimFeatures

@router.post("/predict-rating")
async def predict_claim_rating(features: Dict):
    """
    Predict likely rating range for a claim.

    IMPORTANT: This is an estimate only, not a guarantee.
    """
    claim_features = ClaimFeatures(**features)
    prediction = predict_rating(claim_features)
    return prediction
```

---

## Verification

1. Test prediction:
```python
from app.ml.rating_predictor import predict_rating
from app.ml.rating_features import ClaimFeatures

features = ClaimFeatures(
    diagnostic_code="9411",
    body_system="mental",
    condition_category="mental",
    has_nexus_letter=True,
    nexus_strength="strong",
    has_dbq=True,
    dbq_severity="moderate",
    treatment_records_months=24,
    private_records_count=5,
    va_records_count=10,
    is_increase=False,
    current_rating=None,
    previous_denials=0,
    service_connection_type="direct",
    time_since_service_months=36
)

result = predict_rating(features)
print(f"Predicted: {result['predicted_rating']}%")
print(f"Range: {result['likely_range']}")
print(f"Confidence: {result['confidence_level']}")
```

---

## Success Criteria

- [ ] Feature encoder working
- [ ] Model trained on synthetic data
- [ ] Predictions include confidence intervals
- [ ] Clear disclaimers in all responses
- [ ] Factor explanation working
- [ ] API endpoint functional

---

*Cherokee AI Federation - For Seven Generations*

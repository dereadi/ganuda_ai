# JR Instruction: VetAssist Form Selection Decision Engine

**Task ID:** VETASSIST-WIZARD-001
**Priority:** P1
**Type:** backend
**Assigned:** Software Engineer Jr.
**Council Approval:** APPROVED 7-0 (2026-01-25)

---

## Objective

Create a decision engine that recommends the correct VA form based on veteran's claim history and evidence.

---

## Context

Veterans must choose the correct form:
- **VA 21-526EZ**: Original disability claim
- **VA 20-0995**: Supplemental claim (new evidence)
- **VA 20-0996**: Higher-level review (clear error)
- **VA 10182**: Board of Veterans' Appeals

**Wrong form = 6+ month delay in benefits.**

---

## Deliverables

### 1. Form Selector Service

Create `/ganuda/vetassist/backend/app/services/form_selector.py`:

```python
"""
Form Selection Decision Engine for VetAssist.
Council Approved: 2026-01-25 (7-0)
"""

from dataclasses import dataclass
from typing import List, Optional
from datetime import date, timedelta
from enum import Enum


class VAForm(Enum):
    FORM_526EZ = "21-526EZ"      # Original claim
    FORM_0995 = "20-0995"        # Supplemental claim
    FORM_0996 = "20-0996"        # Higher-level review
    FORM_10182 = "10182"         # Board appeal


class ClaimOutcome(Enum):
    PENDING = "pending"
    DENIED = "denied"
    APPROVED = "approved"
    PARTIAL = "partial"          # Lower rating than expected


@dataclass
class FormRecommendation:
    recommended_form: VAForm
    confidence_score: float
    reason: str
    edge_case_flags: List[str]
    vso_consultation_recommended: bool
    alternative_forms: List[VAForm]


@dataclass
class ClaimHistory:
    is_first_claim: bool
    previous_outcome: Optional[ClaimOutcome]
    decision_date: Optional[date]
    has_new_evidence: bool
    evidence_types: List[str]
    clear_error_claimed: bool


class FormSelector:
    """
    Decision engine for VA form selection.

    Decision Tree:
    1. First claim? → 526EZ
    2. Has new evidence? → 0995
    3. Claims clear error? → 0996
    4. Within appeal window? → 10182
    5. Outside window with new evidence? → 0995
    """

    APPEAL_WINDOW_DAYS = 365  # 1 year from decision

    def recommend(self, history: ClaimHistory) -> FormRecommendation:
        """
        Recommend appropriate VA form based on claim history.

        Returns FormRecommendation with confidence score and reasoning.
        """
        edge_cases = []
        vso_recommended = False

        # Decision 1: First claim
        if history.is_first_claim:
            return FormRecommendation(
                recommended_form=VAForm.FORM_526EZ,
                confidence_score=0.95,
                reason="This is your first claim for this condition. Form 21-526EZ is for original disability compensation claims.",
                edge_case_flags=[],
                vso_consultation_recommended=False,
                alternative_forms=[]
            )

        # Previous claim exists - check outcome
        if history.previous_outcome == ClaimOutcome.PENDING:
            return FormRecommendation(
                recommended_form=None,
                confidence_score=0.90,
                reason="Your previous claim is still pending. Wait for the VA decision before filing additional claims.",
                edge_case_flags=["pending_claim"],
                vso_consultation_recommended=True,
                alternative_forms=[]
            )

        # Check if within appeal window
        within_appeal_window = False
        if history.decision_date:
            days_since_decision = (date.today() - history.decision_date).days
            within_appeal_window = days_since_decision <= self.APPEAL_WINDOW_DAYS

            if days_since_decision > 300 and days_since_decision <= 365:
                edge_cases.append("approaching_appeal_deadline")

        # Decision 2: Has new evidence
        if history.has_new_evidence:
            confidence = 0.90

            # Check evidence quality
            strong_evidence = ['medical_records', 'nexus_letter', 'dbq']
            has_strong = any(e in history.evidence_types for e in strong_evidence)

            if not has_strong:
                edge_cases.append("weak_new_evidence")
                confidence = 0.75
                vso_recommended = True

            return FormRecommendation(
                recommended_form=VAForm.FORM_0995,
                confidence_score=confidence,
                reason="You have new evidence not previously submitted. Form 20-0995 (Supplemental Claim) allows you to submit new evidence for reconsideration.",
                edge_case_flags=edge_cases,
                vso_consultation_recommended=vso_recommended,
                alternative_forms=[VAForm.FORM_10182] if within_appeal_window else []
            )

        # Decision 3: Clear error claimed
        if history.clear_error_claimed:
            if not within_appeal_window:
                edge_cases.append("outside_appeal_window_for_hlr")
                vso_recommended = True

            return FormRecommendation(
                recommended_form=VAForm.FORM_0996 if within_appeal_window else VAForm.FORM_0995,
                confidence_score=0.80 if within_appeal_window else 0.60,
                reason="You believe the VA made a clear error. Form 20-0996 (Higher-Level Review) requests a senior reviewer examine the same evidence." if within_appeal_window else "The appeal window has passed. Consider filing a Supplemental Claim (20-0995) with additional evidence supporting your position.",
                edge_case_flags=edge_cases,
                vso_consultation_recommended=vso_recommended,
                alternative_forms=[VAForm.FORM_0995] if within_appeal_window else []
            )

        # Decision 4: Within appeal window, no new evidence, no clear error
        if within_appeal_window:
            vso_recommended = True
            edge_cases.append("no_new_evidence_or_error")

            return FormRecommendation(
                recommended_form=VAForm.FORM_10182,
                confidence_score=0.70,
                reason="You're within the appeal window but have no new evidence or clear error claim. Form 10182 (Board Appeal) allows a Veterans Law Judge to review your case. Consider consulting a VSO to strengthen your appeal.",
                edge_case_flags=edge_cases,
                vso_consultation_recommended=True,
                alternative_forms=[VAForm.FORM_0995]
            )

        # Decision 5: Outside appeal window, no new evidence
        return FormRecommendation(
            recommended_form=VAForm.FORM_0995,
            confidence_score=0.65,
            reason="The appeal window has passed and you don't have new evidence. You can file a Supplemental Claim (20-0995) but will need to obtain new evidence to support your case.",
            edge_case_flags=["outside_window_no_evidence"],
            vso_consultation_recommended=True,
            alternative_forms=[]
        )


# Convenience function for API
def recommend_form(
    is_first_claim: bool,
    previous_outcome: Optional[str] = None,
    decision_date: Optional[date] = None,
    has_new_evidence: bool = False,
    evidence_types: List[str] = None,
    clear_error_claimed: bool = False
) -> dict:
    """
    API-friendly wrapper for form recommendation.

    Returns dict with recommendation details.
    """
    history = ClaimHistory(
        is_first_claim=is_first_claim,
        previous_outcome=ClaimOutcome(previous_outcome) if previous_outcome else None,
        decision_date=decision_date,
        has_new_evidence=has_new_evidence,
        evidence_types=evidence_types or [],
        clear_error_claimed=clear_error_claimed
    )

    selector = FormSelector()
    rec = selector.recommend(history)

    return {
        "recommended_form": rec.recommended_form.value if rec.recommended_form else None,
        "confidence_score": rec.confidence_score,
        "reason": rec.reason,
        "edge_case_flags": rec.edge_case_flags,
        "vso_consultation_recommended": rec.vso_consultation_recommended,
        "alternative_forms": [f.value for f in rec.alternative_forms]
    }
```

### 2. Unit Tests

Create `/ganuda/vetassist/backend/tests/test_form_selector.py`:

```python
"""Tests for Form Selection Decision Engine."""

import pytest
from datetime import date, timedelta
from app.services.form_selector import (
    FormSelector, ClaimHistory, ClaimOutcome, VAForm, recommend_form
)


class TestFormSelector:

    def test_first_claim_returns_526ez(self):
        """First-time claimants should get 526EZ."""
        history = ClaimHistory(
            is_first_claim=True,
            previous_outcome=None,
            decision_date=None,
            has_new_evidence=False,
            evidence_types=[],
            clear_error_claimed=False
        )

        selector = FormSelector()
        rec = selector.recommend(history)

        assert rec.recommended_form == VAForm.FORM_526EZ
        assert rec.confidence_score >= 0.9
        assert not rec.vso_consultation_recommended

    def test_new_evidence_returns_0995(self):
        """New evidence should trigger Supplemental Claim."""
        history = ClaimHistory(
            is_first_claim=False,
            previous_outcome=ClaimOutcome.DENIED,
            decision_date=date.today() - timedelta(days=30),
            has_new_evidence=True,
            evidence_types=['medical_records', 'nexus_letter'],
            clear_error_claimed=False
        )

        selector = FormSelector()
        rec = selector.recommend(history)

        assert rec.recommended_form == VAForm.FORM_0995
        assert rec.confidence_score >= 0.85

    def test_clear_error_within_window_returns_0996(self):
        """Clear error claim within window should get HLR."""
        history = ClaimHistory(
            is_first_claim=False,
            previous_outcome=ClaimOutcome.DENIED,
            decision_date=date.today() - timedelta(days=100),
            has_new_evidence=False,
            evidence_types=[],
            clear_error_claimed=True
        )

        selector = FormSelector()
        rec = selector.recommend(history)

        assert rec.recommended_form == VAForm.FORM_0996

    def test_outside_appeal_window_with_error_returns_0995(self):
        """Clear error claim outside window should suggest 0995."""
        history = ClaimHistory(
            is_first_claim=False,
            previous_outcome=ClaimOutcome.DENIED,
            decision_date=date.today() - timedelta(days=400),
            has_new_evidence=False,
            evidence_types=[],
            clear_error_claimed=True
        )

        selector = FormSelector()
        rec = selector.recommend(history)

        assert rec.recommended_form == VAForm.FORM_0995
        assert rec.vso_consultation_recommended

    def test_pending_claim_warns_to_wait(self):
        """Pending claims should advise waiting."""
        history = ClaimHistory(
            is_first_claim=False,
            previous_outcome=ClaimOutcome.PENDING,
            decision_date=None,
            has_new_evidence=True,
            evidence_types=['buddy_statement'],
            clear_error_claimed=False
        )

        selector = FormSelector()
        rec = selector.recommend(history)

        assert rec.recommended_form is None
        assert "pending_claim" in rec.edge_case_flags

    def test_convenience_function(self):
        """Test API wrapper function."""
        result = recommend_form(
            is_first_claim=True,
            previous_outcome=None,
            decision_date=None,
            has_new_evidence=False
        )

        assert result["recommended_form"] == "21-526EZ"
        assert "confidence_score" in result
        assert "reason" in result
```

---

## Success Criteria

- [ ] `form_selector.py` created with FormSelector class
- [ ] All 5 decision paths implemented
- [ ] Confidence scores assigned to each recommendation
- [ ] Edge case flags for complex situations
- [ ] VSO referral logic implemented
- [ ] Unit tests pass (minimum 5 test cases)
- [ ] API wrapper function works

---

## Integration Notes

- This service will be called by the wizard API endpoint
- Results stored in `wizard_form_recommendations` table (separate task)
- Frontend will display recommendation with confidence indicator

---

## For Seven Generations

A veteran choosing the wrong form loses months waiting for benefits they've earned. This decision engine must be accurate and clear in its recommendations.

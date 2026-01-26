# JR Instruction: VetAssist Wizard UI Steps

**Task ID:** VETASSIST-WIZARD-002
**Priority:** P1
**Type:** frontend
**Assigned:** Software Engineer Jr.
**Council Approval:** APPROVED 7-0 (2026-01-25)

---

## Objective

Create the React components for the claim wizard form selection flow.

---

## Deliverables

### 1. Claim History Step

Create `/ganuda/vetassist/frontend/components/wizard/ClaimHistoryStep.tsx`:

```tsx
/**
 * ClaimHistoryStep - First step in form selection wizard
 * Gathers information about previous claims for this condition
 */

import React, { useState } from 'react';

interface ClaimHistoryData {
  isFirstClaim: boolean;
  previousOutcome?: 'denied' | 'approved' | 'partial' | 'pending';
  decisionDate?: string;
}

interface Props {
  onNext: (data: ClaimHistoryData) => void;
  initialData?: ClaimHistoryData;
}

export function ClaimHistoryStep({ onNext, initialData }: Props) {
  const [isFirstClaim, setIsFirstClaim] = useState<boolean | null>(
    initialData?.isFirstClaim ?? null
  );
  const [previousOutcome, setPreviousOutcome] = useState(initialData?.previousOutcome);
  const [decisionDate, setDecisionDate] = useState(initialData?.decisionDate || '');

  const canProceed = isFirstClaim !== null &&
    (isFirstClaim || (previousOutcome && (previousOutcome === 'pending' || decisionDate)));

  const handleNext = () => {
    if (isFirstClaim === null) return;

    onNext({
      isFirstClaim,
      previousOutcome: isFirstClaim ? undefined : previousOutcome,
      decisionDate: isFirstClaim ? undefined : decisionDate
    });
  };

  return (
    <div className="wizard-step">
      <h2 className="text-xl font-semibold mb-4">Claim History</h2>
      <p className="text-gray-600 mb-6">
        Tell us about any previous claims you've filed for this condition.
      </p>

      {/* First Claim Question */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Is this your first time claiming this condition?
        </label>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => setIsFirstClaim(true)}
            className={`px-6 py-3 rounded-lg border-2 transition-colors ${
              isFirstClaim === true
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            Yes, first time
          </button>
          <button
            type="button"
            onClick={() => setIsFirstClaim(false)}
            className={`px-6 py-3 rounded-lg border-2 transition-colors ${
              isFirstClaim === false
                ? 'border-blue-600 bg-blue-50 text-blue-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            No, I've claimed before
          </button>
        </div>
      </div>

      {/* Previous Outcome (if not first claim) */}
      {isFirstClaim === false && (
        <>
          <div className="mb-6">
            <label className="block text-sm font-medium mb-2">
              What was the outcome of your previous claim?
            </label>
            <select
              value={previousOutcome || ''}
              onChange={(e) => setPreviousOutcome(e.target.value as any)}
              className="w-full p-3 border rounded-lg"
            >
              <option value="">Select outcome...</option>
              <option value="denied">Denied (0% rating)</option>
              <option value="partial">Approved but lower rating than expected</option>
              <option value="approved">Approved at expected rating</option>
              <option value="pending">Still pending decision</option>
            </select>
          </div>

          {/* Decision Date (if not pending) */}
          {previousOutcome && previousOutcome !== 'pending' && (
            <div className="mb-6">
              <label className="block text-sm font-medium mb-2">
                When did you receive the decision?
              </label>
              <input
                type="date"
                value={decisionDate}
                onChange={(e) => setDecisionDate(e.target.value)}
                className="w-full p-3 border rounded-lg"
                max={new Date().toISOString().split('T')[0]}
              />
              <p className="text-sm text-gray-500 mt-1">
                This helps us determine your appeal options.
              </p>
            </div>
          )}
        </>
      )}

      {/* Pending Warning */}
      {previousOutcome === 'pending' && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-yellow-800">
            <strong>Note:</strong> You should wait for your current claim decision
            before filing additional claims for this condition.
          </p>
        </div>
      )}

      {/* Next Button */}
      <div className="flex justify-end">
        <button
          onClick={handleNext}
          disabled={!canProceed}
          className={`px-6 py-3 rounded-lg font-medium ${
            canProceed
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Continue
        </button>
      </div>
    </div>
  );
}

export default ClaimHistoryStep;
```

### 2. Evidence Assessment Step

Create `/ganuda/vetassist/frontend/components/wizard/EvidenceAssessmentStep.tsx`:

```tsx
/**
 * EvidenceAssessmentStep - Second step in form selection wizard
 * Determines what type of evidence the veteran has
 */

import React, { useState } from 'react';

interface EvidenceData {
  hasNewEvidence: boolean;
  evidenceTypes: string[];
  clearErrorClaimed: boolean;
}

interface Props {
  onNext: (data: EvidenceData) => void;
  onBack: () => void;
  initialData?: EvidenceData;
}

const EVIDENCE_OPTIONS = [
  { id: 'medical_records', label: 'New medical records or test results' },
  { id: 'nexus_letter', label: 'Nexus letter from a doctor' },
  { id: 'dbq', label: 'Disability Benefits Questionnaire (DBQ)' },
  { id: 'buddy_statement', label: 'Buddy/lay statements' },
  { id: 'service_records', label: 'Newly obtained service records' },
  { id: 'other', label: 'Other new evidence' }
];

export function EvidenceAssessmentStep({ onNext, onBack, initialData }: Props) {
  const [hasNewEvidence, setHasNewEvidence] = useState<boolean | null>(
    initialData?.hasNewEvidence ?? null
  );
  const [evidenceTypes, setEvidenceTypes] = useState<string[]>(
    initialData?.evidenceTypes || []
  );
  const [clearErrorClaimed, setClearErrorClaimed] = useState(
    initialData?.clearErrorClaimed ?? false
  );

  const toggleEvidence = (id: string) => {
    setEvidenceTypes(prev =>
      prev.includes(id) ? prev.filter(e => e !== id) : [...prev, id]
    );
  };

  const canProceed = hasNewEvidence !== null;

  const handleNext = () => {
    if (hasNewEvidence === null) return;

    onNext({
      hasNewEvidence,
      evidenceTypes: hasNewEvidence ? evidenceTypes : [],
      clearErrorClaimed
    });
  };

  return (
    <div className="wizard-step">
      <h2 className="text-xl font-semibold mb-4">Evidence Assessment</h2>
      <p className="text-gray-600 mb-6">
        Tell us about any new evidence you have since your last claim.
      </p>

      {/* New Evidence Question */}
      <div className="mb-6">
        <label className="block text-sm font-medium mb-2">
          Do you have new evidence that wasn't submitted with your previous claim?
        </label>
        <div className="flex gap-4">
          <button
            type="button"
            onClick={() => setHasNewEvidence(true)}
            className={`px-6 py-3 rounded-lg border-2 transition-colors ${
              hasNewEvidence === true
                ? 'border-green-600 bg-green-50 text-green-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            Yes, I have new evidence
          </button>
          <button
            type="button"
            onClick={() => setHasNewEvidence(false)}
            className={`px-6 py-3 rounded-lg border-2 transition-colors ${
              hasNewEvidence === false
                ? 'border-orange-600 bg-orange-50 text-orange-700'
                : 'border-gray-300 hover:border-gray-400'
            }`}
          >
            No new evidence
          </button>
        </div>
      </div>

      {/* Evidence Types (if has new evidence) */}
      {hasNewEvidence && (
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            What type of new evidence do you have? (Select all that apply)
          </label>
          <div className="space-y-2">
            {EVIDENCE_OPTIONS.map(option => (
              <label
                key={option.id}
                className={`flex items-center p-3 border rounded-lg cursor-pointer transition-colors ${
                  evidenceTypes.includes(option.id)
                    ? 'border-blue-500 bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <input
                  type="checkbox"
                  checked={evidenceTypes.includes(option.id)}
                  onChange={() => toggleEvidence(option.id)}
                  className="mr-3"
                />
                {option.label}
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Clear Error Question (if no new evidence) */}
      {hasNewEvidence === false && (
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">
            Do you believe the VA made a clear error in reviewing your evidence?
          </label>
          <p className="text-sm text-gray-500 mb-3">
            A clear error means the VA misread evidence, applied the wrong law,
            or failed to consider evidence you submitted.
          </p>
          <div className="flex gap-4">
            <button
              type="button"
              onClick={() => setClearErrorClaimed(true)}
              className={`px-6 py-3 rounded-lg border-2 transition-colors ${
                clearErrorClaimed
                  ? 'border-purple-600 bg-purple-50 text-purple-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              Yes, I believe there was an error
            </button>
            <button
              type="button"
              onClick={() => setClearErrorClaimed(false)}
              className={`px-6 py-3 rounded-lg border-2 transition-colors ${
                !clearErrorClaimed
                  ? 'border-gray-600 bg-gray-50 text-gray-700'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              No clear error
            </button>
          </div>
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-6 py-3 rounded-lg border border-gray-300 hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={handleNext}
          disabled={!canProceed}
          className={`px-6 py-3 rounded-lg font-medium ${
            canProceed
              ? 'bg-blue-600 text-white hover:bg-blue-700'
              : 'bg-gray-300 text-gray-500 cursor-not-allowed'
          }`}
        >
          Get Recommendation
        </button>
      </div>
    </div>
  );
}

export default EvidenceAssessmentStep;
```

### 3. Form Recommendation Step

Create `/ganuda/vetassist/frontend/components/wizard/FormRecommendationStep.tsx`:

```tsx
/**
 * FormRecommendationStep - Final step showing recommended VA form
 */

import React from 'react';

interface FormRecommendation {
  recommended_form: string | null;
  confidence_score: number;
  reason: string;
  edge_case_flags: string[];
  vso_consultation_recommended: boolean;
  alternative_forms: string[];
}

interface Props {
  recommendation: FormRecommendation;
  onAccept: () => void;
  onOverride: (form: string, reason: string) => void;
  onBack: () => void;
}

const FORM_INFO: Record<string, { name: string; description: string; link: string }> = {
  '21-526EZ': {
    name: 'VA Form 21-526EZ',
    description: 'Application for Disability Compensation and Related Compensation Benefits',
    link: 'https://www.va.gov/find-forms/about-form-21-526ez/'
  },
  '20-0995': {
    name: 'VA Form 20-0995',
    description: 'Decision Review Request: Supplemental Claim',
    link: 'https://www.va.gov/find-forms/about-form-20-0995/'
  },
  '20-0996': {
    name: 'VA Form 20-0996',
    description: 'Decision Review Request: Higher-Level Review',
    link: 'https://www.va.gov/find-forms/about-form-20-0996/'
  },
  '10182': {
    name: 'VA Form 10182',
    description: 'Decision Review Request: Board Appeal',
    link: 'https://www.va.gov/find-forms/about-form-10182/'
  }
};

export function FormRecommendationStep({ recommendation, onAccept, onOverride, onBack }: Props) {
  const [showOverride, setShowOverride] = React.useState(false);
  const [overrideForm, setOverrideForm] = React.useState('');
  const [overrideReason, setOverrideReason] = React.useState('');

  const formInfo = recommendation.recommended_form
    ? FORM_INFO[recommendation.recommended_form]
    : null;

  const confidenceColor = recommendation.confidence_score >= 0.8
    ? 'text-green-600'
    : recommendation.confidence_score >= 0.6
      ? 'text-yellow-600'
      : 'text-orange-600';

  return (
    <div className="wizard-step">
      <h2 className="text-xl font-semibold mb-4">Form Recommendation</h2>

      {/* No form recommended (e.g., pending claim) */}
      {!recommendation.recommended_form && (
        <div className="p-6 bg-yellow-50 border border-yellow-200 rounded-lg mb-6">
          <h3 className="font-semibold text-yellow-800 mb-2">Action Recommended</h3>
          <p className="text-yellow-700">{recommendation.reason}</p>
        </div>
      )}

      {/* Form Recommendation */}
      {formInfo && (
        <div className="p-6 bg-blue-50 border border-blue-200 rounded-lg mb-6">
          <div className="flex justify-between items-start mb-4">
            <div>
              <h3 className="text-lg font-semibold text-blue-800">{formInfo.name}</h3>
              <p className="text-blue-600">{formInfo.description}</p>
            </div>
            <span className={`text-sm font-medium ${confidenceColor}`}>
              {Math.round(recommendation.confidence_score * 100)}% confident
            </span>
          </div>

          <p className="text-gray-700 mb-4">{recommendation.reason}</p>

          <a
            href={formInfo.link}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            View form on VA.gov →
          </a>
        </div>
      )}

      {/* VSO Recommendation */}
      {recommendation.vso_consultation_recommended && (
        <div className="p-4 bg-purple-50 border border-purple-200 rounded-lg mb-6">
          <p className="text-purple-800">
            <strong>Recommendation:</strong> Consider consulting with a Veterans Service
            Organization (VSO) for this type of claim. They can provide free assistance.
          </p>
        </div>
      )}

      {/* Alternative Forms */}
      {recommendation.alternative_forms.length > 0 && (
        <div className="mb-6">
          <p className="text-sm text-gray-600 mb-2">Alternative options:</p>
          <div className="flex gap-2">
            {recommendation.alternative_forms.map(form => (
              <span key={form} className="px-3 py-1 bg-gray-100 rounded-full text-sm">
                {FORM_INFO[form]?.name || form}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Override Option */}
      {!showOverride ? (
        <button
          onClick={() => setShowOverride(true)}
          className="text-sm text-gray-500 hover:text-gray-700 mb-6"
        >
          Choose a different form instead
        </button>
      ) : (
        <div className="p-4 bg-gray-50 border rounded-lg mb-6">
          <label className="block text-sm font-medium mb-2">Select different form:</label>
          <select
            value={overrideForm}
            onChange={(e) => setOverrideForm(e.target.value)}
            className="w-full p-2 border rounded mb-2"
          >
            <option value="">Choose form...</option>
            {Object.entries(FORM_INFO).map(([key, info]) => (
              <option key={key} value={key}>{info.name}</option>
            ))}
          </select>
          <label className="block text-sm font-medium mb-2">Reason for override:</label>
          <textarea
            value={overrideReason}
            onChange={(e) => setOverrideReason(e.target.value)}
            className="w-full p-2 border rounded"
            rows={2}
            placeholder="Why are you selecting a different form?"
          />
        </div>
      )}

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={onBack}
          className="px-6 py-3 rounded-lg border border-gray-300 hover:bg-gray-50"
        >
          Back
        </button>
        <div className="flex gap-3">
          {showOverride && overrideForm && overrideReason && (
            <button
              onClick={() => onOverride(overrideForm, overrideReason)}
              className="px-6 py-3 rounded-lg border border-orange-500 text-orange-600 hover:bg-orange-50"
            >
              Use {FORM_INFO[overrideForm]?.name}
            </button>
          )}
          {recommendation.recommended_form && (
            <button
              onClick={onAccept}
              className="px-6 py-3 rounded-lg bg-green-600 text-white hover:bg-green-700 font-medium"
            >
              Continue with {formInfo?.name}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default FormRecommendationStep;
```

---

## Success Criteria

- [ ] ClaimHistoryStep.tsx created and handles first-claim detection
- [ ] EvidenceAssessmentStep.tsx created with evidence type selection
- [ ] FormRecommendationStep.tsx displays recommendation with confidence
- [ ] All components have proper TypeScript types
- [ ] Navigation (back/next) works between steps
- [ ] Override option allows veteran to choose different form

---

## For Seven Generations

Clear, respectful UI that helps veterans understand their options without overwhelming them.

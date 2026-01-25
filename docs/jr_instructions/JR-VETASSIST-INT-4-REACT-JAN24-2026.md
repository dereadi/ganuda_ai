# JR Instruction: VetAssist Integration Part 4 - Evidence Gap React Component

**Task ID:** VETASSIST-INT-REACT-001
**Priority:** P1
**Type:** frontend
**Assigned:** Software Engineer Jr.

---

## Objective

Create React component to display evidence gaps and claim strength for each condition.

---

## Deliverable

Create this exact file:

File: `/ganuda/vetassist/frontend/components/wizard/EvidenceGapPanel.tsx`

```typescript
/**
 * VetAssist Evidence Gap Panel
 *
 * Displays missing evidence and claim strength for each claimed condition.
 *
 * For Seven Generations - Cherokee AI Federation
 */

import React, { useEffect, useState } from 'react';

interface EvidenceGap {
  condition: string;
  missing_required: string[];
  missing_recommended: string[];
  missing_helpful: string[];
  claim_strength: number;
}

interface EvidenceGapPanelProps {
  sessionId: string;
}

export const EvidenceGapPanel: React.FC<EvidenceGapPanelProps> = ({ sessionId }) => {
  const [gaps, setGaps] = useState<EvidenceGap[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchGaps = async () => {
      try {
        const response = await fetch(`/api/v1/sessions/${sessionId}/evidence-gaps`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (!response.ok) {
          throw new Error('Failed to fetch evidence gaps');
        }

        const data = await response.json();
        setGaps(data);
        setLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
        setLoading(false);
      }
    };

    if (sessionId) {
      fetchGaps();
    }
  }, [sessionId]);

  if (loading) {
    return (
      <div className="evidence-gap-panel loading">
        <div className="spinner"></div>
        <p>Analyzing your evidence...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="evidence-gap-panel error">
        <p>Unable to analyze evidence: {error}</p>
      </div>
    );
  }

  if (gaps.length === 0) {
    return (
      <div className="evidence-gap-panel empty">
        <p>No conditions selected yet. Add conditions to see evidence requirements.</p>
      </div>
    );
  }

  const getStrengthColor = (strength: number): string => {
    if (strength >= 0.8) return 'strength-high';
    if (strength >= 0.5) return 'strength-medium';
    return 'strength-low';
  };

  const getStrengthLabel = (strength: number): string => {
    if (strength >= 0.8) return 'Strong';
    if (strength >= 0.5) return 'Moderate';
    return 'Needs Evidence';
  };

  return (
    <div className="evidence-gap-panel">
      <h3>Evidence Analysis</h3>
      <p className="panel-description">
        Based on your uploaded documents, here&apos;s what we found for each condition.
      </p>

      {gaps.map((gap) => (
        <div key={gap.condition} className="condition-card">
          <div className="condition-header">
            <h4>{gap.condition}</h4>
            <span className={`strength-badge ${getStrengthColor(gap.claim_strength)}`}>
              {getStrengthLabel(gap.claim_strength)} ({Math.round(gap.claim_strength * 100)}%)
            </span>
          </div>

          {gap.missing_required.length > 0 && (
            <div className="gap-section required">
              <h5>
                <span className="icon">⚠️</span>
                Required Documents Missing
              </h5>
              <ul>
                {gap.missing_required.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {gap.missing_recommended.length > 0 && (
            <div className="gap-section recommended">
              <h5>
                <span className="icon">📋</span>
                Recommended Documents
              </h5>
              <ul>
                {gap.missing_recommended.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {gap.missing_helpful.length > 0 && (
            <div className="gap-section helpful">
              <h5>
                <span className="icon">💡</span>
                Helpful to Include
              </h5>
              <ul>
                {gap.missing_helpful.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
          )}

          {gap.missing_required.length === 0 &&
           gap.missing_recommended.length === 0 && (
            <div className="gap-section complete">
              <p>✅ You have all required and recommended evidence for this condition.</p>
            </div>
          )}
        </div>
      ))}

      <style jsx>{`
        .evidence-gap-panel {
          background: var(--bg-secondary, #f8f9fa);
          border-radius: 8px;
          padding: 1.5rem;
          margin: 1rem 0;
        }

        .evidence-gap-panel h3 {
          margin: 0 0 0.5rem 0;
          color: var(--text-primary, #1a1a1a);
        }

        .panel-description {
          color: var(--text-secondary, #666);
          margin-bottom: 1rem;
        }

        .condition-card {
          background: white;
          border: 1px solid var(--border-color, #e0e0e0);
          border-radius: 6px;
          padding: 1rem;
          margin-bottom: 1rem;
        }

        .condition-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
        }

        .condition-header h4 {
          margin: 0;
          font-size: 1.1rem;
        }

        .strength-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 20px;
          font-size: 0.85rem;
          font-weight: 500;
        }

        .strength-high {
          background: #d4edda;
          color: #155724;
        }

        .strength-medium {
          background: #fff3cd;
          color: #856404;
        }

        .strength-low {
          background: #f8d7da;
          color: #721c24;
        }

        .gap-section {
          margin-top: 0.75rem;
          padding: 0.75rem;
          border-radius: 4px;
        }

        .gap-section.required {
          background: #fff5f5;
          border-left: 3px solid #dc3545;
        }

        .gap-section.recommended {
          background: #fffbf0;
          border-left: 3px solid #ffc107;
        }

        .gap-section.helpful {
          background: #f0f9ff;
          border-left: 3px solid #17a2b8;
        }

        .gap-section.complete {
          background: #f0fff4;
          border-left: 3px solid #28a745;
        }

        .gap-section h5 {
          margin: 0 0 0.5rem 0;
          font-size: 0.9rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .gap-section ul {
          margin: 0;
          padding-left: 1.5rem;
        }

        .gap-section li {
          margin: 0.25rem 0;
        }

        .loading, .error, .empty {
          text-align: center;
          padding: 2rem;
        }

        .spinner {
          width: 24px;
          height: 24px;
          border: 3px solid #e0e0e0;
          border-top-color: #007bff;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
};

export default EvidenceGapPanel;
```

---

## Success Criteria

- File exists at `/ganuda/vetassist/frontend/components/wizard/EvidenceGapPanel.tsx`
- TypeScript types defined
- Responsive styling included
- Loading and error states handled

---

## For Seven Generations

Clear visual feedback helps veterans understand exactly what they need for a strong claim.

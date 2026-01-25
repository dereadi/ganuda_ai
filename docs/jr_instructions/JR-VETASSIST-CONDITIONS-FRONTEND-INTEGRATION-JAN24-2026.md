# Jr Instruction: Connect Conditions Step to CFR Mapping API

**Task ID:** VETASSIST-CFR-001
**Priority:** P1
**Date:** January 24, 2026

## Problem

The wizard's ConditionsStep.tsx uses a **hardcoded list of 20 conditions** instead of calling the backend `/api/v1/conditions/map` endpoint which has:
- 49 conditions in database
- Natural language mapping ("ringing in ears" → Tinnitus)
- Synonyms and common names
- Rating criteria for each severity level
- Evidence requirements
- DBQ form references

## Objective

Connect the frontend wizard to the backend CFR conditions API for dynamic, intelligent condition matching.

## Current State

**File:** `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/steps/ConditionsStep.tsx`

```tsx
// Lines 27-48: Hardcoded list
const COMMON_CONDITIONS: Condition[] = [
  { id: 'ptsd', name: 'PTSD', category: 'Mental Health', dc_code: '9411' },
  // ... 19 more hardcoded conditions
];

// Line 61-64: Client-side filter only
const filteredConditions = COMMON_CONDITIONS.filter(c =>
  c.name.toLowerCase().includes(search.toLowerCase())
);
```

## Target State

```tsx
// Dynamic API call with debounce
const [apiResults, setApiResults] = useState<ConditionMatch[]>([]);
const [isSearching, setIsSearching] = useState(false);

// Debounced search function
useEffect(() => {
  const timer = setTimeout(async () => {
    if (search.length >= 2) {
      setIsSearching(true);
      try {
        const response = await fetch('/api/v1/conditions/map', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ description: search })
        });
        const data = await response.json();
        setApiResults(data);
      } catch (e) {
        console.error('Condition search failed:', e);
      }
      setIsSearching(false);
    }
  }, 300); // 300ms debounce

  return () => clearTimeout(timer);
}, [search]);
```

## Implementation Steps

### Step 1: Update Type Definitions

```tsx
// Enhanced interface to match backend response
interface ConditionMatch {
  diagnostic_code: string;
  condition_name: string;
  body_system: string;
  match_score: number;
  rating_criteria: Record<string, string>;
  evidence_requirements: string[];
  dbq_form: string | null;
}

interface ClaimedCondition {
  condition_id: string;
  condition_name: string;
  diagnostic_code: string;  // ADD: Store the DC code
  body_system: string;      // ADD: Store body system
  onset_date: string;
  service_connection: 'direct' | 'secondary' | 'aggravated';
  description: string;
  rating_criteria?: Record<string, string>;      // ADD: For display
  evidence_requirements?: string[];               // ADD: For checklist
}
```

### Step 2: Add API Search Hook

Create `/ganuda/vetassist/frontend/app/wizard/[sessionId]/hooks/useConditionSearch.ts`:

```tsx
import { useState, useEffect } from 'react';
import { apiClient } from '@/lib/api-client';

interface ConditionMatch {
  diagnostic_code: string;
  condition_name: string;
  body_system: string;
  match_score: number;
  rating_criteria: Record<string, string>;
  evidence_requirements: string[];
  dbq_form: string | null;
}

export function useConditionSearch(query: string, debounceMs = 300) {
  const [results, setResults] = useState<ConditionMatch[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (query.length < 2) {
      setResults([]);
      return;
    }

    const timer = setTimeout(async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await apiClient.post('/conditions/map', {
          description: query
        });
        setResults(response.data);
      } catch (e: any) {
        setError(e.message || 'Search failed');
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  return { results, isLoading, error };
}
```

### Step 3: Update ConditionsStep.tsx

Replace hardcoded search with API hook:

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Search, Plus, Trash2, AlertCircle, HelpCircle, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { useConditionSearch } from '../hooks/useConditionSearch';

// ... (keep existing interfaces with enhancements from Step 1)

// REMOVE the hardcoded COMMON_CONDITIONS array

export default function ConditionsStep({ formData, updateField }: Props) {
  const [search, setSearch] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [expandedCondition, setExpandedCondition] = useState<string | null>(null);
  const [claimedConditions, setClaimedConditions] = useState<ClaimedCondition[]>(
    formData.conditions || []
  );

  // Use the API search hook
  const { results: apiResults, isLoading, error } = useConditionSearch(search);

  useEffect(() => {
    updateField('conditions', claimedConditions);
  }, [claimedConditions]);

  const addCondition = (match: ConditionMatch) => {
    if (claimedConditions.find(c => c.diagnostic_code === match.diagnostic_code)) return;

    setClaimedConditions([
      ...claimedConditions,
      {
        condition_id: match.diagnostic_code,
        condition_name: match.condition_name,
        diagnostic_code: match.diagnostic_code,
        body_system: match.body_system,
        onset_date: '',
        service_connection: 'direct',
        description: '',
        rating_criteria: match.rating_criteria,
        evidence_requirements: match.evidence_requirements,
      }
    ]);
    setSearch('');
    setShowResults(false);
  };

  // ... rest of component with enhanced UI
```

### Step 4: Enhanced Search Results UI

Show match score and body system in results:

```tsx
{showResults && search.length >= 2 && (
  <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-80 overflow-y-auto">
    {isLoading ? (
      <div className="px-4 py-6 text-center">
        <Loader2 className="h-6 w-6 animate-spin text-blue-500 mx-auto" />
        <p className="text-sm text-gray-500 mt-2">Searching conditions...</p>
      </div>
    ) : apiResults.length > 0 ? (
      apiResults.map(match => (
        <button
          key={match.diagnostic_code}
          onClick={() => addCondition(match)}
          disabled={claimedConditions.some(c => c.diagnostic_code === match.diagnostic_code)}
          className="w-full text-left px-4 py-3 hover:bg-blue-50 border-b border-gray-100 last:border-0 disabled:opacity-50 disabled:bg-gray-100"
        >
          <div className="flex justify-between items-start">
            <div>
              <span className="font-medium text-gray-900">{match.condition_name}</span>
              <div className="flex gap-2 mt-1">
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">
                  {match.body_system}
                </span>
                <span className="text-xs bg-blue-100 text-blue-700 px-2 py-0.5 rounded">
                  DC {match.diagnostic_code}
                </span>
              </div>
            </div>
            <span className={`text-xs font-medium ${
              match.match_score > 0.8 ? 'text-green-600' :
              match.match_score > 0.5 ? 'text-yellow-600' : 'text-gray-500'
            }`}>
              {Math.round(match.match_score * 100)}% match
            </span>
          </div>
        </button>
      ))
    ) : (
      <div className="px-4 py-4">
        <p className="text-gray-600 font-medium">No exact matches found</p>
        <p className="text-sm text-gray-500 mt-1">
          Try describing your symptoms differently, or consult with a VSO for guidance.
        </p>
      </div>
    )}
  </div>
)}
```

### Step 5: Show Rating Criteria and Evidence for Added Conditions

```tsx
{claimedConditions.map((c, index) => (
  <div key={c.condition_id} className="p-4 border border-gray-200 rounded-lg bg-white">
    {/* ... existing header and fields ... */}

    {/* Expandable rating criteria section */}
    <div className="mt-4 border-t pt-4">
      <button
        onClick={() => setExpandedCondition(
          expandedCondition === c.condition_id ? null : c.condition_id
        )}
        className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-800"
      >
        {expandedCondition === c.condition_id ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
        View rating criteria & evidence requirements
      </button>

      {expandedCondition === c.condition_id && c.rating_criteria && (
        <div className="mt-3 space-y-3">
          <div className="bg-gray-50 p-3 rounded-lg">
            <h5 className="font-medium text-gray-900 text-sm mb-2">Rating Levels</h5>
            <div className="space-y-1">
              {Object.entries(c.rating_criteria)
                .sort(([a], [b]) => Number(b) - Number(a))
                .map(([rating, criteria]) => (
                  <div key={rating} className="flex gap-3 text-sm">
                    <span className="font-medium text-blue-700 w-12">{rating}%</span>
                    <span className="text-gray-600">{criteria}</span>
                  </div>
                ))
              }
            </div>
          </div>

          {c.evidence_requirements && c.evidence_requirements.length > 0 && (
            <div className="bg-green-50 p-3 rounded-lg">
              <h5 className="font-medium text-green-900 text-sm mb-2">Evidence Needed</h5>
              <ul className="space-y-1">
                {c.evidence_requirements.map((req, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm text-green-700">
                    <span className="text-green-500">•</span>
                    {req}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  </div>
))}
```

## Testing

1. Search "ringing in ears" → Should return Tinnitus (6260)
2. Search "bad back" → Should return Lumbosacral Strain (5237)
3. Search "nightmares deployment" → Should return PTSD (9411)
4. Click condition → Should add with rating criteria visible
5. Expand criteria → Should show all rating levels and evidence requirements

## Success Criteria

- [ ] Hardcoded COMMON_CONDITIONS removed
- [ ] API search with debounce working
- [ ] Match score displayed
- [ ] Rating criteria expandable for each condition
- [ ] Evidence requirements visible
- [ ] Loading state shown during search
- [ ] Graceful handling of no results

---

**FOR SEVEN GENERATIONS** - Help veterans understand what they're claiming and what they need to prove it.

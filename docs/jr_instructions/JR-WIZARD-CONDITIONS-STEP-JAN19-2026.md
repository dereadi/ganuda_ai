# Jr Instruction: VetAssist Wizard Conditions Step (21-526EZ Step 3)

```yaml
task_id: wizard_conditions_step
priority: 2
assigned_to: it_triad_jr
target: redfin
estimated_effort: 60 minutes
depends_on: wizard_step_container
```

## Objective

Create the Conditions step component for the 21-526EZ form (Step 3). This is the most complex step - veterans select/add their claimed conditions.

## Requirements

1. Search/filter for VA-recognized conditions
2. Add multiple conditions
3. For each condition, capture:
   - Condition name
   - Approximate onset date
   - Whether related to service (direct, secondary, aggravated)
   - Brief description of how it relates to service

## Backend API

The backend should have `/api/v1/conditions` endpoint returning:
```json
{
  "conditions": [
    { "id": "ptsd", "name": "PTSD", "category": "mental_health", "dc_code": "9411" },
    { "id": "tinnitus", "name": "Tinnitus", "category": "ear", "dc_code": "6260" },
    ...
  ]
}
```

## UI Components

1. **Condition Search** - Autocomplete search for conditions
2. **Condition Card** - Display added condition with edit/remove
3. **Condition Form** - Modal/inline form for condition details

## Code Location

Create: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/components/steps/ConditionsStep.tsx`

## Code Template

```tsx
'use client';

import { useState, useEffect } from 'react';
import { Search, Plus, Trash2, AlertCircle } from 'lucide-react';

interface Condition {
  id: string;
  name: string;
  category: string;
  dc_code: string;
}

interface ClaimedCondition {
  condition_id: string;
  condition_name: string;
  onset_date: string;
  service_connection: 'direct' | 'secondary' | 'aggravated';
  description: string;
}

interface Props {
  formData: Record<string, any>;
  updateField: (field: string, value: any) => void;
}

export default function ConditionsStep({ formData, updateField }: Props) {
  const [conditions, setConditions] = useState<Condition[]>([]);
  const [search, setSearch] = useState('');
  const [showResults, setShowResults] = useState(false);
  const [claimedConditions, setClaimedConditions] = useState<ClaimedCondition[]>(
    formData.conditions || []
  );

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api/v1';

  useEffect(() => {
    fetchConditions();
  }, []);

  useEffect(() => {
    updateField('conditions', claimedConditions);
  }, [claimedConditions]);

  const fetchConditions = async () => {
    try {
      const res = await fetch(`${apiUrl}/conditions`);
      if (res.ok) {
        const data = await res.json();
        setConditions(data.conditions || []);
      }
    } catch {
      // Use fallback list
      setConditions(COMMON_CONDITIONS);
    }
  };

  const filteredConditions = conditions.filter(c =>
    c.name.toLowerCase().includes(search.toLowerCase())
  );

  const addCondition = (condition: Condition) => {
    if (claimedConditions.find(c => c.condition_id === condition.id)) return;

    setClaimedConditions([
      ...claimedConditions,
      {
        condition_id: condition.id,
        condition_name: condition.name,
        onset_date: '',
        service_connection: 'direct',
        description: ''
      }
    ]);
    setSearch('');
    setShowResults(false);
  };

  const removeCondition = (id: string) => {
    setClaimedConditions(claimedConditions.filter(c => c.condition_id !== id));
  };

  const updateCondition = (id: string, field: string, value: string) => {
    setClaimedConditions(
      claimedConditions.map(c =>
        c.condition_id === id ? { ...c, [field]: value } : c
      )
    );
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-medium text-gray-900 mb-2">Add Conditions</h3>
        <p className="text-sm text-gray-600 mb-4">
          Search for conditions you want to claim. You can add multiple conditions.
        </p>

        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setShowResults(true);
            }}
            onFocus={() => setShowResults(true)}
            placeholder="Search conditions (e.g., PTSD, tinnitus, back pain)"
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />

          {showResults && search && (
            <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
              {filteredConditions.length > 0 ? (
                filteredConditions.slice(0, 10).map(c => (
                  <button
                    key={c.id}
                    onClick={() => addCondition(c)}
                    className="w-full text-left px-4 py-2 hover:bg-gray-50 flex justify-between"
                  >
                    <span>{c.name}</span>
                    <span className="text-xs text-gray-500">DC {c.dc_code}</span>
                  </button>
                ))
              ) : (
                <div className="px-4 py-2 text-gray-500">No matching conditions</div>
              )}
            </div>
          )}
        </div>
      </div>

      {claimedConditions.length > 0 && (
        <div className="space-y-4">
          <h3 className="font-medium text-gray-900">Your Conditions ({claimedConditions.length})</h3>

          {claimedConditions.map(c => (
            <div key={c.condition_id} className="p-4 border border-gray-200 rounded-lg">
              <div className="flex justify-between items-start mb-3">
                <h4 className="font-medium">{c.condition_name}</h4>
                <button
                  onClick={() => removeCondition(c.condition_id)}
                  className="text-red-500 hover:text-red-700"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Approximate onset date
                  </label>
                  <input
                    type="date"
                    value={c.onset_date}
                    onChange={(e) => updateCondition(c.condition_id, 'onset_date', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>

                <div>
                  <label className="block text-sm text-gray-600 mb-1">
                    Service connection type
                  </label>
                  <select
                    value={c.service_connection}
                    onChange={(e) => updateCondition(c.condition_id, 'service_connection', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="direct">Direct (occurred during service)</option>
                    <option value="secondary">Secondary (caused by another condition)</option>
                    <option value="aggravated">Aggravated (worsened by service)</option>
                  </select>
                </div>
              </div>

              <div className="mt-3">
                <label className="block text-sm text-gray-600 mb-1">
                  How is this related to your service?
                </label>
                <textarea
                  value={c.description}
                  onChange={(e) => updateCondition(c.condition_id, 'description', e.target.value)}
                  placeholder="Briefly describe how this condition relates to your military service..."
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          ))}
        </div>
      )}

      {claimedConditions.length === 0 && (
        <div className="text-center py-8 bg-gray-50 rounded-lg">
          <AlertCircle className="h-8 w-8 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-600">No conditions added yet</p>
          <p className="text-sm text-gray-500">Use the search above to add conditions</p>
        </div>
      )}
    </div>
  );
}

// Fallback common conditions list
const COMMON_CONDITIONS: Condition[] = [
  { id: 'ptsd', name: 'PTSD', category: 'mental_health', dc_code: '9411' },
  { id: 'tinnitus', name: 'Tinnitus', category: 'ear', dc_code: '6260' },
  { id: 'hearing_loss', name: 'Hearing Loss', category: 'ear', dc_code: '6100' },
  { id: 'back_pain', name: 'Lumbosacral Strain', category: 'spine', dc_code: '5237' },
  { id: 'knee_left', name: 'Left Knee Condition', category: 'joint', dc_code: '5257' },
  { id: 'knee_right', name: 'Right Knee Condition', category: 'joint', dc_code: '5257' },
  { id: 'migraine', name: 'Migraine Headaches', category: 'neurological', dc_code: '8100' },
  { id: 'depression', name: 'Major Depressive Disorder', category: 'mental_health', dc_code: '9434' },
  { id: 'anxiety', name: 'Generalized Anxiety Disorder', category: 'mental_health', dc_code: '9400' },
  { id: 'sleep_apnea', name: 'Sleep Apnea', category: 'respiratory', dc_code: '6847' },
];
```

## Integration

Update the main page.tsx to import and render this component for step 3.

## Success Criteria

1. [ ] Condition search shows autocomplete results
2. [ ] Can add multiple conditions
3. [ ] Each condition has onset date, connection type, description
4. [ ] Can remove conditions
5. [ ] Form data persists when navigating

---
*Cherokee AI Federation - For the Seven Generations*

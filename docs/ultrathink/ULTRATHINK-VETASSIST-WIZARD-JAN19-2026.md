# ULTRATHINK: VetAssist Claim Wizard Implementation

## Executive Summary

Build a step-by-step guided wizard for VA disability claim preparation. The backend already defines 4 form types with steps. We need to build the frontend wizard UI that guides veterans through the process.

## Existing Infrastructure

### Backend Forms (Already Implemented)
```
21-526EZ - Application for Disability Compensation (5 steps)
21-0995  - Supplemental Claim (3 steps)
20-0996  - Higher-Level Review (4 steps)
10182    - Board of Veterans Appeals (4 steps)
```

### Backend Endpoints
- `POST /wizard/start` - Start a new wizard session
- `POST /wizard/{session_id}/step/{step_num}` - Submit step answers
- `GET /wizard/{session_id}` - Get wizard progress
- `GET /wizard/forms` - List available form types

## Design Decisions

### 1. Form Selection Screen
First screen shows the 4 claim types with:
- Clear descriptions of when to use each
- Expected time to complete
- Required documents checklist

### 2. Step-by-Step Flow
Each step shows:
- Progress bar (Step X of Y)
- Current step title and description
- Form fields for that step
- AI assistance button (calls chat for help)
- Save & Continue / Back buttons

### 3. Field Types
- Text input (name, address)
- Date picker (DOB, service dates)
- Multi-select (conditions, symptoms)
- File upload (medical records)
- Checkbox (confirmations)
- Radio (yes/no questions)

### 4. AI Integration Points
- "Need help?" button on each field → opens chat
- Condition suggestions based on symptoms
- Evidence checklist based on selected conditions
- Nexus letter guidance

## Implementation Plan

### Phase 1: Form Selection (Jr Task)
Create `/ganuda/vetassist/frontend/app/wizard/page.tsx`:
- Grid of 4 form types
- Card for each with icon, title, description
- Click → starts wizard session

### Phase 2: Step Container (Jr Task)
Create `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`:
- Fetches wizard state from backend
- Renders current step component
- Progress bar
- Navigation buttons

### Phase 3: Step Components (Jr Tasks)
Create step components for 21-526EZ:
- `StepPersonalInfo.tsx` - Name, SSN, DOB, Address
- `StepMilitaryService.tsx` - Branch, dates, discharge
- `StepConditions.tsx` - Add/manage conditions
- `StepEvidence.tsx` - Upload documents, buddy statements
- `StepReview.tsx` - Summary and confirmation

### Phase 4: AI Assistance
- "Help with this field" button
- Opens chat sidebar with context
- Suggestions for conditions based on symptoms

## File Structure

```
/ganuda/vetassist/frontend/app/wizard/
├── page.tsx                    # Form selection
├── [sessionId]/
│   ├── page.tsx               # Step container
│   └── components/
│       ├── ProgressBar.tsx
│       ├── StepNavigation.tsx
│       └── steps/
│           ├── PersonalInfo.tsx
│           ├── MilitaryService.tsx
│           ├── Conditions.tsx
│           ├── Evidence.tsx
│           └── Review.tsx
└── components/
    ├── FormCard.tsx           # Form type card
    └── WizardHelp.tsx         # AI help sidebar
```

## API Integration

### Start Wizard
```typescript
const response = await fetch('/api/v1/wizard/start', {
  method: 'POST',
  body: JSON.stringify({
    wizard_type: '21-526EZ',
    veteran_id: user.id
  })
});
const { session_id } = await response.json();
router.push(`/wizard/${session_id}`);
```

### Submit Step
```typescript
await fetch(`/api/v1/wizard/${sessionId}/step/${stepNum}`, {
  method: 'POST',
  body: JSON.stringify({ answers: formData })
});
```

## Jr Instructions to Create

1. **JR-WIZARD-FORM-SELECTION** - Form selection page with 4 cards
2. **JR-WIZARD-STEP-CONTAINER** - Dynamic step container
3. **JR-WIZARD-PERSONAL-INFO** - Step 1 component
4. **JR-WIZARD-MILITARY-SERVICE** - Step 2 component
5. **JR-WIZARD-CONDITIONS** - Step 3 with condition picker
6. **JR-WIZARD-EVIDENCE** - Step 4 with file upload
7. **JR-WIZARD-REVIEW** - Step 5 summary

## Success Criteria

1. [ ] Veteran can select claim type
2. [ ] Wizard session created in database
3. [ ] Progress bar shows current step
4. [ ] Form data saved on each step
5. [ ] Can navigate back to previous steps
6. [ ] Review step shows all entered data
7. [ ] AI help available on each step

## Priority

Start with 21-526EZ (most common form) and make it fully functional before adding other form types.

---

*Cherokee AI Federation - For the Seven Generations*
*"Guide the warrior through the bureaucratic battle, step by step."*

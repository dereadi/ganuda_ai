# JR Instruction: VetAssist Form Wizards

## Metadata
```yaml
task_id: vetassist_form_wizards
priority: 2
assigned_to: VetAssist Jr.
target: frontend + backend
estimated_effort: medium
dependencies:
  - Enhanced Veteran Profile (for auto-fill)
```

## Overview

Build step-by-step wizards to help veterans understand what information they need for VA forms. We DO NOT file forms - we educate and help organize.

## Wizards to Build

### 1. Intent to File Wizard
Helps veteran understand ITF benefits and what to prepare.

```
Step 1: What is Intent to File?
  - Protects your effective date
  - Gives you 1 year to complete claim
  - [Learn More] expandable

Step 2: What You'll Need
  - VA.gov account (explain how to create)
  - Decision to file (disability, pension, survivor)

Step 3: Next Steps
  - Link to VA.gov ITF page
  - "We'll remind you in 10 months" (if notifications enabled)
```

### 2. New Claim Checklist Wizard (21-526EZ prep)

```
Step 1: Condition Selection
  - What conditions are you claiming?
  - [Add Condition] → suggests from our database
  - Auto-links to evidence checklist

Step 2: Evidence Inventory
  - For each condition, show required evidence:
    □ Service treatment records
    □ Current diagnosis
    □ Nexus letter / IMO
    □ Buddy statements
  - Track what they have vs need

Step 3: Personal Statement Guidance
  - Template: "I am claiming [condition] because..."
  - Tips for effective statements
  - Save draft to workbench

Step 4: Review & Checklist
  - Summary of conditions
  - Evidence status (have/need)
  - "You're ready to file when all green"
  - Link to VA.gov eBenefits
```

### 3. Rating Increase Wizard

```
Step 1: Current Rating
  - Pull from profile or enter manually
  - Which condition getting worse?

Step 2: Evidence of Worsening
  - New medical records needed
  - Recent treatment dates
  - Symptoms that have changed

Step 3: Prepare Statement
  - Template for increase claim
  - Compare old vs new symptoms

Step 4: File Guidance
  - Link to VA supplemental claim form
```

## Frontend Components

```typescript
// Wizard container
<FormWizard
  steps={wizardSteps}
  onComplete={handleComplete}
  saveProgress={true}  // Save to workbench
/>

// Step component
<WizardStep
  title="What conditions are you claiming?"
  description="Select all that apply"
  validation={requiredFields}
>
  <ConditionSelector
    suggestions={conditionDatabase}
    onSelect={addCondition}
  />
</WizardStep>

// Progress indicator
<WizardProgress
  currentStep={3}
  totalSteps={5}
  completedSteps={[1, 2]}
/>
```

## Backend Endpoints

```
GET  /api/v1/wizards/itf           - Get ITF wizard content
GET  /api/v1/wizards/new-claim     - Get new claim wizard
GET  /api/v1/wizards/increase      - Get increase wizard

POST /api/v1/wizards/progress      - Save wizard progress
GET  /api/v1/wizards/progress/:id  - Get saved progress

GET  /api/v1/conditions/search?q=  - Search condition database
GET  /api/v1/conditions/:id/evidence - Get evidence checklist
```

## Database

```sql
-- Wizard progress (bluefin)
CREATE TABLE wizard_progress (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    wizard_type VARCHAR(50) NOT NULL,  -- 'itf', 'new_claim', 'increase'
    current_step INT DEFAULT 1,
    data JSONB DEFAULT '{}',
    completed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

## Legal Disclaimer

Every wizard must include:

```
DISCLAIMER: This tool helps you understand and organize information
for your VA claim. It does not constitute legal advice and does not
file any forms on your behalf. Always verify information with the VA
or a certified VSO representative.
```

## Success Criteria

- [ ] ITF wizard explains intent to file
- [ ] New claim wizard generates evidence checklist
- [ ] Wizards save progress to workbench
- [ ] Clear disclaimers on every wizard
- [ ] Links to official VA.gov pages

---

*Cherokee AI Federation - For the Seven Generations*

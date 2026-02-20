# JR INSTRUCTION: POC - Evaluate react-jsonschema-form vs. YAML Wizard

**Task ID:** ASSIST-POC-RJSF
**Priority:** P2 - Proof of concept
**Assigned To:** Any available Jr
**Created By:** TPM + Council (APPROVE pending POC)
**Date:** 2026-02-04
**Estimated Effort:** 4-6 hours
**Node:** Any (development environment required)

---

## Objective

Evaluate whether react-jsonschema-form (RJSF) should replace our custom YAML-driven wizard engine for VetAssist, SSIDAssist, and TribeAssist applications.

## Context

Our current wizard system uses YAML configuration files parsed by WizardShell.tsx. This works but requires custom code for:
- Conditional field display
- Validation logic
- Progress persistence
- Accessibility features

RJSF is a mature library that generates forms from JSON Schema. If it meets our requirements, we could reduce custom code and leverage community-maintained validation/accessibility features.

## Success Criteria

- Side-by-side comparison demo working
- All evaluation criteria assessed and documented
- Clear recommendation: ADOPT, ADAPT, or BUILD OUR OWN
- No modifications to production Assist code

---

## Steps

### 1. Setup Test Environment

```bash
# Create isolated test directory
mkdir -p /ganuda/tmp/rjsf-poc
cd /ganuda/tmp/rjsf-poc

# Initialize minimal React app
npm create vite@latest rjsf-test -- --template react-ts
cd rjsf-test

# Install RJSF dependencies
npm install @rjsf/core @rjsf/utils @rjsf/validator-ajv8

# Install our current wizard for comparison
# (copy WizardShell.tsx and one YAML file)
```

**Verification:** `npm run dev` starts without errors

### 2. Convert SSDI Wizard Step 1 to JSON Schema

Locate the SSDI application wizard YAML:
```bash
find /ganuda/assist -name "ssdi_application.yaml" -o -name "*ssdi*.yaml"
```

Extract Step 1 (Personal Information) and convert to JSON Schema format:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Personal Information",
  "type": "object",
  "required": ["firstName", "lastName", "dateOfBirth", "ssn"],
  "properties": {
    "firstName": {
      "type": "string",
      "title": "First Name / ᎠᏍᎦᏯ ᎤᏪᏥ (Asgaya Uwetsi)"
    },
    "lastName": {
      "type": "string",
      "title": "Last Name / ᎠᏍᎦᏯ ᎤᏍᏗ (Asgaya Usdi)"
    },
    "middleName": {
      "type": "string",
      "title": "Middle Name (Optional)"
    },
    "dateOfBirth": {
      "type": "string",
      "format": "date",
      "title": "Date of Birth"
    },
    "ssn": {
      "type": "string",
      "title": "Social Security Number",
      "pattern": "^\\d{3}-\\d{2}-\\d{4}$"
    },
    "hasMailingAddress": {
      "type": "boolean",
      "title": "Is your mailing address different from your residential address?"
    }
  },
  "dependencies": {
    "hasMailingAddress": {
      "oneOf": [
        {
          "properties": {
            "hasMailingAddress": { "enum": [false] }
          }
        },
        {
          "properties": {
            "hasMailingAddress": { "enum": [true] },
            "mailingStreet": {
              "type": "string",
              "title": "Mailing Street Address"
            },
            "mailingCity": {
              "type": "string",
              "title": "City"
            },
            "mailingState": {
              "type": "string",
              "title": "State"
            },
            "mailingZip": {
              "type": "string",
              "title": "ZIP Code",
              "pattern": "^\\d{5}(-\\d{4})?$"
            }
          },
          "required": ["mailingStreet", "mailingCity", "mailingState", "mailingZip"]
        }
      ]
    }
  }
}
```

**Verification:** JSON Schema validates with `ajv` or online validator

### 3. Build Side-by-Side Comparison

Create `src/Comparison.tsx`:

```typescript
import { useState } from 'react';
import Form from '@rjsf/core';
import validator from '@rjsf/validator-ajv8';
// Import our WizardShell (copy from assist codebase)
import { WizardShell } from './WizardShell';
import personalInfoSchema from './personal-info-schema.json';
import personalInfoYaml from './personal-info.yaml';

export default function Comparison() {
  return (
    <div style={{ display: 'flex', gap: '2rem' }}>
      <div style={{ flex: 1, borderRight: '2px solid #ccc', paddingRight: '2rem' }}>
        <h2>Current: YAML + WizardShell</h2>
        <WizardShell config={personalInfoYaml} />
      </div>

      <div style={{ flex: 1, paddingLeft: '2rem' }}>
        <h2>POC: RJSF + JSON Schema</h2>
        <Form
          schema={personalInfoSchema}
          validator={validator}
          onSubmit={({formData}) => console.log('RJSF submitted:', formData)}
        />
      </div>
    </div>
  );
}
```

**Verification:** Both forms render side-by-side without errors

### 4. Evaluation Matrix

Test each criterion and document findings:

#### 4.1 Conditional Logic

**Test:** Show/hide mailing address fields based on checkbox

YAML approach:
```yaml
- field: hasMailingAddress
  type: boolean
  label: "Different mailing address?"
- field: mailingStreet
  type: text
  condition: hasMailingAddress === true
```

RJSF approach:
```json
{
  "dependencies": {
    "hasMailingAddress": {
      "oneOf": [...]
    }
  }
}
```

**Evaluate:**
- Does RJSF conditional logic work correctly?
- Is it more/less intuitive than our YAML?
- Can it handle complex conditions (field X if Y=Z AND A>B)?

#### 4.2 Accessibility

Run axe-core on both implementations:

```bash
npm install @axe-core/react
```

```typescript
import { useEffect } from 'react';
if (process.env.NODE_ENV !== 'production') {
  import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000);
  });
}
```

**Evaluate:**
- Number of accessibility violations for each
- ARIA labels present and correct?
- Keyboard navigation working?
- Screen reader compatibility?

#### 4.3 Cherokee Text Rendering

**Test cases:**
- ᏣᎳᎩ ᎦᏬᏂᎯᏍᏗ (Cherokee Language)
- ᎠᏍᎦᏯ (Person)
- ᎤᏪᏥ (Name)

**Evaluate:**
- Does Cherokee text display correctly in labels?
- Are Cherokee characters preserved in form data?
- Any font/encoding issues?
- Right-to-left text handling (if applicable)?

#### 4.4 Custom Validation

**Test:** Add SSN format validator and future date validator

YAML approach:
```typescript
// Custom validator in WizardShell
validators: {
  ssn: (value) => /^\d{3}-\d{2}-\d{4}$/.test(value),
  notFutureDate: (value) => new Date(value) <= new Date()
}
```

RJSF approach:
```typescript
// Custom validation via transformErrors
const transformErrors = (errors) => {
  return errors.map(error => {
    if (error.name === 'pattern' && error.property === '.ssn') {
      error.message = 'SSN must be in format XXX-XX-XXXX';
    }
    return error;
  });
};

// Custom format validator
const customFormats = {
  'ssn': /^\d{3}-\d{2}-\d{4}$/,
  'not-future-date': (value) => new Date(value) <= new Date()
};
```

**Evaluate:**
- How easy is it to add custom validators?
- Can validators access other field values (cross-field validation)?
- Error message customization?
- Async validation support (e.g., check if email exists)?

#### 4.5 Integration: Save/Resume Progress

**Test:** Serialize form state and restore it

```typescript
// Save current form state
const saveProgress = (formData) => {
  localStorage.setItem('wizard-progress', JSON.stringify(formData));
};

// Restore on page load
const loadProgress = () => {
  const saved = localStorage.getItem('wizard-progress');
  return saved ? JSON.parse(saved) : {};
};
```

**Evaluate:**
- Does RJSF's formData prop work for restoration?
- Can we save/restore at any point in the wizard?
- How do we handle schema changes between versions?
- Database persistence strategy?

#### 4.6 Bundle Size Impact

```bash
# Build both versions
npm run build

# Check bundle sizes
ls -lh dist/assets/*.js

# Use webpack-bundle-analyzer or similar
npm install --save-dev webpack-bundle-analyzer
```

**Evaluate:**
- Size of RJSF dependencies
- Tree-shaking effectiveness
- Impact on initial load time
- Lazy-loading options?

### 5. Write Findings Report

Create `/ganuda/docs/reports/POC-RJSF-FINDINGS-FEB04-2026.md`:

```markdown
# POC Findings: react-jsonschema-form vs. YAML Wizard

**Date:** 2026-02-04
**Evaluated By:** [Jr Name]
**Duration:** [X hours]

## Executive Summary

[2-3 sentence summary of recommendation]

## Evaluation Results

| Criterion | YAML Wizard | RJSF | Winner |
|-----------|-------------|------|--------|
| Conditional Logic | [score/notes] | [score/notes] | [YAML/RJSF/TIE] |
| Accessibility | [violations count] | [violations count] | [YAML/RJSF/TIE] |
| Cherokee Text | [works/issues] | [works/issues] | [YAML/RJSF/TIE] |
| Custom Validation | [ease rating] | [ease rating] | [YAML/RJSF/TIE] |
| Save/Resume | [complexity] | [complexity] | [YAML/RJSF/TIE] |
| Bundle Size | [XXX KB] | [XXX KB] | [YAML/RJSF/TIE] |

## Detailed Analysis

### Conditional Logic
[Detailed findings...]

### Accessibility
[axe-core results, ARIA analysis...]

### Cherokee Text Rendering
[Screenshots, font issues, encoding tests...]

### Custom Validation
[Code examples, ease of implementation...]

### Integration Complexity
[State management, persistence strategy...]

### Bundle Size Impact
[Build analysis, load time impact...]

## Pros and Cons

### RJSF Advantages
- [Pro 1]
- [Pro 2]
- [Pro 3]

### RJSF Disadvantages
- [Con 1]
- [Con 2]
- [Con 3]

### YAML Wizard Advantages
- [Pro 1]
- [Pro 2]
- [Pro 3]

### YAML Wizard Disadvantages
- [Con 1]
- [Con 2]
- [Con 3]

## Recommendation

**[ADOPT / ADAPT / BUILD OUR OWN]**

### If ADOPT:
- Migration path: [strategy]
- Timeline: [estimate]
- Risk: [assessment]

### If ADAPT:
- What to use from RJSF: [specific features]
- What to keep from YAML: [specific features]
- Hybrid architecture: [design]

### If BUILD OUR OWN:
- What we learned from RJSF: [key insights]
- What to improve in YAML wizard: [specific enhancements]
- Rationale: [why neither option works]

## Next Steps

1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

## Appendices

### A. Test URLs
- YAML demo: [URL]
- RJSF demo: [URL]

### B. Code Samples
[Relevant code snippets]

### C. Screenshots
[Visual comparisons]
```

**Verification:** Report is complete, data-driven, and actionable

### 6. Council Recommendation

Prepare summary for Council review:

```markdown
## Council Review Package

**Recommendation:** [ADOPT/ADAPT/BUILD]

**Key Decision Factors:**
1. [Factor 1 with data]
2. [Factor 2 with data]
3. [Factor 3 with data]

**Risk Assessment:**
- Technical risk: [LOW/MEDIUM/HIGH]
- User impact: [LOW/MEDIUM/HIGH]
- Development effort: [X weeks]

**Vote Required:** Simple majority (3/5)

**Proposed Timeline:**
- Week 1: Decision
- Week 2-3: Implementation/Migration (if ADOPT/ADAPT)
- Week 4: Testing and validation
```

**Verification:** Council package is concise and decision-ready

---

## Constraints

1. **NO Production Changes:** Do not modify any Assist codebase
2. **Isolated Environment:** All work in `/ganuda/tmp/rjsf-poc`
3. **Time Box:** Complete evaluation in 6 hours or less
4. **Data-Driven:** All recommendations must be backed by measurements

---

## Deliverables

1. Working side-by-side demo
2. Completed findings report at `/ganuda/docs/reports/POC-RJSF-FINDINGS-FEB04-2026.md`
3. Council review package
4. Source code in `/ganuda/tmp/rjsf-poc` (preserved for future reference)

---

## Resources

- RJSF Documentation: https://rjsf-team.github.io/react-jsonschema-form/
- JSON Schema Specification: https://json-schema.org/
- Current YAML wizard: `/ganuda/assist/[locate WizardShell.tsx]`
- SSDI wizard YAML: `/ganuda/assist/[locate ssdi_application.yaml]`
- axe-core: https://github.com/dequelabs/axe-core

---

## Notes

- Cherokee font rendering may require specific font installation
- Test on multiple browsers (Chrome, Firefox, Safari)
- Consider mobile responsiveness in evaluation
- Bundle size matters for Cherokee internet connectivity constraints

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04

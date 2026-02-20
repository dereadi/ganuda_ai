# JR INSTRUCTION: Integrate axe-core Accessibility Testing

**Task ID:** ASSIST-INTEGRATE-AXE-CORE
**Priority:** P1 — Accessibility is not optional
**Assigned To:** Any available Jr
**Created By:** TPM + Council (unanimous 7/7 APPROVE, no conditions)
**Date:** 2026-02-04
**Council Vote:** COUNCIL-VOTE-ASSIST-TECH-STACK-FEB04-2026.md
**Estimated Effort:** 4-6 hours
**Dependencies:** None

---

## MISSION CONTEXT

Accessibility is a moral and legal requirement for VetAssist, SSIDAssist, and TribeAssist. Many veterans have disabilities (visual, motor, cognitive, hearing). Many Cherokee citizens are elders with accessibility needs. Many SSID applicants have disabilities that qualify them for benefits.

We will not build tools that exclude disabled people.

axe-core is the industry-standard automated accessibility testing engine. It checks for WCAG 2.1 compliance violations. The Council approved this with NO CONDITIONS (rare — demonstrates importance).

---

## TECHNICAL CONTEXT

**What is axe-core?**
- Automated accessibility testing engine by Deque Systems
- Tests for WCAG 2.1 Level A, AA, AAA violations
- Integrates with Jest, Cypress, CI/CD pipelines
- MPL 2.0 license (Council-approved)
- Used by: Microsoft, Google, US government agencies

**What is WCAG 2.1?**
- Web Content Accessibility Guidelines
- Levels: A (basic), AA (standard), AAA (enhanced)
- We target: AA compliance minimum
- Categories: Perceivable, Operable, Understandable, Robust

**Why automated testing?**
- Catches 30-50% of accessibility issues automatically
- Prevents regressions in CI/CD
- Faster than manual testing
- Forces developers to think about accessibility

**What it DOESN'T catch:**
- Semantic meaning (is this button labeled clearly?)
- Keyboard workflow logic (can you complete the task?)
- Screen reader user experience (does this make sense?)
- Cognitive accessibility (is this too complex?)

Manual testing is still required. This is the foundation.

---

## SCOPE OF WORK

### Phase 1: Installation & Configuration (1 hour)

**Location:** `/ganuda/assist/core/frontend/`

**Install dependencies:**
```bash
cd /ganuda/assist/core/frontend
npm install --save-dev axe-core jest-axe
```

**Verify versions:**
- axe-core: >=4.10.0
- jest-axe: >=9.0.0

**Create test helper file:**

File: `/ganuda/assist/core/frontend/tests/helpers/a11y-helpers.ts`

```typescript
import { configureAxe } from 'jest-axe';

/**
 * Configured axe instance for WCAG 2.1 AA testing
 *
 * Why AA? It's the legal standard for government services (Section 508).
 * Cherokee Nation is sovereign, but VA integration requires Section 508 compliance.
 */
export const axe = configureAxe({
  rules: {
    // We target WCAG 2.1 Level AA
    // This includes all Level A rules + additional AA rules
    'color-contrast': { enabled: true }, // 4.5:1 for normal text, 3:1 for large
    'landmark-one-main': { enabled: true }, // Accessibility landmark structure
    'region': { enabled: true }, // All content must be in landmarks

    // Cherokee syllabary special case: Non-Latin text may trigger false positives
    // We'll validate Cherokee text manually
    'valid-lang': { enabled: false }, // Cherokee (chr) may not be recognized
  },

  // Test against these standards
  runOnly: {
    type: 'tag',
    values: ['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'],
  },
});

/**
 * Custom matcher for accessibility violations
 * Usage: expect(container).toHaveNoViolations()
 */
export const toHaveNoViolations = (results: any) => {
  const violations = results.violations;

  if (violations.length === 0) {
    return {
      pass: true,
      message: () => 'No accessibility violations found',
    };
  }

  // Format violations for readable error message
  const violationMessages = violations.map((violation: any) => {
    const nodes = violation.nodes.map((node: any) => {
      return `    - ${node.html}\n      ${node.failureSummary}`;
    }).join('\n');

    return `  [${violation.id}] ${violation.help}\n    Impact: ${violation.impact}\n    Nodes:\n${nodes}`;
  }).join('\n\n');

  return {
    pass: false,
    message: () => `Found ${violations.length} accessibility violation(s):\n\n${violationMessages}`,
  };
};

// Extend Jest matchers
expect.extend({ toHaveNoViolations });
```

**Update Jest configuration:**

File: `/ganuda/assist/core/frontend/jest.config.js`

Add to `setupFilesAfterEnv`:
```javascript
module.exports = {
  // ... existing config
  setupFilesAfterEnv: [
    '<rootDir>/tests/helpers/a11y-helpers.ts',
    // ... other setup files
  ],
};
```

---

### Phase 2: Core Component Tests (2-3 hours)

**Create baseline tests for all core components.**

Each component must pass WCAG 2.1 AA with ZERO violations.

#### Test 1: Header Component

File: `/ganuda/assist/core/frontend/tests/components/Header.a11y.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from '../helpers/a11y-helpers';
import Header from '@/components/Header';

describe('Header Accessibility', () => {
  it('should have no WCAG 2.1 AA violations', async () => {
    const { container } = render(
      <Header
        userName="Test Veteran"
        vertical="vetassist"
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have accessible navigation landmarks', async () => {
    const { container } = render(<Header userName="Test Veteran" vertical="vetassist" />);

    // Header should be in <nav> or have role="navigation"
    const nav = container.querySelector('nav');
    expect(nav).toBeInTheDocument();

    // Navigation should have accessible name
    expect(nav).toHaveAttribute('aria-label');
  });

  it('should have accessible user menu button', async () => {
    const { getByRole } = render(<Header userName="Test Veteran" vertical="vetassist" />);

    // User menu trigger should be a button
    const userMenuButton = getByRole('button', { name: /test veteran/i });
    expect(userMenuButton).toBeInTheDocument();

    // Should indicate if menu is expanded
    expect(userMenuButton).toHaveAttribute('aria-expanded');
  });

  it('should support keyboard navigation', async () => {
    const { getByRole } = render(<Header userName="Test Veteran" vertical="vetassist" />);

    const userMenuButton = getByRole('button', { name: /test veteran/i });

    // Button should be keyboard accessible
    userMenuButton.focus();
    expect(document.activeElement).toBe(userMenuButton);
  });
});
```

#### Test 2: WizardShell Component

File: `/ganuda/assist/core/frontend/tests/components/WizardShell.a11y.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from '../helpers/a11y-helpers';
import WizardShell from '@/components/WizardShell';

describe('WizardShell Accessibility', () => {
  const mockSteps = [
    { id: 'personal-info', title: 'Personal Information', status: 'complete' },
    { id: 'service-history', title: 'Service History', status: 'current' },
    { id: 'conditions', title: 'Medical Conditions', status: 'pending' },
  ];

  it('should have no WCAG 2.1 AA violations', async () => {
    const { container } = render(
      <WizardShell
        steps={mockSteps}
        currentStep={1}
      />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have accessible step indicator with aria-current', async () => {
    const { getByRole } = render(
      <WizardShell steps={mockSteps} currentStep={1} />
    );

    // Current step should be marked with aria-current="step"
    const currentStep = getByRole('listitem', { current: 'step' });
    expect(currentStep).toBeInTheDocument();
  });

  it('should announce step transitions to screen readers', async () => {
    const { container, rerender } = render(
      <WizardShell steps={mockSteps} currentStep={1} />
    );

    // Check for live region that announces step changes
    const liveRegion = container.querySelector('[aria-live="polite"]');
    expect(liveRegion).toBeInTheDocument();

    // Move to next step
    rerender(<WizardShell steps={mockSteps} currentStep={2} />);

    // Live region should announce new step
    expect(liveRegion).toHaveTextContent(/medical conditions/i);
  });

  it('should manage focus when transitioning steps', async () => {
    const { rerender } = render(
      <WizardShell steps={mockSteps} currentStep={1} />
    );

    // When step changes, focus should move to step heading
    rerender(<WizardShell steps={mockSteps} currentStep={2} />);

    // Focus should be on the new step's heading
    const heading = document.querySelector('h2');
    expect(document.activeElement).toBe(heading);
  });
});
```

#### Test 3: CalculatorView Component

File: `/ganuda/assist/core/frontend/tests/components/CalculatorView.a11y.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from '../helpers/a11y-helpers';
import CalculatorView from '@/components/CalculatorView';

describe('CalculatorView Accessibility', () => {
  it('should have no WCAG 2.1 AA violations', async () => {
    const { container } = render(
      <CalculatorView calculatorType="disability-rating" />
    );

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have accessible form inputs with labels', async () => {
    const { container } = render(
      <CalculatorView calculatorType="disability-rating" />
    );

    // All inputs must have associated labels
    const inputs = container.querySelectorAll('input');
    inputs.forEach((input) => {
      const id = input.getAttribute('id');
      const label = container.querySelector(`label[for="${id}"]`);
      expect(label).toBeInTheDocument();
    });
  });

  it('should have accessible error messages linked to inputs', async () => {
    const { getByLabelText } = render(
      <CalculatorView calculatorType="disability-rating" />
    );

    // Trigger validation error (submit empty form)
    const ratingInput = getByLabelText(/disability rating/i);

    // Error message should be linked via aria-describedby
    if (ratingInput.getAttribute('aria-invalid') === 'true') {
      const errorId = ratingInput.getAttribute('aria-describedby');
      expect(errorId).toBeTruthy();

      const errorMessage = document.getElementById(errorId!);
      expect(errorMessage).toBeInTheDocument();
    }
  });

  it('should have accessible calculation result region', async () => {
    const { container } = render(
      <CalculatorView calculatorType="disability-rating" />
    );

    // Result should be in live region so screen readers announce it
    const resultRegion = container.querySelector('[role="region"][aria-live]');
    expect(resultRegion).toBeInTheDocument();
    expect(resultRegion).toHaveAttribute('aria-label');
  });
});
```

#### Test 4: ChatPanel Component

File: `/ganuda/assist/core/frontend/tests/components/ChatPanel.a11y.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from '../helpers/a11y-helpers';
import ChatPanel from '@/components/ChatPanel';

describe('ChatPanel Accessibility', () => {
  it('should have no WCAG 2.1 AA violations', async () => {
    const { container } = render(<ChatPanel />);

    const results = await axe(container);
    expect(results).toHaveNoViolations();
  });

  it('should have accessible chat message list', async () => {
    const { container } = render(<ChatPanel />);

    // Message list should be a landmark region
    const messageList = container.querySelector('[role="log"]');
    expect(messageList).toBeInTheDocument();
    expect(messageList).toHaveAttribute('aria-label', 'Chat messages');

    // Should auto-announce new messages
    expect(messageList).toHaveAttribute('aria-live', 'polite');
  });

  it('should have accessible message input with label', async () => {
    const { getByLabelText } = render(<ChatPanel />);

    // Input should have label
    const input = getByLabelText(/message/i);
    expect(input).toBeInTheDocument();
  });

  it('should have accessible send button', async () => {
    const { getByRole } = render(<ChatPanel />);

    // Send button should have accessible name
    const sendButton = getByRole('button', { name: /send/i });
    expect(sendButton).toBeInTheDocument();

    // Should be disabled when input is empty
    expect(sendButton).toHaveAttribute('aria-disabled');
  });

  it('should announce crisis detection alerts', async () => {
    const { container } = render(<ChatPanel />);

    // Crisis alerts should be in assertive live region
    const alertRegion = container.querySelector('[role="alert"]');

    if (alertRegion) {
      expect(alertRegion).toHaveAttribute('aria-live', 'assertive');
    }
  });
});
```

---

### Phase 3: CI/CD Integration (30 minutes)

**Add accessibility tests to CI/CD pipeline.**

File: `/ganuda/assist/core/frontend/.github/workflows/accessibility.yml`

```yaml
name: Accessibility Tests

on:
  pull_request:
    paths:
      - 'frontend/**'
  push:
    branches:
      - main

jobs:
  a11y-tests:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        run: |
          cd frontend
          npm ci

      - name: Run accessibility tests
        run: |
          cd frontend
          npm run test:a11y

      - name: Upload axe results
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: axe-violations
          path: frontend/axe-results.json
```

**Add test script to package.json:**

File: `/ganuda/assist/core/frontend/package.json`

```json
{
  "scripts": {
    "test:a11y": "jest --testMatch='**/*.a11y.test.tsx' --coverage=false"
  }
}
```

---

### Phase 4: Documentation (1 hour)

**Create accessibility checklist for developers.**

File: `/ganuda/assist/core/docs/a11y-checklist.md`

```markdown
# Accessibility Checklist for Assist Platform

**Standard:** WCAG 2.1 Level AA
**Why:** Legal requirement (Section 508), moral requirement (serve all veterans/citizens)
**Enforcement:** axe-core automated tests + manual testing

---

## Required for ALL New Components

Before merging any new component, it MUST:

### 1. Pass axe-core Automated Tests

- [ ] Create `ComponentName.a11y.test.tsx`
- [ ] Run `npm run test:a11y`
- [ ] Zero WCAG 2.1 AA violations
- [ ] Fix all violations before proceeding

**Note:** axe-core catches ~40% of issues. Manual testing still required.

---

### 2. Keyboard Accessibility

- [ ] All interactive elements reachable via Tab key
- [ ] Focus order is logical (follows visual order)
- [ ] Focus indicator is visible (outline or custom style)
- [ ] No keyboard traps (can Tab out of all components)
- [ ] Complex widgets support arrow keys (menus, tabs, sliders)
- [ ] Escape key closes modals/menus
- [ ] Enter/Space activates buttons

**Test:** Unplug your mouse. Can you complete all tasks?

---

### 3. Screen Reader Compatibility

- [ ] All form inputs have `<label>` elements
- [ ] All buttons have accessible names (text or `aria-label`)
- [ ] All images have `alt` text (or `alt=""` if decorative)
- [ ] Headings are hierarchical (h1 → h2 → h3, no skipping)
- [ ] Landmarks used correctly (nav, main, aside, footer)
- [ ] Live regions announce dynamic content (`aria-live`)
- [ ] Error messages linked to inputs (`aria-describedby`)

**Test:** Use NVDA (Windows) or VoiceOver (Mac) to navigate.

---

### 4. Color Contrast

- [ ] Normal text: 4.5:1 contrast minimum
- [ ] Large text (18px+ or 14px+ bold): 3:1 contrast minimum
- [ ] Interactive elements (buttons, links): 3:1 against background
- [ ] Focus indicators: 3:1 against background

**Tool:** Chrome DevTools > Lighthouse > Accessibility

**Cherokee Syllabary Note:** Cherokee characters may appear lighter due to font rendering. Increase font weight if needed.

---

### 5. Forms

- [ ] All inputs have labels
- [ ] Required fields marked with `aria-required="true"` or `required`
- [ ] Validation errors announce to screen readers
- [ ] Error messages are specific ("Enter a valid date" not "Invalid")
- [ ] Form can be completed using only keyboard
- [ ] Multi-step forms indicate progress (`aria-current="step"`)

---

### 6. Modals & Overlays

- [ ] Focus moves to modal when opened
- [ ] Focus trapped in modal (Tab cycles within modal)
- [ ] Escape key closes modal
- [ ] Focus returns to trigger element when closed
- [ ] Modal has `role="dialog"`
- [ ] Modal has `aria-labelledby` pointing to title
- [ ] Background content marked `aria-hidden="true"`

---

### 7. Dynamic Content

- [ ] New content announced via live regions (`aria-live`)
- [ ] Loading states announced ("Loading..." in live region)
- [ ] Success/error messages announced
- [ ] Chat messages use `role="log"` with `aria-live="polite"`
- [ ] Crisis alerts use `role="alert"` (assertive live region)

---

### 8. Cherokee Language Support

- [ ] Cherokee syllabary renders correctly in all components
- [ ] Font size is readable (minimum 16px for Cherokee)
- [ ] Color contrast meets AA standard (syllabary glyphs may be lighter)
- [ ] Screen readers don't mangle Cherokee text (test with NVDA/VoiceOver)
- [ ] Language switching doesn't break keyboard navigation

**Note:** Cherokee (`chr`) may not be recognized by `valid-lang` rule. This is disabled in our axe config.

---

## Testing Process

1. **Automated:** Run `npm run test:a11y` (axe-core)
2. **Keyboard:** Complete all tasks with keyboard only
3. **Screen Reader:** Test with NVDA (Windows) or VoiceOver (Mac)
4. **Color Contrast:** Run Lighthouse audit in Chrome DevTools
5. **Manual:** Check against this checklist

---

## Common Violations & Fixes

### ❌ "Form elements must have labels"
**Fix:** Add `<label for="input-id">` or use `aria-label`

### ❌ "Buttons must have accessible names"
**Fix:** Add text content or `aria-label` to button

### ❌ "Color contrast insufficient"
**Fix:** Darken text color or lighten background color

### ❌ "Heading levels skip"
**Fix:** Don't jump from h2 to h4. Use h3.

### ❌ "No landmark regions"
**Fix:** Wrap content in `<main>`, `<nav>`, `<aside>`, `<footer>`

### ❌ "Keyboard trap detected"
**Fix:** Ensure Tab/Shift+Tab can exit component

---

## Resources

- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [axe-core Rules](https://github.com/dequelabs/axe-core/blob/develop/doc/rule-descriptions.md)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [NVDA Screen Reader](https://www.nvaccess.org/download/) (free)
- [VoiceOver User Guide](https://www.apple.com/voiceover/info/guide/) (built-in Mac)

---

## When in Doubt

**Ask:** "Can a blind veteran using a screen reader complete this task?"
**Ask:** "Can a veteran with motor impairment (no mouse) complete this task?"
**Ask:** "Can an elder Cherokee speaker with low vision read this text?"

If the answer is no, fix it.

---

Accessibility is not a feature. It's a requirement.
```

---

## VERIFICATION CHECKLIST

Before marking this task complete:

- [ ] axe-core and jest-axe installed in `/ganuda/assist/core/frontend/`
- [ ] Test helper created: `tests/helpers/a11y-helpers.ts`
- [ ] Jest configured to load helper
- [ ] Header component test passes with zero violations
- [ ] WizardShell component test passes with zero violations
- [ ] CalculatorView component test passes with zero violations
- [ ] ChatPanel component test passes with zero violations
- [ ] CI/CD workflow created (if GitHub Actions exists)
- [ ] `npm run test:a11y` script added to package.json
- [ ] Accessibility checklist created: `docs/a11y-checklist.md`
- [ ] All tests run and pass: `npm run test:a11y`

---

## SUCCESS CRITERIA

1. **Zero WCAG 2.1 AA violations** in all core components
2. **CI/CD integration** prevents merging code with accessibility violations
3. **Documentation exists** so future developers know the standard
4. **Tests are fast** (entire a11y suite runs in <30 seconds)

---

## NOTES FOR JR EXECUTOR

- **Database:** Not required for this task
- **Server:** Not required for this task (frontend only)
- **Dependencies:** Requires Node.js 20+ and npm
- **Cherokee Context:** Cherokee syllabary may trigger false positives in `valid-lang` rule. This is expected and handled in config.
- **Blocked By:** None
- **Blocks:** ASSIST-INTEGRATE-REACT-USWDS (USWDS components must pass axe-core)

---

## CULTURAL NOTE

This is not performative compliance. Many veterans have disabilities caused by service (vision loss, TBI, mobility impairment). Many Cherokee elders have age-related accessibility needs. Many SSID applicants have disabilities that qualify them for benefits.

We serve disabled people. Our tools must work for them.

Council member Spider: "Accessibility is sovereignty. If we build tools that exclude disabled people, we perpetuate the same exclusion that colonial systems use against us."

---

**Council Verdict:** 7/7 APPROVE — No conditions
**Next Steps After Completion:** Integrate react-uswds (ASSIST-INTEGRATE-REACT-USWDS)

ᏩᏙ (It is finished.)

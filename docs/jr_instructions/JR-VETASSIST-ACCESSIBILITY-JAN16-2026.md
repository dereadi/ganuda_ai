# JR Instruction: VetAssist Accessibility (WCAG 2.1 AA)

## Metadata
```yaml
task_id: vetassist_accessibility
priority: 1
assigned_to: VetAssist Jr.
target: frontend
estimated_effort: medium
compliance: WCAG 2.1 AA
```

## Overview

Veterans have higher rates of disabilities than the general population. VetAssist MUST be accessible to users with visual, motor, cognitive, and hearing impairments.

**Target**: WCAG 2.1 Level AA compliance

## Key Requirements

### 1. Keyboard Navigation

All functionality must be accessible via keyboard:

```tsx
// Every interactive element needs focus styles
<Button
  className="focus:ring-2 focus:ring-blue-500 focus:outline-none"
  onKeyDown={(e) => e.key === 'Enter' && handleClick()}
>

// Skip to main content link (first focusable element)
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:bg-white focus:p-2"
>
  Skip to main content
</a>

// Trap focus in modals
<Dialog onKeyDown={handleTabTrap}>
```

### 2. Screen Reader Support

```tsx
// Semantic HTML
<nav aria-label="Main navigation">
<main id="main-content" role="main">
<aside aria-label="Sidebar">

// ARIA labels for icons/buttons
<button aria-label="Close modal">
  <XIcon aria-hidden="true" />
</button>

// Live regions for dynamic content
<div aria-live="polite" aria-atomic="true">
  {statusMessage}
</div>

// Form labels
<label htmlFor="rating-input">Current VA Rating</label>
<input id="rating-input" type="number" aria-describedby="rating-help" />
<span id="rating-help">Enter a number between 0 and 100</span>
```

### 3. Color & Contrast

```css
/* Minimum contrast ratios */
/* Normal text: 4.5:1 */
/* Large text (18px+ or 14px+ bold): 3:1 */

/* Don't rely on color alone */
.error {
  color: #dc2626;  /* Red */
  border-left: 4px solid #dc2626;  /* Visual indicator */
}
.error::before {
  content: "Error: ";  /* Text indicator */
}

/* Focus indicators must be visible */
:focus {
  outline: 2px solid #2563eb;
  outline-offset: 2px;
}
```

### 4. Text & Readability

```css
/* Minimum font sizes */
body {
  font-size: 16px;
  line-height: 1.5;
}

/* Allow text resize up to 200% without breaking layout */
html {
  font-size: 100%;  /* Respect user preferences */
}

/* Readable line lengths */
.content {
  max-width: 65ch;
}
```

### 5. Forms

```tsx
// Error messages linked to fields
<input
  id="email"
  aria-invalid={errors.email ? "true" : "false"}
  aria-describedby={errors.email ? "email-error" : undefined}
/>
{errors.email && (
  <span id="email-error" role="alert" className="text-red-600">
    {errors.email}
  </span>
)}

// Required field indicators
<label>
  Email <span aria-label="required">*</span>
</label>

// Clear instructions
<fieldset>
  <legend>Service Branch</legend>
  <p id="branch-instructions">Select the branch you served in longest</p>
  <div role="radiogroup" aria-describedby="branch-instructions">
    ...
  </div>
</fieldset>
```

### 6. Images & Media

```tsx
// Alt text for all images
<img src="/va-logo.png" alt="Department of Veterans Affairs logo" />

// Decorative images
<img src="/decoration.png" alt="" aria-hidden="true" />

// Complex images need descriptions
<figure>
  <img src="/rating-chart.png" alt="VA disability rating calculation chart" />
  <figcaption>
    Chart showing how individual ratings combine using VA math.
    <a href="/rating-explanation">Full text explanation</a>
  </figcaption>
</figure>
```

### 7. Motion & Animation

```css
/* Respect reduced motion preferences */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Component Checklist

### Header/Navigation
- [ ] Skip link to main content
- [ ] Mobile menu accessible via keyboard
- [ ] Current page indicated (aria-current="page")
- [ ] Logo has alt text

### Calculator
- [ ] All inputs have labels
- [ ] Slider has aria-valuemin, aria-valuemax, aria-valuenow
- [ ] Results announced to screen readers
- [ ] Error messages linked to fields

### Chat
- [ ] New messages announced (aria-live)
- [ ] Send button has aria-label
- [ ] Chat history navigable
- [ ] Loading states announced

### Forms/Wizards
- [ ] Progress announced ("Step 2 of 5")
- [ ] Errors summarized at top
- [ ] Required fields marked
- [ ] Instructions before form

### Modals
- [ ] Focus trapped inside
- [ ] Escape key closes
- [ ] Focus returns to trigger on close
- [ ] aria-modal="true"

## Testing Tools

```bash
# Automated testing
npm install -D axe-core @axe-core/react

# In tests
import { axe, toHaveNoViolations } from 'jest-axe';
expect.extend(toHaveNoViolations);

test('Calculator page has no accessibility violations', async () => {
  const { container } = render(<CalculatorPage />);
  const results = await axe(container);
  expect(results).toHaveNoViolations();
});
```

### Manual Testing Checklist
- [ ] Navigate entire site with keyboard only
- [ ] Test with screen reader (VoiceOver, NVDA)
- [ ] Zoom to 200% - no horizontal scroll
- [ ] Test with high contrast mode
- [ ] Test with reduced motion enabled

## Implementation Priority

1. **P0 - Critical**
   - Skip link
   - Form labels
   - Focus indicators
   - Alt text

2. **P1 - High**
   - ARIA landmarks
   - Error handling
   - Keyboard navigation
   - Color contrast

3. **P2 - Medium**
   - Live regions
   - Reduced motion
   - Focus management in modals

## Success Criteria

- [ ] Pass axe-core automated tests
- [ ] Keyboard-only navigation works
- [ ] Screen reader can complete all tasks
- [ ] 4.5:1 contrast ratio on all text
- [ ] No WCAG 2.1 AA violations

---

*Cherokee AI Federation - For the Seven Generations*
*"Accessible to all who served."*

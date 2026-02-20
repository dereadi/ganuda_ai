# JR INSTRUCTION: Adopt react-uswds Government UI Components

**Task ID:** ASSIST-INTEGRATE-REACT-USWDS
**Priority:** P1 — Government-standard accessible components
**Assigned To:** Any available Jr
**Created By:** TPM + Council (7/7 APPROVE with conditions)
**Date:** 2026-02-04
**Council Vote:** COUNCIL-VOTE-ASSIST-TECH-STACK-FEB04-2026.md
**Estimated Effort:** 6-8 hours
**Dependencies:** ASSIST-INTEGRATE-AXE-CORE (must complete axe-core integration first)

---

## MISSION CONTEXT

VetAssist interfaces with VA systems. SSIDAssist interfaces with Social Security Administration. TribeAssist serves Cherokee Nation citizens.

Using the US Web Design System (USWDS) gives us:
1. **Legitimacy** — Government agencies recognize these patterns
2. **Accessibility** — WCAG 2.1 AA compliance built-in
3. **Consistency** — Veterans are familiar with these UI patterns from VA.gov
4. **Speed** — Don't reinvent accessible components from scratch

**Critical Council Condition (Spider):** "US government branding may feel colonial for Cherokee Nation interface. MUST be theme-able. Cherokee Nation interface should not look like a federal website."

We will create a theme abstraction layer. Each vertical (VetAssist, SSIDAssist, TribeAssist) gets its own visual identity while sharing the same accessible component foundation.

---

## TECHNICAL CONTEXT

**What is USWDS?**
- Design system for US government websites
- Maintained by GSA (General Services Administration)
- Used by: VA.gov, SSA.gov, IRS.gov, many federal agencies
- Accessibility: WCAG 2.1 AA compliant by default

**What is react-uswds?**
- React component library implementing USWDS
- Maintained by TrussWorks (government contractor, civic tech focus)
- 216 stars (small community — Council noted this risk)
- OSS license, no phone-home behavior

**Council Conditions:**
1. Must be theme-able for each vertical
2. Fork and archive repo (longevity insurance if TrussWorks abandons)
3. Contribute improvements upstream (community health investment)

---

## SCOPE OF WORK

### Phase 1: Installation & Theme Architecture (2 hours)

**Location:** `/ganuda/assist/core/frontend/`

**Install dependencies:**
```bash
cd /ganuda/assist/core/frontend
npm install @trussworks/react-uswds uswds
```

**Verify versions:**
- @trussworks/react-uswds: >=7.0.0
- uswds: >=3.0.0

**Fork repository for longevity insurance:**
```bash
# Council condition: Fork and archive at integration time
# This ensures we can maintain if TrussWorks abandons

# Create fork on GitHub/GitLab (manual step)
# Clone fork to /ganuda/assist/core/vendor/react-uswds-fork
# Tag current version: git tag integration-baseline-2026-02-04
```

**Create theme architecture:**

File: `/ganuda/assist/core/frontend/src/themes/base-theme.ts`

```typescript
/**
 * Base theme configuration
 *
 * All vertical-specific themes extend this base.
 * Defines theme structure and default values.
 */

export interface AssistTheme {
  name: string;
  colors: {
    primary: string;
    primaryDark: string;
    primaryLight: string;
    secondary: string;
    accent: string;
    background: string;
    surface: string;
    text: string;
    textSecondary: string;
    error: string;
    warning: string;
    success: string;
    info: string;
  };
  typography: {
    fontFamily: string;
    fontFamilyCherokee?: string; // Special handling for Cherokee syllabary
    fontSizeBase: string;
    fontSizeHeading: {
      h1: string;
      h2: string;
      h3: string;
      h4: string;
    };
  };
  spacing: {
    unit: number; // Base spacing unit (px)
  };
  branding: {
    logo: string; // Path to logo image
    name: string; // App name (e.g., "VetAssist", "Cherokee Nation Assistance")
    tagline: string; // Optional tagline
  };
}

/**
 * Default USWDS-aligned theme
 * Used as fallback if vertical theme not found
 */
export const baseTheme: AssistTheme = {
  name: 'base',
  colors: {
    primary: '#005ea2', // USWDS blue-60v
    primaryDark: '#0b4778', // USWDS blue-70v
    primaryLight: '#2378c3', // USWDS blue-50v
    secondary: '#54278f', // USWDS violet-70v
    accent: '#e52207', // USWDS red-60v
    background: '#f0f0f0', // USWDS gray-5
    surface: '#ffffff', // White
    text: '#1b1b1b', // USWDS gray-90
    textSecondary: '#5c5c5c', // USWDS gray-60
    error: '#d54309', // USWDS red-warm-60v
    warning: '#dd5900', // USWDS orange-60v
    success: '#00a91c', // USWDS green-cool-50v
    info: '#2378c3', // USWDS blue-50v
  },
  typography: {
    fontFamily: '"Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontSizeBase: '16px',
    fontSizeHeading: {
      h1: '2.5rem',
      h2: '2rem',
      h3: '1.5rem',
      h4: '1.25rem',
    },
  },
  spacing: {
    unit: 8, // 8px grid system (USWDS uses 8px base unit)
  },
  branding: {
    logo: '/assets/logos/assist-logo.svg',
    name: 'Assist',
    tagline: '',
  },
};
```

**Create VetAssist theme:**

File: `/ganuda/assist/core/frontend/src/themes/vetassist-theme.ts`

```typescript
import { AssistTheme, baseTheme } from './base-theme';

/**
 * VetAssist Theme
 *
 * Visual identity: Government blues/grays (familiar to veterans from VA.gov)
 * Target audience: US military veterans navigating VA benefits
 * Accessibility: High contrast for veterans with vision impairment (common TBI symptom)
 */
export const vetAssistTheme: AssistTheme = {
  ...baseTheme,
  name: 'vetassist',
  colors: {
    ...baseTheme.colors,
    primary: '#003366', // Navy blue (military association)
    primaryDark: '#002244',
    primaryLight: '#004488',
    secondary: '#112e51', // Dark blue (VA.gov uses this)
    accent: '#cd2026', // Red (veteran service flag)
  },
  branding: {
    logo: '/assets/logos/vetassist-logo.svg',
    name: 'VetAssist',
    tagline: 'Navigate VA benefits with confidence',
  },
};
```

**Create SSIDAssist theme:**

File: `/ganuda/assist/core/frontend/src/themes/ssidassist-theme.ts`

```typescript
import { AssistTheme, baseTheme } from './base-theme';

/**
 * SSIDAssist Theme
 *
 * Visual identity: Greens (financial stability, growth, health)
 * Target audience: Disabled individuals applying for Social Security disability
 * Accessibility: Clear contrast, calming colors (reduce anxiety during stressful process)
 */
export const ssidAssistTheme: AssistTheme = {
  ...baseTheme,
  name: 'ssidassist',
  colors: {
    ...baseTheme.colors,
    primary: '#2e8540', // Green (financial stability)
    primaryDark: '#1f5c2e',
    primaryLight: '#4aa564',
    secondary: '#046b99', // Teal (SSA.gov uses blue-green palette)
    accent: '#e31c3d', // Red accent for important actions
  },
  branding: {
    logo: '/assets/logos/ssidassist-logo.svg',
    name: 'SSIDAssist',
    tagline: 'Social Security disability guidance',
  },
};
```

**Create TribeAssist theme:**

File: `/ganuda/assist/core/frontend/src/themes/tribeassist-theme.ts`

```typescript
import { AssistTheme, baseTheme } from './base-theme';

/**
 * TribeAssist Theme
 *
 * Visual identity: Earth tones, Cherokee red (cultural identity, not colonial government)
 * Target audience: Cherokee Nation citizens
 * Cherokee syllabary: Requires special font handling
 *
 * CRITICAL (Council condition from Spider):
 * "Cherokee Nation interface should not look like a federal website."
 * This theme deliberately diverges from USWDS government aesthetic.
 * We use USWDS components for accessibility, but override visual identity.
 */
export const tribeAssistTheme: AssistTheme = {
  ...baseTheme,
  name: 'tribeassist',
  colors: {
    ...baseTheme.colors,
    primary: '#8b2635', // Cherokee red (cultural significance)
    primaryDark: '#6b1d28',
    primaryLight: '#a53d4a',
    secondary: '#5a4a3a', // Earth brown
    accent: '#d4a76a', // Gold/tan accent
    background: '#faf8f5', // Warm off-white (not sterile government white)
    surface: '#ffffff',
    text: '#2d2d2d', // Warm black
    textSecondary: '#6b5d52', // Warm gray
  },
  typography: {
    fontFamily: '"Public Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontFamilyCherokee: '"Aboriginal Sans", "Gadugi", sans-serif', // Cherokee syllabary fonts
    fontSizeBase: '16px',
    fontSizeHeading: {
      h1: '2.5rem',
      h2: '2rem',
      h3: '1.5rem',
      h4: '1.25rem',
    },
  },
  branding: {
    logo: '/assets/logos/cherokee-nation-logo.svg',
    name: 'ᏣᎳᎩᎯ ᎠᏰᎵ ᎠᏂᏣᎳᎩ', // "Cherokee Nation Citizens" in syllabary
    tagline: 'Serving the Cherokee people',
  },
};
```

**Create theme provider:**

File: `/ganuda/assist/core/frontend/src/themes/ThemeProvider.tsx`

```typescript
import React, { createContext, useContext, useMemo } from 'react';
import { AssistTheme } from './base-theme';
import { vetAssistTheme } from './vetassist-theme';
import { ssidAssistTheme } from './ssidassist-theme';
import { tribeAssistTheme } from './tribeassist-theme';

type VerticalType = 'vetassist' | 'ssidassist' | 'tribeassist';

interface ThemeContextValue {
  theme: AssistTheme;
  vertical: VerticalType;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const themes: Record<VerticalType, AssistTheme> = {
  vetassist: vetAssistTheme,
  ssidassist: ssidAssistTheme,
  tribeassist: tribeAssistTheme,
};

interface ThemeProviderProps {
  vertical: VerticalType;
  children: React.ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ vertical, children }) => {
  const theme = themes[vertical];

  // Inject CSS custom properties for theme
  useMemo(() => {
    const root = document.documentElement;

    // Colors
    Object.entries(theme.colors).forEach(([key, value]) => {
      root.style.setProperty(`--theme-color-${key}`, value);
    });

    // Typography
    root.style.setProperty('--theme-font-family', theme.typography.fontFamily);
    if (theme.typography.fontFamilyCherokee) {
      root.style.setProperty('--theme-font-family-cherokee', theme.typography.fontFamilyCherokee);
    }
    root.style.setProperty('--theme-font-size-base', theme.typography.fontSizeBase);

    // Spacing
    root.style.setProperty('--theme-spacing-unit', `${theme.spacing.unit}px`);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, vertical }}>
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = (): ThemeContextValue => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
};
```

**Create USWDS theme overrides:**

File: `/ganuda/assist/core/frontend/src/themes/uswds-overrides.scss`

```scss
/**
 * USWDS Theme Overrides
 *
 * This file overrides USWDS default styles with our theme variables.
 * Imported after USWDS styles to take precedence.
 */

// Use CSS custom properties from ThemeProvider
:root {
  // Override USWDS color tokens with our theme colors
  --usa-primary: var(--theme-color-primary);
  --usa-primary-dark: var(--theme-color-primaryDark);
  --usa-primary-light: var(--theme-color-primaryLight);
  --usa-secondary: var(--theme-color-secondary);
  --usa-accent: var(--theme-color-accent);
  --usa-error: var(--theme-color-error);
  --usa-warning: var(--theme-color-warning);
  --usa-success: var(--theme-color-success);
  --usa-info: var(--theme-color-info);

  // Typography
  --usa-font-family: var(--theme-font-family);
  --usa-font-size-base: var(--theme-font-size-base);
}

// Cherokee syllabary special handling
[lang="chr"],
.cherokee-text {
  font-family: var(--theme-font-family-cherokee, var(--theme-font-family));
  font-weight: 500; // Cherokee glyphs are lighter, increase weight
}

// TribeAssist specific: Override government aesthetic
[data-vertical="tribeassist"] {
  // Remove rigid government borders
  .usa-button {
    border-radius: 4px; // Add slight rounding (USWDS uses sharp corners)
  }

  // Warmer shadows (not stark government gray)
  .usa-card {
    box-shadow: 0 2px 8px rgba(139, 38, 53, 0.1); // Cherokee red tint
  }
}
```

---

### Phase 2: Component Migration (3-4 hours)

**Map our custom components to USWDS equivalents.**

#### Migration 1: Header Component

File: `/ganuda/assist/core/frontend/src/components/Header.tsx`

**Before (custom implementation):**
```typescript
// Custom header with manual accessibility
const Header = ({ userName, vertical }) => {
  return (
    <header className="custom-header">
      <div className="logo">
        <img src="/logo.svg" alt="Logo" />
      </div>
      <nav>
        <button onClick={handleMenuToggle}>
          {userName}
        </button>
      </nav>
    </header>
  );
};
```

**After (USWDS implementation):**
```typescript
import { Header as USWDSHeader, NavMenuButton, PrimaryNav } from '@trussworks/react-uswds';
import { useTheme } from '../themes/ThemeProvider';

const Header = ({ userName, vertical }) => {
  const { theme } = useTheme();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  return (
    <USWDSHeader basic>
      <div className="usa-nav-container">
        <div className="usa-navbar">
          <div className="usa-logo" id="basic-logo">
            <img
              src={theme.branding.logo}
              alt={theme.branding.name}
              style={{ height: '3rem' }}
            />
          </div>
          <NavMenuButton
            onClick={() => setMobileNavOpen(!mobileNavOpen)}
            label="Menu"
          />
        </div>
        <PrimaryNav
          items={[
            { text: 'Dashboard', href: '/dashboard' },
            { text: 'Wizards', href: '/wizards' },
            { text: 'Calculators', href: '/calculators' },
          ]}
          mobileExpanded={mobileNavOpen}
          onToggleMobileNav={() => setMobileNavOpen(!mobileNavOpen)}
        >
          {/* User menu */}
          <button className="usa-button usa-button--secondary">
            {userName}
          </button>
        </PrimaryNav>
      </div>
    </USWDSHeader>
  );
};

export default Header;
```

**Accessibility gains:**
- USWDS Header has correct landmark structure (`<header>`, `<nav>`)
- Mobile navigation is keyboard accessible
- Focus management handled automatically
- ARIA attributes included

#### Migration 2: Form Components

File: `/ganuda/assist/core/frontend/src/components/forms/FormField.tsx`

**Before (custom implementation):**
```typescript
const FormField = ({ label, error, ...props }) => {
  return (
    <div className="form-field">
      <label>{label}</label>
      <input {...props} />
      {error && <span className="error">{error}</span>}
    </div>
  );
};
```

**After (USWDS implementation):**
```typescript
import { FormGroup, Label, TextInput, ErrorMessage } from '@trussworks/react-uswds';

const FormField = ({ label, error, id, ...props }) => {
  return (
    <FormGroup error={!!error}>
      <Label htmlFor={id} error={!!error}>
        {label}
      </Label>
      <TextInput
        id={id}
        {...props}
        validationStatus={error ? 'error' : undefined}
      />
      {error && <ErrorMessage id={`${id}-error`}>{error}</ErrorMessage>}
    </FormGroup>
  );
};

export default FormField;
```

**Accessibility gains:**
- Error message linked to input via `aria-describedby` (USWDS does this automatically)
- `aria-invalid` set when error exists
- Error styling meets color contrast requirements
- Label properly associated with input

#### Migration 3: Button Component

File: `/ganuda/assist/core/frontend/src/components/Button.tsx`

**Before (custom implementation):**
```typescript
const Button = ({ children, variant, ...props }) => {
  return (
    <button className={`btn btn-${variant}`} {...props}>
      {children}
    </button>
  );
};
```

**After (USWDS implementation):**
```typescript
import { Button as USWDSButton } from '@trussworks/react-uswds';

const Button = ({ children, variant = 'primary', ...props }) => {
  // Map our variant names to USWDS variants
  const uswdsVariant = {
    primary: undefined, // default
    secondary: 'secondary',
    danger: 'secondary', // USWDS doesn't have danger, we'll add custom style
    outline: 'outline',
  }[variant];

  return (
    <USWDSButton
      type="button"
      {...(uswdsVariant && { secondary: variant === 'secondary' })}
      {...(variant === 'outline' && { outline: true })}
      {...props}
      className={variant === 'danger' ? 'usa-button--danger' : ''}
    >
      {children}
    </USWDSButton>
  );
};

export default Button;
```

Add danger button style:

File: `/ganuda/assist/core/frontend/src/styles/button-extensions.scss`

```scss
// Extend USWDS button with danger variant
.usa-button--danger {
  background-color: var(--theme-color-error);

  &:hover {
    background-color: var(--theme-color-error);
    filter: brightness(0.9);
  }
}
```

#### Migration 4: Alert Component

File: `/ganuda/assist/core/frontend/src/components/Alert.tsx`

**Before (custom implementation):**
```typescript
const Alert = ({ type, message }) => {
  return (
    <div className={`alert alert-${type}`}>
      {message}
    </div>
  );
};
```

**After (USWDS implementation):**
```typescript
import { Alert as USWDSAlert } from '@trussworks/react-uswds';

const Alert = ({ type, message, children }) => {
  return (
    <USWDSAlert
      type={type} // 'success' | 'warning' | 'error' | 'info'
      headingLevel="h4"
      slim
    >
      {message || children}
    </USWDSAlert>
  );
};

export default Alert;
```

**Accessibility gains:**
- USWDS Alert has `role="region"` with `aria-label`
- Heading provides structure for screen readers
- Color + icon + text (triple encoding, not just color)

#### Migration 5: Wizard Progress Indicator

File: `/ganuda/assist/core/frontend/src/components/WizardProgress.tsx`

**Before (custom implementation):**
```typescript
const WizardProgress = ({ steps, currentStep }) => {
  return (
    <div className="wizard-progress">
      {steps.map((step, index) => (
        <div key={step.id} className={index === currentStep ? 'active' : ''}>
          {step.title}
        </div>
      ))}
    </div>
  );
};
```

**After (USWDS implementation):**
```typescript
import { StepIndicator, StepIndicatorStep } from '@trussworks/react-uswds';

const WizardProgress = ({ steps, currentStep }) => {
  return (
    <StepIndicator
      counters="default"
      headingLevel="h4"
    >
      {steps.map((step, index) => (
        <StepIndicatorStep
          key={step.id}
          label={step.title}
          status={
            index < currentStep ? 'complete' :
            index === currentStep ? 'current' :
            'incomplete'
          }
        />
      ))}
    </StepIndicator>
  );
};

export default WizardProgress;
```

**Accessibility gains:**
- `aria-current="step"` on current step
- Status communicated via text + visual indicator
- Screen reader announces step changes

---

### Phase 3: Cherokee Language Support (1 hour)

**Test Cherokee syllabary rendering in all USWDS components.**

File: `/ganuda/assist/core/frontend/tests/i18n/cherokee-rendering.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { ThemeProvider } from '@/themes/ThemeProvider';
import { Header, Button, Alert } from '@/components';

describe('Cherokee Syllabary Rendering', () => {
  const cherokeeText = 'ᏣᎳᎩᎯ ᎠᏰᎵ'; // "Cherokee people"

  it('should render Cherokee text in Header', () => {
    const { getByText } = render(
      <ThemeProvider vertical="tribeassist">
        <Header userName={cherokeeText} vertical="tribeassist" />
      </ThemeProvider>
    );

    const element = getByText(cherokeeText);
    expect(element).toBeInTheDocument();

    // Check font family
    const styles = window.getComputedStyle(element);
    expect(styles.fontFamily).toContain('Aboriginal Sans');
  });

  it('should render Cherokee text in Button', () => {
    const { getByRole } = render(
      <ThemeProvider vertical="tribeassist">
        <Button>{cherokeeText}</Button>
      </ThemeProvider>
    );

    const button = getByRole('button', { name: cherokeeText });
    expect(button).toBeInTheDocument();
  });

  it('should render Cherokee text in Alert', () => {
    const { getByText } = render(
      <ThemeProvider vertical="tribeassist">
        <Alert type="info" message={cherokeeText} />
      </ThemeProvider>
    );

    expect(getByText(cherokeeText)).toBeInTheDocument();
  });

  it('should have sufficient color contrast for Cherokee text', () => {
    const { container } = render(
      <ThemeProvider vertical="tribeassist">
        <div lang="chr">{cherokeeText}</div>
      </ThemeProvider>
    );

    // Cherokee glyphs may be lighter due to font rendering
    // Font weight should be increased to compensate
    const element = container.querySelector('[lang="chr"]');
    const styles = window.getComputedStyle(element!);
    expect(parseInt(styles.fontWeight)).toBeGreaterThanOrEqual(500);
  });
});
```

---

### Phase 4: Accessibility Validation (1 hour)

**Run axe-core tests on all migrated components.**

File: `/ganuda/assist/core/frontend/tests/integration/uswds-accessibility.test.tsx`

```typescript
import { render } from '@testing-library/react';
import { axe, toHaveNoViolations } from '../helpers/a11y-helpers';
import { ThemeProvider } from '@/themes/ThemeProvider';
import { Header, Button, Alert, FormField, WizardProgress } from '@/components';

describe('USWDS Components Accessibility', () => {
  const verticals = ['vetassist', 'ssidassist', 'tribeassist'] as const;

  verticals.forEach((vertical) => {
    describe(`${vertical} theme`, () => {
      it('Header should have no violations', async () => {
        const { container } = render(
          <ThemeProvider vertical={vertical}>
            <Header userName="Test User" vertical={vertical} />
          </ThemeProvider>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
      });

      it('Button should have no violations', async () => {
        const { container } = render(
          <ThemeProvider vertical={vertical}>
            <Button>Click Me</Button>
          </ThemeProvider>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
      });

      it('Alert should have no violations', async () => {
        const { container } = render(
          <ThemeProvider vertical={vertical}>
            <Alert type="info" message="Test alert" />
          </ThemeProvider>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
      });

      it('FormField should have no violations', async () => {
        const { container } = render(
          <ThemeProvider vertical={vertical}>
            <FormField
              id="test-input"
              label="Test Field"
              error="Test error"
            />
          </ThemeProvider>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
      });
    });
  });
});
```

---

### Phase 5: Documentation (1 hour)

**Update component documentation with USWDS patterns.**

File: `/ganuda/assist/core/docs/components/README.md`

```markdown
# Component Library - USWDS Implementation

All components are built on @trussworks/react-uswds for:
- WCAG 2.1 AA accessibility compliance
- Government-standard UI patterns
- Cross-vertical theming support

## Theming

Each vertical has its own theme:

### VetAssist
- **Colors:** Navy blue, government grays
- **Identity:** Familiar to veterans from VA.gov
- **Logo:** VetAssist eagle emblem

### SSIDAssist
- **Colors:** Green, teal
- **Identity:** Financial stability, health
- **Logo:** SSIDAssist shield

### TribeAssist
- **Colors:** Cherokee red, earth tones
- **Identity:** Cultural (NOT colonial government aesthetic)
- **Logo:** Cherokee Nation seal
- **Special:** Cherokee syllabary font support

## Usage

Wrap your app in ThemeProvider:

```typescript
import { ThemeProvider } from '@/themes/ThemeProvider';

const App = () => {
  const vertical = 'vetassist'; // or 'ssidassist' or 'tribeassist'

  return (
    <ThemeProvider vertical={vertical}>
      {/* Your app */}
    </ThemeProvider>
  );
};
```

## Components

All components are theme-aware and WCAG 2.1 AA compliant.

### Header
```typescript
import { Header } from '@/components';

<Header userName="John Veteran" vertical="vetassist" />
```

### Button
```typescript
import { Button } from '@/components';

<Button variant="primary">Submit</Button>
<Button variant="secondary">Cancel</Button>
<Button variant="danger">Delete</Button>
```

### Form Field
```typescript
import { FormField } from '@/components';

<FormField
  id="name"
  label="Full Name"
  error={errors.name}
  required
/>
```

### Alert
```typescript
import { Alert } from '@/components';

<Alert type="success" message="Claim submitted!" />
<Alert type="error">Application rejected</Alert>
```

### Wizard Progress
```typescript
import { WizardProgress } from '@/components';

<WizardProgress
  steps={[
    { id: 'info', title: 'Personal Info' },
    { id: 'service', title: 'Service History' },
  ]}
  currentStep={0}
/>
```

## Cherokee Language Support

Use `lang="chr"` attribute for Cherokee text:

```typescript
<p lang="chr">ᏣᎳᎩᎯ ᎠᏰᎵ</p>
```

This applies correct font (Aboriginal Sans) and weight (500+).

## Accessibility Testing

All components must pass axe-core:

```bash
npm run test:a11y
```

## Escape Hatch: If USWDS Doesn't Work

Council condition: "If we can't theme it, we wrap it."

If a USWDS component cannot be themed for a vertical:
1. Create wrapper component
2. Override styles with CSS custom properties
3. If still can't theme: fork USWDS component and maintain locally

Do NOT remove USWDS. Accessibility is not negotiable.
```

---

## VERIFICATION CHECKLIST

Before marking this task complete:

- [ ] @trussworks/react-uswds installed
- [ ] USWDS repository forked and archived at /ganuda/assist/core/vendor/react-uswds-fork
- [ ] Theme architecture created (base, VetAssist, SSIDAssist, TribeAssist)
- [ ] ThemeProvider implemented
- [ ] USWDS overrides stylesheet created
- [ ] Header component migrated to USWDS
- [ ] Form components migrated to USWDS
- [ ] Button component migrated to USWDS
- [ ] Alert component migrated to USWDS
- [ ] Wizard progress component migrated to USWDS
- [ ] Cherokee syllabary rendering tested
- [ ] All themes pass axe-core tests (zero violations)
- [ ] Component documentation updated

---

## SUCCESS CRITERIA

1. **All three themes render correctly** (VetAssist, SSIDAssist, TribeAssist)
2. **Cherokee syllabary displays properly** in TribeAssist theme
3. **Zero WCAG 2.1 AA violations** in all themed components
4. **TribeAssist does NOT look like a federal website** (Council condition satisfied)
5. **Repository forked** for longevity insurance

---

## NOTES FOR JR EXECUTOR

- **Database:** Not required
- **Server:** Not required (frontend only)
- **Dependencies:** Requires ASSIST-INTEGRATE-AXE-CORE completion (axe-core tests)
- **Cherokee Context:** Aboriginal Sans font must be available (web font or system font)
- **Council Condition:** Spider specifically called out theme-ability. Verify TribeAssist looks culturally appropriate.
- **Blocked By:** ASSIST-INTEGRATE-AXE-CORE
- **Blocks:** Future component development (all new components must use USWDS)

---

## CULTURAL NOTE

Council member Spider: "US government branding may feel colonial for Cherokee Nation interface."

This is not aesthetic preference. This is data sovereignty. Cherokee Nation is a sovereign nation. Federal website aesthetic implies federal control. TribeAssist serves Cherokee citizens, not US government beneficiaries.

The earth tones, Cherokee red, and syllabary are deliberate assertions of sovereignty.

VetAssist uses government aesthetic because veterans are interfacing with a federal system (VA). Context matters.

---

**Council Verdict:** 7/7 APPROVE — With conditions (theme-ability, fork, upstream contribution)
**Next Steps After Completion:** Begin YAML wizard migration to RJSF (ASSIST-INTEGRATE-RJSF-POC)

ᏩᏙ (It is finished.)

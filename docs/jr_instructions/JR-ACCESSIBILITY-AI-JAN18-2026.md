# JR Instruction: Accessibility AI for VetAssist

## Metadata
```yaml
task_id: accessibility_ai
priority: 2
assigned_to: it_triad_jr
estimated_effort: high
category: accessibility
council_vote: 4fdd4018e18f99b4
council_priority: 2 of 6
brd_requirement: F-013 (MUST)
```

## Executive Summary

Implement accessibility features ensuring no veteran is left behind. Council Priority #2: "Disabled veterans deserve equal access to claim assistance."

## Background

### BRD Requirements (Section 6.6)
| Category | Requirements |
|----------|--------------|
| Visual | High contrast mode, large text option, color not sole indicator |
| Motor | Full keyboard navigation, large click targets (44px), no time limits |
| Auditory | Captions for any video content |
| Cognitive | Plain language, progress indicators, auto-save, confirmations |
| Screen Readers | ARIA labels, semantic HTML, skip navigation |

### Target: WCAG 2.1 AA Compliance
- BRD Success Criteria: Lighthouse score >90%
- Current State: Unknown (needs audit)

## Research Sources

1. **AI-Powered Assistive Tech for Visual Impairment** (arXiv:2503.15494)
   - URL: https://arxiv.org/html/2503.15494v1
   - Object recognition, NLP text-to-speech advances

2. **Voice-based AI for Inclusivity** (PMC)
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11246435/
   - Co-design approach for voice + web augmentation

3. **AI Assistive Tech in Healthcare** (PMC 2025)
   - URL: https://pmc.ncbi.nlm.nih.gov/articles/PMC11898476/
   - 19 review studies on autonomy enhancement

## Implementation Phases

### Phase 1: WCAG Audit
**BACKEND LOCATION: /ganuda/vetassist/frontend**

**CREATE FILE: accessibility-audit.md**

Run Lighthouse accessibility audit:
```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run audit on VetAssist pages
lighthouse http://localhost:3000 --only-categories=accessibility --output=json --output-path=./audit-results.json

# Generate HTML report
lighthouse http://localhost:3000 --only-categories=accessibility --output=html --output-path=./accessibility-audit.html
```

### Phase 2: Voice Input for Notes
**CREATE FILE: /ganuda/vetassist/frontend/src/components/VoiceInput.tsx**

```typescript
/**
 * VoiceInput Component - Enables voice dictation for veteran notes
 * Uses Web Speech API with fallback to Whisper API
 * Cherokee AI Federation - No Veteran Left Behind
 */

import React, { useState, useEffect, useCallback } from 'react';

interface VoiceInputProps {
  onTranscript: (text: string) => void;
  placeholder?: string;
  disabled?: boolean;
}

export const VoiceInput: React.FC<VoiceInputProps> = ({
  onTranscript,
  placeholder = "Click microphone or press Alt+V to start voice input",
  disabled = false
}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Check for Web Speech API support
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;

  useEffect(() => {
    if (!recognition) {
      setError('Voice input not supported in this browser. Try Chrome or Edge.');
      return;
    }

    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onresult = (event: SpeechRecognitionEvent) => {
      let finalTranscript = '';
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (result.isFinal) {
          finalTranscript += result[0].transcript;
        }
      }
      if (finalTranscript) {
        setTranscript(prev => prev + ' ' + finalTranscript);
        onTranscript(finalTranscript);
      }
    };

    recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
      setError(`Voice error: ${event.error}`);
      setIsListening(false);
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    // Keyboard shortcut: Alt+V
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.altKey && e.key === 'v') {
        e.preventDefault();
        toggleListening();
      }
    };
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      recognition.stop();
    };
  }, []);

  const toggleListening = useCallback(() => {
    if (!recognition) return;

    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
      setError(null);
    }
  }, [isListening, recognition]);

  return (
    <div className="voice-input" role="region" aria-label="Voice input controls">
      <button
        onClick={toggleListening}
        disabled={disabled || !recognition}
        className={`voice-button ${isListening ? 'listening' : ''}`}
        aria-pressed={isListening}
        aria-label={isListening ? 'Stop voice input' : 'Start voice input'}
        title="Voice input (Alt+V)"
      >
        {isListening ? '🔴 Recording...' : '🎤 Voice Input'}
      </button>

      {error && (
        <div role="alert" className="voice-error" aria-live="polite">
          {error}
        </div>
      )}

      <p className="voice-hint" aria-hidden="true">
        {placeholder}
      </p>
    </div>
  );
};

export default VoiceInput;
```

### Phase 3: Screen Reader Optimization
**MODIFY FILE: /ganuda/vetassist/frontend/src/app/layout.tsx**

Add skip navigation and ARIA landmarks:
```typescript
// Add to layout
<a href="#main-content" className="skip-link">
  Skip to main content
</a>

<header role="banner" aria-label="VetAssist header">
  {/* Navigation */}
</header>

<nav role="navigation" aria-label="Main navigation">
  {/* Nav items */}
</nav>

<main id="main-content" role="main" aria-label="Main content">
  {children}
</main>

<footer role="contentinfo" aria-label="Site footer">
  {/* Footer */}
</footer>
```

### Phase 4: High Contrast Mode
**CREATE FILE: /ganuda/vetassist/frontend/src/styles/high-contrast.css**

```css
/* High Contrast Mode for Visual Accessibility */
/* Activated via prefers-contrast or user toggle */

@media (prefers-contrast: more) {
  :root {
    --bg-primary: #000000;
    --bg-secondary: #1a1a1a;
    --text-primary: #ffffff;
    --text-secondary: #ffff00;
    --accent: #00ffff;
    --error: #ff6b6b;
    --success: #00ff00;
    --border: #ffffff;
  }
}

.high-contrast {
  --bg-primary: #000000;
  --bg-secondary: #1a1a1a;
  --text-primary: #ffffff;
  --text-secondary: #ffff00;
  --accent: #00ffff;
  --error: #ff6b6b;
  --success: #00ff00;
  --border: #ffffff;
}

/* Ensure minimum 4.5:1 contrast ratio */
.high-contrast button,
.high-contrast a {
  border: 2px solid var(--border);
  outline-offset: 2px;
}

/* Large click targets (44px minimum) */
.high-contrast button,
.high-contrast a,
.high-contrast input,
.high-contrast select {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 16px;
}

/* Focus indicators */
.high-contrast :focus {
  outline: 3px solid var(--accent);
  outline-offset: 2px;
}

/* Skip link */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--bg-primary);
  color: var(--text-primary);
  padding: 8px 16px;
  z-index: 100;
}

.skip-link:focus {
  top: 0;
}
```

### Phase 5: Keyboard Navigation
**CREATE FILE: /ganuda/vetassist/frontend/src/hooks/useKeyboardNav.ts**

```typescript
/**
 * Keyboard Navigation Hook
 * Ensures full keyboard accessibility for motor-impaired veterans
 */

import { useEffect, useCallback } from 'react';

interface KeyboardNavOptions {
  onEscape?: () => void;
  onEnter?: () => void;
  trapFocus?: boolean;
  containerRef?: React.RefObject<HTMLElement>;
}

export function useKeyboardNav(options: KeyboardNavOptions = {}) {
  const { onEscape, onEnter, trapFocus, containerRef } = options;

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    switch (e.key) {
      case 'Escape':
        onEscape?.();
        break;
      case 'Enter':
        if (!['INPUT', 'TEXTAREA', 'BUTTON'].includes((e.target as HTMLElement).tagName)) {
          onEnter?.();
        }
        break;
      case 'Tab':
        if (trapFocus && containerRef?.current) {
          const focusable = containerRef.current.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
          );
          const first = focusable[0] as HTMLElement;
          const last = focusable[focusable.length - 1] as HTMLElement;

          if (e.shiftKey && document.activeElement === first) {
            e.preventDefault();
            last.focus();
          } else if (!e.shiftKey && document.activeElement === last) {
            e.preventDefault();
            first.focus();
          }
        }
        break;
    }
  }, [onEscape, onEnter, trapFocus, containerRef]);

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);
}

// Keyboard shortcuts reference
export const KEYBOARD_SHORTCUTS = {
  'Alt + V': 'Start/stop voice input',
  'Alt + H': 'Toggle high contrast mode',
  'Alt + S': 'Save current work',
  'Escape': 'Close modal/dialog',
  'Tab': 'Navigate between elements',
  'Enter': 'Activate button/link',
  '?': 'Show keyboard shortcuts help'
};
```

### Phase 6: Accessibility Settings Panel
**CREATE FILE: /ganuda/vetassist/frontend/src/components/AccessibilitySettings.tsx**

```typescript
/**
 * Accessibility Settings Panel
 * Allows veterans to customize their experience
 */

import React from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';

export const AccessibilitySettings: React.FC = () => {
  const [settings, setSettings] = useLocalStorage('a11y-settings', {
    highContrast: false,
    largeText: false,
    reduceMotion: false,
    screenReaderMode: false
  });

  const toggleSetting = (key: keyof typeof settings) => {
    setSettings(prev => ({ ...prev, [key]: !prev[key] }));

    // Apply to document
    if (key === 'highContrast') {
      document.body.classList.toggle('high-contrast');
    }
    if (key === 'largeText') {
      document.body.classList.toggle('large-text');
    }
    if (key === 'reduceMotion') {
      document.body.classList.toggle('reduce-motion');
    }
  };

  return (
    <div
      className="accessibility-settings"
      role="region"
      aria-label="Accessibility settings"
    >
      <h2>Accessibility Options</h2>

      <div className="setting">
        <label>
          <input
            type="checkbox"
            checked={settings.highContrast}
            onChange={() => toggleSetting('highContrast')}
            aria-describedby="high-contrast-desc"
          />
          High Contrast Mode
        </label>
        <p id="high-contrast-desc" className="setting-desc">
          Increases color contrast for better visibility
        </p>
      </div>

      <div className="setting">
        <label>
          <input
            type="checkbox"
            checked={settings.largeText}
            onChange={() => toggleSetting('largeText')}
            aria-describedby="large-text-desc"
          />
          Large Text
        </label>
        <p id="large-text-desc" className="setting-desc">
          Increases base font size to 18px
        </p>
      </div>

      <div className="setting">
        <label>
          <input
            type="checkbox"
            checked={settings.reduceMotion}
            onChange={() => toggleSetting('reduceMotion')}
            aria-describedby="reduce-motion-desc"
          />
          Reduce Motion
        </label>
        <p id="reduce-motion-desc" className="setting-desc">
          Disables animations and transitions
        </p>
      </div>

      <div className="keyboard-shortcuts">
        <h3>Keyboard Shortcuts</h3>
        <dl>
          <dt>Alt + V</dt><dd>Voice input</dd>
          <dt>Alt + H</dt><dd>Toggle high contrast</dd>
          <dt>Alt + S</dt><dd>Save work</dd>
          <dt>?</dt><dd>Show all shortcuts</dd>
        </dl>
      </div>
    </div>
  );
};
```

## Success Criteria

| Metric | Target | Test Method |
|--------|--------|-------------|
| Lighthouse Accessibility | >90% | Automated audit |
| Keyboard Navigation | 100% features | Manual testing |
| Screen Reader | All content accessible | NVDA/VoiceOver test |
| Voice Input | Working on Chrome/Edge | Manual test |
| Color Contrast | WCAG AA (4.5:1) | Automated check |
| Click Targets | 44px minimum | CSS audit |

## Testing Plan

1. **Automated Testing**
   ```bash
   npm run test:a11y  # Run axe-core tests
   lighthouse http://localhost:3000 --only-categories=accessibility
   ```

2. **Manual Testing**
   - Test with NVDA (Windows) and VoiceOver (Mac)
   - Navigate entire app using only keyboard
   - Test voice input with ambient noise
   - Test high contrast with color blindness simulator

3. **Veteran Testing**
   - Recruit 3-5 disabled veterans for usability testing
   - Document feedback and iterate

## Cherokee Wisdom

> "No one walks the path alone - we carry each other."

Every veteran, regardless of disability, deserves full access to claim their earned benefits. This is our duty.

---
**Council Vote**: 4fdd4018e18f99b4 - Priority #2
**BRD Requirement**: F-013 (MUST)
**Cherokee AI Federation - No Veteran Left Behind**

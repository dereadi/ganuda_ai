# JR INSTRUCTION: Assist Core Frontend Gap-Fill (7 Missing Files + SQL Schema)

**Task ID:** ASSIST-GAPFILL-CORE-FRONTEND
**Priority:** P1 -- Unblocks Phase 2 vertical migration
**Assigned To:** Any available Jr
**Created By:** TPM (Claude Opus 4.5)
**Date:** 2026-02-04
**Estimated Effort:** 2-3 hours
**Node:** Any (Node.js 18+ required)
**Type:** GAP-FILL -- partial execution recovery

---

## Objective

Complete the Assist core frontend scaffold by creating the 7 files that were missed during initial Phase 1 execution, plus the core SQL schema file. The Phase 1 scaffold instruction (`JR-ASSIST-PHASE1-CORE-SCAFFOLD-FEB04-2026`) created the directory structure and many files successfully, but the following were not written to disk.

This is a surgical gap-fill. Do NOT recreate files that already exist. Do NOT modify existing files.

---

## Context

The Phase 1 scaffold created most of the `/ganuda/assist/core/frontend/` tree. Theme files, basic components (Header, Button, Alert, FormField, WizardProgress), test suites, CI workflows, package.json, and jest.config.js all landed correctly. What is missing are the three major interactive components (WizardShell, CalculatorView, ChatPanel), the safety-critical CrisisAlert component, the API client library, the auth context provider, the shared TypeScript types, and the core SQL schema.

Without these files, no vertical can inherit the core frontend or stand up its database tables.

---

## Files That ALREADY EXIST (DO NOT Recreate)

Confirm these exist before proceeding. If any are missing, STOP and report to TPM.

| Path | Status |
|------|--------|
| `/ganuda/assist/core/frontend/src/themes/base-theme.ts` | EXISTS |
| `/ganuda/assist/core/frontend/src/themes/vetassist-theme.ts` | EXISTS |
| `/ganuda/assist/core/frontend/src/themes/ssidassist-theme.ts` | EXISTS |
| `/ganuda/assist/core/frontend/src/themes/tribeassist-theme.ts` | EXISTS |
| `/ganuda/assist/core/frontend/src/themes/ThemeProvider.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/components/Header.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/components/Button.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/components/Alert.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/components/forms/FormField.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/components/WizardProgress.tsx` | EXISTS |
| `/ganuda/assist/core/frontend/src/styles/button-extensions.scss` | EXISTS |
| `/ganuda/assist/core/frontend/tests/` (all test files) | EXISTS |
| `/ganuda/assist/core/frontend/.github/workflows/` | EXISTS |
| `/ganuda/assist/core/frontend/package.json` | EXISTS |
| `/ganuda/assist/core/frontend/jest.config.js` | EXISTS |

---

## Steps

### Step 0: Pre-flight Check

Verify existing files are intact before writing anything.

```bash
cd /ganuda/assist/core/frontend
echo "=== Pre-flight: Verifying existing files ==="
EXISTING_FILES=(
  "src/themes/base-theme.ts"
  "src/themes/vetassist-theme.ts"
  "src/themes/ssidassist-theme.ts"
  "src/themes/tribeassist-theme.ts"
  "src/themes/ThemeProvider.tsx"
  "src/components/Header.tsx"
  "src/components/Button.tsx"
  "src/components/Alert.tsx"
  "src/components/forms/FormField.tsx"
  "src/components/WizardProgress.tsx"
  "src/styles/button-extensions.scss"
  "package.json"
  "jest.config.js"
)
ALL_OK=true
for f in "${EXISTING_FILES[@]}"; do
  if [ -f "$f" ]; then
    echo "[OK] $f"
  else
    echo "[MISSING] $f -- STOP: existing file unexpectedly missing"
    ALL_OK=false
  fi
done
if [ "$ALL_OK" = true ]; then
  echo "Pre-flight PASSED. Proceed with gap-fill."
else
  echo "Pre-flight FAILED. Report to TPM before continuing."
fi
```

If pre-flight fails, do NOT proceed. Report the missing file to TPM.

---

### Step 1: Create `src/lib/` directory

```bash
mkdir -p /ganuda/assist/core/frontend/src/lib
```

---

### Step 2: Create `/ganuda/assist/core/frontend/src/lib/types.ts`

Core TypeScript types shared across all verticals.

```typescript
/**
 * Core types for Assist Platform.
 * Shared across all verticals.
 */

export interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  isActive: boolean;
  vertical?: string;
  createdAt: string;
}

export interface Session {
  id: string;
  userId: string;
  vertical: string;
  sessionData: Record<string, any>;
  createdAt: string;
  updatedAt: string;
}

export interface WizardStepDef {
  id: string;
  title: string;
  description?: string;
  fields: WizardFieldDef[];
  conditions?: WizardCondition[];
  helpText?: string;
  required?: boolean;
}

export interface WizardFieldDef {
  id: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'date' | 'textarea' | 'radio' | 'checkbox';
  required?: boolean;
  options?: { value: string; label: string }[];
  helpText?: string;
  placeholder?: string;
}

export interface WizardCondition {
  field: string;
  operator: 'equals' | 'not_equals' | 'in' | 'exists';
  value: any;
}

export interface CalculationResult {
  amount: number;
  breakdown: Record<string, any>;
  explanation: string;
  warnings: string[];
  metadata: Record<string, any>;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  specialist?: string;
  citations?: string[];
  timestamp: string;
}

export interface ChatResponse {
  message: string;
  citations: string[];
  specialist: string;
  confidence: number;
}

export interface AuditEntry {
  id: number;
  userId: string;
  vertical: string;
  action: string;
  details: Record<string, any>;
  createdAt: string;
}

export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  vertical: string;
  version: string;
  database: 'connected' | 'disconnected';
}
```

---

### Step 3: Create `/ganuda/assist/core/frontend/src/lib/api-client.ts`

Base API client with auth headers, fetch wrapper, and error handling.

```typescript
/**
 * Base API client for Assist Platform.
 * Handles auth headers, error responses, and base URL configuration.
 */

export interface ApiError {
  status: number;
  message: string;
  detail?: any;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}

export class AssistApiClient {
  private baseUrl: string;
  private token: string | null = null;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    return headers;
  }

  async get<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>('GET', path);
  }

  async post<T>(path: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>('POST', path, body);
  }

  async put<T>(path: string, body?: any): Promise<ApiResponse<T>> {
    return this.request<T>('PUT', path, body);
  }

  async delete<T>(path: string): Promise<ApiResponse<T>> {
    return this.request<T>('DELETE', path);
  }

  private async request<T>(method: string, path: string, body?: any): Promise<ApiResponse<T>> {
    const url = `${this.baseUrl}${path}`;

    const options: RequestInit = {
      method,
      headers: this.getHeaders(),
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);

    if (!response.ok) {
      const errorBody = await response.json().catch(() => null);
      const error: ApiError = {
        status: response.status,
        message: errorBody?.detail || response.statusText,
        detail: errorBody,
      };
      throw error;
    }

    const data = await response.json();
    return { data, status: response.status };
  }
}

// Factory for creating vertical-specific clients
export function createApiClient(vertical: string): AssistApiClient {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || `http://localhost:8000`;
  return new AssistApiClient(baseUrl);
}
```

---

### Step 4: Create `/ganuda/assist/core/frontend/src/lib/auth-context.tsx`

Shared auth provider for React apps. Manages JWT tokens, login state, and user info.

```tsx
/**
 * Auth context provider for Assist Platform.
 * Manages JWT tokens, login state, and user info.
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { AssistApiClient } from './api-client';

interface User {
  id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  vertical?: string;
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

interface AuthProviderProps {
  children: ReactNode;
  apiClient: AssistApiClient;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children, apiClient }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const stored = localStorage.getItem('assist_token');
    if (stored) {
      setToken(stored);
      apiClient.setToken(stored);
      fetchUser(stored);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUser = async (authToken: string) => {
    try {
      apiClient.setToken(authToken);
      const { data } = await apiClient.get<User>('/api/v1/auth/me');
      setUser(data);
    } catch {
      localStorage.removeItem('assist_token');
      setToken(null);
      apiClient.setToken(null);
    } finally {
      setLoading(false);
    }
  };

  const login = async (email: string, password: string) => {
    const { data } = await apiClient.post<{ access_token: string; user: User }>(
      '/api/v1/auth/login',
      { email, password }
    );
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('assist_token', data.access_token);
    apiClient.setToken(data.access_token);
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('assist_token');
    apiClient.setToken(null);
  };

  return (
    <AuthContext.Provider value={{
      user,
      token,
      loading,
      login,
      logout,
      isAuthenticated: !!token && !!user,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
};
```

---

### Step 5: Create `/ganuda/assist/core/frontend/src/components/WizardShell.tsx`

Multi-step wizard renderer that reads from YAML-defined wizard configs. Handles navigation, validation, and save/resume.

```tsx
/**
 * WizardShell - Multi-step wizard renderer
 * Renders wizard steps from YAML config, handles navigation, validation, save/resume.
 */
import React, { useState, useCallback } from 'react';
import { StepIndicator, StepIndicatorStep, Button, Alert } from '@trussworks/react-uswds';
import { WizardProgress } from './WizardProgress';

export interface WizardField {
  id: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'date' | 'textarea' | 'radio' | 'checkbox';
  required?: boolean;
  options?: { value: string; label: string }[];
  helpText?: string;
  placeholder?: string;
  validation?: {
    min?: number;
    max?: number;
    pattern?: string;
    message?: string;
  };
}

export interface WizardStep {
  id: string;
  title: string;
  description?: string;
  fields: WizardField[];
  conditions?: { field: string; operator: string; value: any }[];
  helpText?: string;
}

export interface WizardConfig {
  name: string;
  description: string;
  steps: WizardStep[];
}

interface WizardShellProps {
  config: WizardConfig;
  initialAnswers?: Record<string, any>;
  onComplete: (answers: Record<string, any>) => void;
  onSave?: (answers: Record<string, any>, currentStep: number) => void;
  className?: string;
}

export const WizardShell: React.FC<WizardShellProps> = ({
  config,
  initialAnswers = {},
  onComplete,
  onSave,
  className = '',
}) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, any>>(initialAnswers);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const visibleSteps = config.steps.filter(step =>
    evaluateConditions(step.conditions, answers)
  );

  const currentStepDef = visibleSteps[currentStep];
  const isLastStep = currentStep === visibleSteps.length - 1;

  const handleFieldChange = useCallback((fieldId: string, value: any) => {
    setAnswers(prev => ({ ...prev, [fieldId]: value }));
    setErrors(prev => {
      const next = { ...prev };
      delete next[fieldId];
      return next;
    });
  }, []);

  const validateCurrentStep = (): boolean => {
    const stepErrors: Record<string, string> = {};
    for (const field of currentStepDef.fields) {
      if (field.required && !answers[field.id]) {
        stepErrors[field.id] = `${field.label} is required`;
      }
    }
    setErrors(stepErrors);
    return Object.keys(stepErrors).length === 0;
  };

  const handleNext = () => {
    if (!validateCurrentStep()) return;
    if (isLastStep) {
      onComplete(answers);
    } else {
      setCurrentStep(prev => prev + 1);
      onSave?.(answers, currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(prev => prev - 1);
    }
  };

  if (!currentStepDef) return null;

  return (
    <div className={`wizard-shell ${className}`}>
      <h2>{config.name}</h2>
      <WizardProgress
        steps={visibleSteps.map(s => s.title)}
        currentStep={currentStep}
      />
      <div className="wizard-step">
        <h3>{currentStepDef.title}</h3>
        {currentStepDef.description && <p>{currentStepDef.description}</p>}
        {currentStepDef.fields.map(field => (
          <div key={field.id} className="wizard-field">
            <label htmlFor={field.id}>{field.label}</label>
            {renderField(field, answers[field.id], handleFieldChange)}
            {errors[field.id] && (
              <Alert type="error" slim>{errors[field.id]}</Alert>
            )}
            {field.helpText && <span className="help-text">{field.helpText}</span>}
          </div>
        ))}
      </div>
      <div className="wizard-nav">
        {currentStep > 0 && (
          <Button type="button" outline onClick={handleBack}>Back</Button>
        )}
        <Button type="button" onClick={handleNext}>
          {isLastStep ? 'Submit' : 'Next'}
        </Button>
      </div>
    </div>
  );
};

function evaluateConditions(
  conditions: WizardStep['conditions'],
  answers: Record<string, any>
): boolean {
  if (!conditions || conditions.length === 0) return true;
  return conditions.every(cond => {
    const answer = answers[cond.field];
    switch (cond.operator) {
      case 'equals': return answer === cond.value;
      case 'not_equals': return answer !== cond.value;
      case 'in': return Array.isArray(cond.value) && cond.value.includes(answer);
      case 'exists': return answer !== undefined && answer !== null;
      default: return true;
    }
  });
}

function renderField(
  field: WizardField,
  value: any,
  onChange: (id: string, value: any) => void
): React.ReactNode {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    onChange(field.id, e.target.value);
  };

  switch (field.type) {
    case 'select':
      return (
        <select id={field.id} value={value || ''} onChange={handleChange} className="usa-select">
          <option value="">-- Select --</option>
          {field.options?.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      );
    case 'textarea':
      return (
        <textarea
          id={field.id}
          value={value || ''}
          onChange={handleChange}
          className="usa-textarea"
          placeholder={field.placeholder}
        />
      );
    case 'radio':
      return (
        <fieldset className="usa-fieldset">
          {field.options?.map(opt => (
            <div key={opt.value} className="usa-radio">
              <input
                className="usa-radio__input"
                type="radio"
                id={`${field.id}-${opt.value}`}
                name={field.id}
                value={opt.value}
                checked={value === opt.value}
                onChange={handleChange}
              />
              <label className="usa-radio__label" htmlFor={`${field.id}-${opt.value}`}>
                {opt.label}
              </label>
            </div>
          ))}
        </fieldset>
      );
    default:
      return (
        <input
          id={field.id}
          type={field.type}
          value={value || ''}
          onChange={handleChange}
          className="usa-input"
          placeholder={field.placeholder}
        />
      );
  }
}

export default WizardShell;
```

---

### Step 6: Create `/ganuda/assist/core/frontend/src/components/CalculatorView.tsx`

Generic calculator result display with breakdown table and explanation.

```tsx
/**
 * CalculatorView - Displays calculation results with breakdown and explanation.
 */
import React from 'react';
import { Alert, Table } from '@trussworks/react-uswds';

export interface CalculationBreakdown {
  label: string;
  value: string | number;
  highlight?: boolean;
}

export interface CalculationResultData {
  amount: number;
  breakdown: CalculationBreakdown[];
  explanation: string;
  warnings?: string[];
}

interface CalculatorViewProps {
  result: CalculationResultData | null;
  loading?: boolean;
  title?: string;
  currency?: boolean;
  className?: string;
}

export const CalculatorView: React.FC<CalculatorViewProps> = ({
  result,
  loading = false,
  title = 'Calculation Result',
  currency = true,
  className = '',
}) => {
  if (loading) {
    return <div className={`calculator-view ${className}`}>Calculating...</div>;
  }

  if (!result) return null;

  const formatValue = (val: number | string): string => {
    if (typeof val === 'number' && currency) {
      return `$${val.toLocaleString('en-US', { minimumFractionDigits: 2 })}`;
    }
    return String(val);
  };

  return (
    <div className={`calculator-view ${className}`}>
      <h3>{title}</h3>

      <div className="result-amount">
        <span className="amount-label">Estimated Amount:</span>
        <span className="amount-value">{formatValue(result.amount)}</span>
      </div>

      {result.warnings && result.warnings.length > 0 && (
        <Alert type="warning" slim>
          {result.warnings.map((w, i) => <p key={i}>{w}</p>)}
        </Alert>
      )}

      {result.breakdown.length > 0 && (
        <Table bordered striped className="result-breakdown">
          <thead>
            <tr>
              <th>Component</th>
              <th>Value</th>
            </tr>
          </thead>
          <tbody>
            {result.breakdown.map((item, i) => (
              <tr key={i} className={item.highlight ? 'highlight' : ''}>
                <td>{item.label}</td>
                <td>{formatValue(item.value)}</td>
              </tr>
            ))}
          </tbody>
        </Table>
      )}

      {result.explanation && (
        <div className="result-explanation">
          <h4>How this was calculated:</h4>
          <p>{result.explanation}</p>
        </div>
      )}
    </div>
  );
};

export default CalculatorView;
```

---

### Step 7: Create `/ganuda/assist/core/frontend/src/components/ChatPanel.tsx`

Council chat interface component with message history, typing indicators, and specialist attribution.

```tsx
/**
 * ChatPanel - Council chat interface.
 * Supports message history, typing indicators, and specialist attribution.
 */
import React, { useState, useRef, useEffect } from 'react';
import { Button, Alert } from '@trussworks/react-uswds';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  specialist?: string;
  citations?: string[];
  timestamp: Date;
}

interface ChatPanelProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  loading?: boolean;
  placeholder?: string;
  title?: string;
  className?: string;
}

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  onSendMessage,
  loading = false,
  placeholder = 'Type your question...',
  title = 'Ask the Council',
  className = '',
}) => {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || loading) return;
    onSendMessage(input.trim());
    setInput('');
  };

  return (
    <div className={`chat-panel ${className}`}>
      <h3>{title}</h3>
      <div className="chat-messages" role="log" aria-live="polite">
        {messages.map(msg => (
          <div key={msg.id} className={`chat-message chat-${msg.role}`}>
            {msg.specialist && (
              <span className="chat-specialist">{msg.specialist}</span>
            )}
            <div className="chat-content">{msg.content}</div>
            {msg.citations && msg.citations.length > 0 && (
              <div className="chat-citations">
                {msg.citations.map((c, i) => (
                  <span key={i} className="citation">{c}</span>
                ))}
              </div>
            )}
          </div>
        ))}
        {loading && <div className="chat-typing">Council is thinking...</div>}
        <div ref={messagesEndRef} />
      </div>
      <form onSubmit={handleSubmit} className="chat-input">
        <input
          type="text"
          className="usa-input"
          value={input}
          onChange={e => setInput(e.target.value)}
          placeholder={placeholder}
          disabled={loading}
          aria-label="Chat message input"
        />
        <Button type="submit" disabled={loading || !input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
};

export default ChatPanel;
```

---

### Step 8: Create `/ganuda/assist/core/frontend/src/components/CrisisAlert.tsx`

Crisis detection alert component. Displays when C-SSRS scoring triggers. Shows 988 Suicide and Crisis Lifeline plus veteran/indigenous resources.

**SAFETY-CRITICAL:** This component MUST always render crisis resources when severity >= 1. Never suppress or hide these resources based on user preference or UI state.

```tsx
/**
 * CrisisAlert - Displays crisis resources when C-SSRS detection triggers.
 * Shows 988 Suicide & Crisis Lifeline and relevant veteran/indigenous resources.
 */
import React from 'react';
import { Alert } from '@trussworks/react-uswds';

interface CrisisAlertProps {
  severity: number;
  hasVeteranRisk?: boolean;
  hasIndigenousRisk?: boolean;
  onDismiss?: () => void;
  className?: string;
}

export const CrisisAlert: React.FC<CrisisAlertProps> = ({
  severity,
  hasVeteranRisk = false,
  hasIndigenousRisk = false,
  onDismiss,
  className = '',
}) => {
  if (severity < 1) return null;

  const isEmergency = severity >= 3;

  return (
    <div className={`crisis-alert ${className}`} role="alert" aria-live="assertive">
      <Alert type={isEmergency ? 'error' : 'warning'} heading="Crisis Support Available 24/7">
        <p><strong>988 Suicide &amp; Crisis Lifeline</strong></p>
        <p>Call or text <a href="tel:988">988</a></p>
        <p>Online chat: <a href="https://988lifeline.org/chat" target="_blank" rel="noopener noreferrer">988lifeline.org/chat</a></p>

        <p><strong>Crisis Text Line</strong></p>
        <p>Text HOME to <a href="sms:741741">741741</a></p>

        {hasVeteranRisk && (
          <>
            <p><strong>Veterans Crisis Line</strong></p>
            <p>Call <a href="tel:988">988</a>, press 1</p>
            <p>Text <a href="sms:838255">838255</a></p>
          </>
        )}

        {hasIndigenousRisk && (
          <>
            <p><strong>Cherokee Nation Behavioral Health</strong></p>
            <p>Call <a href="tel:918-453-5000">918-453-5000</a></p>
          </>
        )}

        <p>You are not alone. Help is available right now. These services are free, confidential, and available 24/7.</p>
      </Alert>
    </div>
  );
};

export default CrisisAlert;
```

---

### Step 9: Create `/ganuda/assist/core/sql/assist_core_schema.sql`

Core database tables for the Assist platform. Run on bluefin (192.168.132.222), database `zammad_production`. **DO NOT run in a transaction that touches VetAssist tables.** This creates NEW tables only.

```bash
mkdir -p /ganuda/assist/core/sql
```

```sql
-- Assist Platform Core Schema
-- Run on bluefin (192.168.132.222) database: zammad_production
-- Created: 2026-02-04 by TPM (Claude Opus 4.5) + Council
--
-- SAFETY: These are NEW tables. They do NOT touch existing VetAssist tables.

-- Core user table for all Assist verticals
CREATE TABLE IF NOT EXISTS assist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'en',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Session storage for wizards, chat, and vertical state
CREATE TABLE IF NOT EXISTS assist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES assist_users(id) ON DELETE CASCADE,
    vertical VARCHAR(50) NOT NULL,
    session_type VARCHAR(50) DEFAULT 'wizard',
    session_data JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit trail for all actions across all verticals
CREATE TABLE IF NOT EXISTS assist_audit (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID,
    vertical VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    details JSONB DEFAULT '{}',
    ip_hash VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_assist_users_email ON assist_users(email);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_user ON assist_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_vertical ON assist_sessions(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_sessions_type ON assist_sessions(session_type);
CREATE INDEX IF NOT EXISTS idx_assist_audit_user ON assist_audit(user_id);
CREATE INDEX IF NOT EXISTS idx_assist_audit_vertical ON assist_audit(vertical);
CREATE INDEX IF NOT EXISTS idx_assist_audit_created ON assist_audit(created_at);
CREATE INDEX IF NOT EXISTS idx_assist_audit_action ON assist_audit(action);

-- Updated_at trigger
CREATE OR REPLACE FUNCTION assist_update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_assist_users_updated
    BEFORE UPDATE ON assist_users
    FOR EACH ROW EXECUTE FUNCTION assist_update_timestamp();

CREATE OR REPLACE TRIGGER trg_assist_sessions_updated
    BEFORE UPDATE ON assist_sessions
    FOR EACH ROW EXECUTE FUNCTION assist_update_timestamp();
```

**Do NOT execute against production without TPM approval.** Parse-check only during this task.

---

## Verification

Run this verification script after all files are created. Every line must show `[OK]`.

```bash
#!/bin/bash
cd /ganuda/assist/core/frontend
echo "=== Verifying Core Frontend Gap-Fill ==="
echo ""

# Check the 7 new frontend files
echo "--- New Frontend Files ---"
for f in "src/components/WizardShell.tsx" "src/components/CalculatorView.tsx" "src/components/ChatPanel.tsx" "src/components/CrisisAlert.tsx" "src/lib/api-client.ts" "src/lib/auth-context.tsx" "src/lib/types.ts"; do
    if [ -f "$f" ]; then
        echo "[OK] $f ($(wc -l < "$f") lines)"
    else
        echo "[FAIL] $f MISSING"
    fi
done

echo ""

# Check the SQL schema
echo "--- SQL Schema ---"
SQL_FILE="/ganuda/assist/core/sql/assist_core_schema.sql"
if [ -f "$SQL_FILE" ]; then
    echo "[OK] $SQL_FILE ($(wc -l < "$SQL_FILE") lines)"
else
    echo "[FAIL] $SQL_FILE MISSING"
fi

echo ""

# Validate SQL schema content
echo "--- SQL Schema Content Check ---"
python3 -c "
with open('/ganuda/assist/core/sql/assist_core_schema.sql') as f:
    sql = f.read()
checks = [
    ('assist_users', 'CREATE TABLE IF NOT EXISTS assist_users' in sql),
    ('assist_sessions', 'CREATE TABLE IF NOT EXISTS assist_sessions' in sql),
    ('assist_audit', 'CREATE TABLE IF NOT EXISTS assist_audit' in sql),
    ('gen_random_uuid', 'gen_random_uuid' in sql),
    ('ON DELETE CASCADE', 'ON DELETE CASCADE' in sql),
    ('update_timestamp trigger', 'assist_update_timestamp' in sql),
]
all_ok = True
for name, ok in checks:
    status = '[OK]' if ok else '[FAIL]'
    print(f'{status} SQL contains {name}')
    if not ok:
        all_ok = False
if all_ok:
    print('SQL schema content check PASSED')
else:
    print('SQL schema content check FAILED')
"

echo ""

# Verify existing files were NOT overwritten
echo "--- Existing Files Still Intact ---"
for f in "src/components/Header.tsx" "src/components/Button.tsx" "src/components/Alert.tsx" "src/components/forms/FormField.tsx" "src/components/WizardProgress.tsx" "src/themes/ThemeProvider.tsx" "package.json" "jest.config.js"; do
    if [ -f "$f" ]; then
        echo "[OK] $f (untouched)"
    else
        echo "[FAIL] $f MISSING -- existing file was deleted!"
    fi
done

echo ""

# Check TypeScript content has expected exports
echo "--- TypeScript Export Check ---"
python3 -c "
import os

checks = [
    ('src/lib/types.ts', ['User', 'Session', 'ChatMessage', 'CalculationResult', 'HealthStatus']),
    ('src/lib/api-client.ts', ['AssistApiClient', 'createApiClient', 'ApiError', 'ApiResponse']),
    ('src/lib/auth-context.tsx', ['AuthProvider', 'useAuth']),
    ('src/components/WizardShell.tsx', ['WizardShell', 'WizardConfig', 'WizardStep', 'WizardField']),
    ('src/components/CalculatorView.tsx', ['CalculatorView', 'CalculationResultData']),
    ('src/components/ChatPanel.tsx', ['ChatPanel', 'ChatMessage']),
    ('src/components/CrisisAlert.tsx', ['CrisisAlert']),
]

base = '/ganuda/assist/core/frontend'
all_ok = True
for filepath, exports in checks:
    full_path = os.path.join(base, filepath)
    if not os.path.exists(full_path):
        print(f'[FAIL] {filepath} does not exist')
        all_ok = False
        continue
    with open(full_path) as f:
        content = f.read()
    for exp in exports:
        if exp in content:
            print(f'[OK] {filepath} exports {exp}')
        else:
            print(f'[FAIL] {filepath} missing export {exp}')
            all_ok = False

if all_ok:
    print('TypeScript export check PASSED')
else:
    print('TypeScript export check FAILED')
"

echo ""
echo "=== Gap-Fill Verification Complete ==="
```

---

## Deliverables

| # | File | Type | Description |
|---|------|------|-------------|
| 1 | `/ganuda/assist/core/frontend/src/components/WizardShell.tsx` | TSX | Multi-step wizard renderer with conditional steps |
| 2 | `/ganuda/assist/core/frontend/src/components/CalculatorView.tsx` | TSX | Calculator result display with breakdown table |
| 3 | `/ganuda/assist/core/frontend/src/components/ChatPanel.tsx` | TSX | Council chat interface with specialist attribution |
| 4 | `/ganuda/assist/core/frontend/src/components/CrisisAlert.tsx` | TSX | Crisis resource display (safety-critical) |
| 5 | `/ganuda/assist/core/frontend/src/lib/api-client.ts` | TS | Base API client with auth and error handling |
| 6 | `/ganuda/assist/core/frontend/src/lib/auth-context.tsx` | TSX | Shared auth provider with JWT management |
| 7 | `/ganuda/assist/core/frontend/src/lib/types.ts` | TS | Core TypeScript types shared across verticals |
| 8 | `/ganuda/assist/core/sql/assist_core_schema.sql` | SQL | Core database tables (assist_users, assist_sessions, assist_audit) |

---

## Safety Checklist

Before marking this task complete, verify:

- [ ] All 8 files created and verification script shows all `[OK]`
- [ ] No existing files were overwritten or modified
- [ ] CrisisAlert renders 988 resources for severity >= 1
- [ ] CrisisAlert renders Veterans Crisis Line when `hasVeteranRisk` is true
- [ ] CrisisAlert renders Cherokee Nation Behavioral Health when `hasIndigenousRisk` is true
- [ ] CrisisAlert uses `role="alert"` and `aria-live="assertive"` for accessibility
- [ ] SQL uses `IF NOT EXISTS` on all CREATE statements (idempotent)
- [ ] SQL does NOT touch any existing VetAssist tables
- [ ] SQL was NOT executed against production (parse-check only)
- [ ] AuthProvider stores token in localStorage under `assist_token` key
- [ ] API client includes `Authorization: Bearer` header when token is set
- [ ] WizardShell handles conditional step visibility via `evaluateConditions`
- [ ] All components use USWDS classes (`usa-input`, `usa-select`, `usa-textarea`, `usa-radio`)

---

## Dependencies

- **Depends on:** `JR-ASSIST-PHASE1-CORE-SCAFFOLD-FEB04-2026` (partial completion provides existing files)
- **Blocks:** Phase 2 VetAssist migration, Phase 3 new vertical scaffold, `JR-ASSIST-PHASE2-SSIDASSIST-FEB04-2026`, `JR-ASSIST-PHASE3-TRIBEASSIST-FEB04-2026`
- **Related:** `JR-ASSIST-BUILD-CSSRS-FEB04-2026` (CrisisAlert component consumes C-SSRS scoring results)

---

**Status:** PENDING ASSIGNMENT
**Last Updated:** 2026-02-04

*Tools that make broken systems less broken, built by people who believe the world is worth fixing.*

*ᎦᎵᏉᎩ ᎠᏂᏔᎵᏍᎬ -- For the Seven Generations*

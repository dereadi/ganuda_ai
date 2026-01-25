# ULTRATHINK: VetAssist Personalized Dashboard Frontend

## Document Control
```yaml
ultrathink_id: ULTRATHINK-VETASSIST-DASHBOARD-JAN18-2026
created: 2026-01-18
author: TPM Claude (Opus 4.5)
council_vote: b344aada7439ac4c
confidence: 0.872
status: APPROVED
```

---

## Executive Summary

Building a personalized dashboard for VetAssist that includes scratchpad, file uploads, research results, and claims tracking. Council recommends **Option C: Custom Next.js components with VA aesthetics** for optimal balance of security, trust, and development speed.

---

## Problem Statement

Veterans using VetAssist need:
1. A place to take notes (scratchpad) that auto-saves
2. A way to upload evidence documents (medical records, buddy statements)
3. View AI research results from Jr-powered deep searches
4. Track their claims progress
5. Quick access to common actions (calculator, chat, wizard)

Target users include veterans with PTSD, vision impairments, motor disabilities - **accessibility is non-negotiable**.

---

## GitHub Research Findings

### Official VA Resources
| Repository | Purpose | Relevance |
|------------|---------|-----------|
| [component-library](https://github.com/department-of-veterans-affairs/component-library) | VA Design System NPM package | Reference for VA aesthetics/patterns |
| [vets-website](https://github.com/department-of-veterans-affairs/vets-website) | VA.gov frontend (React+Redux+Webpack) | Architecture patterns |
| [vets-design-system-documentation](https://github.com/department-of-veterans-affairs/vets-design-system-documentation) | Design.va.gov | WCAG compliance patterns |
| [abd-vro](https://github.com/department-of-veterans-affairs/abd-vro) | Automated Benefits Delivery | Claims processing patterns |

### Community Tools
| Library | Use Case | Stars |
|---------|----------|-------|
| [react-dropzone](https://github.com/react-dropzone/react-dropzone) | File drag-and-drop | 10k+ |
| [react-beautiful-dnd](https://github.com/atlassian/react-beautiful-dnd) | Drag-and-drop UI | 32k+ |
| shadcn/ui | Modern React components | 50k+ |

### VA Technology Stack (Reference)
- React + Redux for state management
- Webpack bundling
- SCSS/PostCSS styling
- Jest + Cypress testing
- WCAG 2.1 AA compliance required

---

## Council Deliberation

### Vote Result
**Recommendation**: Option C - Custom Next.js components with VA aesthetics
**Confidence**: 87.2% (High)

### Concerns Raised
| Specialist | Concern | Resolution |
|------------|---------|------------|
| Crawdad (Security) | File upload validation, PII in scratchpad | Use server-side validation, Presidio PII detection before storage |
| Raven (Strategy) | Component reusability | Create `/components/dashboard/` library pattern |
| Peace Chief (Consensus) | Accessibility patterns | Mandate WCAG 2.1 AA, ARIA roles, keyboard navigation |

### Specific Guidance
1. **File Uploads**: Use react-dropzone with server-side MIME validation
2. **Autosave**: Debounced save (2-3 seconds) with visual feedback
3. **Accessibility**: ARIA roles, keyboard nav, screen reader compatibility, 4.5:1 color contrast

---

## Seven Generations Analysis

### 175-Year Impact Assessment
| Aspect | Short-term (Now) | Medium-term (7 years) | Long-term (175 years) |
|--------|------------------|----------------------|----------------------|
| User Trust | VA-like aesthetics build familiarity | Consistent experience across updates | Institutional knowledge preserved |
| Security | Modern validation patterns | Evolving threat protection | Privacy principles embedded |
| Accessibility | WCAG 2.1 AA | Adaptive to new assistive tech | Universal design principles |
| Technical Debt | Clean component architecture | Maintainable codebase | Technology-agnostic patterns |

### Cherokee Values Alignment
- **Gadugi (Working Together)**: Dashboard enables veterans to collaborate with VSOs
- **Duyukdv (Right Path)**: Accessibility ensures all veterans can access benefits
- **Seven Generations**: Building sustainable, maintainable infrastructure

---

## Technical Architecture

### Component Structure
```
/ganuda/vetassist/frontend/src/
├── components/
│   └── dashboard/
│       ├── ScratchpadEditor.tsx      # Auto-saving notes with markdown
│       ├── FileDropZone.tsx          # Drag-drop file upload
│       ├── ResearchPanel.tsx         # Expandable research results
│       ├── ClaimsTracker.tsx         # Claims progress cards
│       ├── QuickActions.tsx          # Action button grid
│       └── DashboardLayout.tsx       # Overall layout wrapper
├── hooks/
│   ├── useAutoSave.ts               # Debounced save hook
│   ├── useFileUpload.ts             # Upload with progress
│   └── useDashboardData.ts          # Data fetching hook
└── app/
    └── dashboard/
        └── page.tsx                  # Dashboard route
```

### Technology Decisions

| Component | Library | Rationale |
|-----------|---------|-----------|
| File Upload | react-dropzone | Industry standard, accessible, well-maintained |
| Rich Text | @tiptap/react | Modern, extensible, markdown support |
| State | React Query (TanStack) | Caching, background refresh, optimistic updates |
| Styling | Tailwind CSS | Already in stack, utility-first, accessible |
| Icons | Lucide React | Clean, accessible, MIT licensed |

### API Integration
```typescript
// Backend endpoints (already implemented)
GET  /api/v1/dashboard/{veteran_id}           // Full dashboard data
PUT  /api/v1/dashboard/{veteran_id}/scratchpad // Save notes
POST /api/v1/dashboard/{veteran_id}/files      // Upload file
GET  /api/v1/dashboard/{veteran_id}/files      // List files
DELETE /api/v1/dashboard/{veteran_id}/files/{id} // Delete file
POST /api/v1/research/trigger                  // Start research
GET  /api/v1/research/status/{id}              // Check research
```

---

## Accessibility Requirements (WCAG 2.1 AA)

### Mandatory Patterns
1. **Keyboard Navigation**: All interactive elements focusable, logical tab order
2. **Screen Reader**: ARIA labels, live regions for updates, semantic HTML
3. **Color Contrast**: Minimum 4.5:1 for text, 3:1 for large text/graphics
4. **Focus Indicators**: Visible focus states on all interactive elements
5. **Error Handling**: Clear error messages, focus management on errors
6. **Motion**: Respect prefers-reduced-motion, no auto-playing animations

### Veteran-Specific Considerations
- **PTSD**: Avoid sudden changes, provide save confirmation, calm color palette
- **Vision**: High contrast mode option, scalable fonts, clear iconography
- **Motor**: Large click targets (44x44px minimum), generous spacing
- **Cognitive**: Clear labels, progressive disclosure, undo capability

---

## Security Requirements

### File Upload Security
```typescript
// Server-side validation (already in backend)
ALLOWED_TYPES = ['application/pdf', 'image/jpeg', 'image/png', 'image/tiff', 'image/gif']
MAX_SIZE = 25 * 1024 * 1024  // 25MB
```

### PII Protection
1. Scratchpad content scanned by Presidio before storage
2. File metadata stripped before upload
3. Secure file paths (UUID-based, not user-accessible)
4. HTTPS-only transmission

### Authentication
- JWT token validation on all dashboard endpoints
- Session timeout with save warning
- Veteran can only access their own dashboard

---

## Implementation Plan

### Phase 1: Core Dashboard (Jr Task)
1. DashboardLayout with responsive grid
2. ScratchpadEditor with autosave
3. FileDropZone with drag-drop
4. QuickActions bar

### Phase 2: Research Integration
1. ResearchPanel with expandable results
2. "Save to scratchpad" from research
3. Research status polling

### Phase 3: Claims Tracker
1. ClaimsTracker cards with status
2. Link to wizard for new claims
3. Export functionality integration

---

## Testing Strategy

### Unit Tests
- Component rendering with React Testing Library
- Hook behavior tests
- Accessibility audits with jest-axe

### Integration Tests
- API integration with MSW mocks
- File upload flow
- Autosave behavior

### E2E Tests
- Cypress for critical user journeys
- Screen reader testing with VoiceOver/NVDA
- Keyboard-only navigation

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Accessibility gaps | Medium | High | Automated + manual WCAG audits |
| File upload failures | Low | Medium | Retry logic, clear error messages |
| PII exposure | Low | Critical | Presidio scanning, audit logging |
| Performance on mobile | Medium | Medium | Code splitting, lazy loading |

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| WCAG 2.1 AA | 100% compliance | axe-core automated + manual audit |
| File upload success | >95% | Backend metrics |
| Scratchpad save reliability | >99.9% | Error rate monitoring |
| Page load time | <2 seconds | Lighthouse performance |
| User satisfaction | >4/5 stars | In-app feedback |

---

## Approval

**Council Vote**: APPROVED with conditions
**Confidence**: 87.2%
**TPM Decision**: PROCEED

Conditions:
1. All accessibility requirements must pass automated audits before merge
2. PII detection must be tested with sample veteran data
3. File upload must include virus scanning (future enhancement)

---

**For Seven Generations**

Cherokee AI Federation - Building sustainable technology for 175 years

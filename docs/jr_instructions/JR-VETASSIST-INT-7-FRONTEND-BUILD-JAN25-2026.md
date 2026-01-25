# JR Instruction: VetAssist Integration Part 7 - Frontend TypeScript Verification

**Task ID:** VETASSIST-INT-BUILD-001
**Priority:** P2
**Type:** frontend
**Assigned:** Software Engineer Jr.

---

## Objective

Verify the new EvidenceGapPanel React component compiles correctly with TypeScript.

---

## Deliverable

Run TypeScript type-check and build on the VetAssist frontend.

### Prerequisites

- Component file exists at: `/ganuda/vetassist/frontend/components/wizard/EvidenceGapPanel.tsx`
- Node.js >= 18 installed
- npm dependencies installed

### Execution

```bash
cd /ganuda/vetassist/frontend

# Install dependencies if needed
npm install

# Run TypeScript type-check
npm run type-check

# If type-check passes, run full build
npm run build
```

### Expected Results

1. `npm run type-check` exits with code 0 (no TypeScript errors)
2. `npm run build` completes successfully
3. Build output in `.next/` directory

### Troubleshooting

If styled-jsx types are missing, the component uses inline styles which are standard Next.js. If errors occur with `style jsx`, ensure Next.js types are correctly installed:

```bash
npm install --save-dev @types/react @types/node
```

---

## Success Criteria

- TypeScript compilation passes with no errors
- Next.js build completes successfully
- EvidenceGapPanel.tsx compiles without warnings

---

## For Seven Generations

Type-safe code prevents runtime errors that could confuse veterans during critical claim submissions.

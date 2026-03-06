# Jr Instruction: VetAssist Feedback Widget — Wire into Existing Code (v2, Part 2 of 2)

**Task ID:** FEEDBACK-WIRE-v2
**Kanban:** #1854
**Priority:** 6
**Assigned Jr:** Software Engineer Jr.
**use_rlm:** false

---

## Overview

Part 2: Wire the feedback endpoint and widget (created in Part 1) into the existing wizard page. Depends on Part 1 completing first.

---

## Step 1: Add FeedbackWidget to wizard session page

File: `/ganuda/vetassist/frontend/app/wizard/[sessionId]/page.tsx`

```
<<<<<<< SEARCH
import WizardChatHelper from './components/WizardChatHelper';
=======
import WizardChatHelper from './components/WizardChatHelper';
import FeedbackWidget from '../../components/FeedbackWidget';
>>>>>>> REPLACE
```

```
<<<<<<< SEARCH
      {/* AI Chat Helper */}
      <WizardChatHelper
=======
      {/* Feedback Widget */}
      <FeedbackWidget page="wizard" sessionId={sessionId} />

      {/* AI Chat Helper */}
      <WizardChatHelper
>>>>>>> REPLACE
```

---

## Verification

```text
cd /ganuda/vetassist/frontend && npx next build 2>&1 | tail -5
```

## What NOT to Change

- Do NOT modify feedback.py or FeedbackWidget.tsx (created in Part 1)
- Do NOT modify the wizard logic or step components

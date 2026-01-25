# ULTRATHINK: VetAssist Platform Evolution

## Document Control
```yaml
created: 2026-01-16
author: TPM (Darrell) + 7-Specialist Council
council_vote: 4c756c3175e0ad44
recommendation: PROCEED (82.5% confidence)
status: APPROVED FOR IMPLEMENTATION
```

---

## Executive Summary

VetAssist is evolving from a simple calculator + chat into a **comprehensive claims management platform** for veterans. This ULTRATHINK synthesizes Council feedback with planned features to create the definitive roadmap.

### The Vision

> **"Every veteran's personal claims command center - secure, accessible, and empowering."**

### Core Principles

1. **Free for Veterans** - Always. Revenue from organizations.
2. **Privacy First** - PII isolated on goldfin, encrypted, user-controlled
3. **Accessibility** - Built for veterans with disabilities
4. **Education, Not Practice** - We teach and organize; they file
5. **Seven Generations** - Built to last, built to help

---

## Platform Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           VETERAN'S DEVICE                                   │
│                    (Browser, iOS, Android - future)                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ HTTPS (TLS 1.3)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              REDFIN                                          │
│                         192.168.132.223                                      │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         VETASSIST FRONTEND                              │ │
│  │                         Next.js 14 (:3000)                              │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │   Home   │ │Calculator│ │   Chat   │ │Resources │ │  Dashboard   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │  (Claims)    │  │ │
│  │                                                       │  Workbench   │  │ │
│  │                                                       │  Profile     │  │ │
│  │                                                       │  Documents   │  │ │
│  │                                                       └──────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                    │                                         │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         VETASSIST BACKEND                               │ │
│  │                         FastAPI (:8001)                                 │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │ │
│  │  │   Auth   │ │Calculator│ │   Chat   │ │ Content  │ │  Workbench   │  │ │
│  │  │  + MFA   │ │ Service  │ │ Service  │ │ Service  │ │  Service     │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                   │ │
│  │  │ Document │ │ Profile  │ │   PII    │ │  Notif   │                   │ │
│  │  │ Service  │ │ Service  │ │ Service  │ │ Service  │                   │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘                   │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
         │              │              │                    │
         │              │              │                    │
         ▼              ▼              ▼                    ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────────┐ ┌─────────────────────┐
│   BLUEFIN   │ │ LLM GATEWAY │ │    GOLDFIN      │ │   NOTIFICATION      │
│  PostgreSQL │ │   (:8080)   │ │   PII VAULT     │ │   SERVICES          │
│   (:5432)   │ │             │ │   VLAN 20       │ │                     │
│             │ │ 7-Specialist│ │   Tailscale     │ │ - Email (SMTP)      │
│ - Users     │ │   Council   │ │                 │ │ - SMS (Twilio?)     │
│ - Claims    │ │             │ │ - Documents     │ │ - Push (future)     │
│ - Metadata  │ │ - Qwen 32B  │ │ - PII Tokens    │ │                     │
│ - Orgs      │ │ - vLLM      │ │ - Statements    │ └─────────────────────┘
│ - Analytics │ │             │ │ - Encryption    │
└─────────────┘ └─────────────┘ │   Keys          │
                                │                 │
                                │ ┌─────────────┐ │
                                │ │ SafeNet     │ │
                                │ │ eToken      │ │
                                │ │ (Hardware   │ │
                                │ │  MFA)       │ │
                                │ └─────────────┘ │
                                └─────────────────┘
```

---

## Feature Matrix

### Tier 1: Core (Free for All Veterans)

| Feature | Status | Description |
|---------|--------|-------------|
| VA Disability Calculator | ✅ Complete | 38 CFR 4.25 formula, bilateral factor |
| AI Chat with Council | ✅ Complete | 7-specialist validation |
| Educational Resources | ✅ Partial | Needs content seeding |
| User Authentication | ✅ Complete | Email/password, JWT |
| Basic Profile | ✅ Complete | Name, email |
| **Enhanced Profile** | 🔨 Building | Service history, VA status, dependents |
| **Claim Workbench** | 🔨 Building | Projects, checklists, notes |
| **Document Storage** | 🔨 Building | Encrypted on goldfin |
| **Form Wizards** | 📋 Planned | Guided claim filing |
| **MFA** | 📋 Planned | TOTP + hardware token |
| **Notifications** | 📋 Planned | Email reminders |
| **Accessibility** | 📋 Planned | WCAG 2.1 AA |

### Tier 2: VSO/Organization Features (Paid)

| Feature | Tier | Price | Description |
|---------|------|-------|-------------|
| Organization Account | Basic | $49/mo | Create org, invite 5 members |
| Member Management | Basic | - | Add/remove members |
| Basic Analytics | Basic | - | Usage counts |
| Extended Seats | Pro | $149/mo | 25 members |
| Advanced Analytics | Pro | - | Trends, top conditions |
| API Access | Pro | - | Integration capability |
| Custom Branding | Pro | - | Logo, colors |
| White Label | Enterprise | $499/mo | Full rebrand |
| Unlimited Seats | Enterprise | - | No member limit |
| Case Management | Enterprise | - | Client tracking |
| SLA & Support | Enterprise | - | Phone support, 99.9% uptime |

---

## Feature Deep Dives

### 1. Enhanced Veteran Profile

**Purpose**: Store veteran's service history and current VA status to auto-populate forms and personalize experience.

```
Profile Structure:
├── Basic Info (bluefin)
│   ├── Name, email, avatar
│   └── Profile completion %
│
├── Service History (bluefin)
│   ├── Branch: Army, Navy, USMC, USAF, USCG, Space Force
│   ├── Service dates
│   ├── MOS/Rating/AFSC
│   ├── Rank at discharge
│   ├── Discharge type
│   └── Combat veteran flag
│
├── Current VA Status (bluefin)
│   ├── Has VA rating? (yes/no)
│   ├── Combined rating (0-100%)
│   ├── Individual conditions + ratings
│   ├── Effective date
│   └── P&T status
│
├── Dependents (bluefin)
│   ├── Spouse (+ A&A flag)
│   ├── Children under 18
│   ├── Children 18-23 in school
│   └── Dependent parents
│
├── Personal PII (goldfin - encrypted)
│   ├── Date of Birth
│   ├── SSN (optional)
│   ├── VA File Number
│   ├── Phone
│   └── Address
│
└── Representation (bluefin)
    ├── Has VSO?
    ├── Organization name
    └── Rep contact info
```

**Auto-Population Benefits**:
- Calculator pre-fills dependents
- Wizards know service dates
- Checklists adapt to combat status
- Personal statements have context

---

### 2. Claim Workbench

**Purpose**: Veterans' private workspace to organize claim materials.

```
Workbench Structure:
├── My Claims
│   └── [Claim Project]
│       ├── Overview
│       │   ├── Claim type (new/increase/supplemental)
│       │   ├── Conditions being claimed
│       │   ├── Status (drafting → submitted → decided)
│       │   └── Progress indicator
│       │
│       ├── Evidence Checklist
│       │   ├── Auto-generated from conditions
│       │   ├── Required vs. recommended items
│       │   ├── Checkboxes with explanations
│       │   └── Links to upload documents
│       │
│       ├── My Documents
│       │   ├── Upload (drag & drop)
│       │   ├── Categories (medical, service, buddy, etc.)
│       │   ├── PII detection badges
│       │   └── View/Download/Delete
│       │
│       ├── Notes & Scratch Pad
│       │   ├── Rich text editor
│       │   ├── Auto-save
│       │   └── Encrypted on goldfin
│       │
│       ├── Personal Statement
│       │   ├── Wizard mode (guided questions)
│       │   ├── Edit mode (free-form)
│       │   ├── AI suggestions (optional)
│       │   └── Export as PDF/Word
│       │
│       └── Timeline
│           ├── Intent to File date
│           ├── Evidence gathered
│           ├── Submitted date
│           ├── C&P exam date
│           └── Decision date
│
├── All Documents
│   └── Cross-claim document library
│
├── Saved Calculations
│   └── Named calculator snapshots
│
└── Chat History
    └── Past conversations
```

**Document Storage Flow**:
```
Upload → Presidio PII Scan → Encrypt → Store on Goldfin
                ↓
        Metadata + Token Refs → Store on Bluefin
```

---

### 3. Form Wizards

**Purpose**: Step-by-step guidance through VA forms without crossing legal lines.

#### Intent to File Wizard (Simple, High Value)
```
Step 1: "Have you filed an Intent to File?"
        [Yes] → Record date, move to evidence
        [No]  → Explain importance, link to VA.gov/call
        [What's that?] → Educational explainer

Step 2: "What conditions do you want to claim?"
        → Add conditions from database
        → Auto-generate evidence checklist

Step 3: Summary
        → ITF date recorded
        → Conditions listed
        → Checklist generated
        → "Start gathering evidence" CTA
```

#### New Claim Wizard (21-526EZ Guidance)
```
Step 1: Intent to File (as above)

Step 2: Service Connection
        For each condition:
        ├── "When did symptoms start?"
        │   [During service / Within 1 year / Later]
        ├── "Is this in your service treatment records?"
        │   [Yes / No / Unsure]
        └── "Do you have a current diagnosis?"
            [Yes / No / Need one]

Step 3: Evidence Inventory
        Auto-generated checklist with:
        ☐ DD-214
        ☐ Service Treatment Records
        ☐ Current diagnosis for [condition]
        ☐ Nexus letter (if needed)
        ☐ Buddy statements
        ☐ Personal statement

Step 4: Buddy Statements
        "Who can corroborate your condition?"
        → Generate template with their info

Step 5: Personal Statement
        Guided questions:
        ├── "Describe the incident/cause..."
        ├── "How does this affect your work?"
        ├── "How does this affect relationships?"
        └── "Describe your worst days..."
        → AI helps organize into statement

Step 6: Review & Next Steps
        Full summary with:
        ├── All evidence gathered
        ├── What's still needed
        └── "Ready to file" instructions
```

#### Increase/Re-evaluation Wizard
```
Step 1: Which condition?
        → Select from current ratings

Step 2: Current vs. Target
        "You're at 50%. Next level is 70%."
        "Here's what 70% requires: [criteria]"

Step 3: Worsening Evidence
        ├── "How has it gotten worse?"
        ├── "New symptoms since last exam?"
        └── "Recent medical visits?"

Step 4: Medical Documentation
        ├── "Get updated records showing..."
        └── "Talking points for your doctor..."

Step 5: Personal Statement
        "Describe how it's worse now vs. when rated..."

Step 6: File for Increase
        Instructions for 21-526EZ increase
```

---

### 4. Multi-Factor Authentication (MFA)

**Council Recommendation**: Required given PII storage.

#### MFA Options

| Method | Security | Usability | Implementation |
|--------|----------|-----------|----------------|
| **TOTP App** | High | Medium | Google Auth, Authy |
| **Email Code** | Medium | High | Simple, accessible |
| **SMS Code** | Medium | High | Twilio integration |
| **Hardware Token** | Very High | Low | SafeNet eToken (admin) |
| **Passkey/WebAuthn** | Very High | High | Future consideration |

#### Implementation Plan

```
Standard Users:
├── TOTP (recommended) - Google Authenticator / Authy
├── Email code (fallback) - 6-digit, 10 min expiry
└── "Remember this device" - 30 days

PII Access:
├── Always require MFA to view SSN/DOB/Address
├── Even if "remembered", re-verify for PII
└── All access logged

Admin/TPM:
├── SafeNet eToken (hardware)
├── Required for goldfin direct access
└── PKI certificate authentication
```

#### SafeNet eToken Integration

From previous goldfin setup:
```
Hardware: SafeNet eToken 5110
Location: goldfin (old) - needs migration to new goldfin
Use cases:
├── TPM admin access to PII vault
├── Emergency PII recovery
├── Key ceremony for encryption keys
└── Audit log signing
```

**Migration Task**: Move eToken PKI setup to new goldfin on VLAN 20.

---

### 5. Notification System

**Council Recommendation**: Real-time updates and reminders.

#### Notification Types

| Trigger | Channel | Message |
|---------|---------|---------|
| ITF expiring (30 days) | Email | "Your Intent to File expires on [date]" |
| ITF expiring (7 days) | Email + In-app | "URGENT: ITF expires in 7 days" |
| Document uploaded | In-app | "Document uploaded successfully" |
| Checklist complete | In-app | "All evidence gathered! Ready to file?" |
| C&P exam reminder | Email | "Your C&P exam is in 3 days" |
| Claim status (manual) | In-app | "You updated status to: Submitted" |
| New educational content | Email (opt-in) | "New guide: PTSD Evidence Tips" |
| VSO: Member joined | Email | "[Name] joined your organization" |

#### Implementation

```python
# Notification service
class NotificationService:
    async def send(
        self,
        user_id: UUID,
        notification_type: str,
        title: str,
        message: str,
        channels: List[str] = ["in_app"],
        data: dict = None
    ):
        # Store in-app notification
        if "in_app" in channels:
            await self.store_notification(user_id, title, message, data)

        # Send email if enabled
        if "email" in channels:
            user = await self.get_user(user_id)
            if user.email_notifications_enabled:
                await self.send_email(user.email, title, message)

        # Future: SMS, push
```

#### User Preferences

```
/dashboard/settings/notifications
├── Email notifications: [On/Off]
├── Reminder frequency: [Daily digest / Immediate / Weekly]
├── Notify me about:
│   ☑ ITF expiration reminders
│   ☑ Claim status changes
│   ☑ Document upload confirmations
│   ☐ New educational content
│   ☐ VetAssist updates
└── Quiet hours: [10pm - 8am]
```

---

### 6. Accessibility (A11y)

**Council Recommendation**: Build for veterans with disabilities.

#### WCAG 2.1 AA Compliance Checklist

| Criterion | Requirement | Implementation |
|-----------|-------------|----------------|
| 1.1.1 | Non-text content has alt text | All images, icons |
| 1.3.1 | Info conveyed through structure | Semantic HTML |
| 1.4.1 | Color not sole indicator | Icons + text |
| 1.4.3 | Contrast ratio 4.5:1 | Verify all colors |
| 1.4.4 | Text resizable to 200% | Responsive design |
| 2.1.1 | Keyboard accessible | Tab navigation |
| 2.4.1 | Skip navigation | Skip links |
| 2.4.4 | Link purpose clear | Descriptive links |
| 3.1.1 | Page language declared | `lang="en"` |
| 3.3.1 | Error identification | Clear error messages |
| 4.1.2 | Name, role, value | ARIA labels |

#### Accessibility Features

```
1. Screen Reader Support
   ├── ARIA labels on all interactive elements
   ├── Semantic HTML (nav, main, article, etc.)
   ├── Skip to main content link
   └── Announce dynamic content changes

2. Visual Accommodations
   ├── High contrast mode toggle
   ├── Large text mode (150%)
   ├── Reduced motion option
   └── Focus indicators visible

3. Motor Accommodations
   ├── Full keyboard navigation
   ├── Large click targets (44px min)
   ├── No time limits on forms
   └── Drag-and-drop has keyboard alternative

4. Cognitive Accommodations
   ├── Plain language (no jargon without explanation)
   ├── Progress indicators on multi-step forms
   ├── Confirmation before destructive actions
   └── Save draft automatically

5. Future: Voice Input
   ├── Voice commands for navigation
   └── Dictation for personal statements
```

#### Testing Plan

```
1. Automated: axe-core, Lighthouse accessibility audit
2. Manual: Keyboard-only navigation test
3. Screen reader: NVDA (Windows), VoiceOver (Mac/iOS)
4. User testing: Recruit veterans with disabilities
```

---

## Database Schema Additions

### New Tables Summary

```sql
-- Bluefin (main database)
veteran_profiles        -- Service history, VA status, dependents
user_claims            -- Claim workbench projects
user_documents         -- Document metadata (files on goldfin)
claim_checklists       -- Evidence checklists
claim_timeline         -- Milestone tracking
organizations          -- VSO/org accounts
organization_members   -- Org membership
organization_invites   -- Pending invites
organization_analytics -- Usage metrics
notifications          -- In-app notifications
notification_preferences -- User settings
mfa_devices            -- TOTP devices

-- Goldfin (PII vault)
veteran_pii            -- Encrypted personal info
documents              -- Encrypted file storage
pii_tokens             -- Tokenized PII references
encrypted_notes        -- Claim notes
personal_statements    -- Statement drafts
document_access_log    -- Audit trail
pii_access_log         -- PII access audit
```

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
```
Week 1:
├── [ ] Enhanced veteran profile (bluefin schema)
├── [ ] Goldfin PII table setup
├── [ ] Profile UI with sections
├── [ ] Profile API endpoints

Week 2:
├── [ ] Claim workbench structure
├── [ ] Basic claim CRUD
├── [ ] Notes/scratch pad (encrypted)
├── [ ] Dashboard layout
```

### Phase 2: Documents & Security (Weeks 3-4)
```
Week 3:
├── [ ] Document upload to goldfin
├── [ ] Presidio PII scanning
├── [ ] Encryption implementation
├── [ ] Document list/download UI

Week 4:
├── [ ] MFA setup (TOTP)
├── [ ] MFA enrollment flow
├── [ ] PII reveal with MFA
├── [ ] SafeNet eToken migration
```

### Phase 3: Smart Features (Weeks 5-6)
```
Week 5:
├── [ ] Evidence checklist auto-generation
├── [ ] Checklist UI with explanations
├── [ ] Intent to File wizard
├── [ ] Timeline component

Week 6:
├── [ ] Personal statement wizard
├── [ ] AI-assisted statement drafts
├── [ ] Export to PDF/Word
├── [ ] New claim wizard
```

### Phase 4: Organizations & Notifications (Weeks 7-8)
```
Week 7:
├── [ ] Organization accounts
├── [ ] Member invite flow
├── [ ] Org dashboard
├── [ ] CVMA pilot setup

Week 8:
├── [ ] Notification service
├── [ ] Email integration
├── [ ] ITF reminders
├── [ ] User preferences
```

### Phase 5: Polish & Accessibility (Weeks 9-10)
```
Week 9:
├── [ ] WCAG 2.1 AA audit
├── [ ] High contrast mode
├── [ ] Keyboard navigation
├── [ ] Screen reader testing

Week 10:
├── [ ] Mobile responsive polish
├── [ ] Performance optimization
├── [ ] User testing
├── [ ] Bug fixes
```

---

## Success Metrics

### User Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Profile completion | >70% | % users with profile >50% complete |
| Claims created | 100+ | Claims in workbench |
| Documents uploaded | 500+ | Files in goldfin |
| Wizard completion | >60% | % who finish wizard |
| MFA adoption | >50% | % users with MFA enabled |

### Quality Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| Accessibility score | >90 | Lighthouse a11y audit |
| PII incidents | 0 | Any unauthorized access |
| Uptime | 99.5% | System availability |
| Page load | <2s | Core pages |

### Business Metrics
| Metric | Target | Measurement |
|--------|--------|-------------|
| CVMA pilot users | 10+ | Active CVMA members |
| VSO signups | 5+ | Organizations created |
| Paid conversions | 2+ | Basic tier subscribers |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| PII breach | Low | Critical | Goldfin isolation, encryption, MFA |
| Legal challenge | Low | High | Clear disclaimers, no UPL |
| Low adoption | Medium | Medium | CVMA pilot, word of mouth |
| Feature creep | Medium | Medium | Phased approach, MVP focus |
| Accessibility gaps | Medium | Medium | Early testing, user feedback |

---

## Council Wisdom

> *"The river that never floods forgets how to flow."*
> — Turtle Specialist

**Interpretation**: Don't let VetAssist become static. Continue evolving based on veteran feedback. The platform should flow and adapt like water, meeting veterans where they are.

---

## Seven Generations Impact

This platform is built to serve:

1. **Today's Veterans** - Immediate claims assistance
2. **Tomorrow's Veterans** - Younger generation inherits better tools
3. **Veteran Families** - Spouses and children understand benefits
4. **VSOs** - Organizations better equipped to serve
5. **Future Developers** - Open patterns for similar platforms
6. **AI Community** - Ethical AI serving vulnerable populations
7. **Society** - Veterans served = stronger communities

---

## Approval

| Role | Name | Status |
|------|------|--------|
| TPM | Darrell | ✅ Approved |
| Council | 7 Specialists | ✅ PROCEED (82.5%) |
| Product Owner | Dr. Joe Bigma | Pending |
| Pilot Partner | CVMA | Pending |

---

*Cherokee AI Federation - For the Seven Generations*
*"Your claim. Your documents. Your control."*

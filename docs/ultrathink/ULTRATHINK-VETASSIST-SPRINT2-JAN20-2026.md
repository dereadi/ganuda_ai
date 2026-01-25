# ULTRATHINK: VetAssist Sprint 2 - Authentication, PDF Export, Dashboard

**Date**: January 20, 2026
**Council Audit Hash**: 3b690ed593a16433
**Confidence**: 87.4% (High)
**TPM Status**: Approved

## Council Decision

The 7-Specialist Council voted on the next three priorities for VetAssist MVP:

| Priority | Feature | Rationale |
|----------|---------|-----------|
| 1 | Authentication Integration | Security foundation - veterans' PII requires proper auth |
| 2 | PDF Generation/Export | Veterans need printable/submittable claim documents |
| 3 | Veteran Dashboard | Session persistence enables claim completion over time |

### Turtle's 7-Generation Concern
The data we collect from veterans (SSN, medical conditions, service history) will persist. We must ensure:
- Data minimization principles
- Clear retention policies
- Veteran control over their data
- Encryption at rest and in transit

## Architecture Decisions

### 1. Authentication Integration

**Approach**: JWT-based auth with session management

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Auth API   │────▶│  PostgreSQL │
│  (Next.js)  │     │  (FastAPI)  │     │  (Users)    │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │
       │              JWT Token
       ▼                   │
┌─────────────┐            │
│   Wizard    │◀───────────┘
│   Sessions  │
└─────────────┘
```

**Database Schema**:
```sql
CREATE TABLE vetassist_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    email_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP
);

CREATE TABLE vetassist_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES vetassist_users(id),
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Endpoints**:
- `POST /api/v1/auth/register` - Create account
- `POST /api/v1/auth/login` - Get JWT token
- `POST /api/v1/auth/logout` - Invalidate session
- `POST /api/v1/auth/refresh` - Refresh token
- `GET /api/v1/auth/me` - Get current user

### 2. PDF Generation/Export

**Approach**: Server-side PDF generation using ReportLab or WeasyPrint

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Wizard    │────▶│  PDF API    │────▶│   Storage   │
│  Complete   │     │  (Python)   │     │  /exports/  │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  VA Form    │
                    │  Templates  │
                    └─────────────┘
```

**Form Templates**:
- 21-526EZ: Application for Disability Compensation
- 21-0995: Supplemental Claim
- 20-0996: Higher-Level Review
- 10182: Board of Veterans Appeals

**Endpoints**:
- `GET /api/v1/wizard/{session_id}/export/pdf` - Generate filled PDF
- `GET /api/v1/wizard/{session_id}/export/summary` - Generate summary doc

### 3. Veteran Dashboard

**Approach**: React dashboard with session management

```
┌────────────────────────────────────────────────────┐
│                 Veteran Dashboard                   │
├────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │
│  │ Active Claims│  │  Completed   │  │ Resources│ │
│  │    (3)       │  │    (2)       │  │          │ │
│  └──────────────┘  └──────────────┘  └──────────┘ │
├────────────────────────────────────────────────────┤
│  Claim: 21-526EZ          Status: In Progress      │
│  Started: Jan 15, 2026    Step: 3/5 (Conditions)   │
│  [Continue] [Delete]                               │
├────────────────────────────────────────────────────┤
│  Claim: 21-0995           Status: Complete         │
│  Completed: Jan 18, 2026  [Download PDF] [View]    │
└────────────────────────────────────────────────────┘
```

**Endpoints**:
- `GET /api/v1/dashboard/claims` - List user's wizard sessions
- `GET /api/v1/dashboard/stats` - User statistics
- `DELETE /api/v1/wizard/{session_id}` - Delete session

## Security Requirements (Addressing Turtle's Concern)

1. **PII Protection**:
   - All PII fields encrypted at rest (AES-256)
   - SSN stored as salted hash, never in plain text
   - Presidio PII scanning on all inputs

2. **Data Retention**:
   - Active sessions: 90 days
   - Completed claims: 7 years (VA record requirements)
   - Abandoned sessions: 30 days then purge

3. **Veteran Control**:
   - Export all data (GDPR-style)
   - Delete account and all data
   - View audit log of data access

## Implementation Order

```
Week 1: Authentication
├── Database schema
├── Auth endpoints
├── JWT middleware
├── Frontend login/register pages
└── Protect wizard routes

Week 2: PDF Generation
├── Install ReportLab/WeasyPrint
├── Create form templates
├── Map wizard data to form fields
├── Export endpoint
└── Download UI on completion page

Week 3: Dashboard
├── Dashboard page layout
├── Claims list component
├── Session management
├── Stats/progress display
└── Integration testing
```

## Success Metrics

- Authentication: < 500ms login response
- PDF Generation: < 5 seconds for full form
- Dashboard: < 2 seconds page load
- Security: Pass OWASP Top 10 audit

## Dependencies

- `python-jose` - JWT handling
- `passlib` - Password hashing
- `reportlab` or `weasyprint` - PDF generation
- `bcrypt` - Password encryption

---

*Council Consensus: PROCEED*
*7-Generation Review: Data stewardship protocols required*

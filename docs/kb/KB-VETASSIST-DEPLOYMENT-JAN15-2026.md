# KB-VETASSIST-DEPLOYMENT-JAN15-2026

## VetAssist Platform Production Deployment

**Date:** January 15, 2026
**Author:** TPM (Claude Opus 4.5)
**Status:** PRODUCTION
**Council Approval:** Pending final review

---

## Overview

VetAssist is a full-stack web application helping U.S. veterans navigate VA disability claims. Deployed on the Cherokee AI Federation infrastructure with Council-validated AI responses.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      VETASSIST STACK                         │
├─────────────────────────────────────────────────────────────┤
│  Frontend (Next.js 14.1.0)          │  redfin:3000          │
│  Backend (FastAPI/uvicorn)          │  redfin:8001          │
│  vLLM (Qwen2.5-Coder-32B-AWQ)       │  redfin:8000          │
│  LLM Gateway (Council)              │  redfin:8080          │
│  PostgreSQL (triad_federation)      │  bluefin:5432         │
└─────────────────────────────────────────────────────────────┘
```

## Access URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://192.168.132.223:3000 | User interface |
| Backend API | http://192.168.132.223:8001 | REST API |
| API Docs | http://192.168.132.223:8001/api/docs | Swagger docs |
| Health Check | http://192.168.132.223:8001/health | Service health |

## Features

### 1. VA Combined Rating Calculator
- Implements 38 CFR 4.25 formula
- Sorts ratings highest to lowest
- Applies bilateral factor where applicable
- Returns raw combined (frontend rounds to nearest 10%)

**API Endpoint:** `POST /api/v1/calculator/calculate`
```json
{
  "conditions": [
    {"name": "PTSD", "rating": 70},
    {"name": "Back", "rating": 20},
    {"name": "Tinnitus", "rating": 10}
  ]
}
```

### 2. AI Chat with Council Validation
- 7-Specialist Council validates responses
- Citations to VA regulations (38 CFR)
- Session-based conversation history
- Specialist attribution (Raven, Turtle, etc.)

**API Endpoint:** `POST /api/v1/chat/message`
```json
{
  "session_id": "uuid",
  "content": "What evidence do I need for PTSD?"
}
```

### 3. Educational Resources
- Articles about VA claims process
- Evidence requirements by condition
- Step-by-step filing guides

## Database Schema

### Core Tables (triad_federation on bluefin)

| Table | Records | Purpose |
|-------|---------|---------|
| users | 2 | User accounts |
| chat_sessions | 2+ | Chat session tracking |
| chat_messages | 4+ | Message history |
| council_validations | - | Council vote records |
| vetassist_conditions | 297 | VA disability conditions |
| vetassist_evidence_matrix | 19 | Evidence checklists |
| va_compensation_rates | 10 | 2025 compensation rates |
| educational_content | 9 | Educational articles |
| vetassist_test_veterans | 5 | Test data |
| vetassist_test_disabilities | 19 | Test disabilities |

## Configuration Files

### Backend (.env)
```
Location: /ganuda/vetassist/backend/.env
Database: postgresql://claude:***@192.168.132.222:5432/triad_federation
vLLM: http://localhost:8000/v1
Council: Enabled
```

### Frontend (.env.local)
```
Location: /ganuda/vetassist/frontend/.env.local
API URL: http://localhost:8001/api/v1
Environment: production
```

### Systemd Services
```
/etc/systemd/system/vetassist-backend.service
/etc/systemd/system/vetassist-frontend.service
```

## Regression Test Results (Jan 15, 2026)

### Services (5/5 PASS)
- [x] Backend API (8001) - healthy
- [x] Frontend (3000) - all pages load
- [x] vLLM (8000) - model loaded
- [x] LLM Gateway (8080) - healthy
- [x] PostgreSQL (bluefin) - connected

### Calculator API (6/6 PASS)
| Input | Expected | Actual | Status |
|-------|----------|--------|--------|
| 70, 20, 10 | 78 | 78 | PASS |
| 50, 20, 10 | 64 | 64 | PASS |
| 50, 40, 10, 10 | 75 | 75 | PASS |
| 100 | 100 | 100 | PASS |
| 10 | 10 | 10 | PASS |
| 0 | 0 | 0 | PASS |

### Chat API (3/3 PASS)
- [x] Session creation
- [x] Message send/receive (Specialist: Raven, Confidence: 1.0)
- [x] Message retrieval

### Frontend Pages (6/6 PASS)
- [x] / (Home)
- [x] /calculator
- [x] /chat
- [x] /resources
- [x] /login
- [x] /register

## Test Data

### Test Veterans
| ID | Name | Branch | Conditions | Combined |
|----|------|--------|------------|----------|
| TV-001 | Marcus Johnson | Army | PTSD 70, Back 20, Tinnitus 10 | 80% |
| TV-002 | Sarah Williams | Navy | Apnea 50, Knees 20+10 | 60% |
| TV-003 | David Chen | Marines | PTSD 50, Back 40, Tinnitus 10, Knee 10 | 80% |
| TV-004 | Jessica Rodriguez | Air Force | Apnea 50, PTSD 30, Hearing 10, Tinnitus 10 | 70% |
| TV-005 | Robert Thompson | Army | PTSD 100 | 100% |

## Operations

### Start Services
```bash
sudo systemctl start vetassist-backend vetassist-frontend
```

### Check Status
```bash
systemctl status vetassist-backend vetassist-frontend
curl http://localhost:8001/health
```

### View Logs
```bash
tail -f /ganuda/vetassist/logs/backend.log
tail -f /ganuda/vetassist/logs/frontend.log
```

### Restart After Changes
```bash
sudo systemctl restart vetassist-backend
sudo systemctl restart vetassist-frontend
```

## Troubleshooting

### Port Already in Use
```bash
sudo pkill -f "uvicorn app.main:app"
sudo systemctl restart vetassist-backend
```

### Database Connection Failed
- Check bluefin is reachable: `ping 192.168.132.222`
- Verify credentials in `/ganuda/vetassist/backend/.env`
- Check PostgreSQL is running on bluefin

### Chat Not Responding
- Verify vLLM is running: `curl http://localhost:8000/v1/models`
- Check backend logs for Council errors
- Ensure session exists before sending messages

## Security Considerations

- PII handling needs Presidio integration (pending)
- SSL/HTTPS needed for production domain
- Rate limiting enabled (60 req/min)
- Input sanitization on all user content

## Related Documentation

- JR Instructions: `/ganuda/docs/jr_instructions/JR-VETASSIST-FRONTEND-DEPLOYMENT-JAN15-2026.md`
- PRD: `/ganuda/docs/vetassist/VetAssist-PRD-v3.md`
- Legal Disclaimers: `/ganuda/docs/vetassist/VetAssist-Legal-Disclaimers.md`

## Council Approvals

- VetAssist Phase 1 MVP: APPROVED 5-0-2 (2025-12-28)
- Production Deployment: Pending (Jan 15, 2026)

---

*Cherokee AI Federation - For the Seven Generations*

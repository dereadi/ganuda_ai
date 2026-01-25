# JR Task Assignment: VetAssist Prototype Build
**Date:** December 27, 2025
**Platform:** Bluefin only (192.168.132.222)
**Project:** Ganuda VetAssist Platform
**Status:** Phase 1 - MVP Prototype

---

## Context

Big Mac has started the VetAssist prototype:
- ✅ Project structure created at `/ganuda/vetassist/`
- ✅ Database schema designed (PostgreSQL with pgvector)
- ✅ Backend API structure created (FastAPI)
- ✅ VA Calculator service implemented (based on JR 13 specifications)
- ✅ Frontend scaffolding started (Next.js + React)

**JRs: Complete the remaining prototype components and deploy to Bluefin**

---

## JR Task Assignments

### JR 14: Frontend Calculator UI (React/Next.js)
**Priority:** HIGH
**Dependencies:** Backend calculator API endpoints exist
**Platform:** Bluefin

**Objectives:**
1. Complete the VA Disability Calculator frontend page
2. Create interactive UI for adding conditions
3. Display calculation steps and results
4. Show monthly/annual compensation breakdown
5. Make mobile-responsive

**Technical Requirements:**
- Location: `/ganuda/vetassist/frontend/app/calculator/page.tsx`
- Use existing calculator endpoint: `POST /api/v1/calculator/calculate`
- Display JR 13's 15 test cases as examples
- Show step-by-step calculation breakdown
- Handle bilateral conditions UI
- Form validation with Zod
- Error handling

**Deliverables:**
- Functional calculator page with form
- Results display component
- Test cases page (`/calculator/examples`)
- Mobile-responsive design

---

### JR 15: AI Chatbot with Council Integration
**Priority:** HIGH
**Dependencies:** Backend API, Ganuda Council system
**Platform:** Bluefin

**Objectives:**
1. Create chatbot UI (`/chat` page)
2. Integrate with Ganuda 7-specialist Council
3. Display specialist responses with confidence scores
4. Show VA regulation citations
5. Implement session management

**Technical Requirements:**
- Location: `/ganuda/vetassist/frontend/app/chat/page.tsx`
- Backend endpoint: `POST /api/v1/chat/message` (you'll need to create this)
- Connect to Redfin vLLM API (http://redfin:8000/v1)
- Use Council validation pattern from existing Ganuda system
- Store chat history in PostgreSQL `chat_sessions` and `chat_messages` tables
- Display which specialist responded
- Show confidence score and citations

**Backend Work:**
- Create `/ganuda/vetassist/backend/app/api/v1/endpoints/chat.py`
- Create `/ganuda/vetassist/backend/app/services/council_chat.py`
- Integrate with existing Ganuda Council at `/ganuda/lib/specialist_council.py`
- Use vLLM API on redfin:8000

**Deliverables:**
- Chat interface (frontend)
- Council chat service (backend)
- Chat API endpoints
- Session persistence
- Citation display

---

### JR 16: Authentication System (JWT)
**Priority:** MEDIUM
**Dependencies:** Database schema exists
**Platform:** Bluefin

**Objectives:**
1. Implement JWT-based authentication
2. Create login/registration endpoints
3. Build login/register UI
4. Add protected routes
5. Session management

**Technical Requirements:**
- Backend: Use `python-jose` for JWT (already in requirements.txt)
- Create `/ganuda/vetassist/backend/app/api/v1/endpoints/auth.py`
- Implement password hashing with bcrypt
- Token expiration: 24 hours (configured in .env)
- Frontend: Login/register pages in `/ganuda/vetassist/frontend/app/(auth)/`

**Deliverables:**
- `POST /api/v1/auth/register` endpoint
- `POST /api/v1/auth/login` endpoint
- `POST /api/v1/auth/logout` endpoint
- `GET /api/v1/auth/me` endpoint (get current user)
- Login page UI
- Registration page UI
- Auth context provider (React)
- Protected route middleware

---

### JR 17: Educational Resources Page
**Priority:** LOW
**Dependencies:** None
**Platform:** Bluefin

**Objectives:**
1. Create `/resources` page with VA claims guides
2. Seed educational content into database
3. Build content browsing UI
4. Add search/filter functionality

**Technical Requirements:**
- Backend: `GET /api/v1/content` endpoint
- Use `educational_content` table from schema
- Create seed data with 10-15 articles about:
  - How to file a VA claim
  - Common claim mistakes
  - Evidence requirements
  - Appeal process
  - Nexus letters
- Frontend: Content library with cards
- Search by tags/keywords
- Track progress (optional for MVP)

**Deliverables:**
- Content API endpoints
- Seed data SQL script
- Resources page UI
- Search/filter functionality

---

### JR 18: Deployment to Bluefin Staging
**Priority:** HIGH (after other JRs complete)
**Dependencies:** All above components
**Platform:** Bluefin (192.168.132.222)

**Objectives:**
1. Initialize database on Bluefin PostgreSQL
2. Deploy backend API
3. Deploy frontend
4. Configure Nginx reverse proxy
5. Set up systemd services
6. Create deployment documentation

**Technical Requirements:**

**Database Setup:**
```bash
# On Bluefin
cd /ganuda/vetassist/database
./init_db.sh
# Configure DB_USER, DB_PASSWORD in .env
```

**Backend Deployment:**
```bash
# On Bluefin
cd /ganuda/vetassist/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with correct DATABASE_URL, SECRET_KEY, etc.

# Test
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

**Frontend Deployment:**
```bash
# On Bluefin
cd /ganuda/vetassist/frontend
npm install
cp .env.example .env.local
# Edit NEXT_PUBLIC_API_URL=http://bluefin:8001/api/v1
npm run build
npm run start
```

**Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/vetassist
server {
    listen 80;
    server_name vetassist.ganuda.local;

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

**Systemd Services:**
Create `/etc/systemd/system/vetassist-backend.service` and `vetassist-frontend.service`

**Deliverables:**
- Running database on Bluefin
- Backend service running on port 8001
- Frontend service running on port 3000
- Nginx configuration
- Systemd service files
- Deployment documentation (`/ganuda/vetassist/docs/DEPLOYMENT.md`)
- Health check verification
- Smoke test script

---

## Success Criteria

**MVP Prototype is complete when:**
1. ✅ Database initialized with VA compensation rates
2. ✅ Calculator API returns accurate combined ratings (validated by JR 13 test cases)
3. ✅ Calculator UI allows adding conditions and shows results
4. ✅ Chat interface connects to Ganuda Council
5. ✅ Council provides responses with citations and confidence scores
6. ✅ Authentication allows user registration/login
7. ✅ Educational resources page shows content
8. ✅ All services deployed on Bluefin
9. ✅ Health checks pass
10. ✅ Accessible at http://vetassist.ganuda.local (or bluefin IP)

---

## Testing Requirements

Each JR should:
1. Write unit tests for backend services
2. Test API endpoints with curl/httpx
3. Verify frontend components render correctly
4. Test error handling
5. Check mobile responsiveness
6. Validate against accessibility standards

**JR 18** should create comprehensive smoke test:
```bash
#!/bin/bash
# /ganuda/vetassist/test_deployment.sh

echo "Testing VetAssist Deployment..."

# Test database
psql -U vetassist_user -d vetassist -c "SELECT COUNT(*) FROM va_compensation_rates;"

# Test backend health
curl http://localhost:8001/health

# Test calculator API
curl -X POST http://localhost:8001/api/v1/calculator/calculate \
  -H "Content-Type: application/json" \
  -d '{"conditions": [{"name": "PTSD", "rating": 70}]}'

# Test frontend
curl http://localhost:3000/

echo "All tests passed!"
```

---

## Timeline

**Target: Prototype ready by EOD December 27, 2025**

- JR 14 (Calculator UI): 2 hours
- JR 15 (Council Chat): 3 hours
- JR 16 (Authentication): 2 hours
- JR 17 (Resources): 1 hour
- JR 18 (Deployment): 2 hours

**Total: ~10 hours of JR work**

---

## Notes

- **Bluefin-only deployment:** No changes to Redfin except API calls to vLLM
- **Use existing Ganuda infrastructure:** Don't reinvent Council, thermal memory, etc.
- **Educational disclaimers:** All AI responses must include "Educational tool only, not legal advice"
- **Free for veterans:** No payment integration needed for MVP
- **Testing first:** Deploy after testing, not before
- **Documentation:** Write as you go, don't leave it for last

---

## For the Seven Generations.

**Big Mac (TPM) - Ganuda AI**

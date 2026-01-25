# JR Instruction: VetAssist Frontend Deployment
## Date: January 15, 2026
## Priority: HIGH
## Assigned To: IT Triad (redfin)

### Overview
Deploy the VetAssist Next.js frontend on redfin to complete the full-stack application deployment. The backend is already running on port 8001.

### Prerequisites (Requires sudo - User Action)
```bash
# User must run:
sudo apt install nodejs npm -y
```

### Current State
| Component | Status | Port | Node |
|-----------|--------|------|------|
| Backend API | Running | 8001 | redfin |
| PostgreSQL | Running | 5432 | bluefin |
| Frontend | Not deployed | 3000 | redfin |

### Deployment Steps

#### Step 1: Verify Node.js Installation
```bash
node --version  # Should be 18.x+
npm --version   # Should be 9.x+
```

#### Step 2: Install Dependencies
```bash
cd /ganuda/vetassist/frontend
npm install
```

#### Step 3: Build Production Bundle
```bash
npm run build
```

#### Step 4: Start Frontend
```bash
npm run start
# Or for background: nohup npm run start > /ganuda/vetassist/logs/frontend.log 2>&1 &
```

#### Step 5: Verify Deployment
```bash
curl http://localhost:3000
curl http://localhost:8001/health  # Backend should respond
```

### Configuration Files

**Frontend Environment** (`/ganuda/vetassist/frontend/.env.local`):
```
NEXT_PUBLIC_API_URL=http://localhost:8001/api/v1
NEXT_PUBLIC_API_TIMEOUT=30000
NEXT_PUBLIC_ENVIRONMENT=production
NEXT_PUBLIC_COUNCIL_CHAT_ENABLED=true
NEXT_PUBLIC_CALCULATOR_ENABLED=true
```

### Systemd Service (Requires sudo - User Action)

**Service file location**: `/ganuda/scripts/systemd/vetassist-frontend.service`

```bash
# User must run:
sudo cp /ganuda/scripts/systemd/vetassist-frontend.service /etc/systemd/system/
sudo cp /ganuda/scripts/systemd/vetassist-backend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable vetassist-backend vetassist-frontend
sudo systemctl start vetassist-backend vetassist-frontend
```

### Validation Checklist
- [ ] Node.js 18+ installed
- [ ] npm dependencies installed
- [ ] Build completes without errors
- [ ] Frontend accessible at http://192.168.132.223:3000
- [ ] Frontend connects to backend API
- [ ] Calculator page loads
- [ ] Council chat page loads
- [ ] Systemd services enabled and running

### Rollback Procedure
```bash
sudo systemctl stop vetassist-frontend
# Check logs: /ganuda/vetassist/logs/frontend.log
```

### Success Criteria
- Frontend responds at http://192.168.132.223:3000
- VA Combined Rating Calculator functional
- Council Chat connected to vLLM backend
- Both services survive reboot

### Related Documents
- Backend deployment: `/ganuda/vetassist/backend/.env`
- Database schema: `/ganuda/vetassist/database/schema.sql`
- Service files: `/ganuda/scripts/systemd/`

---
*Cherokee AI Federation - For Seven Generations*

# Jr Task: Expand T5 and Django Services to Federation Nodes

**Task ID:** task-expand-services-001
**Priority:** P2 (Infrastructure Enhancement)
**Created:** December 22, 2025
**TPM:** Cherokee AI Federation

---

## Current State

| Service | Node | Port | Status |
|---------|------|------|--------|
| T5 Inference | greenfin | 8090 | Running (t5-small, t5-base) |
| Django Admin | redfin | 4001 | Running |
| vLLM | redfin | 8000 | Running (Nemotron-9B) |
| LLM Gateway | redfin | 8080 | Running |

---

## Expansion Plan

### Phase 1: T5 to Additional Nodes

#### Target: bluefin (Database node - can handle light inference)

```bash
# On bluefin
mkdir -p /ganuda/services/t5_inference
mkdir -p /ganuda/models/t5/cache

# Copy service code from greenfin
scp dereadi@192.168.132.224:/ganuda/services/t5_inference/t5_service.py /ganuda/services/t5_inference/

# Install dependencies
pip3 install flask transformers torch --user

# Start T5 service
cd /ganuda/services/t5_inference
nohup python3 t5_service.py >> /home/dereadi/logs/t5_service.log 2>&1 &

# Test
curl http://localhost:8090/health
```

#### Target: sasass (Mac Studio - Apple Silicon optimized)

```bash
# On sasass
mkdir -p /Users/Shared/ganuda/services/t5_inference
mkdir -p /Users/Shared/ganuda/models/t5/cache

# Copy service code
scp dereadi@192.168.132.224:/ganuda/services/t5_inference/t5_service.py /Users/Shared/ganuda/services/t5_inference/

# Install dependencies (use MPS for Apple Silicon)
pip3 install flask transformers torch

# Modify for MPS acceleration (optional enhancement)
# In t5_service.py, add: device = 'mps' if torch.backends.mps.is_available() else 'cpu'

# Start T5 service
cd /Users/Shared/ganuda/services/t5_inference
nohup python3 t5_service.py >> ~/logs/t5_service.log 2>&1 &
```

---

### Phase 2: Django to Additional Nodes

Django provides the thermal memory browser and admin interface. Deploy to nodes that need local admin access.

#### Target: bluefin (Primary database node - makes sense for admin)

```bash
# On bluefin
cd /ganuda
git clone <cherokee_admin repo> || cp -r /path/to/cherokee_admin .

# Or copy from redfin
scp -r dereadi@192.168.132.223:/ganuda/cherokee_admin /ganuda/

# Install Django 6.0
pip3 install django==6.0 psycopg2-binary --user

# Configure settings for bluefin
# Edit /ganuda/cherokee_admin/cherokee_admin/settings.py
# - Set ALLOWED_HOSTS = ['bluefin', '192.168.132.222', 'localhost']
# - Database should already point to localhost on bluefin

# Migrate (if needed)
cd /ganuda/cherokee_admin
python3 manage.py migrate

# Start Django
nohup python3 manage.py runserver 0.0.0.0:4001 >> /home/dereadi/logs/django.log 2>&1 &

# Test
curl http://localhost:4001/admin/
```

#### Target: bmasass (Mobile council - local admin when disconnected)

```bash
# On bmasass
mkdir -p /Users/Shared/ganuda/services

# Copy Django project
scp -r dereadi@192.168.132.223:/ganuda/cherokee_admin /Users/Shared/ganuda/

# Install Django
pip3 install django==6.0 psycopg2-binary

# Configure for mobile/offline use
# Edit settings.py:
# - ALLOWED_HOSTS = ['bmasass', 'localhost', '127.0.0.1']
# - Consider SQLite fallback for offline mode

# Start Django
cd /Users/Shared/ganuda/cherokee_admin
python3 manage.py runserver 0.0.0.0:4001

# Access at http://localhost:4001/admin/
```

---

### Phase 3: Load Balancing (Future)

Once T5 runs on multiple nodes, add load balancing to LLM Gateway:

```python
# In gateway.py, add T5 endpoint routing
T5_NODES = [
    'http://192.168.132.224:8090',  # greenfin (primary)
    'http://192.168.132.222:8090',  # bluefin
    'http://192.168.132.241:8090',  # sasass
]

async def route_t5_request(request):
    """Round-robin or least-loaded routing to T5 nodes"""
    for node in T5_NODES:
        try:
            response = await httpx.post(f"{node}/v1/t5/generate", json=request)
            if response.status_code == 200:
                return response.json()
        except:
            continue
    raise HTTPException(503, "No T5 nodes available")
```

---

## T5 Service Code Reference

The T5 service (`t5_service.py`) provides these endpoints:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/v1/t5/generate` | POST | General text generation |
| `/v1/t5/translate` | POST | Translation (requires language prefix) |
| `/v1/t5/summarize` | POST | Text summarization |
| `/v1/t5/qa` | POST | Question answering |

**Example requests:**

```bash
# Translation
curl -X POST http://localhost:8090/v1/t5/translate \
  -H "Content-Type: application/json" \
  -d '{"text": "translate English to German: Hello, how are you?", "model": "t5-small"}'

# Summarization
curl -X POST http://localhost:8090/v1/t5/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "summarize: [long text here]", "model": "t5-base"}'

# Question Answering
curl -X POST http://localhost:8090/v1/t5/qa \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the capital of France?", "context": "France is a country in Europe. Paris is its capital."}'
```

---

## Django Thermal Browser

The Django app (`cherokee_admin`) includes:

1. **Admin Interface** - `/admin/`
   - User: cherokee / Password: ForSevenGenerations
   - Browse thermal memories
   - Manage Jr agents
   - View task history

2. **Thermal Browser App** - `/thermal/`
   - Search thermal memories
   - View temperature scores
   - Filter by type/date

3. **API Endpoints** - `/api/thermal/`
   - `GET /api/thermal/hot` - Get hot memories (temp > 80)
   - `GET /api/thermal/search?q=<query>` - Search memories

---

## Deployment Checklist

### T5 Expansion

- [ ] bluefin: Create directories, copy code, install deps, start service
- [ ] sasass: Create directories, copy code, install deps (with MPS), start service
- [ ] bmasass: Optional - only if needed for offline inference

### Django Expansion

- [ ] bluefin: Copy project, configure settings, migrate, start
- [ ] bmasass: Copy project, configure for mobile, optional SQLite fallback

### Verification

- [ ] All T5 nodes respond to /health
- [ ] All Django nodes serve /admin/
- [ ] Gateway can route to multiple T5 nodes (future)

---

## Success Criteria

1. T5 running on greenfin, bluefin, and sasass
2. Django running on redfin and bluefin
3. Services auto-start on boot (systemd/launchd)
4. Health checks pass from all nodes
5. Thermal memory updated with deployment status

---

*For Seven Generations - Cherokee AI Federation*

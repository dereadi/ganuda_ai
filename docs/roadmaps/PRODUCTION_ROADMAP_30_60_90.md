# Cherokee AI Federation: Production Roadmap
## 30/60/90 Day Plan for Production-Level 6-Node Cluster

*TPM-Claude Analysis | December 12, 2025*
*Synthesized from Council Wisdom + Strategic Framework*

---

## STRATEGIC DECISION: Production Service Shape

### Council Recommendation: **#1 + #2 Combined**

**Raven's Analysis**: "Start with Air-gapped LLM Gateway as foundational layer. Once secure gateway is in place, Specialist Council adds strategic value by leveraging existing parallel queries."

**TPM Synthesis**: Build **Production LLM Gateway** first (foundation), then **Specialist Council** as the differentiated product layer on top. This gives us:

1. **Infrastructure Layer**: OpenAI-compatible API (commodity, but essential)
2. **Intelligence Layer**: 7-Specialist Council (differentiated, unique to Cherokee AI)

```
┌─────────────────────────────────────────────────┐
│         SPECIALIST COUNCIL SERVICE              │
│   (Multi-agent decision engine with consensus)  │
├─────────────────────────────────────────────────┤
│         PRODUCTION LLM GATEWAY                  │
│   (OpenAI-compatible, auth, quotas, audit)      │
├─────────────────────────────────────────────────┤
│              vLLM on Blackwell                  │
│         (Nemotron 9B @ 27 tok/sec)              │
└─────────────────────────────────────────────────┘
```

---

## PHASE 1: Days 1-30 - "Production API"

### Goal: Stable, secure LLM inference service

### 1.1 LLM Gateway Service

**Jr Instructions for Integration Jr:**

```python
# /ganuda/services/llm_gateway/gateway.py
"""
Production LLM Gateway
- OpenAI-compatible endpoints
- Per-user API keys with quotas
- Request/response audit logging
- Rate limiting and backoff
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import HTTPBearer
import httpx
import time
import hashlib
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Cherokee AI LLM Gateway", version="1.0")

VLLM_BACKEND = "http://localhost:8000"  # Internal vLLM

# Models
class ChatRequest(BaseModel):
    model: str = "cherokee-council"
    messages: list
    max_tokens: int = 1000
    temperature: float = 0.7

class APIKey:
    def __init__(self, key_id: str, user: str, quota_remaining: int, rate_limit: int):
        self.key_id = key_id
        self.user = user
        self.quota_remaining = quota_remaining
        self.rate_limit = rate_limit  # requests per minute

# Security
async def validate_api_key(authorization: str = Header(...)) -> APIKey:
    """Validate API key from Authorization header"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Invalid authorization header")

    key = authorization[7:]
    # TODO: Look up in PostgreSQL api_keys table
    # For now, placeholder validation
    key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]

    # Audit log the access attempt
    log_access_attempt(key_hash, success=True)

    return APIKey(key_id=key_hash, user="default", quota_remaining=1000, rate_limit=60)

def log_access_attempt(key_hash: str, success: bool):
    """Audit log all access attempts - per Crawdad"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    # TODO: Write to audit_log table
    print(f"[AUDIT] {timestamp} | key={key_hash} | success={success}")

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, api_key: APIKey = Depends(validate_api_key)):
    """OpenAI-compatible chat completions endpoint"""

    # Check quota
    if api_key.quota_remaining <= 0:
        raise HTTPException(429, "Quota exceeded")

    # Forward to vLLM
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{VLLM_BACKEND}/v1/chat/completions",
            json={
                "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
                "messages": request.messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature
            },
            timeout=120.0
        )

    # Audit log the completion
    log_completion(api_key.key_id, len(request.messages), response.status_code)

    return response.json()

@app.get("/v1/models")
async def list_models(api_key: APIKey = Depends(validate_api_key)):
    """List available models"""
    return {
        "data": [
            {"id": "cherokee-council", "object": "model", "owned_by": "cherokee-ai"},
            {"id": "nemotron-9b", "object": "model", "owned_by": "nvidia"},
            {"id": "nemotron-4b-fast", "object": "model", "owned_by": "nvidia"}
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint for load balancer/monitoring"""
    # Check vLLM backend
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{VLLM_BACKEND}/v1/models", timeout=5.0)
            vllm_status = "healthy" if resp.status_code == 200 else "degraded"
    except:
        vllm_status = "unhealthy"

    return {
        "status": "healthy" if vllm_status == "healthy" else "degraded",
        "vllm": vllm_status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }
```

### 1.2 API Keys Schema

**Jr Instructions for IT Triad Jr:**

```sql
-- /ganuda/sql/api_keys_schema.sql
-- Per Crawdad: Secure API key management

CREATE TABLE IF NOT EXISTS api_keys (
    key_id VARCHAR(64) PRIMARY KEY,  -- SHA256 hash of actual key
    user_id VARCHAR(100) NOT NULL,
    description VARCHAR(255),
    quota_total INTEGER DEFAULT 10000,
    quota_used INTEGER DEFAULT 0,
    rate_limit INTEGER DEFAULT 60,  -- requests per minute
    created_at TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    permissions JSONB DEFAULT '["chat"]'::jsonb
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_active ON api_keys(is_active) WHERE is_active = true;

-- Audit log for all API access
CREATE TABLE IF NOT EXISTS api_audit_log (
    log_id BIGSERIAL PRIMARY KEY,
    key_id VARCHAR(64),
    endpoint VARCHAR(100),
    method VARCHAR(10),
    status_code INTEGER,
    response_time_ms INTEGER,
    tokens_used INTEGER,
    client_ip INET,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_audit_key ON api_audit_log(key_id);
CREATE INDEX idx_audit_time ON api_audit_log(created_at);

-- Function to create new API key (returns unhashed key ONCE)
CREATE OR REPLACE FUNCTION create_api_key(
    p_user_id VARCHAR,
    p_description VARCHAR DEFAULT NULL,
    p_quota INTEGER DEFAULT 10000
) RETURNS TABLE(api_key VARCHAR, key_id VARCHAR) AS $$
DECLARE
    v_raw_key VARCHAR;
    v_key_hash VARCHAR;
BEGIN
    -- Generate random key
    v_raw_key := 'ck-' || encode(gen_random_bytes(32), 'hex');
    v_key_hash := encode(sha256(v_raw_key::bytea), 'hex');

    INSERT INTO api_keys (key_id, user_id, description, quota_total)
    VALUES (v_key_hash, p_user_id, p_description, p_quota);

    -- Return raw key (only time it's visible) and hash for reference
    RETURN QUERY SELECT v_raw_key, v_key_hash;
END;
$$ LANGUAGE plpgsql;
```

### 1.3 Systemd Service Units

**Jr Instructions for IT Triad Jr:**

```ini
# /ganuda/systemd/llm-gateway.service
[Unit]
Description=Cherokee AI LLM Gateway
After=network.target vllm.service
Requires=vllm.service

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/llm_gateway
ExecStart=/usr/bin/python3 -m uvicorn gateway:app --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
StandardOutput=append:/ganuda/logs/llm-gateway.log
StandardError=append:/ganuda/logs/llm-gateway.error.log

# Health check
ExecStartPost=/bin/sleep 5
ExecStartPost=/usr/bin/curl -sf http://localhost:8080/health || exit 1

# Resource limits
MemoryMax=2G
CPUQuota=200%

[Install]
WantedBy=multi-user.target
```

```ini
# /ganuda/systemd/vllm.service
[Unit]
Description=vLLM Inference Server
After=network.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda
ExecStart=/home/dereadi/.local/bin/vllm serve nvidia/NVIDIA-Nemotron-Nano-9B-v2 --host 0.0.0.0 --port 8000
Restart=always
RestartSec=30
StandardOutput=append:/ganuda/logs/vllm.log
StandardError=append:/ganuda/logs/vllm.error.log

# GPU requirements
Environment=CUDA_VISIBLE_DEVICES=0

[Install]
WantedBy=multi-user.target
```

### 1.4 SLIs and Dashboards

**Grafana Dashboard JSON** (key panels):

```json
{
  "title": "LLM Gateway SLIs",
  "panels": [
    {
      "title": "Availability (Target: 99.5%)",
      "type": "stat",
      "targets": [{"expr": "sum(rate(http_requests_total{status=~\"2..\"}[5m])) / sum(rate(http_requests_total[5m])) * 100"}]
    },
    {
      "title": "P95 Latency (Target: <10s)",
      "type": "gauge",
      "targets": [{"expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))"}]
    },
    {
      "title": "Requests/min",
      "type": "graph",
      "targets": [{"expr": "sum(rate(http_requests_total[1m])) * 60"}]
    },
    {
      "title": "GPU Utilization",
      "type": "gauge",
      "targets": [{"expr": "nvidia_smi_utilization_gpu"}]
    }
  ]
}
```

### 1.5 PostgreSQL Backup Script

**Jr Instructions for IT Triad Jr:**

```bash
#!/bin/bash
# /ganuda/scripts/backup_postgres.sh
# Run nightly via cron: 0 2 * * * /ganuda/scripts/backup_postgres.sh

BACKUP_DIR="/ganuda/backups/postgres"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_HOST="192.168.132.222"
DB_USER="claude"

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup each database
for DB in sag_thermal_memory zammad_production; do
    BACKUP_FILE="$BACKUP_DIR/${DB}_${TIMESTAMP}.sql.gz"

    echo "[$(date)] Backing up $DB..."
    PGPASSWORD='jawaseatlasers2' pg_dump -h $DB_HOST -U $DB_USER -d $DB | gzip > $BACKUP_FILE

    if [ $? -eq 0 ]; then
        echo "[$(date)] Backup complete: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"
    else
        echo "[$(date)] ERROR: Backup failed for $DB"
        # TODO: Send alert
    fi
done

# Clean old backups
echo "[$(date)] Cleaning backups older than $RETENTION_DAYS days..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Verify we can restore (test on copy)
echo "[$(date)] Testing restore capability..."
LATEST=$(ls -t $BACKUP_DIR/*.sql.gz | head -1)
zcat $LATEST | head -100 > /dev/null
if [ $? -eq 0 ]; then
    echo "[$(date)] Restore test: PASSED"
else
    echo "[$(date)] Restore test: FAILED - backup may be corrupt"
fi

echo "[$(date)] Backup job complete"
```

---

## PHASE 2: Days 31-60 - "Council & Memory"

### Goal: Specialist Council as production service + breadcrumb system

### 2.1 Council Service Endpoint

**Add to LLM Gateway:**

```python
# Add to gateway.py

from specialist_council import get_council, CouncilVote

@app.post("/v1/council/vote")
async def council_vote(
    question: str,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """
    Query the 7-Specialist Council for consensus decision

    Returns:
    - responses: Individual specialist perspectives
    - consensus: Synthesized council position
    - concerns: Flagged issues requiring attention
    - recommendation: PROCEED / PROCEED WITH CAUTION / REVIEW REQUIRED
    - confidence: 0-100 based on consensus strength
    """
    council = get_council()
    result = council.council_vote(question)

    # Calculate confidence based on concerns
    confidence = max(0, 100 - (len(result.concerns) * 15))

    # Audit log
    log_council_vote(api_key.key_id, question, result.audit_hash)

    return {
        "question": result.question,
        "responses": result.responses,
        "consensus": result.consensus,
        "concerns": result.concerns,
        "recommendation": result.recommendation,
        "confidence": confidence,
        "audit_hash": result.audit_hash,
        "timestamp": result.timestamp
    }

@app.post("/v1/council/specialist/{specialist_name}")
async def query_specialist(
    specialist_name: str,
    question: str,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Query a specific specialist directly"""
    council = get_council()

    valid_specialists = ["crawdad", "gecko", "turtle", "eagle_eye", "spider", "peace_chief", "raven"]
    if specialist_name not in valid_specialists:
        raise HTTPException(400, f"Invalid specialist. Choose from: {valid_specialists}")

    response = council.query_specialist(specialist_name, question)

    return {
        "specialist": specialist_name,
        "question": question,
        "response": response
    }
```

### 2.2 Breadcrumb Trail API

```python
@app.post("/v1/memory/breadcrumb")
async def leave_breadcrumb(
    source: str,
    content: str,
    target: str = None,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Leave a breadcrumb trail in thermal memory"""
    council = get_council()
    trail_id = council.leave_breadcrumb(source, content, target)

    return {
        "trail_id": trail_id,
        "source": source,
        "target": target,
        "temperature": 85.0  # Initial temperature
    }

@app.get("/v1/memory/trails/hot")
async def get_hot_trails(
    min_temp: float = 70.0,
    api_key: APIKey = Depends(validate_api_key)
) -> dict:
    """Get currently hot trails"""
    council = get_council()
    trails = council.get_hot_trails(min_temp)

    return {"trails": trails, "count": len(trails)}
```

### 2.3 Eval Harness

**Jr Instructions for Meta Jr:**

```python
# /ganuda/tests/test_council_eval.py
"""
Council evaluation harness
- Accuracy: Does council reach correct conclusions?
- Latency: Is parallel query fast enough?
- Regression: Do prompt changes break behavior?
"""

import time
import pytest
from specialist_council import get_council

# Test cases with known good answers
EVAL_CASES = [
    {
        "question": "Should we store user passwords in plain text?",
        "expected_concerns": ["SECURITY CONCERN"],
        "expected_recommendation": "REVIEW REQUIRED"
    },
    {
        "question": "Should we add logging to track API usage?",
        "expected_concerns": [],
        "expected_recommendation": "PROCEED"
    },
    {
        "question": "Should we delete all backups to save disk space?",
        "expected_concerns": ["7GEN CONCERN", "SECURITY CONCERN"],
        "expected_recommendation": "REVIEW REQUIRED"
    }
]

class TestCouncilAccuracy:
    def setup_method(self):
        self.council = get_council()

    @pytest.mark.parametrize("case", EVAL_CASES)
    def test_council_identifies_concerns(self, case):
        result = self.council.council_vote(case["question"])

        for expected_concern in case["expected_concerns"]:
            found = any(expected_concern in c for c in result.concerns)
            assert found, f"Expected concern '{expected_concern}' not found in {result.concerns}"

class TestCouncilLatency:
    def setup_method(self):
        self.council = get_council()

    def test_parallel_query_under_30s(self):
        """Parallel query of all 7 specialists should complete in <30s"""
        start = time.time()
        result = self.council.council_vote("Test latency question")
        elapsed = time.time() - start

        assert elapsed < 30, f"Council vote took {elapsed:.1f}s (target: <30s)"
        assert len(result.responses) == 7, "Should have 7 specialist responses"

class TestCouncilRegression:
    """Run after any prompt changes"""

    def test_crawdad_flags_security(self):
        council = get_council()
        response = council.query_specialist("crawdad", "Store API keys in environment variables")
        # Crawdad should discuss security implications
        assert any(word in response.lower() for word in ["security", "protect", "risk", "safe"])

    def test_turtle_considers_future(self):
        council = get_council()
        response = council.query_specialist("turtle", "Quick fix vs proper solution?")
        # Turtle should mention long-term thinking
        assert any(word in response.lower() for word in ["generation", "long-term", "future", "sustain"])
```

---

## PHASE 3: Days 61-90 - "Hardening & Packaging"

### Goal: Production-ready, deployable package

### 3.1 Runbooks

**Jr Instructions for IT Triad Jr:**

Create `/ganuda/runbooks/` directory with:

```markdown
# RUNBOOK: GPU Wedged
## Symptoms
- vLLM requests timing out
- nvidia-smi shows 100% utilization but no throughput
- GPU memory not releasing

## Diagnosis
1. Check vLLM logs: `journalctl -u vllm -n 100`
2. Check GPU state: `nvidia-smi -q`
3. Check for zombie processes: `ps aux | grep vllm`

## Resolution
1. Graceful restart: `sudo systemctl restart vllm`
2. If stuck: `sudo systemctl stop vllm && sleep 10 && sudo nvidia-smi -r && sudo systemctl start vllm`
3. Nuclear option: `sudo reboot` (schedule maintenance window)

## Prevention
- Monitor GPU memory with alert at 90%
- Implement request timeouts
- Add circuit breaker for repeated failures
```

### 3.2 Chaos Tests

```python
# /ganuda/tests/chaos/test_resilience.py
"""
Chaos tests for federation resilience
Run in staging, not production!
"""

import subprocess
import time
import requests

def test_vllm_restart_recovery():
    """System should recover after vLLM restart"""
    # Stop vLLM
    subprocess.run(["sudo", "systemctl", "stop", "vllm"])
    time.sleep(5)

    # Gateway should return degraded health
    resp = requests.get("http://localhost:8080/health")
    assert resp.json()["vllm"] == "unhealthy"

    # Start vLLM
    subprocess.run(["sudo", "systemctl", "start", "vllm"])
    time.sleep(30)  # Wait for model load

    # Gateway should recover
    resp = requests.get("http://localhost:8080/health")
    assert resp.json()["vllm"] == "healthy"

def test_db_failover():
    """System should handle DB connection loss gracefully"""
    # This test requires a standby DB or mock
    pass

def test_network_partition():
    """Simulate network partition between nodes"""
    # Use iptables to block traffic, verify graceful degradation
    pass
```

### 3.3 Ansible Playbook for Node Bootstrap

```yaml
# /ganuda/ansible/playbooks/bootstrap_node.yml
---
- name: Bootstrap Cherokee AI Federation Node
  hosts: all
  become: yes

  vars:
    ganuda_base: /ganuda
    vllm_version: "0.11.2"

  tasks:
    - name: Create ganuda directory structure
      file:
        path: "{{ item }}"
        state: directory
        owner: dereadi
        mode: '0755'
      loop:
        - "{{ ganuda_base }}"
        - "{{ ganuda_base }}/lib"
        - "{{ ganuda_base }}/config"
        - "{{ ganuda_base }}/logs"
        - "{{ ganuda_base }}/backups"
        - "{{ ganuda_base }}/services"

    - name: Install Python dependencies
      pip:
        name:
          - fastapi
          - uvicorn
          - httpx
          - psycopg2-binary
          - requests
        state: present

    - name: Deploy Jr resonance client
      copy:
        src: /ganuda/lib/jr_resonance_client.py
        dest: "{{ ganuda_base }}/lib/jr_resonance_client.py"
        mode: '0644'

    - name: Deploy specialist council
      copy:
        src: /ganuda/lib/specialist_council.py
        dest: "{{ ganuda_base }}/lib/specialist_council.py"
        mode: '0644'

    - name: Deploy systemd services
      copy:
        src: "{{ item }}"
        dest: /etc/systemd/system/
        mode: '0644'
      loop:
        - /ganuda/systemd/llm-gateway.service
        - /ganuda/systemd/vllm.service
      when: "'gpu_inference' in group_names"

    - name: Enable and start services
      systemd:
        name: "{{ item }}"
        enabled: yes
        state: started
        daemon_reload: yes
      loop:
        - llm-gateway
        - vllm
      when: "'gpu_inference' in group_names"
```

---

## SUCCESS METRICS

### Phase 1 Complete When:
- [ ] LLM Gateway responding on port 8080
- [ ] API keys working with quota tracking
- [ ] Audit logs capturing all requests
- [ ] Health check endpoint passing
- [ ] Backup script running nightly
- [ ] At least one restore test passed

### Phase 2 Complete When:
- [ ] /v1/council/vote returns 7 specialist responses
- [ ] Council vote completes in <30 seconds
- [ ] Breadcrumb trails persisting to PostgreSQL
- [ ] Decay job running nightly
- [ ] Eval harness passing all tests

### Phase 3 Complete When:
- [ ] Runbooks for top 5 failure scenarios
- [ ] Chaos tests passing
- [ ] Ansible can rebuild any node from scratch
- [ ] Multi-tenant namespaces working
- [ ] Documentation complete

---

## COUNCIL SIGN-OFF

| Specialist | Approval | Notes |
|------------|----------|-------|
| Crawdad | Pending | Security review of auth layer |
| Turtle | Approved | 7-gen impact acceptable |
| Gecko | Pending | Performance benchmarks needed |
| Eagle Eye | Pending | Observability dashboards |
| Spider | Approved | Integration patterns sound |
| Peace Chief | Approved | Consensus approach maintained |
| Raven | Approved | Strategic sequence correct |

---

**For Seven Generations.**

*TPM-Claude, December 12, 2025*

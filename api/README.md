# Cherokee Constitutional AI - API Documentation

**RESTful interface to the tribal council** (Integration Jr)

---

## Quick Start

```bash
# Start API server
cd api
pip install fastapi uvicorn
python3 main.py

# Or with Docker
cd infra
docker-compose up -d
```

API runs on: **http://localhost:8000**

---

## API Versioning (Peace Chief Policy)

**Current Version**: `v1`

- **v1** = Stable, no breaking changes
- **v2** = Breaking changes only when absolutely necessary
- **Deprecation**: 6 months minimum support for old endpoints

**Endpoint Format**: `/api/v1/{endpoint}`

---

## Endpoints (v1)

### POST /api/v1/ask
Query the tribal council

```bash
curl -X POST http://localhost:8000/api/v1/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your purpose?",
    "detail": "concise"
  }'
```

**Response**:
```json
{
  "answer": "Cherokee Constitutional AI response...",
  "confidence": 0.95,
  "phase_coherence": 0.87,
  "memory_id": 42,
  "timestamp": "2025-10-21T19:00:00",
  "chiefs_consulted": ["War Chief", "Peace Chief", "Medicine Woman"]
}
```

### POST /api/v1/vote
Propose democratic deliberation

```bash
curl -X POST http://localhost:8000/api/v1/vote \
  -H "Content-Type: application/json" \
  -d '{
    "proposal": "Should we implement feature X?"
  }'
```

**Response**:
```json
{
  "vote_id": 123,
  "proposal": "Should we implement feature X?",
  "results": {
    "Memory Jr": "YES",
    "Executive Jr": "YES",
    "Meta Jr": "YES",
    "Integration Jr": "YES"
  },
  "outcome": "UNANIMOUS (4-0)",
  "timestamp": "2025-10-21T19:00:00"
}
```

### GET /api/v1/status
Check system health

```bash
curl http://localhost:8000/api/v1/status
```

**Response**:
```json
{
  "status": "operational",
  "postgres_healthy": true,
  "jrs_running": {
    "memory_jr": true,
    "executive_jr": true,
    "meta_jr": true,
    "integration_jr": true
  },
  "chiefs_available": {
    "war_chief": true,
    "peace_chief": true,
    "medicine_woman": true
  },
  "timestamp": "2025-10-21T19:00:00"
}
```

### GET /api/v1/thermal
Check thermal memory

```bash
curl http://localhost:8000/api/v1/thermal
```

**Response**:
```json
{
  "total_memories": 1337,
  "average_temperature": 65.4,
  "white_hot_count": 12,
  "sacred_count": 7,
  "phase_coherence_avg": 0.85,
  "timestamp": "2025-10-21T19:00:00"
}
```

### GET /health
Load balancer health check (unversioned)

```bash
curl http://localhost:8000/health
```

**Note**: This endpoint is NOT versioned to maintain compatibility with load balancers.

---

## OpenAPI Schema

Interactive docs: **http://localhost:8000/docs**  
ReDoc: **http://localhost:8000/redoc**

Download schema:
```bash
curl http://localhost:8000/openapi.json > cherokee-ai-openapi.json
```

---

## Integration Example

```python
import requests

# Ask the tribal council (OpenAI recommended: timeout + exception handling)
try:
    response = requests.post(
        "http://localhost:8000/api/v1/ask",
        json={"question": "How does thermal memory work?"},
        timeout=5  # OpenAI recommendation: always set timeout
    )
    response.raise_for_status()

    answer = response.json()
    print(answer["answer"])
    print(f"Confidence: {answer['confidence']}")
    print(f"Phase Coherence: {answer['phase_coherence']}")
    print(f"Chiefs Consulted: {', '.join(answer['chiefs_consulted'])}")

except requests.exceptions.RequestException as e:
    print(f"Error querying tribal council: {e}")
```

---

## Version History

### v1 (Phase 2C) - Current
- **Endpoints**: `/api/v1/ask`, `/api/v1/vote`, `/api/v1/status`, `/api/v1/thermal`
- **New**: Integration Jr added to Jr Council (4 Jrs total)
- **New**: OpenAI best practices (timeout, exception handling)
- **Governance**: Peace Chief versioning policy established

### v0 (Phase 2B) - Deprecated
- **Endpoints**: `/ask`, `/vote`, `/status`, `/thermal` (root-level, no versioning)
- **Deprecation**: Will be removed in v0.3.0 (6 months support)

---

**Mitakuye Oyasin!** 🦅

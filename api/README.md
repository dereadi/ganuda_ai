# Cherokee Constitutional AI - API Documentation

**RESTful interface to the tribal council**

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

## Endpoints

### POST /ask
Query the tribal council

```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is your purpose?",
    "detail": "concise"
  }'
```

### POST /vote
Propose democratic deliberation

```bash
curl -X POST http://localhost:8000/vote \
  -H "Content-Type: application/json" \
  -d '{
    "proposal": "Should we implement feature X?"
  }'
```

### GET /status
Check system health

```bash
curl http://localhost:8000/status
```

### GET /thermal
Check thermal memory

```bash
curl http://localhost:8000/thermal
```

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

# Ask the tribal council
response = requests.post(
    "http://localhost:8000/ask",
    json={"question": "How does thermal memory work?"}
)

answer = response.json()
print(answer["answer"])
print(f"Confidence: {answer['confidence']}")
```

---

**Mitakuye Oyasin!** 🦅

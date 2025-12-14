# Ganuda Gateway Quickstart

Get a private, OpenAI-compatible LLM API running in 5 minutes.

---

## Prerequisites

- Docker or Podman installed
- 4GB RAM minimum (8GB recommended)
- GPU optional (for local inference)

---

## Quick Install

```bash
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda
./scripts/quickstart.sh
```

That's it. The script auto-detects Docker or Podman and configures everything.

---

## Manual Install

```bash
# 1. Clone and enter directory
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda

# 2. Create configuration files
cp .env.example .env
cp config/ganuda.yaml.example config/ganuda.yaml

# 3. Edit .env with a secure database password
nano .env

# 4. Start services
docker-compose up -d   # or: podman-compose up -d

# 5. Verify
curl http://localhost:8080/health
```

---

## What You Get

| Service | Port | Description |
|---------|------|-------------|
| Gateway | 8080 | OpenAI-compatible API |
| PostgreSQL | 5432 | Audit logs & API keys (internal) |

---

## Your First API Call

### Using curl

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer gnd-admin-default-key" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Using Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="gnd-admin-default-key"
)

response = client.chat.completions.create(
    model="default",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

### Using JavaScript

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer gnd-admin-default-key'
  },
  body: JSON.stringify({
    model: 'default',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});
const data = await response.json();
console.log(data.choices[0].message.content);
```

---

## Configuration

All settings are in `config/ganuda.yaml`. Edit and restart to apply.

### Inference Backends

**External API (Default)**
```yaml
inference:
  backend: openai
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
```
Set `OPENAI_API_KEY` in your environment.

**Local vLLM (GPU Required)**
```yaml
inference:
  backend: vllm
  base_url: http://vllm:8000
  model: meta-llama/Llama-3.1-8B-Instruct
```
Uncomment the `vllm` service in `docker-compose.yml`.

### Apply Changes

```bash
# Edit config
nano config/ganuda.yaml

# Restart
docker-compose restart gateway

# Verify
curl http://localhost:8080/v1/config/current
```

---

## Managing API Keys

```bash
# List keys
docker-compose exec postgres psql -U ganuda -c \
  "SELECT id, name, created_at FROM api_keys WHERE is_active = true;"

# Create new key
docker-compose exec postgres psql -U ganuda -c \
  "INSERT INTO api_keys (key_hash, name) VALUES 
   (encode(sha256('my-new-key'::bytea), 'hex'), 'My App');"
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | `docker-compose ps` - is gateway running? |
| 401 Unauthorized | Check API key in Authorization header |
| 500 Internal Error | `docker-compose logs gateway` |
| Slow first response | Normal - model loading on first request |

---

## Stop & Cleanup

```bash
# Stop services
docker-compose down

# Stop and remove data
docker-compose down -v
```

---

## Next Steps

- [Configuration Reference](docs/CONFIGURATION.md)
- [API Documentation](docs/API.md)
- [Intelligence Modules](docs/MODULES.md)

---

*For Seven Generations - Cherokee AI Federation*

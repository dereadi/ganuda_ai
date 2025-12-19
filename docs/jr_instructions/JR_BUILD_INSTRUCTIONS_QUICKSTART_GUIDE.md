# Jr Build Instructions: Ganuda Quickstart Guide
## Priority: CRITICAL - Required for v1.0 User Experience

---

## Objective

Create a 3-page maximum user-facing quickstart guide that enables new users to:
1. Install Ganuda in < 5 minutes
2. Make their first API call
3. Understand configuration basics

**Principle**: Boring first. Make it work before making it brilliant.

---

## Target Audience

- Developers familiar with Docker
- Teams wanting private LLM inference
- Users migrating from OpenAI API

**NOT**: AI researchers, Cherokee Federation internals, advanced users

---

## Document Structure

### Page 1: Installation

Location: `/ganuda/docs/QUICKSTART.md` (Page 1 section)

```markdown
# Ganuda Gateway Quickstart

Get a private, OpenAI-compatible LLM API running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 8GB RAM minimum (16GB recommended)
- GPU optional (for local inference)

## Quick Install

```bash
# Clone repository
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda

# Copy example configuration
cp ganuda.yaml.example ganuda.yaml
cp .env.example .env

# Edit .env with your settings (at minimum, set a database password)
nano .env

# Start Ganuda
docker-compose up -d

# Verify it's running
curl http://localhost:8080/health
```

## What You Get

| Service | Port | Description |
|---------|------|-------------|
| Gateway API | 8080 | OpenAI-compatible chat completions |
| PostgreSQL | 5432 | Audit logging and API keys |

## Next Steps

- [Make Your First API Call →](#page-2-first-api-call)
- [Configure Your Instance →](#page-3-configuration)
```

### Page 2: First API Call

```markdown
## Your First API Call

Ganuda is OpenAI-compatible. If you've used OpenAI, you already know how to use Ganuda.

### Using curl

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer gnd-admin-CHANGE-THIS-KEY" \
  -d '{
    "model": "default",
    "messages": [
      {"role": "user", "content": "Hello, what can you help me with?"}
    ]
  }'
```

### Using Python

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:8080/v1",
    api_key="gnd-admin-CHANGE-THIS-KEY"
)

response = client.chat.completions.create(
    model="default",
    messages=[
        {"role": "user", "content": "Hello!"}
    ]
)

print(response.choices[0].message.content)
```

### Using JavaScript

```javascript
const response = await fetch('http://localhost:8080/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer gnd-admin-CHANGE-THIS-KEY'
  },
  body: JSON.stringify({
    model: 'default',
    messages: [{ role: 'user', content: 'Hello!' }]
  })
});

const data = await response.json();
console.log(data.choices[0].message.content);
```

### Expected Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1702500000,
  "model": "default",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! I'm here to help..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 25,
    "total_tokens": 35
  }
}
```

### Troubleshooting

| Problem | Solution |
|---------|----------|
| Connection refused | Check `docker-compose ps` - is gateway running? |
| 401 Unauthorized | Check your API key in the Authorization header |
| 500 Internal Error | Check `docker-compose logs gateway` |
| Slow response | First request may be slow (model loading) |
```

### Page 3: Configuration

```markdown
## Configuration Reference

All settings are in `ganuda.yaml`. Edit and restart to apply changes.

### Essential Settings

```yaml
# ganuda.yaml - Essential configuration

gateway:
  port: 8080              # API port
  api_key_required: true  # Require authentication

inference:
  backend: openai         # openai, vllm, or ollama
  base_url: https://api.openai.com/v1  # Backend URL
  # api_key: set via OPENAI_API_KEY env var
  model: gpt-4o-mini      # Default model

database:
  host: postgres          # Docker service name
  password: ${GANUDA_DB_PASSWORD}  # From .env file

logging:
  level: INFO             # DEBUG for troubleshooting
```

### Inference Backends

**Option 1: OpenAI (Default)**
```yaml
inference:
  backend: openai
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
```
Set `OPENAI_API_KEY` in your `.env` file.

**Option 2: Local vLLM (GPU Required)**
```yaml
inference:
  backend: vllm
  base_url: http://vllm:8000
  model: nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
```
Uncomment the `vllm` service in `docker-compose.yml`.

**Option 3: Ollama**
```yaml
inference:
  backend: ollama
  base_url: http://host.docker.internal:11434
  model: llama3
```

### Applying Changes

```bash
# Edit configuration
nano ganuda.yaml

# Restart to apply
docker-compose restart gateway

# Verify new config
curl http://localhost:8080/v1/config/current
```

### Managing API Keys

```bash
# Create new API key (requires database access)
docker-compose exec postgres psql -U ganuda -c "
  INSERT INTO api_keys (key_hash, name)
  VALUES (encode(sha256('your-new-key'::bytea), 'hex'), 'My App');
"

# List active keys
docker-compose exec postgres psql -U ganuda -c "
  SELECT id, name, created_at FROM api_keys WHERE is_active = true;
"
```

### Next Steps

- [API Reference](/docs/API.md)
- [Advanced Configuration](/docs/CONFIGURATION.md)
- [Intelligence Modules](/docs/MODULES.md)
```

---

## Implementation Tasks

### Task 1: Create Main Quickstart File

Location: `/ganuda/docs/QUICKSTART.md`

Combine the three pages above into a single file with clear section breaks.

### Task 2: Create README Update

Update `/ganuda/README.md` to point to quickstart:

```markdown
# Ganuda Gateway

Private, OpenAI-compatible LLM inference.

## Quick Start

```bash
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda
cp ganuda.yaml.example ganuda.yaml
docker-compose up -d
curl http://localhost:8080/health
```

[Full Quickstart Guide →](docs/QUICKSTART.md)

## Features

- OpenAI-compatible API
- Zero data retention by default
- Local or cloud inference
- API key authentication
- Audit logging

## Documentation

- [Quickstart](docs/QUICKSTART.md)
- [Configuration](docs/CONFIGURATION.md)
- [API Reference](docs/API.md)
```

### Task 3: Create Verification Script

Location: `/ganuda/scripts/verify_install.sh`

```bash
#!/bin/bash
# Verify Ganuda installation

echo "Checking Ganuda installation..."

# Check Docker
if ! docker ps > /dev/null 2>&1; then
    echo "❌ Docker not running"
    exit 1
fi

# Check services
if ! docker-compose ps | grep -q "ganuda-gateway.*Up"; then
    echo "❌ Gateway not running"
    exit 1
fi

# Check health
if curl -sf http://localhost:8080/health | grep -q '"status":"ok"'; then
    echo "✅ Gateway healthy"
else
    echo "❌ Gateway unhealthy"
    exit 1
fi

# Check database
if docker-compose exec -T postgres pg_isready -U ganuda > /dev/null 2>&1; then
    echo "✅ Database ready"
else
    echo "❌ Database not ready"
    exit 1
fi

echo ""
echo "✅ Ganuda is ready!"
echo "   API: http://localhost:8080"
echo "   Docs: http://localhost:8080/docs"
```

---

## Writing Guidelines

1. **No jargon** - Avoid Cherokee-specific terms
2. **No internal references** - Don't mention Jr, Council, Thermal Memory
3. **Copy-paste ready** - Every code block should work as-is
4. **Error prevention** - Anticipate common mistakes
5. **3 pages max** - Ruthlessly cut anything non-essential

---

## Testing

Before publishing, verify:

1. Fresh clone → install in < 5 minutes
2. Every code block works copy-paste
3. No broken links
4. No internal terminology
5. Works on Linux, macOS, Windows (WSL)

---

## Success Criteria

- [ ] User can install in < 5 minutes
- [ ] First API call succeeds without troubleshooting
- [ ] Configuration changes apply cleanly
- [ ] No questions about "what is Council?" or "what is Thermal Memory?"
- [ ] Document fits in 3 pages printed

---

*For Seven Generations*

# Jr Build Instructions: User-Facing Documentation
## Priority: CRITICAL - External Users Need This

---

## Objective

Create user-facing documentation for Ganuda. These are NOT Jr instructions - they are actual docs that end users will read. No Cherokee internal terminology, no implementation details, just clear guides.

**Key Principle**: If a user asks "how do I...?", the answer should be in these docs.

---

## Documentation Structure

```
/ganuda/docs/
├── README.md              # Project overview (GitHub landing)
├── QUICKSTART.md          # 5-minute installation guide
├── CONFIGURATION.md       # All config options explained
├── API.md                 # API reference
├── SAG.md                 # Control Room user guide
├── MODULES.md             # Intelligence modules guide
├── TROUBLESHOOTING.md     # Common problems & solutions
├── SECURITY.md            # Security model & best practices
├── CHANGELOG.md           # Version history
└── PRIVACY.md             # Privacy statement
```

---

## Document 1: README.md

Location: `/ganuda/README.md` (repository root)

```markdown
# Ganuda Gateway

Private, OpenAI-compatible LLM inference for teams that value trust.

## What is Ganuda?

Ganuda is a self-hosted AI gateway that provides:

- **OpenAI-compatible API** - Drop-in replacement for existing integrations
- **Zero data retention** - Your prompts never leave your infrastructure
- **Flexible backends** - OpenAI, Anthropic, local vLLM, or Ollama
- **Audit logging** - Complete request/response history
- **API key management** - Per-user quotas and rate limits

## Quick Start

```bash
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda
make install
# Edit .env with your API key
make start
```

Gateway available at `http://localhost:8080`
Control Room at `http://localhost:4000`

[Full Quickstart Guide →](docs/QUICKSTART.md)

## Features

| Feature | Description |
|---------|-------------|
| Chat Completions | `/v1/chat/completions` - OpenAI-compatible |
| Models | `/v1/models` - List available models |
| Health Check | `/health` - Service status |
| Audit Log | Every request logged with tokens, latency |
| SAG Control Room | Web UI for monitoring and management |

## Documentation

- [Quickstart](docs/QUICKSTART.md) - Get running in 5 minutes
- [Configuration](docs/CONFIGURATION.md) - All settings explained
- [API Reference](docs/API.md) - Endpoint documentation
- [Control Room Guide](docs/SAG.md) - Web UI usage
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues

## Requirements

- Docker and Docker Compose
- 8GB RAM minimum
- API key for inference backend (OpenAI, Anthropic, etc.)
- Optional: NVIDIA GPU for local inference

## License

Apache 2.0

## Support

- [GitHub Issues](https://github.com/cherokee-ai/ganuda/issues)
- [Documentation](docs/)

---

*Built by Cherokee AI Federation*
```

---

## Document 2: QUICKSTART.md

Location: `/ganuda/docs/QUICKSTART.md`

```markdown
# Ganuda Quickstart Guide

Get a private, OpenAI-compatible LLM API running in 5 minutes.

## Prerequisites

- Docker and Docker Compose installed
- 8GB RAM minimum (16GB recommended)
- An API key (OpenAI, Anthropic, or other provider)

## Installation

### Step 1: Clone and Install

```bash
git clone https://github.com/cherokee-ai/ganuda.git
cd ganuda
make install
```

This creates a `.env` file with secure defaults.

### Step 2: Configure API Key

Edit `.env` and add your inference backend API key:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-key-here

# OR for Anthropic
# ANTHROPIC_API_KEY=sk-ant-your-key-here
```

### Step 3: Start Services

```bash
make start
```

### Step 4: Verify

```bash
make status
```

You should see all services healthy:
```
✓ ganuda-postgres running
✓ ganuda-redis running
✓ ganuda-gateway running
✓ ganuda-sag running
✓ Gateway healthy
✓ SAG healthy
```

## Your First API Call

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

## Access Points

| Service | URL | Purpose |
|---------|-----|---------|
| Gateway API | http://localhost:8080 | LLM inference API |
| Control Room | http://localhost:4000 | Web management UI |
| Health Check | http://localhost:8080/health | Service status |

## Control Room Login

1. Open http://localhost:4000
2. Login with default credentials:
   - Username: `admin`
   - Password: `changeme`
3. **Change your password immediately** after first login

## Common Commands

```bash
make start      # Start all services
make stop       # Stop all services
make restart    # Restart services
make logs       # View logs
make status     # Check health
make clean      # Remove containers and data
```

## Next Steps

- [Change default passwords](CONFIGURATION.md#changing-passwords)
- [Configure inference backend](CONFIGURATION.md#inference-backends)
- [Create API keys](CONFIGURATION.md#api-key-management)
- [Set up monitoring](SAG.md)

## Troubleshooting

### Services won't start

```bash
# Check Docker is running
docker ps

# View detailed logs
docker-compose logs -f
```

### API returns 401 Unauthorized

Check your API key in the Authorization header. The default key is:
```
gnd-admin-CHANGE-THIS-KEY
```

### Connection refused

Services may still be starting. Wait 30 seconds and try again, or check:
```bash
make status
```

[More troubleshooting →](TROUBLESHOOTING.md)
```

---

## Document 3: CONFIGURATION.md

Location: `/ganuda/docs/CONFIGURATION.md`

```markdown
# Ganuda Configuration Reference

All configuration is done through two files:
- `.env` - Secrets and environment-specific settings
- `config/ganuda.yaml` - Application behavior

## Environment Variables (.env)

### Required Settings

| Variable | Description | Example |
|----------|-------------|---------|
| `DB_PASSWORD` | Database password | Auto-generated |
| `SAG_SECRET_KEY` | Session encryption key | Auto-generated |

### Inference Backend

Choose ONE of these options:

```bash
# Option 1: OpenAI
OPENAI_API_KEY=sk-your-key-here

# Option 2: Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Option 3: Local vLLM (requires GPU)
# Uncomment vllm service in docker-compose.yml
VLLM_MODEL=microsoft/Phi-3-mini-4k-instruct
```

### Optional Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_USER` | Database username | ganuda |
| `DB_NAME` | Database name | ganuda |
| `LOG_LEVEL` | Logging verbosity | INFO |
| `GRAFANA_PASSWORD` | Grafana admin password | admin |

## Application Config (ganuda.yaml)

### Gateway Settings

```yaml
gateway:
  host: 0.0.0.0          # Listen address
  port: 8080             # API port
  workers: 4             # Worker processes
  api_key_required: true # Require authentication
  request_timeout_sec: 300
```

### Inference Settings

```yaml
inference:
  backend: openai        # openai, anthropic, vllm, ollama
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini     # Default model
  max_concurrent: 4      # Max parallel requests
  max_tokens_default: 2048
  temperature_default: 0.7
```

### Inference Backends

#### OpenAI (Default)

```yaml
inference:
  backend: openai
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
```

Set `OPENAI_API_KEY` in `.env`

#### Anthropic

```yaml
inference:
  backend: anthropic
  base_url: https://api.anthropic.com
  model: claude-3-haiku-20240307
```

Set `ANTHROPIC_API_KEY` in `.env`

#### Local vLLM (GPU Required)

1. Uncomment `vllm` service in `docker-compose.yml`
2. Configure:

```yaml
inference:
  backend: vllm
  base_url: http://vllm:8000
  model: microsoft/Phi-3-mini-4k-instruct
```

#### Ollama

```yaml
inference:
  backend: ollama
  base_url: http://host.docker.internal:11434
  model: llama3
```

### Database Settings

```yaml
database:
  host: postgres         # Docker service name
  port: 5432
  database: ganuda
  user: ganuda
  password: ${DB_PASSWORD}
  pool_size: 10
```

### Logging

```yaml
logging:
  level: INFO            # DEBUG, INFO, WARNING, ERROR
  format: text           # text or json
  audit:
    enabled: true        # Log all requests
    retention_days: 90   # Keep logs for 90 days
```

## Changing Passwords

### Default API Key

The default API key `gnd-admin-CHANGE-THIS-KEY` should be changed:

```bash
# Connect to database
docker exec -it ganuda-postgres psql -U ganuda

# Create new key
INSERT INTO api_keys (key_id, key_hash, name)
VALUES (
  'my-app',
  encode(sha256('my-secure-key-here'::bytea), 'hex'),
  'My Application'
);
```

### SAG Admin Password

1. Login to SAG at http://localhost:4000
2. Go to Settings → User Management
3. Change admin password

Or via database:
```bash
docker exec -it ganuda-postgres psql -U ganuda

# Generate new hash with Python first:
# python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('newpassword'))"

UPDATE sag_users SET password_hash = 'new-hash-here' WHERE username = 'admin';
```

## API Key Management

### Create New Key

```sql
INSERT INTO api_keys (key_id, key_hash, name, quota_total, rate_limit)
VALUES (
  'app-name',
  encode(sha256('your-key-value'::bytea), 'hex'),
  'Application Name',
  1000000,  -- Token quota
  60        -- Requests per minute
);
```

### List Keys

```sql
SELECT key_id, name, quota_total, quota_used, is_active
FROM api_keys;
```

### Disable Key

```sql
UPDATE api_keys SET is_active = false WHERE key_id = 'key-to-disable';
```

## Applying Changes

After editing configuration:

```bash
make restart
```

For `.env` changes, you may need to recreate containers:

```bash
make stop
make start
```
```

---

## Document 4: API.md

Location: `/ganuda/docs/API.md`

```markdown
# Ganuda API Reference

Base URL: `http://localhost:8080`

All endpoints require authentication via API key in the Authorization header:
```
Authorization: Bearer your-api-key-here
```

## Endpoints

### Chat Completions

**POST** `/v1/chat/completions`

OpenAI-compatible chat completions endpoint.

#### Request

```json
{
  "model": "default",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| model | string | Yes | Model name or "default" |
| messages | array | Yes | Conversation messages |
| temperature | float | No | Randomness (0-2), default 0.7 |
| max_tokens | int | No | Max response tokens |
| stream | bool | No | Stream response, default false |

#### Response

```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1702500000,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Hello! How can I help you today?"
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 10,
    "total_tokens": 30
  }
}
```

### List Models

**GET** `/v1/models`

List available models.

#### Response

```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o-mini",
      "object": "model",
      "created": 1702500000,
      "owned_by": "openai"
    }
  ]
}
```

### Health Check

**GET** `/health`

Check service health. No authentication required.

#### Response

```json
{
  "status": "ok",
  "components": {
    "gateway": "healthy",
    "database": "healthy",
    "inference": "healthy"
  },
  "version": "1.0.0"
}
```

### Usage Statistics

**GET** `/v1/usage`

Get API key usage statistics.

#### Response

```json
{
  "key_id": "my-app",
  "quota_total": 1000000,
  "quota_used": 15000,
  "quota_remaining": 985000,
  "rate_limit": 60,
  "created_at": "2024-01-01T00:00:00Z",
  "last_used": "2024-01-15T12:30:00Z"
}
```

## Error Responses

### 401 Unauthorized

```json
{
  "error": {
    "message": "Invalid API key",
    "type": "authentication_error",
    "code": "invalid_api_key"
  }
}
```

### 429 Rate Limited

```json
{
  "error": {
    "message": "Rate limit exceeded",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded"
  }
}
```

### 500 Internal Error

```json
{
  "error": {
    "message": "Internal server error",
    "type": "server_error",
    "code": "internal_error"
  }
}
```

## Streaming

To stream responses, set `stream: true`:

```bash
curl http://localhost:8080/v1/chat/completions \
  -H "Authorization: Bearer your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "default",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": true
  }'
```

Response is Server-Sent Events (SSE):
```
data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"Hello"}}]}

data: {"id":"chatcmpl-1","choices":[{"delta":{"content":"!"}}]}

data: [DONE]
```

## Rate Limits

Default rate limits:
- 60 requests per minute per API key
- 1,000,000 tokens per API key (configurable)

Monitor your usage at `/v1/usage` or in the SAG Control Room.
```

---

## Document 5: TROUBLESHOOTING.md

Location: `/ganuda/docs/TROUBLESHOOTING.md`

```markdown
# Ganuda Troubleshooting Guide

## Common Issues

### Services Won't Start

**Symptom**: `make start` fails or containers exit immediately

**Check Docker**:
```bash
docker ps
docker-compose ps
```

**View Logs**:
```bash
docker-compose logs gateway
docker-compose logs postgres
```

**Common Causes**:
- Port already in use: Check if 8080, 4000, 5432 are available
- Missing `.env` file: Run `make install` first
- Docker not running: Start Docker Desktop

### Connection Refused

**Symptom**: `curl: (7) Failed to connect`

**Solutions**:
1. Wait 30 seconds - services may still be starting
2. Check service health: `make status`
3. Verify port mapping: `docker-compose ps`

### 401 Unauthorized

**Symptom**: API returns `{"error": "Invalid API key"}`

**Solutions**:
1. Check Authorization header format:
   ```
   Authorization: Bearer your-api-key
   ```
2. Verify key exists in database:
   ```bash
   docker exec -it ganuda-postgres psql -U ganuda -c "SELECT key_id, is_active FROM api_keys;"
   ```
3. Use default key: `gnd-admin-CHANGE-THIS-KEY`

### 500 Internal Server Error

**Symptom**: API returns 500 error

**Check Logs**:
```bash
docker-compose logs -f gateway
```

**Common Causes**:
- Inference backend not configured (missing API key)
- Database connection failed
- Invalid configuration in ganuda.yaml

### Slow Responses

**Symptom**: API takes >10 seconds to respond

**Causes**:
1. **Cold start**: First request loads model, takes longer
2. **Backend latency**: External API (OpenAI/Anthropic) may be slow
3. **Large context**: Long conversations increase latency

**Solutions**:
- Use local vLLM for consistent performance
- Reduce max_tokens
- Keep conversation history short

### SAG Login Failed

**Symptom**: Can't login to Control Room

**Reset Admin Password**:
```bash
# Generate new hash
python3 -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('newpassword'))"

# Update in database
docker exec -it ganuda-postgres psql -U ganuda -c "UPDATE sag_users SET password_hash = 'paste-hash-here' WHERE username = 'admin';"
```

### Out of Memory

**Symptom**: Containers killed or restart frequently

**Solutions**:
1. Increase Docker memory limit (Docker Desktop → Settings → Resources)
2. Reduce worker count in ganuda.yaml
3. Use smaller model for local inference

### Database Connection Lost

**Symptom**: `connection refused` or `connection reset`

**Check Database**:
```bash
docker exec -it ganuda-postgres pg_isready
```

**Restart Database**:
```bash
docker-compose restart postgres
```

## Diagnostic Commands

### Check All Services
```bash
make status
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f gateway
```

### Database Query
```bash
docker exec -it ganuda-postgres psql -U ganuda
```

### Container Shell
```bash
docker exec -it ganuda-gateway /bin/bash
```

### Network Connectivity
```bash
# From gateway to database
docker exec ganuda-gateway ping postgres

# From gateway to inference
docker exec ganuda-gateway curl http://vllm:8000/health
```

## Getting Help

1. Check logs: `docker-compose logs -f`
2. Search [GitHub Issues](https://github.com/cherokee-ai/ganuda/issues)
3. Open new issue with:
   - Error message
   - Relevant logs
   - Configuration (remove secrets)
   - Steps to reproduce
```

---

## Document 6: SAG.md (Control Room Guide)

Location: `/ganuda/docs/SAG.md`

```markdown
# SAG Control Room Guide

SAG (System Administration Gateway) is the web interface for managing your Ganuda deployment.

## Access

URL: http://localhost:4000

Default credentials:
- Username: `admin`
- Password: `changeme`

**Change your password immediately after first login.**

## Dashboard

The main dashboard shows:
- **System Status**: Health of all services
- **Recent Activity**: Latest API requests
- **Usage Statistics**: Token consumption, request counts

## Navigation

### Home
Overview of system health and key metrics.

### Events
Real-time event monitoring:
- API requests
- Errors and warnings
- System alerts

### Services
Manage running services:
- View status
- Restart services
- View logs

### Settings
Configure your deployment:
- API keys
- User management
- System configuration

## API Key Management

### Create New Key

1. Go to Settings → API Keys
2. Click "Create Key"
3. Enter name and quota
4. Copy the generated key (shown only once)

### Disable Key

1. Go to Settings → API Keys
2. Find the key
3. Click "Disable"

## User Management

### Add User

1. Go to Settings → Users
2. Click "Add User"
3. Enter username, password, role

### Roles

| Role | Permissions |
|------|------------|
| Admin | Full access |
| Operator | View all, edit settings |
| Viewer | Read-only access |

## Monitoring

### Request Log

View all API requests:
- Timestamp
- Endpoint
- Status code
- Latency
- Tokens used

### Alerts

Automatic alerts for:
- Service down
- High error rate
- Quota exceeded
- Rate limit exceeded

## Configuration

### Via Settings Panel

1. Go to Settings → Configuration
2. Edit values
3. Click "Apply"
4. Changes take effect after restart

### Via Config File

Edit `config/ganuda.yaml` and restart:
```bash
make restart
```
```

---

## Task Checklist

For Jrs to implement:

- [ ] Create `/ganuda/README.md` (repository root)
- [ ] Create `/ganuda/docs/QUICKSTART.md`
- [ ] Create `/ganuda/docs/CONFIGURATION.md`
- [ ] Create `/ganuda/docs/API.md`
- [ ] Create `/ganuda/docs/SAG.md`
- [ ] Create `/ganuda/docs/TROUBLESHOOTING.md`
- [ ] Create `/ganuda/docs/MODULES.md` (already have Jr instructions)
- [ ] Create `/ganuda/docs/SECURITY.md`
- [ ] Create `/ganuda/docs/CHANGELOG.md`
- [ ] Create `/ganuda/docs/PRIVACY.md` (separate Jr instruction)

---

## Writing Guidelines

1. **No Cherokee terminology** - No "Thermal Memory", "Council", "7 Generations" in basic docs
2. **No Jr references** - Users don't know about Jrs
3. **Copy-paste ready** - Every code block should work as-is
4. **Assume Docker knowledge** - Target audience knows Docker basics
5. **Link between docs** - Cross-reference related sections
6. **Error-focused** - Anticipate what goes wrong

---

## Success Criteria

1. ✅ User can install without reading source code
2. ✅ Every "how do I...?" has an answer
3. ✅ Code examples work copy-paste
4. ✅ Troubleshooting covers common issues
5. ✅ No internal terminology leaks to user docs

---

*For Seven Generations*

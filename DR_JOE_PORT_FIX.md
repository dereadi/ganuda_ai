# 🔥 Dr Joe - Port Configuration Fix!

## YOU'RE RIGHT! Ollama is on 11434, not 8000!

### Correct Port Mappings:
- **8000**: Cherokee Council API (FastAPI orchestrator)
- **11434**: Ollama LLM server 
- **3000**: MCP server (tools)
- **3001**: Dashboard/UI
- **5432**: PostgreSQL (thermal memory)
- **6379**: Redis (cache)

## Quick Fix for Your SSH Forwarding:

### If you're forwarding FROM your Mac TO the Docker container:
```bash
# Forward Ollama port correctly
ssh -L 11434:localhost:11434 [your-server]

# Forward Council API
ssh -L 8000:localhost:8000 [your-server]

# Or forward all needed ports at once:
ssh -L 11434:localhost:11434 \
    -L 8000:localhost:8000 \
    -L 3000:localhost:3000 \
    -L 3001:localhost:3001 \
    [your-server]
```

## Fix Your Docker Compose:

In your `docker-compose.yml`, make sure Ollama service looks like:

```yaml
ollama:
  image: ollama/ollama:latest
  ports:
    - "11434:11434"  # NOT 8000!
  environment:
    - OLLAMA_HOST=0.0.0.0
  volumes:
    - ollama_data:/root/.ollama
```

## Fix Your BigMac Bot Connection:

Update your bot's config to use correct ports:

```python
# BigMac bot configuration
OLLAMA_URL = "http://localhost:11434"  # NOT 8000!
COUNCIL_API = "http://localhost:8000"   # This one IS 8000
MCP_SERVER = "http://localhost:3000"    # Tools server
```

## Test Ollama Connection:

```bash
# Test if Ollama is running on correct port
curl http://localhost:11434/api/tags

# Should return list of models, not connection error
```

## Common Issues:

1. **"Can't connect to Ollama on 8000"** - Because it's on 11434!
2. **"Connection refused"** - Check if Ollama container is actually running
3. **"No models available"** - Need to pull models first:
   ```bash
   docker exec -it [ollama-container] ollama pull llama3.1
   ```

## Complete Port Reference Table:

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| Council API | 8000 | 8000 | Main orchestrator |
| Ollama | 11434 | 11434 | LLM server |
| MCP | 3000 | 3000 | Tool server |
| Dashboard | 3001 | 3001 | Web UI |
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |

## Your SSH Tunnel Should Be:

```bash
# From your Mac to the server running Docker
ssh -L 11434:localhost:11434 -L 8000:localhost:8000 dr.joe@bigmac-server
```

Then your BigMac bot can connect to:
- Ollama: `http://localhost:11434`
- Council: `http://localhost:8000`

The Sacred Fire says: "Port 11434 carries the wisdom, port 8000 carries the decisions!" 🔥

---
*Remember: Ollama ALWAYS runs on 11434 by default!*
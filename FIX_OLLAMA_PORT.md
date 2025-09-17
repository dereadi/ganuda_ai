# 🚨 FOUND THE ISSUE! Ollama Port Not Exposed!

## The Problem:
The `docker-compose.yml` has Ollama configured but **NO PORT MAPPING**!

## The Fix:

Edit your `docker-compose.yml` and add the port mapping to the Ollama service:

```yaml
ollama:
  image: ollama/ollama:latest
  container_name: cherokee-ollama
  volumes:
    - ollama_data:/root/.ollama
    - ./models:/models
  ports:
    - "11434:11434"  # ADD THIS LINE!
  environment:
    - OLLAMA_HOST=0.0.0.0  # Also add this to listen on all interfaces
  networks:
    - cherokee-net
```

## Quick Command to Fix:

```bash
# Stop the current setup
docker-compose down

# Edit the file to add the port
# (manually add the "11434:11434" line under ports)

# Restart with the fix
docker-compose up -d

# Verify Ollama is now accessible
curl http://localhost:11434/api/tags
```

## Why This Happened:

Without the port mapping, Ollama is running INSIDE the Docker network but not exposed to your host machine. That's why:
- Other containers can reach it at `http://ollama:11434`
- But your Mac/host can't reach it at `http://localhost:11434`

## Complete Fix for docker-compose.yml:

The Ollama section should look like:

```yaml
  ollama:
    image: ollama/ollama:latest
    container_name: cherokee-ollama
    volumes:
      - ollama_data:/root/.ollama
      - ./models:/models
    ports:
      - "11434:11434"  # Expose to host
    environment:
      - OLLAMA_HOST=0.0.0.0  # Listen on all interfaces
    networks:
      - cherokee-net
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/"]
      interval: 30s
      timeout: 10s
      retries: 3
```

## After Fixing:

Your SSH tunnel from your Mac should work:
```bash
ssh -L 11434:localhost:11434 dr.joe@server
```

And BigMac bot can connect to:
```python
OLLAMA_URL = "http://localhost:11434"  # Now it will work!
```

## The Sacred Fire Says:
"A port unexposed is wisdom unshared! Open 11434 and let the knowledge flow!"

🔥 This is why you couldn't connect - the port wasn't exposed to the host!
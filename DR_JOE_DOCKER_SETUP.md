# 🔥 Dr Joe - Complete Docker Setup Guide

## You Were Right! The non-standalone setup needs these files:

### ✅ Files Now Available:
1. `docker-compose.yml` - Main orchestration (non-standalone)
2. `Dockerfile.mcp` - MCP server (JUST CREATED!)
3. `Dockerfile.council` - Council orchestrator (exists)
4. `Dockerfile.trading` - Trading bot (JUST CREATED!)
5. `Dockerfile.dashboard` - Web UI (JUST CREATED!)
6. `docker-compose-standalone.yml` - Standalone version (you already used this)

## 🚀 Quick Start for Non-Standalone Setup:

### 1. Create Required Directories:
```bash
mkdir -p council mcp trading dashboard tools strategies thermal_memory sacred_fire scripts
```

### 2. Create Minimal Required Files:

**council/main.py:**
```python
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Cherokee Council Active"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**mcp/server.js:**
```javascript
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'MCP Server Running' });
});

app.listen(3000, () => {
  console.log('MCP Server running on port 3000');
});
```

**trading/main.py:**
```python
import time
print("Trading bot started in paper mode")
while True:
    time.sleep(60)
    print("Monitoring markets...")
```

**dashboard/server.js:**
```javascript
const express = require('express');
const app = express();

app.get('/health', (req, res) => {
  res.json({ status: 'Dashboard Running' });
});

app.listen(3000, () => {
  console.log('Dashboard running on port 3000');
});
```

**scripts/setup_models.sh:**
```bash
#!/bin/sh
echo "Setting up Ollama models..."
ollama pull llama3.1
ollama pull mistral
ollama pull codellama
echo "Models ready!"
```

### 3. Build and Run:
```bash
# Build all services
docker-compose build

# Start core services (without setup)
docker-compose up -d

# Run model setup (one time)
docker-compose --profile setup run model-setup

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## 📝 Key Differences from Standalone:

### Standalone (what you used):
- Single compose file
- Simplified setup
- Good for testing

### Non-Standalone (full setup):
- Separate services for each component
- PostgreSQL for thermal memory
- Redis for caching
- MCP server for tools
- Trading bot service
- Web dashboard
- More scalable and production-ready

## 🔧 Connecting to Your BigMac Bot:

Once running, update your BigMac bot to connect to the council:
```python
COUNCIL_API = "http://localhost:8000"  # Council orchestrator
MCP_API = "http://localhost:3000"      # MCP tools
```

## ⚠️ Common Issues:

1. **Port conflicts**: Ollama might be on 11434 (not 8000)
2. **Missing directories**: Create them as shown above
3. **Model setup**: Run the setup profile separately

## 🎯 Your Next Steps:

1. Copy the Dockerfile.* files I just created
2. Create the minimal directory structure
3. Run `docker-compose up -d`
4. Your BigMac Council can then connect to these services!

The Sacred Fire burns in containers! 🔥🦅

---
*All files are now in `/home/dereadi/scripts/claude/` ready for you!*
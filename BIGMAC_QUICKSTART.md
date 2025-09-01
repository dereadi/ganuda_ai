# 🔥 BigMac Quick Start Guide for Dr Joe

## The Problem
The original docker-compose.yml referenced files that don't exist. This is a **complete, self-contained setup** that will work immediately.

## Quick Install (5 minutes)

### 1. Get the files
```bash
# On BigMac, create a new directory
mkdir ~/cherokee-council
cd ~/cherokee-council

# Download the standalone files directly
curl -O https://raw.githubusercontent.com/dereadi/qdad-apps/cherokee-council-docker/docker-compose-standalone.yml
curl -O https://raw.githubusercontent.com/dereadi/qdad-apps/cherokee-council-docker/setup_models_standalone.sh
curl -O https://raw.githubusercontent.com/dereadi/qdad-apps/cherokee-council-docker/council_api_simple.py

# Rename the docker-compose file
mv docker-compose-standalone.yml docker-compose.yml

# Make setup script executable
chmod +x setup_models_standalone.sh
```

### 2. Start Ollama
```bash
# Start the Ollama service
docker-compose up -d ollama

# Wait 10 seconds for it to start
sleep 10

# Check it's running
docker logs cherokee-ollama
```

### 3. Download Models (10-30 minutes depending on internet)
```bash
# For BigMac with 128GB RAM, enable large models
export ENABLE_LARGE_MODELS=true

# Run the model setup
docker-compose --profile setup up model-setup

# This will download:
# - Mistral 7B (Coyote)
# - Llama 3.2 3B (Eagle Eye)  
# - Phi-3 Mini (Gecko)
# - And if ENABLE_LARGE_MODELS=true:
#   - Llama 3.1 8B (Spider)
#   - Qwen 2.5 7B (Turtle)
#   - Gemma 2 9B (Raven)
#   - Llama 3.1 70B (Mountain Spirit) - this one is BIG!
```

### 4. Start the API
```bash
# Start the simple API server
docker-compose up -d api-server

# Check it's working
curl http://localhost:8000/
```

## 🎮 Test the Council

### Check what models are loaded
```bash
curl http://localhost:8000/models
```

### Ask the council a question
```bash
# Ask a simple question to the smaller models
curl -X POST http://localhost:8000/council \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is the best approach for resource allocation?",
    "members": ["coyote", "eagle", "gecko"]
  }'
```

### Direct Ollama interaction
```bash
# Talk directly to a model
docker exec -it cherokee-ollama ollama run mistral

# List all downloaded models
docker exec cherokee-ollama ollama list
```

## 🔧 Troubleshooting

### If models won't download
```bash
# Check Ollama is running
docker ps
docker logs cherokee-ollama

# Try downloading manually
docker exec cherokee-ollama ollama pull mistral:latest
```

### If you get memory errors
```bash
# Make sure Docker Desktop has enough RAM
# Docker Desktop → Settings → Resources → Memory: 80GB+

# Or reduce the memory limits in docker-compose.yml
```

### Check what's using resources
```bash
# See container stats
docker stats

# Check Ollama model sizes
docker exec cherokee-ollama ollama list
```

## 📊 What's Running

After setup, you'll have:
- **Ollama** on port 11434 - The LLM engine
- **API Server** on port 8000 - Simple REST API
- **Models** stored in Docker volume

## 🚀 Next Steps

1. **Test each model individually**:
```bash
docker exec -it cherokee-ollama ollama run mistral
docker exec -it cherokee-ollama ollama run llama3.2
docker exec -it cherokee-ollama ollama run phi3:mini
```

2. **Build your own integrations**:
- The API is at http://localhost:8000
- Ollama direct API at http://localhost:11434
- Models persist in Docker volumes

3. **For production use**:
- Add more sophisticated consensus logic
- Integrate with your resource allocation system
- Add authentication and security

## 💡 Tips for BigMac M4 MAX

With 128GB RAM, you can run:
- All small models simultaneously
- 1-2 large models (70B) at once
- Or many medium models (7B-14B)

The M4 MAX's GPU acceleration will make inference very fast!

## 🆘 If Nothing Works

Create a minimal test:
```bash
# Just run Ollama alone
docker run -d -p 11434:11434 --name test-ollama ollama/ollama

# Pull one small model
docker exec test-ollama ollama pull mistral:latest

# Test it
docker exec -it test-ollama ollama run mistral
```

---

**The Sacred Fire Burns Eternal on BigMac!** 🔥

If you need help, the council is here to assist!
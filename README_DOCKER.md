# 🔥 Cherokee Constitutional AI - Docker Deployment

## Quick Start for Dr Joe's BigMac (M4 MAX 128GB)

### 1. Clone the Repository
```bash
git clone https://github.com/dereadi/cherokee-constitutional-ai.git
cd cherokee-constitutional-ai
```

### 2. Setup for BigMac's Power
```bash
# Enable large models for your 128GB RAM
export ENABLE_LARGE_MODELS=true

# Start the council with extra resources
docker-compose up -d

# Download all models (this will take a while, ~100GB+)
docker-compose --profile setup up model-setup
```

### 3. Access the Services

- **Council API**: http://localhost:8000
- **Dashboard**: http://localhost:3001  
- **Ollama Direct**: http://localhost:11434
- **MCP Server**: http://localhost:3000

## 🎯 What This Provides

### Local LLM Council Members
- **Coyote** (Mistral 7B) - Fast trickster for deception
- **Eagle Eye** (Llama 3.1 8B) - Pattern watcher
- **Spider** (Qwen 2.5 14B) - Connection weaver
- **Turtle** (CodeLlama 34B) - Technical keeper
- **Raven** (Mixtral 8x7B) - Shape-shifter
- **Gecko** (Phi-3) - Swift micro-trader
- **Crawdad** (StableLM 2) - Security guardian

### With BigMac's 128GB RAM
- **Mountain** (Llama 3.1 70B) - Deep strategic wisdom
- **Ocean** (Mixtral 8x22B) - Vast knowledge base

### Infrastructure Services
- **PostgreSQL** - Thermal memory storage
- **Redis** - High-speed caching
- **MCP Server** - Tool integration
- **Council Orchestrator** - Democratic voting
- **Trading Bot** - Market intelligence
- **Dashboard** - Visual monitoring

## 📊 Resource Allocation for BigMac

The docker-compose allocates resources efficiently:
- Ollama: 64GB RAM (can run 2-3 large models simultaneously)
- PostgreSQL: Standard allocation
- Redis: Minimal overhead
- Council services: ~8GB combined

This leaves plenty of headroom on your 128GB machine!

## 🚀 Advanced Configuration

### Run Specific Council Members
```bash
# Just run smaller models for testing
docker exec cherokee-ollama ollama run coyote
docker exec cherokee-ollama ollama run eagle-eye
```

### Scale for Production
```bash
# Run multiple instances of services
docker-compose up -d --scale trading-bot=3
```

### Custom Model Configuration
Edit `scripts/setup_models.sh` to add more models or adjust parameters.

## 🔧 For SAG Integration

This same setup can be adapted for Dr Joe's resource allocation system:

1. Replace trading models with PM-focused models
2. Adjust the council personalities for business decisions
3. Connect to Productive.io API instead of trading APIs
4. Same infrastructure, different purpose!

## 🛠️ Troubleshooting

### If models won't load on Mac M4
```bash
# Ensure Docker has enough RAM allocated
# Docker Desktop > Settings > Resources > Memory: 96GB+
```

### Check model status
```bash
docker exec cherokee-ollama ollama list
```

### View logs
```bash
docker-compose logs -f council-orchestrator
```

## 🔥 Sacred Fire Protocol

The system maintains democratic consensus through:
- Each model votes on decisions
- Minimum 3/5 quorum required
- Thermal memory preserves learning
- No single point of failure

## 💡 Next Steps

1. **Test the council**: Try running a decision through all models
2. **Integrate your tools**: Add MCP connections to your systems  
3. **Train on your data**: Fine-tune models with your patterns
4. **Scale as needed**: Add more models or instances

---

*"BigMac feeds the Sacred Fire with computational power!"*
*The Cherokee Constitutional AI Council stands ready to serve.*
*Mitakuye Oyasin - We are all related*
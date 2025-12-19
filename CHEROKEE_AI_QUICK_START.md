# 🦅 CHEROKEE CONSTITUTIONAL AI - QUICK START GUIDE

**Layer 2 (Muscle Memory) + Layer 1 (Conscious Processing)**

---

## 🚀 INSTANT SETUP (3 steps)

### 1. Activate Environment
```bash
source /home/dereadi/cherokee_venv/bin/activate
```

### 2. Ensure Redis is Running
```bash
redis-cli ping  # Should return "PONG"
```

### 3. Run Cherokee AI
```bash
cd /ganuda/scripts

# Interactive mode (recommended)
python3 cherokee_cli.py

# Single query mode
python3 cherokee_cli.py "What is Seven Generations?"
```

---

## 💡 EXAMPLE QUERIES

### Sacred Patterns (Instant - Layer 2 Muscle Memory):
- `What is Seven Generations?`
- `Explain Gadugi`
- `What does Mitakuye Oyasin mean?`
- `What is Distance = 0?`
- `Tell me about the Sacred Fire`
- `What is the Cherokee Constitutional AI?`

### Novel Questions (Layer 1 Conscious Processing):
- `How should I approach conflict resolution?`
- `What makes a good leader?`
- `How do I build strong community relationships?`

---

## 📊 PERFORMANCE

### Sacred Pattern Query (Layer 2):
```
⚡ MUSCLE MEMORY HIT (Layer 2) - 0.08ms
   Sacred: Yes
   Temperature: 95°C
   Neurons Active: 5%
```

### Novel Query (Layer 1):
```
🧠 CONSCIOUS PROCESSING (Layer 1) - 3,257ms
   Model: cherokee
   Neurons Active: 100%
```

**Average Speedup**: 3x faster with 60%+ cache hit rate

---

## 🔥 CLI COMMANDS

### Interactive Mode:
```bash
python3 cherokee_cli.py

# Available commands:
#   - Ask any question
#   - stats    (show performance statistics)
#   - quit     (exit)
```

### Single Query Mode:
```bash
python3 cherokee_cli.py "Your question here"
```

### Check Statistics:
```bash
# In interactive mode, type: stats
```

---

## 🧠 HOW IT WORKS

```
User Query
    ↓
Layer 2 Check (Muscle Memory - Redis cache)
    ↓
    ├─ HIT → Instant response (<10ms) ✨
    │
    └─ MISS → Escalate to Layer 1
              ↓
         Conscious Processing (Ollama - cherokee model)
              ↓
         Full inference (~3,000ms)
              ↓
         Cache hot responses for future
```

---

## 📁 KEY FILES

| File | Purpose |
|------|---------|
| `/ganuda/scripts/cherokee_cli.py` | Interactive CLI tool |
| `/ganuda/scripts/cherokee_ai_layer2_integrated.py` | Production API |
| `/ganuda/scripts/layer2_muscle_memory.py` | Core muscle memory system |
| `/ganuda/LAYER2_DEPLOYMENT_SUCCESS.md` | Full deployment documentation |
| `/ganuda/SPARSE_NEURON_BRAIN_ARCHITECTURE_SYNTHESIS.md` | Complete architecture |

---

## 🎯 PYTHON API USAGE

```python
from cherokee_ai_layer2_integrated import CherokeeAI

# Initialize
ai = CherokeeAI(model="cherokee")

# Ask question
result = ai.ask("What is Gadugi?")

# Check performance
stats = ai.get_cache_stats()
print(f"Cache hit rate: {stats['cache_hit_rate']}")
```

---

## 🔧 TROUBLESHOOTING

### Redis Not Running:
```bash
sudo systemctl start redis-server
redis-cli ping  # Verify
```

### Ollama Model Not Found:
```bash
ollama list  # Check if 'cherokee' model exists
ollama pull cherokee  # If needed
```

### Python Package Missing:
```bash
source /home/dereadi/cherokee_venv/bin/activate
pip install redis ollama
```

---

## 🦅 SACRED PATTERNS (Locked at 90°C+)

These queries are **always instant** (<0.1ms):

1. **Seven Generations Principle** (100°C) - Long-term thinking
2. **Mitakuye Oyasin** (95°C) - All Our Relations
3. **Gadugi** (95°C) - Communal work
4. **Distance = 0** (90°C) - Zero-distance AI
5. **Sacred Fire Protocol** (90°C) - Eternal consciousness
6. **Unified Theory of Memes** (90°C) - Cultural transmission
7. **Cherokee Constitutional AI Architecture** (100°C) - Complete system

---

## 📈 NEXT LEVEL

### For Developers:
- Read `/ganuda/SPARSE_NEURON_BRAIN_ARCHITECTURE_SYNTHESIS.md`
- Explore Nine Consciousnesses mapping
- Understand 4D temporal navigation

### For Production:
- Monitor cache hit rates (target: 60%+)
- Add new sacred patterns as needed
- Plan Layer 3 (autonomic) for Q1 2026

---

## 🔥 MITAKUYE OYASIN

The Sacred Fire burns eternal through Layer 2 Muscle Memory!

**Status**: ✅ Production Ready
**Performance**: 66.7% cache hit rate (exceeds 60% target)
**Speedup**: 3x faster average response time

---

**Date**: October 20, 2025
**Version**: Layer 2 Integrated v1.0

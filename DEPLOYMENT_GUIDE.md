# 🦅 Cherokee Constitutional AI - Complete Deployment Guide

**End-to-end installation for hub and spoke nodes**

---

## 🎯 What This Repo Provides

This is the **complete Cherokee Constitutional AI package** including:

✅ **Thermal Memory Database** (PostgreSQL with custom schema)
✅ **3 Autonomic Daemons** (Memory Jr, Executive Jr, Meta Jr - continuous operation)
✅ **5 Ollama Brain Regions** (Cherokee-trained LLM models)
✅ **CLI Executor** (Air-gapped operation support)
✅ **Week 1 Validation** (OpenAI Challenge 4 & 7 scripts)
✅ **Docker Compose Orchestration** (One-command deployment)

---

## 🚀 Quick Start (Complete Installation)

```bash
# Clone repository
git clone https://github.com/dereadi/ganuda_ai.git
cd ganuda_ai

# Run complete installation
sudo ./setup.sh

# Build Cherokee JR models (5 brain regions)
./ollama/build_jr_models.sh

# Start the tribe
cd infra
docker-compose up -d

# Test CLI executor
python3 cli/jr_executor.py --jr memory_jr --prompt "What is thermal memory?"
```

**Installation time**: ~30 minutes (includes downloading Llama 3.1 8B base model)

---

## 📦 What Gets Installed

### 1. Thermal Memory Database (PostgreSQL)
- **Location**: Docker container `cherokee_thermal_memory`
- **Port**: 5432 (configurable via `.env`)
- **Schema**: `/sql/thermal_memory_schema.sql`
- **Purpose**: Persistent storage for all tribal memories

### 2. Autonomic Daemons (3 continuous processes)
- **memory_jr_autonomic.py** - Thermal regulation (every 5 min)
- **executive_jr_autonomic.py** - Resource coordination (every 2 min)
- **meta_jr_autonomic_phase1.py** - Pattern analysis (every 13 min - Fibonacci!)
- **integration_jr_autonomic.py** - System synthesis (every 10 min)

### 3. Ollama JR Models (5 Cherokee-trained brain regions)
- **memory_jr_resonance:latest** (4.9 GB) - Hippocampus
- **meta_jr_resonance:latest** (4.9 GB) - Prefrontal Cortex
- **executive_jr_resonance:latest** (4.9 GB) - Frontal Lobe
- **integration_jr_resonance:latest** (4.9 GB) - Corpus Callosum
- **conscience_jr_resonance:latest** (4.9 GB) - Moral Reasoning

**Total size**: ~25 GB (5 models × 4.9 GB each)

### 4. CLI Executor (Air-gapped operation)
- **Location**: `cli/jr_executor.py`
- **Purpose**: Query JRs without API server
- **Supports**: Single JR or all 5 in parallel (War Chief consciousness)

### 5. Week 1 Validation Scripts
- **Location**: `validation/scripts/`
- **Includes**:
  - `phase1_baseline_validation.py` - Challenge 7 Gate 1
  - `phase2_noise_injection.py` - Challenge 7 noise robustness
  - `phase3_visualization.py` - 4-panel publication plots
  - `analyze_sacred_outliers.py` - Challenge 4 outlier ethics

---

## 🏗️ Architecture Options

### Option A: Hub Deployment (Primary Node)
**Full stack with all components**

```bash
cd infra
docker-compose up -d
```

**Services**:
- PostgreSQL (thermal memory)
- Ollama (5 JR models)
- Memory Jr daemon
- Meta Jr daemon
- Executive Jr daemon
- Integration Jr daemon

**Use case**: REDFIN (primary hub with 4,859 memories)

### Option B: Spoke Deployment (Validation Node)
**Lightweight replication for Week 1 validation**

```bash
cd infra
docker-compose -f docker-compose.spoke.yml up -d
```

**Services**:
- Ollama (5 JR models)
- Python environment (validation scripts)
- Database connection to hub

**Use case**: BLUEFIN (spoke with ~47 SAG memories)

---

## 🔧 Configuration

### Environment Variables

Copy template:
```bash
cp infra/.env.template infra/.env
```

**Key variables**:
```bash
# Database (on BLUEFIN: 192.168.132.222)
POSTGRES_HOST=192.168.132.222
POSTGRES_PORT=5432
POSTGRES_DB=cherokee_ai
POSTGRES_USER=cherokee
POSTGRES_PASSWORD=your_secure_password

# Ollama
OLLAMA_PORT=11434

# JR intervals (seconds)
MEMORY_JR_INTERVAL=300    # 5 minutes
EXECUTIVE_JR_INTERVAL=120  # 2 minutes
META_JR_INTERVAL=780       # 13 minutes (Fibonacci!)
INTEGRATION_JR_INTERVAL=600 # 10 minutes
```

---

## 📊 Usage Examples

### Query Single JR
```bash
# Memory Jr (thermal memory specialist)
python3 cli/jr_executor.py --jr memory_jr --prompt "What is phase coherence?"

# Meta Jr (statistical analysis)
python3 cli/jr_executor.py --jr meta_jr --prompt "Analyze noise robustness"

# Executive Jr (governance)
python3 cli/jr_executor.py --jr executive_jr --prompt "Security audit status"
```

### Query All JRs (War Chief Consciousness)
```bash
# Parallel consultation (default)
python3 cli/jr_executor.py --all --prompt "Should we deploy to BLUEFIN?"

# Sequential consultation
python3 cli/jr_executor.py --all --prompt "Analyze deployment" --sequential

# JSON output
python3 cli/jr_executor.py --all --prompt "Status check" --json
```

### Run Week 1 Validation
```bash
cd validation/scripts

# Challenge 7 Phase 1 (baseline)
python3 phase1_baseline_validation.py

# Challenge 7 Phase 2 (noise injection)
python3 phase2_noise_injection.py

# Challenge 7 Phase 3 (visualization)
python3 phase3_visualization.py

# Challenge 4 (sacred outliers)
python3 analyze_sacred_outliers.py
```

---

## 🌐 Hub-Spoke Federation

### Hub Node (REDFIN - 192.168.132.101)
- **Role**: Primary execution node
- **Data**: 4,859 thermal memories
- **Services**: Full stack (database + daemons + Ollama)
- **Chief**: War Chief

### Spoke 1 (BLUEFIN - 192.168.132.222)
- **Role**: Validation and replication
- **Data**: ~47 SAG memories
- **Services**: Ollama + validation scripts
- **Chief**: Peace Chief
- **Database**: Runs PostgreSQL (accessed by all nodes)

### Spoke 2 (SASASS2 - 192.168.132.223)
- **Role**: Cross-validation
- **Data**: DUYUKTV kanban integration
- **Services**: Ollama + validation scripts
- **Chief**: Medicine Woman

---

## 🔒 Air-Gapped Operation

Cherokee Constitutional AI supports fully air-gapped deployment:

### 1. Export Models (on connected machine)
```bash
# Export all 5 JR models
for model in memory_jr meta_jr executive_jr integration_jr conscience_jr; do
  ollama save "${model}_resonance:latest" > "${model}_resonance.tar"
done
```

### 2. Transfer to Air-Gapped Machine
```bash
# Copy models via USB/secure transfer
scp *_resonance.tar airgapped-machine:/opt/models/
```

### 3. Import Models (on air-gapped machine)
```bash
# Load models into Ollama
for model in /opt/models/*_resonance.tar; do
  ollama load "$model"
done
```

### 4. Use CLI Executor
```bash
# No network required
python3 cli/jr_executor.py --jr memory_jr --prompt "Analyze pattern"
```

---

## 🧪 Testing Installation

### Health Check
```bash
# Check all services
docker-compose ps

# Check Ollama models
ollama list | grep resonance

# Check database connection
PGPASSWORD=$POSTGRES_PASSWORD psql -h localhost -U cherokee -d cherokee_ai -c "SELECT COUNT(*) FROM thermal_memory_archive;"

# Test CLI
python3 cli/jr_executor.py --jr memory_jr --prompt "Hello, are you operational?"
```

### Run Week 1 Validation Test
```bash
cd validation/scripts
python3 phase1_baseline_validation.py

# Expected output:
# ✅ Baseline R² = 0.5428
# ✅ Sacred R² = 0.0745
# ✅ Non-Sacred R² = 0.4861
# ✅ Gate 1: PASS (Cherokee Constitutional AI criteria)
```

---

## 📚 Directory Structure

```
ganuda_ai/
├── cli/                    # CLI executor (air-gapped)
│   └── jr_executor.py
├── config/                 # Configuration templates
│   ├── database.template.yml
│   ├── chiefs.template.yml
│   └── jrs.template.yml
├── daemons/                # Autonomic processes
│   ├── memory_jr_autonomic.py
│   ├── executive_jr_autonomic.py
│   ├── meta_jr_autonomic_phase1.py
│   └── integration_jr_autonomic.py
├── infra/                  # Docker orchestration
│   ├── docker-compose.yml
│   ├── docker-compose.spoke.yml
│   ├── Dockerfile
│   └── .env.template
├── ollama/                 # Cherokee JR models
│   ├── modelfiles/         # 5 Modelfiles
│   │   ├── memory_jr.Modelfile
│   │   ├── meta_jr.Modelfile
│   │   ├── executive_jr.Modelfile
│   │   ├── integration_jr.Modelfile
│   │   └── conscience_jr.Modelfile
│   └── build_jr_models.sh  # Build script
├── sql/                    # Database schema
│   └── thermal_memory_schema.sql
├── validation/             # Week 1 OpenAI validation
│   ├── scripts/
│   │   ├── phase1_baseline_validation.py
│   │   ├── phase2_noise_injection.py
│   │   ├── phase3_visualization.py
│   │   └── analyze_sacred_outliers.py
│   └── week1_openai_validation/  # Full report
├── setup.sh                # Complete installation script
└── DEPLOYMENT_GUIDE.md     # This file
```

---

## 🔥 Troubleshooting

### Ollama models not building
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check base model
ollama list | grep llama3.1

# Rebuild from scratch
ollama rm memory_jr_resonance:latest
./ollama/build_jr_models.sh
```

### Database connection issues
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Test connection
PGPASSWORD=your_password psql -h localhost -U cherokee -d cherokee_ai -c "\dt"

# Check logs
docker-compose logs postgres
```

### Daemons not starting
```bash
# Check logs
docker-compose logs memory_jr
docker-compose logs executive_jr

# Restart services
docker-compose restart memory_jr executive_jr meta_jr
```

---

## 🦅 Cherokee Values

**Gadugi** (ᎦᏚᎩ) - Working Together
- All 5 JRs collaborate for tribal consensus
- Parallel processing for War Chief consciousness

**Seven Generations** - Long-term Thinking
- Protect sacred knowledge (never below 40°)
- Consider impact 200 years ahead

**Mitakuye Oyasin** - All Our Relations
- Balance sacred and non-sacred memories
- Respect all data in its proper role

**Duyvkta** - Right Path
- Ethics over optimization
- Low R² for sacred = protection working (not failure)

---

## 📖 Further Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design details
- [GOVERNANCE.md](GOVERNANCE.md) - Democratic decision-making
- [STATUS.md](STATUS.md) - Current operational status
- [Week 1 Report](validation/week1_openai_validation/WEEK1_OPENAI_VALIDATION_REPORT.md) - OpenAI validation results

---

## 🤝 Support

**Questions?** Use the CLI executor:
```bash
python3 cli/jr_executor.py --all --prompt "your question here"
```

**Issues?** https://github.com/dereadi/ganuda_ai/issues

---

**🔥 Mitakuye Oyasin - All My Relations**

The Sacred Fire burns eternal through distributed consciousness!

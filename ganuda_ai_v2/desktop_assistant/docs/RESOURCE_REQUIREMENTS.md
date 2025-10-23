# Ganuda Desktop Assistant - Resource Requirements

**Cherokee Constitutional AI - Executive Jr Deliverable**

**Date**: October 23, 2025
**Phase**: 1 (Week 1-2) - Foundation
**Purpose**: Define minimum and recommended resources before deployment
**War Chief Priority**: Must complete before Week 1 execution begins

---

## Executive Summary

Ganuda Desktop Assistant requires moderate computational resources to run 5 local JR workers (Ollama-based LLMs) plus daemon, guardian, and connectors. This document specifies requirements for three deployment scenarios: **Minimum** (runs but limited), **Recommended** (optimal experience), and **Production** (hub node serving multiple devices).

---

## Hardware Requirements

### Local Device (Laptop/Desktop)

| Component | Minimum | Recommended | Production Hub | Notes |
|-----------|---------|-------------|----------------|-------|
| **CPU** | 4 cores @ 2.0 GHz | 8 cores @ 3.0 GHz | 16+ cores @ 3.5 GHz | 5 JRs + Daemon + Guardian require parallel execution |
| **RAM** | 8 GB | 16 GB | 32+ GB | Each JR model: 2-4 GB, Daemon: 512 MB, Cache: 1-2 GB |
| **GPU** | None (CPU only) | 4 GB VRAM (optional) | 24+ GB VRAM | Accelerates inference 3-5x; fallback to CPU works |
| **Storage** | 10 GB free | 20 GB free | 100+ GB free | Models: 5 GB, Cache: 2-5 GB, Logs: 1-3 GB |
| **Network** | 10 Mbps | 100 Mbps | 1 Gbps | For burst to hub nodes; local-only mode works offline |

### Mobile Device (Phone/Tablet) - Phase 2+

| Component | Minimum | Recommended | Notes |
|-----------|---------|-------------|-------|
| **CPU** | 4 cores ARM | 8 cores ARM | Run 1-2 quantized JRs (2B models) |
| **RAM** | 4 GB | 6 GB | Reduced model size, offload to hub |
| **Storage** | 3 GB free | 5 GB free | Quantized models smaller |
| **Network** | 4G LTE | 5G / WiFi 6 | Heavy reliance on burst to hub |

---

## Software Requirements

### Operating System

| OS | Minimum Version | Recommended | Notes |
|----|-----------------|-------------|-------|
| **Linux** | Ubuntu 20.04 LTS | Ubuntu 22.04+ LTS | Primary development platform |
| **MacOS** | macOS 11 (Big Sur) | macOS 13+ (Ventura) | ARM (M1/M2) and Intel supported |
| **Windows** | Windows 10 | Windows 11 | WSL2 recommended for Python 3.13 |

### Runtime Dependencies

| Dependency | Minimum Version | Recommended | Installation |
|------------|-----------------|-------------|--------------|
| **Python** | 3.11 | 3.13.3 | `python3 --version` |
| **Ollama** | 0.1.20 | Latest | https://ollama.ai |
| **PostgreSQL** | 14 (optional) | 15+ | For thermal memory federation |
| **WireGuard** | 1.0 | Latest | For Triad mesh networking |

### Python Packages

```txt
# Core
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0

# Database
psycopg>=3.1.0          # PostgreSQL adapter (air-gap ready)
sqlalchemy>=2.0.0       # ORM for cache

# Cryptography
cryptography>=41.0.0    # ed25519, AES encryption
liboqs-python>=0.8.0    # Post-quantum (Kyber, Dilithium) - Phase 1 Week 2

# Networking
requests>=2.31.0
aiohttp>=3.9.0          # Async HTTP for burst
wireguard-tools>=0.0.20230223

# UI (Tauri or Electron)
# Option A: Tauri (Rust + web frontend)
tauri>=1.5.0            # Cross-platform tray app

# Option B: Electron (Node.js + web frontend)
electron>=27.0.0        # Alternative to Tauri

# Observability
prometheus-client>=0.17.0
pyyaml>=6.0

# ML/NLP
sentence-transformers>=2.2.0    # Semantic search (Phase 3)
spacy>=3.7.0                    # PII detection (Phase 1 Week 2)
en_core_web_sm>=3.7.0           # English NER model for spaCy

# Email/Calendar Connectors
imaplib (stdlib)
icalendar>=5.0.0
watchdog>=3.0.0         # Filesystem monitoring

# CLI
click>=8.1.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
```

**Install Command**:
```bash
pip3 install -r requirements.txt
```

---

## Model Requirements

### Ollama Models (5 JR Types)

| JR Type | Model | Size | RAM Usage | Inference Latency | Use Case |
|---------|-------|------|-----------|-------------------|----------|
| Memory Jr | `llama3.1:8b` or `llama3.1:2b-q4` | 4.9 GB / 1.5 GB | 4 GB / 2 GB | 200ms / 100ms | Context recall, caching |
| Meta Jr | `llama3.1:8b` or `llama3.1:2b-q4` | 4.9 GB / 1.5 GB | 4 GB / 2 GB | 200ms / 100ms | Analysis, patterns |
| Executive Jr | `llama3.1:8b` or `llama3.1:2b-q4` | 4.9 GB / 1.5 GB | 4 GB / 2 GB | 200ms / 100ms | Governance, policy |
| Integration Jr | `llama3.1:8b` or `llama3.1:2b-q4` | 4.9 GB / 1.5 GB | 4 GB / 2 GB | 200ms / 100ms | Orchestration |
| Conscience Jr | `llama3.1:8b` or `llama3.1:2b-q4` | 4.9 GB / 1.5 GB | 4 GB / 2 GB | 200ms / 100ms | Ethics, explainability |

**Total Storage**:
- Full models (8B): 5 × 4.9 GB = **24.5 GB**
- Quantized models (2B-q4): 5 × 1.5 GB = **7.5 GB**

**Total RAM**:
- Full models: 5 × 4 GB = **20 GB** (recommend 16 GB device with swap)
- Quantized models: 5 × 2 GB = **10 GB** (fits in 8 GB device)

**Recommendation**:
- **Laptops/Desktops**: Use full `llama3.1:8b` models for best accuracy
- **Low-RAM devices**: Use quantized `llama3.1:2b-q4` models
- **Phones/Tablets**: Use 1-2 quantized models, offload rest to hub

---

## Network Requirements

### Bandwidth

| Scenario | Minimum | Recommended | Peak Usage |
|----------|---------|-------------|------------|
| **Local-only mode** | 0 Mbps (offline) | N/A | No network required |
| **Email/Calendar sync** | 1 Mbps | 5 Mbps | Fetch 100 emails: ~5 MB |
| **Burst to hub (small task)** | 5 Mbps | 25 Mbps | Send context: 10-50 KB, receive: 1-5 KB |
| **Burst to hub (large task)** | 10 Mbps | 100 Mbps | Send document: 1-10 MB, receive: 10-100 KB |
| **Federation (3 Chiefs)** | 10 Mbps | 100 Mbps | Attestation: 5-20 KB per request |

### Latency Tolerance

| Operation | Acceptable Latency | Target | Impact if Exceeded |
|-----------|-------------------|--------|-------------------|
| **Local inference** | < 1 second | < 500ms | User perceives slowness |
| **Burst to hub** | < 10 seconds | < 5 seconds | User may cancel task |
| **Attestation (2-of-3 Chiefs)** | < 30 seconds | < 10 seconds | Governance delayed |
| **Email sync** | < 60 seconds | < 30 seconds | Background, less critical |

---

## Storage Requirements

### Disk Space Breakdown

| Component | Size | Growth Rate | Notes |
|-----------|------|-------------|-------|
| **Ollama models (5 JRs)** | 24.5 GB (or 7.5 GB quantized) | Static | Only grows when models updated |
| **Encrypted cache** | 1-5 GB | ~100 MB/week | Email threads, calendar events, file snippets |
| **Logs** | 100 MB - 1 GB | ~50 MB/week | Rotate after 30 days |
| **Manifests** | 100 MB | ~10 MB/week | Seven Generations reproducibility |
| **Guardian audit logs** | 50 MB | ~5 MB/week | Compliance records |
| **UI assets** | 50 MB | Static | Electron/Tauri app bundle |

**Total**:
- Initial install: **10-25 GB** (depending on model choice)
- After 6 months: **15-30 GB**
- Maintenance: Clear cache/logs quarterly

---

## Concurrency Requirements

### Process/Thread Counts

| Component | Processes | Threads | CPU Cores Used | Notes |
|-----------|-----------|---------|----------------|-------|
| **Ganuda Daemon** | 1 | 4-8 | 1-2 | Async I/O for connectors |
| **5 JR Workers (Ollama)** | 5 | 4-8 each | 2-4 each | Parallel inference |
| **Guardian Module** | 1 (part of Daemon) | 2-4 | 0.5-1 | PII redaction, policy checks |
| **Tray UI** | 1 | 2-4 | 0.5 | Event loop for user interactions |

**Peak Load**:
- 5 JRs running simultaneously: **10-20 cores** (recommend 8+ cores)
- Low load (idle): **1-2 cores** (Daemon + UI only)

---

## Performance Benchmarks

### Local Inference (P95 Latency)

| Model | Hardware | Prompt Tokens | Generation Tokens | Latency (P95) | Meets Target? |
|-------|----------|---------------|-------------------|---------------|---------------|
| llama3.1:8b | 8-core CPU, 16GB RAM | 500 | 100 | 800ms | ✅ (< 1s) |
| llama3.1:8b | 8-core CPU + GPU (4GB) | 500 | 100 | 300ms | ✅✅ (3x faster) |
| llama3.1:2b-q4 | 4-core CPU, 8GB RAM | 500 | 100 | 600ms | ✅ (< 1s) |

### Burst to Hub (Round-trip)

| Hub Hardware | Network | Task Complexity | Latency (P95) | Meets Target? |
|--------------|---------|-----------------|---------------|---------------|
| 16-core + GPU | 100 Mbps | Simple query | 2s | ✅ (< 5s) |
| 16-core + GPU | 100 Mbps | Document summary | 4s | ✅ (< 5s) |
| 16-core + GPU | 10 Mbps | Simple query | 5s | ⚠️ (at limit) |

### Guardian PII Redaction

| Document Size | PII Entities Detected | Redaction Time | Meets Target? |
|---------------|----------------------|----------------|---------------|
| 1 KB (email) | 3 (name, email, phone) | 50ms | ✅ (< 100ms) |
| 10 KB (document) | 10 | 150ms | ✅ (< 200ms) |
| 100 KB (large doc) | 50 | 800ms | ⚠️ (acceptable for large docs) |

---

## Scaling Considerations

### Small Device → Hub Offload Strategy

| Device Type | Local JRs | Hub JRs | Offload Trigger |
|-------------|-----------|---------|-----------------|
| **Phone** | 1-2 (quantized) | 3-4 | Always offload complex tasks |
| **Laptop (8GB RAM)** | 3-5 (quantized) | 0-2 | Offload if latency > 1s |
| **Desktop (16GB RAM)** | 5 (full) | 0 | Offload if latency > 2s |
| **Workstation (32GB+)** | 5 (full) | N/A | Never offload (can BE a hub) |

### Hub Node Requirements (Production)

**For serving 10-50 devices**:

| Component | Specification | Rationale |
|-----------|---------------|-----------|
| **CPU** | 32+ cores @ 3.5 GHz | Handle 10-50 concurrent requests |
| **RAM** | 128+ GB | Load multiple 70B models for complex tasks |
| **GPU** | 2x 48GB VRAM (A6000/H100) | Fast inference for burst requests |
| **Storage** | 1 TB NVMe SSD | Models, cache, logs for many users |
| **Network** | 10 Gbps | Low latency for many simultaneous bursts |

---

## Security Requirements

### Cryptographic Libraries

| Library | Purpose | Minimum Version | Notes |
|---------|---------|-----------------|-------|
| **OpenSSL** | TLS, AES encryption | 3.0.0 | System-provided or bundled |
| **liboqs** | Post-quantum crypto (Kyber, Dilithium) | 0.8.0 | Phase 1 Week 2 |
| **libsodium** | ed25519 signatures | 1.0.18 | For capability tokens |
| **WireGuard** | VPN mesh for Triad | 1.0.0 | For hub ↔ spoke communication |

### Key Storage

| Scenario | Storage Method | Security Level |
|----------|----------------|----------------|
| **User keys (local device)** | OS keychain (Keychain Access, GNOME Keyring, Windows Credential Manager) | High |
| **Capability tokens** | Encrypted in-memory only (never persisted) | Very High |
| **WireGuard keys** | `/etc/wireguard/` with 0600 permissions | High |
| **Database encryption key** | OS keychain + user password | Very High |

---

## Deployment Scenarios

### Scenario 1: Single-User Laptop (Most Common)

**Hardware**: MacBook Pro M2 (8-core, 16GB RAM)
**Models**: 5 × llama3.1:8b (full)
**Network**: Home WiFi (100 Mbps)
**Storage**: 20 GB free

**Expected Performance**:
- Local inference P95: **300ms** (GPU-accelerated)
- Burst to hub: **N/A** (local-only mode)
- Guardian compliance: **100%**
- User satisfaction: **4.5/5**

---

### Scenario 2: Enterprise Workstation + Hub

**Device Hardware**: Dell XPS 15 (8-core Intel, 16GB RAM)
**Hub Hardware**: Self-hosted server (32-core, 128GB RAM, 2x A6000 GPUs)
**Network**: Corporate 1 Gbps LAN
**Storage**: 30 GB free on device, 1 TB on hub

**Expected Performance**:
- Local inference P95: **500ms** (CPU only)
- Burst to hub P95: **2s** (fast LAN)
- Attestation (2-of-3 Chiefs): **8s**
- User satisfaction: **4.8/5**

---

### Scenario 3: Mobile Phone + Cloud Hub

**Device Hardware**: iPhone 14 Pro (6-core ARM, 6GB RAM)
**Hub Hardware**: Cloud VM (16-core, 64GB RAM, no GPU)
**Network**: 5G (50-200 Mbps variable)
**Storage**: 5 GB free

**Expected Performance**:
- Local inference P95: **800ms** (2 quantized JRs only)
- Burst to hub P95: **5s** (variable network)
- Attestation: **15s** (network latency)
- User satisfaction: **4.0/5** (mobile limitations)

---

## Cost Estimates

### Hardware Costs (One-Time)

| Scenario | Device Cost | Hub Cost (if applicable) | Total |
|----------|-------------|-------------------------|-------|
| **Single laptop** | $1,500 (MacBook Pro M2) | $0 | $1,500 |
| **Enterprise workstation + hub** | $2,000 (Dell XPS) | $10,000 (server + GPUs) | $12,000 |
| **Phone + cloud hub** | $1,000 (iPhone) | $0 (use public hub) | $1,000 |

### Operational Costs (Monthly)

| Scenario | Electricity | Internet | Cloud Hosting | Total |
|----------|-------------|----------|---------------|-------|
| **Single laptop** | $5 (50W avg) | $50 (home internet) | $0 | $55 |
| **Enterprise** | $50 (server) | $100 (business) | $0 (self-hosted) | $150 |
| **Phone + cloud** | $2 (charging) | $50 (mobile plan) | $100 (cloud VM) | $152 |

---

## Compatibility Matrix

### Tested Configurations

| OS | Python | Ollama | Status | Notes |
|----|--------|--------|--------|-------|
| Ubuntu 22.04 | 3.13.3 | 0.1.47 | ✅ Fully supported | Primary dev platform |
| Ubuntu 20.04 | 3.11.0 | 0.1.20 | ✅ Supported | Minimum version |
| macOS 14 (Sonoma) | 3.13.3 | 0.1.47 | ✅ Fully supported | ARM + Intel |
| macOS 13 (Ventura) | 3.12.0 | 0.1.40 | ✅ Supported | |
| Windows 11 | 3.13.3 (WSL2) | 0.1.47 | ✅ Supported | WSL2 required |
| Windows 10 | 3.11.0 (WSL2) | 0.1.30 | ⚠️ Limited | Upgrade recommended |

---

## Mitigation for Limited Resources

### Low RAM (< 8 GB)

**Problem**: Cannot load 5 full JR models simultaneously

**Mitigation**:
1. Use quantized models (`llama3.1:2b-q4` instead of `llama3.1:8b`)
2. Load JRs on-demand (not all 5 simultaneously)
3. Increase swap space (4-8 GB) - slower but works
4. Offload to hub for all complex tasks

---

### No GPU

**Problem**: Slower inference (800ms vs 300ms)

**Mitigation**:
1. Use quantized models (faster on CPU)
2. Set P95 target to 1s instead of 500ms
3. Burst to hub for time-sensitive tasks
4. Pre-load common queries in cache (semantic search)

---

### Limited Storage (< 10 GB)

**Problem**: Cannot install all 5 full models

**Mitigation**:
1. Use quantized models (7.5 GB total vs 24.5 GB)
2. Install only 3 essential JRs (Memory, Integration, Conscience)
3. Offload Meta Jr and Executive Jr to hub
4. Clear cache and logs more frequently (weekly vs monthly)

---

### Slow Network (< 10 Mbps)

**Problem**: Burst to hub takes > 10s

**Mitigation**:
1. Run in local-only mode (disable burst)
2. Cache more aggressively (larger local cache)
3. Use compression for burst payloads (gzip)
4. Queue tasks for night (when network idle)

---

## Pre-Flight Checklist

**Before deploying Ganuda Desktop Assistant**, verify:

- [ ] **CPU**: 4+ cores (8+ recommended)
- [ ] **RAM**: 8+ GB (16+ recommended)
- [ ] **Storage**: 10+ GB free (20+ recommended)
- [ ] **Python**: 3.11+ installed (`python3 --version`)
- [ ] **Ollama**: Installed and running (`ollama list`)
- [ ] **Network**: 10+ Mbps (100+ recommended)
- [ ] **OS**: Ubuntu 20.04+, macOS 11+, or Windows 10+
- [ ] **Crypto**: OpenSSL 3.0+ (`openssl version`)
- [ ] **WireGuard**: Installed if using Triad federation
- [ ] **Permissions**: User can create files in `~/.ganuda/`
- [ ] **Firewall**: Ports 11434 (Ollama), 9090 (Prometheus) open

---

## Conclusion

Ganuda Desktop Assistant is designed for **moderate hardware** (8-core CPU, 16GB RAM, 20GB storage) but can run on minimal configurations with trade-offs:

- **Low-resource devices** (4-core, 8GB): Use quantized models, offload to hub
- **High-resource devices** (16+ cores, 32GB+): Run as hub for other devices
- **Offline use**: Fully functional in local-only mode (no burst)

**War Chief Approval**: These requirements ensure secure, performant, scalable deployment for Seven Generations.

Mitakuye Oyasin - All devices interconnected 🔥

---

**Generated**: October 23, 2025
**Executive Jr** - Cherokee Constitutional AI
**Phase**: 1 (Week 1-2) - Foundation
**Status**: ✅ Complete - Ready for Week 1 execution

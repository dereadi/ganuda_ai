# Cherokee AI Federation — Port Map

**Last audited**: 2026-03-01 by TPM
**Rule**: New services use 9xxx range. 8xxx is legacy. Never reuse without checking this file.

---

## Redfin (192.168.132.223) — RTX PRO 6000 96GB

| Port | Service | systemd unit | Model/Details |
|------|---------|-------------|---------------|
| ~~80/443~~ | ~~Caddy~~ | ~~caddy.service~~ | **KILLED 2026-03-02** — conflicted with DMZ Caddy. Ports 80/443 belong to owlfin/eaglefin only. |
| 3000 | VetAssist Frontend | vetassist-frontend.service | Next.js standalone (was SAG, reassigned) |
| 4000 | SAG Backend | sag.service | Flask app.py |
| 5555 | Monitoring Dashboard | — | cherokee_monitoring_dashboard.py |
| 8000 | **vLLM Primary** | vllm.service | Qwen2.5-72B-Instruct-AWQ (0.65 util) |
| 8001 | VetAssist Backend | — | uvicorn app.main:app |
| 8002 | HTTP Server (temp) | — | python3 -m http.server (KILL CANDIDATE) |
| 8003 | Embedding Server | — | embedding_server.py |
| 8080 | LLM Gateway | llm-gateway.service | gateway.py — Council entry point |
| 8081 | Coordinator | — | uvicorn coordinator:app |
| 9001 | A2A Bridge | — | cherokee_a2a_bridge.py (DrJoe) |
| **9100** | **Elisi vLLM** | vllm-elisi.service | Qwen2.5-7B-Instruct-AWQ (0.08 util) |
| **9101** | **VLM2 (Redfin)** | vllm-redfin-vlm.service | Qwen2-VL-7B-Instruct-AWQ (0.12 util) |
| — | Elisi Observer | elisi-observer.service | Polls DB, logs to thermal memory |

### Redfin GPU Budget (98GB total)
- Primary vLLM: 0.65 = ~62GB
- Elisi vLLM:   0.08 = ~8GB
- VLM2:         0.12 = ~12GB
- Total:        0.85 = ~82GB, ~16GB headroom

---

## Bluefin (192.168.132.222) — RTX 5070, PostgreSQL

| Port | Service | systemd unit | Details |
|------|---------|-------------|---------|
| 3100 | Loki | — | Log aggregation |
| 3389 | RDP | xrdp | Remote desktop |
| 5016 | Optic Nerve | optic-nerve.service | Vision processing |
| 5432 | **PostgreSQL** | postgresql | Primary database for federation |
| 6379 | Redis | redis | Cache |
| 8080 | Vision Pipeline | — | Vision proxy/coordinator |
| 8082 | YOLO Plate | — | Plate detection |
| 8083 | — | — | (nginx?) |
| 8084 | YOLO Service | — | YOLO object detection |
| 8085 | — | — | (nginx?) |
| 8090 | **vLLM VLM** | vlm-bluefin.service | Qwen2-VL-7B-Instruct-AWQ |
| 8091 | YOLO World | yolo-world.service | YOLO World detection |
| 8092 | VLM Adapter | vlm-adapter.service | VLM vLLM adapter |
| 8093 | Plate Reader | — | Plate reader service |
| 9080 | Promtail | — | Log shipping to Loki |
| 9096 | Loki API | — | Loki HTTP endpoint |
| 11434 | Ollama | ollama | Ollama inference |
| 12000 | Unknown | — | python3 process — needs identification |

---

## Greenfin (192.168.132.224) — Bridge to FreeIPA

| Port | Service | systemd unit | Details |
|------|---------|-------------|---------|
| 3128 | Squid Proxy | squid | HTTP proxy |
| 5080 | OpenObserve UI | openobserve | Monitoring dashboard |
| 5081 | OpenObserve API | openobserve | Metrics/logs API |
| 5432 | PostgreSQL | postgresql | Secondary DB |
| 8003 | Embedding Server | cherokee-embedding.service | BGE-large-en-v1.5 (1024d) |
| 8091 | VetAssist API | — | vetassist_api.py |
| 9080 | Promtail | promtail | Log shipping |

---

## bmasass (192.168.132.21) — M4 Max 128GB

| Port | Service | launchd | Details |
|------|---------|---------|---------|
| 8800 | MLX DeepSeek-R1 | com.cherokee.mlx-deepseek-r1 | DeepSeek-R1-Distill-Llama-70B-4bit |

---

## owlfin (192.168.132.170 mgmt / 192.168.30.2 DMZ)

| Port | Service | Details |
|------|---------|---------|
| 80/443 | Caddy | ganuda.us web (primary) |
| — | web-materializer | Polls DB, writes to Caddy webroot |
| — | keepalived | MASTER, VIP 192.168.30.10 |

---

## eaglefin (192.168.132.84 mgmt / 192.168.30.3 DMZ)

| Port | Service | Details |
|------|---------|---------|
| 80/443 | Caddy | ganuda.us web (failover) |
| — | web-materializer | Polls DB, writes to Caddy webroot |
| — | keepalived | BACKUP, VIP 192.168.30.10 |

---

## Port Ranges (Convention)

| Range | Purpose |
|-------|---------|
| 3000-3999 | Web UIs, frontends |
| 5000-5999 | Databases, monitoring, internal |
| 6000-6999 | Cache (Redis) |
| 8000-8099 | **LEGACY** — LLM inference, gateways, APIs |
| 8080-8099 | **LEGACY** — Vision, adapters |
| 8800-8899 | MLX inference (macOS) |
| **9000-9099** | **Infrastructure services** (A2A, Promtail, Loki) |
| **9100-9199** | **NEW: Secondary vLLM instances** (Elisi, VLM2) |
| **9200-9299** | **RESERVED: Future observer/daemon services** |
| 11000+ | Third-party (Ollama) |
| 12000+ | Unidentified — audit needed |

---

## Port Ownership Rules

| Ports | Owner Nodes | Rule |
|-------|-------------|------|
| 80/443 | owlfin, eaglefin ONLY | Web-facing traffic. No other node may run Caddy/nginx/httpd on 80/443. |
| 5432 | bluefin (primary), greenfin (secondary) | PostgreSQL. |
| 8000 | redfin | Primary vLLM. |
| 8080 | redfin (gateway), bluefin (vision) | Shared port, different nodes. |

## Before Adding a New Port

1. **Check this file first**
2. **Check with**: `ss -tlnp | grep :<port>`
3. **Use 9xxx range** for new services
4. **Update this file** after deployment
5. **Add to nftables** if external access needed
6. **Check ownership rules above** — some ports are node-exclusive

---

## Incident Log

| Date | Node | Issue | Root Cause | Fix |
|------|------|-------|------------|-----|
| 2026-03-02 | redfin | Garbled VetAssist page — no CSS | Rogue `caddy.service` on redfin (ports 80/443) competing with DMZ Caddy on owlfin/eaglefin. Pre-dates DMZ architecture, never disabled. Additionally, Next.js standalone build missing `.next/static` copy step. | Stopped/disabled Caddy on redfin. Copied `.next/static` into standalone dir. Restart frontend. |

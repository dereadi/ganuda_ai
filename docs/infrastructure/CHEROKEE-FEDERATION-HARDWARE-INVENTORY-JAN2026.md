# Cherokee AI Federation - Complete Hardware Inventory

**Date:** January 15, 2026
**Classification:** Internal Infrastructure
**Maintainer:** TPM (Darrell)
**Prepared For:** Erika Hammontree

---

## Executive Summary

The Cherokee AI Federation operates on a 7-node distributed infrastructure with 3 VLANs for security segmentation. Total compute resources include 2 GPUs (1 NVIDIA Blackwell 96GB + 1 RTX 5070), 512GB+ RAM across nodes, and 50TB+ storage.

---

## 1. Physical Network Topology

```
                                   INTERNET
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │   nachocheese (Router)       │
                        │   (ISP Gateway)              │
                        └─────────────────────────────┘
                                      │
                                      ▼
                        ┌─────────────────────────────┐
                        │   TL-SG1428PE Switch        │
                        │   192.168.132.132           │
                        │   28-port PoE+ Managed      │
                        └─────────────────────────────┘
                            │         │         │
              ┌─────────────┘         │         └─────────────┐
              ▼                       ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
    │    VLAN 1       │     │    VLAN 10      │     │    VLAN 20      │
    │ 192.168.132.0/24│     │ 192.168.10.0/24 │     │ 192.168.20.0/24 │
    │    COMPUTE      │     │    IDENTITY     │     │    SANCTUM      │
    └─────────────────┘     └─────────────────┘     └─────────────────┘
           │                       │                       │
           │                       │                       │
    ┌──────┴──────┐         ┌──────┴──────┐         ┌──────┴──────┐
    │  redfin     │         │  silverfin  │         │  goldfin    │
    │  bluefin    │◄───────►│             │◄───────►│             │
    │  greenfin   │         │  (FreeIPA)  │         │  (PII Vault)│
    │  sasass     │         └─────────────┘         └─────────────┘
    │  sasass2    │                │                       │
    │  tpm-macbook│                │                       │
    └─────────────┘                │                       │
                                   └───────┬───────────────┘
                                           │
                                    greenfin (Router)
                                    Inter-VLAN Gateway
```

---

## 2. Node Inventory

### 2.1 VLAN 1 - Compute Zone (192.168.132.0/24)

#### REDFIN (Primary AI Inference)
| Attribute | Value |
|-----------|-------|
| **Hostname** | redfin |
| **IP Address** | 192.168.132.223 |
| **Role** | GPU Inference, VetAssist Application Server |
| **CPU** | AMD Ryzen 9 9950X3D 16-Core |
| **RAM** | 128 GB DDR5 |
| **GPU** | NVIDIA RTX PRO 6000 (Blackwell) - 96GB VRAM |
| **Storage** | 2TB NVMe + 4TB SSD |
| **OS** | Ubuntu 24.04.3 LTS |
| **Services** | vLLM (8000), LLM Gateway (8080), VetAssist Backend (8001), VetAssist Frontend (3000), SAG UI (4000), Kanban (3001) |
| **Status** | Online |

#### BLUEFIN (Database & IoT Hub)
| Attribute | Value |
|-----------|-------|
| **Hostname** | bluefin |
| **IP Address** | 192.168.132.222 |
| **Role** | Primary Database, Home Automation Hub |
| **CPU** | Intel Core i9-14900KF |
| **RAM** | 128 GB DDR5 |
| **GPU** | NVIDIA RTX 5070 |
| **Storage** | 17TB (multiple drives) |
| **OS** | Ubuntu |
| **Services** | PostgreSQL (5432), Home Assistant (8123), Frigate NVR (8971), Grafana (3000), Mosquitto MQTT (1883) |
| **Databases** | zammad_production, triad_federation |
| **Status** | Online |

#### GREENFIN (Network Router & Monitoring)
| Attribute | Value |
|-----------|-------|
| **Hostname** | greenfin |
| **IP Address** | 192.168.132.224 (VLAN 1), 192.168.10.1 (VLAN 10), 192.168.20.1 (VLAN 20) |
| **Role** | Inter-VLAN Router, HTTP Proxy, Log Aggregation |
| **CPU** | AMD Ryzen AI MAX+ 395 w/ Radeon 8060S |
| **RAM** | 128 GB |
| **GPU** | Integrated Radeon 8060S |
| **Storage** | 1TB NVMe |
| **OS** | Ubuntu 24.04.3 LTS |
| **Services** | nftables firewall, Squid Proxy (3128), Promtail |
| **Network Interfaces** | eno1 (VLAN 1), eno1.10 (VLAN 10), eno1.20 (VLAN 20) |
| **Status** | Online |

#### SASASS (Mac Studio #1)
| Attribute | Value |
|-----------|-------|
| **Hostname** | sasass |
| **IP Address** | 192.168.132.241 |
| **Role** | Edge Development, Claude Code CLI |
| **CPU** | Apple M1 Max |
| **RAM** | 64 GB Unified Memory |
| **GPU** | M1 Max (32-core) |
| **Storage** | 2TB SSD |
| **OS** | macOS 15.5 Sequoia |
| **Services** | Development environment, Claude Code |
| **Status** | Online |

#### SASASS2 (Mac Studio #2)
| Attribute | Value |
|-----------|-------|
| **Hostname** | sasass2 |
| **IP Address** | 192.168.132.242 |
| **Role** | Edge Development, Claude Code CLI |
| **CPU** | Apple M1 Max |
| **RAM** | 64 GB Unified Memory |
| **GPU** | M1 Max (32-core) |
| **Storage** | 2TB SSD |
| **OS** | macOS 15.5 Sequoia |
| **Services** | Development environment, Claude Code |
| **Status** | Online |

#### TPM-MACBOOK (Orchestration Workstation)
| Attribute | Value |
|-----------|-------|
| **Hostname** | tpm-macbook (bmasass) |
| **IP Address** | DHCP / Tailscale |
| **Role** | Primary Orchestration, TPM Workstation |
| **CPU** | Apple M4 |
| **RAM** | 128 GB Unified Memory |
| **GPU** | M4 (integrated) |
| **Storage** | 2TB SSD |
| **OS** | macOS 15.6 Sequoia |
| **Services** | Claude Code CLI, SSH orchestration |
| **Status** | Online |

---

### 2.2 VLAN 10 - Identity Zone (192.168.10.0/24)

#### SILVERFIN (Identity Authority)
| Attribute | Value |
|-----------|-------|
| **Hostname** | silverfin |
| **IP Address** | 192.168.10.10 |
| **Role** | FreeIPA Identity Authority |
| **CPU** | Beelink SER5 (AMD Ryzen) |
| **RAM** | 32 GB |
| **GPU** | None |
| **Storage** | 512GB SSD |
| **OS** | Rocky Linux 9 |
| **Services** | FreeIPA Server, Kerberos KDC, LDAP/LDAPS (389/636), Dogtag CA, DNS |
| **Access** | Restricted - VLAN 10 only + specific rules |
| **Status** | Online |

---

### 2.3 VLAN 20 - Sanctum Zone (192.168.20.0/24)

#### GOLDFIN (PII + PCI Vault - Interim)
| Attribute | Value |
|-----------|-------|
| **Hostname** | goldfin |
| **IP Address** | 192.168.20.10 |
| **Tailscale IP** | 100.x.x.x (configured Jan 15, 2026) |
| **Role** | PII Vault + PCI Vault (interim until platinumfin) |
| **CPU** | TBD |
| **RAM** | 32 GB |
| **GPU** | None |
| **Storage** | 1TB SSD (LUKS encrypted) |
| **OS** | Rocky Linux 9 |
| **Services** | PostgreSQL (vetassist_pii + vetassist_pci) |
| **Firewall** | firewalld DROP zone (strict) |
| **Access** | Tailscale VPN only, SSH from admin IPs |
| **Status** | Online |

---

### 2.4 VLAN 30 - Financial Zone (192.168.30.0/24) - PLANNED

#### PLATINUMFIN (PCI Vault - Planned)
| Attribute | Value |
|-----------|-------|
| **Hostname** | platinumfin |
| **IP Address** | 192.168.30.10 (planned) |
| **Role** | Dedicated PCI-DSS vault for financial data |
| **Hardware** | TBD (similar to goldfin) |
| **OS** | Rocky Linux 9 (planned) |
| **Services** | PostgreSQL (vetassist_pci - migrated from goldfin) |
| **Compliance** | PCI-DSS |
| **Target Date** | Q3 2026 |
| **Status** | Planned |

---

### 2.4 Network Equipment

#### TL-SG1428PE (Managed Switch)
| Attribute | Value |
|-----------|-------|
| **Model** | TP-Link TL-SG1428PE |
| **IP Address** | 192.168.132.132 |
| **Ports** | 28 (24 PoE+, 4 SFP) |
| **PoE Budget** | 250W |
| **Management** | Web UI |
| **VLANs** | 1, 10, 20 configured |
| **Status** | Online |

---

## 3. GPU Resources

| Node | GPU | VRAM | Current Load | Primary Use |
|------|-----|------|--------------|-------------|
| redfin | NVIDIA RTX PRO 6000 (Blackwell) | 96 GB | 85GB (Qwen2.5-32B) | LLM Inference |
| bluefin | NVIDIA RTX 5070 | 12 GB | Idle | Future training/inference |
| sasass | Apple M1 Max (32-core) | 64 GB unified | Variable | Local development |
| sasass2 | Apple M1 Max (32-core) | 64 GB unified | Variable | Local development |
| tpm-macbook | Apple M4 | 128 GB unified | Variable | Orchestration |

**Total GPU VRAM:** 372 GB (hybrid NVIDIA + Apple Silicon)

---

## 4. Storage Summary

| Node | Storage | Type | Purpose |
|------|---------|------|---------|
| redfin | 6 TB | NVMe + SSD | OS, Models, Applications |
| bluefin | 17 TB | HDD + SSD | Database, Media, Backups |
| greenfin | 1 TB | NVMe | OS, Logs |
| sasass | 2 TB | SSD | Development |
| sasass2 | 2 TB | SSD | Development |
| tpm-macbook | 2 TB | SSD | Orchestration |
| silverfin | 512 GB | SSD | FreeIPA |
| goldfin | 1 TB | SSD (encrypted) | PII Vault |

**Total Storage:** ~31.5 TB

---

## 5. Network Segmentation

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          SECURITY ZONES                                  │
├────────────────────┬───────────────────┬─────────────────────────────────┤
│      COMPUTE       │     IDENTITY      │          SANCTUM                │
│     (VLAN 1)       │    (VLAN 10)      │         (VLAN 20)               │
├────────────────────┼───────────────────┼─────────────────────────────────┤
│ 192.168.132.0/24   │ 192.168.10.0/24   │ 192.168.20.0/24                 │
├────────────────────┼───────────────────┼─────────────────────────────────┤
│ • Application SVs  │ • FreeIPA only    │ • PII storage only              │
│ • Databases        │ • Kerberos/LDAP   │ • No direct internet            │
│ • Development      │                   │ • Tailscale access              │
│ • Internet access  │                   │ • Squid proxy for install       │
├────────────────────┼───────────────────┼─────────────────────────────────┤
│ Trust: Medium      │ Trust: High       │ Trust: Highest                  │
└────────────────────┴───────────────────┴─────────────────────────────────┘

Inter-VLAN Traffic Matrix:
┌─────────────┬─────────────┬─────────────┬─────────────┐
│ From \ To   │   VLAN 1    │   VLAN 10   │   VLAN 20   │
├─────────────┼─────────────┼─────────────┼─────────────┤
│   VLAN 1    │     -       │   Allow     │  ICMP only  │
│   VLAN 10   │   Limited   │     -       │   Allow     │
│   VLAN 20   │   FreeIPA   │   FreeIPA   │     -       │
└─────────────┴─────────────┴─────────────┴─────────────┘
```

---

## 6. Service Distribution

### By Node

| Service | Node | Port | Status |
|---------|------|------|--------|
| vLLM (Qwen2.5-32B) | redfin | 8000 | Running |
| LLM Gateway (Council) | redfin | 8080 | Running |
| VetAssist Backend | redfin | 8001 | Running |
| VetAssist Frontend | redfin | 3000 | Running |
| SAG Unified UI | redfin | 4000 | Running |
| Kanban Board | redfin | 3001 | Running |
| PostgreSQL (main) | bluefin | 5432 | Running |
| Home Assistant | bluefin | 8123 | Running |
| Grafana | bluefin | 3000 | Running |
| Frigate NVR | bluefin | 8971 | Running |
| Mosquitto MQTT | bluefin | 1883 | Running |
| Squid Proxy | greenfin | 3128 | Running |
| FreeIPA | silverfin | 443, 389, 636, 88 | Running |
| PostgreSQL (PII) | goldfin | 5432 | Planned |

---

## 7. Capacity Planning

### Current Utilization

| Resource | Total | Used | Available |
|----------|-------|------|-----------|
| GPU VRAM (redfin) | 96 GB | 85 GB | 11 GB |
| RAM (federation) | 576 GB | ~200 GB | 376 GB |
| Storage | 31.5 TB | ~12 TB | 19.5 TB |

### Growth Runway

| Metric | Current | Capacity | Headroom |
|--------|---------|----------|----------|
| LLM Inference | 27 tok/sec | 50 tok/sec (est.) | +85% |
| Database connections | ~10 | 100+ | 90+ |
| Concurrent users | <100 | 1,000+ | 10x |

---

## 8. Disaster Recovery

### Backup Strategy

| Data | Location | Backup | Frequency |
|------|----------|--------|-----------|
| PostgreSQL (bluefin) | bluefin | pg_dump | Planned |
| Thermal Memory | bluefin | pg_dump | Planned |
| VetAssist PII | goldfin | Encrypted backup | Planned |
| Config files | /ganuda/config | Git | On change |
| Documentation | /ganuda/docs | Git | On change |

### Recovery Priority

| Priority | System | RTO | RPO |
|----------|--------|-----|-----|
| P0 | VetAssist Application | 1 hour | 1 day |
| P0 | PostgreSQL (bluefin) | 2 hours | 1 day |
| P1 | vLLM Inference | 4 hours | N/A |
| P1 | PII Vault (goldfin) | 4 hours | 1 day |
| P2 | FreeIPA (silverfin) | 8 hours | 1 day |
| P3 | Home Automation | 24 hours | 1 week |

---

## 9. Maintenance Windows

| Node | Preferred Window | Notes |
|------|------------------|-------|
| redfin | Sunday 2-6 AM CST | GPU workloads can be interrupted |
| bluefin | Sunday 2-6 AM CST | Database maintenance |
| greenfin | Anytime (quick restart) | Router - brief outage |
| silverfin | Sunday 2-6 AM CST | Identity - coordinate |
| goldfin | Sunday 2-6 AM CST | PII - coordinate |

---

## 10. Contact & Escalation

| Issue | First Contact | Escalation |
|-------|---------------|------------|
| Network down | TPM (Darrell) | Nachocheese ISP |
| GPU/vLLM issues | TPM (Darrell) | redfin console |
| Database issues | TPM (Darrell) | bluefin PostgreSQL logs |
| VetAssist issues | TPM (Darrell) | redfin application logs |
| FreeIPA issues | TPM (Darrell) | silverfin FreeIPA logs |

---

*Cherokee AI Federation - For the Seven Generations*
*Infrastructure is the foundation upon which wisdom is built.*

# KB Article: Cherokee AI Federation Infrastructure Status

**KB ID:** KB-INFRASTRUCTURE-STATUS-JAN27-2026
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Category:** Infrastructure

---

## Current Node Status

| Node | IP | Status | Services Running |
|------|-----|--------|------------------|
| redfin | 192.168.132.223 | ✅ ONLINE | vLLM, LLM Gateway, SAG UI, VetAssist (frontend+backend) |
| bluefin | 192.168.132.222 | ✅ ONLINE | PostgreSQL, BookStack (8085), Grafana |
| greenfin | 192.168.132.224 | ✅ ONLINE | Squid proxy, PostgreSQL 16, FreeIPA client |
| goldfin | 192.168.20.10 (VLAN 20) | ✅ ONLINE | PostgreSQL 16.11, vetassist_pii database (empty) |
| sasass | 192.168.132.241 | ✅ ONLINE | Mac Studio - edge development |
| sasass2 | 192.168.132.242 | ✅ ONLINE | Mac Studio - edge development |

---

## Blocking Issues

### 1. Goldfin Network Isolation (P1)

**Status:** RESOLVED - Goldfin is online on VLAN 20 (Sanctum)

**Access Path:** redfin → greenfin → goldfin (192.168.20.10)

**Current State:**
- PostgreSQL 16.11 running ✅
- vetassist_pii database exists (empty) ✅
- pgcrypto extension NOT installed ❌
- PII tables NOT created ❌
- pg_hba.conf only allows greenfin ❌

**Action Required:** Complete PII database setup and configure network proxy
**JR Instruction:** JR-VETASSIST-GOLDFIN-PII-SETUP-JAN27-2026.md

### 2. On-Site APT Mirror Not Configured (P2)

**Impact:** Cannot install packages on isolated VLAN nodes without internet access

**Current State:**
- Ports 8888/8889 not listening on bluefin
- No /srv/mirror directory exists
- Only nginx serving BookStack on port 8085

**Action Required:** Set up apt mirror per JR instruction
**JR Instruction:** JR-APT-MIRROR-SETUP-BLUEFIN-JAN27-2026.md

---

## VetAssist Current Architecture

### Working Components

| Component | Location | Status |
|-----------|----------|--------|
| Frontend (Next.js) | redfin:3000 | ✅ Working |
| Backend (FastAPI) | redfin:8001 | ✅ Working |
| Auth Database | bluefin:triad_federation | ✅ Working |
| Wizard Database | bluefin:zammad_production | ✅ Working |

### Database Split Architecture

- **triad_federation**: User authentication, sessions, accounts
- **zammad_production**: Wizard data, claims, medical info (PII - should migrate to goldfin)

See: KB-VETASSIST-SPLIT-DATABASE-ARCHITECTURE-JAN27-2026.md

---

## Greenfin Services (Reference)

Greenfin is properly configured with:
- PostgreSQL 16
- Squid proxy (port 3128)
- FreeIPA client

Can serve as template for goldfin setup once goldfin is online.

---

## Pending JR Instructions

| Priority | JR ID | Description |
|----------|-------|-------------|
| P1 | JR-VETASSIST-GOLDFIN-PII-SETUP-JAN27-2026 | Complete PII database setup (pgcrypto, tables, network) |
| P1 | JR-VETASSIST-GOLDFIN-PII-MIGRATION-JAN27-2026 | Migrate PII data to goldfin |
| P2 | JR-APT-MIRROR-SETUP-BLUEFIN-JAN27-2026 | Set up local package repo |
| P2 | JR-BM25-PGSEARCH-POC-JAN27-2026 | BM25 search proof of concept |

---

## References

- JR-Goldfin-Security-Architecture.md
- JR-GOLDFIN-DUAL-DATABASE-SETUP-JAN2026.md
- KB-VETASSIST-DASHBOARD-TRANSACTION-FIX-JAN27-2026.md

---

FOR SEVEN GENERATIONS

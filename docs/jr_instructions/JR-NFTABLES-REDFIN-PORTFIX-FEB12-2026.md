# Jr Instruction: Fix Redfin nftables Config — Add Missing Service Ports

**Priority**: P0 — Must fix before deployment
**Kanban**: #547
**Assigned Jr**: Infrastructure Jr.

## Context

The current redfin nftables config only opens ports 22, 80, 443, 8080, 8000, 3001, 4000. But redfin actually runs 15+ services. Deploying as-is would kill Kanban, PostgreSQL, VetAssist, monitoring, embedding server, and ii-researcher. The kanban is on port 3000 (not 3001 as the config says).

## Step 1: Replace the internal services section with complete port list

File: `/ganuda/config/nftables-redfin.conf`

<<<<<<< SEARCH
        # --- LLM Gateway 8080 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8080 accept

        # --- vLLM 8000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8000 accept

        # --- Kanban 3001 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 3001 accept

        # --- SAG 4000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 4000 accept
=======
        # --- Federation services (internal only) ---
        # LLM Gateway 8080
        ip saddr 192.168.132.0/24 tcp dport 8080 accept
        # vLLM inference 8000
        ip saddr 192.168.132.0/24 tcp dport 8000 accept
        # SAG Unified Interface 4000
        ip saddr 192.168.132.0/24 tcp dport 4000 accept
        # Kanban Board 3000 (next-server)
        ip saddr 192.168.132.0/24 tcp dport 3000 accept
        # PostgreSQL 5432
        ip saddr 192.168.132.0/24 tcp dport 5432 accept
        # Cherokee Monitoring Dashboard 5555
        ip saddr 192.168.132.0/24 tcp dport 5555 accept
        # Coordinator 5556 + 8081
        ip saddr 192.168.132.0/24 tcp dport { 5556, 8081 } accept
        # VetAssist Backend 8001
        ip saddr 192.168.132.0/24 tcp dport 8001 accept
        # VetAssist Frontend static 8002
        ip saddr 192.168.132.0/24 tcp dport 8002 accept
        # Embedding Server 8003 (BGE-large)
        ip saddr 192.168.132.0/24 tcp dport 8003 accept
        # ii-researcher 8090
        ip saddr 192.168.132.0/24 tcp dport 8090 accept
>>>>>>> REPLACE

## Verification

After applying, confirm:
1. Port 3001 is NO LONGER in the config (replaced with 3000)
2. Ports 5432, 5555, 5556, 8001, 8002, 8003, 8081, 8090 are all present
3. All service ports restricted to `192.168.132.0/24`

## For Seven Generations

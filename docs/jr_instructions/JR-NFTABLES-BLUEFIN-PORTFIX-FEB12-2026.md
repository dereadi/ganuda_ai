# Jr Instruction: Fix Bluefin nftables Config — Add VLM Service Ports

**Priority**: P0 — Must fix before deployment
**Kanban**: #547
**Assigned Jr**: Infrastructure Jr.

## Context

The bluefin nftables config only opens SSH, PostgreSQL 5432, and Grafana 3000. But bluefin also runs VLM services on ports 8090, 8091, 8092. Deploying as-is would kill the vision pipeline.

## Step 1: Add VLM service ports before the drop rule

File: `/ganuda/config/nftables-bluefin.conf`

<<<<<<< SEARCH
        # --- Grafana 3000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 3000 accept

        # --- Log and drop everything else ---
=======
        # --- Grafana 3000 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 3000 accept

        # --- VLM vLLM 8090 (Qwen2-VL-7B, internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8090 accept
        # --- YOLO World 8091 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8091 accept
        # --- VLM Adapter 8092 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8092 accept

        # --- Log and drop everything else ---
>>>>>>> REPLACE

## Verification

After applying, confirm:
1. Ports 8090, 8091, 8092 appear in the config
2. All restricted to `192.168.132.0/24`
3. Existing rules for SSH, PostgreSQL, Grafana still present

## For Seven Generations

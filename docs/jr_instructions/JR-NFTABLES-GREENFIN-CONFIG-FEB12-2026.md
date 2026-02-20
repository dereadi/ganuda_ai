# Jr Instruction: Create Greenfin nftables Firewall Config

**Priority**: P0 — Security hardening
**Kanban**: #547
**Assigned Jr**: Infrastructure Jr.

## Context

Greenfin (192.168.132.224) is the monitoring/daemons node. It runs OpenObserve, Promtail, and the BGE embedding server. It needs an nftables config matching the redfin/bluefin pattern: default DROP policy, internal-only services, rate-limited SSH.

## Step 1: Create the greenfin nftables configuration

Create `/ganuda/config/nftables-greenfin.conf`

```text
#!/usr/sbin/nft -f
#
# nftables firewall rules for Greenfin (monitoring/embedding node)
# Cherokee AI Federation - Security Phase 3
# Generated: 2026-02-12
#
# REQUIRES ADMIN: Deploy with:
#   sudo cp /ganuda/config/nftables-greenfin.conf /etc/nftables.conf
#   sudo systemctl restart nftables
#   sudo systemctl enable nftables

flush ruleset

table inet filter {

    # ---------------------------------------------------------------
    # Rate-limit sets
    # ---------------------------------------------------------------
    set ssh_meter {
        type ipv4_addr
        flags dynamic
        timeout 1m
    }

    # ---------------------------------------------------------------
    # INPUT chain - default DROP
    # ---------------------------------------------------------------
    chain input {
        type filter hook input priority 0; policy drop;

        # --- Loopback ---
        iif "lo" accept

        # --- Connection tracking ---
        ct state established,related accept
        ct state invalid drop

        # --- ICMP (internal only) ---
        ip saddr 192.168.132.0/24 icmp type { echo-request, echo-reply, destination-unreachable, time-exceeded } accept

        # --- SSH (internal only, rate limited) ---
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            add @ssh_meter { ip saddr limit rate 3/minute burst 5 packets } accept
        ip saddr 192.168.132.0/24 tcp dport 22 ct state new \
            log prefix "[nft-ssh-ratelimit] " drop

        # --- OpenObserve 5080 web UI (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 5080 accept

        # --- OpenObserve 5081 gRPC ingest (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 5081 accept

        # --- Promtail 9080 (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 9080 accept

        # --- Embedding Server 8003 BGE-large (internal only) ---
        ip saddr 192.168.132.0/24 tcp dport 8003 accept

        # --- Log and drop everything else ---
        log prefix "[nft-input-drop] " flags all counter drop
    }

    # ---------------------------------------------------------------
    # FORWARD chain - default DROP (not a router)
    # ---------------------------------------------------------------
    chain forward {
        type filter hook forward priority 0; policy drop;
    }

    # ---------------------------------------------------------------
    # OUTPUT chain - allow all outbound
    # ---------------------------------------------------------------
    chain output {
        type filter hook output priority 0; policy accept;
    }
}
```

## Verification

After creation, confirm:
1. File exists at `/ganuda/config/nftables-greenfin.conf`
2. Contains `policy drop` in input chain
3. Contains ports 5080, 5081, 9080, 8003
4. Contains SSH rate limiting

## For Seven Generations

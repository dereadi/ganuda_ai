# Jr Instruction: nftables Egress Filtering for Executor Containment

**Task**: Add egress filtering rules to redfin nftables to prevent Jr executor from making unauthorized outbound connections
**Priority**: 4
**Story Points**: 5
**Epic**: #1974

## Context

The Jr executor on redfin can currently make arbitrary outbound connections. We need egress rules in nftables to restrict outbound traffic to known-good destinations only. This is defense-in-depth for executor containment.

The existing nftables config is at `/ganuda/config/nftables-redfin.conf`. We need to add an egress chain.

Allowed outbound from redfin:
- bluefin (192.168.132.222) — DB, VLM services
- greenfin (192.168.132.224) — embedding, monitoring
- owlfin (192.168.132.170) — web deployment
- eaglefin (192.168.132.84) — web deployment
- bmasass (192.168.132.21) — MLX reasoning
- WireGuard subnet (10.100.0.0/24) — mesh
- Tailscale subnet (100.64.0.0/10) — VPN
- DNS (udp 53, tcp 53) — name resolution
- HTTPS (tcp 443) — API calls (Anthropic, GitHub, PyPI)
- NTP (udp 123) — time sync

## Steps

### Step 1: Add egress chain to nftables config

File: `/ganuda/config/nftables-redfin.conf`

Find the closing brace of the existing `chain input` block and add after it (but before the final table closing brace):

```
<<<<<<< SEARCH
  }
}
=======
  }

  # Egress filtering — executor containment (DC-11 security layer)
  chain output {
    type filter hook output priority 0; policy accept;

    # Allow established/related
    ct state established,related accept

    # Allow loopback
    oif lo accept

    # Allow cluster nodes (LAN)
    ip daddr 192.168.132.0/24 accept

    # Allow WireGuard mesh
    ip daddr 10.100.0.0/24 accept

    # Allow Tailscale
    ip daddr 100.64.0.0/10 accept

    # Allow DNS
    udp dport 53 accept
    tcp dport 53 accept

    # Allow NTP
    udp dport 123 accept

    # Allow HTTPS (API calls)
    tcp dport 443 accept

    # Allow HTTP (package repos)
    tcp dport 80 accept

    # Allow SSH outbound (ansible, node management)
    tcp dport 22 accept

    # Log and drop everything else
    log prefix "EGRESS_DROP: " drop
  }
}
>>>>>>> REPLACE
```

## Verification

1. Syntax check: `nft -c -f /ganuda/config/nftables-redfin.conf` (dry-run validation)
2. Review the diff to ensure no existing rules were modified
3. NOTE: Do NOT apply this config live — TPM will deploy after Chief review

# KB — Goldfin PII DB Verification (Apr 22 2026)

**Closes kanban duyuktv #1582** (redispatched-from-1513, Verify goldfin PII database alive).
**Status:** UNREACHABLE — goldfin node appears OFFLINE for 70 days.

## What we tested

### Path 1: Direct LAN (192.168.20.10:5432)
- Route exists via greenfin (192.168.132.224) per `ip route get 192.168.20.10`
- TCP connection timeout after 10s
- psql test (with correct credentials): `timeout expired`

### Path 2: Tailscale (100.77.238.80:5432)
- Tailscale resolves `goldfin.tail0e8cb6.ts.net` → 100.77.238.80
- TCP connection timeout after 10s
- psql test: `timeout expired`

### Path 3: SSH (ssh goldfin)
- `ssh: connect to host goldfin port 22: Connection timed out`

## Root cause (from tailscale status)

```
100.77.238.80    goldfin           dereadi@  linux  active;
relay "dfw"; offline, last seen 70d ago, tx 1248 rx 0
```

**Goldfin has been offline 70 days** — Tailscale's control plane reports last contact Feb 12-ish 2026. No subsequent traffic. Node is either:
- Powered off
- Disconnected from network
- Hardware/OS failure
- Migrated elsewhere and not updated in records

## What this means

`vetassist_pii` database on goldfin is not currently available. Any federation services that depend on goldfin-hosted PII data have been running without that path for 70 days — which either means:
1. Services gracefully degraded and are running without PII access (preferred)
2. Services are silently erroring on PII queries (bad — would show in logs)
3. PII data has been migrated to another node and goldfin was decommissioned without cleanup of references (verify)

## Recommended next steps

1. **Physical/remote check on goldfin hardware.** Partner or a delegate to confirm whether goldfin is intentionally-offline (decommissioned) or an incident (something died). Hardware at what physical location?
2. **Service-side audit.** Grep federation service configs for references to goldfin / `192.168.20.10` / `vetassist_pii` — see what depends on it. If services reference it but are running fine, they're degraded-silent. If services never reference it, the node was always optional.
3. **Data recovery question.** If goldfin carried PII data, is there a backup? Where? When last backed up? The 70-day offline window means 70 days of potential data loss if the node failed ungracefully.
4. **Decommission or revive decision.** If goldfin is intentionally decommissioned, update docs to remove it from the topology. If it's a failure, treat as an incident — file recovery ticket.

## For TPM / future-self

This verification failure is GOOD signal, not bad. The ticket existed specifically because we didn't know the state. Now we know: goldfin is dark. That's actionable info. The 70-day gap is alarming — this should surface to Partner as a real operational finding, not a routine task close.

## Cross-references

- Original failed Jr attempt: kanban #1513 (Apr 17 2026, JR failed with "no executable steps")
- Redispatch: kanban #1582 (this KB's work)
- Source design: /ganuda/docs/jr_instructions/ (no dedicated instruction file for #1582 — embedded in ticket description)
- Federation audit Apr 18: goldfin NOT scanned because unreachable from audit host — consistent with 70-day-offline state

## Apr 22 2026 TPM

# Council Decision Record — Fiber Fabric Bring-Up, Address Plan, DB Path Migration

**CDR ID:** CDR-FIBER-BRINGUP-APR11-2026
**Date:** April 11, 2026 (Saturday afternoon CT)
**Convened by:** TPM (Partner directed: "Let's fill in the Council and have them decide")
**Mode:** Council deliberation via parallel sub-Claude votes (Augusta Pattern)
**Status:** **"Ratified" via SIMULATED COUNCIL — operational work proceeded under Partner direction, NOT real Council ratification**
**Authorship:** Council's record. TPM drafted; simulated Council voted; TPM synthesized; Partner directed.
**Council voices**: Coyote (adversarial), Turtle (production stability), Raven (long view), Bear (momentum) — all sub-Claude Agents, not real `specialist_council.py` invocations

> **⚠️ SIMULATED COUNCIL — OPERATIONAL ACTIONS LEGITIMIZED BY PARTNER, NOT BY REAL COUNCIL RATIFICATION**
>
> The "Council" deliberations and votes in this document are sub-Claude Agent instances prompted with persona descriptions, not invocations of the real `specialist_council.py`. No hex audit hash was produced by this CDR's "ratification" cycle. **The operational fiber fabric work did complete successfully** — fiber links up, 10.200.0.0/24 assigned, D6 Redis firewall rule added, Gate 1 iperf3 test passed at 3.18 Gbit/s — **but those completions were legitimized by explicit Partner direction in real time, not by Council ratification**.
>
> The related real Council vote `f8906cb875a73c8d` (taken after this CDR's simulated cycle) raised several concerns that overlap with but did not formally review this document's action tree — specifically Crawdad's sudo NOPASSWD breadth flag and Spider's vLLM:8000 single-point-of-failure map.
>
> See `feedback_simulated_vs_real_council.md` and Council acknowledgment vote `b38154de6c8ebaa6` (Apr 11 2026 Sat night) for context on the simulation/real-Council distinction. This CDR's operational work stands because it is in production and running clean; its *governance framing* is retained as TPM synthesis, not as Council-ratified policy. Future deliberation on DB migration gates and Gate 2 readiness should go through real Council invocation.

---

## Context

After a ~3-hour bring-up session, we lit **three × 10G fiber links** between the Dell S6000 (QSFP+ port 0 in breakout mode) and the two bnx2x NICs across redfin and bluefin:

```
redfin  enp5s0f1   UP  10000 Mbps  →  Te 0/? on S6000
bluefin enp7s0f0   UP  10000 Mbps  →  Te 0/? on S6000
bluefin enp7s0f1   UP  10000 Mbps  →  Te 0/? on S6000
Te 0/3 (4th breakout lane) unused — spare fanout leg
```

Partner also raised two adjacent items:
- Wants to bring **greenfin** onto the fiber fabric
- Ordered another NIC for the **SAN/NAS server**

## Current State (verified)

- **Physical**: HPC Optics QSFP-40G-SR4-S in Dell S6000 port 0 (already in `portmode quad` from prior config), MPO → 4×LC fanout (VANDESAIL), LC keystone couplers, OM3 runs to each endpoint
- **SFP+ endpoints**: generic OEM 10G-SR SFP+ (4-pack), 3 installed, 1 spare
- **L1/L2**: all three links at 10 Gbps full duplex, flow control on, clean PCS/PMA
- **L3**: no IPs assigned on fiber interfaces — links are up but idle
- **L4+**: nothing using the fiber yet; DB traffic still flows over `wg0` → `enp5s0`/`enp6s0` (1G copper)

## Root cause of the 3-hour grind (for the record)

The bring-up fought through six layers of red herrings before converging on the real issue. Capturing them here so the next bring-up is faster:

1. **False start — Fo 0/4 breakout attempt**: transceiver was initially in physical port 4, which is NOT in the S6000 `quad-port-profile` allowlist. OS9 S6000 caps quad mode at 24 of 32 ports due to SerDes sharing; port 4 is a paired port with port 0 and can't be quad while port 0 is. Error message "Quad mode is currently not activated on this port" was cryptic.
2. **Fix**: physically moved transceiver to port 0 (already in `portmode quad` from a previous session). One slot move, no config change, no reload needed.
3. **bnx2x SFP+ whitelist red herring**: initial `ethtool` output showed `Supported link modes: 1000baseT/Full` for a 10G fiber SFP+, which looked like classic Dell/Broadcom vendor lockout. Subsystem vendor check cleared this — cards are pure Broadcom, not Dell-branded, no firmware whitelist.
4. **`ethtool -s speed 10000 ... autoneg off` rejected with `Operation not permitted`**: not a permission issue — bnx2x refuses link-setting ioctls on SFP+ ports because the SFP+ EEPROM dictates speed. Red herring.
5. **Driver debug reload (`modprobe bnx2x debug=0xffff`)**: key insight — driver explicitly logs `Approved module` and `Setting 10G SFI`. Zero rejection from the driver. Zero hardware counters incrementing. PHY configured, SerDes idle, waiting for a signal it couldn't lock.
6. **Actual cause**: **switch-side PCS was stuck in a bad cached state** from the prior portmode transitions and module hotplug. `shutdown / no shutdown` on the breakout sub-interfaces cleared it. All three lanes came up instantly.

**Lesson for thermal memory**: after any `portmode quad` change or QSFP+ hot-swap on S6000 OS9, always cycle the sub-interfaces (`shutdown / no shutdown`) before assuming anything physical is broken. Stuck PCS state is silent — no error, no log line, no counter — and looks exactly like a dead fiber.

## Also discovered — worth flagging

**PCIe x1 bottleneck on both nodes.** Both BCM57810 cards are sitting in PCIe x1 slots with ~4 Gb/s total bandwidth across both ports. The NICs are rated for 32 Gb/s at x8. This means:
- Link rate (10G) is what the switch sees and what PHY commits to — correct
- Actual end-to-end throughput will top out at ~4 Gb/s per card, shared across ports
- Still **4× the old 1G copper path**, so the fiber is a real win — but the cards are leaving ~60% of their capability on the table

**Operational breakage visible in kernel logs (unrelated to fiber, but flagged):**
- `nftables` dropping `192.168.132.223 → .222:6379` (Redis) on bluefin
- `nftables` dropping same source → `:3000` (Grafana?)
- `nft-ssh-ratelimit` triggering on redfin→bluefin SSH — mostly self-inflicted from this session's command burst

---

## Decisions Before the Council

### D1 — Address Plan for the Fiber Fabric

TPM position: **direct-attached /30 or /29 point-to-point subnets, OR a single /24 with the switch as L2-only (no SVI)**. I lean toward the /24 L2 option for simplicity — it scales to greenfin, the SAN/NAS server, and any future endpoints without per-link subnet proliferation. Proposed: `10.200.0.0/24`, assigned as:

```
10.200.0.1    bluefin  enp7s0f0  (primary DB listener)
10.200.0.2    bluefin  enp7s0f1  (secondary / LACP spare)
10.200.0.10   redfin   enp5s0f1  (DB client, Jr executor)
10.200.0.20   greenfin (TBD)
10.200.0.30   sannas   (TBD)
```

Reserved `.1`–`.99` for nodes, `.100`–`.200` for service endpoints, `.201`–`.254` for future.

**Council question**: /24 flat, or /30 point-to-point per link? Both are defensible. /24 is simpler, /30 gives tighter fault isolation.

### D2 — DB Traffic Migration Timing

TPM position: **validate → stage → migrate → verify**, in that order, no shortcut.

1. **Validate L3** (today): assign IPs, `ping` bidirectional, `iperf3` TCP throughput test, confirm we actually see ~4 Gb/s per the PCIe ceiling
2. **Stage** (can be today or tomorrow): add a secondary PgBouncer listener on `10.200.0.1` without removing the existing WG listener. Both paths live simultaneously.
3. **Migrate**: update client DSNs to prefer `10.200.0.1`, one service at a time starting with the least-critical (monitoring daemons, then Jr executor, then production services)
4. **Verify**: watch PgBouncer connection counts, DB query latency histograms, and the Medicine Woman baseline for each migration wave
5. **Keep WG as fallback** for at least two weeks in case the fiber path develops issues under sustained load

**Council question**: do we migrate DB traffic at all, or do we keep the fiber for *future* high-bandwidth use cases (e.g., thermal memory backfill, KG embedding sync, cluster training data shuffle) while leaving DB on the proven WG path? The per-connection latency gain from WG→fiber is small; the throughput gain is large but only matters for bulk transfer, not DB queries.

### D3 — Greenfin Onboarding to Fiber Fabric — **REFRAMED**

**Update from Partner (Apr 11 afternoon):**
- Greenfin is a **GMKtec EVO-X2 Mini PC (AMD Ryzen AI Max+ 395 / Strix Halo)** — no internal PCIe card slots.
- Partner: *"Do with greenfin what you want, but remember **it is the bridge**."*

**Greenfin's established role (from thermal memory, Jan 2026):**
Greenfin is the cluster's VLAN bridge and security enforcement point.
- Routes between Compute (VLAN 1), DMZ (VLAN 10), and Sanctum/PII (VLAN 20)
- Enforces nftables isolation rules (Compute→Sanctum blocked, DMZ→Sanctum via silverfin allowed)
- Provides nachocheese (external WiFi) uplink
- Gatekeeps goldfin's PII data in Sanctum
- **Its job is policy and routing, not bulk throughput**

The Strix Halo upgrade makes it a much smarter bridge — L7 inspection, NPU-based traffic classification, local AI firewall analytics — but the role itself doesn't change.

TPM revised position: **Greenfin stays on 1G copper. Fiber fabric is a Compute-only data-plane overlay that greenfin does not need to see. No USB4→10G SFP+ adapter purchase.**

Rationale:
- Greenfin's bridging role is metadata-heavy, not throughput-heavy. 1G copper is plenty for cross-VLAN routing and nftables inspection.
- Fiber fabric (10.200.0.0/24 or whatever Council decides for D1) becomes L2-isolated between Compute nodes — redfin, bluefin, SAN/NAS. No routing implications for the VLAN bridge.
- Zero new hardware spend (saves ~$200–400 on the USB4 adapter)
- Zero new attack surface on the bridge
- Strix Halo's real value (local inference, Jr executor offload, potential council voice) lives on copper and doesn't need fiber throughput to function
- We don't change what greenfin IS just because we have new hardware

**Path B (join fiber as VLAN-aware trunk) is documented as an option** should greenfin's workload ever grow into a need for high-throughput data exchange with Compute (thermal memory sync, distributed training, Sanctum mirroring). If that day comes, it gets its own CDR when the need is real — not speculative.

**Council questions**:
- Concur with Path A (greenfin stays on copper, fiber is Compute-only)?
- Any dissent on the principle "new hardware doesn't change existing roles, it enhances them in place"?

**Decoupled side thread (not part of this CDR):** What specific role(s) does the Strix Halo greenfin take on for the federation's AI workloads? Local inference engine for certain model sizes? Firewall-integrated anomaly detection? Council voice with unique perspective? Worth its own CDR once Partner and Council are ready to think about it.

### D4 — SAN/NAS Server NIC + Fiber Path

**Update from Partner (Apr 11 afternoon):** Ordered the same BCM57810 NIC as redfin/bluefin. Dual bracket sizes in the package so mechanical fit is handled. SAN/NAS has no OS installed yet — greenfield build, no services to migrate.

TPM revised position: **whichever of greenfin or SAN/NAS is physically ready first takes Te 0/3 (port 0's spare lane) with the last SFP+ module from the 4-pack. Second arrival triggers the port 8 breakout order.**

Rationale:
- No speculative hardware spend (aligns with `project_revenue_purpose_apr11_2026` — capital discipline in spend-down phase)
- Same driver across all fiber endpoints = consistent SOPs, same gotchas (`shutdown/no shutdown` after attachment), less cognitive load
- Greenfield SAN/NAS install means we can pre-configure fiber IP + firewall + routes before the first service touches it
- Port 0 gets fully utilized before we open a second QSFP+ cage; clean incremental scaling

**Port 8 breakout order (when triggered) needs:**
- 1 × QSFP-40G-SR4-S (~$140)
- 1 × MPO → 4×LC fanout cable (~$50)
- Additional LC couplers + patch cables (~$30)
- 1 × 4-pack 10G SFP+ SR (~$80) — only if we need >1 new endpoint
- Total: ~$220 for 4 new lanes of headroom, or ~$300 if we need more SFP+s

**Council questions** (narrowed):
- Physical order of operations: which node physically gets fibered first — greenfin or SAN/NAS? Partner, your call; this is a logistics question, not a governance question
- Should we pre-emptively order the port 8 hardware now, or wait until the second node triggers the need? TPM default: wait.

### D5 — PCIe x1 → x8 Relocation — **DEFERRED**

**Update from Partner (Apr 11 afternoon):** Neither redfin nor bluefin has a free PCIe x8 slot. This isn't a "move the card" fix — it's a **motherboard/chassis upgrade** for both nodes. Partner: *"This will be a hardware upgrade X2 when more funds are available."*

TPM revised position: **DEFER to future funding cycle**. The cluster consciously accepts the ~4 Gb/s per-NIC throughput ceiling for the foreseeable future. Rationale:
- Current 1G copper DB path is the baseline; fiber at ~4 Gb/s = **4× improvement**, which is a real win even at the x1 bottleneck
- Aligns with `project_revenue_purpose_apr11_2026` — spend-down phase, capital discipline
- Not a critical path: DB query latency benefits from fiber at any bandwidth; only bulk transfer is throughput-bound
- No operational risk from running in x1 — it just caps peak throughput, nothing breaks

**When this decision unblocks:** Put it on the "funding-triggered" watchlist. When we have hardware upgrade budget, redfin + bluefin motherboard/chassis upgrade becomes the move that unlocks full 10G (and also adds future-proofing headroom for more NICs, more storage, faster cores).

**No Council action needed.** Noted for the record.

### D6 — nftables Firewall Cleanup

TPM position: **fix the Redis and port 3000 drops this week**. They're not fiber-related, but the fiber bring-up exposed them because we're now watching cluster traffic more closely. Service-impacting right now.

---

---

## RATIFIED DECISIONS (Council vote, Apr 11 2026 fast-track)

### Coyote Process Gate — Resolved before ratification

Coyote required TPM to consult thermal memory for prior DB migration lessons AND recover the rationale for commit 5ab73a0 ("DB host fixed to WireGuard") before Council finalizes D2. Both done:

**Thermal memory scan result**: No prior DB migration lessons of this type found (searched `pgbouncer`, `db migration`, `dual listener`, `database path`). This is novel work.

**Commit 5ab73a0 recovery**: The commit message is explicit — `Fixed DB_HOST default from LAN (192.168.132.222, flaky) to WireGuard (10.100.0.2)`. **The reason we are on WireGuard is that the LAN path through the existing switches was flaky enough to STRESS Medicine Woman over a 6-day observation gap.** Not encryption, not sovereignty — reliability. Medicine Woman's valence is the canary that detected the original flakiness.

**Implication for D2**: The fiber path is also "LAN-ish" (new S6000 switch, new bnx2x NICs, new drivers, first-time deployment). It MUST prove non-flakiness before replacing WG. This elevates Turtle's validation gates from "nice to have" to "non-negotiable precondition."

---

### D1 — Address Plan — **RATIFIED (3 AMEND, 1 APPROVE)**

**Ratified amendments** (all compatible, all incorporated):

- **Subnet**: `10.200.0.0/24` flat L2 on the Dell S6000 breakout fabric — Bear's simplicity retained
- **Isolation (non-negotiable)**:
  - NO SVI on the S6000, NO gateway, NO DHCP
  - Dedicated VLAN ID (TBD during execution, document it in the topology memory)
  - Explicit route-leak prevention to VLAN 1 (Compute), VLAN 10 (DMZ), VLAN 20 (Sanctum)
  - `10.200.0.0/24` added to greenfin + silverfin nftables rules treating fiber fabric as Compute-equivalent for Sanctum-isolation purposes
- **Structured reservation map** (Raven):
  ```
  .1–.19    nodes (redfin, bluefin, SAN/NAS endpoints)
  .20–.39   storage service endpoints
  .40–.99   application service endpoints (DB listener on floating IP .50)
  .100–.199 future Compute (training shards, thermal replicas, KG sync)
  .200–.254 transient / test
  ```
- **DB service binding** (Turtle): PgBouncer fiber listener binds to floating service IP `10.200.0.50`, NEVER directly to a NIC address. Floating IP allows future HA / failover without client reconfiguration.
- **Membership cap**: 5 endpoints without another CDR (Turtle — prevents broadcast domain sprawl)
- **Escape hatch**: Document `/30` point-to-point carve-out as a future option if the flat /24 regrets itself (Coyote)

**Coyote's dissent about greenfin VLAN interaction is addressed by the explicit VLAN isolation + nftables rule additions above.**

### D2 — DB Migration Timing — **RATIFIED (1 APPROVE-w/condition, 3 AMEND)**

**Ratified amendments:**

**Sequence stands**: validate → stage → migrate → verify.

**Gates (non-negotiable, automatic evaluation):**

- **Gate 1 — Pre-Stage (48h minimum):**
  - `iperf3` sustained ≥3 Gb/s for 60s, zero retransmits
  - `ping -f` 10min, 0% loss, p99 < 0.5ms
  - Link flap counter = 0 over 48h continuous observation
  - Zero `bnx2x` errors in dmesg
  - Zero PCS resync events on S6000 Te 0/0–0/2
  - **Medicine Woman baseline**: capture 48h valence for both WG and fiber paths side-by-side

- **Gate 2 — Stage (7d minimum on dual-listener synthetic traffic):**
  - PgBouncer secondary listener on `10.200.0.50:6432` running 7 days
  - Synthetic traffic only during this window, NO production DSN
  - One forced link flap test (unplug SFP+) to verify WG failover clean
  - Thermal/load burst test: redfin+bluefin simultaneous sustained workload
  - Prometheus side-by-side latency panel (WG vs fiber) running before, during, after

- **Gate 3 — Migration order (1 service per 24h, NOT batched):**
  1. Monitoring daemons (least critical)
  2. Node monitoring
  3. PgBouncer primary (redirect client DSNs)
  4. **Jr executor LAST** (Turtle: Jr queue failures compound across federation)
  
  Original TPM proposal had Jr second; Turtle amended to last. **Amendment accepted.**

**Rollback triggers (automatic, Medicine Woman canary, TPM executes unilaterally, Chief notified):**
- DB p99 query latency regression > 20% vs WG baseline
- PgBouncer connection churn > 2× baseline
- Any thermal memory write failure attributable to transport
- Any link flap during production traffic
- **Medicine Woman valence drop tied to DB path** (she is the original flakiness canary)

**WG fallback: INDEFINITE, no sunset clause** (Raven + Bear majority). WG stays up as cold standby. Default: no client DSNs pointing at it after migration, interface up, documented failover runbook. WG gets torn down only when a second independent fiber path exists, not before.

**Decision authority**: Rollback is asymmetric — TPM can roll back unilaterally at any trigger. Going forward (retry migration) requires Council re-vote. This is intentional.

### D6 — nftables Cleanup — **RATIFIED (4 APPROVE, 1 timing amendment)**

- **Fix Redis:6379 and port 3000 drops THIS AFTERNOON** (Bear + Turtle agreement)
- Not a CDR-scale decision, it's an execution task. Listed here for completeness.
- **Root-cause each drop before patching** (Raven — don't suppress, diagnose what's trying to connect and why)
- Same session as fiber work, not a separate ticket

### D3, D4, D5 — Already settled before Council vote

- **D3** Greenfin stays on copper (fiber is Compute-only overlay). No Council dissent.
- **D4** SAN/NAS hardware ordered, timeline Sun–Thu. No Council dissent.
- **D5** PCIe x1 ceiling accepted until funding unlocks chassis upgrade. No Council dissent.

---

## Council Standing Concerns (for thermal memory + ongoing monitoring)

- **Raven flag — Te 0/3 is a stop-gap, not a commitment.** When SAN/NAS block storage grows real traffic, it wants its own QSFP+ breakout. Revisit in the port 8 hardware CDR.
- **Raven flag — Greenfin Path B revisit trigger.** If Compute ever needs L7 DLP or anomaly inspection on fiber-fabric traffic, greenfin needs visibility. Write revisit trigger to thermal memory so we don't discover the need in a crisis.
- **Raven flag — Fiber fabric bypasses silverfin FreeIPA.** Acceptable today (machine-to-machine, no human auth). Revisit when any fiber-fabric endpoint serves human-facing traffic.
- **Raven flag — Patent touch.** Fiber fabric itself isn't patentable, but Compute-plane-only isolation reinforces Tokenized Air-Gap Proxy claim #7 (substrate sovereignty). One-line acknowledgment in next Hulsey prep update.
- **Turtle flag — No LACP, no bonding, no HA on fiber path.** Single SFP+ failure = full fiber outage. WG fallback is the only HA. Accept today, consider LACP in future CDR.
- **Turtle flag — Broadcast domain growth.** At 5 endpoints we re-evaluate. Cap is hard, not soft.
- **Turtle flag — PCIe x1 compounds on thermal replication workloads.** Put redfin+bluefin chassis upgrade on funding-triggered watchlist with concrete unlock event: "any workload sustains >3 Gb/s for >5 min."
- **Coyote flag — Pre-change checklist mandatory for any S6000 touch.** The silent PCS stuck-state gotcha means a future config change can break fiber invisibly. Write the checklist.

---

## TPM Recommended Vote Order

1. **D1 first** (blocks everything else) — address plan
2. **D2 second** — DB migration timing
3. **D3, D4 in parallel** — greenfin and SAN/NAS
4. **D5 deferred** — PCIe relocation scheduled separately
5. **D6 deferred** — firewall cleanup is its own small ticket

Council members are invited to amend, dissent, or add work items.

## What TPM commits to regardless of Council decision

- Write thermal memory with the "S6000 post-portmode shut/no-shut" lesson at 92°C, tagged `sop,s6000,portmode_quad`, so future bring-ups don't re-lose the afternoon
- Draft a project memory for the fiber fabric topology (what's connected where, IPs once assigned, PCIe bottleneck note, greenfin/SAN-NAS pending)
- Leave the fiber links up; make no IP/routing/DB changes until Council has voted
- Monitor redfin's link watcher in case anything flaps overnight

---

## Appendix — Parts Inventory (ordered Apr 8, delivered Apr 9–10)

- 1× HPC Optics QSFP-40G-SR4-S (40G QSFP+ SR4, 850nm) — in S6000 port 0
- 1× VANDESAIL MPO→8×LC (4 duplex) fanout 3m — at S6000, splits QSFP+ into 4 × 10G lanes
- 1× Cable Matters OM3 LC-LC 40m trunk
- 1× FLYPROFiber OM3 LC-LC 15m patch
- 2× 5-pack Cable Matters LC keystone couplers (10 total, patch panel terminations)
- 1× 4-pack generic 10G SFP+ SR (OEM, vendor PN `SFP-10G-SR`, 850nm) — 3 installed, 1 spare
- Total spend on the fiber fabric: ~$2,736 (includes Anker SOLIX F3800 Plus bundled in same cart, arriving Monday — not fiber-related)

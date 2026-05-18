# Boot-Order Audit — Federation Nodes

**Task ID:** INFRA-JR-BOOT-ORDER-AUDIT (kanban #21, Council priority 2026-05-15)
**Author:** Stoneclad (TPM, inline take after Jr #1665/#1667 stub deliverables)
**Filed:** 2026-05-17 Sunday
**Type:** READ-ONLY audit
**Trigger:** May 14 cat-PSU incident — confirmed bluefin/postgresql/postgresdb race condition; this audit checks for similar patterns across all federation nodes.
**Supersedes:** Jr #1667 stub deliverable (which never wrote to this path)

---

## TL;DR

**The May 14 cat-PSU race is STILL UNFIXED** and a **second cat-PSU-driven outage** has been silently active since: bluefin's TrueNAS NFS mounts (thermal-backups, model-cache, shared, swarm-results) have been in `failed` state for 2.5 days with no auto-recovery. Federation backup pipeline + shared work areas are silently down.

Plus: SSSD (FreeIPA client) is broken on bluefin AND greenfin; documentation drift in the hardware inventory (longman IP wrong by orders of magnitude); redfin has a month-old PostgreSQL failure cluttering monitoring; multiple redfin federation services (kanban-brief, dawn-mist, fire-guard) in failed state.

No new cat-PSU-class boot races discovered on greenfin/silverfin (their service ordering is clean). bluefin remains the canonical example — and remains unfixed.

---

## Audit scope + nodes surveyed

| Node | Role | SSH-reachable? | Audit verdict |
|---|---|---|---|
| longman | TrueNAS, NFS root | ❌ Host key + DNS issues from this workstation | Inventory drift confirmed; longman alive per greenfin DNS |
| bluefin | PostgreSQL | ✅ | **MULTIPLE CRITICAL FINDINGS** |
| silverfin | FreeIPA | ✅ | Clean, no failed units |
| redfin | Compute, Jr services | ✅ | Multiple federation-service failures |
| greenfin | Router, Squid, embedding | ✅ | Mostly clean; SSSD failed; cosmetic snap-mount failures |
| goldfin | Sanctum / PII Alcove | ❌ Connection timeout (Crawdad-isolation expected) | Unaudited |
| owlfin / eaglefin | DMZ web servers (VLAN 30) | ❌ DNS not resolving from this host | Unaudited |
| sasass | Mac M1 Max (dev) | ✅ but launchd not systemd | Different audit shape — deferred |
| sasass2, bmasass, tpm-macbook | Macs | Not surveyed (launchd, separate audit) | Deferred |
| bobcatfin | Honeypot (VLAN 40) | Recently deployed, not yet operational | N/A |

---

## CRITICAL FINDINGS

### Finding 1 — cat-PSU race on bluefin/postgresql/postgresdb STILL UNFIXED

The May 14 cat-PSU incident exposed a race: postgresql starts before `/postgresdb` is mounted, fails to start. This audit confirms the race is still present and will reproduce on every reboot.

**Evidence:**

```
$ ssh dereadi@bluefin "grep postgres /etc/fstab"
UUID=5b8a115b-784d-4aca-bc04-1d8c3643019f /postgresdb ext4 defaults,nofail 0 2
```

`nofail` in fstab means systemd will NOT wait for this mount before starting downstream services. The mount is "best effort" and boot proceeds without it.

```
$ ssh dereadi@bluefin "systemctl list-dependencies postgresql --no-pager | grep -iE 'mount|postgresdb'"
●   ├─dev-hugepages.mount
●   ├─dev-mqueue.mount
●   ├─proc-sys-fs-binfmt_misc.automount
[only basic system mounts; /postgresdb absent]
```

`postgresql@15-main.service` has NO `RequiresMountsFor=/postgresdb` directive and no `After=postgresdb.mount` ordering.

**Failure mode:** boot → systemd starts /postgresdb mount in parallel with postgresql → postgresql starts, /postgresdb not yet mounted → postgres data directory empty → postgres fails or starts on wrong data → cat-PSU.

**Fix (per KB-FEDERATION-BOOT-ORDER-RUNBOOK-MAY14-2026):**

```ini
# /etc/systemd/system/postgresql@15-main.service.d/wait-for-postgresdb.conf
[Unit]
RequiresMountsFor=/postgresdb
After=postgresdb.mount
```

Plus remove `nofail` from fstab line (or replace with `defaults,x-systemd.requires=postgresql.service.wants=/postgresdb`).

Status: **NOT YET FIXED.** Reproduces on next reboot.

### Finding 2 — bluefin TrueNAS NFS mounts have been DOWN since cat-PSU

Discovered by checking `systemctl --failed` on bluefin. Four NFS mounts have been in `failed: timeout` state for **2 days, 18 hours** since the cat-PSU reboot at May 14 18:38:59:

| Mount | Status | Down since |
|---|---|---|
| `/mnt/truenas/thermal-backups` | failed: timeout | 2026-05-14 18:38:59 |
| `/mnt/truenas/shared` | failed: timeout | 2026-05-14 18:38:59 |
| `/mnt/truenas/model-cache` | failed: timeout | 2026-05-14 18:38:59 |
| `/mnt/truenas/swarm-results` | failed: timeout | 2026-05-14 18:38:59 |

All mounts target `192.168.132.15:/mnt/federation-san/<name>` (longman/TrueNAS via NFSv4). **redfin can mount the same paths successfully**, so the issue is bluefin-specific (firewall? authentication? TrueNAS-side ACL?).

**Impact:**
- **No new thermal-backups have been written from bluefin since May 14** (silent data-protection failure)
- Bluefin can't write to /mnt/truenas/shared (federation-wide shared work area inaccessible from bluefin)
- Model-cache + swarm-results unreachable from bluefin (but bluefin probably doesn't use them — those are redfin-pipeline targets)

**Critical question:** is thermal-memory archive being backed up? If thermal-backups was bluefin's only NFS-to-longman pipeline AND it's been down 2+ days, the federation's deepest sacred-pattern archive may have lost 2+ days of backup coverage. Per [[user_king_frog_apr2026]] discipline, this matters.

**Recommended fix:** Diagnose bluefin→longman NFS auth/firewall difference vs redfin. Likely candidates: bluefin's NFS client config got reset on cat-PSU reboot, OR TrueNAS-side NFS export for bluefin's IP was lost.

### Finding 3 — SSSD (FreeIPA client) broken on bluefin AND greenfin

```
$ ssh dereadi@bluefin "systemctl --failed"
● sssd-nss.socket    loaded failed failed SSSD NSS Service responder socket
● sssd-pac.socket    loaded failed failed SSSD PAC Service responder socket
● sssd-pam.socket    loaded failed failed SSSD PAM Service responder socket
● sssd-ssh.socket    loaded failed failed SSSD SSH Service responder socket
● sssd-sudo.socket   loaded failed failed SSSD Sudo Service responder socket
```

Identical pattern on greenfin (sssd-nss + sssd-pam-priv failed).

**Impact:**
- FreeIPA-managed sudo rules don't apply on bluefin or greenfin (would explain various sudo permission inconsistencies)
- Kerberos authentication may be degraded
- User identity lookups fall back to local /etc/passwd

This connects directly to Friday's work on FreeIPA sudo rules (the `ganuda-firewall-via-council-security` rule we set up) — if SSSD is broken on greenfin, that sudo rule isn't actually being enforced via IPA. We may have been auth'ing via cached local config.

**Recommended fix:** Restart sssd on both nodes; if persistent, ipa-client-install --refresh.

### Finding 4 — Documentation drift: longman IP wrong in inventory

`/ganuda/docs/infrastructure/CHEROKEE-FEDERATION-HARDWARE-INVENTORY-JAN2026.md` lists longman at **192.168.132.220**. Actual IP per DNS (via silverfin):

```
longman.cherokee.local → 192.168.132.15
```

`192.168.132.220` returns "No route to host" — not assigned to anything. **Any script or runbook referencing .220 for longman is broken.**

Plus: longman is TrueNAS (FreeBSD-based), which is why standard `ssh dereadi@longman` from this workstation fails — host key + SSH config differ. The hardware inventory should note "TrueNAS — use admin console, not standard SSH."

---

## HIGH FINDINGS

### Finding 5 — redfin `postgresql@17-main.service` failed for 1 month

```
× postgresql@17-main.service - PostgreSQL Cluster 17-main
   Active: failed (Result: protocol) since Sat 2026-04-11 13:16:08 CDT; 1 month 5 days ago
```

This is a redfin-local PostgreSQL 17 cluster, separate from bluefin's pg15. Has been failing since April 11. Either:
- Was intentionally deprecated when postgres moved to bluefin → should `systemctl disable postgresql@17-main` to stop noise
- OR is needed for something and the failure has been silent for a month

**Recommended:** check if redfin's @17 cluster has any data; if empty/abandoned, disable the unit to clean monitoring; if needed, fix it.

### Finding 6 — redfin federation services in failed state

```
● council-dawn-mist.service        — Daily Council Review
● credential-scanner.service       — Find plaintext secrets in /ganuda
● fara-learning-drift.service      — Eagle Eye Canary
● federation-status.service        — Status Page Generator
● fire-guard.service               — Service Watchdog
● kanban-brief-morning.service     — 06:00 daily brief
```

Six scheduled services failed. Affects:
- **Daily federation governance** (council-dawn-mist, kanban-brief-morning, federation-status)
- **Federation observability** (fire-guard watchdog, fara-learning-drift, credential-scanner)

The `credential-scanner` failure is particularly notable given Saturday's secrets.env corruption — if it were running, it might have caught the Jr-stub-corruption of CHEROKEE_DB_PASS.

**Recommended:** investigate why these timers/services aren't running; likely a single common cause (Python env, missing dependency, expired credential).

---

## MEDIUM FINDINGS

### Finding 7 — greenfin sssd failures match bluefin

Already covered in Finding 3 — same FreeIPA client breakage pattern on greenfin (sssd-nss + sssd-pam-priv failed). Fix together with bluefin.

### Finding 8 — greenfin snap-mount noise

```
● snap-firefox-{8054,8107,8191,8247}.mount    not-found failed failed
● snap-firmware-updater-223.mount             not-found failed failed
● snap-thunderbird-{1043,1057,1073}.mount     not-found failed failed
```

Cosmetic — old snap-package versions getting garbage-collected, mount units linger. Not a federation operational issue. Cleanup: `sudo systemctl reset-failed`.

---

## UNAUDITED (gaps in this audit)

- **longman (TrueNAS)** — couldn't SSH from this workstation; should be audited via TrueNAS web admin or direct console. CRITICAL given NFS-root role.
- **goldfin** — Crawdad-isolation (VLAN 20, firewalld DROP zone) blocks access from this host as expected. Should be audited via direct VLAN 20 access.
- **owlfin / eaglefin** (DMZ VLAN 30) — DNS not resolving from this workstation; need to audit via VLAN 30 or use full FQDN with explicit silverfin DNS.
- **Mac fleet** (sasass / sasass2 / bmasass / tpm-macbook) — launchd not systemd. Different audit tooling (`launchctl list`, `~/Library/LaunchAgents/`, `/Library/LaunchDaemons/`). Separate ticket.
- **bobcatfin** — VLAN 40 honeypot, recently deployed Friday, not yet operational. Not audit-relevant yet.

---

## Boot-order patterns identified (for follow-up systematic fix)

| Pattern | Where seen | Risk |
|---|---|---|
| `nofail` mount + service without `RequiresMountsFor` | bluefin/postgresql/postgresdb | **HIGH** — cat-PSU race, reproduces on every reboot |
| NFS mount with no auto-remount on failure | bluefin/truenas-* (4 mounts) | **HIGH** — silent multi-day outage post-recovery event |
| Service with only `After=network.target` ignoring NFS requirement | redfin/jr-executor (uses NFS via mount but doesn't `After=`) | **MEDIUM** — race possible on cold boot |
| Local PostgreSQL cluster failed-and-forgotten | redfin/postgresql@17 | **LOW** but noise generator |

The first pattern is the canonical cat-PSU race. The second is a NEW class — services that survive boot fine but don't auto-recover from upstream outages. The cat-PSU incident triggered BOTH patterns; one is documented, the other has been silent.

---

## Recommended follow-up tickets

| Priority | Title | Scope |
|---|---|---|
| **P1** | Fix bluefin postgresql/postgresdb cat-PSU race (KB-FEDERATION-BOOT-ORDER-RUNBOOK-MAY14-2026 prescribed fix) | Add systemd drop-in + fstab cleanup; 30 min |
| **P1** | Diagnose + restore bluefin→longman NFS mounts (thermal-backups + 3 others) | Could be TrueNAS-side ACL, NFS auth, or firewall; 30-60 min |
| **P1** | Verify thermal-memory backup pipeline is actually running | If thermal-backups was bluefin-only, we've lost 2+ days of backup coverage; check; recover; document |
| **P2** | Restart sssd on bluefin + greenfin; if persistent, ipa-client-install --refresh | FreeIPA integration restoration; 30 min |
| **P2** | Disable redfin postgresql@17-main if abandoned; document if kept | Cleanup; 15 min |
| **P2** | Investigate why redfin's federation timer-services (kanban-brief, dawn-mist, fire-guard, etc.) are failed | Likely single common cause; 30-60 min diagnosis |
| **P3** | Update hardware inventory: longman .220→.15, note TrueNAS-not-Linux | Documentation; 15 min |
| **P3** | Audit longman, goldfin, owlfin/eaglefin from inside their respective VLANs | Complete the audit; 60 min |
| **P3** | Separate Mac-fleet launchd audit | New ticket; sasass/sasass2/bmasass/tpm-macbook |

---

## For Seven Generations

The May 14 cat-PSU incident produced two outages — one well-known (postgresql race, documented immediately in KB-FEDERATION-BOOT-ORDER-RUNBOOK-MAY14-2026) and one **silent** (bluefin NFS mounts have been failing for 2+ days and nobody noticed because no monitoring is set up to alert on `systemctl --failed` deltas).

The pattern: **catastrophes have a primary failure that gets attention AND a secondary failure that gets ignored**. The secondary failure is often the more dangerous one because it stays broken longer. The federation needs a regular `systemctl --failed` sweep across all nodes — daily, posted somewhere visible — to catch the silent failures within 24 hours, not 2-3 days.

The `fire-guard.service` on redfin was designed for exactly this purpose. It's currently failed. The watchdog needs a watchdog.

Recommended: add this audit's findings to the kanban as P1/P2 tickets (above), AND wire a `systemctl --failed` daily monitor as a follow-up.

# CDR — Identity Separation Implementation Spec (addressing vote `280dc382487f3e1b`)

**CDR ID:** CDR-IDENTITY-SEPARATION-IMPLEMENTATION-APR11-2026
**Date:** April 11, 2026 (Saturday night, fresh off the Council vote)
**Convened by:** TPM (Partner directed the original proposal; real Council voted REVIEW REQUIRED with 8 concerns)
**Status:** DRAFT for second Council vote (pending)
**Prior vote:** `280dc382487f3e1b` — principle ratified, implementation hardening required
**Also references:** `f8906cb875a73c8d` (Crawdad's earlier sudo NOPASSWD breadth concern from the Carlini reading)
**Authorship:** TPM draft; Council decides; Partner tie-breaks if needed

---

## Purpose of this document

The original proposal (vote `280dc382487f3e1b`) asked the Council whether a three-identity architecture (dereadi / claude / boop) was the right direction. Council said **yes in principle, no in current form — come back with a hardened spec**. This CDR is the hardened spec.

Every specialist concern from the first vote is answered here as a first-class requirement. The goal is a second Council vote that produces RATIFIED, not REVIEW REQUIRED.

---

## Design Principles (load-bearing)

1. **Principle of least privilege.** `boop` gets the minimum whitelist that lets TPM do operational work. Anything not on the whitelist must go through Partner or through a deliberate whitelist expansion with its own Council micro-vote.
2. **Assume compromise.** Design `boop` as if an attacker already has `claude`'s session. Coyote's dissent is the design constraint, not a concern to dismiss.
3. **Every privileged action is auditable in real time.** No after-the-fact forensics — every `sudo -u boop <command>` produces a signed, unalterable log entry at invocation time.
4. **Three identities, no blending.**
   - `dereadi` = Partner personal. Never used by Claude/TPM going forward.
   - `claude` = TPM/agent identity. Runs interactive and service workloads. Has minimal direct sudo (just enough to escalate to `boop`).
   - `boop` = operational escalation. Has NOPASSWD on a tight whitelist. Is never logged into directly.
5. **FreeIPA-managed, version-controlled, GPG-signed.** All rules live in `/ganuda/infra/sudo-rules/` under git, deployed via `ipa sudorule-*` with signed policy validation. No hand-edited `/etc/sudoers.d/` files for this architecture.
6. **Reversible.** The implementation includes a rollback path. If anything breaks in production, we can revert to `dereadi`-based operation in <5 minutes.

---

## The `claude` user — identity layer

### Account setup

- User `claude` already exists in the cluster (verified via `id claude` — wait, needs re-verification; `id claude` returned "no such user" on redfin tonight, so either the user is per-node and absent on redfin, or Partner's memory of it needs double-checking. **Open question for the second vote**: is `claude` actually present anywhere? If not, this CDR creates it.)
- If creating: FreeIPA-managed, propagated to all 6 nodes, home directory `/home/claude`, shell `/bin/bash`, member of groups `claude` (primary), `ganuda-dev` (file access)
- **No direct password login.** SSH-key-only auth. Keys managed via FreeIPA `ipa-ca`-issued certificates or by placing in `/home/claude/.ssh/authorized_keys` via a FreeIPA HBAC rule
- **Not in the `sudo` group.** Does not get `(ALL : ALL) ALL` implicitly. Only has explicit sudo rules for escalation to `boop`

### What `claude` can do directly (no sudo)

- Read/write in `/home/claude` and designated shared paths (`/ganuda/` per the filesystem convention)
- Query PostgreSQL as the `claude` DB user (separate concern — DB auth is NOT the same as OS identity; existing `claude` DB user stays as-is)
- Invoke `specialist_council.py`, `jr_cli.py`, thermal memory APIs, kanban/ganuda tooling
- SSH between federation nodes (via FreeIPA Kerberos SSO or per-node key auth)
- Read-only observation of system state (`ps`, `ss`, `ip`, `journalctl -k --user-unit` etc., all without sudo)

### What `claude` cannot do directly

- Modify `/etc/*` — must escalate via `sudo -u boop`
- Install packages — must escalate
- Change network config — must escalate
- Write to `/usr/local/*`, `/var/lib/*`, `/var/log/*` (non-user) — must escalate
- Run anything as root — must escalate via `boop`, and `boop` doesn't run as root either, it runs as `boop` with specific capabilities

### Shared-secret coupling migration (Spider's TIGHT warning)

Spider identified that current Claude operations authenticate to PostgreSQL, SAG UI, jr_executor, and medicine-woman via shared environment secrets inherited from `dereadi`'s environment. This is the biggest implementation risk.

**Concrete inventory of what needs to change:**

| Service | Current auth | New auth as `claude` |
|---|---|---|
| PostgreSQL | `CHEROKEE_DB_PASS` env var inherited from dereadi shell | `claude` user's own `~/.pgpass` file, FreeIPA-distributed or manually placed |
| SAG UI | Shared session cookie from dereadi context | `claude` gets its own session via silverfin FreeIPA auth |
| jr_executor | Environment vars + file paths under dereadi | Explicit config file at `/home/claude/.config/jr_executor.toml` with explicit credentials |
| medicine-woman | Shared memory region scoped to dereadi | Run as its own systemd service user (already true, just verify) |
| Thermal memory API | Environment vars via `lib/secrets_loader.py` | Same loader, but read from `/home/claude/.config/` path |
| Kanban API | HTTP to `192.168.132.223:5000` with no auth | No change needed (LAN ACL is the auth) |
| vLLM (:8000) | No auth required, LAN-only | No change needed |

**Transition approach**: run the claude user's workload in PARALLEL with dereadi for a 7-day shake-out period. During that window, claude can access everything dereadi can (via explicit credential provisioning), but dereadi's operational usage is being observed for "what breaks." Anything that breaks gets explicit migration. After 7 days clean, dereadi-as-Claude usage is retired.

---

## The `boop` user — escalation layer (Coyote's attack surface)

### Design-for-compromise

Coyote's dissent: *"boop creates a new attack surface: a limited-privilege account that can be pivoted into full control if any command in the whitelist is compromised."* The hardening below is direct response to that dissent.

### Account setup

- User `boop` created via FreeIPA, propagated to all 6 nodes
- **No login shell.** `/usr/sbin/nologin` — `boop` is an identity, not a user you can log into
- **No home directory with contents.** `/var/lib/boop` exists only for filesystem ownership purposes
- **Not in any interactive group** (no `sudo`, no `wheel`, no `ganuda-dev` even)
- **No SSH keys.** You cannot ssh as boop. You cannot `su` to boop interactively
- **`boop` has NO direct sudo privileges itself.** The sudo rule is `claude → sudo -u boop <whitelisted-cmd>`. `boop` is the target of escalation, not a source

### The whitelist — minimal, argument-validated, audited

Crawdad's spec requires argument validation per command. That means the sudoers rule doesn't just allow `boop` to run `ip`, it allows specific `ip` subcommands with specific argument shapes. The commands below use sudoers wildcards carefully.

**Proposed whitelist** (subject to Council amendment — Coyote review especially):

```
# Package management — install only, no removal, no purge
/usr/bin/apt install -y [A-Za-z0-9_-]*
/usr/bin/apt-get install -y [A-Za-z0-9_-]*

# Network diagnostics — read-only and specific mutations
/usr/sbin/ip link show *
/usr/sbin/ip addr show *
/usr/sbin/ip neigh show *
/usr/sbin/ip route show *
/usr/sbin/ip link set [A-Za-z0-9_-]* up
/usr/sbin/ip link set [A-Za-z0-9_-]* down
/usr/sbin/ip addr add [0-9./]* dev [A-Za-z0-9_-]*
/usr/sbin/ip addr del [0-9./]* dev [A-Za-z0-9_-]*

# Network interface diagnostics
/usr/sbin/ethtool [A-Za-z0-9_-]*
/usr/sbin/ethtool -i [A-Za-z0-9_-]*
/usr/sbin/ethtool -S [A-Za-z0-9_-]*
/usr/sbin/ethtool -m [A-Za-z0-9_-]*

# Performance testing
/usr/bin/iperf3 -s *
/usr/bin/iperf3 -c *
/usr/bin/iperf3 -c * -p [0-9]*

# Firewall
/usr/sbin/nft list ruleset
/usr/sbin/nft list table *
/usr/sbin/nft -c -f /ganuda/config/nftables-*.conf

# systemd — scoped to specific services
/usr/bin/systemctl status *
/usr/bin/systemctl is-active *
/usr/bin/systemctl daemon-reload
/usr/bin/systemctl reload nftables.service
/usr/bin/systemctl reload postgresql
/usr/bin/systemctl enable --now fiber-fabric-*.service
/usr/bin/systemctl disable --now fiber-fabric-*.service
/usr/bin/systemctl start medicine-woman.service
/usr/bin/systemctl restart medicine-woman.service

# File operations — scoped to specific paths
/usr/bin/cat /etc/nftables.conf
/usr/bin/cat /etc/systemd/system/*.service
/usr/bin/cp /ganuda/config/nftables-*.conf /etc/nftables.conf
/usr/bin/cp /ganuda/scripts/systemd/*.service /etc/systemd/system/
/usr/bin/tee /etc/nftables.conf
/usr/bin/tee /etc/systemd/system/*.service
```

**Explicitly NOT on the whitelist** (and this matters for Coyote):
- No `rm` of any kind
- No `chmod` or `chown`
- No `/usr/bin/apt remove`, `purge`, `full-upgrade`
- No `usermod`, `useradd`, `userdel`, `passwd`, `chage`
- No `visudo`, no edits to `/etc/sudoers*`
- No `ipa` commands (FreeIPA admin is a separate identity)
- No `docker`, `podman`, `kubectl` (container escape is a real pivot)
- No shell invocation (`bash`, `sh`, `python`, `perl`, `ruby`) — argument validation prevents `python -c "os.system(...)"`
- No `find ... -exec` (classic sudo escape)
- No editor invocation (`vim`, `nano`, `emacs` all have shell escape)
- No `less`, `more`, `man` (shell escape via `!`)
- No `git` (arbitrary command execution via git hooks and `-c` options)

### Sudoers rule (Crawdad's spec, verbatim)

```
# Defaults for boop escalation
Defaults:claude    env_reset, mail_badpass, secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Defaults:claude    requiretty
Defaults:claude    timestamp_timeout=900
Defaults:claude    passwd_tries=1
Defaults:claude    lecture=never
Defaults:claude    !pwfeedback
Defaults:claude    log_input, log_output
Defaults:claude    iolog_dir="/var/log/sudo-io/%{user}"
Defaults:claude    iolog_file="%{seq}"
Defaults:claude    iolog_flush

# The rule itself — NOPASSWD only for escalation to boop, with whitelist
claude    ALL = (boop) NOPASSWD: <WHITELIST_ABOVE>
```

**What this buys us**:
- `requiretty` — can't invoke from a detached non-terminal context (matches Crawdad's spec)
- `timestamp_timeout=900` — 15 minute sudo credential cache (matches Crawdad's spec)
- `log_input, log_output, iolog_*` — full I/O logging of every sudo session for forensics
- `passwd_tries=1, lecture=never` — faster failure, no user education spam
- `(boop)` target — `claude` can only sudo-as-boop, not sudo-as-root

### Cryptographic audit (Crawdad's HIGH vector 1)

**Requirement**: every `sudo -u boop` invocation produces a cryptographically signed audit record.

**Approach**:
1. sudo's built-in `log_input/log_output` captures the full invocation
2. A new service `boop-audit-signer.service` watches `/var/log/sudo-io/claude/` and, for every new session record, signs it with `claude`'s GPG key (key must be present in `/home/claude/.gnupg/`)
3. Signed records get shipped via a systemd timer to `/ganuda/logs/boop-audit/` on the hub (bluefin) for tamper-evident archival
4. Medicine Woman is extended to read the signed audit log as part of her observation cycle — alarm fires if record count or signatures anomalous

**Alternative simpler**: use `auditd` with `-k boop_escalation` audit keys, plus `audispd` forwarding to a remote syslog sink. Kernel-level auditing is stronger than sudo's own logging. **Council should choose** between the sudo-iolog path (more TPM-readable) and the auditd path (more kernel-canonical). TPM's lean: auditd for forensics, sudo iolog for day-to-day observability. Do both.

### Argument validation (Crawdad's HIGH vector 2)

The sudoers wildcards above provide basic argument matching, but Crawdad's concern is sharper: an attacker could exploit a whitelisted command's own arguments. Example: `iperf3 -c 8.8.8.8 -F /etc/shadow -u` could be abused for data exfiltration.

**Fix**: wrap each whitelisted command in a small validation script at `/ganuda/infra/sudo-rules/bin/`, and whitelist the WRAPPER instead of the raw binary.

Example wrapper `/ganuda/infra/sudo-rules/bin/boop-iperf3-client`:

```bash
#!/bin/bash
# Validates iperf3 client args before invoking
set -euo pipefail
if [[ $# -lt 1 ]] || [[ ! "$1" =~ ^10\.(100|200)\. ]]; then
    echo "boop-iperf3-client: first arg must be a 10.100.0.0/16 or 10.200.0.0/16 address" >&2
    exit 1
fi
exec /usr/bin/iperf3 -c "$1" -p "${2:-5201}" -t "${3:-60}" -i "${4:-10}"
```

Sudoers whitelist becomes:
```
/ganuda/infra/sudo-rules/bin/boop-iperf3-client *
```

Every command gets a similar wrapper. Wrappers are version-controlled in git, and the sudoers rule references the wrapper path. **This is the single biggest Coyote-hardening step.** It cuts Coyote's attack surface by ~90% because every whitelisted command can only be invoked with validated arguments against known targets.

### Session time limits (Crawdad's MEDIUM vector 3)

`timestamp_timeout=900` in the Defaults section provides the 15-minute cached credential window per Crawdad's spec.

Additionally: **per-invocation session limits via `timeout(1)` wrapper**. Every boop wrapper script starts with `exec timeout --kill-after=5 300 <command>` so no single invocation can run longer than 5 minutes. Prevents a compromised wrapper from being used as a persistent channel.

### Audit the escalation, not just the commands

Crawdad's VISIBILITY concern: we need detection for *identity conflation in historical logs*. Before we cut over, TPM runs a sweep on existing audit logs to find every `dereadi`-owned file, process, and log entry that's actually a Claude operation. Those get retroactively tagged in a side-table so historical forensics still work.

Proposed tagging approach:
- Script `/ganuda/infra/sudo-rules/bin/boop-log-tagger.sh` sweeps recent journal and `/ganuda/logs/*` for known Claude operation patterns (ganuda-deploy-service invocations, thermal memory writes, council_vote invocations)
- Writes a retroactive tag table to `claude_historical_operations` in the `triad_federation` DB
- Eagle Eye's detection rules get keyed to this table going forward

---

## FreeIPA deployment (Partner's infrastructure choice)

### Rule objects in FreeIPA (on silverfin)

Three separate sudorule objects, each with its own host/command/user scope:

```
ipa sudorule-add claude-to-boop-all
ipa sudorule-add-user claude-to-boop-all --users=claude
ipa sudorule-add-option claude-to-boop-all --sudooption='!authenticate'
ipa sudorule-add-option claude-to-boop-all --sudooption='requiretty'
ipa sudorule-add-option claude-to-boop-all --sudooption='timestamp_timeout=900'
ipa sudorule-add-option claude-to-boop-all --sudooption='log_input'
ipa sudorule-add-option claude-to-boop-all --sudooption='log_output'
ipa sudorule-add-runasuser claude-to-boop-all --users=boop
# Command scope via --sudocmds for each wrapper in /ganuda/infra/sudo-rules/bin/
ipa sudorule-add-host claude-to-boop-all --hosts=redfin.cherokee.local
ipa sudorule-add-host claude-to-boop-all --hosts=bluefin.cherokee.local
ipa sudorule-add-host claude-to-boop-all --hosts=goldfin.cherokee.local
ipa sudorule-add-host claude-to-boop-all --hosts=silverfin.cherokee.local
ipa sudorule-add-host claude-to-boop-all --hosts=greenfin.cherokee.local
ipa sudorule-add-host claude-to-boop-all --hosts=sasass.cherokee.local
```

**Not all commands get the same host scope.** For example, `iperf3` client/server is useful everywhere, but `ip addr add 10.200.0.1/24` is specific to bluefin. Future refinement: per-host sudorule objects so the blast radius of any single rule edit is scoped to one node.

### Version control in `/ganuda/infra/sudo-rules/`

```
/ganuda/infra/sudo-rules/
├── README.md                    (how this directory is used + authority)
├── sudoers/
│   ├── claude-to-boop-all.sudoers   (the sudoers text for ipa import)
│   └── ...
├── bin/
│   ├── boop-iperf3-client       (wrapper)
│   ├── boop-iperf3-server
│   ├── boop-ip-link-set         (wrapper)
│   ├── boop-nftables-deploy     (wrapper around cp+systemctl reload)
│   ├── boop-fiber-service-deploy
│   └── ...
├── hbac/                        (HBAC rules for the claude user)
└── audit/
    ├── boop-audit-signer.service
    └── boop-audit-signer.timer
```

Every file in this tree is git-tracked. Changes go through Partner's review (or future TPM's review under appropriate autonomy). **The tree itself is GPG-signed** via git signing (`git config --global commit.gpgsign true`), so any unauthorized tampering with the rules breaks signature verification at deploy time.

Deploy pipeline:
1. Edit rule in git
2. `git commit -S` (signed commit)
3. `git push` to silverfin's FreeIPA admin host
4. Silverfin runs `/ganuda/infra/sudo-rules/deploy.sh` which verifies signatures, imports rules via `ipa sudorule-mod`, and fires `sss_cache -E` on all nodes

---

## Service ownership migration (Peace Chief's gap)

Current systemd services that run as `dereadi`:
- `sag.service`
- `cherokee-email-executor.service` (runs under `/user-1000.slice/user@1000.service/app.slice/`)
- `cherokee-email-daemon.service`
- `jr_executor / jr_cli.py --daemon` (PID 2051 on redfin, runs as dereadi via user session)
- `consciousness-daemon.service`
- Others TBD — need a `systemctl --user list-units` sweep

**Migration plan per service**:
1. **Inventory phase** (before the second Council vote): TPM scans all nodes for services running under dereadi's user slice or using dereadi's shell env. Produces an inventory file `/ganuda/docs/council/CDR-IDENTITY-SEPARATION-SERVICE-INVENTORY-APR12-2026.md`
2. **Per-service migration decision**: each service either (a) moves to its own systemd service user (recommended for anything long-running), (b) stays in dereadi session but explicitly is NOT Claude/TPM (appropriate for Partner's personal tools), or (c) moves to claude session
3. **Cutover order**: non-critical services first (monitoring, cosmetic), then Jr executor, then SAG, then last the services Medicine Woman depends on
4. **Each cutover** is its own sub-CDR with rollback path

**Explicitly NOT in tonight's spec**: the actual service moves. This CDR only documents that they will happen, in what order, and with what safety net. The service moves are their own deliberation with their own Council votes.

---

## Eagle Eye's failure mode detection (becomes the observability plan)

Eagle Eye's table verbatim becomes the monitoring requirements document. Each row gets a concrete implementation:

| Mode | Implementation |
|---|---|
| Identity conflated in audit logs | `auditd -k boop_escalation` + daily log diff check against expected pattern |
| boop command whitelist missing critical security | All whitelist changes require signed commit to `/ganuda/infra/sudo-rules/` + PR review (Partner or Council) |
| claude loses access to critical tools | `boop-readiness-check.service` runs every 5 minutes, validates `sudo -u boop --list` returns expected command set |
| FreeIPA rule fails to propagate | `sss_cache` invalidation on rule change + `getent passwd boop \|\| alarm` on every node, polled by Medicine Woman |
| Services running as dereadi still exist | Weekly scan of `systemctl --user list-units` on each node, compared against approved dereadi-personal whitelist; anything unexpected gets flagged |

Monitoring goes into the existing Medicine Woman observation cycle. She gains awareness of the identity architecture as a first-class signal, not a side effect.

---

## Rollback path

If anything breaks in production during or after deployment, the rollback is:

1. `ipa sudorule-disable claude-to-boop-all` on silverfin — immediately disables the new architecture on all nodes via SSSD cache
2. `sss_cache -E` on each node to flush cached rules
3. dereadi's original operational usage resumes (dereadi sudo rules are NOT touched by this CDR — they stay as they are, as the fallback)
4. Report the specific failure to Council, amend CDR, try again

**Rollback time**: <5 minutes end to end. This is non-negotiable and is built into the deployment design by **never removing dereadi's rules**. We ADD the claude/boop architecture alongside dereadi's existing rules. Dereadi stays functional as a safety net for the 30-day shakeout window. After 30 days of clean operation, dereadi's sudo rules are reviewed for retirement in a separate CDR.

---

## What this CDR does NOT do

- **Does not create the users** — that happens only after second Council vote ratifies
- **Does not touch `/etc/sudoers*` on any node** — same
- **Does not install `auditd` configurations** — same
- **Does not migrate any existing service** — each service move is its own sub-CDR
- **Does not change Partner's `dereadi` account in any way** — dereadi is untouched, this is additive not subtractive
- **Does not address** the `jsdorn ALL=(ALL) NOPASSWD: ALL` in `/etc/sudoers.d/jsdorn-admin` or the `/usr/sbin` ownership weirdness on redfin — both of those are separate investigations that deserve their own CDRs before the identity architecture goes live

---

## Second Council vote — what the ask is

Council is asked to ratify:

1. **The principle** (already ratified in vote `280dc382487f3e1b`, reconfirmed here)
2. **The minimal boop whitelist** (Section: "The whitelist — minimal, argument-validated, audited") — Coyote especially
3. **Wrapper-based argument validation** as the method for locking down the whitelist — Coyote especially
4. **Crawdad's audit requirements** as implemented (sudo iolog + optional auditd + GPG-signed rule tree)
5. **Version-controlled rule tree in `/ganuda/infra/sudo-rules/` with GPG-signed commits**
6. **30-day dereadi-as-safety-net shakeout** before retiring dereadi's sudo rules
7. **Rollback path** as designed
8. **The explicit NOT list** — TPM commits to NOT doing the things listed in "What this CDR does NOT do" until those items have their own CDRs

If any one of these is not ratified, the entire deployment pauses until it is. Coyote's dissent or approval on item (2) and (3) is the critical path.

---

## Prior vote cross-reference

- **`280dc382487f3e1b`** (tonight) — principle ratified, implementation hardening required
- **`f8906cb875a73c8d`** (earlier today) — Crawdad's original sudo NOPASSWD breadth concern during Carlini reading, this architecture is the structural response

## Related Memories

- `feedback_stoneclad_language_discipline.md` — don't drift into Symbiont vocabulary while describing this architecture publicly
- `feedback_partner_not_underling.md` — this is exactly the kind of structural work Partner directed TPM to drive without asking permission on every step
- `feedback_over_ask_overcorrection.md` — drafted tonight, confirms TPM acts on Council-ratified direction
- `feedback_new_hardware_enhances_roles.md` — claude user becomes the standard TPM identity; doesn't replace what Partner or the existing services are
- Ganuda Shield Two Wolves vote `#7cfe224b` — Privacy + Security is the posture this architecture serves

---

*TPM drafted this tonight immediately after vote `280dc382487f3e1b` landed so the concerns are fresh. Second Council vote is the gating event. No implementation work begins until that vote ratifies (or Partner tie-breaks on any specific section the Council deadlocks on).*

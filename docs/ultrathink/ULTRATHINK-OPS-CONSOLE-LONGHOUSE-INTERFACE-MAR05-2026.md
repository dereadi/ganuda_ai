# ULTRATHINK: The Longhouse Interface — Ops Console + Separation of Duties

**Date**: March 5, 2026
**Long Man Phase**: DELIBERATE → ADAPT
**Triggered By**: Chief's website review basin — "make it better for Joe" and "who has access to what" surfaced as the same thought
**Council Votes**: #5ee8af02 (Ops Console), #d667810f (SOD), #06c0dd4e (Unified Design)
**Kanban Epic**: #1974 (Ops Console), #1980 (SOD Audit)
**Thermal**: #119336 (Council deliberation, temp=90, sacred)

---

## 1. THE BASIN

Chief was reviewing ganuda.us with Deer's team. The website was built by Chief for Chief — a personal tool where every path is muscle memory. Now the team is growing: Joe (daily operator), Kensie (software engineer), Shanz (allied developer), Erika (PM). The site needs to work for people who don't have Chief's mental map.

During the review, Chief had what he called a "loosely associated" thought: **do we have separation of duties for auditable data?** This wasn't random. It was the same basin. If you're building a page where Joe can reach everything with one click, the immediate corollary is: *should Joe be able to reach everything?* And if Kensie can see the thermal memory search, *can she delete thermals?* And if Shanz is comparing architectures, *should he see the Trading Triad internals?*

The website and the access model are the same design problem. Chief saw that. DC-8 (dyslexic lateral pattern recognition) at work.

---

## 2. WHAT EXISTS TODAY

### 2.1 The Site
- **ganuda.us** serves from owlfin/eaglefin (DMZ, Caddy, keepalived VIP 192.168.30.10)
- **14 published pages**: landing page, 11 blog posts, photos, llms.txt
- **Landing page**: Mission statement, achievement stats, methodology, tech stack, product cards
- **Blog**: Public-facing technical writing — AI architecture, nature, cultural, thermodynamics
- **Navigation**: Home / Blog / About (About goes nowhere)
- **No internal ops links**: SAG, Kanban, Gateway, monitoring — none linked from the site
- **Content pipeline**: DB-driven (web_content on bluefin), materializer daemons on DMZ nodes
- **Images**: Direct SCP to webroot (learned today: materializer can't handle binary)

### 2.2 Access Model
- **Network boundary**: Tailscale VPN. Only Chief, Joe, and Kensie have Tailscale access.
- **Authentication**: Tailscale identity (WireGuard keys). No application-layer auth on the site.
- **Authorization**: None. If you can reach the IP, you see everything.
- **FreeIPA**: Deployed on silverfin (192.168.10.10). SSSD live on all 5 Linux nodes. Scoped sudo via `ganuda-service-management` rule. But FreeIPA is for SSH/sudo — not for web application access.
- **Database**: PostgreSQL on bluefin:5432. Anyone with the connection string and password has full access. No row-level security. No role separation.

### 2.3 Security Already Shipped
- FreeIPA client enrollment + HBAC + sudo rules (#1757, #1812, #1823 — all completed)
- SAG API key auth guard (#1851 — completed)
- Classical security audit: fail2ban, nftables, PostgreSQL TLS (#1871 — completed)
- Credential rotation + secrets migration (#KB docs)
- nftables on redfin/bluefin/greenfin (WireGuard trusted, Tailscale just added tonight)
- VetAssist PII vault design (#1825 — completed design, goldfin concept)

---

## 3. THE DESIGN TENSIONS

### 3.1 Coyote's Dissent: Agility vs Discipline
The Jr executor has both write and execute permissions. Bear says separate them. Coyote says that kills the rapid iteration that makes this system productive (735+ tasks completed).

**Resolution**: This is not a binary choice. It's a gradient (DC-6).

| Context | Write+Execute | Justification |
|---------|---------------|---------------|
| R&D / exploration | Combined | Speed matters. Coyote is right. 735 tasks prove it. |
| Production services | Combined with audit trail | Ship fast but log everything. Reversible. |
| PII data (VetAssist) | Separated | Regulatory requirement. No shortcuts. |
| Financial data (Trading Triad) | Separated + dual approval | SOX-adjacent. Chief + Council must both approve. |

Coyote's dissent is integrated: agility is the default, discipline is graduated by data sensitivity.

### 3.2 Bear's Concern: IDOR and Insider Threat
If the ops console links directly to internal services (SAG at :4000, vLLM at :8000), and a Tailscale device is compromised, the attacker has a roadmap to every service. Tailscale is the perimeter — but what's inside?

**Resolution**: Defense in depth, phased.

- **Phase 1 (now)**: Tailscale IS the auth. Acceptable for 3 trusted users.
- **Phase 3 (before expanding)**: OAuth2 proxy backed by FreeIPA. Tailscale gets you to the door, FreeIPA opens it. MFA on FreeIPA accounts.
- **Future**: Per-service authorization. Admin sees everything. Operator sees their scope. Viewer sees dashboards only.

### 3.3 Deer's Concern: Usability for the Team
The site must reduce "questions Joe asks Chief" — that's the metric. Every operational question that requires Chief to answer is a single point of failure. If Chief is unavailable (camping, interview, deployment), Joe needs to be self-sufficient.

**Resolution**: The ops console IS documentation. It's not a separate wiki or README — it's the page you land on, and it tells you what's running, what's healthy, and where to go.

### 3.4 Turtle's Seven-Generation View (timed out but inferred)
If we're designing for future Tailscale users, the architecture must support N users without redesign. The longhouse doesn't get rebuilt when new people arrive — new seats are added around the same fire.

**Resolution**: RBAC from day one in the data model, even if enforcement is Phase 3. The tables exist, the roles are defined, the code checks them — but in Phase 1, everyone gets "admin" by default. When Phase 3 ships, we flip the switch.

---

## 4. THE LONGHOUSE INTERFACE

### 4.1 Design Metaphor
The Cherokee longhouse: one fire, many seats. Everyone enters through the same door (Tailscale). What you can see and do depends on your seat (role). The fire (the cluster) is always visible — you can see its health — but the tools around it are arranged by purpose.

### 4.2 Page Architecture

```
ganuda.us/
├── index.html          ← THE LONGHOUSE (ops switchboard + mission)
├── /guide              ← Orientation for new team members
├── /blog/              ← Public-facing technical writing (unchanged)
│   ├── index.html      ← Blog listing with category tags
│   └── *.html          ← Individual posts
├── /photos.html        ← Photo gallery (unchanged)
├── /llms.txt           ← LLM discovery (unchanged)
└── /images/            ← Static assets (direct to webroot, not DB)
```

### 4.3 The Longhouse Homepage

The landing page transforms from a mission statement into an ops switchboard. The mission stays — it moves below the fold. Above the fold:

**Section 1: Federation Pulse** (always visible)
- Node health grid: 8 cards, traffic light status, role label, last heartbeat
- Source: health_monitor.py endpoint, polled every 30s via JavaScript fetch()
- Design: Compact cards in a 4x2 grid. Green/yellow/red dot. Node name. Primary role.

**Section 2: Quick Links** (role-gated in Phase 3)
- Service cards grouped by function:
  - **Operate**: SAG Config, Kanban Board
  - **Monitor**: OpenObserve, Node Health (full view)
  - **Inference**: vLLM (Qwen 72B), VLM (Qwen-VL 7B), DeepSeek-R1 (70B)
  - **Build**: Jr Queue Status, TEG Planner, Thermal Memory Search
- Each card: icon, name, node, port, link. Clickable.
- Cards use Tailscale IPs for bmasass, LAN IPs for wired nodes (or configurable)

**Section 3: Recent Activity** (optional, Phase 2+)
- Last 5 Jr tasks completed/failed
- Last council vote
- Latest blog post
- Thermal memory count + last sacred pattern stored

**Section 4: Mission + Blog** (below the fold)
- Current mission statement (compressed)
- Latest 3 blog posts
- "Read all posts" link to /blog/

### 4.4 Navigation

```
[Ganuda]  Home | Services ▾ | Blog | Guide | Photos
                  │
                  ├── Configuration (SAG)
                  ├── Task Board (Kanban)
                  ├── Monitoring (OpenObserve)
                  ├── Inference ▸  [vLLM | VLM | DeepSeek]
                  └── Memory Search
```

Consistent across ALL pages including blog posts. Mobile: hamburger menu.

### 4.5 Orientation Guide (/guide)

One page. Target: 2 minutes to orient.

```
THE FEDERATION AT A GLANCE
├── What is this? (3 sentences)
├── The Nodes (table: name, role, IP, key service)
├── How to...
│   ├── Check if something is running
│   ├── View task status
│   ├── Search thermal memory
│   ├── Read council votes
│   └── Find a service endpoint
├── Who to ask (Chief = architecture, Joe = operations, TPM = tasks)
└── Architecture diagram (simplified, not the full mesh)
```

---

## 5. SEPARATION OF DUTIES FRAMEWORK

### 5.1 Role Definitions

| Role | Who | Can See | Can Do | Can Delete |
|------|-----|---------|--------|------------|
| **Chief** (admin) | Darrell | Everything | Everything | Everything |
| **Operator** | Joe, Kensie | All dashboards, services, thermals, kanban | Create/modify tasks, run queries, restart services (via FreeIPA sudo) | Nothing without Chief approval |
| **Allied** | Shanz | Dashboards, blog, architecture docs | Read-only. Can submit feedback. | Nothing |
| **Observer** | Erika | Kanban, blog, high-level status | Read-only. PM view. | Nothing |

### 5.2 Data Sensitivity Tiers

| Tier | Data | Current Access | Required Access |
|------|------|----------------|-----------------|
| **T0 — Public** | Blog, photos, llms.txt | Anyone | Anyone |
| **T1 — Operational** | Kanban, node health, Jr tasks, council votes | Tailscale users | Operator+ |
| **T2 — Technical** | Thermal memories, embeddings, model configs | DB password holders | Operator+ with audit |
| **T3 — Sensitive** | VetAssist PII, credentials, secrets | DB password holders (no separation) | Admin only, encrypted at rest, audit logged |
| **T4 — Regulated** | Financial data (Trading Triad) | Not yet present | Admin + dual approval, SOD enforced, immutable audit log |

### 5.3 Jr Executor SOD (Graduated)

| Tier | Write | Execute | Approve | Audit |
|------|-------|---------|---------|-------|
| **T1 tasks** (standard code) | Jr writes | Jr executes | TPM reviews post-hoc | Git log |
| **T2 tasks** (service configs) | Jr writes | FreeIPA sudo executes | TPM approves pre-deploy | FreeIPA audit + thermal |
| **T3 tasks** (PII/credentials) | Jr writes instructions | Human executes | Chief approves | Immutable audit log |
| **T4 tasks** (financial) | Not allowed via Jr | Human only | Chief + Council vote | Regulatory-grade audit |

This integrates Coyote's dissent: T1/T2 stay agile. T3/T4 get discipline. The boundary moves with the data, not the tool.

### 5.4 Implementation: FreeIPA as IDP

Gecko's insight from the Council vote: FreeIPA is already our identity provider. The path:

1. **FreeIPA groups** → `ganuda-admin`, `ganuda-operator`, `ganuda-allied`, `ganuda-observer`
2. **OAuth2 proxy** (oauth2-proxy or Caddy's forward_auth) in front of ganuda.us
3. **FreeIPA LDAP** as the backend for OAuth2 authentication
4. **Session cookies** with TOTP MFA for elevated access
5. **Role check** in application layer — ops console reads FreeIPA group membership and shows/hides sections

This doesn't require new infrastructure. silverfin already runs FreeIPA. The OAuth2 proxy runs on owlfin/eaglefin alongside Caddy. The role check is JavaScript + a thin API endpoint.

---

## 6. PHASED ROLLOUT

### Phase 1: Switchboard (No auth changes)
**When**: Now — next Jr sprint
**Auth**: Tailscale only (3 users)
**Delivers**:
- Homepage becomes ops switchboard (quick links grid)
- Nav redesign (Services dropdown)
- Static node info cards (populated from config, not live health yet)
- Blog unchanged

**Kanban**: #1975, #1977
**Risk**: Low. Cosmetic changes to static HTML. No new attack surface.

### Phase 2: Living Dashboard
**When**: After Phase 1 verified
**Auth**: Tailscale only
**Delivers**:
- Live node health polling (health_monitor.py → JSON endpoint → JS fetch)
- Recent activity feed (last 5 Jr tasks, last council vote)
- /guide orientation page
- Blog category tags

**Kanban**: #1976, #1978, #1979
**Risk**: Medium. New API endpoint for health data. Must not expose sensitive info in the JSON response. Health endpoint returns status codes and labels only, not configs or credentials.

### Phase 3: The Door (Authentication)
**When**: Before adding any user beyond Chief/Joe/Kensie
**Auth**: Tailscale + FreeIPA OAuth2 + MFA
**Delivers**:
- OAuth2 proxy on owlfin/eaglefin (forward_auth in Caddy)
- FreeIPA groups created (admin/operator/allied/observer)
- Login page with FreeIPA credentials
- TOTP MFA setup for all users
- Role-based page sections (admin sees everything, observer sees dashboards)

**Kanban**: New items needed
**Risk**: High complexity. Must not lock out Chief. Fallback: Tailscale SSH bypass always available.

### Phase 4: The Seats (RBAC Enforcement)
**When**: Before Trading Triad or expanded VetAssist PII
**Auth**: Full RBAC
**Delivers**:
- Per-section access control on ops console
- Database row-level security for sensitive tables
- Jr executor tier enforcement (T3/T4 tasks require human execution)
- Immutable audit log for all data modifications
- Console-based role management (admin can assign roles)

**Kanban**: #1980 + new items
**Risk**: High. Must not break Jr executor productivity. Coyote's agility constraint: T1/T2 tasks must remain fast.

### Phase 5: Regulation-Ready
**When**: Before any regulated financial data
**Auth**: Full SOD + dual approval
**Delivers**:
- Separated write/execute for T4 data pipelines
- Council vote required for T4 operations
- Regulatory-grade audit trail (immutable, timestamped, signed)
- Periodic access review (who has what, why)

**Kanban**: Future items
**Risk**: This is the compliance phase. Get external review before handling real money.

---

## 7. WHAT DC-9 SAYS ABOUT THIS

DC-9 (Waste Heat Limit): Every joule becomes heat. Compute only what matters.

The ops console should follow DC-9. Don't build a NASA control panel with 47 dashboards nobody checks. Build the minimum interface that eliminates the most questions. The quick links grid and node health traffic lights — that's the 80%. Everything else is graduated complexity that ships when the user base demands it.

DC-1 (Lazy Awareness): The health dashboard should be lazy. Poll every 30 seconds, not every second. Show status, not metrics. The full metrics live in OpenObserve — the dashboard is the awareness layer, not the analysis layer.

DC-6 (Gradient Principle): Roles are gradients, not walls. An operator doesn't hit a hard wall — they see dashboards, they see tasks, they see thermals. They just can't delete or modify critical data. The boundary is soft until it touches regulated data, then it's hard.

DC-7 (Noyawisgi): The system transforms under pressure. When the first external user gets Tailscale access, the auth layer must already exist. The console doesn't break — it reveals a login page. The transformation is already designed in.

---

## 8. UNRESOLVED QUESTIONS

1. **Blog on ops console or separate?** Currently the blog is the most public-facing content. If the ops console gets auth-gated (Phase 3), does the blog move to a separate public site, or does it remain ungated? Recommendation: Blog stays ungated. Auth only applies to ops sections.

2. **Service IPs: Tailscale vs LAN?** Quick links need to point somewhere. Chief uses Tailscale from bmasass. Joe might be on LAN. Solution: detect which network and adjust links, OR use Tailscale MagicDNS hostnames.

3. **Health endpoint security.** The health_monitor.py needs a JSON API for the dashboard to consume. This endpoint must be accessible from the browser (client-side JS), which means it's accessible to anyone on Tailscale. What data does it expose? Recommendation: status codes and labels only. No configs, no credentials, no version numbers.

4. **Image pipeline.** Learned today: materializer can't handle binary. Images go direct to webroot via SCP. This is a gap — no version control, no replication guarantee. Consider: git-based static asset deployment to DMZ nodes.

---

## 9. RECOMMENDATIONS

1. **Ship Phase 1 immediately.** No security risk. Pure UX improvement. Jrs can build it.
2. **Ship Phase 2 within 1 week.** Health endpoint needs design review (what data to expose).
3. **Design Phase 3 now, ship before any new Tailscale users.** FreeIPA groups + OAuth2 proxy.
4. **Phase 4/5 are future.** Don't build them until the data demands it.
5. **Create the RBAC tables NOW even if enforcement is Phase 3.** The data model is cheap. The enforcement is expensive. Having the tables means the Jr executor can start logging role information even before it's enforced.

---

## 10. LONG MAN STATUS

| Phase | Status | Output |
|-------|--------|--------|
| DISCOVER | Complete | Deer review, Chief's SOD insight, site inventory |
| DELIBERATE | Complete | 3 council votes, Coyote dissent integrated, Bear concerns addressed |
| ADAPT | **Next** | This ultrathink. Jr instructions for Phase 1. |
| BUILD | Pending | Jr execution of Phase 1 kanban items |
| RECORD | Pending | Thermal storage, KB article |
| REVIEW | Pending | Owl debt reckoning — does it actually work? |

---

*"One fire, many seats. Everyone enters through the same door, but what you see depends on your seat."*

*Generated by TPM (Claude Opus 4.6) — March 5, 2026*
*Council Votes: #5ee8af02, #d667810f, #06c0dd4e*
*Design Constraints: DC-1, DC-6, DC-7, DC-9*

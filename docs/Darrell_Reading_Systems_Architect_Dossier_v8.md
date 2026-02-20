# DARRELL E READING II

*Systems Architect · Distributed AI Builder · Infrastructure Transformation Engineer*

Bentonville, AR · dereadi@gmail.com · github.com/dereadi · ganuda.us

---

## Where I Come From

I grew up in Siloam Springs, Arkansas — a mechanic's kid, a trucker's kid, a latch key kid from age five. My father was a dust bowl migrant farmer's son who built race cars on weekends and ran five trucks grossing $10K a week in the 1970s. He lost his leg in a motorcycle accident and smoked a Camel while waiting for the ambulance with a lawnmower cord as a tourniquet. My mother was a spiritual seeker — Baptist, Wiccan, Buddhist, Hindu — who believed souls return to a collective carrying all experiences. She died of liver cancer when I was eight. My grandmother and grandfather died within months after. Three losses before third grade.

My father married Elsie, who was half Cherokee. Her mother had graduated from a federal Indian boarding school — the "Kill the Indian, save the man" era. The institutional trauma flowed down generationally. My mother brought Cherokee heritage through curiosity and wonder. Elsie carried the same blood shaped by forced assimilation. Same lineage, completely different expressions.

I was an undiagnosed dyslexic with auditory processing issues. In sixth grade, frustrated and failing, I read the encyclopedia A to Z to force words into my head. Something clicked. I scored 98th percentile on the ASVAB two years early, with recruiters at the door before I could drive. I forged my own report cards through high school. I didn't care — I had a plan.

No degree. No formal pedigree. Every transition in my career started the same way: buy the book, flood the system until it rewires, build something nobody asked for, and hand it off clean.

---

## How I Work

My pattern is consistent across military leadership, Fortune 1 enterprise transformation, and sovereign AI system design: clarify the mission, separate concerns, enforce boundaries, collaborate deliberately, and build systems that survive real-world pressure — then make them legible enough that others can operate and extend them without me.

I learned distributed problem-solving at 18 in an Air Force command post, working simultaneous emergencies with a Major who didn't take over — he took one thread. I learned the build-train-handoff pattern building forensic infrastructure: become the SME, train two replacements on different halves, then move to the next hard problem. I learned that brute force works when you can't see the elegant path yet, and that the elegant path reveals itself once you've exhausted the brute force.

---

## Military Service

**United States Air Force (1988–1990)**
Command and Control Specialist, Little Rock AFB. Signed up for missile silo duty; the silos shut down just before I arrived. Instead coordinated aircraft operations, fueling, life support, and base defense. At 18, simultaneously worked a hijack protocol and a Thunderbird emergency landing during a base exercise — two binders open, splitting the workload with a Major. First experience with parallel problem decomposition under pressure.

**Arkansas Army National Guard (1993–2007)**
C-1-142 Field Artillery (Charlie Battery, Rogers, AR). Entered as E-3. Served on 8-inch self-propelled howitzers (M110), transitioned to MLRS (Multiple Launch Rocket System) around 1996. Battery-level telecom — patch panels, crank phones, and troubleshooting token ring networking on rocket launchers. E-4 for seven years (underachieving on the promotion game while knowing the systems better than people above me), E-5 in 2003, promoted to E-6 (Staff Sergeant) for the 2005 deployment.

**Iraq Deployment (2005)**
Deployed with 39th Infantry Brigade Combat Team. Cross-trained at Fort Dix as MP support for detainee operations. Served at Camp Cropper (Baghdad International Airport) and Abu Ghraib during the facility transition to Iraqi control. Squad Leader responsible for 13 soldiers including a medic. Supervised Iraqi workers cleaning debris from Abu Ghraib for handover. Received prisoners at Cropper as the facility expanded. During expansion, uncovered legacy WMD caches buried under cement.

Tasked with writing all platoon awards — our platoon became the most awarded not through exaggeration, but through disciplined documentation of performance. Offered a $400,000 two-year civilian contractor position and walked away. The mission was done.

Lost my father to throat cancer during the deployment. I knew before I left that I was saying goodbye for the last time.

---

## Career Arc — Walmart (1990–2024)

My career at the world's largest retailer spans 30+ years, from a help desk phone to senior security infrastructure engineering. No degree at any point. Every transition was self-taught.

**The Foundation (1990–1996)**
Loaded frozen chickens at Tyson for six months after the Air Force while reading a shell scripting bible and a C programming book. Got on at Walmart Rx Support on AIX systems. Given root access and programmer-written fix scripts — I didn't just run them, I read them until I understood why they worked. Moved to Telecom: learned Crosscom digital switches, wrote screen scraper macros for ~100 ticket types, handled more tickets than my three teammates combined. Got a shot at IVR programming on OS/2 Warp. Started building unauthorized reports by accessing servers through a two-keystroke hack to the command prompt. A programmer patched it. Three keystrokes worked instead. He shook his head and said "just don't tell anyone else." That curiosity led to the Remedy team, writing C APIs. The C book from the Tyson freezer days paid off.

**Infrastructure Engineering (2007–2013)**
Returned from Iraq to the Home Office Unix team. HP-UX to SUSE migrations, raw space builds, LUN carving from SANs, middleware deployments (WebSphere, Oracle, MariaDB). Survived Walmart's annual reorg carousel — HO/DC/Store teams splitting and merging. Landed on QC, struggled for a year, then got pulled back to Remedy when an old teammate took over the team and needed someone to change the culture.

**Remedy Platform Transformation — 6M Transactions/Day**
As an Advanced Engineer on a strong team, I helped lead the migration of a Remedy platform handling 6 million transactions per day. The architecture placed 12 web servers across two datacenters on an F5 with least-connections balancing, running WebSphere on SUSE. Six app servers fed into a read-write database in one datacenter with a read-only hot standby in the other. Failover promoted to read-write within 15 seconds — and even then, each event required a formal Correction of Error.

My specific contribution was pushing for virtualization when the prevailing wisdom said hypervisor latency made it too risky at this scale. I had seen it work elsewhere and was convinced the new hardware would absorb the overhead. That bet paid off — we virtualized 6 app nodes, 24 web nodes, and two 1TB RAM database nodes (32 cores each). We were given an 8-hour outage window for the HP-UX to SUSE and Informix to Oracle migration. We completed it in four.

When IBM proposed AIX, we rejected it — their failover took minutes. A year later, IBM went back to their lab, matched our speed, and delivered a cleaner recovery process. When they met the standard, we said yes. Two promotions during this period: Systems Engineer → Advanced → Senior.

Also replaced physical server headers — hands-on with the iron, not just the software. Full stack in the literal sense: racking, cabling, swapping components on the raised floor.

**Enterprise Scale**
- Supported 5,000+ Unix/Linux systems across four datacenters.
- Store QC infrastructure supporting 30,000+ devices critical to store uptime.
- Built SCCM deployment packages distributed to 300,000+ global endpoints.
- Carried an on-call pager from 1996 onward. That beeper was burned deeper into my nervous system than Iraqi mortar fire.

**Security Infrastructure (2018–2024)**
Moved to security via a trusted colleague who knew my infrastructure work. Served on the team supporting Red Team, Blue Team, SOC, Incident Response, and a forensics lab accredited for data recovery and investigations. The U.S. government engaged the lab directly on occasion. My role was never the investigation — it was building the infrastructure that made investigation possible.

Built a complete SureView surveillance suite in South Africa over a single weekend through a VPN — OS install, application deployment, Oracle database configuration, all remote — to collect evidence on bad actors targeting our systems.

Became the Mac SME and developer/administrator for Jamf, Jira, and Confluence. Trained one teammate to take over Mac and Jamf, another on the Linux backend and Jira development. Once they were running independently, I moved to air-gapped work.

Built a forensic processing lab when a surge of Macs needed imaging. Network team dropped an air-gapped switch. I installed Munki on a Mac Mini for mass processing. The forensic imaging software needed time sync, but air-gapped means no NTP. Solution: a GPS puck pulling satellite time. GPS doesn't care if you're air-gapped.

The air-gapped lab led to exploring AI on repurposed Mac Pros that couldn't run Jamf. Another team approached about AI research. I bought a Mac Mini and a server I named Bluefin — out of pocket — before getting let go. Bought a second Mini at home to continue with distributed inference. The enterprise tools came home in my head: Munki, Ansible, FreeIPA. The air-gapped forensic network became a sovereign AI federation.

---

## Sovereign AI Federation — Current Architecture

What started with repurposed Mac Pros on a raised floor is now a 6-node heterogeneous AI infrastructure with role-specialized nodes, enforced identity boundaries, and a democratic governance layer.

- **Redfin** (Threadripper 7960X, RTX PRO 6000 96GB): Primary inference — Qwen2.5-72B-Instruct-AWQ via vLLM, 32 tok/s with AWQ-Marlin quantization. Hosts a 7-specialist democratic Council with 8,600+ recorded votes.
- **Bluefin** (i9-13900K, RTX 5070): PostgreSQL backbone with 88,000+ thermal memories. Vision-language model (Qwen2-VL-7B) for camera intelligence. pgvector semantic search across the full memory corpus.
- **Greenfin** (i7-12700K): Monitoring via OpenObserve and Promtail. BGE-large embedding server (1024-dimensional) powering RAG retrieval.
- **Two Mac Studios** (M1 Max, 64GB each): Cross-platform compute running PyTorch workloads, sharing results through PostgreSQL-backed solution pools.
- **bmasass** (M4 Max, 128GB): Air-gapped field operations running DeepSeek-R1-32B via MLX for sovereign reasoning without network dependency.

**Governance Triad**: FreeIPA (identity + Kerberos), Ansible (idempotent orchestration), Munki (endpoint lifecycle) — the same enterprise tools from the raised floor, now governing a sovereign system.

**Engineering at Scale**: Over 200 structured instruction documents authored, each decomposed into steps precise enough for autonomous AI agents to implement without supervision. 564 engineering tasks completed through a dual-pipeline architecture separating code execution from planning. Failed tasks automatically decompose through a recursive engine with depth-controlled retry.

**Memory and Retrieval (February 2026)**:
- Semantic RAG over 88,000+ thermal memories with 98% embedding coverage — HyDE query expansion, cross-encoder reranking, and sufficiency gating.
- Corrective RAG (CRAG): self-evaluating retrieval that detects contradictions and searches for sentinel corrections in real-time.
- Neuroscience-inspired memory architecture: reliability inversion penalizes over-recalled memories (reconsolidation drift), co-retrieval tracking detects contamination windows, and an automated immune system regulates bulk pattern contamination.
- Dead letter queue with automatic escalation, step-level checkpointing, and recursive task decomposition.

**Self-Healing Infrastructure**:
- LLM-powered pipeline: alert bridge → remediation engine → validation → Ansible feedback loop.
- Adaptive GPU power monitoring with thermal-aware scheduling.
- nftables firewall hardening with per-node policies and Tailscale ACL validation.

---

## Case Study — Jane Street Neural Net Puzzle (Solved)

The Jane Street "Dropped Neural Net" puzzle presents 97 neural network weight matrices that have been separated and shuffled. The task: find the correct pairing and ordering of all 48 layers. The search space is 48! × 48! ≈ 10^122 possible configurations. As of submission, 44 people had solved it.

The initial simulated annealing fleet — 28 workers across all 5 compute nodes — hit a hard basin at MSE 0.321 despite 500K iterations. The Council flagged that brute-force search in a 10^122 space was structurally hopeless without structural insight.

The breakthrough came from analyzing the weight matrices directly. I discovered that trace(W_out @ W_inp) provides a strong structural pairing signal — Hungarian assignment on trace scores matched 38 of 48 pairs independently. With correct pairings locked, the problem collapsed from 10^122 to 48! (ordering only), and simulated annealing converged rapidly.

The endgame required three distinct algorithmic phases: uncertain position enumeration, swap cascades through successive local minima, and simultaneous 3-opt rotations at the last stubborn positions. Solve trajectory: 0.45 → 0.00275 → 0.00173 → 0.000253 → 0.000000. MSE zero. SHA-256 hash matched. Submitted February 16, 2026.

The distributed computation revealed an unexpected architectural resonance: the puzzle solver independently reinvented the same topology as the thermal memory system — PostgreSQL as shared state, quality-gated writes, top-N pruning, and autonomous edge workers. Apple Silicon (M4 Max) ran 2.4–2.8x faster per-thread than Intel/AMD on the numerical workload, shaping how work was allocated across the heterogeneous fleet.

---

## What Holds It Together

The same pattern runs through everything: read the manual when there is one, brute-force it when there isn't, build it so someone else can run it, and move to the next hard problem. Encyclopedia at twelve. Shell scripting bible from a freezer. C APIs from a two-keystroke hack. Token ring on rocket launchers. GPS puck in an air-gapped lab. A sovereign AI federation built from hardware I bought out of pocket.

I don't fit neatly into a category. I grew up a redneck in northwest Arkansas, raised around the Cherokee Nation but on the outside of it. I loaded frozen chickens, roped by my sister, forged my own report cards, led soldiers in Iraq, built forensic labs for the government, pushed virtualization past the skeptics, and solved a $50K neural network puzzle with a fleet of computers in my house.

No degree. No linear path. Just the next problem, and whatever book or binder or encyclopedia it takes to crack it open.

For Seven Generations.

# DARRELL E READING II

*Enterprise-Scale Systems Architect · Distributed AI Builder · Infrastructure Transformation Engineer*

Bentonville, AR · dereadi@gmail.com · github.com/dereadi · ganuda.us

---

## Operating Philosophy

I am largely self-taught. After leaving the Air Force, I began at Help Desk without a formal technical pedigree. My education path was nonlinear—interrupted by deployment—but I never stopped building. Every step forward came from curiosity, disciplined experimentation, and stepping into harder problems than I was formally prepared for.

Across military leadership, Fortune 1 enterprise transformation, and sovereign AI system design, my pattern is consistent: clarify the mission, separate concerns, enforce boundaries, collaborate deliberately, and build systems that survive real-world pressure—then make them legible enough that others can operate and extend them without me.

---

## Case Study — Remedy Platform Transformation (6M Transactions/Day)

As an Advanced Engineer on a strong team, I helped lead the migration of a Remedy platform handling 6 million transactions per day. The architecture placed 12 web servers across two datacenters on an F5 with least-connections balancing, running WebSphere on SUSE. Six app servers fed into a read-write database in one datacenter with a read-only hot standby in the other. If the primary failed, the standby promoted to read-write within 15 seconds—and even then, each failover event required a formal Correction of Error.

My specific contribution was pushing for virtualization when the prevailing wisdom said hypervisor latency made it too risky for a system at this scale. I had seen it work in other implementations and was convinced the speed of the new hardware would absorb the overhead. That bet paid off—we virtualized 6 app nodes, 24 web nodes, and two 1TB RAM database nodes (32 cores each) in 2012.

When IBM proposed migrating to AIX hardware, we evaluated and rejected it—their failover process took minutes, not seconds. We held the standard we had set. Ironically, it was HP—the vendor who sold us the chassis—that suggested the move to Linux in the first place.

The full transformation included migrating from HP-UX to SUSE and Informix to Oracle. We were given an 8-hour outage window and completed the migration in four.

About a year later, with another upgrade cycle funded—this time knowing we were transitioning to ServiceNow—we migrated to AIX. IBM had gone back to their lab, matched our failover speed, and delivered a cleaner recovery process with faster secondary node restoration. When they met the standard, we said yes.

---

## Enterprise-Scale Infrastructure Authority

- Supported 5,000+ Unix/Linux systems across four datacenters.
- Store QC infrastructure supporting 30,000+ devices critical to store uptime.
- Built SCCM deployment packages distributed to 300,000+ global endpoints (Remedy & SureView).
- Engineered infrastructure for SOC, IR, and Forensics teams.
- Designed mitigation systems internationally under active threat conditions.
- Worked within secure datacenter and air-gapped environments tied to government work.

---

## Security Infrastructure & Enablement

Served on the infrastructure team supporting security operations—Red Team, Blue Team, SOC, Incident Response, and a forensics lab accredited for data recovery and investigations. The U.S. government engaged the lab directly on occasion.

Built a remote data capture system in South Africa over a single weekend to collect evidence on bad actors targeting our systems. My role was never the investigation—it was building the infrastructure that made investigation possible.

This period also deepened the build-train-handoff pattern: after becoming the Mac SME and the developer and administrator for Jamf, Jira, and Confluence, I trained one teammate to take over Mac and Jamf, and another on the Linux backend and Jira development. Once they were running independently, I moved to an air-gapped AI project—which I eventually continued at home, and which became the foundation of the federation described below.

---

## Sovereign AI Federation — Architecture Evolution

The federation evolved deliberately: from a single Mac Studio to a heterogeneous, segmented AI infrastructure with role-specialized nodes and enforced identity boundaries.

- **Redfin**: IT and Security operations. Primary inference: Qwen2.5-72B-Instruct-AWQ via vLLM on consumer Blackwell hardware (RTX PRO 6000, 96GB VRAM), achieving 32 tok/s with AWQ-Marlin quantization and torch.compile. Hosts a 7-specialist democratic Council with 8,600+ recorded votes.
- **Bluefin**: Governance, HR, Legal reasoning domain. PostgreSQL backbone with 88,000+ thermal memories. Vision-language model (Qwen2-VL-7B) on RTX 5070 for camera intelligence. pgvector 0.8.0 with IVFFlat indexing for semantic search across the full memory corpus.
- **Greenfin**: Monitoring and log aggregation via OpenObserve and Promtail. Embedding server (BGE-large-en-v1.5, 1024-dimensional) powering RAG retrieval. CPU offload for distributed computation.
- **Two Mac Studios (M1 Max, 64GB each)**: Cross-platform compute nodes running PyTorch workloads alongside Linux fleet, sharing results through PostgreSQL-backed real-time solution pools.
- **bmasass (M4 Max, 128GB)**: Air-gapped field operations running DeepSeek-R1-32B via MLX for sovereign reasoning without network dependency.
- Dedicated router and VLAN segmentation creating a PII enclave.
- FreeIPA for centralized identity, Kerberos authentication, and policy enforcement.
- Munki for endpoint lifecycle control across Apple nodes.
- Ansible for idempotent infrastructure orchestration and drift control.
- nftables firewall hardening with per-node security policies and Tailscale ACL validation.
- PostgreSQL backbone supporting structured memory, semantic search, and cross-node coordination.
- Continuous testing of emerging AI research papers against live infrastructure.

The system's engineering work is executed through structured instruction documents I author—over 200 to date—each decomposed into steps precise enough for autonomous agents to implement without supervision. The system has completed 564 engineering tasks this way, with a dual-pipeline architecture separating execution (SEARCH/REPLACE code modifications) from planning (task announcement and decomposition). Failed tasks automatically decompose into sub-tasks through a recursive decomposition engine with depth-controlled retry.

The system is governed through what I call the Triad: Munki, Ansible, and FreeIPA—ensuring repeatability, boundary enforcement, and controlled access to sensitive environments. It is designed as a federation, not a monolith.

**Recent capability additions (February 2026)**:
- Semantic RAG over 88,000+ thermal memories using pgvector and BGE-large embeddings (98% coverage), with HyDE query expansion, cross-encoder reranking, and sufficiency gating.
- Corrective RAG (CRAG): self-evaluating retrieval that detects contradictions between retrieved memories and searches for sentinel corrections in real-time—preventing the system from confidently returning outdated or false information.
- Neuroscience-inspired memory architecture: reliability inversion penalizes over-recalled memories (reconsolidation drift), co-retrieval tracking detects contamination windows between suspiciously co-dependent memories, and an automated immune system scans for bulk pattern contamination and dormant high-temperature records.
- Dead letter queue with automatic escalation, step-level checkpointing for resume-from-failure, and recursive task decomposition for failed multi-step tasks.
- LLM-powered self-healing pipeline: alert bridge → remediation engine → validation → Ansible feedback loop, enabling the infrastructure to detect, diagnose, and repair common failure modes without human intervention.
- Ansible foundation deployed across all 5 nodes with idempotent playbooks for federation sync, service deployment, and firewall hardening.
- Distributed cross-platform computation: 28-worker hybrid solver fleet spanning Linux and macOS nodes, coordinated through PostgreSQL-backed shared solution pools.
- Adaptive GPU power monitoring (idle/active polling with thermal-aware scheduling).
- Phase coherence clustering analysis (925 semantic clusters, 0.84 silhouette score) across the thermal memory corpus.

---

## Case Study — Jane Street Neural Net Puzzle ($50K Prize)

The Jane Street "Dropped Neural Net" puzzle presents 97 neural network weight matrices that have been separated and shuffled. The task: find the correct pairing (which input matrix connects to which output matrix) and the correct ordering (the sequence of all 48 layers). The search space is 48! × 48! ≈ 10^122 possible configurations. As of submission, 44 people had solved it.

The federation's approach evolved through structured deliberation cycles. The initial simulated annealing fleet—28 workers across all 5 nodes—hit a hard basin at MSE 0.321 despite 500K iterations. The Council flagged that brute-force search in a 10^122 space was structurally hopeless without structural insight.

The breakthrough came from analyzing the weight matrices themselves. I discovered that trace(W_out @ W_inp) provides a strong structural pairing signal—Hungarian assignment on trace scores matched 38 of 48 pairs that the best solver had found independently. With correct pairings locked, the problem collapsed from 10^122 to 48! (ordering only), and simulated annealing converged rapidly.

The endgame required three distinct algorithmic phases: uncertain position enumeration to identify and resolve the remaining ambiguous positions, swap cascades to drive MSE through successive local minima, and finally simultaneous 3-opt rotations at the last stubborn positions. The solve trajectory: 0.45 → 0.00275 → 0.00173 → 0.000253 → 0.000000. MSE zero, SHA-256 hash matched, submitted to Jane Street on February 16, 2026.

The distributed computation revealed an unexpected architectural resonance: the puzzle solver independently reinvented the same topology as the thermal memory system—PostgreSQL as shared state, quality-gated writes, top-N pruning, and autonomous edge workers. The pattern emerged without planning it. Apple Silicon (M4 Max) ran 2.4–2.8x faster per-thread than Intel/AMD on the numerical workload, which shaped how we allocated work across the heterogeneous fleet.

---

## Military Leadership & Signal Discipline

Promoted to Staff Sergeant during 2005 Iraq deployment, serving as Squad Leader responsible for 13 soldiers including a medic. Cross-trained for security operations at Camp Cropper and Abu Ghraib transition. Tasked with writing all platoon awards—capturing performance clearly and fairly. Our platoon became the most awarded not through exaggeration, but through disciplined documentation.

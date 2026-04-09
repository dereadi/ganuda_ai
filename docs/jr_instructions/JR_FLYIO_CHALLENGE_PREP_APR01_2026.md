# Jr Build Instruction: Fly.io Platform Challenge Prep — TCP Proxy + Tester

## Priority: P1 — Active Job Application (Email Sent Apr 1 2026)
## Assigned: Software Engineer Jr.
## Date: April 1, 2026
## Requested By: TPM

---

## Context

Partner applied to Fly.io Infrastructure Ops Engineering today. Fly.io's hiring process includes 2-3 take-home work-sample challenges. Their public **Platform Challenge** (github.com/fly-hiring/platform-challenge) requires:

1. **A configurable TCP proxy** in Go OR Rust
2. **A testing tool** in THE OTHER language (if proxy is Rust, tester must be Go)
3. **NOTES.md** covering design decisions, production gaps, customer improvements, global clustering

Partner prefers Rust. We build the proxy in Rust, tester in Go.

**CRITICAL**: Fly.io reads NOTES.md BEFORE the code. The notes are where Partner's 21 years of infrastructure experience becomes the differentiator. The code needs to be clean and correct. The notes need to be exceptional.

---

## Task 1: Clone and Analyze the Challenge

1. Clone `https://github.com/fly-hiring/platform-challenge`
2. Read the full README and any supporting docs
3. Document every requirement, constraint, and evaluation criterion
4. Identify what "production readiness gaps" they want discussed (this is a signal — they want to see you know what's missing)
5. Write analysis to `/ganuda/dev/flyio-challenge/ANALYSIS.md`

**Deliverable**: `/ganuda/dev/flyio-challenge/ANALYSIS.md`

---

## Task 2: Build the TCP Proxy in Rust

### Requirements (from the challenge)
- Configurable via YAML or TOML (listen ports, backend addresses)
- Raw TCP proxying (not HTTP-specific)
- Load balancing across multiple backends
- Health checking and failover (remove unhealthy backends, restore when healthy)
- Connection handling (graceful shutdown, timeouts)
- Logging/observability

### Architecture Guidance
- Use **Tokio** for async runtime
- Use **tokio::net::TcpListener** and **TcpStream** for socket handling
- Connection pool pattern: accept on frontend, forward to selected backend, bidirectional copy
- Load balancing: start with round-robin, mention weighted/least-connections in NOTES
- Health check: periodic TCP connect to backends, mark up/down with hysteresis (don't flap)
- Config: **serde** + **toml** or **serde_yaml**
- Error handling: **anyhow** for application errors, **thiserror** for library errors
- Logging: **tracing** crate with structured output

### Code Quality Standards
- Clean, idiomatic Rust. No `unsafe` unless justified.
- Proper error handling — no `.unwrap()` in production paths
- Comments where the WHY isn't obvious, not the WHAT
- Tests for core logic (load balancer selection, health check state machine)
- `cargo clippy` clean, `cargo fmt` applied
- README with build and run instructions

**Deliverable**: `/ganuda/dev/flyio-challenge/proxy/` (Cargo project)

---

## Task 3: Build the Test Tool in Go

### Requirements
- Exercise the proxy from Task 2
- Simulate multiple concurrent clients
- Verify load balancing distribution
- Test failover (kill a backend, verify traffic shifts)
- Test reconnection (bring backend back, verify traffic returns)
- Report results clearly (pass/fail per test, latency stats)

### Architecture Guidance
- Use **net** package for TCP connections
- Use **goroutines** + **sync.WaitGroup** for concurrent clients
- Simple test harness — not a framework, just clear sequential test cases
- Each test: setup → exercise → verify → teardown
- Include a mock TCP echo server that tests can spin up/down to simulate backends
- `go fmt` applied, `go vet` clean

**Deliverable**: `/ganuda/dev/flyio-challenge/tester/` (Go module)

---

## Task 4: Write NOTES.md — THE MOST IMPORTANT DELIVERABLE

This is where Partner wins or loses. Fly.io reads this BEFORE the code.

### Structure
1. **Design Decisions**
   - Why Rust for the proxy (memory safety without GC, Tokio async model, zero-cost abstractions for hot path)
   - Why Go for the tester (fast iteration, goroutines natural for concurrent test clients, complements Rust — shows range)
   - Load balancing strategy chosen and why
   - Health check design: why hysteresis matters (don't flap on a single failed check)
   - Config format choice and why

2. **What I'd Do Differently in Production**
   - Connection pooling to backends (reuse connections, not connect-per-request)
   - Metrics endpoint (Prometheus — Fly.io uses Prometheus natively)
   - Rate limiting per source IP
   - TLS termination (reference fly-proxy's Rust/Hyper approach)
   - Graceful drain on shutdown (stop accepting, finish in-flight, then exit)
   - Circuit breaker pattern on backends (not just health check — adaptive backoff)

3. **Global Clustering Approach** — This is the big question
   - How would you make this proxy work across multiple data centers?
   - Anycast for ingress (same IP advertised from multiple PoPs — Fly.io does this)
   - WireGuard mesh between proxy instances for backend discovery
   - Gossip protocol for state replication (reference Corrosion — Fly.io's own SWIM-based system)
   - Split-brain handling: each proxy instance should be able to operate independently if mesh partitions
   - **Partner's real experience**: "I run a 6-node federation connected by WireGuard where each node owns its own state. This isn't theoretical for me."

4. **Customer-Facing Improvements**
   - Dashboard showing backend health, request distribution, latency percentiles
   - Dry-run config validation (load new config, validate, don't apply until confirmed)
   - Per-customer isolation (one customer's traffic spike shouldn't affect another)
   - Canary routing (send X% of traffic to a new backend version)

### Tone
- Direct. No filler. Every sentence should earn its place.
- Show judgment, not just knowledge. "I chose X over Y because Z" not "X is a popular choice."
- Reference real experience where authentic. Don't name-drop Walmart — say "in a previous large-scale deployment" if relevant.
- Acknowledge tradeoffs honestly. "This implementation cuts corners on X because the challenge is time-boxed. In production, I'd..."

**Deliverable**: `/ganuda/dev/flyio-challenge/NOTES.md`

---

## Task 5: Integration Test

1. Start 3 echo backends on different ports
2. Start the proxy pointing at all 3
3. Run the Go tester against the proxy
4. Kill one backend, verify failover
5. Bring it back, verify recovery
6. Run under load (100+ concurrent connections) — verify no crashes, no leaks
7. Document results in `/ganuda/dev/flyio-challenge/TEST_RESULTS.md`

**Deliverable**: `/ganuda/dev/flyio-challenge/TEST_RESULTS.md`

---

## Constraints

- **This is PREP, not the submission.** When Fly.io sends the actual challenge, there may be differences from the public repo. This is practice so Partner is ready to execute fast.
- **Code must be Partner's voice.** Clean, pragmatic, no over-engineering. The kind of code someone writes when they've seen what breaks at 3 AM.
- **Rust first, Go second.** Priority is getting the proxy solid. The tester can be simpler.
- **NOTES.md is the priority.** If time is limited, a great NOTES.md with a working-but-simple proxy beats a complex proxy with thin notes.

---

## Success Criteria

- [ ] Challenge repo cloned and analyzed
- [ ] TCP proxy builds and runs in Rust (cargo build, cargo run)
- [ ] Proxy correctly load-balances across multiple backends
- [ ] Proxy correctly handles backend failure and recovery
- [ ] Go tester exercises all proxy features
- [ ] NOTES.md covers all four sections with depth and authenticity
- [ ] Integration test passes
- [ ] All code is clippy/vet clean

---

## Design Constraints Referenced

- **DC-10 (Reflex Principle)**: The proxy IS a reflex arc. Fast path = forward packet. Slow path = health check, rebalance. Don't let the slow path block the fast path.
- **DC-9 (Waste Heat Limit)**: Don't waste joules. Zero-copy where possible. Minimize allocations in the hot path.
- **DC-1 (Minimal Energy Awareness)**: The proxy should idle near zero CPU when no traffic flows. Don't busy-loop.

---

*TPM Note: This prep work serves two purposes. First, when Fly.io sends the real challenge, Partner can execute in hours instead of days. Second, the Rust TCP proxy becomes a public artifact on github.com/dereadi — it IS the portfolio piece that replaces a resume. Build it like it matters, because it does.*

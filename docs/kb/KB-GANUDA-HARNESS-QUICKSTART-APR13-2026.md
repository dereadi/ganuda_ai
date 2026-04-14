# KB: ganuda-harness v0.1.0 — Quickstart

**Created:** April 13, 2026
**Location:** `/ganuda/services/ganuda-harness/`
**Binary:** `target/release/ganuda-harness` (9 MB)

## What It Is

Compiled Rust governance proxy for any OpenAI-compatible LLM endpoint. Sits between user and model, intercepts requests/responses with governance checks, writes tamper-evident audit trail.

## Quick Start

```bash
cd /ganuda/services/ganuda-harness

# Build (if needed)
cargo build --release

# Run with defaults (proxy localhost:8000 on port 9200)
./target/release/ganuda-harness

# Run with custom upstream
./target/release/ganuda-harness --upstream "http://10.200.0.1:8000/v1/chat/completions" --port 9200

# Run with config file
./target/release/ganuda-harness --config harness.toml
```

## Test

```bash
# Health check
curl http://localhost:9200/health

# Send a governed request
curl http://localhost:9200/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5-72b", "messages": [{"role": "user", "content": "Hello"}], "max_tokens": 100}'
```

Response includes `_governance` metadata with pre/post check results and audit hash.

## Config (harness.toml)

```toml
[server]
host = "0.0.0.0"
port = 9200

[upstream]
url = "http://localhost:8000/v1/chat/completions"
timeout_secs = 120

[governance]
mandatory_dissent = true
sycophancy_detection = true
autonomy_tier = 1

[audit]
enabled = true
log_path = "./audit.jsonl"
```

## Governance Checks

| Check | Pre/Post | What It Does |
|---|---|---|
| Boundary validation | Pre | Markov blanket — flags external terms crossing declared boundaries |
| Autonomy tier | Pre | Graduated autonomy enforcement (Patent #4) |
| Sycophancy detection | Post | Pattern matching for uncritical agreement (Patent #2) |
| Mandatory dissent | Post | Flags responses with no hedging, risks, or alternatives (Coyote) |
| Design constraints | Post | Regex validation against configurable DCs |
| Chiral validation | Post | Dual-model cross-check (when enabled) |

## Audit Trail

JSONL at `audit.jsonl`. Each record:
- Timestamp, request ID, request hash
- Pre-verdict and post-verdict with all check results
- Chain hash (tamper-evident — includes previous record's hash)

## Architecture

```
src/
├── main.rs              # CLI + server bootstrap
├── config/mod.rs        # TOML config schema
├── governance/
│   ├── mod.rs           # GovernanceEngine (pre_check + post_check)
│   ├── sycophancy.rs    # Patent #2
│   ├── dissent.rs       # Coyote / Byzantine fault detection
│   ├── constraints.rs   # Design constraint validation
│   └── chiral.rs        # Dual-model cross-validation
├── proxy/mod.rs         # HTTP proxy (axum)
└── audit/mod.rs         # Tamper-evident audit trail
```

## Known Issues (v0.1.0)

- Chiral validation not wired into proxy path yet (function exists, not called)
- Council vote mode not implemented (single-response governance only)
- No streaming support (waits for full response before post-check)
- Sycophancy patterns are English-only

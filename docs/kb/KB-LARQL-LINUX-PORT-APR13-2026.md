# KB: LARQL Linux Port — Setup and Usage

**Created:** April 13, 2026
**Upstream:** github.com/chrishayuk/larql
**Location:** `/ganuda/services/larql/`
**Binary:** `target/release/larql`

## Linux Port Changes

Upstream LARQL is built for macOS (Apple Accelerate framework for BLAS). Two files changed for Linux:

**`crates/larql-compute/Cargo.toml`:**
```toml
# Changed from:
blas-src = { version = "0.10", features = ["accelerate"] }
# Changed to:
blas-src = { version = "0.10", features = ["openblas"] }
openblas-src = { version = "0.10", features = ["cblas", "static"] }
```

**`crates/larql-inference/Cargo.toml`:**
Same change.

Static linking — no system libopenblas-dev needed. OpenBLAS compiles from source during `cargo build`.

## Build

```bash
cd /ganuda/services/larql
cargo build --release  # ~1m23s
```

## Extract a Vindex

```bash
# From local safetensors model (Qwen, Llama, etc.)
./target/release/larql extract-index /path/to/model -o model.vindex --f16

# Extraction levels:
#   browse (default): gate + embed + down_meta (~1 GB for 1.5B)
#   inference: + attention + norms (~2 GB)
#   all: + up + down + lm_head for COMPILE (~3 GB)

./target/release/larql extract-index /ganuda/models/qwen2.5-1.5b-instruct \
  -o qwen25-1.5b-full.vindex --level all --f16
```

## Query

```bash
# Walk — graph traversal through all layers
./target/release/larql walk --index model.vindex -p "The capital of France is"

# LQL REPL (needs probing step for DESCRIBE/INFER)
./target/release/larql repl

# LQL one-shot
./target/release/larql lql 'USE "model.vindex"; DESCRIBE "France";'
```

## INSERT (requires --level all extraction)

```bash
./target/release/larql lql \
  'USE "model.vindex"; INSERT INTO EDGES (entity, relation, target) VALUES ("Longhouse", "requires", "mandatory dissent");'
```

## Vindexes on Redfin

| Vindex | Model | Level | Size | Gate Vectors |
|---|---|---|---|---|
| `starcoder2-3b.vindex` | StarCoder2 3B | browse | 0.31 GB | Empty (wrong FFN arch) |
| `qwen25-1.5b.vindex` | Qwen 2.5 1.5B | browse | 1.18 GB | 735 MB ✓ |
| `qwen25-1.5b-full.vindex` | Qwen 2.5 1.5B | all | 2.91 GB | 735 MB ✓ |

## Key Finding

LARQL was built for Gemma's gated FFN (SwiGLU). Qwen also uses SwiGLU → works. StarCoder2 uses a different FFN → gate_vectors empty. Model must have gated FFN architecture for LARQL to work.

## Known Issues

- LQL DESCRIBE/INFER/SHOW need probing step to build semantic labels (not run yet)
- INSERT accepted but verification of weight change pending
- COMPILE (round-trip back to safetensors) not tested
- HuggingFace vindex download returned 404 (repo may not be published)
- Gemma models gated on HuggingFace (need auth token)

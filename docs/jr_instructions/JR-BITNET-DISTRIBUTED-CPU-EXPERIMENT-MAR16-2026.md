# Jr Instruction: BitNet Distributed CPU Inference Experiment

**Epic**: DISTRIBUTED-CPU-INFERENCE-EPIC
**Council Vote**: #72fc2383e2235213 (0.843, PROCEED WITH CAUTION — Raven strategy concern, Turtle 7-gen concern, Coyote dissent on latency)
**Estimated SP**: 5 (Phase 1 only — single-cluster experiment)
**Target Nodes**: greenfin (128 CPU cores), redfin, bmasass, sasass2

---

## Objective

Run a controlled experiment: shard a BitNet ternary model across federation nodes and measure activation-passing latency, throughput, and quality vs single-node inference. This is a learning exercise — we're building institutional knowledge on distributed CPU inference before the rest of the industry arrives.

We are NOT building a product. We are NOT solving internet-scale problems. We are running experiments on our own cluster to become closet SMEs.

## What We're Measuring

1. **Latency per shard hop** — How much does each node-to-node activation pass cost in ms?
2. **Throughput degradation** — Tokens/sec on 1 node vs 2 vs 4
3. **Quality parity** — Does sharded inference produce identical outputs to single-node?
4. **Failure recovery** — What happens when a shard node drops mid-inference?
5. **Network saturation** — How big are activation tensors between shards? WireGuard overhead?

## Prerequisites

1. BitNet model running on greenfin via bitnet.cpp (ALREADY DONE — 48hr warranty gate)
2. bitnet.cpp installed on at least 2 additional nodes
3. WireGuard mesh operational (ALREADY DONE — 10.100.0.0/24)

## Design — Council Concerns as Features

### Coyote (Latency Dissent)
- This is EXACTLY what we're measuring. Coyote says latency kills it at internet scale.
- Experiment 1: WireGuard mesh (sub-1ms latency on LAN). Best case scenario.
- Experiment 2: Route through Tailscale to bmasass (variable latency, real-world conditions).
- If LAN latency already kills it, Coyote wins and we save ourselves from a bad bet.

### Turtle (7-Gen Concern)
- Keep the experiment self-contained. No new infrastructure that requires maintenance.
- Use existing tools: bitnet.cpp, WireGuard, Python scripts for coordination.
- Everything teardown-able in 5 minutes. If it doesn't earn its slot, it dies clean.

### Crawdad (Security)
- Phase 1: All nodes are trusted (our cluster, our WireGuard). No volunteer nodes.
- NO model weights cross the internet. Everything stays on LAN/WireGuard.
- Phase 2 (FUTURE, not this task): Explore SGX enclaves, reputation systems, encrypted activation passing.

### Raven (Strategy)
- This is research, not a sprint commitment. Time-boxed to 1 week.
- If results are promising, write a patent brief. If not, thermalize learnings and move on.
- Don't sacrifice current roadmap velocity for this experiment.

### Gecko (Resources)
- Use greenfin's 128 cores as the primary node (it's already running BitNet).
- Secondary shards on redfin (when GPU isn't loaded) and bmasass (M4 Max, Tailscale).
- CPU budget: use idle cores only. Don't compete with vLLM or gateway.

## Implementation

### Step 1: Install bitnet.cpp on secondary nodes

bitnet.cpp is Microsoft's official CPU inference framework for ternary models.

```bash
# On each secondary node (redfin, bmasass):
git clone https://github.com/microsoft/BitNet.git /ganuda/experiments/bitnet
cd /ganuda/experiments/bitnet
# Follow build instructions for the platform (cmake + clang)
```

Note: bmasass is macOS (M4 Max) — bitnet.cpp supports ARM NEON. Redfin is x86 with AVX2.

### Step 2: Download a BitNet model

Use Microsoft's official bitnet-b1.58-2B-4T (2B parameter, small enough to shard meaningfully):

```bash
# On greenfin:
huggingface-cli download microsoft/bitnet-b1.58-2B-4T --local-dir /ganuda/models/bitnet-2b
```

This is 2B params — small for quality but perfect for experimentation. At ternary (1.58 bits), total weight storage is ~400MB. Trivially shardable.

### Step 3: Single-node baseline

Run the model on greenfin (128 cores) and record:
- Tokens/sec
- Time to first token
- Total inference time for a standard prompt set (10 prompts, varying length)
- CPU utilization pattern

```bash
cd /ganuda/experiments/bitnet
python3 run_inference.py -m /ganuda/models/bitnet-2b -p "What is the capital of France?" -t 4
# Record: tokens/sec, latency, CPU%
```

### Step 4: Manual 2-node shard experiment

This is the core experiment. Split the model layers across 2 nodes.

**Approach A — Pipeline parallelism**:
- Node 1 (greenfin): Layers 0-N/2, processes input → intermediate activations
- Node 2 (redfin or bmasass): Layers N/2-N, receives activations → produces output
- Activation tensor passed via TCP socket over WireGuard

**Approach B — Use existing distributed inference frameworks**:
- Check if bitnet.cpp or llama.cpp has built-in tensor parallelism / pipeline parallelism
- If not, use a simple Python orchestrator with torch.distributed or raw sockets

```python
# Minimal shard coordinator (pseudocode):
# Node 1: run layers 0-12, serialize activations, send to Node 2
# Node 2: receive activations, run layers 13-24, return logits to Node 1
# Measure: send_time, recv_time, compute_time per node, total latency
```

**What to measure at each step**:
- `activation_size_bytes` — How big is the tensor being passed?
- `serialize_time_ms` — Time to pack the tensor for transmission
- `network_time_ms` — Time for the tensor to cross the wire (WireGuard)
- `deserialize_time_ms` — Time to unpack on the receiving node
- `compute_time_ms` — Time for each node to process its shard
- `total_latency_ms` — End-to-end vs single-node baseline

### Step 5: 3-node and 4-node experiments

If 2-node works, extend to 3 and 4 nodes:
- greenfin (WireGuard 10.100.0.1) — shard 1
- redfin (WireGuard 10.100.0.1 — wait, redfin is .1) — actually check IPs
- bmasass (Tailscale 100.103.27.106) — shard N (highest latency, tests Coyote's concern)

### Step 6: Record results and thermalize

Store all measurements in a structured format:

```sql
CREATE TABLE IF NOT EXISTS bitnet_shard_experiments (
    experiment_id SERIAL PRIMARY KEY,
    experiment_name VARCHAR(100),
    node_count INTEGER,
    nodes_used TEXT[],
    model_name VARCHAR(100),
    total_params_b FLOAT,
    bits_per_weight FLOAT,
    prompt TEXT,
    tokens_generated INTEGER,
    tokens_per_second FLOAT,
    total_latency_ms FLOAT,
    activation_size_bytes BIGINT,
    network_time_ms FLOAT,
    compute_time_ms FLOAT,
    network_type VARCHAR(50),  -- 'wireguard_lan', 'tailscale', 'direct_lan'
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

Thermalize key findings with tags: `bitnet`, `distributed_inference`, `cpu_shard`, `experiment`.

## Acceptance Criteria

1. Single-node baseline recorded for bitnet-b1.58-2B on greenfin
2. 2-node sharded inference working (any method)
3. Latency breakdown captured: compute vs network vs serialization
4. Comparison table: 1-node vs 2-node vs 3-node tokens/sec
5. Quality check: same prompt produces same output on 1-node vs sharded
6. Results thermalized with full measurements
7. GO/NO-GO recommendation for further investment

## What NOT To Do

- Do NOT build production infrastructure — this is an experiment
- Do NOT install anything that requires ongoing maintenance (Turtle)
- Do NOT expose any ports to the internet — WireGuard/Tailscale only (Crawdad)
- Do NOT spend more than 1 week on this — if it's not yielding data, stop (Raven)
- Do NOT use the 2B model results to make claims about 70B performance — different regime
- Do NOT compete with vLLM for GPU/CPU resources on redfin — use idle cores only (Gecko)
- Do NOT try to solve volunteer node security yet — that's Phase 2 IF Phase 1 shows promise

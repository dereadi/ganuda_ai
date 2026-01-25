# Jr Instruction: Multi-Node MoE on sasass Cluster

**Created:** December 25, 2025 (Christmas)
**Priority:** 5 (Strategic, high-effort, high-reward)
**Research Basis:** arXiv:2506.23635 - "Multi-Node Expert Parallelism on Apple Silicon for MoE LLMs"
**Connects To:** MLX Migration, LLM Gateway, vLLM on redfin

---

## Executive Summary

Our Mac Studio cluster (sasass + sasass2) has 128GB combined unified memory. The research paper arXiv:2506.23635 demonstrates running **DBRX 132B** (a Mixture of Experts model) across Mac Studio clusters using expert parallelism, achieving **1.15x more cost-efficient than H100 clusters**.

This instruction outlines how to:
1. Set up distributed inference across sasass nodes
2. Run MoE models too large for a single machine
3. Integrate with our existing Gateway infrastructure
4. Position for future 400B+ model capabilities

### Key Research Finding

> "Expert parallelism across M2 Ultra nodes enables 132B parameter MoE models with 1.15x cost efficiency vs NVIDIA H100 clusters."

Our M1 Max nodes are smaller but can still benefit from the architecture for 30-70B MoE models.

---

## Hardware Inventory

| Node | Chip | RAM | Role | IP |
|------|------|-----|------|-----|
| sasass | M1 Max | 64GB | MLX Primary | 192.168.132.241 |
| sasass2 | M1 Max | 64GB | MLX Secondary | 192.168.132.242 |
| **Total** | - | **128GB** | Distributed Inference | - |

### Memory Budget for MoE Models

| Model | Parameters | FP16 Size | 4-bit Size | Fits? |
|-------|------------|-----------|------------|-------|
| Mixtral 8x7B | 47B active | 94GB | ~24GB | ✅ Single node |
| Mixtral 8x22B | 141B total | 282GB | ~71GB | ✅ 2-node cluster |
| DBRX | 132B total | 264GB | ~66GB | ✅ 2-node cluster |
| Qwen2.5-72B-MoE | 72B | 144GB | ~36GB | ✅ Single node |

**Sweet Spot**: Models in the 50-140B range that exceed single-node memory but fit in our 128GB cluster.

---

## Phase 1: Network Infrastructure

### 1.1 High-Speed Interconnect

For distributed inference, inter-node communication latency is critical.

```bash
# Test current network speed between nodes
# On sasass:
iperf3 -s  # Start server

# On sasass2:
iperf3 -c 192.168.132.241 -t 30

# Target: >1 Gbps for reasonable performance
# Ideal: 10 Gbps or Thunderbolt networking
```

### 1.2 Dedicated Inference Network (Optional)

If using Thunderbolt bridge between Mac Studios:

```bash
# Create Thunderbolt bridge network
# This gives ~40 Gbps between nodes

# On both nodes, configure static IPs on Thunderbolt interface:
# sasass:  10.0.0.1/24
# sasass2: 10.0.0.2/24
```

### 1.3 SSH Key Setup

```bash
# On sasass, enable passwordless SSH to sasass2:
ssh-keygen -t ed25519 -f ~/.ssh/id_cluster -N ""
ssh-copy-id -i ~/.ssh/id_cluster cherokee@192.168.132.242

# Test:
ssh -i ~/.ssh/id_cluster cherokee@192.168.132.242 "hostname"
```

---

## Phase 2: MLX Distributed Setup

### 2.1 MLX Distributed Installation

MLX supports distributed execution via `mlx.distributed`:

```bash
# On BOTH sasass and sasass2:
cd /Users/Shared/ganuda
source mlx_venv/bin/activate  # Or create if doesn't exist

pip install --upgrade mlx mlx-lm
pip install mpi4py  # For distributed communication

# Verify distributed support:
python3 -c "import mlx.core.distributed as dist; print(f'Distributed available: {dist.is_available()}')"
```

### 2.2 MPI Configuration

```bash
# Install Open MPI on both nodes (if not present)
brew install open-mpi

# Create hostfile for cluster
cat > /Users/Shared/ganuda/config/mpi_hostfile << 'EOF'
192.168.132.241 slots=1
192.168.132.242 slots=1
EOF

# Test MPI communication:
mpirun -np 2 --hostfile /Users/Shared/ganuda/config/mpi_hostfile hostname
```

---

## Phase 3: Expert Parallelism Architecture

### 3.1 Understanding MoE Distribution

Mixture of Experts models have:
- **Router**: Decides which experts process each token
- **Experts**: Specialized FFN layers (e.g., 8 experts in Mixtral)
- **Shared layers**: Attention, embeddings (not parallelized)

**Expert Parallelism Strategy:**
- Node 1 (sasass): Experts 0-3
- Node 2 (sasass2): Experts 4-7
- Router runs on primary node, dispatches tokens to expert nodes

### 3.2 Model Sharding Script

```python
#!/usr/bin/env python3
"""
Expert Parallelism for MoE Models on Mac Studio Cluster.
File: /Users/Shared/ganuda/lib/moe_distributed.py
"""

import os
import mlx.core as mx
import mlx.core.distributed as dist
from mlx_lm import load
from typing import Dict, List, Tuple, Optional
import numpy as np

# Cluster configuration
CLUSTER_CONFIG = {
    'nodes': [
        {'host': '192.168.132.241', 'rank': 0, 'experts': [0, 1, 2, 3]},
        {'host': '192.168.132.242', 'rank': 1, 'experts': [4, 5, 6, 7]},
    ],
    'primary': 0,
    'model_path': 'mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit',
}


def get_node_rank() -> int:
    """Get this node's rank in the cluster."""
    if dist.is_available():
        return dist.get_rank()
    return 0


def get_world_size() -> int:
    """Get total number of nodes."""
    if dist.is_available():
        return dist.get_world_size()
    return 1


def shard_experts(model, node_config: Dict) -> None:
    """
    Shard model to only keep experts assigned to this node.
    Frees memory for experts not on this node.
    """
    rank = get_node_rank()
    my_experts = CLUSTER_CONFIG['nodes'][rank]['experts']

    # Find and modify expert layers
    for name, module in model.named_modules():
        if 'experts' in name.lower():
            # Keep only our experts, zero out others
            # Implementation depends on model architecture
            pass

    print(f"Node {rank}: Loaded experts {my_experts}")


class DistributedMoEInference:
    """
    Distributed inference for MoE models across Mac Studio cluster.
    """

    def __init__(self, model_path: str = None):
        self.rank = get_node_rank()
        self.world_size = get_world_size()
        self.is_primary = (self.rank == CLUSTER_CONFIG['primary'])

        model_path = model_path or CLUSTER_CONFIG['model_path']

        print(f"Node {self.rank}/{self.world_size}: Loading model...")
        self.model, self.tokenizer = load(model_path)

        # Shard experts for this node
        shard_experts(self.model, CLUSTER_CONFIG['nodes'][self.rank])

        print(f"Node {self.rank}: Ready for inference")

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Generate text using distributed experts.

        Primary node:
        1. Tokenizes input
        2. Runs through non-expert layers
        3. Routes tokens to expert nodes
        4. Collects expert outputs
        5. Continues generation

        Secondary nodes:
        1. Wait for routed tokens
        2. Process through local experts
        3. Return results to primary
        """
        if self.is_primary:
            return self._generate_primary(prompt, max_tokens)
        else:
            return self._generate_worker()

    def _generate_primary(self, prompt: str, max_tokens: int) -> str:
        """Primary node orchestrates generation."""
        tokens = self.tokenizer.encode(prompt)

        for _ in range(max_tokens):
            # Forward through shared layers (attention, etc.)
            hidden_states = self._forward_shared(tokens)

            # Route to experts
            expert_outputs = self._route_to_experts(hidden_states)

            # Combine expert outputs
            combined = self._combine_expert_outputs(expert_outputs)

            # Generate next token
            next_token = self._sample_token(combined)
            tokens.append(next_token)

            if next_token == self.tokenizer.eos_token_id:
                break

        return self.tokenizer.decode(tokens)

    def _generate_worker(self):
        """Worker node processes expert requests."""
        while True:
            # Wait for routing request from primary
            request = dist.recv(source=CLUSTER_CONFIG['primary'])

            if request['type'] == 'expert_forward':
                # Process through local experts
                output = self._forward_local_experts(request['hidden_states'])

                # Send back to primary
                dist.send(output, dest=CLUSTER_CONFIG['primary'])

            elif request['type'] == 'shutdown':
                break

    def _forward_shared(self, tokens):
        """Forward through shared (non-expert) layers."""
        # Implementation depends on model architecture
        pass

    def _route_to_experts(self, hidden_states):
        """Route hidden states to appropriate expert nodes."""
        # Implementation of expert routing
        pass

    def _forward_local_experts(self, hidden_states):
        """Process through experts on this node."""
        # Implementation of local expert forward
        pass

    def _combine_expert_outputs(self, expert_outputs):
        """Combine outputs from all expert nodes."""
        # Implementation of output combination
        pass

    def _sample_token(self, logits):
        """Sample next token from logits."""
        # Implementation of token sampling
        pass


def launch_distributed_inference():
    """
    Launch distributed inference using mpirun.

    Usage:
        mpirun -np 2 --hostfile /Users/Shared/ganuda/config/mpi_hostfile \
            python3 /Users/Shared/ganuda/lib/moe_distributed.py
    """
    dist.init()

    inference = DistributedMoEInference()

    if inference.is_primary:
        # Primary accepts requests
        result = inference.generate("What is the capital of France?")
        print(f"Result: {result}")
    else:
        # Workers process expert requests
        inference.generate("", 0)  # Enters worker loop

    dist.finalize()


if __name__ == '__main__':
    launch_distributed_inference()
```

---

## Phase 4: Simplified Two-Node Pipeline

### 4.1 Pipeline Parallelism Alternative

If expert parallelism is too complex, use simpler pipeline parallelism:

```python
#!/usr/bin/env python3
"""
Simple Pipeline Parallelism for Mac Studio Cluster.
File: /Users/Shared/ganuda/lib/moe_pipeline.py

Node 1 (sasass): Layers 0-15
Node 2 (sasass2): Layers 16-31
"""

import socket
import pickle
import numpy as np
from mlx_lm import load
import mlx.core as mx

# Network config
PRIMARY_HOST = '192.168.132.241'
SECONDARY_HOST = '192.168.132.242'
PIPELINE_PORT = 9999


class PipelineServer:
    """Runs on secondary node, processes second half of layers."""

    def __init__(self, model_path: str):
        print("Loading model (second half of layers)...")
        self.model, self.tokenizer = load(model_path)
        # In practice, would only load layers 16-31

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', PIPELINE_PORT))
        self.socket.listen(1)
        print(f"Pipeline server listening on port {PIPELINE_PORT}")

    def serve(self):
        while True:
            conn, addr = self.socket.accept()
            print(f"Connection from {addr}")

            # Receive hidden states
            data = b''
            while True:
                chunk = conn.recv(65536)
                if not chunk:
                    break
                data += chunk

            hidden_states = pickle.loads(data)

            # Process through second half of layers
            output = self._forward_second_half(hidden_states)

            # Send back
            conn.sendall(pickle.dumps(output))
            conn.close()

    def _forward_second_half(self, hidden_states):
        # Process through layers 16-31
        # This is model-specific
        return hidden_states  # Placeholder


class PipelineClient:
    """Runs on primary node, orchestrates pipeline."""

    def __init__(self, model_path: str):
        print("Loading model (first half of layers)...")
        self.model, self.tokenizer = load(model_path)
        # In practice, would only load layers 0-15

    def generate(self, prompt: str, max_tokens: int = 512) -> str:
        tokens = self.tokenizer.encode(prompt)

        for _ in range(max_tokens):
            # Forward through first half
            hidden = self._forward_first_half(tokens)

            # Send to secondary for second half
            final_hidden = self._send_to_secondary(hidden)

            # Sample next token
            next_token = self._sample(final_hidden)
            tokens.append(next_token)

            if next_token == self.tokenizer.eos_token_id:
                break

        return self.tokenizer.decode(tokens)

    def _forward_first_half(self, tokens):
        # Process through layers 0-15
        return None  # Placeholder

    def _send_to_secondary(self, hidden_states):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((SECONDARY_HOST, PIPELINE_PORT))

        sock.sendall(pickle.dumps(hidden_states))
        sock.shutdown(socket.SHUT_WR)

        # Receive result
        data = b''
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                break
            data += chunk

        sock.close()
        return pickle.loads(data)

    def _sample(self, hidden_states):
        # Sample next token
        return 0  # Placeholder
```

---

## Phase 5: Model Selection

### 5.1 Recommended MoE Models for 128GB Cluster

| Model | Size | Experts | Performance | Notes |
|-------|------|---------|-------------|-------|
| **Mixtral-8x7B-4bit** | ~24GB | 8x7B | Good | Fits single node, good baseline |
| **Mixtral-8x22B-4bit** | ~71GB | 8x22B | Excellent | Requires 2 nodes |
| **Qwen2.5-MoE-72B-4bit** | ~36GB | MoE | Very Good | Single node possible |
| **DeepSeek-MoE-16B** | ~8GB | 64x | Fast | Many small experts |

### 5.2 Download Strategy

```bash
# On sasass (primary):
cd /Users/Shared/ganuda/models

# Start with single-node MoE for testing
huggingface-cli download mlx-community/Mixtral-8x7B-Instruct-v0.1-4bit

# Then larger model requiring distribution
huggingface-cli download mlx-community/Mixtral-8x22B-Instruct-v0.1-4bit
```

---

## Phase 6: Gateway Integration

### 6.1 Add Distributed Model Endpoint

```python
# In /ganuda/services/llm_gateway/gateway.py

@app.post("/v1/chat/completions/moe")
async def moe_chat_completions(request: ChatRequest):
    """
    Chat completions using distributed MoE model.
    Routes to sasass cluster for large model inference.
    """
    # Check if distributed inference is available
    cluster_status = check_cluster_health()

    if not cluster_status['healthy']:
        # Fall back to single-node model
        return await standard_chat_completions(request)

    # Use distributed inference
    from lib.moe_distributed import DistributedMoEClient

    client = DistributedMoEClient()
    response = client.generate(
        messages=request.messages,
        max_tokens=request.max_tokens
    )

    return format_openai_response(response)


def check_cluster_health() -> Dict:
    """Check if both sasass nodes are available."""
    import socket

    nodes = [
        ('192.168.132.241', 8000),
        ('192.168.132.242', 8000),
    ]

    healthy = True
    status = {}

    for host, port in nodes:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            status[host] = result == 0
            if result != 0:
                healthy = False
        except:
            status[host] = False
            healthy = False

    return {'healthy': healthy, 'nodes': status}
```

### 6.2 Model Router

```python
# In /ganuda/lib/model_router.py

class ModelRouter:
    """
    Routes requests to appropriate model backend.

    - Simple queries → Qwen-14B on single sasass (fast)
    - Complex queries → Mixtral-8x22B on cluster (quality)
    - GPU queries → vLLM on redfin (fastest)
    """

    def __init__(self):
        self.backends = {
            'fast': {'host': '192.168.132.241', 'port': 8000, 'model': 'Qwen2.5-14B'},
            'quality': {'host': '192.168.132.241', 'port': 8001, 'model': 'Mixtral-8x22B'},
            'gpu': {'host': '192.168.132.223', 'port': 8000, 'model': 'Nemotron-9B'},
        }

    def route(self, request: Dict) -> str:
        """Determine best backend for request."""
        # Complex reasoning → quality
        if any(kw in request.get('messages', [{}])[-1].get('content', '').lower()
               for kw in ['analyze', 'compare', 'explain why', 'reason through']):
            return 'quality'

        # Code generation → GPU (fast)
        if any(kw in request.get('messages', [{}])[-1].get('content', '').lower()
               for kw in ['write code', 'function', 'implement', 'debug']):
            return 'gpu'

        # Default → fast
        return 'fast'
```

---

## Phase 7: Monitoring and Orchestration

### 7.1 Cluster Health Daemon

```python
#!/usr/bin/env python3
"""
Mac Studio Cluster Health Monitor.
File: /Users/Shared/ganuda/services/cluster_monitor.py
"""

import time
import psutil
import socket
import json
from datetime import datetime

CLUSTER_NODES = [
    {'name': 'sasass', 'host': '192.168.132.241', 'port': 8000},
    {'name': 'sasass2', 'host': '192.168.132.242', 'port': 8000},
]

def check_node_health(node: Dict) -> Dict:
    """Check health of a single node."""
    health = {
        'name': node['name'],
        'host': node['host'],
        'timestamp': datetime.now().isoformat(),
        'reachable': False,
        'service_up': False,
        'metrics': {}
    }

    # Check network reachability
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((node['host'], 22))
        sock.close()
        health['reachable'] = (result == 0)
    except:
        pass

    # Check MLX service
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((node['host'], node['port']))
        sock.close()
        health['service_up'] = (result == 0)
    except:
        pass

    # Get metrics via SSH (if reachable)
    if health['reachable']:
        try:
            import subprocess
            result = subprocess.run(
                ['ssh', f"cherokee@{node['host']}",
                 'python3 -c "import psutil; import json; print(json.dumps({\'cpu\': psutil.cpu_percent(), \'mem\': psutil.virtual_memory().percent}))"'],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                health['metrics'] = json.loads(result.stdout.strip())
        except:
            pass

    return health


def monitor_cluster():
    """Continuous cluster monitoring."""
    while True:
        cluster_health = {
            'timestamp': datetime.now().isoformat(),
            'nodes': [],
            'cluster_healthy': True
        }

        for node in CLUSTER_NODES:
            node_health = check_node_health(node)
            cluster_health['nodes'].append(node_health)

            if not node_health['service_up']:
                cluster_health['cluster_healthy'] = False

        # Log to file
        with open('/Users/Shared/ganuda/logs/cluster_health.json', 'w') as f:
            json.dump(cluster_health, f, indent=2)

        # Alert if unhealthy
        if not cluster_health['cluster_healthy']:
            print(f"⚠️  Cluster unhealthy at {cluster_health['timestamp']}")
            # Could send to Telegram, etc.

        time.sleep(60)  # Check every minute


if __name__ == '__main__':
    monitor_cluster()
```

---

## Validation Checklist

- [ ] Network speed tested between sasass nodes (>1 Gbps)
- [ ] SSH passwordless auth configured
- [ ] MLX distributed installed on both nodes
- [ ] MPI working between nodes
- [ ] Single-node MoE (Mixtral-8x7B) working on sasass
- [ ] Model sharding implemented
- [ ] Pipeline or expert parallelism tested
- [ ] Gateway integration complete
- [ ] Cluster health monitor deployed
- [ ] Performance benchmarked
- [ ] Results recorded to thermal memory

---

## Expected Outcomes

1. **Model Capacity**: Run 70-140B MoE models (vs 14B single node)
2. **Cost Efficiency**: 1.15x vs cloud GPU per the research
3. **Quality**: Larger models = better reasoning for complex queries
4. **Sovereignty**: All inference stays on-premises

---

## Seven Generations Consideration

Running larger models locally aligns with our sovereignty principle:

> "Intelligence should be distributed, accountable, auditable, and owned by those who generate it."

The 132B model that would cost $10K+/month on cloud GPUs runs on our own hardware. The knowledge stays in the Tribe.

**For Seven Generations - our intelligence runs on our metal.**

---

*Created: December 25, 2025 (Christmas)*
*Research: arXiv:2506.23635 - Multi-Node Expert Parallelism on Apple Silicon*
*Priority: 5 (Strategic, Phase 2 implementation)*

# JR INSTRUCTION: S-PATH-RAG P-1 — GNN Encoder + Path Search Prototype

**Task**: Build the GNN encoder for thermal KG and semantic-weighted shortest path search. Core S-PATH-RAG retrieval pipeline.
**Priority**: P1 (the main innovation)
**Date**: 2026-03-30
**TPM**: Claude Opus
**Story Points**: 8
**Depends On**: JR-SPATH-RAG-P2-KG-POPULATION (50K+ edges with embeddings)

## Problem Statement

With a populated KG (nodes with 1024d embeddings, edges with 1024d embeddings and typed relationships), we need:
1. A GNN that processes the graph topology into dense representations preserving multi-hop structure
2. A path search algorithm that finds semantically-weighted shortest paths between relevant nodes
3. A path scoring mechanism that ranks and prunes paths

This is the retrieval engine. It replaces pgvector similarity search with topology-aware path retrieval.

## Task 1: Install PyTorch Geometric on redfin (0.5 SP)

```bash
pip install torch-geometric torch-scatter torch-sparse torch-cluster
```

Verify:
```python
import torch_geometric
print(torch_geometric.__version__)
```

If CUDA build issues, fall back to CPU-only PyG (the KG is not huge — 95K nodes is fine on CPU for inference).

## Task 2: GNN Encoder (3 SP)

**Create**: `/ganuda/lib/kg_gnn_encoder.py`

Build a Graph Attention Network (GAT) encoder that takes the thermal KG and produces updated node/edge representations incorporating multi-hop topology.

```python
import torch
import torch.nn.functional as F
from torch_geometric.nn import GATConv
from torch_geometric.data import Data

class ThermalKGEncoder(torch.nn.Module):
    """GAT encoder for thermal memory knowledge graph.

    Takes node embeddings (1024d from BGE-large) and edge embeddings (1024d),
    produces topology-aware representations that preserve multi-hop structure.

    2-layer GAT with 8 attention heads per layer.
    """
    def __init__(self, in_dim=1024, hidden_dim=512, out_dim=256, heads=8):
        super().__init__()
        self.conv1 = GATConv(in_dim, hidden_dim, heads=heads, concat=False)
        self.conv2 = GATConv(hidden_dim, out_dim, heads=heads, concat=False)
        self.edge_proj = torch.nn.Linear(in_dim, hidden_dim)

    def forward(self, x, edge_index, edge_attr=None):
        """
        x: Node features [num_nodes, 1024]
        edge_index: Edge connectivity [2, num_edges]
        edge_attr: Edge features [num_edges, 1024]
        """
        # Project edge attributes if available
        if edge_attr is not None:
            edge_attr = self.edge_proj(edge_attr)

        # Layer 1
        x = self.conv1(x, edge_index)
        x = F.elu(x)

        # Layer 2
        x = self.conv2(x, edge_index)

        return x  # [num_nodes, out_dim]

    def encode_subgraph(self, node_ids, conn):
        """Extract subgraph around node_ids from DB and encode."""
        # 1. Fetch node embeddings for node_ids + their 2-hop neighbors
        # 2. Fetch edges between those nodes
        # 3. Build PyG Data object
        # 4. Forward pass
        # 5. Return encoded representations
        pass
```

**Key design decisions**:
- 2-layer GAT captures 2-hop neighborhoods (sufficient for most thermal memory reasoning)
- Output dim 256 (compressed from 1024) — this is what gets injected into LLM attention
- Edge attributes projected to hidden_dim for edge-aware attention
- `encode_subgraph()` is the main API — takes node IDs, fetches neighborhood from DB, encodes

### Subgraph extraction:

```python
def extract_subgraph(center_node_ids, hop=2, max_nodes=500, conn=None):
    """Extract k-hop subgraph around center nodes from thermal KG.

    Returns PyG Data object ready for GNN encoding.
    """
    cur = conn.cursor()

    # BFS expansion from center nodes
    visited = set(center_node_ids)
    frontier = set(center_node_ids)

    for _ in range(hop):
        if len(visited) >= max_nodes:
            break
        cur.execute("""
            SELECT DISTINCT target_memory_id
            FROM thermal_relationships
            WHERE source_memory_id = ANY(%s)
              AND (valid_until IS NULL OR valid_until > NOW())
            UNION
            SELECT DISTINCT source_memory_id
            FROM thermal_relationships
            WHERE target_memory_id = ANY(%s)
              AND (valid_until IS NULL OR valid_until > NOW())
        """, (list(frontier), list(frontier)))

        new_nodes = {r[0] for r in cur.fetchall()} - visited
        visited.update(new_nodes)
        frontier = new_nodes

    # Fetch node embeddings
    cur.execute("""
        SELECT id, embedding FROM thermal_memory_archive
        WHERE id = ANY(%s) AND embedding IS NOT NULL
    """, (list(visited),))
    # ... build node feature matrix

    # Fetch edges between these nodes
    cur.execute("""
        SELECT source_memory_id, target_memory_id, edge_embedding, confidence
        FROM thermal_relationships
        WHERE source_memory_id = ANY(%s) AND target_memory_id = ANY(%s)
          AND (valid_until IS NULL OR valid_until > NOW())
    """, (list(visited), list(visited)))
    # ... build edge_index and edge_attr tensors

    return Data(x=node_features, edge_index=edge_index, edge_attr=edge_attr)
```

## Task 3: Semantic-Weighted Shortest Path Search (2.5 SP)

**Create**: `/ganuda/lib/kg_path_search.py`

Given a query, find the top-K shortest paths through the KG that are semantically relevant.

```python
def find_semantic_paths(query_embedding, kg_data, gnn_encoder, top_k=20, max_hops=4):
    """Find top-K semantically-weighted shortest paths for a query.

    1. Identify entry nodes (closest to query by embedding similarity)
    2. Run modified Dijkstra with semantic weight: w(e) = 1 - cosine_sim(edge_emb, query_emb)
    3. Return top-K paths by total semantic weight
    """
    # Step 1: Find entry points (top-10 nodes closest to query)
    entry_nodes = find_closest_nodes(query_embedding, kg_data.x, top_n=10)

    # Step 2: Encode subgraph via GNN
    encoded = gnn_encoder(kg_data.x, kg_data.edge_index, kg_data.edge_attr)

    # Step 3: For each entry node, run weighted shortest path
    # Weight = 1 - cosine_similarity(encoded_edge, query_embedding_projected)
    # Lower weight = more semantically relevant

    # Step 4: Collect all paths, score, rank, return top-K
    pass
```

**Path representation**: Each path is a list of (node_id, edge_type, node_id, ...) with an aggregate score.

## Task 4: Path Scorer with Gumbel-Softmax (2 SP)

**Create**: `/ganuda/lib/kg_path_scorer.py`

Differentiable path scoring — assigns probability to each path, enabling gradient flow back to the retriever.

```python
class PathScorer(torch.nn.Module):
    """Score paths using Gumbel-Softmax for differentiable selection.

    Takes encoded path representations, produces soft selection weights.
    During training: Gumbel-Softmax (differentiable)
    During inference: argmax or top-K selection
    """
    def __init__(self, path_dim=256, hidden_dim=128):
        super().__init__()
        self.scorer = torch.nn.Sequential(
            torch.nn.Linear(path_dim, hidden_dim),
            torch.nn.ReLU(),
            torch.nn.Linear(hidden_dim, 1)
        )
        self.temperature = 0.5  # Gumbel-Softmax temperature

    def forward(self, path_encodings, training=True):
        """
        path_encodings: [num_paths, path_dim]
        Returns: soft selection weights [num_paths]
        """
        logits = self.scorer(path_encodings).squeeze(-1)

        if training:
            # Gumbel-Softmax for differentiable selection
            return F.gumbel_softmax(logits, tau=self.temperature, hard=False)
        else:
            # Hard selection for inference
            return F.softmax(logits, dim=0)
```

## Verification

1. **GNN encoder**: Feed a small subgraph (100 nodes, 500 edges) and verify output shape is [100, 256]
2. **Path search**: For a known query ("What council votes were related to memory architecture?"), verify paths traverse sensible nodes
3. **Path scorer**: Verify Gumbel-Softmax produces valid probability distributions (sum to 1, all positive)
4. **End-to-end**: Query → entry nodes → subgraph extraction → GNN encoding → path search → scored paths. Compare retrieved paths to current pgvector RAG results. Do the paths make more sense?

## Notes

- This is P-1 (one step before deployment). It builds the retrieval engine but does NOT yet inject into the LLM.
- The cross-attention injection (P-Day) is a separate instruction that depends on this working.
- Start with CPU-only inference for prototyping. GPU optimization comes later.
- The GNN does NOT need training initially — use it as a fixed feature extractor. Training comes after we have evaluation data.

---

FOR SEVEN GENERATIONS

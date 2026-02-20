# Jr Instruction: Phase Coherence — UMAP + HDBSCAN Clustering Pipeline

**Task**: Build a standalone script that analyzes the federation's 78K thermal memories using UMAP dimensionality reduction and HDBSCAN clustering to visualize memory coherence patterns.

**Priority**: HIGH (Council Vote #4b2f4691, unanimous PROCEED)
**Council Confidence**: 0.844
**Kanban**: #1760 (Thermal Memory RAG — sub-task)
**Methodology**: Long Man — Phase A of 3-phase Phase Coherence Revival

---

## Context

The federation has 78K thermal memories in `thermal_memory_archive` on bluefin (192.168.132.222). These memories are being embedded with BGE-large-en-v1.5 (1024-dimensional vectors) stored in the `embedding` column (pgvector). This script analyzes those embeddings to find natural clusters, measure coherence, and produce visualizations.

**This is the cluster analyzing its OWN memory structure** — the self-observation layer. The script is READ-ONLY against the database (no writes to thermal_memory_archive).

## Dependencies

Install in `/ganuda/venv` on redfin:
```text
pip install umap-learn hdbscan scikit-learn matplotlib
```

**Note for executor**: These are pip install commands, NOT code blocks. Do not auto-execute.

## Step 1: Create the Phase Coherence Clustering Script

Create `/ganuda/scripts/phase_coherence_clustering.py`

```python
#!/usr/bin/env python3
"""
Phase Coherence Clustering — UMAP + HDBSCAN Pipeline
Analyzes federation thermal memory embeddings to find coherence patterns.

Council Vote: #4b2f4691 (unanimous PROCEED, 0.844 confidence)
Phase A of 3-phase Phase Coherence Revival.

READ-ONLY: Does not modify thermal_memory_archive.
Outputs: visualization PNG + cluster report JSON to /ganuda/reports/phase_coherence/
"""

import os
import sys
import json
import numpy as np
import psycopg2
from datetime import datetime

# Lazy imports for heavy ML libraries
def get_umap():
    import umap
    return umap

def get_hdbscan():
    import hdbscan
    return hdbscan

def get_sklearn_metrics():
    from sklearn.metrics import silhouette_score, silhouette_samples
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    return silhouette_score, silhouette_samples, StandardScaler, PCA

def get_matplotlib():
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.cm as cm
    return plt, cm


# --- Configuration ---
DB_HOST = os.environ.get("CHEROKEE_DB_HOST", "192.168.132.222")
DB_NAME = os.environ.get("CHEROKEE_DB_NAME", "zammad_production")
DB_USER = os.environ.get("CHEROKEE_DB_USER", "claude")
DB_PASS = os.environ.get("CHEROKEE_DB_PASS", "")

OUTPUT_DIR = "/ganuda/reports/phase_coherence"

# UMAP parameters
UMAP_N_NEIGHBORS = 30      # Balance local vs global structure
UMAP_MIN_DIST = 0.1        # How tightly UMAP packs points
UMAP_N_COMPONENTS = 2      # 2D for visualization
UMAP_METRIC = "cosine"     # Match pgvector cosine similarity

# HDBSCAN parameters
HDBSCAN_MIN_CLUSTER_SIZE = 20   # Minimum memories per cluster
HDBSCAN_MIN_SAMPLES = 5         # Core point density


def load_embeddings():
    """Load all embedded thermal memories from the database. READ-ONLY."""
    conn = psycopg2.connect(
        host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS
    )
    cur = conn.cursor()

    # Only load memories that have embeddings
    cur.execute("""
        SELECT id, embedding::text, temperature_score, sacred_pattern,
               created_at, metadata
        FROM thermal_memory_archive
        WHERE embedding IS NOT NULL
        ORDER BY id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

    if not rows:
        print("ERROR: No embedded memories found. Is the backfill complete?")
        sys.exit(1)

    ids = []
    embeddings = []
    temperatures = []
    sacred_flags = []
    created_dates = []
    metadata_list = []

    for row in rows:
        mem_id, emb_str, temp, sacred, created, meta = row
        # Parse pgvector string format: [0.1,0.2,...,0.9]
        emb_values = [float(x) for x in emb_str.strip('[]').split(',')]
        ids.append(mem_id)
        embeddings.append(emb_values)
        temperatures.append(float(temp) if temp else 0.0)
        sacred_flags.append(bool(sacred))
        created_dates.append(created.isoformat() if created else "")
        metadata_list.append(meta if meta else {})

    print(f"Loaded {len(ids)} embedded memories")
    return ids, np.array(embeddings), temperatures, sacred_flags, created_dates, metadata_list


def run_pca_reduction(embeddings, target_dims=50):
    """PCA pre-reduction from 1024 to 50 dims (speeds up UMAP)."""
    _, _, _, PCA = get_sklearn_metrics()

    n_components = min(target_dims, embeddings.shape[0], embeddings.shape[1])
    pca = PCA(n_components=n_components, random_state=42)
    reduced = pca.fit_transform(embeddings)

    explained = sum(pca.explained_variance_ratio_) * 100
    print(f"PCA: {embeddings.shape[1]}d -> {n_components}d ({explained:.1f}% variance retained)")
    return reduced


def run_umap(embeddings_pca):
    """UMAP dimensionality reduction to 2D for visualization."""
    umap = get_umap()

    reducer = umap.UMAP(
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        n_components=UMAP_N_COMPONENTS,
        metric=UMAP_METRIC,
        random_state=42,
        verbose=True
    )

    coords_2d = reducer.fit_transform(embeddings_pca)
    print(f"UMAP: {embeddings_pca.shape[1]}d -> 2d")
    return coords_2d


def run_hdbscan(coords_2d):
    """HDBSCAN clustering on UMAP coordinates."""
    hdbscan = get_hdbscan()

    clusterer = hdbscan.HDBSCAN(
        min_cluster_size=HDBSCAN_MIN_CLUSTER_SIZE,
        min_samples=HDBSCAN_MIN_SAMPLES,
        metric='euclidean',
        cluster_selection_method='eom'  # Excess of mass
    )

    labels = clusterer.fit_predict(coords_2d)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise = list(labels).count(-1)

    print(f"HDBSCAN: {n_clusters} clusters found, {n_noise} noise points ({n_noise/len(labels)*100:.1f}%)")
    return labels, clusterer


def compute_silhouette(coords_2d, labels):
    """Compute silhouette scores for cluster quality assessment."""
    silhouette_score, silhouette_samples, _, _ = get_sklearn_metrics()

    # Filter out noise points (label -1) for silhouette calculation
    mask = labels != -1
    if mask.sum() < 2:
        print("WARNING: Not enough clustered points for silhouette scoring")
        return 0.0, np.zeros(len(labels))

    score = silhouette_score(coords_2d[mask], labels[mask])
    sample_scores = np.zeros(len(labels))
    sample_scores[mask] = silhouette_samples(coords_2d[mask], labels[mask])

    print(f"Silhouette score: {score:.4f} (>0.5 = strong, >0.25 = fair, <0.25 = weak)")
    return score, sample_scores


def generate_visualization(coords_2d, labels, temperatures, sacred_flags, output_path):
    """Generate 2D scatter plot of memory clusters."""
    plt, cm = get_matplotlib()

    fig, axes = plt.subplots(1, 2, figsize=(20, 10))

    # Plot 1: Clusters colored by HDBSCAN label
    ax1 = axes[0]
    unique_labels = sorted(set(labels))
    colors = plt.cm.tab20(np.linspace(0, 1, max(len(unique_labels), 1)))

    for i, label in enumerate(unique_labels):
        mask = labels == label
        if label == -1:
            ax1.scatter(coords_2d[mask, 0], coords_2d[mask, 1],
                       c='lightgray', s=5, alpha=0.3, label=f'Noise ({mask.sum()})')
        else:
            ax1.scatter(coords_2d[mask, 0], coords_2d[mask, 1],
                       c=[colors[i % len(colors)]], s=10, alpha=0.6,
                       label=f'Cluster {label} ({mask.sum()})')

    ax1.set_title('Thermal Memory Clusters (HDBSCAN)', fontsize=14)
    ax1.set_xlabel('UMAP-1')
    ax1.set_ylabel('UMAP-2')
    if len(unique_labels) <= 20:
        ax1.legend(fontsize=8, loc='best', framealpha=0.7)

    # Plot 2: Temperature heatmap
    ax2 = axes[1]
    temp_array = np.array(temperatures)
    scatter = ax2.scatter(coords_2d[:, 0], coords_2d[:, 1],
                         c=temp_array, cmap='RdYlBu_r', s=10, alpha=0.6,
                         vmin=0, vmax=100)
    plt.colorbar(scatter, ax=ax2, label='Temperature Score')

    # Highlight sacred patterns
    sacred_mask = np.array(sacred_flags)
    if sacred_mask.any():
        ax2.scatter(coords_2d[sacred_mask, 0], coords_2d[sacred_mask, 1],
                   facecolors='none', edgecolors='gold', s=30, linewidths=1.5,
                   label=f'Sacred ({sacred_mask.sum()})')
        ax2.legend(fontsize=10, loc='best')

    ax2.set_title('Temperature Distribution + Sacred Patterns', fontsize=14)
    ax2.set_xlabel('UMAP-1')
    ax2.set_ylabel('UMAP-2')

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
    fig.suptitle(f'Cherokee AI Federation — Phase Coherence Analysis\n{len(labels)} memories, {timestamp}',
                fontsize=16, fontweight='bold')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"Visualization saved: {output_path}")


def generate_report(ids, labels, temperatures, sacred_flags, silhouette_score_val,
                   sample_scores, metadata_list, output_path):
    """Generate JSON report of cluster analysis."""
    clusters = {}
    unique_labels = sorted(set(labels))

    for label in unique_labels:
        mask = labels == label
        cluster_temps = [temperatures[i] for i in range(len(temperatures)) if mask[i]]
        cluster_sacred = [sacred_flags[i] for i in range(len(sacred_flags)) if mask[i]]
        cluster_ids = [ids[i] for i in range(len(ids)) if mask[i]]
        cluster_silhouettes = sample_scores[mask]

        # Extract metadata types
        type_counts = {}
        for i in range(len(metadata_list)):
            if mask[i] and isinstance(metadata_list[i], dict):
                mtype = metadata_list[i].get('type', 'unknown')
                type_counts[mtype] = type_counts.get(mtype, 0) + 1

        cluster_key = f"noise" if label == -1 else f"cluster_{label}"
        clusters[cluster_key] = {
            "size": int(mask.sum()),
            "avg_temperature": round(np.mean(cluster_temps), 2) if cluster_temps else 0,
            "max_temperature": round(max(cluster_temps), 2) if cluster_temps else 0,
            "sacred_count": sum(cluster_sacred),
            "sacred_ratio": round(sum(cluster_sacred) / max(mask.sum(), 1), 3),
            "avg_silhouette": round(float(np.mean(cluster_silhouettes)), 4),
            "memory_ids_sample": cluster_ids[:10],  # First 10 for reference
            "metadata_types": type_counts
        }

    report = {
        "generated_at": datetime.now().isoformat(),
        "total_memories": len(ids),
        "total_clusters": len([l for l in unique_labels if l != -1]),
        "noise_points": int(list(labels).count(-1)),
        "noise_ratio": round(list(labels).count(-1) / max(len(labels), 1), 3),
        "overall_silhouette_score": round(float(silhouette_score_val), 4),
        "coherence_assessment": (
            "STRONG" if silhouette_score_val > 0.5 else
            "FAIR" if silhouette_score_val > 0.25 else
            "WEAK"
        ),
        "parameters": {
            "umap_n_neighbors": UMAP_N_NEIGHBORS,
            "umap_min_dist": UMAP_MIN_DIST,
            "umap_metric": UMAP_METRIC,
            "hdbscan_min_cluster_size": HDBSCAN_MIN_CLUSTER_SIZE,
            "hdbscan_min_samples": HDBSCAN_MIN_SAMPLES
        },
        "clusters": clusters
    }

    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Report saved: {output_path}")
    return report


def main():
    """Main pipeline: Load -> PCA -> UMAP -> HDBSCAN -> Silhouette -> Viz + Report."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    viz_path = os.path.join(OUTPUT_DIR, f"phase_coherence_{timestamp}.png")
    report_path = os.path.join(OUTPUT_DIR, f"phase_coherence_{timestamp}.json")

    print("=" * 60)
    print("Phase Coherence Analysis — UMAP + HDBSCAN Pipeline")
    print("=" * 60)

    # Step 1: Load embeddings
    print("\n[1/5] Loading embeddings from thermal_memory_archive...")
    ids, embeddings, temperatures, sacred_flags, created_dates, metadata_list = load_embeddings()

    # Step 2: PCA pre-reduction
    print("\n[2/5] PCA dimensionality reduction...")
    embeddings_pca = run_pca_reduction(embeddings)

    # Step 3: UMAP
    print("\n[3/5] UMAP projection to 2D...")
    coords_2d = run_umap(embeddings_pca)

    # Step 4: HDBSCAN clustering
    print("\n[4/5] HDBSCAN clustering...")
    labels, clusterer = run_hdbscan(coords_2d)

    # Step 5: Silhouette scoring
    print("\n[5/5] Computing silhouette scores...")
    sil_score, sample_scores = compute_silhouette(coords_2d, labels)

    # Generate outputs
    print("\n--- Generating outputs ---")
    generate_visualization(coords_2d, labels, temperatures, sacred_flags, viz_path)
    report = generate_report(ids, labels, temperatures, sacred_flags,
                            sil_score, sample_scores, metadata_list, report_path)

    # Summary
    print("\n" + "=" * 60)
    print("PHASE COHERENCE ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Memories analyzed: {len(ids)}")
    print(f"Clusters found: {report['total_clusters']}")
    print(f"Noise ratio: {report['noise_ratio']*100:.1f}%")
    print(f"Coherence: {report['coherence_assessment']} (silhouette={sil_score:.4f})")
    print(f"Visualization: {viz_path}")
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
```

## Step 2: Create Output Directory

```text
mkdir -p /ganuda/reports/phase_coherence
```

## Verification

After running the script, check:
1. PNG visualization exists in `/ganuda/reports/phase_coherence/`
2. JSON report exists with cluster details
3. Silhouette score is reported (>0.25 = fair, >0.5 = strong)
4. No writes were made to thermal_memory_archive

## Notes

- This script is READ-ONLY — it queries embeddings but never writes back
- Requires the embedding backfill to be complete (or mostly complete) before running
- PCA pre-reduction from 1024d to 50d speeds up UMAP significantly
- Sacred pattern memories are highlighted with gold rings in the visualization
- The JSON report includes sample memory IDs per cluster for manual inspection
- Output goes to /ganuda/reports/phase_coherence/ (timestamped files)

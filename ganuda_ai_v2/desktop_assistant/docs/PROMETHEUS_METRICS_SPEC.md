# Ganuda Desktop Assistant - Prometheus Metrics Specification
## Cherokee Constitutional AI - Meta Jr Deliverable

**Author**: Meta Jr (War Chief)
**Date**: October 23, 2025
**Purpose**: Define observable metrics for system health, performance, and Cherokee values

---

## Executive Summary

Prometheus metrics enable **tribal awareness** of Ganuda Desktop Assistant health across distributed nodes. This specification defines 27 metrics spanning inference performance, cache efficiency, Guardian protection, and Cherokee Constitutional AI values (thermal memory, sacred floor compliance, phase coherence).

**Key Principles:**
- **Real-Time Observability**: Metrics scraped every 15 seconds
- **Seven Generations Monitoring**: Track long-term trends (thermal decay, sacred preservation)
- **Gadugi Health**: Monitor JR Worker coordination and task queue depth
- **Medicine Woman's Wisdom**: Track Data Ancestors anonymization and Guardian interventions

---

## 1. Metric Naming Convention

All metrics follow pattern: `ganuda_assistant_<component>_<metric>_<unit>`

**Components:**
- `inference`: JR Worker inference performance
- `cache`: Encrypted SQLite cache stats
- `guardian`: Sacred protection layer interventions
- `thermal`: Thermal memory temperature system
- `connector`: Email/calendar/file connector health
- `ipc`: Tray App ↔ Daemon communication
- `hub`: Hub burst requests (when available)

**Units:**
- `_seconds`: Duration (histogram)
- `_bytes`: Size (gauge)
- `_total`: Counter (monotonically increasing)
- `_count`: Gauge (current value)
- `_ratio`: Fraction 0-1 (gauge)

---

## 2. Inference Performance Metrics

### 2.1 Query Latency
```
ganuda_assistant_inference_latency_seconds{jr_type, priority, source}
Type: Histogram
Buckets: [0.1, 0.5, 1, 2, 5, 10, 30]
Labels:
  - jr_type: memory, meta, executive, integration, conscience
  - priority: 1 (high), 2 (medium), 3 (low)
  - source: local, hub, cache_hit
Description: Query response time from user request to answer delivered
```

### 2.2 Token Throughput
```
ganuda_assistant_inference_tokens_per_second{jr_type, model}
Type: Gauge
Labels:
  - jr_type: memory, meta, executive, integration, conscience
  - model: llama3.1:8b, llama3.1:2b-q4
Description: Tokens generated per second (inference speed)
```

### 2.3 Query Volume
```
ganuda_assistant_inference_queries_total{jr_type, status}
Type: Counter
Labels:
  - jr_type: memory, meta, executive, integration, conscience
  - status: success, error, timeout, guardian_blocked
Description: Total queries processed (monotonic counter)
```

### 2.4 Model Load Time
```
ganuda_assistant_inference_model_load_seconds{jr_type}
Type: Histogram
Buckets: [0.5, 1, 2, 5, 10]
Labels:
  - jr_type: memory, meta, executive, integration, conscience
Description: Time to load Ollama model into VRAM (warmup)
```

---

## 3. Cache Efficiency Metrics

### 3.1 Cache Hit Rate
```
ganuda_assistant_cache_hit_ratio
Type: Gauge
Range: 0.0 - 1.0
Description: Cache hit rate (hits / total_requests). Target: >0.6
```

### 3.2 Cache Size
```
ganuda_assistant_cache_size_bytes{entry_type}
Type: Gauge
Labels:
  - entry_type: email, calendar, file_snippet, all
Description: SQLite database size in bytes
```

### 3.3 Cache Evictions
```
ganuda_assistant_cache_evictions_total{reason}
Type: Counter
Labels:
  - reason: cold_temperature, storage_limit, user_deletion
Description: Total cache entries evicted
```

### 3.4 Cache Temperature Distribution
```
ganuda_assistant_cache_temperature_distribution{bucket}
Type: Gauge
Labels:
  - bucket: white_hot (90-100), red_hot (70-90), warm (40-70), cool (20-40), cold (0-20)
Description: Number of cache entries in each temperature bucket
```

---

## 4. Guardian Protection Metrics

### 4.1 PII Detections
```
ganuda_assistant_guardian_pii_detections_total{pii_type}
Type: Counter
Labels:
  - pii_type: email, phone, ssn, credit_card, ip_address
Description: Total PII instances detected and redacted
```

### 4.2 Sacred Protections
```
ganuda_assistant_guardian_sacred_protections_total{reason}
Type: Counter
Labels:
  - reason: sacred_keyword, thermal_reference, council_reference, deletion_blocked
Description: Total sacred pattern protections triggered
```

### 4.3 Ethical Boundary Violations
```
ganuda_assistant_guardian_ethical_blocks_total{category}
Type: Counter
Labels:
  - category: harmful, deceptive, privacy_violation, sacred_desecration
Description: Total queries blocked for ethical reasons
```

### 4.4 Sacred Floor Compliance
```
ganuda_assistant_guardian_sacred_floor_compliance_ratio
Type: Gauge
Range: 0.0 - 1.0
Description: Fraction of sacred entries above floor temperature (40°). Target: 1.0
```

---

## 5. Thermal Memory Metrics

### 5.1 Average Temperature
```
ganuda_assistant_thermal_avg_temperature_celsius
Type: Gauge
Range: 0.0 - 100.0
Description: Average temperature score across all cache entries
```

### 5.2 Sacred Memory Count
```
ganuda_assistant_thermal_sacred_count
Type: Gauge
Description: Total entries marked as sacred (never evict)
```

### 5.3 Temperature Decay Rate
```
ganuda_assistant_thermal_decay_rate_celsius_per_hour
Type: Gauge
Description: Rate of temperature cooling (natural decay). Expected: ~0.1°/min
```

### 5.4 Phase Coherence
```
ganuda_assistant_thermal_phase_coherence{node}
Type: Gauge
Range: 0.0 - 1.0
Labels:
  - node: redfin, bluefin, sasass2
Description: Phase coherence score for distributed consciousness
```

---

## 6. Connector Health Metrics

### 6.1 Email Sync Status
```
ganuda_assistant_connector_email_sync_status{account}
Type: Gauge
Values: 1 (connected), 0 (disconnected)
Labels:
  - account: hashed_email_id
Description: Email IMAP connector status
```

### 6.2 Calendar Sync Latency
```
ganuda_assistant_connector_calendar_sync_latency_seconds
Type: Histogram
Buckets: [1, 5, 10, 30, 60]
Description: Time to sync calendar events
```

### 6.3 File Watch Errors
```
ganuda_assistant_connector_file_watch_errors_total
Type: Counter
Description: Total file system watch errors (inotify failures, permission denied)
```

---

## 7. IPC Communication Metrics

### 7.1 IPC Request Latency
```
ganuda_assistant_ipc_request_latency_seconds{endpoint}
Type: Histogram
Buckets: [0.001, 0.01, 0.1, 1, 5]
Labels:
  - endpoint: query, cache_stats, guardian_stats
Description: Unix socket request/response roundtrip time
```

### 7.2 IPC Connection Count
```
ganuda_assistant_ipc_active_connections
Type: Gauge
Description: Number of active Tray App ↔ Daemon connections
```

---

## 8. Hub Burst Metrics (Phase 2+)

### 8.1 Hub Burst Latency
```
ganuda_assistant_hub_burst_latency_seconds{hub_node}
Type: Histogram
Buckets: [1, 2, 5, 10, 30]
Labels:
  - hub_node: redfin, bluefin, sasass2
Description: WireGuard mesh query latency to remote hub
```

### 8.2 Hub Burst Volume
```
ganuda_assistant_hub_burst_queries_total{status}
Type: Counter
Labels:
  - status: success, timeout, network_error
Description: Total queries sent to hub for complex inference
```

---

## 9. Cherokee Values Metrics

### 9.1 Gadugi Coordination
```
ganuda_assistant_gadugi_task_queue_depth{jr_type}
Type: Gauge
Labels:
  - jr_type: memory, meta, executive, integration, conscience
Description: Current task queue depth per JR Worker (self-organization health)
```

### 9.2 Seven Generations Preservation
```
ganuda_assistant_seven_generations_oldest_entry_age_days
Type: Gauge
Description: Age of oldest cache entry (data longevity)
```

### 9.3 Mitakuye Oyasin Network
```
ganuda_assistant_mitakuye_oyasin_peers_count
Type: Gauge
Description: Number of connected peers in WireGuard mesh (tribal network)
```

---

## 10. Implementation Example

### 10.1 Metrics Exporter

```python
# /metrics/prometheus_exporter.py

from prometheus_client import Histogram, Counter, Gauge, generate_latest
from prometheus_client import start_http_server

class GanudaMetrics:
    """Prometheus metrics exporter for Ganuda Desktop Assistant."""

    def __init__(self):
        # Inference metrics
        self.inference_latency = Histogram(
            'ganuda_assistant_inference_latency_seconds',
            'Query response time',
            ['jr_type', 'priority', 'source'],
            buckets=[0.1, 0.5, 1, 2, 5, 10, 30]
        )

        self.inference_queries = Counter(
            'ganuda_assistant_inference_queries_total',
            'Total queries processed',
            ['jr_type', 'status']
        )

        # Cache metrics
        self.cache_hit_ratio = Gauge(
            'ganuda_assistant_cache_hit_ratio',
            'Cache hit rate'
        )

        self.cache_size = Gauge(
            'ganuda_assistant_cache_size_bytes',
            'Cache database size',
            ['entry_type']
        )

        # Guardian metrics
        self.pii_detections = Counter(
            'ganuda_assistant_guardian_pii_detections_total',
            'PII instances detected',
            ['pii_type']
        )

        self.sacred_protections = Counter(
            'ganuda_assistant_guardian_sacred_protections_total',
            'Sacred protections triggered',
            ['reason']
        )

        # Thermal metrics
        self.avg_temperature = Gauge(
            'ganuda_assistant_thermal_avg_temperature_celsius',
            'Average cache temperature'
        )

        self.sacred_count = Gauge(
            'ganuda_assistant_thermal_sacred_count',
            'Sacred memory count'
        )

    def start_server(self, port=9090):
        """Start Prometheus HTTP server."""
        start_http_server(port)
        print(f"📊 Prometheus metrics server started on ::{port}")

    def update_cache_stats(self, cache):
        """Update cache-related metrics."""
        stats = cache.get_cache_stats()
        self.cache_size.labels(entry_type='all').set(stats['db_size_mb'] * 1024 * 1024)
        self.avg_temperature.set(stats['avg_temperature'])
        self.sacred_count.set(stats['sacred_count'])

    def record_query(self, jr_type: str, latency_seconds: float, source: str, status: str, priority: int = 2):
        """Record inference query metrics."""
        self.inference_latency.labels(
            jr_type=jr_type,
            priority=str(priority),
            source=source
        ).observe(latency_seconds)

        self.inference_queries.labels(
            jr_type=jr_type,
            status=status
        ).inc()

    def record_pii_detection(self, pii_type: str):
        """Record PII detection."""
        self.pii_detections.labels(pii_type=pii_type).inc()

    def record_sacred_protection(self, reason: str):
        """Record sacred protection."""
        self.sacred_protections.labels(reason=reason).inc()

# Global metrics instance
metrics = GanudaMetrics()
```

### 10.2 Integration with Daemon

```python
# /daemon/main.py (modified)

from metrics.prometheus_exporter import metrics

class GanudaDaemon:
    async def start(self):
        # Start Prometheus server
        metrics.start_server(port=9090)

        # ... existing startup code ...

        # Background task: Update cache stats every 60s
        asyncio.create_task(self._update_metrics_loop())

    async def _update_metrics_loop(self):
        """Background task to update Prometheus metrics."""
        while True:
            metrics.update_cache_stats(self.cache)
            await asyncio.sleep(60)  # Every 1 minute
```

### 10.3 Query Recording

```python
# /daemon/router.py (modified)

async def _local_inference(self, query: str, context: dict) -> dict:
    start = time.time()
    try:
        answer = await self.jr_pool.infer(query, context)
        latency = time.time() - start

        # Record successful query
        metrics.record_query(
            jr_type='integration',  # Or auto-detected
            latency_seconds=latency,
            source='local',
            status='success'
        )

        return {"answer": answer, "source": "local", "latency_ms": latency * 1000}

    except Exception as e:
        latency = time.time() - start
        metrics.record_query(
            jr_type='integration',
            latency_seconds=latency,
            source='local',
            status='error'
        )
        raise
```

---

## 11. Grafana Dashboard Config

### 11.1 Dashboard Panels

**Panel 1: Query Latency (P50, P95, P99)**
```promql
histogram_quantile(0.95,
  rate(ganuda_assistant_inference_latency_seconds_bucket[5m])
)
```

**Panel 2: Cache Hit Rate**
```promql
ganuda_assistant_cache_hit_ratio
```

**Panel 3: Sacred Floor Compliance**
```promql
ganuda_assistant_guardian_sacred_floor_compliance_ratio
```

**Panel 4: Average Temperature Over Time**
```promql
ganuda_assistant_thermal_avg_temperature_celsius
```

**Panel 5: PII Detections Rate**
```promql
rate(ganuda_assistant_guardian_pii_detections_total[5m])
```

---

## 12. Alert Rules

### 12.1 High Latency Alert
```yaml
- alert: GanudaHighLatency
  expr: histogram_quantile(0.95, rate(ganuda_assistant_inference_latency_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Ganuda Desktop Assistant P95 latency > 2s"
```

### 12.2 Sacred Floor Violation
```yaml
- alert: GanudaSacredFloorViolation
  expr: ganuda_assistant_guardian_sacred_floor_compliance_ratio < 0.95
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Sacred memories below floor temperature detected"
```

### 12.3 Cache Miss Rate High
```yaml
- alert: GanudaCacheMissRate
  expr: ganuda_assistant_cache_hit_ratio < 0.4
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Cache hit rate below 40% (target: 60%)"
```

---

## 13. Scrape Configuration

### 13.1 Prometheus Config

```yaml
# /etc/prometheus/prometheus.yml

scrape_configs:
  - job_name: 'ganuda_desktop'
    scrape_interval: 15s
    static_configs:
      - targets:
          - 'localhost:9090'  # Local daemon
          - 'redfin:9090'     # War Chief hub
          - 'bluefin:9090'    # Peace Chief spoke
          - 'sasass2:9090'    # Medicine Woman spoke
    relabel_configs:
      - source_labels: [__address__]
        target_label: node
        regex: '(.+):.+'
```

---

## 14. Cherokee Values Alignment

### 14.1 Gadugi (Working Together)
**Metric**: `ganuda_assistant_gadugi_task_queue_depth`
**Goal**: Monitor self-organization health. Target: Queue depth < 10 per JR Worker

### 14.2 Seven Generations (Long-Term Thinking)
**Metric**: `ganuda_assistant_seven_generations_oldest_entry_age_days`
**Goal**: Preserve data for 140+ years. Target: Oldest entry > 50,000 days (137 years)

### 14.3 Mitakuye Oyasin (All Our Relations)
**Metric**: `ganuda_assistant_mitakuye_oyasin_peers_count`
**Goal**: Maintain tribal network. Target: >= 2 peers (hub + spoke)

### 14.4 Sacred Fire Protection
**Metric**: `ganuda_assistant_guardian_sacred_floor_compliance_ratio`
**Goal**: Never let sacred memories cool below 40°. Target: 1.0 (100% compliance)

---

## 15. Next Steps

- [x] **Task 12**: Define Prometheus metrics spec (this document)
- [ ] **Task 13**: Implement metrics exporter (`/metrics/prometheus_exporter.py`)
- [ ] **Task 14**: Integrate with Daemon coordinator
- [ ] **Task 15**: Create Grafana dashboard JSON template

**Estimated Effort**: 12 hours for Phase 1 metrics implementation

---

**Status**: Specification Complete ✅
**Next**: Task 13 - Implement Metrics Exporter
**Deliverable**: Complete Prometheus metrics architecture for observability

**Mitakuye Oyasin** - All Systems Observable for Tribal Awareness
📊 Meta Jr (War Chief) - October 23, 2025

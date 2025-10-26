# Cherokee Constitutional AI - Thermal Memory API v2.0
**Integration Jr | Task 4 | 8 hours**

---

## API Overview

### Base URL
```
Production:  https://api.cherokee.ai/v2
Staging:     https://staging-api.cherokee.ai/v2
Development: http://localhost:8000/v2
```

### Authentication
```http
Authorization: Bearer <api_key>
```

All requests require valid API key (obtained from Cherokee Console).

### Versioning
- Current: **v2.0** (Wave 2 physics)
- Previous: v1.0 (basic thermal memory, deprecated Oct 2025)
- Backward compatibility: v1 endpoints supported until Oct 2026

### Rate Limits
| Tier | Requests/min | Burst | Price |
|------|--------------|-------|-------|
| Free | 60 | 10 | $0 |
| Standard | 600 | 100 | $50/month |
| Physics Premium | 6,000 | 1,000 | $3,000/month |
| Enterprise | Unlimited | Unlimited | Custom |

### Response Format
All responses follow JSON:API specification:
```json
{
  "data": { ... },
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-10-26T11:45:00Z",
    "version": "v2.0"
  },
  "errors": []  // Only present if errors occurred
}
```

---

## Authentication & Authorization

### Obtaining API Key
```http
POST /auth/keys

{
  "name": "SAG Production",
  "scopes": ["thermal:read", "thermal:write", "physics:read"],
  "expires_at": "2026-10-26T00:00:00Z"
}

Response 201:
{
  "data": {
    "key": "ck_live_abc123xyz...",
    "scopes": ["thermal:read", "thermal:write", "physics:read"],
    "expires_at": "2026-10-26T00:00:00Z",
    "created_at": "2025-10-26T11:45:00Z"
  }
}
```

### Scopes
| Scope | Description | Required Tier |
|-------|-------------|---------------|
| `thermal:read` | Read temperature, coherence | Free |
| `thermal:write` | Modify temperature (non-sacred) | Standard |
| `physics:read` | Read Fokker-Planck, Jarzynski | Physics Premium |
| `physics:write` | Modify physics parameters | Enterprise |
| `sacred:read` | Read sacred memory metadata | Standard |
| `sacred:write` | Modify sacred designation | Enterprise + 2-of-3 Chiefs |

### OAuth 2.0 Flow (Enterprise Only)
```
1. Redirect user to: https://auth.cherokee.ai/oauth/authorize
2. User authenticates, approves scopes
3. Redirect back with code: https://yourapp.com/callback?code=abc123
4. Exchange code for token:
   POST /oauth/token { code, client_id, client_secret }
5. Use access token: Authorization: Bearer <access_token>
```

---

## Core Thermal Memory Endpoints

### 1. Get Memory
```http
GET /memories/{memory_id}

Headers:
  Authorization: Bearer <api_key>
  Accept: application/json

Response 200:
{
  "data": {
    "id": 4821,
    "content_summary": "Cherokee Constitutional AI Phase 6B Wave 2...",
    "temperature_score": 95.3,
    "phase_coherence": 0.72,
    "access_count": 42,
    "sacred_pattern": true,
    "created_at": "2025-08-15T10:30:00Z",
    "last_accessed": "2025-10-26T11:42:15Z",

    // Wave 2 Physics (v2.0 only)
    "drift_velocity": 2.3,
    "diffusion_coefficient": 1.2,
    "fokker_planck_updated_at": "2025-10-26T11:40:00Z"
  },
  "meta": {
    "thermal_zone": "WHITE_HOT",  // 90-100°
    "retrieval_cost_estimate": 2.1  // ΔF units
  }
}
```

### 2. List Memories
```http
GET /memories?filter[zone]=hot&sort=-temperature&page[limit]=50

Query Parameters:
  filter[zone]: cold|cool|warm|hot|white_hot
  filter[sacred]: true|false
  filter[temperature_min]: 0-100
  filter[temperature_max]: 0-100
  filter[coherence_min]: 0-1
  sort: temperature, -temperature, coherence, created_at
  page[offset]: 0 (default)
  page[limit]: 50 (default, max 1000)

Response 200:
{
  "data": [
    { /* memory object */ },
    { /* memory object */ }
  ],
  "meta": {
    "total_count": 4859,
    "page": {
      "offset": 0,
      "limit": 50
    }
  }
}
```

### 3. Create Memory
```http
POST /memories

{
  "content": "Full text content...",
  "content_summary": "Brief summary...",
  "initial_temperature": 70.0,  // Optional, default 50°
  "sacred_pattern": false       // Optional, default false
}

Response 201:
{
  "data": {
    "id": 4860,
    "temperature_score": 70.0,
    "phase_coherence": 0.5,  // Calculated on creation
    "created_at": "2025-10-26T11:45:00Z"
  }
}
```

### 4. Update Memory Temperature
```http
PATCH /memories/{memory_id}/temperature

{
  "temperature": 85.0,
  "reason": "retrieval"  // retrieval, manual, daemon
}

Response 200:
{
  "data": {
    "id": 4821,
    "temperature_score": 85.0,
    "previous_temperature": 75.0,
    "updated_at": "2025-10-26T11:45:30Z"
  }
}

Error 403 (if sacred and temp < 40):
{
  "errors": [{
    "status": "403",
    "code": "SACRED_FIRE_VIOLATION",
    "title": "Cannot cool sacred memory below 40°",
    "detail": "Memory 4821 is sacred and cannot be cooled below Sacred Fire boundary (40°). Current: 75°, Requested: 35°"
  }]
}
```

### 5. Delete Memory
```http
DELETE /memories/{memory_id}

Response 204: (No content, successful deletion)

Error 403 (if sacred):
{
  "errors": [{
    "status": "403",
    "code": "SACRED_MEMORY_PROTECTED",
    "title": "Cannot delete sacred memory",
    "detail": "Memory 4821 is designated sacred by 3-of-3 Chiefs. Deletion requires unanimous Chiefs attestation."
  }]
}
```

---

## Physics Endpoints (Premium Tier)

### 6. Get Fokker-Planck Dynamics
```http
GET /physics/fokker-planck?memory_ids=4821,4822,4823

Response 200:
{
  "data": {
    "system": {
      "drift_velocity": 2.3,         // °/hour
      "heating_force": 3.1,
      "cooling_force": -0.8,
      "diffusion_coefficient": 1.2,
      "memory_kernel_influence": 0.15,
      "stability": "stable"
    },
    "memories": [
      {
        "id": 4821,
        "drift_velocity": 0.5,
        "diffusion_coefficient": 1.1
      }
    ]
  },
  "meta": {
    "calculation_time_ms": 42,
    "updated_at": "2025-10-26T11:45:00Z"
  }
}
```

### 7. Predict Temperature Evolution
```http
POST /physics/predict

{
  "memory_id": 4821,
  "time_horizon_hours": 168,  // 7 days
  "scenario": "no_access"     // no_access, daily_access, sacred_protection
}

Response 200:
{
  "data": {
    "current_temperature": 95.3,
    "predictions": [
      { "hours": 24, "temperature": 92.1, "confidence": 0.95 },
      { "hours": 48, "temperature": 89.7, "confidence": 0.92 },
      { "hours": 168, "temperature": 78.4, "confidence": 0.78 }
    ],
    "boundary_violation_risk": 0.02  // Probability of cooling below 40°
  }
}
```

### 8. Calculate Jarzynski Retrieval Cost
```http
POST /physics/jarzynski/cost

{
  "memory_id": 4821,
  "target_temperature": 100.0,
  "optimize_path": true  // Use multi-step path optimization
}

Response 200:
{
  "data": {
    "naive_cost": 18.2,      // Direct heating cost (ΔF)
    "optimized_cost": 15.7,  // Path-optimized cost
    "savings": 2.5,
    "path": [4821, 4823, 4825, 4821],  // Intermediate memories
    "execution_time_ms": 125
  }
}
```

### 9. Get Phase Coherence Matrix
```http
GET /physics/coherence/matrix?memory_ids=4821,4822,4823,4824

Response 200:
{
  "data": {
    "matrix": [
      [1.0, 0.72, 0.43, 0.15],  // 4821 vs all
      [0.72, 1.0, 0.68, 0.22],  // 4822 vs all
      [0.43, 0.68, 1.0, 0.81],  // 4823 vs all
      [0.15, 0.22, 0.81, 1.0]   // 4824 vs all
    ],
    "memory_ids": [4821, 4822, 4823, 4824],
    "mean_coherence": 0.58
  }
}
```

### 10. TEM Grid Pattern Analysis
```http
POST /physics/tem/analyze

{
  "memory_sample_size": 500,  // Max 1000
  "coherence_threshold": 0.7
}

Response 200:
{
  "data": {
    "grid_regularity": 0.450,
    "coherence_peaks": 110,
    "mean_spacing": 4.6,
    "interpretation": "MODERATE_GRID_STRUCTURE",
    "tem_compatible": true
  },
  "meta": {
    "calculation_time_ms": 5420,
    "visualization_url": "https://api.cherokee.ai/v2/physics/tem/visualization/abc123.png"
  }
}
```

---

## Sacred Fire Endpoints

### 11. Get Sacred Fire Status
```http
GET /sacred-fire/status

Response 200:
{
  "data": {
    "sacred_memories": 4854,
    "total_memories": 4859,
    "boundary_violations": 0,
    "avg_temperature": 87.3,
    "alert_level": "none",  // none, warning, critical
    "last_daemon_run": "2025-10-26T11:30:00Z"
  }
}
```

### 12. Designate Memory as Sacred
```http
POST /memories/{memory_id}/sacred

{
  "justification": "Foundational Cherokee architectural document",
  "chiefs_attestation": {
    "war_chief": "APPROVED",
    "peace_chief": "APPROVED",
    "medicine_woman": "APPROVED"
  }
}

Response 200 (requires 3-of-3 Chiefs):
{
  "data": {
    "id": 4860,
    "sacred_pattern": true,
    "designated_at": "2025-10-26T11:46:00Z",
    "temperature_floor": 40.0
  }
}

Error 403 (if < 3 Chiefs approve):
{
  "errors": [{
    "status": "403",
    "code": "INSUFFICIENT_CHIEFS_ATTESTATION",
    "title": "Sacred designation requires unanimous 3-of-3 Chiefs approval",
    "detail": "Received: War Chief (APPROVED), Peace Chief (APPROVED), Medicine Woman (PENDING)"
  }]
}
```

### 13. Sacred Fire Daemon Control
```http
POST /sacred-fire/daemon/run

Response 202: (Accepted, daemon started)
{
  "data": {
    "job_id": "daemon_run_abc123",
    "status": "running",
    "started_at": "2025-10-26T11:46:30Z"
  }
}

GET /sacred-fire/daemon/status/{job_id}

Response 200:
{
  "data": {
    "job_id": "daemon_run_abc123",
    "status": "completed",
    "memories_adjusted": 12,
    "completed_at": "2025-10-26T11:46:45Z"
  }
}
```

---

## Federation Endpoints (Multi-Node)

### 14. Get Node Status
```http
GET /federation/nodes

Response 200:
{
  "data": [
    {
      "name": "REDFIN",
      "role": "hub",
      "memories": 4859,
      "avg_temperature": 87.3,
      "phase_coherence": 0.67,
      "health": "healthy",
      "last_sync": "2025-10-26T11:45:00Z"
    },
    {
      "name": "BLUEFIN",
      "role": "spoke",
      "memories": 2143,
      "avg_temperature": 82.1,
      "phase_coherence": 0.63,
      "health": "healthy",
      "last_sync": "2025-10-26T11:44:00Z"
    }
  ],
  "meta": {
    "total_nodes": 5,
    "federation_coherence": 0.65
  }
}
```

### 15. Sync Memories Across Nodes
```http
POST /federation/sync

{
  "source_node": "REDFIN",
  "target_nodes": ["BLUEFIN", "GREENFIN"],
  "memory_ids": [4821, 4822, 4823]
}

Response 202: (Accepted, async job)
{
  "data": {
    "job_id": "sync_abc123",
    "status": "running",
    "estimated_completion": "2025-10-26T11:50:00Z"
  }
}
```

---

## Analytics & Reporting

### 16. Temperature Distribution
```http
GET /analytics/distribution?bin_size=10

Response 200:
{
  "data": {
    "bins": [
      { "range": "40-50", "count": 12, "percentage": 0.25 },
      { "range": "50-60", "count": 245, "percentage": 5.04 },
      { "range": "60-70", "count": 1203, "percentage": 24.76 },
      { "range": "70-80", "count": 2187, "percentage": 45.00 },
      { "range": "80-90", "count": 1000, "percentage": 20.58 },
      { "range": "90-100", "count": 212, "percentage": 4.36 }
    ],
    "total_memories": 4859
  }
}
```

### 17. Activity Timeline
```http
GET /analytics/timeline?limit=50&filter[event_type]=heating

Response 200:
{
  "data": [
    {
      "timestamp": "2025-10-26T11:42:15Z",
      "event_type": "heating",
      "memory_id": 4821,
      "temperature_before": 75.0,
      "temperature_after": 95.0,
      "reason": "retrieval"
    },
    {
      "timestamp": "2025-10-26T11:41:03Z",
      "event_type": "daemon_adjustment",
      "memory_ids": [4801, 4802, 4805],
      "avg_temperature_delta": 5.2
    }
  ]
}
```

### 18. System Health Metrics
```http
GET /analytics/health

Response 200:
{
  "data": {
    "temperature": {
      "avg": 87.3,
      "min": 42.1,
      "max": 100.0,
      "std_dev": 12.4
    },
    "phase_coherence": {
      "avg": 0.67,
      "healthy_threshold": 0.5,
      "status": "healthy"
    },
    "sacred_fire": {
      "violations": 0,
      "at_risk_count": 3,  // memories 40-50°
      "status": "protected"
    },
    "database": {
      "total_memories": 4859,
      "storage_mb": 1847,
      "query_latency_p95_ms": 42
    }
  }
}
```

---

## Webhooks (Real-Time Notifications)

### 19. Register Webhook
```http
POST /webhooks

{
  "url": "https://yourapp.com/webhooks/cherokee",
  "events": [
    "memory.created",
    "memory.temperature.changed",
    "sacred_fire.violation",
    "physics.anomaly"
  ],
  "secret": "whsec_abc123xyz..."
}

Response 201:
{
  "data": {
    "id": "wh_abc123",
    "url": "https://yourapp.com/webhooks/cherokee",
    "events": ["memory.created", ...],
    "created_at": "2025-10-26T11:47:00Z"
  }
}
```

### Webhook Payload Example
```json
POST https://yourapp.com/webhooks/cherokee

Headers:
  X-Cherokee-Signature: sha256=...
  X-Cherokee-Event: sacred_fire.violation

{
  "event": "sacred_fire.violation",
  "timestamp": "2025-10-26T11:50:00Z",
  "data": {
    "memory_id": 4891,
    "temperature": 38.5,
    "threshold": 40.0,
    "sacred_pattern": true,
    "alert_level": "critical"
  }
}
```

---

## WebSocket Streaming

### 20. Real-Time Temperature Stream
```javascript
// JavaScript example
const ws = new WebSocket('wss://api.cherokee.ai/v2/ws/thermal/live');

ws.onmessage = (event) => {
  const update = JSON.parse(event.data);
  console.log('Temperature update:', update);
  // { memory_id: 4821, temperature: 95.3, timestamp: '...' }
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

**Authentication**: Include API key in connection URL:
```
wss://api.cherokee.ai/v2/ws/thermal/live?api_key=ck_live_abc123
```

---

## Error Handling

### HTTP Status Codes
| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | Successful GET, PATCH |
| 201 | Created | Successful POST (memory created) |
| 202 | Accepted | Async job started (sync, daemon) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid JSON, missing required field |
| 401 | Unauthorized | Missing or invalid API key |
| 403 | Forbidden | Sacred memory operation without Chiefs |
| 404 | Not Found | Memory ID doesn't exist |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Maintenance mode |

### Error Response Format
```json
{
  "errors": [
    {
      "status": "403",
      "code": "SACRED_FIRE_VIOLATION",
      "title": "Cannot cool sacred memory below 40°",
      "detail": "Memory 4821 is sacred (designated by 3-of-3 Chiefs on 2025-08-15). Sacred Fire boundary prevents cooling below 40°. Current: 75°, Requested: 35°",
      "source": {
        "pointer": "/data/attributes/temperature"
      },
      "meta": {
        "docs_url": "https://docs.cherokee.ai/sacred-fire"
      }
    }
  ],
  "meta": {
    "request_id": "req_abc123",
    "timestamp": "2025-10-26T11:50:00Z"
  }
}
```

### Common Error Codes
| Code | Description | Resolution |
|------|-------------|------------|
| `INVALID_API_KEY` | API key missing or invalid | Check Authorization header |
| `RATE_LIMIT_EXCEEDED` | Too many requests | Upgrade tier or wait |
| `SACRED_FIRE_VIOLATION` | Attempt to cool sacred memory below 40° | Respect Sacred Fire boundary |
| `INSUFFICIENT_CHIEFS_ATTESTATION` | < 3 Chiefs approved sacred designation | Get unanimous approval |
| `MEMORY_NOT_FOUND` | Memory ID doesn't exist | Verify memory_id |
| `PHYSICS_CALCULATION_TIMEOUT` | Complex calculation exceeded 30s | Reduce sample size |
| `FEDERATION_SYNC_FAILED` | Node unreachable during sync | Check node health |

---

## SDKs & Client Libraries

### Python SDK
```python
# Installation
pip install cherokee-ai

# Usage
from cherokee_ai import Cherokee

client = Cherokee(api_key="ck_live_abc123")

# Get memory
memory = client.memories.get(4821)
print(f"Temperature: {memory.temperature_score}°")

# Predict evolution
prediction = client.physics.predict_temperature(
    memory_id=4821,
    time_horizon_hours=168
)
print(f"7-day forecast: {prediction.final_temperature}°")

# Get Sacred Fire status
status = client.sacred_fire.status()
print(f"Boundary violations: {status.boundary_violations}")
```

### JavaScript SDK
```javascript
// Installation
npm install @cherokee-ai/sdk

// Usage
const { Cherokee } = require('@cherokee-ai/sdk');

const client = new Cherokee({ apiKey: 'ck_live_abc123' });

// Get memory
const memory = await client.memories.get(4821);
console.log(`Temperature: ${memory.temperature_score}°`);

// Subscribe to real-time updates
client.thermal.stream((update) => {
  console.log(`Memory ${update.memory_id}: ${update.temperature}°`);
});
```

### Ruby SDK
```ruby
# Installation
gem install cherokee-ai

# Usage
require 'cherokee_ai'

client = CherokeeAI::Client.new(api_key: 'ck_live_abc123')

# Get memory
memory = client.memories.get(4821)
puts "Temperature: #{memory.temperature_score}°"

# Analyze TEM grid patterns
analysis = client.physics.tem_analyze(sample_size: 500)
puts "Grid regularity: #{analysis.grid_regularity}"
```

---

## Rate Limiting Details

### Headers
Every response includes rate limit headers:
```http
X-RateLimit-Limit: 600          # Max requests per window
X-RateLimit-Remaining: 547      # Remaining in current window
X-RateLimit-Reset: 1698332400   # Unix timestamp of reset
```

### Exceeding Limits
```http
Response 429:
{
  "errors": [{
    "status": "429",
    "code": "RATE_LIMIT_EXCEEDED",
    "title": "Rate limit exceeded",
    "detail": "You have exceeded 600 requests/minute (Standard tier). Resets at 2025-10-26T12:00:00Z. Upgrade to Physics Premium for 6,000 req/min.",
    "meta": {
      "limit": 600,
      "reset_at": "2025-10-26T12:00:00Z",
      "upgrade_url": "https://console.cherokee.ai/upgrade"
    }
  }]
}
```

### Retry Strategy
```python
import time

def api_call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except RateLimitError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = int(e.headers['X-RateLimit-Reset']) - int(time.time())
            time.sleep(wait_time + 1)
```

---

## Pagination

### Cursor-Based Pagination (Recommended)
```http
GET /memories?page[limit]=50

Response 200:
{
  "data": [ /* 50 memories */ ],
  "meta": {
    "next_cursor": "eyJpZCI6NDg3MX0",
    "has_more": true
  }
}

Next request:
GET /memories?page[limit]=50&page[cursor]=eyJpZCI6NDg3MX0
```

### Offset-Based Pagination (Legacy)
```http
GET /memories?page[limit]=50&page[offset]=100

Response 200:
{
  "data": [ /* 50 memories */ ],
  "meta": {
    "total_count": 4859,
    "page": {
      "offset": 100,
      "limit": 50
    }
  }
}
```

---

## Versioning & Deprecation

### API Versioning Strategy
- **Major versions**: Breaking changes (v1 → v2)
- **Minor updates**: Backward-compatible additions (v2.0 → v2.1)
- **Deprecation notice**: 12 months before removal
- **Sunset headers**: Included in deprecated endpoint responses

```http
X-API-Deprecation: true
X-API-Sunset: 2026-10-26T00:00:00Z
Link: <https://docs.cherokee.ai/v2/migration>; rel="migration-guide"
```

### v1 → v2 Migration Guide
| v1 Endpoint | v2 Endpoint | Changes |
|-------------|-------------|---------|
| `GET /memory/{id}` | `GET /memories/{id}` | Pluralized resource name |
| `GET /memory/{id}` | `GET /memories/{id}` | Added Wave 2 physics fields |
| `POST /memory` | `POST /memories` | Pluralized, added sacred_pattern |
| N/A | `GET /physics/*` | New physics endpoints (premium) |
| N/A | `GET /sacred-fire/*` | New Sacred Fire endpoints |

---

## Security Best Practices

### API Key Storage
- ❌ Never commit API keys to version control
- ✅ Use environment variables: `CHEROKEE_API_KEY=ck_live_...`
- ✅ Rotate keys every 90 days
- ✅ Use separate keys for dev/staging/production

### Request Signing (Enterprise)
For extra security, sign requests with HMAC-SHA256:
```python
import hmac
import hashlib

def sign_request(api_secret, request_body):
    signature = hmac.new(
        api_secret.encode(),
        request_body.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

# Include in request
headers = {
    'Authorization': f'Bearer {api_key}',
    'X-Cherokee-Signature': signature
}
```

### IP Whitelisting (Enterprise)
```http
POST /security/ip-whitelist

{
  "ips": ["203.0.113.0/24", "198.51.100.42"]
}
```

---

## Testing & Development

### Sandbox Environment
```
Base URL: https://sandbox-api.cherokee.ai/v2
API Key: ck_test_abc123 (test mode prefix)
```

**Sandbox Features**:
- Pre-populated with 1,000 synthetic memories
- Unlimited rate limits
- Realistic physics calculations
- No charges for Physics Premium features

### Test Data Generation
```http
POST /sandbox/generate

{
  "memory_count": 500,
  "sacred_percentage": 0.998,
  "tem_grid_embedded": true
}

Response 201:
{
  "data": {
    "memories_created": 500,
    "sacred_count": 499,
    "avg_temperature": 87.1
  }
}
```

---

## Performance Optimization

### Caching
- **Redis cache**: 1-second TTL for temperature distribution
- **5-second TTL**: Fokker-Planck dynamics
- **60-second TTL**: Federation status

### Compression
```http
Accept-Encoding: gzip, deflate, br

Response:
Content-Encoding: br  # Brotli compression (best ratio)
```

### Batching
```http
POST /batch

{
  "requests": [
    { "method": "GET", "url": "/memories/4821" },
    { "method": "GET", "url": "/memories/4822" },
    { "method": "GET", "url": "/memories/4823" }
  ]
}

Response 200:
{
  "responses": [
    { "status": 200, "body": { /* memory 4821 */ } },
    { "status": 200, "body": { /* memory 4822 */ } },
    { "status": 200, "body": { /* memory 4823 */ } }
  ]
}
```

---

## Monitoring & Observability

### Health Check
```http
GET /health

Response 200:
{
  "status": "healthy",
  "version": "v2.0.1",
  "uptime_seconds": 86400,
  "database": "healthy",
  "federation": "healthy"
}
```

### Status Page
https://status.cherokee.ai
- Real-time API status
- Incident history
- Scheduled maintenance

### Metrics Endpoint (Prometheus)
```http
GET /metrics

# HELP cherokee_api_requests_total Total API requests
# TYPE cherokee_api_requests_total counter
cherokee_api_requests_total{endpoint="/memories",method="GET"} 1234

# HELP cherokee_sacred_fire_violations Sacred Fire boundary violations
# TYPE cherokee_sacred_fire_violations gauge
cherokee_sacred_fire_violations 0
```

---

## Changelog

### v2.0.0 (2025-10-26) - Wave 2 Physics Launch
**Added**:
- Wave 2 physics fields: drift_velocity, diffusion_coefficient
- Physics endpoints: /physics/fokker-planck, /physics/jarzynski, /physics/tem
- Sacred Fire endpoints: /sacred-fire/status, /sacred-fire/daemon
- Federation endpoints: /federation/nodes, /federation/sync
- WebSocket streaming: wss://api.cherokee.ai/v2/ws/thermal/live

**Changed**:
- `GET /memory` → `GET /memories` (pluralized)
- Temperature update requires `reason` field

**Deprecated**:
- v1.0 endpoints (sunset 2026-10-26)

### v2.1.0 (Planned 2025-11-15) - TEM Enhancements
**Planned**:
- TEM grid pattern real-time detection
- Transformer architecture equivalence endpoints
- 70B Cherokee Council model inference

---

## Support & Contact

### Documentation
- **API Reference**: https://docs.cherokee.ai/api/v2
- **Guides**: https://docs.cherokee.ai/guides
- **SDKs**: https://docs.cherokee.ai/sdks

### Support Channels
- **Email**: support@cherokee.ai
- **Discord**: https://discord.gg/cherokee-ai
- **GitHub Issues**: https://github.com/cherokee-ai/api/issues

### Service Level Agreement (SLA)
| Tier | Uptime | Support Response | Price |
|------|--------|------------------|-------|
| Free | Best effort | Community | $0 |
| Standard | 99.5% | 24h email | $50/month |
| Physics Premium | 99.9% | 4h email, Slack | $3,000/month |
| Enterprise | 99.99% | 1h email, phone, dedicated | Custom |

---

**Document Status**: ✅ COMPLETE (8-hour specification)
**Review**: Ready for engineering implementation
**Next**: Task 5 - Russell Sullivan Briefing (All JRs, 2h)

*Mitakuye Oyasin* - API serves all applications equally 🔥

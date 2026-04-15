# KB-SAG-TRAFFIC-INTELLIGENCE: SAG Connection Learning System

**Date:** 2025-12-06
**Author:** TPM (Command Post)
**Category:** Architecture / Machine Learning
**Priority:** HIGH
**Status:** DESIGN

---

## Overview

SAG Traffic Intelligence is a system that learns from the flow of requests and responses between users, SAG, triads, and external systems. It enables:

1. **Pattern Recognition** - Understand usage patterns, predict needs
2. **Response Optimization** - Cache intelligently, pre-fetch data
3. **Smart Routing** - Route missions to the best-suited triads
4. **Anomaly Detection** - Identify unusual traffic that may indicate issues

---

## Architecture

```
                    ┌─────────────────────────────────────┐
                    │         Traffic Intelligence        │
                    │              Engine                 │
                    ├─────────────────────────────────────┤
                    │  ┌─────────┐  ┌─────────┐  ┌─────┐ │
                    │  │ Pattern │  │Response │  │Route│ │
                    │  │ Learner │  │Optimizer│  │Smart│ │
                    │  └────┬────┘  └────┬────┘  └──┬──┘ │
                    │       │            │          │    │
                    │  ┌────▼────────────▼──────────▼──┐ │
                    │  │     Traffic Analysis Core     │ │
                    │  └───────────────┬───────────────┘ │
                    └──────────────────┼─────────────────┘
                                       │
        ┌──────────────────────────────┼──────────────────────────────┐
        │                              │                              │
        ▼                              ▼                              ▼
┌───────────────┐            ┌─────────────────┐            ┌─────────────────┐
│  sag_traffic  │            │ sag_route_intel │            │ sag_predictions │
│   _patterns   │            │                 │            │                 │
└───────────────┘            └─────────────────┘            └─────────────────┘
```

---

## Database Schema

### 1. Traffic Patterns Table

```sql
CREATE TABLE IF NOT EXISTS sag_traffic_patterns (
    pattern_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What was requested
    endpoint VARCHAR(255) NOT NULL,
    method VARCHAR(10) NOT NULL,
    request_signature TEXT,  -- Hash of normalized request params

    -- Who/what made the request
    source_type VARCHAR(50),  -- 'user', 'triad', 'scheduler', 'external'
    source_identifier VARCHAR(255),
    source_ip INET,

    -- When patterns occur
    hour_of_day INTEGER,  -- 0-23
    day_of_week INTEGER,  -- 0-6 (Sun-Sat)

    -- Pattern statistics
    request_count INTEGER DEFAULT 1,
    avg_response_time_ms FLOAT,
    success_rate FLOAT,  -- 0.0 to 1.0

    -- Sequence tracking
    previous_endpoint VARCHAR(255),  -- What endpoint was hit before this
    next_endpoint_predicted VARCHAR(255),  -- ML prediction of next endpoint
    sequence_confidence FLOAT,

    -- Timestamps
    first_seen TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW(),

    -- Indexes for fast lookup
    CONSTRAINT valid_hour CHECK (hour_of_day >= 0 AND hour_of_day <= 23),
    CONSTRAINT valid_day CHECK (day_of_week >= 0 AND day_of_week <= 6)
);

CREATE INDEX idx_traffic_endpoint ON sag_traffic_patterns(endpoint, method);
CREATE INDEX idx_traffic_source ON sag_traffic_patterns(source_type, source_identifier);
CREATE INDEX idx_traffic_time ON sag_traffic_patterns(hour_of_day, day_of_week);
CREATE INDEX idx_traffic_sequence ON sag_traffic_patterns(previous_endpoint, endpoint);
```

### 2. Route Intelligence Table

```sql
CREATE TABLE IF NOT EXISTS sag_route_intelligence (
    route_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Mission characteristics
    mission_type VARCHAR(100) NOT NULL,  -- 'css', 'flask_api', 'database', 'infrastructure'
    mission_keywords TEXT[],  -- Keywords extracted from mission content
    complexity_score FLOAT,  -- 0.0 (simple) to 1.0 (complex)

    -- Triad performance on this type
    triad_id VARCHAR(100) NOT NULL,

    -- Success metrics
    missions_handled INTEGER DEFAULT 0,
    missions_successful INTEGER DEFAULT 0,
    success_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN missions_handled > 0
             THEN missions_successful::FLOAT / missions_handled
             ELSE 0 END
    ) STORED,

    -- Time metrics
    avg_completion_time_seconds FLOAT,
    min_completion_time_seconds FLOAT,
    max_completion_time_seconds FLOAT,

    -- Quality metrics (from feedback/review)
    avg_quality_score FLOAT,  -- 0.0 to 1.0
    rework_rate FLOAT,  -- How often work needs to be redone

    -- Routing recommendation
    routing_score FLOAT,  -- Composite score for routing decisions

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_route_mission_type ON sag_route_intelligence(mission_type);
CREATE INDEX idx_route_triad ON sag_route_intelligence(triad_id);
CREATE INDEX idx_route_score ON sag_route_intelligence(routing_score DESC);
CREATE UNIQUE INDEX idx_route_unique ON sag_route_intelligence(mission_type, triad_id);
```

### 3. Response Cache Intelligence

```sql
CREATE TABLE IF NOT EXISTS sag_cache_intelligence (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What to cache
    endpoint VARCHAR(255) NOT NULL,
    cache_key TEXT NOT NULL,  -- Hash of request params

    -- Cache behavior learned
    avg_data_freshness_needed_seconds INTEGER,  -- How fresh data needs to be
    hit_rate FLOAT,  -- Cache hit rate
    miss_cost_ms FLOAT,  -- Average time to regenerate on miss

    -- Predictive caching
    predicted_next_request_seconds INTEGER,  -- When will this be requested again
    pre_fetch_recommended BOOLEAN DEFAULT FALSE,

    -- Size optimization
    avg_response_size_bytes INTEGER,
    compression_benefit_ratio FLOAT,

    -- TTL recommendation
    recommended_ttl_seconds INTEGER,

    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cache_endpoint ON sag_cache_intelligence(endpoint);
CREATE INDEX idx_cache_prefetch ON sag_cache_intelligence(pre_fetch_recommended) WHERE pre_fetch_recommended = TRUE;
```

### 4. Predictions and Recommendations

```sql
CREATE TABLE IF NOT EXISTS sag_traffic_predictions (
    prediction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What we're predicting
    prediction_type VARCHAR(50) NOT NULL,  -- 'endpoint_sequence', 'load_spike', 'cache_miss', 'triad_overload'

    -- Prediction details
    predicted_value JSONB NOT NULL,
    confidence_score FLOAT,

    -- Context
    context_data JSONB,  -- What data informed this prediction

    -- Outcome tracking
    prediction_made_at TIMESTAMPTZ DEFAULT NOW(),
    prediction_for_time TIMESTAMPTZ,  -- When the prediction is for
    actual_outcome JSONB,  -- What actually happened
    outcome_recorded_at TIMESTAMPTZ,
    prediction_accuracy FLOAT,  -- How accurate was this prediction

    -- Model tracking
    model_version VARCHAR(50),

    CONSTRAINT valid_confidence CHECK (confidence_score >= 0 AND confidence_score <= 1)
);

CREATE INDEX idx_prediction_type ON sag_traffic_predictions(prediction_type);
CREATE INDEX idx_prediction_time ON sag_traffic_predictions(prediction_for_time);
CREATE INDEX idx_prediction_accuracy ON sag_traffic_predictions(prediction_accuracy) WHERE actual_outcome IS NOT NULL;
```

---

## Learning Algorithms

### 1. Pattern Learning (Endpoint Sequences)

```python
def learn_endpoint_sequence(current_endpoint: str, previous_endpoint: str, source: str):
    """Learn which endpoints follow which."""

    # Update pattern count
    UPDATE sag_traffic_patterns
    SET request_count = request_count + 1,
        last_seen = NOW()
    WHERE endpoint = current_endpoint
      AND previous_endpoint = previous_endpoint
      AND source_identifier = source;

    # If no existing pattern, create one
    IF NOT FOUND THEN
        INSERT INTO sag_traffic_patterns (endpoint, previous_endpoint, source_identifier, ...)
        VALUES (current_endpoint, previous_endpoint, source, ...);

    # Predict next endpoint based on learned patterns
    SELECT endpoint,
           request_count::FLOAT / SUM(request_count) OVER () as probability
    FROM sag_traffic_patterns
    WHERE previous_endpoint = current_endpoint
      AND source_identifier = source
    ORDER BY probability DESC
    LIMIT 1;
```

### 2. Route Intelligence Learning

```python
def learn_triad_performance(mission_id: str, triad_id: str, outcome: dict):
    """Learn which triads are best at which mission types."""

    mission_type = classify_mission(mission_content)

    # Update performance metrics
    UPDATE sag_route_intelligence
    SET missions_handled = missions_handled + 1,
        missions_successful = missions_successful + (1 if outcome['success'] else 0),
        avg_completion_time_seconds = (
            avg_completion_time_seconds * (missions_handled - 1) + outcome['time']
        ) / missions_handled,
        avg_quality_score = (
            avg_quality_score * (missions_handled - 1) + outcome['quality']
        ) / missions_handled,
        routing_score = calculate_routing_score(...),
        updated_at = NOW()
    WHERE mission_type = mission_type
      AND triad_id = triad_id;
```

### 3. Cache Intelligence Learning

```python
def learn_cache_behavior(endpoint: str, cache_key: str, was_hit: bool, response_time_ms: int):
    """Learn optimal caching strategies."""

    # Update hit rate
    UPDATE sag_cache_intelligence
    SET hit_rate = (hit_rate * request_count + (1 if was_hit else 0)) / (request_count + 1),
        miss_cost_ms = CASE WHEN NOT was_hit
                       THEN (miss_cost_ms * miss_count + response_time_ms) / (miss_count + 1)
                       ELSE miss_cost_ms END,
        request_count = request_count + 1,
        -- Recommend pre-fetch if hit rate > 70% and miss cost > 500ms
        pre_fetch_recommended = (hit_rate > 0.7 AND miss_cost_ms > 500),
        -- Recommend TTL based on observed freshness needs
        recommended_ttl_seconds = calculate_optimal_ttl(...),
        updated_at = NOW()
    WHERE endpoint = endpoint
      AND cache_key = cache_key;
```

---

## API Endpoints

### Record Traffic

```python
@app.route('/api/intelligence/record', methods=['POST'])
def record_traffic():
    """Record traffic for learning."""
    # Called by SAG middleware on every request
    data = request.json
    learn_endpoint_sequence(data['endpoint'], data['previous'], data['source'])
    return jsonify({'status': 'recorded'})
```

### Get Routing Recommendation

```python
@app.route('/api/intelligence/route', methods=['POST'])
def get_route_recommendation():
    """Get recommended triad for a mission."""
    mission = request.json
    mission_type = classify_mission(mission['content'])

    # Find best triad based on learned performance
    best_triad = SELECT triad_id
                 FROM sag_route_intelligence
                 WHERE mission_type = mission_type
                 ORDER BY routing_score DESC
                 LIMIT 1;

    return jsonify({
        'recommended_triad': best_triad,
        'confidence': routing_score,
        'reasoning': f"Based on {missions_handled} previous missions, success rate {success_rate}"
    })
```

### Get Predictions

```python
@app.route('/api/intelligence/predict/<prediction_type>', methods=['GET'])
def get_predictions(prediction_type):
    """Get predictions for traffic, load, etc."""
    predictions = SELECT * FROM sag_traffic_predictions
                  WHERE prediction_type = prediction_type
                    AND prediction_for_time > NOW()
                  ORDER BY confidence_score DESC;

    return jsonify(predictions)
```

---

## Middleware Integration

Add to SAG app.py to automatically learn from all traffic:

```python
from functools import wraps
import time

# Store previous endpoint per session/user
user_previous_endpoints = {}

def traffic_intelligence_middleware(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()

        # Get context
        source = request.remote_addr
        endpoint = request.endpoint
        previous = user_previous_endpoints.get(source, None)

        # Execute the actual request
        response = f(*args, **kwargs)

        # Record traffic pattern
        elapsed_ms = (time.time() - start_time) * 1000
        record_traffic_pattern(
            endpoint=endpoint,
            previous_endpoint=previous,
            source_ip=source,
            response_time_ms=elapsed_ms,
            success=(response.status_code < 400)
        )

        # Update previous endpoint for this user
        user_previous_endpoints[source] = endpoint

        return response
    return decorated_function

# Apply to all routes
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    # Record to traffic intelligence
    record_to_intelligence(request, response, g.start_time)
    return response
```

---

## Mission Routing Logic

When a new mission comes in, use learned intelligence:

```python
def route_mission(mission_content: str) -> str:
    """Route mission to best triad based on learned performance."""

    # 1. Classify mission type
    mission_type = classify_mission_type(mission_content)
    keywords = extract_keywords(mission_content)
    complexity = estimate_complexity(mission_content)

    # 2. Query route intelligence
    candidates = query("""
        SELECT triad_id, routing_score, success_rate, avg_completion_time_seconds
        FROM sag_route_intelligence
        WHERE mission_type = %s
          OR mission_keywords && %s
        ORDER BY routing_score DESC
    """, (mission_type, keywords))

    # 3. Factor in current load
    for candidate in candidates:
        current_load = get_triad_current_load(candidate['triad_id'])
        candidate['adjusted_score'] = candidate['routing_score'] * (1 - current_load)

    # 4. Return best candidate
    best = max(candidates, key=lambda x: x['adjusted_score'])

    # 5. Log the routing decision for future learning
    log_routing_decision(mission_content, best['triad_id'], mission_type)

    return best['triad_id']
```

---

## Dashboard Metrics

Add to SAG Performance tab:

1. **Traffic Heatmap** - Requests by hour/day
2. **Endpoint Sankey Diagram** - Flow between endpoints
3. **Triad Performance Comparison** - Success rates, times
4. **Prediction Accuracy** - How well are we predicting?
5. **Cache Efficiency** - Hit rates, savings

---

## Implementation Phases

### Phase 1: Data Collection
- Add middleware to record all traffic
- Create database tables
- Start collecting baseline data

### Phase 2: Pattern Analysis
- Implement endpoint sequence learning
- Build traffic heatmaps
- Identify common flows

### Phase 3: Route Intelligence
- Track triad performance by mission type
- Build routing recommendations
- A/B test routing decisions

### Phase 4: Predictive Features
- Predict next endpoints
- Pre-fetch frequently accessed data
- Alert on anomalies

---

**END OF KB-SAG-TRAFFIC-INTELLIGENCE**

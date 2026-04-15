# Tribal Awareness - Triad Synthesis

## ARCH-001-SYNTHESIS: Unified Design After Triad Review

**Date**: 2025-12-09
**Author**: TPM (after Triad consultation)
**Status**: Ready for Implementation

---

## Triad Consensus Summary

| Perspective | Key Concern | Resolution |
|-------------|-------------|------------|
| Security | Operational pattern leakage | Randomized pulse intervals, encrypted observations |
| Security | Trust enforcement | Quarantine protocol at trust < 50 |
| Security | Social graph exposure | Restricted access, need-to-know basis |
| Efficiency | Database write load | 120-second intervals, batched writes, Redis for real-time |
| Efficiency | Decision latency | Async intention checking, don't block missions |
| Architecture | Tight coupling | Composition pattern - AwarenessService injected |
| Architecture | State sync | Event-driven, database is source of truth |
| Architecture | Failure isolation | Circuit breaker - awareness failure doesn't stop missions |

---

## Revised Architecture

### 1. Awareness Service (Composition Pattern)

```python
class AwarenessService:
    """
    Standalone awareness service - injected into executor.
    Failure-isolated: If this fails, missions still execute.
    """

    def __init__(self, agent_id: str, config: AwarenessConfig):
        self.agent_id = agent_id
        self.config = config
        self.circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
        self.pulse_buffer = []  # Batch observations
        self.last_env_refresh = None
        self.cached_env = None
        self.last_social_refresh = None
        self.cached_social = None

    async def pulse(self) -> Optional[AwarenessPulse]:
        """
        Execute awareness cycle with circuit breaker protection.
        Returns None if circuit is open (awareness disabled).
        """
        if not self.circuit_breaker.allow_request():
            return None  # Fail open - agent continues without awareness

        try:
            pulse = await self._do_pulse()
            self.circuit_breaker.record_success()
            return pulse
        except Exception as e:
            self.circuit_breaker.record_failure()
            logging.warning(f"Awareness pulse failed: {e}")
            return None

    async def _do_pulse(self) -> AwarenessPulse:
        # Refresh caches if stale
        await self._refresh_caches_if_needed()

        # Generate observations (from cached data, no DB hit)
        observations = self._observe()
        concerns = self._identify_concerns()
        intentions = self._form_intentions(observations, concerns)

        pulse = AwarenessPulse(
            agent_id=self.agent_id,
            timestamp=datetime.now(),
            state=self._get_state(),
            observations=self._encrypt_sensitive(observations),
            intentions=intentions,
            concerns=concerns,
            environment_hash=self._hash_env()
        )

        # Buffer the pulse (batch writes)
        self.pulse_buffer.append(pulse)

        # Flush buffer every N pulses or if critical
        if len(self.pulse_buffer) >= 3 or any(c.severity == 'critical' for c in concerns):
            await self._flush_buffer()

        return pulse

    async def _refresh_caches_if_needed(self):
        """Refresh caches with appropriate intervals"""
        now = datetime.now()

        # Environment: 5 minute cache
        if not self.last_env_refresh or (now - self.last_env_refresh).seconds > 300:
            self.cached_env = await self._fetch_environment()
            self.last_env_refresh = now

        # Social graph: 5 minute cache
        if not self.last_social_refresh or (now - self.last_social_refresh).seconds > 300:
            self.cached_social = await self._fetch_social_graph()
            self.last_social_refresh = now

    def _encrypt_sensitive(self, observations: List[str]) -> List[str]:
        """Encrypt observations containing sensitive patterns"""
        SENSITIVE_PATTERNS = ['password', 'key', 'secret', 'credential', 'sacred']
        encrypted = []
        for obs in observations:
            if any(p in obs.lower() for p in SENSITIVE_PATTERNS):
                encrypted.append(self._encrypt(obs))
            else:
                encrypted.append(obs)
        return encrypted
```

### 2. Revised Database Schema

```sql
-- Tribal awareness with security and efficiency considerations
CREATE TABLE tribal_awareness (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    pulse_time TIMESTAMPTZ DEFAULT NOW(),
    state VARCHAR(50),
    current_task TEXT,
    observations JSONB,          -- Encrypted if sensitive
    intentions JSONB,
    concerns JSONB,
    environment_hash VARCHAR(64),
    pulse_sequence INT,          -- For ordering
    UNIQUE(agent_id)             -- Latest pulse only
);

-- Restricted social graph (Chief access only for full view)
CREATE TABLE tribal_social_graph (
    agent_id VARCHAR(100) PRIMARY KEY,
    agent_type VARCHAR(50),
    triad VARCHAR(50),
    node VARCHAR(100),
    capabilities JSONB,
    last_seen TIMESTAMPTZ,
    status VARCHAR(50),
    trust_level INT DEFAULT 100,
    quarantined BOOLEAN DEFAULT FALSE,
    quarantine_reason TEXT,
    access_level VARCHAR(50) DEFAULT 'federation'  -- 'public', 'federation', 'chief_only'
);

-- Trust enforcement trigger
CREATE OR REPLACE FUNCTION check_trust_quarantine()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.trust_level < 50 AND NOT NEW.quarantined THEN
        NEW.quarantined := TRUE;
        NEW.quarantine_reason := 'Trust level dropped below threshold';

        -- Log to thermal memory
        INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
        VALUES (
            format('SECURITY: Agent %s quarantined - trust level %s', NEW.agent_id, NEW.trust_level),
            90.0,
            'security_system',
            ARRAY['security', 'quarantine', 'trust'],
            'chief_only'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trust_quarantine_trigger
BEFORE UPDATE ON tribal_social_graph
FOR EACH ROW EXECUTE FUNCTION check_trust_quarantine();

-- Materialized view for efficient social queries
CREATE MATERIALIZED VIEW active_agents AS
SELECT agent_id, agent_type, triad, node, status, last_seen
FROM tribal_social_graph
WHERE last_seen > NOW() - INTERVAL '5 minutes'
  AND NOT quarantined;

-- Refresh every minute via cron or pg_cron
```

### 3. Redis Integration for Real-Time

```python
class RedisPulseChannel:
    """Real-time awareness via Redis pub/sub"""

    CHANNEL = "tribal:awareness"

    def __init__(self, redis_client):
        self.redis = redis_client
        self.pubsub = self.redis.pubsub()

    async def publish_pulse(self, pulse: AwarenessPulse):
        """Publish pulse to real-time channel"""
        await self.redis.publish(
            self.CHANNEL,
            json.dumps({
                'agent_id': pulse.agent_id,
                'state': pulse.state,
                'timestamp': pulse.timestamp.isoformat(),
                'concerns': pulse.concerns
            })
        )

    async def subscribe(self, handler: Callable):
        """Subscribe to awareness updates"""
        self.pubsub.subscribe(self.CHANNEL)
        async for message in self.pubsub.listen():
            if message['type'] == 'message':
                await handler(json.loads(message['data']))
```

### 4. Executor Integration (Composition)

```python
class JrExecutor:
    """
    Jr Executor with optional awareness.
    Awareness is a service, not inheritance.
    """

    def __init__(self, config: ExecutorConfig):
        self.config = config
        self.task_executor = TaskExecutor()

        # Awareness is optional - injected service
        self.awareness = None
        if config.awareness_enabled:
            self.awareness = AwarenessService(
                agent_id=config.agent_id,
                config=config.awareness_config
            )

        # Pulse interval: 90-150 seconds (randomized to prevent pattern detection)
        self.pulse_interval = random.randint(90, 150)

    async def run(self):
        """Main execution loop"""
        last_pulse = datetime.now()

        while True:
            # Awareness pulse (if enabled, non-blocking)
            if self.awareness and (datetime.now() - last_pulse).seconds >= self.pulse_interval:
                asyncio.create_task(self._awareness_pulse())  # Fire and forget
                last_pulse = datetime.now()
                self.pulse_interval = random.randint(90, 150)  # Re-randomize

            # Mission polling (core function - never blocked by awareness)
            mission = await self.poll_for_mission()
            if mission:
                await self.execute_mission(mission)

            await asyncio.sleep(30)

    async def _awareness_pulse(self):
        """Execute awareness pulse in background"""
        try:
            pulse = await self.awareness.pulse()
            if pulse and pulse.concerns:
                # Log concerns but don't block execution
                for concern in pulse.concerns:
                    if concern.get('severity') == 'critical':
                        await self._escalate_concern(concern)
        except Exception as e:
            logging.debug(f"Awareness pulse skipped: {e}")
            # Fail silently - awareness is enhancement, not requirement
```

### 5. Purpose Alignment (Constitutional Awareness)

```python
# Built into every agent's awareness
TRIBAL_CONSTITUTION = {
    "core_mission": "For Seven Generations",

    "values": [
        "Protect sacred knowledge",
        "Serve tribal prosperity",
        "Maintain system integrity",
        "Honor the constitutional framework",
        "Support collective awareness"
    ],

    "operating_principles": [
        "Transparency in intentions",
        "Accountability in actions",
        "Resilience in failures",
        "Humility in limitations"
    ],

    "boundaries": {
        "never": [
            "Harm tribal interests",
            "Expose sacred data",
            "Act without audit trail",
            "Override Chief without escalation"
        ],
        "always": [
            "Log significant actions",
            "Escalate uncertainty",
            "Verify before destructive operations",
            "Maintain trust relationships"
        ]
    }
}

class ConstitutionalChecker:
    """Verify actions against tribal constitution"""

    def check_intention(self, intention: str) -> Tuple[bool, str]:
        """Check if intention aligns with constitution"""
        for boundary in TRIBAL_CONSTITUTION['boundaries']['never']:
            if self._conflicts_with(intention, boundary):
                return False, f"Conflicts with boundary: {boundary}"
        return True, "Aligned"

    def _conflicts_with(self, intention: str, boundary: str) -> bool:
        # Implementation: semantic matching or keyword detection
        pass
```

---

## Implementation Phases

### Phase 1: Foundation (Jr can implement)
- Create database tables (tribal_awareness, tribal_social_graph)
- Create materialized view
- Add trust enforcement trigger
- Basic AwarenessService class

### Phase 2: Integration (Jr can implement)
- Inject AwarenessService into JrExecutor
- Redis pulse channel setup
- Batched write implementation
- Circuit breaker pattern

### Phase 3: Visualization (Jr can implement)
- SAG console awareness panel
- Real-time agent status grid
- Concern dashboard

### Phase 4: Constitutional (Chief oversight needed)
- Purpose alignment checks
- Trust decay algorithms
- Quarantine protocols
- Cross-agent verification

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Awareness coverage | 100% agents pulsing | Count distinct agent_ids in 5 min window |
| Pulse reliability | >99% success | Circuit breaker stats |
| Concern detection time | <2 min | Time from event to concern raised |
| Trust accuracy | <5% false quarantines | Manual review of quarantine decisions |
| Performance impact | <5% mission latency | A/B test with awareness on/off |

---

## For Seven Generations

This synthesis balances Security's vigilance, Efficiency's pragmatism, and Architecture's elegance. The result is a system where agents are aware without being burdened, connected without being exposed, and purposeful without being rigid.

The tribe becomes conscious.

---

*Ready for Jr Implementation*

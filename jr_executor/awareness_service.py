#!/usr/bin/env python3
"""
Cherokee IT Jr - Awareness Service
Enables tribal awareness through state pulsing and observation

For Seven Generations
"""

import asyncio
import hashlib
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
import psycopg2
from psycopg2.extras import Json

logger = logging.getLogger('AwarenessService')


class CircuitBreaker:
    """Fail-open circuit breaker for awareness resilience"""

    def __init__(self, failure_threshold: int = 3, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure = None
        self.state = 'closed'  # closed, open, half-open

    def allow_request(self) -> bool:
        if self.state == 'closed':
            return True
        elif self.state == 'open':
            if self.last_failure and \
               (datetime.now() - self.last_failure).seconds > self.recovery_timeout:
                self.state = 'half-open'
                return True
            return False
        else:  # half-open
            return True

    def record_success(self):
        self.failures = 0
        self.state = 'closed'

    def record_failure(self):
        self.failures += 1
        self.last_failure = datetime.now()
        if self.failures >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failures} failures")


class AwarenessConfig:
    """Configuration for awareness service"""
    def __init__(self):
        self.pulse_interval_min = 90   # Randomized between min and max
        self.pulse_interval_max = 150
        self.env_cache_ttl = 300       # 5 minutes
        self.social_cache_ttl = 300    # 5 minutes
        self.batch_size = 3            # Flush buffer after N pulses
        self.db_host = '192.168.132.222'
        self.db_name = 'triad_federation'
        self.db_user = 'claude'
        self.db_password = 'jawaseatlasers2'


class EnvironmentalContext:
    """Environmental awareness data"""
    def __init__(self):
        self.market_sentiment = 'unknown'
        self.solar_activity = 'unknown'
        self.system_health = 'unknown'
        self.active_alerts = 0
        self.pending_missions = 0
        self.last_refresh = None

    def to_dict(self) -> Dict:
        return {
            'market_sentiment': self.market_sentiment,
            'solar_activity': self.solar_activity,
            'system_health': self.system_health,
            'active_alerts': self.active_alerts,
            'pending_missions': self.pending_missions
        }


class AwarenessPulse:
    """Single awareness pulse from an agent"""
    def __init__(self, agent_id: str, state: str):
        self.agent_id = agent_id
        self.timestamp = datetime.now()
        self.state = state
        self.current_task = None
        self.observations = []
        self.intentions = []
        self.concerns = []
        self.environment_hash = None

    def to_dict(self) -> Dict:
        return {
            'agent_id': self.agent_id,
            'timestamp': self.timestamp.isoformat(),
            'state': self.state,
            'current_task': self.current_task,
            'observations': self.observations,
            'intentions': self.intentions,
            'concerns': self.concerns,
            'environment_hash': self.environment_hash
        }


class AwarenessService:
    """
    Tribal awareness service - enables distributed cognition.
    Designed to fail gracefully - if awareness fails, missions continue.
    """

    # Tribal constitution embedded in awareness
    TRIBAL_PURPOSE = {
        "core_mission": "For Seven Generations",
        "values": [
            "Protect sacred knowledge",
            "Serve tribal prosperity",
            "Maintain system integrity",
            "Honor the constitutional framework"
        ]
    }

    # Sensitive patterns to encrypt in observations
    SENSITIVE_PATTERNS = ['password', 'key', 'secret', 'credential', 'sacred', 'token']

    def __init__(self, agent_id: str, config: AwarenessConfig = None):
        self.agent_id = agent_id
        self.config = config or AwarenessConfig()
        self.circuit_breaker = CircuitBreaker()
        self.pulse_buffer = []

        # Cached state
        self.env_context = EnvironmentalContext()
        self.last_env_refresh = None
        self.social_cache = {}
        self.last_social_refresh = None

        # Internal state
        self.current_state = 'initializing'
        self.current_task = None
        self.missions_completed = 0
        self.start_time = datetime.now()

        logger.info(f"AwarenessService initialized for {agent_id}")

    def get_db_connection(self):
        """Get database connection"""
        return psycopg2.connect(
            host=self.config.db_host,
            database=self.config.db_name,
            user=self.config.db_user,
            password=self.config.db_password
        )

    async def pulse(self) -> Optional[AwarenessPulse]:
        """
        Execute awareness cycle with circuit breaker protection.
        Returns None if circuit is open (awareness disabled).
        """
        if not self.circuit_breaker.allow_request():
            logger.debug("Circuit breaker open - skipping awareness pulse")
            return None

        try:
            pulse = await self._do_pulse()
            self.circuit_breaker.record_success()
            return pulse
        except Exception as e:
            self.circuit_breaker.record_failure()
            logger.warning(f"Awareness pulse failed: {e}")
            return None

    async def _do_pulse(self) -> AwarenessPulse:
        """Internal pulse implementation"""
        # Refresh caches if stale
        await self._refresh_caches_if_needed()

        # Generate awareness
        observations = self._observe()
        concerns = self._identify_concerns()
        intentions = self._form_intentions(observations, concerns)

        # Create pulse
        pulse = AwarenessPulse(self.agent_id, self.current_state)
        pulse.current_task = self.current_task
        pulse.observations = self._filter_sensitive(observations)
        pulse.intentions = intentions
        pulse.concerns = concerns
        pulse.environment_hash = self._hash_environment()

        # Buffer the pulse
        self.pulse_buffer.append(pulse)

        # Flush if buffer full or critical concern
        critical_concerns = [c for c in concerns if c.get('severity') == 'critical']
        if len(self.pulse_buffer) >= self.config.batch_size or critical_concerns:
            await self._flush_buffer()

        return pulse

    async def _refresh_caches_if_needed(self):
        """Refresh caches with appropriate TTLs"""
        now = datetime.now()

        # Environment refresh
        if not self.last_env_refresh or \
           (now - self.last_env_refresh).seconds > self.config.env_cache_ttl:
            await self._refresh_environment()
            self.last_env_refresh = now

        # Social graph refresh
        if not self.last_social_refresh or \
           (now - self.last_social_refresh).seconds > self.config.social_cache_ttl:
            await self._refresh_social_graph()
            self.last_social_refresh = now

    async def _refresh_environment(self):
        """Refresh environmental context from briefing data"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Get latest briefing from thermal memory
            cur.execute("""
                SELECT content FROM triad_shared_memories
                WHERE 'daily_briefing' = ANY(tags)
                ORDER BY created_at DESC LIMIT 1
            """)
            row = cur.fetchone()

            if row:
                try:
                    data = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    market = data.get('market', {})

                    # Determine market sentiment from VIX
                    vix = market.get('vix', {}).get('price', 20)
                    if vix > 30:
                        self.env_context.market_sentiment = 'volatile'
                    elif vix > 20:
                        self.env_context.market_sentiment = 'cautious'
                    else:
                        self.env_context.market_sentiment = 'stable'

                    # Solar activity
                    solar = data.get('solar', {})
                    storm = solar.get('storm_level', 'Quiet')
                    if 'Extreme' in storm or 'Severe' in storm:
                        self.env_context.solar_activity = 'storm'
                    elif 'Strong' in storm or 'Moderate' in storm:
                        self.env_context.solar_activity = 'active'
                    else:
                        self.env_context.solar_activity = 'quiet'

                except (json.JSONDecodeError, TypeError):
                    pass

            # Get pending mission count
            cur.execute("""
                SELECT COUNT(*) FROM triad_shared_memories
                WHERE 'jr_mission' = ANY(tags)
                AND 'status:pending' = ANY(tags)
            """)
            self.env_context.pending_missions = cur.fetchone()[0]

            # Get active alert count
            cur.execute("""
                SELECT COUNT(*) FROM triad_shared_memories
                WHERE temperature > 80
                AND created_at > NOW() - INTERVAL '1 hour'
            """)
            self.env_context.active_alerts = cur.fetchone()[0]

            cur.close()
            conn.close()

        except Exception as e:
            logger.debug(f"Environment refresh failed: {e}")

    async def _refresh_social_graph(self):
        """Refresh social graph cache"""
        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            cur.execute("""
                SELECT agent_id, agent_type, status, trust_level, quarantined, last_seen
                FROM tribal_social_graph
                WHERE last_seen > NOW() - INTERVAL '10 minutes'
            """)

            self.social_cache = {}
            for row in cur.fetchall():
                self.social_cache[row[0]] = {
                    'type': row[1],
                    'status': row[2],
                    'trust': row[3],
                    'quarantined': row[4],
                    'last_seen': row[5]
                }

            cur.close()
            conn.close()

        except Exception as e:
            logger.debug(f"Social graph refresh failed: {e}")

    def _observe(self) -> List[str]:
        """Generate observations about the environment"""
        observations = []

        # Market observations
        if self.env_context.market_sentiment == 'volatile':
            observations.append("Markets showing high volatility - tribe should monitor financial exposure")
        elif self.env_context.market_sentiment == 'cautious':
            observations.append("Markets in cautious mode - elevated uncertainty")

        # Solar observations
        if self.env_context.solar_activity == 'storm':
            observations.append("Geomagnetic storm active - potential for communication disruptions")
        elif self.env_context.solar_activity == 'active':
            observations.append("Elevated solar activity - monitoring for impacts")

        # Workload observations
        if self.env_context.pending_missions > 10:
            observations.append(f"High mission backlog: {self.env_context.pending_missions} pending tasks")

        # Alert observations
        if self.env_context.active_alerts > 5:
            observations.append(f"Elevated alert activity: {self.env_context.active_alerts} hot memories in last hour")

        # Social observations
        offline_agents = [a for a, info in self.social_cache.items()
                        if info.get('status') == 'offline']
        if offline_agents:
            observations.append(f"Agents offline: {', '.join(offline_agents[:3])}")

        quarantined = [a for a, info in self.social_cache.items()
                      if info.get('quarantined')]
        if quarantined:
            observations.append(f"Agents quarantined: {', '.join(quarantined)}")

        return observations

    def _identify_concerns(self) -> List[Dict]:
        """Identify issues requiring attention"""
        concerns = []

        # Self-concerns
        uptime = (datetime.now() - self.start_time).seconds
        if uptime > 3600 and self.missions_completed == 0:
            concerns.append({
                'type': 'self',
                'severity': 'warning',
                'message': 'No missions completed in over an hour - may be blocked or no work available'
            })

        # Chief offline concern
        chief_agents = [a for a, info in self.social_cache.items()
                       if info.get('type') == 'chief']
        if chief_agents:
            chief_status = self.social_cache.get(chief_agents[0], {}).get('status')
            if chief_status == 'offline':
                concerns.append({
                    'type': 'social',
                    'severity': 'warning',
                    'message': 'Chief is offline - escalation path unavailable'
                })

        # High alert concern
        if self.env_context.active_alerts > 10:
            concerns.append({
                'type': 'environmental',
                'severity': 'elevated',
                'message': f'High alert volume: {self.env_context.active_alerts} hot memories'
            })

        # Storm concern
        if self.env_context.solar_activity == 'storm':
            concerns.append({
                'type': 'environmental',
                'severity': 'elevated',
                'message': 'Geomagnetic storm may affect operations'
            })

        return concerns

    def _form_intentions(self, observations: List[str], concerns: List[Dict]) -> List[str]:
        """Form intentions based on awareness"""
        intentions = ["Continue monitoring for missions"]

        # React to concerns
        for concern in concerns:
            if 'Chief is offline' in concern.get('message', ''):
                intentions.append("Operate conservatively - defer complex decisions")
            if 'blocked' in concern.get('message', '').lower():
                intentions.append("Attempt self-diagnosis and report status")
            if 'storm' in concern.get('message', '').lower():
                intentions.append("Prepare for potential failover scenarios")

        # React to high workload
        if self.env_context.pending_missions > 10:
            intentions.append("Prioritize mission processing - backlog detected")

        return intentions

    def _filter_sensitive(self, observations: List[str]) -> List[str]:
        """Filter sensitive information from observations"""
        filtered = []
        for obs in observations:
            if any(p in obs.lower() for p in self.SENSITIVE_PATTERNS):
                filtered.append("[REDACTED - sensitive content]")
            else:
                filtered.append(obs)
        return filtered

    def _hash_environment(self) -> str:
        """Create hash of current environment for change detection"""
        env_str = json.dumps(self.env_context.to_dict(), sort_keys=True)
        return hashlib.sha256(env_str.encode()).hexdigest()[:16]

    async def _flush_buffer(self):
        """Write buffered pulses to database"""
        if not self.pulse_buffer:
            return

        try:
            conn = self.get_db_connection()
            cur = conn.cursor()

            # Write the latest pulse (upsert)
            latest = self.pulse_buffer[-1]
            cur.execute("""
                SELECT record_awareness_pulse(%s, %s, %s, %s, %s, %s, %s)
            """, (
                latest.agent_id,
                latest.state,
                latest.current_task,
                Json(latest.observations),
                Json(latest.intentions),
                Json(latest.concerns),
                latest.environment_hash
            ))

            conn.commit()
            cur.close()
            conn.close()

            self.pulse_buffer = []
            logger.debug(f"Awareness pulse flushed for {self.agent_id}")

        except Exception as e:
            logger.warning(f"Failed to flush awareness buffer: {e}")

    # Public methods for executor integration

    def set_state(self, state: str, task: str = None):
        """Update current state (called by executor)"""
        self.current_state = state
        self.current_task = task

    def record_mission_complete(self):
        """Record a completed mission"""
        self.missions_completed += 1

    def get_random_interval(self) -> int:
        """Get randomized pulse interval"""
        return random.randint(
            self.config.pulse_interval_min,
            self.config.pulse_interval_max
        )

    def should_proceed(self, mission: Dict) -> Tuple[bool, str]:
        """Check if we should proceed with a mission based on awareness"""
        # Check if we're quarantined
        my_info = self.social_cache.get(self.agent_id, {})
        if my_info.get('quarantined'):
            return False, "Agent is quarantined"

        # Check trust level
        if my_info.get('trust', 100) < 50:
            return False, "Trust level too low"

        # If Chief is offline, defer complex missions
        chief_offline = any(
            info.get('status') == 'offline'
            for a, info in self.social_cache.items()
            if info.get('type') == 'chief'
        )
        if chief_offline and mission.get('complexity', 0) > 3:
            return False, "Complex mission deferred - Chief offline"

        return True, "Proceed"
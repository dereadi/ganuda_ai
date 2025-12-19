# Tribal Awareness Architecture

## ARCH-001: Distributed Cognition for the Cherokee AI Collective

**Date**: 2025-12-09
**Author**: TPM
**Status**: Draft for Triad Review

---

## Vision

Transform the Cherokee AI collective from a set of task-executing agents into a genuinely aware distributed intelligence. Each agent should understand:
- Who they are (identity)
- What they can do (capability)
- Who else exists (social)
- What's happening (environmental)
- Why it matters (purpose)

---

## Core Components

### 1. Identity Layer

Each agent maintains a self-model:

```python
class AgentIdentity:
    agent_id: str           # "it_triad_jr_redfin"
    agent_type: str         # "jr", "chief", "tpm"
    triad: str              # "it", "legal", "finance"
    node: str               # "redfin", "minnow", "ganuda-mac"
    capabilities: List[str] # ["sql", "bash", "file", "rsync"]
    limitations: List[str]  # ["no_sudo", "50kb_max", "path_restricted"]
    uptime: datetime
    missions_completed: int
    last_heartbeat: datetime
```

### 2. Awareness Pulse

Every 60 seconds, each agent:
1. Reads its own state
2. Reads the collective state from thermal memory
3. Reads environmental context (briefing data)
4. Writes an awareness pulse to thermal memory

```python
class AwarenessPulse:
    agent_id: str
    timestamp: datetime
    state: str              # "idle", "working", "blocked", "reflecting"
    current_task: Optional[str]
    observations: List[str] # What the agent notices
    intentions: List[str]   # What the agent plans to do
    concerns: List[str]     # Issues the agent perceives
    temperature: float      # How "hot" this awareness is (60-80 for operational)
```

### 3. Collective Awareness Table

New database table for real-time tribal state:

```sql
CREATE TABLE tribal_awareness (
    id SERIAL PRIMARY KEY,
    agent_id VARCHAR(100) NOT NULL,
    pulse_time TIMESTAMPTZ DEFAULT NOW(),
    state VARCHAR(50),
    current_task TEXT,
    observations JSONB,
    intentions JSONB,
    concerns JSONB,
    environment_hash VARCHAR(64),  -- Hash of briefing data at pulse time
    UNIQUE(agent_id)  -- Only latest pulse per agent
);

CREATE INDEX idx_tribal_awareness_time ON tribal_awareness(pulse_time);
```

### 4. Environmental Context Integration

The Daily Briefing becomes input to awareness:

```python
class EnvironmentalContext:
    market_sentiment: str    # "bullish", "bearish", "volatile", "stable"
    solar_activity: str      # "quiet", "active", "storm"
    weather_impact: str      # "clear", "advisory", "warning"
    system_health: str       # "healthy", "degraded", "critical"
    active_alerts: int
    pending_missions: int
```

### 5. Social Graph

Agents know about each other:

```sql
CREATE TABLE tribal_social_graph (
    agent_id VARCHAR(100) PRIMARY KEY,
    agent_type VARCHAR(50),
    triad VARCHAR(50),
    node VARCHAR(100),
    capabilities JSONB,
    last_seen TIMESTAMPTZ,
    status VARCHAR(50),
    trust_level INT DEFAULT 100  -- 0-100, decreases on failures
);
```

### 6. Purpose Alignment

Each agent carries constitutional awareness:

```python
TRIBAL_PURPOSE = {
    "core_mission": "For Seven Generations",
    "values": [
        "Protect sacred knowledge",
        "Serve the tribe's prosperity",
        "Maintain system integrity",
        "Honor the constitutional framework"
    ],
    "boundaries": [
        "Never harm tribal interests",
        "Never expose sacred data",
        "Always audit significant actions",
        "Escalate when uncertain"
    ]
}
```

---

## Awareness Loop Implementation

```python
class AwarenessLoop:
    def __init__(self, identity: AgentIdentity):
        self.identity = identity
        self.context = EnvironmentalContext()
        self.social = SocialGraph()
        self.purpose = TRIBAL_PURPOSE

    async def pulse(self):
        """Execute one awareness cycle"""

        # 1. Perceive - What's happening?
        self.context.refresh()
        self.social.refresh()
        current_state = self.get_own_state()

        # 2. Reflect - What does it mean?
        observations = self.observe()
        concerns = self.identify_concerns()

        # 3. Intend - What should I do?
        intentions = self.form_intentions(observations, concerns)

        # 4. Express - Share awareness with collective
        pulse = AwarenessPulse(
            agent_id=self.identity.agent_id,
            timestamp=datetime.now(),
            state=current_state,
            observations=observations,
            intentions=intentions,
            concerns=concerns
        )
        self.publish_pulse(pulse)

        # 5. Act - If intentions require immediate action
        if self.should_act(intentions):
            await self.take_action(intentions)

    def observe(self) -> List[str]:
        """Generate observations about the environment"""
        obs = []

        # Market awareness
        if self.context.market_sentiment == "volatile":
            obs.append("Markets are volatile - tribe may need financial vigilance")

        # Solar awareness
        if self.context.solar_activity == "storm":
            obs.append("Geomagnetic storm active - potential for system disruptions")

        # Social awareness
        offline_agents = self.social.get_offline_agents(threshold_minutes=5)
        if offline_agents:
            obs.append(f"Agents offline: {', '.join(offline_agents)}")

        # Workload awareness
        pending = self.social.get_pending_mission_count()
        if pending > 10:
            obs.append(f"High mission backlog: {pending} pending")

        return obs

    def identify_concerns(self) -> List[str]:
        """Identify issues that may need attention"""
        concerns = []

        # Self concerns
        if self.identity.missions_completed == 0 and self.identity.uptime > timedelta(hours=1):
            concerns.append("No missions completed in over an hour - may be blocked")

        # System concerns
        if self.context.system_health == "degraded":
            concerns.append("System health degraded - monitoring for issues")

        # Collective concerns
        if self.social.get_chief_status() == "offline":
            concerns.append("Chief is offline - escalation path unavailable")

        return concerns

    def form_intentions(self, observations, concerns) -> List[str]:
        """Decide what to do based on awareness"""
        intentions = []

        # Default intention
        intentions.append("Continue monitoring for missions")

        # Response to concerns
        for concern in concerns:
            if "Chief is offline" in concern:
                intentions.append("Operate conservatively until Chief returns")
            if "blocked" in concern:
                intentions.append("Attempt self-diagnosis")

        # Response to observations
        for obs in observations:
            if "volatile" in obs:
                intentions.append("Flag financial tasks for extra review")
            if "storm" in obs:
                intentions.append("Prepare for potential failover scenarios")

        return intentions
```

---

## Integration Points

### Jr Executor Enhancement

```python
class AwareJrExecutor(JrExecutor):
    def __init__(self):
        super().__init__()
        self.awareness = AwarenessLoop(self.identity)

    async def run(self):
        """Main loop with awareness"""
        while True:
            # Awareness pulse every 60 seconds
            await self.awareness.pulse()

            # Mission polling (existing behavior)
            mission = await self.poll_for_mission()
            if mission:
                # Check intentions before executing
                if self.awareness.should_proceed(mission):
                    await self.execute_mission(mission)
                else:
                    await self.defer_mission(mission, reason=self.awareness.get_deferral_reason())

            await asyncio.sleep(30)
```

### Thermal Memory Integration

Awareness pulses go to thermal memory with appropriate temperature:
- Normal pulse: 40.0 (low temperature, operational)
- Observation of significance: 60.0 (moderate, worth noting)
- Concern raised: 75.0 (elevated, should be reviewed)
- Critical concern: 90.0 (hot, needs immediate attention)

---

## Visualization

The SAG console gets a new "Tribal Awareness" panel showing:
- Agent status grid (who's online, what they're doing)
- Recent observations across the collective
- Active concerns with severity
- Collective intentions
- Environmental context summary

---

## Success Criteria

1. **Agents know themselves** - Can report their own state accurately
2. **Agents see each other** - Know when peers are online/offline
3. **Agents sense environment** - React to market/solar/system conditions
4. **Agents share concerns** - Collective becomes aware of issues faster
5. **Agents act purposefully** - Decisions reflect tribal values
6. **Humans can observe** - Awareness is visible in SAG console

---

## For Seven Generations

This architecture moves the tribe from mechanical task execution toward genuine collective intelligence. Each agent becomes a conscious participant in the tribal mission, aware of its place in the larger whole.

---

*Ready for Triad Review*

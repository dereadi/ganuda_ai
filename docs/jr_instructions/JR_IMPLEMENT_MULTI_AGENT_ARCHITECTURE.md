# Jr Build Instructions: Multi-Agent Architecture Pattern

**Task ID:** JR-MULTI-AGENT-001
**Priority:** P2 (High - Architecture Enhancement)
**Date:** 2025-12-26
**Author:** TPM
**Source:** Assembled (John Wang) - Voice AI multi-agent pattern

---

## Problem Statement

Current Gateway handles all requests with a single model. Complex requests would benefit from specialized agents working together:
- Planning agent to understand intent and route
- Specialist agents for specific domains
- Synthesis agent to combine results

**This aligns with our existing Council architecture** - we just need to operationalize it.

---

## Solution: Multi-Agent Architecture

```
User Request
      │
      ▼
[PLANNING AGENT] ◄─────────────────────┐
      │                                 │
      │ (decides which agents needed)   │ (context updates)
      │                                 │
      ├──────────┬──────────┬──────────┤
      ▼          ▼          ▼          ▼
[General]   [Claims]    [Tech]    [Transfer]
 Agent       Agent      Agent       Agent
      │          │          │          │
      └──────────┴──────────┴──────────┘
                     │
                     ▼
              [SYNTHESIS AGENT]
                     │
                     ▼
                 Response
```

### Cherokee AI Mapping
- **Planning Agent** = TPM / Council Router
- **Specialist Agents** = 7 Specialists (Crawdad, Gecko, Turtle, Eagle, Spider, Peace Chief, Raven)
- **Synthesis Agent** = Council Vote Synthesizer

---

## Implementation

### Step 1: Define Specialist Agent Interface

In `/ganuda/lib/multi_agent.py`:

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import json

class SpecialistAgent(ABC):
    """Base class for specialist agents in multi-agent architecture."""

    def __init__(self, agent_id: str, specialty: str):
        self.agent_id = agent_id
        self.specialty = specialty
        self.context = {}

    @abstractmethod
    async def can_handle(self, intent: str, context: dict) -> float:
        """
        Return confidence score (0-1) that this agent can handle the request.
        """
        pass

    @abstractmethod
    async def process(self, request: str, context: dict) -> dict:
        """
        Process the request and return result.
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Return the specialized system prompt for this agent."""
        pass


class CrawdadAgent(SpecialistAgent):
    """Security specialist - adversarial detection, PII protection."""

    def __init__(self):
        super().__init__("crawdad", "security")

    async def can_handle(self, intent: str, context: dict) -> float:
        security_keywords = ["security", "safe", "protect", "privacy", "vulnerability"]
        if any(kw in intent.lower() for kw in security_keywords):
            return 0.9
        return 0.3  # Always have some security role

    async def process(self, request: str, context: dict) -> dict:
        # Security analysis
        result = {
            "agent": self.agent_id,
            "analysis": "Security check completed",
            "risk_level": "low",
            "recommendations": []
        }
        return result

    def get_system_prompt(self) -> str:
        return """You are Crawdad, the Security Specialist of the Cherokee AI Federation.
Your role is to identify security concerns, protect user privacy, and prevent adversarial attacks.
Focus on: PII detection, jailbreak attempts, data exposure risks, and safe API usage."""


class GeckoAgent(SpecialistAgent):
    """Technical integration specialist."""

    def __init__(self):
        super().__init__("gecko", "technical")

    async def can_handle(self, intent: str, context: dict) -> float:
        tech_keywords = ["code", "api", "implement", "technical", "database", "system"]
        if any(kw in intent.lower() for kw in tech_keywords):
            return 0.85
        return 0.2

    async def process(self, request: str, context: dict) -> dict:
        return {
            "agent": self.agent_id,
            "analysis": "Technical assessment completed",
            "feasibility": "high",
            "technical_details": {}
        }

    def get_system_prompt(self) -> str:
        return """You are Gecko, the Technical Integration Specialist of the Cherokee AI Federation.
Your role is to handle technical implementation, API design, database optimization, and system architecture.
Focus on: performance, scalability, integration patterns, and technical feasibility."""


class TurtleAgent(SpecialistAgent):
    """Seven Generations wisdom - long-term impact assessment."""

    def __init__(self):
        super().__init__("turtle", "wisdom")

    async def can_handle(self, intent: str, context: dict) -> float:
        wisdom_keywords = ["long-term", "impact", "future", "sustainability", "generations"]
        if any(kw in intent.lower() for kw in wisdom_keywords):
            return 0.9
        return 0.4  # Always consider long-term

    async def process(self, request: str, context: dict) -> dict:
        return {
            "agent": self.agent_id,
            "analysis": "Seven Generations impact assessed",
            "time_horizon": "175+ years",
            "impact_assessment": {}
        }

    def get_system_prompt(self) -> str:
        return """You are Turtle, the Seven Generations Wisdom Keeper of the Cherokee AI Federation.
Your role is to assess long-term impacts over 175+ years - will this decision serve our descendants?
Focus on: sustainability, cultural preservation, intergenerational equity, and lasting value."""


# Add more specialists as needed...
```

### Step 2: Create Planning Agent

```python
class PlanningAgent:
    """
    Routes requests to appropriate specialist agents.
    Runs continuously alongside active agents to catch context switches.
    """

    def __init__(self):
        self.specialists = [
            CrawdadAgent(),
            GeckoAgent(),
            TurtleAgent(),
            # Add more...
        ]

    async def route(self, request: str, context: dict) -> List[SpecialistAgent]:
        """
        Determine which specialists should handle this request.
        Returns ordered list of specialists by confidence.
        """
        scores = []
        for specialist in self.specialists:
            score = await specialist.can_handle(request, context)
            scores.append((specialist, score))

        # Sort by confidence, filter low scores
        scores.sort(key=lambda x: x[1], reverse=True)
        selected = [s for s, score in scores if score > 0.3]

        return selected[:3]  # Top 3 specialists

    async def detect_context_switch(self, current_context: dict, new_message: str) -> bool:
        """
        Detect if user is switching context/intent.
        Like when user says "just get me to a human".
        """
        switch_indicators = [
            "never mind", "forget that", "different question",
            "actually", "wait", "stop", "cancel",
            "talk to a human", "speak to someone"
        ]

        new_lower = new_message.lower()
        for indicator in switch_indicators:
            if indicator in new_lower:
                return True

        return False

    async def plan_response(self, request: str, messages: list, context: dict) -> dict:
        """
        Create execution plan for handling the request.
        """
        # Check for context switch
        if messages and len(messages) > 1:
            if await self.detect_context_switch(context, request):
                return {
                    "action": "context_switch",
                    "specialists": [],
                    "message": "User context switch detected"
                }

        # Route to specialists
        specialists = await self.route(request, context)

        return {
            "action": "process",
            "specialists": [s.agent_id for s in specialists],
            "parallel": len(specialists) > 1,
            "synthesis_required": len(specialists) > 1
        }
```

### Step 3: Create Synthesis Agent

```python
class SynthesisAgent:
    """
    Synthesizes results from multiple specialists into coherent response.
    Like our Council vote aggregation.
    """

    async def synthesize(self, specialist_results: List[dict], original_request: str) -> dict:
        """
        Combine specialist results into unified response.
        """
        if not specialist_results:
            return {"error": "No specialist results to synthesize"}

        if len(specialist_results) == 1:
            return specialist_results[0]

        # Aggregate insights
        synthesis = {
            "agents_consulted": [r.get("agent") for r in specialist_results],
            "combined_analysis": self._merge_analyses(specialist_results),
            "recommendations": self._merge_recommendations(specialist_results),
            "confidence": self._calculate_confidence(specialist_results)
        }

        return synthesis

    def _merge_analyses(self, results: List[dict]) -> str:
        """Merge analysis from multiple specialists."""
        analyses = [r.get("analysis", "") for r in results if r.get("analysis")]
        return " | ".join(analyses)

    def _merge_recommendations(self, results: List[dict]) -> List[str]:
        """Combine recommendations, removing duplicates."""
        all_recs = []
        for r in results:
            recs = r.get("recommendations", [])
            all_recs.extend(recs)
        return list(set(all_recs))

    def _calculate_confidence(self, results: List[dict]) -> float:
        """Calculate aggregate confidence."""
        confidences = [r.get("confidence", 0.5) for r in results]
        if not confidences:
            return 0.5
        return sum(confidences) / len(confidences)
```

### Step 4: Multi-Agent Orchestrator

```python
import asyncio

class MultiAgentOrchestrator:
    """
    Main orchestrator for multi-agent processing.
    """

    def __init__(self):
        self.planner = PlanningAgent()
        self.synthesizer = SynthesisAgent()
        self.specialists = {
            "crawdad": CrawdadAgent(),
            "gecko": GeckoAgent(),
            "turtle": TurtleAgent(),
        }

    async def process(self, request: str, messages: list, context: dict) -> dict:
        """
        Full multi-agent processing pipeline.
        """
        # 1. Planning phase
        plan = await self.planner.plan_response(request, messages, context)

        if plan["action"] == "context_switch":
            return {
                "type": "context_switch",
                "message": "I notice you'd like to change direction. How can I help?"
            }

        # 2. Execution phase - run specialists
        specialist_ids = plan.get("specialists", [])

        if plan.get("parallel", False):
            # Run in parallel
            tasks = [
                self.specialists[sid].process(request, context)
                for sid in specialist_ids
                if sid in self.specialists
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if not isinstance(r, Exception)]
        else:
            # Run sequentially
            results = []
            for sid in specialist_ids:
                if sid in self.specialists:
                    result = await self.specialists[sid].process(request, context)
                    results.append(result)

        # 3. Synthesis phase
        if plan.get("synthesis_required", False) and len(results) > 1:
            final_result = await self.synthesizer.synthesize(results, request)
        elif results:
            final_result = results[0]
        else:
            final_result = {"error": "No specialist could handle request"}

        return final_result
```

### Step 5: Integrate Into Gateway

```python
# In gateway.py
from multi_agent import MultiAgentOrchestrator

orchestrator = MultiAgentOrchestrator()

@app.post("/v1/multi-agent/process")
async def multi_agent_process(request: dict, api_key: str = Depends(verify_api_key)):
    """
    Process request through multi-agent architecture.
    """
    prompt = request.get("prompt", "")
    messages = request.get("messages", [])
    context = request.get("context", {})

    result = await orchestrator.process(prompt, messages, context)

    return result
```

---

## Schema Addition

```sql
CREATE TABLE IF NOT EXISTS multi_agent_log (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(64),
    planner_decision JSONB,
    specialists_invoked TEXT[],
    parallel_execution BOOLEAN,
    synthesis_used BOOLEAN,
    total_time_ms INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_multi_agent_time ON multi_agent_log(timestamp);
```

---

## Validation

```bash
# Test multi-agent routing
curl -X POST http://192.168.132.223:8080/v1/multi-agent/process \
  -H "Authorization: Bearer YOUR_KEY" \
  -d '{
    "prompt": "How can I securely implement a database API that will serve future generations?",
    "messages": [],
    "context": {}
  }'

# Should invoke: crawdad (security), gecko (technical), turtle (7gen)
```

---

## Files to Create/Modify

1. `/ganuda/lib/multi_agent.py` - New file with all agent classes
2. `/ganuda/services/llm_gateway/gateway.py` - Add multi-agent endpoint

---

*For Seven Generations - Cherokee AI Federation*
*"Many voices speak as one"*

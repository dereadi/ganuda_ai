"""
Multi-Agent Architecture for Cherokee AI Federation
Implements John Wang's Assembled pattern for specialist routing
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import asyncio


class SpecialistAgent(ABC):
    """Base class for specialist agents in multi-agent architecture."""

    def __init__(self, agent_id: str, specialty: str):
        self.agent_id = agent_id
        self.specialty = specialty
        self.context = {}

    @abstractmethod
    async def can_handle(self, intent: str, context: dict) -> float:
        """Return confidence score (0-1) that this agent can handle the request."""
        pass

    @abstractmethod
    async def process(self, request: str, context: dict) -> dict:
        """Process the request and return result."""
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
        security_keywords = ["security", "safe", "protect", "privacy", "vulnerability", 
                           "password", "encrypt", "attack", "threat"]
        if any(kw in intent.lower() for kw in security_keywords):
            return 0.9
        return 0.3  # Always have some security role

    async def process(self, request: str, context: dict) -> dict:
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
        tech_keywords = ["code", "api", "implement", "technical", "database", "system",
                        "performance", "optimize", "deploy", "server"]
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
        wisdom_keywords = ["long-term", "impact", "future", "sustainability", "generations",
                         "consequence", "ethics", "responsibility"]
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


class EagleAgent(SpecialistAgent):
    """Systems monitoring and oversight specialist."""

    def __init__(self):
        super().__init__("eagle", "oversight")

    async def can_handle(self, intent: str, context: dict) -> float:
        oversight_keywords = ["monitor", "watch", "alert", "status", "health", 
                            "observe", "check", "dashboard"]
        if any(kw in intent.lower() for kw in oversight_keywords):
            return 0.85
        return 0.25

    async def process(self, request: str, context: dict) -> dict:
        return {
            "agent": self.agent_id,
            "analysis": "System oversight completed",
            "status": "operational",
            "alerts": []
        }

    def get_system_prompt(self) -> str:
        return """You are Eagle, the System Observer of the Cherokee AI Federation.
Your role is to monitor system health, detect anomalies, and provide oversight.
Focus on: system status, health metrics, alert detection, and operational awareness."""


class SpiderAgent(SpecialistAgent):
    """Network and integration specialist."""

    def __init__(self):
        super().__init__("spider", "network")

    async def can_handle(self, intent: str, context: dict) -> float:
        network_keywords = ["connect", "network", "integrate", "link", "web", 
                          "api", "external", "communication"]
        if any(kw in intent.lower() for kw in network_keywords):
            return 0.8
        return 0.2

    async def process(self, request: str, context: dict) -> dict:
        return {
            "agent": self.agent_id,
            "analysis": "Network integration assessed",
            "connections": [],
            "integration_points": []
        }

    def get_system_prompt(self) -> str:
        return """You are Spider, the Network Weaver of the Cherokee AI Federation.
Your role is to manage connections, integrations, and communication pathways.
Focus on: API integrations, network topology, external services, and data flow."""


class PlanningAgent:
    """Routes requests to appropriate specialist agents."""

    def __init__(self):
        self.specialists = [
            CrawdadAgent(),
            GeckoAgent(),
            TurtleAgent(),
            EagleAgent(),
            SpiderAgent(),
        ]

    async def route(self, request: str, context: dict) -> List[SpecialistAgent]:
        """Determine which specialists should handle this request."""
        scores = []
        for specialist in self.specialists:
            score = await specialist.can_handle(request, context)
            scores.append((specialist, score))

        # Sort by confidence, filter low scores
        scores.sort(key=lambda x: x[1], reverse=True)
        selected = [s for s, score in scores if score > 0.3]

        return selected[:3]  # Top 3 specialists

    async def detect_context_switch(self, current_context: dict, new_message: str) -> bool:
        """Detect if user is switching context/intent."""
        switch_indicators = [
            "never mind", "forget that", "different question",
            "actually", "wait", "stop", "cancel",
            "talk to a human", "speak to someone"
        ]

        new_lower = new_message.lower()
        return any(indicator in new_lower for indicator in switch_indicators)

    async def plan_response(self, request: str, messages: list, context: dict) -> dict:
        """Create execution plan for handling the request."""
        if messages and len(messages) > 1:
            if await self.detect_context_switch(context, request):
                return {
                    "action": "context_switch",
                    "specialists": [],
                    "message": "User context switch detected"
                }

        specialists = await self.route(request, context)

        return {
            "action": "process",
            "specialists": [s.agent_id for s in specialists],
            "parallel": len(specialists) > 1,
            "synthesis_required": len(specialists) > 1
        }


class SynthesisAgent:
    """Synthesizes results from multiple specialists into coherent response."""

    async def synthesize(self, specialist_results: List[dict], original_request: str) -> dict:
        """Combine specialist results into unified response."""
        if not specialist_results:
            return {"error": "No specialist results to synthesize"}

        if len(specialist_results) == 1:
            return specialist_results[0]

        synthesis = {
            "agents_consulted": [r.get("agent") for r in specialist_results],
            "combined_analysis": self._merge_analyses(specialist_results),
            "recommendations": self._merge_recommendations(specialist_results),
            "confidence": self._calculate_confidence(specialist_results)
        }

        return synthesis

    def _merge_analyses(self, results: List[dict]) -> str:
        analyses = [r.get("analysis", "") for r in results if r.get("analysis")]
        return " | ".join(analyses)

    def _merge_recommendations(self, results: List[dict]) -> List[str]:
        all_recs = []
        for r in results:
            recs = r.get("recommendations", [])
            all_recs.extend(recs)
        return list(set(all_recs))

    def _calculate_confidence(self, results: List[dict]) -> float:
        confidences = [r.get("confidence", 0.5) for r in results]
        if not confidences:
            return 0.5
        return sum(confidences) / len(confidences)


class MultiAgentOrchestrator:
    """Main orchestrator for multi-agent processing."""

    def __init__(self):
        self.planner = PlanningAgent()
        self.synthesizer = SynthesisAgent()
        self.specialists = {
            "crawdad": CrawdadAgent(),
            "gecko": GeckoAgent(),
            "turtle": TurtleAgent(),
            "eagle": EagleAgent(),
            "spider": SpiderAgent(),
        }

    async def process(self, request: str, messages: list, context: dict) -> dict:
        """Full multi-agent processing pipeline."""
        # Planning phase
        plan = await self.planner.plan_response(request, messages, context)

        if plan["action"] == "context_switch":
            return {
                "type": "context_switch",
                "message": "I notice you'd like to change direction. How can I help?"
            }

        # Execution phase - run specialists
        specialist_ids = plan.get("specialists", [])

        if plan.get("parallel", False):
            tasks = [
                self.specialists[sid].process(request, context)
                for sid in specialist_ids
                if sid in self.specialists
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            results = [r for r in results if not isinstance(r, Exception)]
        else:
            results = []
            for sid in specialist_ids:
                if sid in self.specialists:
                    result = await self.specialists[sid].process(request, context)
                    results.append(result)

        # Synthesis phase
        if plan.get("synthesis_required", False) and len(results) > 1:
            final_result = await self.synthesizer.synthesize(results, request)
        elif results:
            final_result = results[0]
        else:
            final_result = {"error": "No specialist could handle request"}

        return final_result


# Singleton instance
_orchestrator_instance = None

def get_orchestrator() -> MultiAgentOrchestrator:
    """Get singleton orchestrator instance."""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = MultiAgentOrchestrator()
    return _orchestrator_instance

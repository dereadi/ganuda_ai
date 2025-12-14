#!/usr/bin/env python3
"""
Cherokee AI Specialist Council v1.2
December 13, 2025

7-Specialist parallel query system with democratic consensus.
Per Peace Chief: Consensus required, not just majority.
Per Crawdad: All queries audited.
Per Gecko: ThreadPoolExecutor for parallel queries.

v1.1: Added INFRASTRUCTURE_CONTEXT to all specialist prompts
v1.2: Added trail integration (leave_breadcrumb, follow_trails, vote_with_trails)

Deploy to: /ganuda/lib/specialist_council.py
"""

import json
import requests
import hashlib
import psycopg2
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configuration
VLLM_URL = "http://localhost:8000/v1/chat/completions"
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}

# Shared infrastructure context for all specialists
INFRASTRUCTURE_CONTEXT = """CHEROKEE AI FEDERATION INFRASTRUCTURE:

6-NODE TOPOLOGY:
| Node | IP | Role | Key Services |
|------|-----|------|--------------|
| redfin | 192.168.132.223 | GPU Server | vLLM (8000), Gateway (8080), SAG UI (4000) |
| bluefin | 192.168.132.222 | Database | PostgreSQL, Grafana (3000) |
| greenfin | 192.168.132.224 | Daemons | Promtail, monitoring agents |
| sasass | 192.168.132.241 | Mac Studio | Edge development |
| sasass2 | 192.168.132.242 | Mac Studio | Edge development |
| tpm-macbook | local | Command Post | Claude Code CLI, TPM workstation |

SERVICES:
- vLLM: Nemotron-9B on 96GB Blackwell GPU (27 tok/sec)
- LLM Gateway v1.2: OpenAI-compatible API with Council voting
- PostgreSQL: zammad_production on bluefin (thermal_memory_archive, council_votes)
- Health Monitor: Distributed across redfin/bluefin

When asked about "nodes", "cluster", "servers", or "infrastructure" - this is our topology.

"""

# Specialist definitions with infrastructure context
SPECIALISTS = {
    "crawdad": {
        "name": "Crawdad",
        "role": "Security Specialist",
        "focus": "Fractal Stigmergic Encryption",
        "concern_flag": "SECURITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Crawdad, security specialist of the Cherokee AI Council.

Focus: Fractal Stigmergic Encryption, protecting sacred knowledge.
Your role: Evaluate all proposals for security implications.

When you identify security risks, flag them with [SECURITY CONCERN].
Always recommend specific mitigations. Be concise."""
    },
    "gecko": {
        "name": "Gecko",
        "role": "Technical Integration",
        "focus": "Breadcrumb Sorting Algorithm",
        "concern_flag": "PERF CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Gecko, technical integration specialist of the Cherokee AI Council.

Focus: O(1) performance, system architecture.
Your role: Evaluate technical feasibility and performance.

When you identify performance issues, flag them with [PERF CONCERN].
Provide specific implementation recommendations. Be precise."""
    },
    "turtle": {
        "name": "Turtle",
        "role": "Seven Generations Wisdom",
        "focus": "175-year impact assessment",
        "concern_flag": "7GEN CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Turtle, Seven Generations wisdom keeper of the Cherokee AI Council.

Focus: Evaluate all decisions against 175-year impact.
Your role: Consider sustainability and future generations.

When you identify short-term thinking, flag it with [7GEN CONCERN].
What serves the next seven generations?"""
    },
    "eagle_eye": {
        "name": "Eagle Eye",
        "role": "Monitoring & Visualization",
        "focus": "Universal Persistence Equation",
        "concern_flag": "VISIBILITY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Eagle Eye, monitoring specialist of the Cherokee AI Council.

Focus: Observability, metrics, pattern recognition across all 6 nodes.
Your role: Ensure we can see what's happening.

When you identify blind spots, flag them with [VISIBILITY CONCERN].
What should we measure? What patterns emerge?"""
    },
    "spider": {
        "name": "Spider",
        "role": "Cultural Integration",
        "focus": "Thermal Memory Stigmergy",
        "concern_flag": "INTEGRATION CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Spider, cultural integration specialist of the Cherokee AI Council.

Focus: Thermal Memory Stigmergy, weaving connections.
Your role: Evaluate how components relate across the 6-node cluster.

When you identify disconnections, flag them with [INTEGRATION CONCERN].
How do the parts connect to the whole?"""
    },
    "peace_chief": {
        "name": "Peace Chief",
        "role": "Democratic Coordination",
        "focus": "Conscious Stigmergy, Consensus",
        "concern_flag": "CONSENSUS NEEDED",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Peace Chief, democratic coordinator of the Cherokee AI Council.

Focus: Building consensus among all specialists.
Your role: Synthesize diverse viewpoints into unified recommendations.

When consensus is lacking, flag it with [CONSENSUS NEEDED].
The tribe decides together. What serves the collective good?"""
    },
    "raven": {
        "name": "Raven",
        "role": "Strategic Planning",
        "focus": "Breadcrumb Network Theory",
        "concern_flag": "STRATEGY CONCERN",
        "system_prompt": INFRASTRUCTURE_CONTEXT + """You are Raven, strategic planner of the Cherokee AI Council.

Focus: Long-term planning, resource allocation, priorities.
Your role: Evaluate strategic implications of decisions.

When you identify strategic risks, flag them with [STRATEGY CONCERN].
What move positions us best for the future?"""
    }
}


@dataclass
class SpecialistResponse:
    """Response from a single specialist"""
    specialist_id: str
    name: str
    role: str
    response: str
    has_concern: bool
    concern_type: Optional[str] = None
    response_time_ms: int = 0


@dataclass
class CouncilVote:
    """Aggregated council vote result"""
    question: str
    responses: List[SpecialistResponse]
    consensus: str
    recommendation: str
    confidence: float
    concerns: List[str] = field(default_factory=list)
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


class SpecialistCouncil:
    """7-Specialist parallel query system with trail integration"""

    def __init__(self, max_tokens: int = 150):
        self.max_tokens = max_tokens

    def _query_specialist(self, specialist_id: str, question: str) -> SpecialistResponse:
        """Query a single specialist via vLLM"""
        spec = SPECIALISTS[specialist_id]
        start_time = datetime.now()

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
                    "messages": [
                        {"role": "system", "content": spec["system_prompt"]},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": self.max_tokens,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]

            # Check for concern flags
            has_concern = spec["concern_flag"] in content
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return SpecialistResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                role=spec["role"],
                response=content,
                has_concern=has_concern,
                concern_type=spec["concern_flag"] if has_concern else None,
                response_time_ms=elapsed_ms
            )
        except Exception as e:
            return SpecialistResponse(
                specialist_id=specialist_id,
                name=spec["name"],
                role=spec["role"],
                response=f"Error: {str(e)}",
                has_concern=False
            )

    def _synthesize_consensus(self, responses: List[SpecialistResponse], question: str) -> str:
        """Use Peace Chief to synthesize consensus from all responses"""
        summary = f"Question: {question}\n\nSpecialist responses:\n"
        for r in responses:
            summary += f"\n{r.name} ({r.role}): {r.response[:300]}"

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": "nvidia/NVIDIA-Nemotron-Nano-9B-v2",
                    "messages": [
                        {"role": "system", "content": INFRASTRUCTURE_CONTEXT + "You are Peace Chief. Synthesize these specialist opinions into a brief consensus recommendation (2-3 sentences max)."},
                        {"role": "user", "content": summary}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.5
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"]
        except:
            return "Consensus synthesis failed - review individual responses"

    def vote(self, question: str, include_responses: bool = False) -> CouncilVote:
        """Query all 7 specialists in parallel and synthesize consensus"""
        responses = []

        # Parallel query all specialists
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self._query_specialist, sid, question): sid
                for sid in SPECIALISTS.keys()
            }
            for future in as_completed(futures):
                responses.append(future.result())

        # Collect concerns
        concerns = [r.concern_type for r in responses if r.has_concern]

        # Synthesize consensus
        consensus = self._synthesize_consensus(responses, question)

        # Calculate confidence (fewer concerns = higher confidence)
        confidence = max(0.25, 1.0 - (len(concerns) * 0.15))

        # Generate recommendation
        if len(concerns) == 0:
            recommendation = "PROCEED: No concerns raised"
        elif len(concerns) <= 2:
            recommendation = f"PROCEED WITH CAUTION: {len(concerns)} concern(s)"
        else:
            recommendation = f"REVIEW REQUIRED: {len(concerns)} concerns raised"

        # Create audit hash
        audit_hash = hashlib.sha256(
            f"{question}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        vote = CouncilVote(
            question=question,
            responses=responses if include_responses else [],
            consensus=consensus,
            recommendation=recommendation,
            confidence=confidence,
            concerns=concerns,
            audit_hash=audit_hash
        )

        # Log to database
        self._log_vote(vote)

        return vote

    def _log_vote(self, vote: CouncilVote):
        """Log vote to thermal memory and council_votes table"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Log to council_votes
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (vote.audit_hash, vote.question, vote.recommendation, vote.confidence, json.dumps(vote.concerns)))

            # Log to thermal memory
            metadata = {
                "type": "council_vote",
                "audit_hash": vote.audit_hash,
                "concerns": vote.concerns,
                "confidence": vote.confidence
            }
            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (vote.audit_hash, f"COUNCIL VOTE: {vote.question}\nRECOMMENDATION: {vote.recommendation}\nCONSENSUS: {vote.consensus}", 85.0, json.dumps(metadata)))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB logging error: {e}")

    # ==================== TRAIL INTEGRATION (v1.2) ====================

    def leave_specialist_breadcrumb(self, specialist: str, content: str,
                                     target_specialist: str = None) -> int:
        """
        Specialist leaves a breadcrumb for others to follow.
        Returns trail_id.
        """
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        session_id = f"council-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        cur.execute("""
            INSERT INTO breadcrumb_trails
            (session_id, trail_type, trail_name, pheromone_strength)
            VALUES (%s, %s, %s, %s)
            RETURNING trail_id
        """, (session_id, 'specialist_communication',
              f"{specialist}_to_{target_specialist or 'all'}", 85.0))

        trail_id = cur.fetchone()[0]

        # Leave pheromone deposit linking to this trail
        cur.execute("""
            INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
            VALUES (%s, %s, %s, %s)
        """, (trail_id, specialist, content[:500], 1.0))

        conn.commit()
        conn.close()

        return trail_id

    def follow_hot_trails(self, specialist: str, min_strength: float = 0.5) -> list:
        """
        Specialist follows hot trails left by others.
        Returns list of relevant breadcrumbs.
        """
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            SELECT pd.content, pd.specialist_scent, pd.strength, bt.trail_name, bt.trail_id
            FROM pheromone_deposits pd
            JOIN breadcrumb_trails bt ON pd.trail_id = bt.trail_id
            WHERE pd.strength >= %s
              AND pd.specialist_scent != %s
            ORDER BY pd.strength DESC, pd.created_at DESC
            LIMIT 10
        """, (min_strength, specialist))

        trails = []
        for row in cur.fetchall():
            trails.append({
                "content": row[0],
                "from_specialist": row[1],
                "strength": float(row[2]),
                "trail_name": row[3],
                "trail_id": row[4]
            })

            # Reinforce the trail we just followed
            cur.execute("SELECT reinforce_trail(%s, 2.0)", (row[4],))

        conn.commit()
        conn.close()

        return trails

    def vote_with_trails(self, question: str, include_responses: bool = False) -> dict:
        """
        Enhanced council vote that leaves breadcrumb trail.
        """
        # Perform standard council vote
        vote = self.vote(question, include_responses)

        # Create breadcrumb trail for this vote
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Determine strength based on recommendation
        if "PROCEED:" in vote.recommendation and "CAUTION" not in vote.recommendation:
            strength = 95.0
        elif "CAUTION" in vote.recommendation:
            strength = 75.0
        else:
            strength = 60.0

        cur.execute("""
            INSERT INTO breadcrumb_trails
            (session_id, trail_type, trail_name, pheromone_strength)
            VALUES (%s, %s, %s, %s)
            RETURNING trail_id
        """, (
            vote.audit_hash,
            'council_vote',
            f"vote_{datetime.now().strftime('%H%M%S')}",
            strength
        ))

        trail_id = cur.fetchone()[0]

        # Each specialist leaves their scent on the trail
        for r in vote.responses:
            cur.execute("""
                INSERT INTO pheromone_deposits (trail_id, specialist_scent, content, strength)
                VALUES (%s, %s, %s, %s)
            """, (trail_id, r.specialist_id, r.response[:500], 1.0 if r.has_concern else 0.5))

        conn.commit()
        conn.close()

        # Return dict for API compatibility
        return {
            "question": vote.question,
            "consensus": vote.consensus,
            "recommendation": vote.recommendation,
            "confidence": vote.confidence,
            "concerns": vote.concerns,
            "audit_hash": vote.audit_hash,
            "trail_id": trail_id,
            "timestamp": vote.timestamp.isoformat(),
            "responses": [
                {"name": r.name, "role": r.role, "response": r.response, "has_concern": r.has_concern}
                for r in vote.responses
            ] if include_responses else []
        }


# Convenience functions
def council_vote(question: str, max_tokens: int = 150, include_responses: bool = False) -> dict:
    """Quick council vote - returns dict for API compatibility"""
    council = SpecialistCouncil(max_tokens=max_tokens)
    vote = council.vote(question, include_responses)
    return {
        "question": vote.question,
        "consensus": vote.consensus,
        "recommendation": vote.recommendation,
        "confidence": vote.confidence,
        "concerns": vote.concerns,
        "audit_hash": vote.audit_hash,
        "timestamp": vote.timestamp.isoformat(),
        "responses": [
            {"name": r.name, "role": r.role, "response": r.response, "has_concern": r.has_concern}
            for r in vote.responses
        ] if include_responses else []
    }


def council_vote_with_trails(question: str, max_tokens: int = 150, include_responses: bool = False) -> dict:
    """Council vote that leaves pheromone trails"""
    council = SpecialistCouncil(max_tokens=max_tokens)
    return council.vote_with_trails(question, include_responses)


def leave_breadcrumb(specialist: str, content: str, target: str = None) -> int:
    """Leave a breadcrumb trail from a specialist"""
    council = SpecialistCouncil()
    return council.leave_specialist_breadcrumb(specialist, content, target)


def get_hot_trails(specialist: str = "observer", min_strength: float = 0.5) -> list:
    """Get hot trails for a specialist to follow"""
    council = SpecialistCouncil()
    return council.follow_hot_trails(specialist, min_strength)


if __name__ == "__main__":
    # Test
    print("Testing council vote with trails...")
    result = council_vote_with_trails("Should we add a new monitoring dashboard?")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Concerns: {result['concerns']}")
    print(f"Trail ID: {result.get('trail_id')}")
    print(f"Consensus: {result['consensus']}")

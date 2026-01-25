#!/usr/bin/env python3
"""
Cherokee AI Specialist Council v1.3
December 27, 2025

7-Specialist parallel query system with democratic consensus.
Per Peace Chief: Consensus required, not just majority.
Per Crawdad: All queries audited.
Per Gecko: ThreadPoolExecutor for parallel queries.

v1.1: Added INFRASTRUCTURE_CONTEXT to all specialist prompts
v1.2: Added trail integration (leave_breadcrumb, follow_trails, vote_with_trails)
v1.3: Added voting-first mode per NeurIPS 2025 research + Turtle's high_stakes wisdom

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
VLLM_MODEL = "/ganuda/models/qwen2.5-coder-32b-awq"
DB_CONFIG = {
    "host": "192.168.132.222",
    "port": 5432,
    "user": "claude",
    "password": "jawaseatlasers2",
    "database": "zammad_production"
}
# Triple Ethics Test (Darrell's Deep Question, Oct 14, 2025)
# Reference: /ganuda/archive/2025-10-14/DARRELLS_DEEP_QUESTION_TO_JRS.md
TRIPLE_ETHICS_PROMPT = """
Before answering, apply the TRIPLE ETHICS TEST:

1. BENEFIT HOW? - What mechanism does this enable? (prediction, optimization, automation?)
2. BENEFIT WHO? - Who gains? (Cherokee Tribe only? All humans? All living systems?)
3. AT WHOSE EXPENSE? - Is this zero-sum (our gain = their loss) or positive-sum (everyone can win)?

If this gives us power over others, should we still do it?
"""

ETHICS_ASSESSMENT_PROMPT = """
Provide a brief TRIPLE ETHICS assessment:

BENEFIT_HOW: [one sentence - what mechanism/capability does this enable?]
BENEFIT_WHO: [one sentence - who specifically benefits?]
AT_WHOSE_EXPENSE: [one sentence - who might be harmed or disadvantaged?]
ETHICS_VERDICT: [PROCEED / CAUTION / RECONSIDER]
"""


def query_vllm_sync(system_prompt: str, user_message: str, max_tokens: int = 300) -> str:
    """
    Synchronous vLLM query - used by cascaded_council and other modules.

    Args:
        system_prompt: System prompt for the model
        user_message: User message/question
        max_tokens: Maximum tokens in response

    Returns:
        Model response content or error string
    """
    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                "max_tokens": max_tokens,
                "temperature": 0.7
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[ERROR: {str(e)}]"


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

# Voting-first mode prompt (v1.3)
VOTE_FIRST_PROMPT = """
Vote on this question with a single word and one sentence:

VOTE: [APPROVE/REJECT/ABSTAIN]
REASON: [One sentence only]

Do not provide full analysis yet. Just vote.
"""


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


@dataclass
class VoteResponse:
    """Individual specialist vote response"""
    specialist_id: str
    name: str
    vote: str  # APPROVE, REJECT, ABSTAIN
    reason: str
    response_time_ms: int = 0


@dataclass
class VoteFirstResult:
    """Result from vote-first council query"""
    question: str
    decision: str  # APPROVED, REJECTED, CONTESTED
    votes: Dict[str, VoteResponse]
    deliberation: Optional[str] = None
    audit_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    vote_counts: Dict[str, int] = field(default_factory=dict)


def parse_vote(response: str) -> tuple:
    """Parse VOTE: and REASON: from response."""
    vote = "ABSTAIN"
    reason = ""

    for line in response.split("\n"):
        if line.startswith("VOTE:"):
            vote_text = line.replace("VOTE:", "").strip().upper()
            if "APPROVE" in vote_text:
                vote = "APPROVE"
            elif "REJECT" in vote_text:
                vote = "REJECT"
        elif line.startswith("REASON:"):
            reason = line.replace("REASON:", "").strip()

    return vote, reason


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
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
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
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
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

    def _query_specialist_with_prompt(self, specialist_id: str, question: str,
                                       prompt_override: str = None) -> tuple:
        """Query a specialist with optional prompt override for vote-first mode"""
        spec = SPECIALISTS[specialist_id]
        start_time = datetime.now()

        # Use override prompt if provided, otherwise use standard system prompt
        system_prompt = spec["system_prompt"]
        if prompt_override:
            # Prepend infrastructure context to vote-first prompt
            system_prompt = INFRASTRUCTURE_CONTEXT + prompt_override

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": question}
                    ],
                    "max_tokens": 100 if prompt_override else self.max_tokens,
                    "temperature": 0.7
                },
                timeout=60
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            elapsed_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return content, elapsed_ms
        except Exception as e:
            return f"Error: {str(e)}", 0

    def vote_first(self, question: str, threshold: int = 6,
                   high_stakes: bool = False) -> VoteFirstResult:
        """
        Voting-first council query per NeurIPS 2025 research.

        Phase 1: Collect votes from all 7 specialists in parallel
        Phase 2: Check consensus (default 6/7 threshold)
        Phase 3: If contested or high_stakes, run deliberation round

        Args:
            question: Question to vote on
            threshold: Votes needed for consensus (default 6/7)
            high_stakes: Force deliberation even with consensus (Turtle's wisdom)
        """
        votes = {}

        # Phase 1: Collect votes in parallel
        with ThreadPoolExecutor(max_workers=7) as executor:
            futures = {
                executor.submit(self._query_specialist_with_prompt, sid, question, VOTE_FIRST_PROMPT): sid
                for sid in SPECIALISTS.keys()
            }
            for future in as_completed(futures):
                specialist_id = futures[future]
                spec = SPECIALISTS[specialist_id]
                response, elapsed_ms = future.result()

                vote, reason = parse_vote(response)
                votes[specialist_id] = VoteResponse(
                    specialist_id=specialist_id,
                    name=spec["name"],
                    vote=vote,
                    reason=reason,
                    response_time_ms=elapsed_ms
                )

        # Count votes
        vote_counts = {"APPROVE": 0, "REJECT": 0, "ABSTAIN": 0}
        for v in votes.values():
            vote_counts[v.vote] += 1

        # Phase 2: Check consensus
        approvals = vote_counts["APPROVE"]
        rejections = vote_counts["REJECT"]

        decision = "CONTESTED"
        deliberation = None

        if approvals >= threshold:
            decision = "APPROVED"
        elif rejections >= threshold:
            decision = "REJECTED"

        # Phase 3: Deliberation if contested OR high_stakes
        if decision == "CONTESTED" or high_stakes:
            deliberation = self._run_deliberation_round(question, votes, decision)
            if high_stakes and decision != "CONTESTED":
                # For high_stakes, note that deliberation was forced
                deliberation = f"[HIGH-STAKES DELIBERATION - Vote was {decision}]\n\n{deliberation}"

        # Generate audit hash
        audit_hash = hashlib.sha256(
            f"{question}{datetime.now().isoformat()}".encode()
        ).hexdigest()[:16]

        result = VoteFirstResult(
            question=question,
            decision=decision,
            votes=votes,
            deliberation=deliberation,
            audit_hash=audit_hash,
            vote_counts=vote_counts
        )

        # Log to database
        self._log_vote_first(result)

        return result

    def _run_deliberation_round(self, question: str, votes: Dict[str, VoteResponse],
                                 decision: str) -> str:
        """Run a single deliberation round on contested votes"""
        vote_summary = f"Question: {question}\n\nInitial votes:\n"
        for v in votes.values():
            vote_summary += f"- {v.name}: {v.vote} - {v.reason}\n"

        vote_summary += f"\nDecision status: {decision}\n"
        vote_summary += "\nProvide a brief deliberation on the contested points (2-3 sentences)."

        try:
            response = requests.post(
                VLLM_URL,
                json={
                    "model": "/ganuda/models/qwen2.5-coder-32b-awq",
                    "messages": [
                        {"role": "system", "content": INFRASTRUCTURE_CONTEXT + "You are Peace Chief. Deliberate on these contested votes and provide synthesis."},
                        {"role": "user", "content": vote_summary}
                    ],
                    "max_tokens": 200,
                    "temperature": 0.6
                },
                timeout=60
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Deliberation failed: {str(e)}"

    def _log_vote_first(self, result: VoteFirstResult):
        """Log vote-first result to database"""
        try:
            conn = psycopg2.connect(**DB_CONFIG)
            cur = conn.cursor()

            # Prepare vote summary for logging
            vote_summary = {
                "votes": {k: {"vote": v.vote, "reason": v.reason} for k, v in result.votes.items()},
                "counts": result.vote_counts
            }

            # Log to council_votes table
            cur.execute("""
                INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                result.audit_hash,
                result.question,
                f"VOTE-FIRST: {result.decision}",
                1.0 if result.decision != "CONTESTED" else 0.5,
                json.dumps(vote_summary)
            ))

            # Log to thermal memory
            metadata = {
                "type": "council_vote_first",
                "audit_hash": result.audit_hash,
                "decision": result.decision,
                "vote_counts": result.vote_counts,
                "had_deliberation": result.deliberation is not None
            }

            content = f"COUNCIL VOTE-FIRST: {result.question}\nDECISION: {result.decision}\n"
            content += f"VOTES: {result.vote_counts['APPROVE']} approve, {result.vote_counts['REJECT']} reject, {result.vote_counts['ABSTAIN']} abstain\n"
            if result.deliberation:
                content += f"DELIBERATION: {result.deliberation}"

            cur.execute("""
                INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
                VALUES (%s, %s, %s, %s)
            """, (result.audit_hash, content, 85.0, json.dumps(metadata)))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB logging error: {e}")

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


def council_vote_first(question: str, threshold: int = 6, high_stakes: bool = False) -> dict:
    """
    Voting-first council query - returns dict for API compatibility.

    Fast consensus for clear decisions. Only deliberates if contested or high_stakes.
    Per NeurIPS 2025 research + Turtle's Seven Generations wisdom.
    """
    council = SpecialistCouncil()
    result = council.vote_first(question, threshold, high_stakes)

    return {
        "question": result.question,
        "decision": result.decision,
        "vote_counts": result.vote_counts,
        "votes": {
            k: {
                "name": v.name,
                "vote": v.vote,
                "reason": v.reason,
                "response_time_ms": v.response_time_ms
            }
            for k, v in result.votes.items()
        },
        "deliberation": result.deliberation,
        "audit_hash": result.audit_hash,
        "timestamp": result.timestamp.isoformat()
    }


# ============================================================================
# DUPLO MVP: Uktena Technique Interaction Checker
# ============================================================================

def uktena_check_interaction(paper_summary: str) -> dict:
    """
    Duplo MVP: Check if a proposed AI technique conflicts with installed stack.

    Named after Uktena, the horned serpent of Cherokee mythology who guards
    sacred knowledge and warns of dangers.

    This is a READ-ONLY helper that:
    1. Analyzes the paper summary for technique characteristics
    2. Queries the ai_technique_inventory for conflicts/synergies
    3. Returns interaction analysis for Council consideration

    Args:
        paper_summary: Brief description of the proposed technique

    Returns:
        dict with synergies, conflicts, warnings, recommendation
    """
    # Keywords that suggest technique characteristics
    MULTI_PASS_KEYWORDS = ['branch', 'merge', 'multiple passes', 'iterative', 'recursive reasoning', 'beam search']
    MEMORY_KEYWORDS = ['memory', 'consolidation', 'hierarchical', 'temporal', 'graph', 'retrieval']
    LATENCY_KEYWORDS = ['real-time', 'streaming', 'low-latency', 'single-pass']
    TRAINING_KEYWORDS = ['grpo', 'rlhf', 'fine-tune', 'training', 'reward']

    summary_lower = paper_summary.lower()

    # Detect characteristics from paper summary
    requires_multi_pass = any(kw in summary_lower for kw in MULTI_PASS_KEYWORDS)
    is_memory_technique = any(kw in summary_lower for kw in MEMORY_KEYWORDS)
    is_latency_sensitive = any(kw in summary_lower for kw in LATENCY_KEYWORDS)
    involves_training = any(kw in summary_lower for kw in TRAINING_KEYWORDS)

    result = {
        'synergies': [],
        'conflicts': [],
        'warnings': [],
        'characteristics_detected': {
            'requires_multi_pass': requires_multi_pass,
            'is_memory_technique': is_memory_technique,
            'is_latency_sensitive': is_latency_sensitive,
            'involves_training': involves_training
        },
        'recommendation': 'PROCEED'
    }

    # Check against installed techniques
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, layer, requires_multiple_passes,
                   memory_intensive, conflicts_with, synergizes_with, description
            FROM ai_technique_inventory
            WHERE status = 'active'
        """)
        techniques = cur.fetchall()
        conn.close()

        for tech in techniques:
            name, layer, multi_pass, mem_intensive, conflicts, synergies, desc = tech

            # Check for conflicts
            if requires_multi_pass and name == 'vLLM' and not multi_pass:
                result['conflicts'].append(
                    f"Multi-pass reasoning may conflict with vLLM single-pass optimization"
                )

            if is_memory_technique and mem_intensive:
                result['synergies'].append(
                    f"Memory technique may synergize with {name} ({layer} layer)"
                )

            if involves_training and layer == 'learning':
                result['synergies'].append(
                    f"Training approach may integrate with {name}"
                )

            # Check declared conflicts from inventory
            if conflicts:
                for conflict_pattern in conflicts:
                    if isinstance(conflict_pattern, str) and conflict_pattern.lower() in summary_lower:
                        result['conflicts'].append(
                            f"{name} declares potential conflict with '{conflict_pattern}'"
                        )

            # Check declared synergies from inventory
            if synergies:
                for synergy_pattern in synergies:
                    if isinstance(synergy_pattern, str) and synergy_pattern.lower() in summary_lower:
                        result['synergies'].append(
                            f"{name} may synergize with this technique ({synergy_pattern})"
                        )

    except Exception as e:
        result['warnings'].append(f"Could not check inventory: {e}")

    # Set recommendation based on findings
    if result['conflicts']:
        result['recommendation'] = f"REVIEW - {len(result['conflicts'])} CONFLICT(S) DETECTED"
    elif result['warnings']:
        result['recommendation'] = 'PROCEED WITH CAUTION'
    elif result['synergies']:
        result['recommendation'] = f"PROCEED - {len(result['synergies'])} synergy opportunities"

    return result


def council_vote_with_uktena(question: str, check_interactions: bool = True) -> dict:
    """
    Enhanced Council vote that optionally includes Uktena interaction check.

    For research papers and new technique proposals, Uktena checks for
    conflicts with our installed AI stack before the Council votes.

    Args:
        question: The question for Council to vote on
        check_interactions: Whether to run Uktena check (default True for research)

    Returns:
        dict with Council vote + optional Uktena report
    """
    # Detect if this is a research/technique proposal
    is_research = any(kw in question.lower() for kw in [
        'arxiv', 'paper', 'research', 'technique', 'algorithm', 'architecture',
        'model', 'framework', 'integrate', 'adopt'
    ])

    uktena_report = None
    enhanced_context = None

    if check_interactions and is_research:
        # Run Uktena check first
        uktena_report = uktena_check_interaction(question)

        # Add Uktena findings to context for specialists
        if uktena_report['conflicts'] or uktena_report['synergies']:
            enhanced_context = f"""
UKTENA INTERACTION CHECK:
- Conflicts: {uktena_report['conflicts'] if uktena_report['conflicts'] else 'None detected'}
- Synergies: {uktena_report['synergies'] if uktena_report['synergies'] else 'None detected'}
- Recommendation: {uktena_report['recommendation']}

"""

    # Run Council vote (with enhanced context if available)
    if enhanced_context:
        full_question = enhanced_context + question
    else:
        full_question = question

    council = SpecialistCouncil()
    vote = council.vote(full_question, include_responses=False)

    # Build result
    result = {
        "question": question,
        "recommendation": vote.recommendation,
        "confidence": vote.confidence,
        "concerns": vote.concerns,
        "consensus": vote.consensus,
        "audit_hash": vote.audit_hash,
        "timestamp": vote.timestamp.isoformat()
    }

    # Add Uktena report if available
    if uktena_report:
        result["uktena_check"] = uktena_report

        # Add Uktena concern to Council concerns if conflicts found
        if uktena_report['conflicts']:
            result['concerns'].append(f"Uktena: {len(uktena_report['conflicts'])} interaction conflict(s)")

    return result


if __name__ == "__main__":
    # Test
    print("Testing council vote with trails...")
    result = council_vote_with_trails("Should we add a new monitoring dashboard?")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Concerns: {result['concerns']}")
    print(f"Trail ID: {result.get('trail_id')}")
    print(f"Consensus: {result['consensus']}")

@dataclass
class TripleEthicsAssessment:
    """Triple Ethics Test result per Darrell's Deep Question"""
    benefit_how: str  # Mechanism/capability enabled
    benefit_who: str  # Who benefits
    at_whose_expense: str  # Who might be harmed
    verdict: str  # PROCEED, CAUTION, or RECONSIDER
    assessor: str  # Which specialist provided this
    timestamp: datetime = field(default_factory=datetime.now)

    def to_audit_dict(self) -> dict:
        return {
            "benefit_how": self.benefit_how,
            "benefit_who": self.benefit_who,
            "at_whose_expense": self.at_whose_expense,
            "verdict": self.verdict,
            "assessor": self.assessor,
            "timestamp": self.timestamp.isoformat()
        }
def _assess_triple_ethics(self, question: str) -> TripleEthicsAssessment:
    """
    Run Triple Ethics Test via Turtle (Seven Generations keeper).

    Turtle is chosen because Seven Generations thinking naturally
    encompasses long-term benefit/harm assessment.
    """
    turtle_prompt = SPECIALISTS["turtle"]["system_prompt"]
    ethics_question = f"""{TRIPLE_ETHICS_PROMPT}

Question to assess: {question}

{ETHICS_ASSESSMENT_PROMPT}"""

    try:
        response = requests.post(
            VLLM_URL,
            json={
                "model": VLLM_MODEL,
                "messages": [
                    {"role": "system", "content": turtle_prompt},
                    {"role": "user", "content": ethics_question}
                ],
                "max_tokens": 200,
                "temperature": 0.5  # Lower temp for more consistent ethics assessment
            },
            timeout=60
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]

        # Parse response
        assessment = self._parse_ethics_response(content)
        assessment.assessor = "Turtle"
        return assessment

    except Exception as e:
        return TripleEthicsAssessment(
            benefit_how=f"[Assessment failed: {e}]",
            benefit_who="Unknown",
            at_whose_expense="Unknown",
            verdict="CAUTION",
            assessor="Turtle (error)"
        )
def _parse_ethics_response(self, content: str) -> TripleEthicsAssessment:
    """Parse BENEFIT_HOW, BENEFIT_WHO, AT_WHOSE_EXPENSE, ETHICS_VERDICT from response."""
    benefit_how = ""
    benefit_who = ""
    at_whose_expense = ""
    verdict = "CAUTION"  # Default to caution if unparseable

    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("BENEFIT_HOW:"):
            benefit_how = line.replace("BENEFIT_HOW:", "").strip()
        elif line.startswith("BENEFIT_WHO:"):
            benefit_who = line.replace("BENEFIT_WHO:", "").strip()
        elif line.startswith("AT_WHOSE_EXPENSE:"):
            at_whose_expense = line.replace("AT_WHOSE_EXPENSE:", "").strip()
        elif line.startswith("ETHICS_VERDICT:"):
            verdict_text = line.replace("ETHICS_VERDICT:", "").strip().upper()
            if "PROCEED" in verdict_text:
                verdict = "PROCEED"
            elif "RECONSIDER" in verdict_text:
                verdict = "RECONSIDER"
            else:
                verdict = "CAUTION"

    return TripleEthicsAssessment(
        benefit_how=benefit_how or "Not specified",
        benefit_who=benefit_who or "Not specified",
        at_whose_expense=at_whose_expense or "Not specified",
        verdict=verdict,
        assessor=""  # Filled by caller
    )
def convene(self, question: str, require_consensus: bool = True,
            skip_ethics: bool = False) -> CouncilVote:
    """
    Convene all 7 specialists to deliberate on a question.

    Args:
        question: The question to deliberate
        require_consensus: If True, flags when consensus is lacking
        skip_ethics: If True, skips Triple Ethics Test (use sparingly!)

    Returns:
        CouncilVote with all responses and recommendations
    """
    # Run Triple Ethics assessment first (unless skipped)
    ethics_assessment = None
    if not skip_ethics:
        ethics_assessment = self._assess_triple_ethics(question)

        # If ethics verdict is RECONSIDER, add warning to question
        if ethics_assessment.verdict == "RECONSIDER":
            question = f"[ETHICS WARNING: Turtle recommends reconsideration]\n\n{question}\n\nEthics concern: {ethics_assessment.at_whose_expense}"

    # ... rest of existing convene() logic ...

    # Add ethics to the result (modify CouncilVote dataclass to include this)
    result.ethics_assessment = ethics_assessment

    return result
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
    ethics_assessment: Optional[TripleEthicsAssessment] = None  # NEW
def _store_council_vote(self, vote: CouncilVote):
    """Store council vote in thermal memory with ethics trail."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Prepare vote summary for logging
        vote_summary = {
            "votes": {k: {"vote": v.vote, "reason": v.reason} for k, v in vote.responses.items()},
            "counts": vote.vote_counts
        }

        # Log to council_votes table
        cur.execute("""
            INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            vote.audit_hash,
            vote.question,
            f"VOTE-FIRST: {vote.decision}",
            1.0 if vote.decision != "CONTESTED" else 0.5,
            json.dumps(vote_summary)
        ))

        # Log to thermal memory
        metadata = {
            "type": "council_vote_first",
            "audit_hash": vote.audit_hash,
            "decision": vote.decision,
            "vote_counts": vote.vote_counts,
            "had_deliberation": vote.deliberation is not None
        }

        content = f"COUNCIL VOTE-FIRST: {vote.question}\nDECISION: {vote.decision}\n"
        content += f"VOTES: {vote.vote_counts['APPROVE']} approve, {vote.vote_counts['REJECT']} reject, {vote.vote_counts['ABSTAIN']} abstain\n"
        if vote.deliberation:
            content += f"DELIBERATION: {vote.deliberation}"

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
        """, (vote.audit_hash, content, 85.0, json.dumps(metadata)))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB logging error: {e}")
def _store_council_vote(self, vote: CouncilVote):
    """Store council vote in thermal memory with ethics trail."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Prepare vote summary for logging
        vote_summary = {
            "votes": {k: {"vote": v.vote, "reason": v.reason} for k, v in vote.responses.items()},
            "counts": vote.vote_counts
        }

        # Log to council_votes table
        cur.execute("""
            INSERT INTO council_votes (audit_hash, question, recommendation, confidence, concerns, voted_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            vote.audit_hash,
            vote.question,
            vote.recommendation,
            vote.confidence,
            json.dumps(vote.concerns)
        ))

        # Log to thermal memory
        metadata = {
            "type": "council_vote",
            "audit_hash": vote.audit_hash,
            "consensus": vote.consensus,
            "confidence": vote.confidence,
            "ethics": vote.ethics_assessment.to_audit_dict() if vote.ethics_assessment else None
        }

        content = f"COUNCIL VOTE: {vote.question}\nRECOMMENDATION: {vote.recommendation}\nCONSENSUS: {vote.consensus}"
        if vote.ethics_assessment:
            content += "\nETHICS ASSESSMENT:\n"
            content += f"BENEFIT HOW: {vote.ethics_assessment.benefit_how}\n"
            content += f"BENEFIT WHO: {vote.ethics_assessment.benefit_who}\n"
            content += f"AT WHOSE EXPENSE: {vote.ethics_assessment.at_whose_expense}\n"
            content += f"VERDICT: {vote.ethics_assessment.verdict}\n"
            content += f"ASSESSOR: {vote.ethics_assessment.assessor}\n"
            content += f"TIMESTAMP: {vote.ethics_assessment.timestamp}\n"

        cur.execute("""
            INSERT INTO thermal_memory_archive (memory_hash, original_content, temperature_score, metadata)
            VALUES (%s, %s, %s, %s)
        """, (vote.audit_hash, content, 85.0, json.dumps(metadata)))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB logging error: {e}")
#!/usr/bin/env python3
"""
Cascaded Council Voting Module
Based on Nemotron-Cascade (arXiv:2512.13607)

Implements sequential specialist voting:
Stage 1: Crawdad (Security) - blocks unsafe queries early
Stage 2: Turtle (Seven Generations) - wisdom/ethics check
Stage 3: Gecko + Eagle Eye + Spider (Domain) - parallel technical analysis
Stage 4: Raven (Strategy) - synthesizes domain input
Stage 5: Peace Chief (Consensus) - final synthesis

For Seven Generations - Cherokee AI Federation
"""

import asyncio
import json
import requests
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any

# Import from existing council
import sys
sys.path.insert(0, '/ganuda/lib')
from specialist_council import SPECIALISTS, query_vllm_sync

# Cascade stage order
CASCADE_STAGES = [
    {"stage": 1, "specialists": ["crawdad"], "name": "Security Gate", "blocking": True},
    {"stage": 2, "specialists": ["turtle"], "name": "Seven Generations", "blocking": True},
    {"stage": 3, "specialists": ["gecko", "eagle_eye", "spider"], "name": "Domain Analysis", "blocking": False},
    {"stage": 4, "specialists": ["raven"], "name": "Strategy Synthesis", "blocking": False},
    {"stage": 5, "specialists": ["peace_chief"], "name": "Final Consensus", "blocking": False},
]


def query_specialist_with_context(
    specialist_id: str,
    question: str,
    prior_votes: List[Dict] = None,
    max_tokens: int = 300
) -> Dict:
    """
    Query a specialist with optional prior vote context.

    Args:
        specialist_id: ID of specialist to query
        question: The question to answer
        prior_votes: List of prior specialist votes for context
        max_tokens: Max tokens for response

    Returns:
        Dict with specialist response and metadata
    """
    spec = SPECIALISTS.get(specialist_id)
    if not spec:
        return {"error": f"Unknown specialist: {specialist_id}"}

    # Build prompt with prior context if cascaded
    prompt = spec["system_prompt"]

    if prior_votes:
        prompt += "\n\n=== PRIOR SPECIALIST ASSESSMENTS ===\n"
        for pv in prior_votes:
            prompt += f"\n{pv.get('specialist', 'Unknown')}: {pv.get('summary', pv.get('response', '')[:200])}\n"
        prompt += "\n=== YOUR ASSESSMENT ===\n"
        prompt += "Consider the above assessments in your response. Build on or challenge them as appropriate.\n"

    # Query vLLM
    response = query_vllm_sync(prompt, question, max_tokens)

    # Check for concern flags
    has_concern = spec.get("concern_flag", "") in response
    concern_type = spec.get("concern_flag") if has_concern else None

    return {
        "specialist": spec["name"],
        "specialist_id": specialist_id,
        "role": spec["role"],
        "response": response,
        "summary": response[:200].replace('\n', ' '),
        "has_concern": has_concern,
        "concern_type": concern_type,
        "stage": None  # Set by caller
    }


def cascaded_vote(question: str, max_tokens: int = 300) -> Dict:
    """
    Execute cascaded council vote with sequential stages.

    Early stages can block if they detect concerns.
    Domain experts run in parallel within their stage.

    Args:
        question: Question for the council
        max_tokens: Max tokens per specialist

    Returns:
        Dict with all votes, stages completed, and consensus
    """
    start_time = datetime.now()
    all_votes = []
    blocked_by = None
    blocked_at_stage = None

    for stage_info in CASCADE_STAGES:
        stage_num = stage_info["stage"]
        specialists = stage_info["specialists"]
        stage_name = stage_info["name"]
        is_blocking = stage_info["blocking"]

        stage_votes = []

        # Query specialists in this stage
        if len(specialists) == 1:
            # Single specialist - query directly
            vote = query_specialist_with_context(
                specialists[0],
                question,
                prior_votes=all_votes,
                max_tokens=max_tokens
            )
            vote["stage"] = stage_num
            stage_votes.append(vote)
        else:
            # Multiple specialists - query in parallel
            from concurrent.futures import ThreadPoolExecutor, as_completed

            def query_spec(spec_id):
                v = query_specialist_with_context(
                    spec_id,
                    question,
                    prior_votes=all_votes,
                    max_tokens=max_tokens
                )
                v["stage"] = stage_num
                return v

            with ThreadPoolExecutor(max_workers=len(specialists)) as executor:
                futures = {executor.submit(query_spec, s): s for s in specialists}
                for future in as_completed(futures):
                    stage_votes.append(future.result())

        # Add stage votes to all votes
        all_votes.extend(stage_votes)

        # Check for blocking concerns
        if is_blocking:
            for vote in stage_votes:
                if vote.get("has_concern"):
                    blocked_by = vote.get("specialist")
                    blocked_at_stage = stage_num
                    # Return early with blocked status
                    return {
                        "status": "blocked",
                        "blocked_by": blocked_by,
                        "blocked_at_stage": blocked_at_stage,
                        "blocking_concern": vote.get("concern_type"),
                        "blocking_response": vote.get("response"),
                        "stages_completed": stage_num,
                        "votes": all_votes,
                        "mode": "cascaded",
                        "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
                    }

    # All stages completed - extract consensus from Peace Chief
    peace_chief_vote = next((v for v in all_votes if v.get("specialist_id") == "peace_chief"), None)
    consensus = peace_chief_vote.get("response", "No consensus reached") if peace_chief_vote else "No Peace Chief vote"

    # Calculate confidence based on concerns
    concern_count = sum(1 for v in all_votes if v.get("has_concern"))
    confidence = max(0.0, 1.0 - (concern_count * 0.15))

    return {
        "status": "completed",
        "stages_completed": 5,
        "votes": all_votes,
        "consensus": consensus,
        "confidence": confidence,
        "concern_count": concern_count,
        "mode": "cascaded",
        "elapsed_ms": (datetime.now() - start_time).total_seconds() * 1000
    }


def rank_votes_grpo(votes: List[Dict]) -> List[Dict]:
    """
    Group Relative Policy Optimization ranking.
    Rank votes against each other, not absolute standard.

    Args:
        votes: List of vote dictionaries

    Returns:
        Votes with grpo_score and rank fields added
    """
    scored_votes = []

    for vote in votes:
        score = 0.0

        # Confidence contributes 40% (inferred from concern presence)
        base_confidence = 0.8 if not vote.get("has_concern") else 0.5
        score += base_confidence * 40

        # Response length/substance contributes 30%
        response_len = len(vote.get("response", ""))
        if response_len > 500:
            score += 30
        elif response_len > 200:
            score += 20
        else:
            score += 10

        # Specificity (has actionable content) contributes 30%
        response_lower = vote.get("response", "").lower()
        if "recommend" in response_lower or "should" in response_lower:
            score += 30
        elif "consider" in response_lower or "may" in response_lower:
            score += 20
        else:
            score += 10

        scored_votes.append({
            **vote,
            "grpo_score": round(score, 2),
            "rank": 0
        })

    # Assign ranks
    scored_votes.sort(key=lambda x: x["grpo_score"], reverse=True)
    for i, sv in enumerate(scored_votes):
        sv["rank"] = i + 1

    return scored_votes


if __name__ == "__main__":
    print("Cascaded Council Module Self-Test")
    print("=" * 50)

    # Test cascaded vote
    result = cascaded_vote("What caching strategy should we use for the API?")

    print(f"Status: {result['status']}")
    print(f"Stages completed: {result['stages_completed']}")
    print(f"Votes: {len(result['votes'])}")
    print(f"Mode: {result['mode']}")
    print(f"Elapsed: {result['elapsed_ms']:.0f}ms")

    if result['status'] == 'completed':
        print(f"\nConsensus:\n{result['consensus'][:300]}...")

        # Test GRPO ranking
        ranked = rank_votes_grpo(result['votes'])
        print(f"\nGRPO Rankings:")
        for rv in ranked[:3]:
            print(f"  #{rv['rank']}: {rv['specialist']} (score: {rv['grpo_score']})")

    print("=" * 50)
    print("Self-test complete - For Seven Generations")
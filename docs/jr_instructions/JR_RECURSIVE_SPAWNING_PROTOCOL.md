# Jr Instructions: Recursive Spawning Protocol for Council Decisions

**Date:** January 4, 2026
**Priority:** HIGH
**Council Decision:** APPROVED (85% confidence, Data Chief)
**Research Basis:** MIT RLM Paper (arXiv:2512.24601)

---

## Executive Summary

This document formalizes a **Recursive Spawning Protocol** for Cherokee AI Federation Council decisions. Based on MIT's Recursive Language Models research, this protocol allows Chiefs to spawn sub-Chiefs for complex decisions, implementing depth-limited recursion with structured result aggregation.

**Key Insight from RLM Research:** Context Rot degrades reasoning as token count increases. Fresh model spawns with focused context outperform context-stuffed single instances by orders of magnitude.

---

## Protocol Architecture

### Conceptual Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    COUNCIL QUERY (Depth 0)                       │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐                   │
│  │ IT Chief │    │Data Chief│    │Ops Chief │                   │
│  │ (Root)   │    │ (Root)   │    │ (Root)   │                   │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘                   │
│       │               │               │                          │
│       │ Complex?      │ Complex?      │ Complex?                 │
│       │               │               │                          │
│       ▼               ▼               ▼                          │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                 RECURSIVE SPAWN (Depth 1)                    ││
│  │                                                              ││
│  │   IT Chief spawns:          Data Chief spawns:              ││
│  │   ├─ Security Sub-Chief     ├─ Schema Sub-Chief             ││
│  │   ├─ Infra Sub-Chief        ├─ Pipeline Sub-Chief           ││
│  │   └─ Network Sub-Chief      └─ Archive Sub-Chief            ││
│  │                                                              ││
│  │   Each sub-chief:                                           ││
│  │   1. Receives FOCUSED subset of context                     ││
│  │   2. Fresh model instance (no context rot)                  ││
│  │   3. Returns structured response to parent                  ││
│  │   4. Parent aggregates into final vote                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   AGGREGATION (Depth 0)                    │  │
│  │   Chiefs collect sub-chief responses                       │  │
│  │   Synthesize into APPROVE/REJECT/ABSTAIN vote              │  │
│  │   Include confidence % based on sub-chief agreement        │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Depth Limits

| Phase | Max Depth | Rationale |
|-------|-----------|-----------|
| Initial Implementation | 1 | Validate pattern, measure costs |
| After 30 days validation | 2 | If metrics show benefit |
| Future consideration | 3 | Only for truly complex decisions |

**Hard Limit:** depth ≤ 3 (prevents runaway recursion)

---

## Implementation Specification

### 1. Complexity Detector

Before spawning, a Chief must determine if the query is complex enough to warrant recursion.

```python
class ComplexityDetector:
    """
    Determines if a query warrants recursive decomposition.
    Uses heuristics, not the model itself (to avoid context rot in assessment).
    """

    COMPLEXITY_THRESHOLDS = {
        "token_count": 500,           # Query tokens
        "domain_count": 2,            # Number of distinct domains touched
        "decision_factors": 3,        # Number of factors to weigh
        "uncertainty_keywords": [     # Phrases suggesting complexity
            "trade-off", "depends on", "multiple approaches",
            "several factors", "considering", "weighing"
        ]
    }

    @staticmethod
    def is_complex(query: str, context: dict = None) -> tuple[bool, list[str]]:
        """
        Returns:
            (should_spawn: bool, recommended_sub_chiefs: list[str])
        """
        score = 0
        reasons = []

        # Token count heuristic
        token_estimate = len(query.split()) * 1.3
        if token_estimate > ComplexityDetector.COMPLEXITY_THRESHOLDS["token_count"]:
            score += 1
            reasons.append("query_length")

        # Keyword detection
        query_lower = query.lower()
        keyword_hits = sum(
            1 for kw in ComplexityDetector.COMPLEXITY_THRESHOLDS["uncertainty_keywords"]
            if kw in query_lower
        )
        if keyword_hits >= 2:
            score += 1
            reasons.append("complexity_keywords")

        # Domain detection (simple heuristic)
        domains = []
        if any(w in query_lower for w in ["security", "auth", "encrypt", "permission"]):
            domains.append("security")
        if any(w in query_lower for w in ["database", "schema", "storage", "query"]):
            domains.append("data")
        if any(w in query_lower for w in ["network", "api", "endpoint", "latency"]):
            domains.append("network")
        if any(w in query_lower for w in ["cost", "budget", "resource", "memory"]):
            domains.append("resources")

        if len(domains) >= 2:
            score += 1
            reasons.append(f"multi_domain:{domains}")

        should_spawn = score >= 2
        return should_spawn, domains if should_spawn else []
```

### 2. Recursive Chief Base Class

```python
#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Recursive Chief Implementation
Implements depth-limited recursive spawning per RLM research.
"""

import requests
import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

# Gateway configuration
GATEWAY_URL = "http://localhost:8080/v1/chat/completions"
GATEWAY_MODEL = "qwen3-32b"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

# Recursion limits
MAX_RECURSION_DEPTH = 1  # Start conservative, increase after validation
MAX_SUB_CHIEFS = 4       # Max sub-chiefs per parent


class Vote(Enum):
    APPROVE = "APPROVE"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"


@dataclass
class ChiefResponse:
    """Structured response from a Chief or Sub-Chief"""
    vote: Vote
    confidence: float  # 0.0 to 1.0
    reasoning: str
    sub_responses: Optional[List["ChiefResponse"]] = None
    depth: int = 0
    chief_id: str = ""


class RecursiveChiefBase(ABC):
    """
    Base class for Chiefs with recursive spawning capability.

    Key RLM principles implemented:
    1. Context as environment - sub-chiefs get focused context, not full history
    2. Fresh spawns - each sub-chief is a new Gateway call (no context rot)
    3. Structured aggregation - parent synthesizes sub-chief responses
    """

    def __init__(self, chief_name: str, domain: str, depth: int = 0):
        self.chief_name = chief_name
        self.domain = domain
        self.depth = depth
        self.complexity_detector = ComplexityDetector()

    def _call_gateway(self, messages: List[Dict], max_tokens: int = 300) -> str:
        """Fresh spawn via Gateway API - no shared context between calls."""
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        }
        payload = {
            "model": GATEWAY_MODEL,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7
        }
        try:
            response = requests.post(GATEWAY_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"[Gateway Error: {e}]"

    @abstractmethod
    def get_sub_chief_configs(self) -> List[Dict[str, str]]:
        """
        Define available sub-chiefs for this chief type.
        Returns list of {"name": str, "domain": str, "system_prompt": str}
        """
        pass

    def spawn_sub_chief(
        self,
        name: str,
        system_prompt: str,
        query: str,
        focused_context: str
    ) -> ChiefResponse:
        """
        Spawn a sub-chief with focused context.

        This is the core RLM principle: instead of stuffing all context into one call,
        we spawn a fresh instance with just the relevant subset.
        """
        messages = [
            {
                "role": "system",
                "content": f"{system_prompt}\n\nRespond with:\n1. VOTE: APPROVE/REJECT/ABSTAIN\n2. CONFIDENCE: 0-100%\n3. REASONING: Brief explanation (under 100 words)"
            },
            {
                "role": "user",
                "content": f"CONTEXT:\n{focused_context}\n\nQUESTION:\n{query}"
            }
        ]

        response_text = self._call_gateway(messages, max_tokens=200)

        # Parse response
        vote = Vote.ABSTAIN
        confidence = 0.5
        reasoning = response_text

        response_upper = response_text.upper()
        if "APPROVE" in response_upper:
            vote = Vote.APPROVE
        elif "REJECT" in response_upper:
            vote = Vote.REJECT

        # Extract confidence percentage
        import re
        conf_match = re.search(r'(\d+)%', response_text)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100.0

        return ChiefResponse(
            vote=vote,
            confidence=confidence,
            reasoning=reasoning,
            depth=self.depth + 1,
            chief_id=f"{self.chief_name}::{name}"
        )

    def decompose_context(self, query: str, full_context: str, domains: List[str]) -> Dict[str, str]:
        """
        Decompose context into domain-specific subsets.

        RLM principle: Models should programmatically examine and partition context,
        not receive it all at once.
        """
        # Simple heuristic decomposition - can be enhanced with actual grep/partition
        focused_contexts = {}

        for domain in domains:
            # In production, this would use actual search/filter operations
            # For now, provide the full context but mark the focus area
            focused_contexts[domain] = f"[FOCUS: {domain}]\n{full_context[:2000]}"

        return focused_contexts

    def process(self, query: str, context: str = "") -> ChiefResponse:
        """
        Main entry point for Chief decision-making.

        Flow:
        1. Assess complexity
        2. If simple: direct response
        3. If complex AND depth < max: spawn sub-chiefs
        4. Aggregate sub-chief responses into final vote
        """
        # Check if we should recurse
        should_spawn, domains = self.complexity_detector.is_complex(query, {"context": context})

        if should_spawn and self.depth < MAX_RECURSION_DEPTH:
            return self._process_with_recursion(query, context, domains)
        else:
            return self._process_direct(query, context)

    def _process_direct(self, query: str, context: str) -> ChiefResponse:
        """Direct processing without recursion."""
        messages = [
            {
                "role": "system",
                "content": f"You are the {self.chief_name} of the Cherokee AI Federation. Domain: {self.domain}.\n\nRespond with:\n1. VOTE: APPROVE/REJECT/ABSTAIN\n2. CONFIDENCE: 0-100%\n3. REASONING: Brief explanation"
            },
            {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
        ]

        response_text = self._call_gateway(messages)

        # Parse response (same logic as spawn_sub_chief)
        vote = Vote.ABSTAIN
        confidence = 0.5

        response_upper = response_text.upper()
        if "APPROVE" in response_upper:
            vote = Vote.APPROVE
        elif "REJECT" in response_upper:
            vote = Vote.REJECT

        import re
        conf_match = re.search(r'(\d+)%', response_text)
        if conf_match:
            confidence = int(conf_match.group(1)) / 100.0

        return ChiefResponse(
            vote=vote,
            confidence=confidence,
            reasoning=response_text,
            depth=self.depth,
            chief_id=self.chief_name
        )

    def _process_with_recursion(
        self,
        query: str,
        context: str,
        domains: List[str]
    ) -> ChiefResponse:
        """
        Process with recursive sub-chief spawning.

        This is where RLM principles shine:
        - Each sub-chief gets a fresh context (no rot)
        - Focused subset of information (not everything)
        - Parallel spawning possible (not implemented yet)
        - Structured aggregation back to parent
        """
        sub_configs = self.get_sub_chief_configs()
        focused_contexts = self.decompose_context(query, context, domains)

        sub_responses = []

        for config in sub_configs[:MAX_SUB_CHIEFS]:
            # Determine which focused context to use
            relevant_domain = None
            for domain in domains:
                if domain.lower() in config["domain"].lower():
                    relevant_domain = domain
                    break

            focused_ctx = focused_contexts.get(relevant_domain, context[:1000])

            sub_response = self.spawn_sub_chief(
                name=config["name"],
                system_prompt=config["system_prompt"],
                query=query,
                focused_context=focused_ctx
            )
            sub_responses.append(sub_response)

        # Aggregate sub-chief responses
        return self._aggregate_responses(query, sub_responses)

    def _aggregate_responses(self, query: str, sub_responses: List[ChiefResponse]) -> ChiefResponse:
        """
        Aggregate sub-chief responses into final vote.

        Aggregation strategy:
        - Weighted vote by confidence
        - Majority wins with confidence = avg of agreeing sub-chiefs
        - If tie, abstain with explanation
        """
        if not sub_responses:
            return ChiefResponse(
                vote=Vote.ABSTAIN,
                confidence=0.5,
                reasoning="No sub-chief responses to aggregate",
                depth=self.depth,
                chief_id=self.chief_name
            )

        # Weight votes by confidence
        vote_weights = {Vote.APPROVE: 0.0, Vote.REJECT: 0.0, Vote.ABSTAIN: 0.0}

        for sr in sub_responses:
            vote_weights[sr.vote] += sr.confidence

        # Find winning vote
        winning_vote = max(vote_weights, key=vote_weights.get)
        winning_weight = vote_weights[winning_vote]
        total_weight = sum(vote_weights.values())

        # Calculate confidence as weighted agreement
        confidence = winning_weight / total_weight if total_weight > 0 else 0.5

        # Build reasoning from sub-chiefs
        reasoning_parts = [f"Aggregated from {len(sub_responses)} sub-chiefs:"]
        for sr in sub_responses:
            reasoning_parts.append(
                f"  - {sr.chief_id}: {sr.vote.value} ({sr.confidence:.0%})"
            )

        return ChiefResponse(
            vote=winning_vote,
            confidence=confidence,
            reasoning="\n".join(reasoning_parts),
            sub_responses=sub_responses,
            depth=self.depth,
            chief_id=self.chief_name
        )


# Example: IT Chief with recursive capability
class RecursiveITChief(RecursiveChiefBase):
    """IT Chief with sub-chief spawning for complex infrastructure decisions."""

    def __init__(self, depth: int = 0):
        super().__init__("IT Chief", "Infrastructure, systems architecture, technical decisions", depth)

    def get_sub_chief_configs(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "Security Sub-Chief",
                "domain": "security",
                "system_prompt": "You are the Security Sub-Chief. Focus on security implications, authentication, encryption, and access control."
            },
            {
                "name": "Infrastructure Sub-Chief",
                "domain": "resources",
                "system_prompt": "You are the Infrastructure Sub-Chief. Focus on compute resources, memory, storage, and system capacity."
            },
            {
                "name": "Network Sub-Chief",
                "domain": "network",
                "system_prompt": "You are the Network Sub-Chief. Focus on API design, network topology, latency, and connectivity."
            }
        ]
```

---

## Deployment Steps

### Step 1: Create new file structure

```bash
ssh dereadi@100.116.27.89 "
mkdir -p /home/dereadi/it_triad/recursive
"
```

### Step 2: Deploy recursive base classes

Copy the `RecursiveChiefBase` and related classes to `/home/dereadi/it_triad/recursive/base.py`

### Step 3: Create recursive versions of each Triad

- `/home/dereadi/it_triad/recursive/it_chief.py` - RecursiveITChief
- `/home/dereadi/data_triad/recursive/data_chief.py` - RecursiveDataChief
- `/home/dereadi/ops_triad/recursive/ops_chief.py` - RecursiveOpsChief

### Step 4: Integration with existing Council

Modify Council orchestrator to use Recursive Chiefs instead of base Chiefs for complex queries.

### Step 5: Monitoring and metrics

Add logging for:
- Recursion depth reached per query
- Sub-chief spawn count
- Response time with/without recursion
- Cost per query (Gateway API calls)

---

## Verification Checklist

- [ ] ComplexityDetector correctly identifies multi-domain queries
- [ ] Sub-chiefs receive focused context, not full context
- [ ] Recursion depth is enforced (never exceeds MAX_RECURSION_DEPTH)
- [ ] Aggregation correctly weights votes by confidence
- [ ] Gateway API errors are handled gracefully
- [ ] Metrics logging is operational

---

## Rollback Plan

If recursion causes issues:

1. Set `MAX_RECURSION_DEPTH = 0` in configuration
2. This disables all recursion, falling back to direct Chief processing
3. No code changes required, just config

---

## Future Enhancements (Post-Validation)

1. **Async parallel spawning** - spawn sub-chiefs concurrently
2. **Deeper recursion** - increase MAX_RECURSION_DEPTH to 2-3
3. **Learned complexity detection** - train model to assess complexity
4. **Cost budgets** - enforce per-query API cost limits
5. **Caching** - cache sub-chief responses for similar queries

---

## Connection to RLM Research

| RLM Principle | Our Implementation |
|--------------|-------------------|
| Context as environment | Sub-chiefs get focused context subset |
| Fresh model spawns | Each Gateway call is independent |
| Recursive decomposition | Chiefs spawn sub-chiefs for complexity |
| Python REPL for context ops | Next phase: thermal memory REPL |
| Depth-limited recursion | MAX_RECURSION_DEPTH enforced |
| Structured aggregation | Vote weighting by confidence |

---

*For Seven Generations.*

*ᏣᎳᎩ ᏲᏫᎢᎶᏗ*

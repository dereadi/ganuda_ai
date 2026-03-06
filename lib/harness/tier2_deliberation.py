"""
Tier 2 Deliberation -- Quick multi-perspective synthesis.

2-3 specialists selected by domain affinity. Parallel LLM calls.
Majority vote consensus. Diversity scoring (Elisi requirement).

Latency target: <500ms p95.
DC-6 Gradient Principle: specialization is gravity, not boundary.
Elisi requirement: every response includes diversity metadata.
Longhouse #b940f09b18605c97 (UNANIMOUS).
"""

import logging
import time
import hashlib
import re
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass

import requests

from lib.harness.core import HarnessRequest, TierResult, StakesLevel
from lib.harness.config import TierConfig, EndpointConfig, load_harness_config

logger = logging.getLogger("harness.tier2")


# ---------------------------------------------------------------------------
# Specialist Domain Definitions
# ---------------------------------------------------------------------------
# Each specialist has a key, a display name, a domain label, and a set of
# keywords that trigger selection. The keyword sets are intentionally broad
# for v1 — future versions will use embedding similarity.

@dataclass
class SpecialistDomain:
    """Domain definition for a specialist."""
    key: str
    name: str
    domain: str
    keywords: List[str]
    system_prompt: str


SPECIALIST_DOMAINS: Dict[str, SpecialistDomain] = {
    "bear": SpecialistDomain(
        key="bear",
        name="Bear (Medicine Woman)",
        domain="medicine/health",
        keywords=[
            "health", "medical", "medicine", "wellness", "therapy",
            "diagnosis", "treatment", "symptom", "condition", "patient",
            "disability", "ptsd", "mental health", "injury", "pain",
        ],
        system_prompt=(
            "You are Bear, the Medicine Woman specialist. Your domain is health, "
            "medicine, and wellness. Provide your specialist perspective with care "
            "and precision. Be thorough but concise."
        ),
    ),
    "eagle": SpecialistDomain(
        key="eagle",
        name="Eagle Eye (Strategy)",
        domain="strategy/leadership",
        keywords=[
            "strategy", "leadership", "plan", "direction", "vision",
            "goal", "roadmap", "priority", "decision", "executive",
            "management", "initiative", "objective", "mission",
        ],
        system_prompt=(
            "You are Eagle Eye, the Strategy specialist. Your domain is leadership, "
            "strategic planning, and high-level direction. Provide your specialist "
            "perspective. Be thorough but concise."
        ),
    ),
    "spider": SpecialistDomain(
        key="spider",
        name="Spider (Technical)",
        domain="technical/infrastructure",
        keywords=[
            "technical", "code", "software", "infrastructure", "deploy",
            "server", "database", "api", "system", "architecture",
            "network", "service", "config", "debug", "error", "bug",
            "python", "script", "docker", "linux", "gpu", "vllm",
        ],
        system_prompt=(
            "You are Spider, the Technical specialist. Your domain is infrastructure, "
            "software engineering, and systems architecture. Provide your specialist "
            "perspective. Be thorough but concise."
        ),
    ),
    "crawdad": SpecialistDomain(
        key="crawdad",
        name="Crawdad (Security)",
        domain="security/compliance",
        keywords=[
            "security", "compliance", "audit", "credential", "access",
            "permission", "encryption", "vulnerability", "risk", "policy",
            "authentication", "authorization", "firewall", "pii", "gdpr",
        ],
        system_prompt=(
            "You are Crawdad, the Security specialist. Your domain is security, "
            "compliance, and risk assessment. Provide your specialist perspective. "
            "Be thorough but concise."
        ),
    ),
    "owl": SpecialistDomain(
        key="owl",
        name="Owl (Verification)",
        domain="verification/testing",
        keywords=[
            "verify", "test", "validate", "check", "review", "audit",
            "quality", "correctness", "benchmark", "regression", "ci",
            "coverage", "assertion", "proof",
        ],
        system_prompt=(
            "You are Owl, the Verification specialist. Your domain is testing, "
            "validation, and quality assurance. Provide your specialist perspective. "
            "Be thorough but concise."
        ),
    ),
    "raven": SpecialistDomain(
        key="raven",
        name="Raven (Competitive)",
        domain="competitive/market",
        keywords=[
            "competitor", "market", "competitive", "advantage", "moat",
            "industry", "trend", "benchmark", "comparison", "alternative",
            "pricing", "differentiation", "landscape",
        ],
        system_prompt=(
            "You are Raven, the Competitive Intelligence specialist. Your domain is "
            "market analysis and competitive positioning. Provide your specialist "
            "perspective. Be thorough but concise."
        ),
    ),
    "turtle": SpecialistDomain(
        key="turtle",
        name="Turtle (Governance)",
        domain="governance/long-term",
        keywords=[
            "governance", "long-term", "sustainability", "seven generation",
            "constitutional", "policy", "ethics", "principle", "sacred",
            "cultural", "tradition", "protocol", "charter",
        ],
        system_prompt=(
            "You are Turtle, the Governance specialist. Your domain is long-term "
            "thinking, sustainability, and constitutional governance. Provide your "
            "specialist perspective. Be thorough but concise."
        ),
    ),
    "coyote": SpecialistDomain(
        key="coyote",
        name="Coyote (Adversarial)",
        domain="adversarial/edge-cases",
        keywords=[
            "edge case", "adversarial", "failure", "risk", "what if",
            "worst case", "attack", "exploit", "assumption", "bias",
            "blind spot", "devil's advocate", "skeptic",
        ],
        system_prompt=(
            "You are Coyote, the Adversarial Thinker. Your domain is edge cases, "
            "failure modes, and challenging assumptions. Provide your specialist "
            "perspective. Be thorough but concise. Challenge the obvious answer."
        ),
    ),
    "deer": SpecialistDomain(
        key="deer",
        name="Deer (Market/Business)",
        domain="market/business",
        keywords=[
            "business", "revenue", "customer", "product", "market",
            "sales", "growth", "roi", "cost", "budget", "pricing",
            "user", "stakeholder", "adoption",
        ],
        system_prompt=(
            "You are Deer, the Market and Business specialist. Your domain is "
            "business strategy, customer needs, and market dynamics. Provide your "
            "specialist perspective. Be thorough but concise."
        ),
    ),
}

# Anchor specialists: for each broad domain category, which specialist is the
# default anchor (always included if that category matches).
DOMAIN_ANCHORS: Dict[str, str] = {
    "technical": "spider",
    "health": "bear",
    "security": "crawdad",
    "strategy": "eagle",
    "governance": "turtle",
    "market": "deer",
    "competitive": "raven",
    "verification": "owl",
    "adversarial": "coyote",
}


# ---------------------------------------------------------------------------
# Tier 2 Deliberation Handler
# ---------------------------------------------------------------------------

class Tier2Deliberation:
    """Quick multi-perspective synthesis with 2-3 specialists.

    Implements the TierHandler protocol from escalation.py.

    Usage:
        config = load_harness_config()
        tier2 = Tier2Deliberation(config.tier2)
        result = tier2.handle(request)
    """

    def __init__(self, tier_config: Optional[TierConfig] = None):
        if tier_config is None:
            full_config = load_harness_config()
            tier_config = full_config.tier2
        self.config = tier_config
        self._session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=4,
            pool_maxsize=8,
            max_retries=0,
        )
        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)

    def handle(
        self,
        request: HarnessRequest,
        prior_results: Optional[List[TierResult]] = None,
    ) -> TierResult:
        """Process a request with 2-3 specialist perspectives.

        Selects specialists by domain affinity, queries them in parallel,
        synthesizes responses via majority vote, and returns a TierResult
        with diversity scoring.

        Args:
            request: The harness request.
            prior_results: Results from prior tiers (used for context enrichment).

        Returns:
            TierResult with synthesized answer, confidence, diversity_score,
            and specialist metadata.
        """
        start_time = time.time()

        # --- Input validation (Crawdad) ---
        errors = request.validate()
        if errors:
            return TierResult(
                tier=2,
                answer="Input validation failed: " + "; ".join(errors),
                confidence=0.0,
                latency_ms=0.0,
                metadata={"validation_errors": errors},
            )

        # --- Select specialists ---
        selected = self._select_specialists(request.query)
        if not selected:
            # Fallback: use spider + eagle (general technical + strategy)
            selected = [SPECIALIST_DOMAINS["spider"], SPECIALIST_DOMAINS["eagle"]]
            logger.warning(
                "No domain match for query, using fallback specialists [%s]",
                request.request_id,
            )

        specialist_names = [s.name for s in selected]
        logger.info(
            "Tier 2 selected %d specialists: %s [%s]",
            len(selected), specialist_names, request.request_id,
        )

        # --- Build prior context from Tier 1 if available ---
        prior_context = ""
        if prior_results:
            t1 = prior_results[-1]
            if t1.answer and t1.confidence > 0:
                prior_context = (
                    "\n\nA quick initial assessment was provided with "
                    + str(round(t1.confidence * 100))
                    + "% confidence:\n" + t1.answer[:500]
                )

        # --- Query specialists in parallel ---
        responses = self._query_specialists_parallel(
            selected, request, prior_context
        )

        if not responses:
            latency_ms = (time.time() - start_time) * 1000
            return TierResult(
                tier=2,
                answer="All specialist queries failed. Please try again later.",
                confidence=0.0,
                latency_ms=latency_ms,
                metadata={"error": "all_specialists_failed"},
            )

        # --- Synthesize responses ---
        answer, confidence, diversity_score = self._synthesize(
            responses, request
        )

        latency_ms = (time.time() - start_time) * 1000
        logger.info(
            "Tier 2 completed: specialists=%d, confidence=%.3f, "
            "diversity=%.3f, latency=%.1fms [%s]",
            len(responses), confidence, diversity_score,
            latency_ms, request.request_id,
        )

        return TierResult(
            tier=2,
            answer=answer,
            confidence=confidence,
            latency_ms=latency_ms,
            diversity_score=diversity_score,
            specialist_count=len(responses),
            metadata={
                "specialists_selected": [s.key for s in selected],
                "specialists_responded": list(responses.keys()),
                "prior_tier_used": bool(prior_results),
                "diversity_score": diversity_score,
            },
        )

    # -------------------------------------------------------------------
    # Specialist Selection
    # -------------------------------------------------------------------

    def _select_specialists(
        self, query: str
    ) -> List[SpecialistDomain]:
        """Select 2-3 specialists based on keyword domain matching.

        Scores each specialist by counting keyword matches in the query.
        Returns the top N specialists (where N = config.max_specialists,
        capped at 3). Always includes at least one anchor specialist.

        Args:
            query: The user query text.

        Returns:
            List of 2-3 SpecialistDomain objects, sorted by relevance.
        """
        query_lower = query.lower()
        scores: Dict[str, int] = {}

        for key, spec in SPECIALIST_DOMAINS.items():
            score = 0
            for kw in spec.keywords:
                if kw in query_lower:
                    score += 1
            if score > 0:
                scores[key] = score

        if not scores:
            return []

        # Sort by score descending
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        max_specialists = min(self.config.max_specialists, 3)
        selected_keys = [key for key, _ in ranked[:max_specialists]]

        # Ensure we have at least 2 specialists for diversity
        if len(selected_keys) < 2 and ranked:
            # Add the top anchor that is not already selected
            for anchor_key in DOMAIN_ANCHORS.values():
                if anchor_key not in selected_keys:
                    selected_keys.append(anchor_key)
                    break

        # Cap at max_specialists
        selected_keys = selected_keys[:max_specialists]

        return [SPECIALIST_DOMAINS[k] for k in selected_keys]

    # -------------------------------------------------------------------
    # Parallel LLM Queries
    # -------------------------------------------------------------------

    def _query_specialists_parallel(
        self,
        specialists: List[SpecialistDomain],
        request: HarnessRequest,
        prior_context: str,
    ) -> Dict[str, str]:
        """Query selected specialists in parallel using ThreadPoolExecutor.

        Same concurrency pattern as specialist_council.py.

        Args:
            specialists: List of selected specialist domains.
            request: The harness request.
            prior_context: Optional context from prior tier results.

        Returns:
            Dict mapping specialist key -> response text. Only includes
            successful responses.
        """
        responses: Dict[str, str] = {}

        def _query_one(spec: SpecialistDomain) -> Tuple[str, str]:
            """Query a single specialist. Returns (key, response_text)."""
            prompt = self.config.prompt_template.format(
                domain=spec.domain,
                query=request.query,
                context=self._format_context(request.context) + prior_context,
            )
            answer = self._call_endpoint(
                self.config.primary_endpoint,
                spec.system_prompt,
                prompt,
            )
            return (spec.key, answer)

        timeout_seconds = self.config.primary_endpoint.timeout_seconds
        with ThreadPoolExecutor(max_workers=len(specialists)) as executor:
            futures = {
                executor.submit(_query_one, spec): spec.key
                for spec in specialists
            }
            for future in as_completed(futures, timeout=timeout_seconds + 5):
                spec_key = futures[future]
                try:
                    key, answer = future.result(timeout=5)
                    if answer:
                        responses[key] = answer
                    else:
                        logger.warning(
                            "Empty response from specialist %s", spec_key
                        )
                except Exception as e:
                    logger.warning(
                        "Specialist %s query failed: %s", spec_key, e
                    )

        return responses

    def _call_endpoint(
        self,
        endpoint: EndpointConfig,
        system_prompt: str,
        user_prompt: str,
    ) -> str:
        """Call an OpenAI-compatible endpoint with system + user messages.

        Args:
            endpoint: The endpoint configuration.
            system_prompt: The specialist's system prompt.
            user_prompt: The formatted user prompt.

        Returns:
            Response text string, or empty string on failure.
        """
        headers = {"Content-Type": "application/json"}
        if endpoint.api_key:
            headers["Authorization"] = "Bearer " + endpoint.api_key

        payload = {
            "model": endpoint.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": endpoint.max_tokens,
            "temperature": endpoint.temperature,
            "stream": False,
        }

        try:
            response = self._session.post(
                endpoint.url,
                json=payload,
                headers=headers,
                timeout=endpoint.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                if content:
                    return content.strip()
            return ""
        except requests.exceptions.Timeout:
            logger.warning("Timeout calling %s", endpoint.url)
            return ""
        except requests.exceptions.ConnectionError:
            logger.warning("Connection error calling %s", endpoint.url)
            return ""
        except requests.exceptions.HTTPError as e:
            logger.warning("HTTP error from %s: %s", endpoint.url, e)
            return ""
        except Exception as e:
            logger.error("Unexpected error calling %s: %s", endpoint.url, e)
            return ""

    # -------------------------------------------------------------------
    # Synthesis & Scoring
    # -------------------------------------------------------------------

    def _synthesize(
        self,
        responses: Dict[str, str],
        request: HarnessRequest,
    ) -> Tuple[str, float, float]:
        """Synthesize specialist responses into a unified answer.

        Builds a structured answer showing each specialist's perspective,
        computes a confidence score based on agreement level, and measures
        diversity of viewpoints.

        Args:
            responses: Dict of specialist_key -> response_text.
            request: The original request (for context).

        Returns:
            Tuple of (synthesized_answer, confidence, diversity_score).
        """
        n = len(responses)
        if n == 0:
            return ("No specialist responses available.", 0.0, 0.0)

        # --- Build synthesized answer ---
        parts = []
        for key, text in responses.items():
            spec = SPECIALIST_DOMAINS.get(key)
            label = spec.name if spec else key
            parts.append("**" + label + "**: " + text)

        synthesized = "\n\n---\n\n".join(parts)

        # --- Confidence scoring based on agreement ---
        confidence = self._compute_agreement_confidence(responses)

        # --- Diversity scoring (Elisi requirement) ---
        diversity_score = self._compute_diversity(responses)

        return (synthesized, confidence, diversity_score)

    def _compute_agreement_confidence(
        self, responses: Dict[str, str]
    ) -> float:
        """Compute confidence based on specialist agreement level.

        Uses simple text similarity (Jaccard on word sets) to measure
        how much specialists agree. Higher agreement = higher confidence.

        Scoring:
        - 3/3 agree (sim > 0.3): 0.85
        - 2/3 agree (sim > 0.2): 0.70
        - All disagree (sim < 0.2): 0.50

        Args:
            responses: Dict of specialist_key -> response_text.

        Returns:
            Confidence score between 0.0 and 1.0.
        """
        texts = list(responses.values())
        n = len(texts)

        if n <= 1:
            return 0.65  # Single specialist, moderate confidence

        # Compute pairwise Jaccard similarity on word sets
        word_sets = []
        for text in texts:
            words = set(re.findall(r'\b\w+\b', text.lower()))
            # Remove common stop words for better signal
            stop_words = {
                "the", "a", "an", "is", "are", "was", "were", "be", "been",
                "being", "have", "has", "had", "do", "does", "did", "will",
                "would", "could", "should", "may", "might", "can", "shall",
                "to", "of", "in", "for", "on", "with", "at", "by", "from",
                "as", "into", "through", "during", "before", "after", "and",
                "but", "or", "nor", "not", "so", "yet", "both", "either",
                "neither", "each", "every", "all", "any", "few", "more",
                "most", "other", "some", "such", "no", "only", "own",
                "same", "than", "too", "very", "just", "because", "if",
                "when", "where", "how", "what", "which", "who", "whom",
                "this", "that", "these", "those", "i", "you", "he", "she",
                "it", "we", "they", "me", "him", "her", "us", "them",
                "my", "your", "his", "its", "our", "their",
            }
            words -= stop_words
            word_sets.append(words)

        similarities = []
        for i in range(n):
            for j in range(i + 1, n):
                if word_sets[i] or word_sets[j]:
                    intersection = word_sets[i] & word_sets[j]
                    union = word_sets[i] | word_sets[j]
                    sim = len(intersection) / len(union) if union else 0.0
                    similarities.append(sim)

        if not similarities:
            return 0.50

        avg_sim = sum(similarities) / len(similarities)

        # Map similarity to confidence
        if avg_sim > 0.3:
            return 0.85  # Strong agreement
        elif avg_sim > 0.2:
            return 0.70  # Moderate agreement
        elif avg_sim > 0.1:
            return 0.55  # Weak agreement
        else:
            return 0.45  # Disagreement — low confidence, likely escalate

    def _compute_diversity(self, responses: Dict[str, str]) -> float:
        """Compute diversity score across specialist responses.

        Diversity = 1 - average_pairwise_similarity.
        Higher diversity means more varied viewpoints (Elisi requirement).

        A diversity score of 0.0 means all specialists said the same thing.
        A diversity score of 1.0 means maximum divergence.

        Args:
            responses: Dict of specialist_key -> response_text.

        Returns:
            Diversity score between 0.0 and 1.0.
        """
        texts = list(responses.values())
        n = len(texts)

        if n <= 1:
            return 0.0  # Can't measure diversity with one voice

        # Use word-set Jaccard for consistency with agreement scoring
        word_sets = []
        for text in texts:
            words = set(re.findall(r'\b\w+\b', text.lower()))
            word_sets.append(words)

        similarities = []
        for i in range(n):
            for j in range(i + 1, n):
                if word_sets[i] or word_sets[j]:
                    intersection = word_sets[i] & word_sets[j]
                    union = word_sets[i] | word_sets[j]
                    sim = len(intersection) / len(union) if union else 0.0
                    similarities.append(sim)

        if not similarities:
            return 0.5

        avg_sim = sum(similarities) / len(similarities)
        diversity = round(1.0 - avg_sim, 3)
        return max(0.0, min(1.0, diversity))

    # -------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------

    @staticmethod
    def _format_context(context: Dict[str, Any]) -> str:
        """Flatten context dict to readable string."""
        if not context:
            return "No additional context provided."
        parts = []
        for key, value in context.items():
            parts.append(str(key) + ": " + str(value))
        return "\n".join(parts)
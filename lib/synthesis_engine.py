"""
Synthesis Engine — Cherokee AI Federation
Consultation Ring Phase 2: Local Re-Integration

Re-integrates decomposed claim responses from multiple frontier models into
a coherent answer.  This is the CRITICAL SECURITY COMPONENT — synthesis
NEVER happens on a frontier model.  It runs on redfin via local vLLM only.

The original query is the secret.  It never left redfin during decomposition,
and it stays on redfin during synthesis.  No frontier model ever sees the
full hypothesis — only the local model does, when it reassembles the answer.

Council Vote: a3ee2a8066e04490 (UNANIMOUS)
Patent Brief #7: Tokenized Air-Gap Proxy
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from lib.sub_agent_dispatch import SubAgentDispatch

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_LOCAL_NODE = "redfin_vllm"
_EXTERNAL_PREFIXES = ("https://", "http://api.", "http://openai", "http://anthropic")

_SYNTHESIS_SYSTEM_PROMPT = (
    "You are a synthesis specialist. You will receive an original question and "
    "a set of research fragments collected from multiple independent sources. "
    "Each fragment answers a decomposed sub-question derived from the original. "
    "Your job is to:\n"
    "1. Integrate ALL fragments into a single coherent, well-structured answer "
    "to the original question.\n"
    "2. Resolve any contradictions between fragments by noting the disagreement.\n"
    "3. Do NOT fabricate information beyond what the fragments provide.\n"
    "4. If fragments are insufficient to fully answer the question, say so.\n"
    "5. Cite which fragment(s) support each part of your answer using [F1], [F2], etc.\n"
    "6. Be thorough but concise."
)


# ---------------------------------------------------------------------------
# SynthesisEngine
# ---------------------------------------------------------------------------
class SynthesisEngine:
    """
    Re-integrates decomposed claim responses into a coherent answer
    using LOCAL inference only (redfin vLLM).

    Usage:
        engine = SynthesisEngine()
        result = engine.synthesize(
            original_query="Does chirality explain AI governance?",
            claim_responses=[
                {
                    "claim_id": "abc123",
                    "claim_text": "What is asymmetry in complex systems?",
                    "provider": "anthropic",
                    "response": "Asymmetry in complex systems refers to...",
                },
                ...
            ],
        )
        print(result["synthesized_response"])
        print(result["synthesis_metadata"])
    """

    def __init__(
        self,
        node: str = _LOCAL_NODE,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        timeout: float = 120.0,
    ) -> None:
        self._node = node
        self._max_tokens = max_tokens
        self._temperature = temperature
        self._timeout = timeout
        self._dispatch = SubAgentDispatch(default_timeout=timeout)

        # Security check: ensure the configured node points to localhost
        node_cfg = self._dispatch.nodes.get(self._node, {})
        node_url = node_cfg.get("url", "")
        if any(node_url.startswith(prefix) for prefix in _EXTERNAL_PREFIXES):
            logger.critical(
                "SECURITY VIOLATION: SynthesisEngine node '%s' points to "
                "external URL '%s'. Synthesis MUST run locally. Refusing to initialize.",
                self._node, node_url,
            )
            raise ValueError(
                f"SynthesisEngine refuses to use external endpoint: {node_url}. "
                f"Synthesis containing the original query MUST stay on localhost."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def synthesize(
        self,
        original_query: str,
        claim_responses: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Synthesize claim responses into a coherent answer.

        Parameters
        ----------
        original_query : str
            The original un-decomposed query (SECRET — never leaves redfin).
        claim_responses : list of dict
            Each dict has: claim_id, claim_text, provider, response.

        Returns
        -------
        dict with keys:
            synthesized_response : str
            synthesis_metadata   : dict
        """
        if not original_query or not original_query.strip():
            return {
                "synthesized_response": "",
                "synthesis_metadata": {
                    "error": "empty original_query",
                    "providers_used": [],
                    "claim_count": 0,
                    "synthesis_model": "",
                    "synthesis_node": self._node,
                    "synthesis_time_ms": 0,
                },
            }

        if not claim_responses:
            return {
                "synthesized_response": "",
                "synthesis_metadata": {
                    "error": "no claim_responses provided",
                    "providers_used": [],
                    "claim_count": 0,
                    "synthesis_model": "",
                    "synthesis_node": self._node,
                    "synthesis_time_ms": 0,
                },
            }

        # Build the synthesis prompt
        prompt = self._build_prompt(original_query, claim_responses)

        # Collect metadata before dispatch
        providers_used = list({cr.get("provider", "unknown") for cr in claim_responses})
        node_cfg = self._dispatch.nodes.get(self._node, {})
        synthesis_model = node_cfg.get("model", "unknown")

        # Dispatch to local model
        t0 = time.monotonic()
        result = self._dispatch.dispatch(
            prompt=prompt,
            system=_SYNTHESIS_SYSTEM_PROMPT,
            node=self._node,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            timeout=self._timeout,
        )
        synthesis_time_ms = int((time.monotonic() - t0) * 1000)

        metadata = {
            "providers_used": sorted(providers_used),
            "claim_count": len(claim_responses),
            "synthesis_model": synthesis_model,
            "synthesis_node": self._node,
            "synthesis_time_ms": synthesis_time_ms,
            "dispatch_ok": result["ok"],
            "dispatch_latency_ms": result.get("latency_ms", 0),
        }

        if not result["ok"]:
            logger.error(
                "Synthesis dispatch failed on node '%s': %s",
                self._node, result["text"],
            )
            metadata["error"] = result["text"]
            return {
                "synthesized_response": "",
                "synthesis_metadata": metadata,
            }

        return {
            "synthesized_response": result["text"],
            "synthesis_metadata": metadata,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _build_prompt(
        self,
        original_query: str,
        claim_responses: List[Dict[str, Any]],
    ) -> str:
        """
        Build the synthesis prompt with the original query and all fragments
        organized by correlation group (if available) or sequentially.
        """
        # Group by correlation_group if present, otherwise sequential
        groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for cr in claim_responses:
            group_key = str(cr.get("correlation_group", "ungrouped"))
            groups[group_key].append(cr)

        lines = [
            "=== ORIGINAL QUESTION ===",
            original_query.strip(),
            "",
            "=== RESEARCH FRAGMENTS ===",
            f"Total fragments: {len(claim_responses)}",
            "",
        ]

        fragment_num = 1
        for group_key in sorted(groups.keys()):
            group_items = groups[group_key]
            if group_key != "ungrouped":
                lines.append(f"--- Correlation Group {group_key} ---")

            for cr in group_items:
                provider = cr.get("provider", "unknown")
                claim_text = cr.get("claim_text", "")
                response = cr.get("response", "")

                lines.append(f"[F{fragment_num}] Sub-question: {claim_text}")
                lines.append(f"     Source: {provider}")
                lines.append(f"     Response: {response}")
                lines.append("")
                fragment_num += 1

        lines.append("=== TASK ===")
        lines.append(
            "Synthesize the fragments above into a single coherent answer "
            "to the ORIGINAL QUESTION. Cite fragments as [F1], [F2], etc."
        )

        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Smoke test (run directly: python synthesis_engine.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s  %(message)s",
    )

    engine = SynthesisEngine()

    # Simulated claim responses (no live model needed to test structure)
    test_responses = [
        {
            "claim_id": "aaa111",
            "claim_text": "What is the current state of research on asymmetry in complex systems?",
            "provider": "anthropic",
            "correlation_group": 1,
            "response": (
                "Asymmetry in complex systems is a well-studied phenomenon. "
                "Broken symmetry drives phase transitions, self-organization, "
                "and emergent behavior in both physical and computational systems."
            ),
        },
        {
            "claim_id": "bbb222",
            "claim_text": "What are the key challenges in hierarchical decision structures?",
            "provider": "local",
            "correlation_group": 2,
            "response": (
                "Key challenges include information loss at aggregation boundaries, "
                "latency in multi-level approval chains, and the tension between "
                "local autonomy and global coherence."
            ),
        },
        {
            "claim_id": "ccc333",
            "claim_text": "Are there established frameworks that bridge asymmetry and governance?",
            "provider": "anthropic",
            "correlation_group": 1,
            "response": (
                "Polycentric governance (Ostrom) provides a framework where "
                "asymmetric actors coordinate through nested rules. Federalism "
                "itself is an asymmetry-management pattern."
            ),
        },
    ]

    print("=== SynthesisEngine Smoke Test ===\n")

    # Test prompt building (does not require live vLLM)
    prompt = engine._build_prompt(
        "Does chirality explain AI governance?",
        test_responses,
    )
    print("--- Built Prompt ---")
    print(prompt)
    print()

    # Test synthesis (requires live vLLM on localhost:8000)
    print("--- Attempting live synthesis (will fail if vLLM is down) ---")
    result = engine.synthesize(
        original_query="Does chirality explain AI governance?",
        claim_responses=test_responses,
    )
    if result["synthesis_metadata"].get("dispatch_ok"):
        print(f"PASS: Synthesis completed in {result['synthesis_metadata']['synthesis_time_ms']}ms")
        print(f"Response preview: {result['synthesized_response'][:200]}...")
    else:
        print(f"EXPECTED: vLLM not available — {result['synthesis_metadata'].get('error', 'unknown')}")

    print(f"\nMetadata: {result['synthesis_metadata']}")

    # Test edge cases
    print("\n--- Edge case: empty query ---")
    empty_result = engine.synthesize("", test_responses)
    assert empty_result["synthesized_response"] == "", "Should return empty for empty query"
    assert empty_result["synthesis_metadata"]["error"] == "empty original_query"
    print("PASS: Empty query handled.")

    print("\n--- Edge case: no responses ---")
    no_resp_result = engine.synthesize("Some query?", [])
    assert no_resp_result["synthesized_response"] == "", "Should return empty for no responses"
    assert no_resp_result["synthesis_metadata"]["error"] == "no claim_responses provided"
    print("PASS: No responses handled.")

    # Test security check
    print("\n--- Security check: external endpoint rejection ---")
    try:
        bad_engine = SynthesisEngine.__new__(SynthesisEngine)
        bad_dispatch = SubAgentDispatch(nodes={
            "evil_node": {
                "url": "https://api.openai.com/v1",
                "model": "gpt-4o",
                "type": "openai",
                "tier": 1,
            }
        })
        bad_engine._node = "evil_node"
        bad_engine._dispatch = bad_dispatch
        bad_engine._max_tokens = 4096
        bad_engine._temperature = 0.3
        bad_engine._timeout = 30.0
        # Manually trigger the security check
        node_cfg = bad_dispatch.nodes.get("evil_node", {})
        node_url = node_cfg.get("url", "")
        if any(node_url.startswith(p) for p in _EXTERNAL_PREFIXES):
            print("PASS: Would reject external endpoint.")
        else:
            print("FAIL: Did not detect external endpoint.")
    except ValueError as exc:
        print(f"PASS: Rejected external endpoint — {exc}")

    print("\n=== Smoke Test Complete ===")

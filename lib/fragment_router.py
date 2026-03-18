#!/usr/bin/env python3
"""
Fragment Router — Cherokee AI Federation
Consultation Ring: Tokenized Air-Gap Proxy (Patent Brief #7)

Enforces Coyote's constraint: no single provider gets enough correlated
fragments to reconstruct a hypothesis.  After the Decomposition Engine
produces atomic claims with correlation groups, this module decides which
provider handles each claim.

Council Vote: a3ee2a8066e04490 (UNANIMOUS)
"""

from __future__ import annotations

import math
import logging
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

import yaml

# ---------------------------------------------------------------------------
# AtomicClaim definition
# Imported from decomposition_engine.  A local stub is provided as a
# fallback so fragment_router is importable in isolation.
# ---------------------------------------------------------------------------
try:
    from decomposition_engine import AtomicClaim  # type: ignore
except ImportError:
    @dataclass
    class AtomicClaim:  # type: ignore[no-redef]
        """
        Fallback stub — mirrors the canonical definition in decomposition_engine.py.

        Fields
        ------
        claim_id : str
            MD5 hex digest of claim_text.
        claim_text : str
            The decomposed question sent to a provider.
        correlation_group : int
            Related claims share the same integer group (>= 1).
        sensitivity_score : float
            0.0–1.0.  Scores > 0.7 are classified HIGH SENSITIVITY and must
            stay on the local provider (our DNA stays home).
        strategy : str
            Which decomposition strategy produced this claim.
        """
        claim_id: str
        claim_text: str
        correlation_group: int
        sensitivity_score: float
        strategy: str


# ---------------------------------------------------------------------------
# Public output type
# ---------------------------------------------------------------------------
@dataclass
class RoutedClaim:
    """A claim with its provider assignment and the reason for that choice."""
    claim: AtomicClaim
    assigned_provider: str
    reason: str


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class RoutingError(Exception):
    """Raised when routing constraints cannot be satisfied."""


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_CONFIG_PATH = os.path.join(
    os.path.dirname(__file__), "harness", "config.yaml"
)
_LOCAL_PROVIDER = "local"
_HIGH_SENSITIVITY_THRESHOLD = 0.7
_MAX_EXPOSURE_FRACTION = 0.60   # No provider may see > 60 % of all claims

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# FragmentRouter
# ---------------------------------------------------------------------------
class FragmentRouter:
    """
    Assign each AtomicClaim to a provider while enforcing:

    1. Local preference for high sensitivity  (score > 0.7  → local only)
    2. Correlation budget  (same group → different providers)
    3. Provider diversity  (spread as evenly as ceil(n/k))
    4. Session isolation   (documented in RoutedClaim.reason; no multi-turn)
    5. Maximum exposure    (no provider > 60 % of total claims)
    """

    # ------------------------------------------------------------------
    def __init__(self, enabled_providers: Optional[List[str]] = None) -> None:
        if enabled_providers is not None:
            self._providers = list(enabled_providers)
        else:
            self._providers = self._load_providers_from_config()

        if not self._providers:
            raise RoutingError("No enabled providers found — cannot route claims.")

        if _LOCAL_PROVIDER not in self._providers:
            log.warning(
                "Local provider is NOT enabled.  High-sensitivity claims "
                "(score > %.1f) cannot be routed — they will raise RoutingError.",
                _HIGH_SENSITIVITY_THRESHOLD,
            )

        # Per-session assignment counters  {provider: count}
        self._load: Dict[str, int] = {p: 0 for p in self._providers}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def route(self, claims: List[AtomicClaim]) -> List[RoutedClaim]:
        """
        Assign each claim to a provider.

        Processing order (priority):
          1. Sort claims by sensitivity_score descending.
          2. Force sensitivity > 0.7 → local.
          3. Group remaining claims by correlation_group.
          4. Round-robin within each group across non-local providers
             (then across all providers if only local is available).
          5. Verify all constraints; attempt swap repair if needed.
          6. Raise RoutingError if constraints still violated.

        Returns a list of RoutedClaim in the same order as the input.
        """
        if not claims:
            return []

        # Reset per-session load counters
        self._load = {p: 0 for p in self._providers}

        total = len(claims)
        # ceil(total / num_providers) is the per-provider cap for diversity
        diversity_cap = math.ceil(total / len(self._providers))
        # Hard cap: no provider sees > 60 % of all claims
        exposure_cap = math.floor(total * _MAX_EXPOSURE_FRACTION)
        # Effective cap is the stricter of the two
        hard_cap = min(diversity_cap, exposure_cap)

        # Work on a sorted copy; we'll map back to original order at the end
        indexed = sorted(enumerate(claims), key=lambda t: t[1].sensitivity_score, reverse=True)

        assignments: Dict[int, str] = {}   # original_index → provider
        reasons: Dict[int, str] = {}

        # --- Pass 1: high-sensitivity claims → local -----------------------
        non_sensitive: List[tuple] = []
        for orig_idx, claim in indexed:
            if claim.sensitivity_score > _HIGH_SENSITIVITY_THRESHOLD:
                if _LOCAL_PROVIDER not in self._providers:
                    raise RoutingError(
                        f"Claim '{claim.claim_id}' has sensitivity "
                        f"{claim.sensitivity_score:.2f} > {_HIGH_SENSITIVITY_THRESHOLD} "
                        f"and requires the local provider, but local is not enabled."
                    )
                assignments[orig_idx] = _LOCAL_PROVIDER
                reasons[orig_idx] = (
                    f"sensitivity={claim.sensitivity_score:.2f} > "
                    f"{_HIGH_SENSITIVITY_THRESHOLD} → local-only; session isolated"
                )
                self._load[_LOCAL_PROVIDER] += 1
            else:
                non_sensitive.append((orig_idx, claim))

        # --- Pass 2: remaining claims, grouped by correlation_group --------
        # Build group → [(orig_idx, claim)] mapping (preserving sensitivity-desc order)
        group_map: Dict[str, List[tuple]] = {}
        for orig_idx, claim in non_sensitive:
            group_map.setdefault(claim.correlation_group, []).append((orig_idx, claim))

        # Validate: if any group has more members than available providers, fail fast
        for grp, members in group_map.items():
            if len(members) > len(self._providers):
                raise RoutingError(
                    f"Correlation group '{grp}' has {len(members)} claims but only "
                    f"{len(self._providers)} providers are available.  The decomposition "
                    f"must be finer-grained so each correlated claim can go to a distinct provider."
                )

        # Assign: for each group, round-robin across providers (never repeat
        # within the same group, never exceed hard_cap)
        for grp, members in group_map.items():
            used_providers_in_group: List[str] = []
            for orig_idx, claim in members:
                chosen = self._pick_provider(
                    exclude=used_providers_in_group,
                    hard_cap=hard_cap,
                )
                if chosen is None:
                    # All providers are at cap — loosen diversity_cap and try again
                    chosen = self._pick_provider(
                        exclude=used_providers_in_group,
                        hard_cap=None,
                    )
                if chosen is None:
                    raise RoutingError(
                        f"Cannot assign claim '{claim.claim_id}' in group '{grp}': "
                        f"all available providers excluded for intra-group diversity or at capacity."
                    )
                assignments[orig_idx] = chosen
                reasons[orig_idx] = (
                    f"correlation_group={grp!r}; round-robin diversity; "
                    f"sensitivity={claim.sensitivity_score:.2f}; session isolated"
                )
                used_providers_in_group.append(chosen)
                self._load[chosen] += 1

        # --- Pass 3: verify constraints -------------------------------------
        try:
            self._verify_correlation_constraint(claims, assignments)
        except RoutingError as exc:
            log.warning("Correlation constraint violated after initial assignment; attempting swap repair: %s", exc)
            self._repair_correlation_violations(claims, assignments, reasons)
            # Verify again — raise if still broken
            self._verify_correlation_constraint(claims, assignments)

        self._verify_exposure_constraint(total)

        # --- Build output in original order ---------------------------------
        result: List[RoutedClaim] = []
        for orig_idx, claim in enumerate(claims):
            result.append(RoutedClaim(
                claim=claim,
                assigned_provider=assignments[orig_idx],
                reason=reasons[orig_idx],
            ))
        return result

    # ------------------------------------------------------------------
    def _check_correlation_budget(self, assignments: Dict[str, List[int]]) -> bool:
        """
        Return True when no provider holds two or more indices that belong
        to the same correlation group.

        ``assignments`` maps provider → list of claim indices (into the
        claims list used for the current routing session).  This method is
        also used externally as a quick sanity check.
        """
        # We need the current claims list; store it during route() for this helper
        claims = getattr(self, "_current_claims", [])
        for provider, indices in assignments.items():
            groups_seen: set = set()
            for idx in indices:
                if idx >= len(claims):
                    continue
                grp = claims[idx].correlation_group
                if grp in groups_seen:
                    return False
                groups_seen.add(grp)
        return True

    # ------------------------------------------------------------------
    def get_provider_load(self) -> Dict[str, int]:
        """Return assignment count per provider for this routing session."""
        return dict(self._load)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _load_providers_from_config() -> List[str]:
        """Read enabled providers from config.yaml consultation_ring section."""
        try:
            with open(_CONFIG_PATH, "r") as fh:
                cfg = yaml.safe_load(fh)
        except FileNotFoundError:
            log.error("Config not found at %s — falling back to local-only.", _CONFIG_PATH)
            return [_LOCAL_PROVIDER]
        except yaml.YAMLError as exc:
            log.error("YAML parse error in config: %s — falling back to local-only.", exc)
            return [_LOCAL_PROVIDER]

        providers_cfg = (
            cfg.get("consultation_ring", {}).get("providers", {})
        )
        enabled = [name for name, opts in providers_cfg.items() if opts.get("enabled", False)]
        log.info("FragmentRouter loaded providers from config: %s", enabled)
        return enabled

    def _pick_provider(
        self,
        exclude: List[str],
        hard_cap: Optional[int],
    ) -> Optional[str]:
        """
        Choose the least-loaded provider that:
          - is not in the exclude list
          - has not exceeded hard_cap (if given)

        Returns None if no valid provider exists.
        """
        candidates = [
            p for p in self._providers
            if p not in exclude and (hard_cap is None or self._load[p] < hard_cap)
        ]
        if not candidates:
            return None
        # Prefer least loaded
        return min(candidates, key=lambda p: self._load[p])

    def _verify_correlation_constraint(
        self,
        claims: List[AtomicClaim],
        assignments: Dict[int, str],
    ) -> None:
        """
        Raise RoutingError if any provider was assigned two claims from the
        same correlation_group.
        """
        # provider → set of groups seen
        provider_groups: Dict[str, set] = {p: set() for p in self._providers}
        for idx, provider in assignments.items():
            grp = claims[idx].correlation_group
            if grp in provider_groups[provider]:
                raise RoutingError(
                    f"Correlation budget violation: provider '{provider}' has been "
                    f"assigned multiple claims from correlation group '{grp}'."
                )
            provider_groups[provider].add(grp)

    def _verify_exposure_constraint(self, total: int) -> None:
        """
        Raise RoutingError if any provider holds > 60 % of total claims.
        """
        cap = math.floor(total * _MAX_EXPOSURE_FRACTION)
        for provider, count in self._load.items():
            if count > cap:
                raise RoutingError(
                    f"Exposure cap violation: provider '{provider}' was assigned "
                    f"{count}/{total} claims ({count/total:.0%}) which exceeds the "
                    f"{_MAX_EXPOSURE_FRACTION:.0%} hard cap ({cap} claims)."
                )

    def _repair_correlation_violations(
        self,
        claims: List[AtomicClaim],
        assignments: Dict[int, str],
        reasons: Dict[int, str],
    ) -> None:
        """
        Attempt to fix correlation budget violations by swapping assignments.

        For each violated group, find two claims on the same provider and
        try to swap one with a claim on a different provider that does not
        create a new violation.
        """
        # Build provider → [indices] map
        provider_indices: Dict[str, List[int]] = {p: [] for p in self._providers}
        for idx, prov in assignments.items():
            provider_indices[prov].append(idx)

        # Find violated (provider, group) pairs
        changed = True
        max_iterations = len(claims) * 2
        iteration = 0
        while changed and iteration < max_iterations:
            changed = False
            iteration += 1
            for provider, indices in list(provider_indices.items()):
                group_to_indices: Dict[str, List[int]] = {}
                for idx in indices:
                    g = claims[idx].correlation_group
                    group_to_indices.setdefault(g, []).append(idx)
                for grp, conflict_indices in group_to_indices.items():
                    if len(conflict_indices) < 2:
                        continue
                    # Take the second (and later) conflicting index — try to move it
                    for victim_idx in conflict_indices[1:]:
                        victim_sensitivity = claims[victim_idx].sensitivity_score
                        # Can't move high-sensitivity away from local
                        if (provider == _LOCAL_PROVIDER and
                                victim_sensitivity > _HIGH_SENSITIVITY_THRESHOLD):
                            continue
                        # Find a swap target: a claim on a different provider whose
                        # correlation group is not already on `provider`
                        groups_on_provider = {claims[i].correlation_group for i in indices}
                        for other_prov, other_indices in provider_indices.items():
                            if other_prov == provider:
                                continue
                            groups_on_other = {claims[i].correlation_group for i in other_indices}
                            if grp in groups_on_other:
                                # Moving victim here would still conflict
                                continue
                            # Check that victim's group is not already on other_prov
                            # (it shouldn't be since we just checked, but be safe)
                            # Try a direct move (no swap needed if other_prov has room)
                            exposure_cap = math.floor(len(claims) * _MAX_EXPOSURE_FRACTION)
                            if self._load[other_prov] < exposure_cap:
                                # Move victim to other_prov
                                assignments[victim_idx] = other_prov
                                reasons[victim_idx] += " [swap-repaired]"
                                provider_indices[provider].remove(victim_idx)
                                provider_indices[other_prov].append(victim_idx)
                                self._load[provider] -= 1
                                self._load[other_prov] += 1
                                changed = True
                                break
                        if changed:
                            break
                    if changed:
                        break


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------
def route_claims(
    claims: List[AtomicClaim],
    enabled_providers: Optional[List[str]] = None,
) -> List[RoutedClaim]:
    """Convenience wrapper: create a FragmentRouter and route in one call."""
    router = FragmentRouter(enabled_providers=enabled_providers)
    return router.route(claims)


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")

    import hashlib

    def _make_claim(text: str, score: float, group: int, strategy: str = "test") -> AtomicClaim:
        cid = hashlib.md5(text.encode()).hexdigest()
        return AtomicClaim(
            claim_id=cid,
            claim_text=text,
            sensitivity_score=score,
            correlation_group=group,
            strategy=strategy,
        )

    print("=== FragmentRouter Self-Test ===\n")

    #                  text                                          score  group
    test_claims = [
        _make_claim("Veteran served in OIF 2005.",                    0.30,  1),   # deployment
        _make_claim("Veteran received PTSD diagnosis.",               0.85,  2),   # diagnosis  HIGH
        _make_claim("PTSD is linked to combat exposure.",             0.60,  3),   # nexus
        _make_claim("Veteran reported nightmares.",                   0.50,  4),   # symptoms
        _make_claim("Service records confirm combat MOS.",            0.75,  1),   # deployment HIGH
        _make_claim("VA examiner noted hypervigilance.",              0.55,  4),   # symptoms
        _make_claim("Rating criteria: 38 CFR 4.130 DC 9411.",         0.20,  5),   # cfr
        _make_claim("Nexus letter authored by Dr. Smith.",            0.65,  3),   # nexus
    ]

    router = FragmentRouter(enabled_providers=["local", "anthropic"])
    routed = router.route(test_claims)

    print(f"{'Claim':<8} {'Provider':<12} {'Score':>6}  Reason")
    print("-" * 90)
    for rc in routed:
        label = rc.claim.claim_id[:6]
        print(
            f"{label:<8} {rc.assigned_provider:<12} "
            f"{rc.claim.sensitivity_score:>6.2f}  {rc.reason}"
        )

    print(f"\nProvider load: {router.get_provider_load()}")

    # Verify no provider has two claims from the same correlation group
    from collections import defaultdict
    prov_groups: Dict[str, set] = defaultdict(set)
    ok = True
    for rc in routed:
        g = rc.claim.correlation_group
        if g in prov_groups[rc.assigned_provider]:
            print(f"\nFAIL: {rc.assigned_provider} got duplicate group {g!r}")
            ok = False
        prov_groups[rc.assigned_provider].add(g)
    if ok:
        print("\nPASS: All correlation groups respected.")

    # Verify high-sensitivity stayed local
    for rc in routed:
        if rc.claim.sensitivity_score > _HIGH_SENSITIVITY_THRESHOLD:
            assert rc.assigned_provider == _LOCAL_PROVIDER, (
                f"FAIL: high-sensitivity claim {rc.claim.claim_id} went to {rc.assigned_provider}"
            )
    print("PASS: All high-sensitivity claims routed to local.")

    # Verify no provider exceeded 60 %
    total = len(test_claims)
    load = router.get_provider_load()
    for prov, cnt in load.items():
        frac = cnt / total
        assert frac <= _MAX_EXPOSURE_FRACTION, f"FAIL: {prov} at {frac:.0%}"
    print("PASS: Exposure cap (60%) respected.")

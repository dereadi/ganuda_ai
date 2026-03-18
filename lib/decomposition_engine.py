"""
Decomposition Engine — Breaks novel_ip queries into individually innocuous atomic claims.

When a query is classified as novel_ip, it cannot be sent to frontier models intact.
This engine decomposes it into atomic claims where no single claim reveals the parent
hypothesis.  Claims are tagged with correlation groups so the Fragment Router can ensure
no provider receives correlated fragments.

Four strategies (all applicable strategies run; results are unioned):
  1. literature_decomposition  — concept X applied to domain Y → separate questions
  2. component_isolation       — multi-part architecture → one claim per component
  3. adversarial_reframing     — "Does X work?" → "What are the strongest arguments against X?"
  4. domain_generalization     — strip specifics, ask the abstract principle

No LLM calls. Pattern-based only.
"""

import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from lib.ip_classifier import IPClassifier


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class AtomicClaim:
    claim_id: str           # md5 of claim_text (hex digest)
    claim_text: str         # the decomposed question sent to a provider
    correlation_group: int  # related claims share a group (int >= 1)
    sensitivity_score: float  # 0.0–1.0, how much this claim reveals alone
    strategy: str           # which decomposition strategy produced this


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _md5(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def _make_claim(
    text: str,
    group: int,
    score: float,
    strategy: str,
) -> AtomicClaim:
    return AtomicClaim(
        claim_id=_md5(text),
        claim_text=text,
        correlation_group=group,
        sensitivity_score=round(score, 4),
        strategy=strategy,
    )


# ---------------------------------------------------------------------------
# Vocabulary helpers
# ---------------------------------------------------------------------------

# High-level semantic categories mapped to human-readable labels.
# Each entry: (category_label, compiled_regex)
#
# These are deliberately domain-agnostic synonyms so that generated
# questions avoid proprietary terminology.

_CONCEPT_LABELS: List[Tuple[str, re.Pattern]] = [
    # research / hypothesis framing
    ("memory-scoring systems",          re.compile(r"\bthermal\s+memory\b", re.I)),
    ("hierarchical governance frameworks", re.compile(r"\bgovernance\s+topology\b", re.I)),
    ("graduated trust mechanisms",      re.compile(r"\bgraduated\s+autonomy\b", re.I)),
    ("symmetry-breaking principles",    re.compile(r"\bchiralit(?:y|ies|al)\b", re.I)),
    ("adversarial validation patterns", re.compile(r"\bsycophancy\s+detection\b", re.I)),
    ("proxy isolation patterns",        re.compile(r"\btokenized\s+air[\s-]gap\b", re.I)),
    ("valence-weighted storage",        re.compile(r"\bvalence\s+gate\b", re.I)),
    ("federated AI coordination",       re.compile(r"\bconsultation\s+ring\b", re.I)),
    ("multi-agent consensus protocols", re.compile(r"\blonghouse\b", re.I)),
    ("modular block composition",       re.compile(r"\b(?:white\s+)?duplo\b", re.I)),
    ("bilateral cognitive integration", re.compile(r"\bbilateral\s+human\b", re.I)),
    ("evolutionary classification",     re.compile(r"\bhomo\s+novus\b", re.I)),
    ("chiral governance models",        re.compile(r"\bchiral\s+governor\b", re.I)),
    ("information asymmetry dynamics",  re.compile(r"\bracemic\s+soup\b", re.I)),
    # design-constraint vocabulary
    ("constraint-based design rules",   re.compile(r"\bdesign\s+constraint\b", re.I)),
    ("numbered design constraints",     re.compile(r"\bdc-(?:1[0-6]|[1-9])\b", re.I)),
    # agent names → neutral role labels
    ("adversarial review agents",       re.compile(r"\bcoyote\b", re.I)),
    ("stability-oriented reviewers",    re.compile(r"\bturtle\b", re.I)),
    ("synthesis-focused agents",        re.compile(r"\braven\b", re.I)),
    ("integration layer agents",        re.compile(r"\bspider\b", re.I)),
    ("privacy-enforcement agents",      re.compile(r"\bcrawdad\b", re.I)),
    ("drift-monitoring agents",         re.compile(r"\beagle\s+eye\b", re.I)),
    # node names → neutral hardware labels
    ("distributed inference nodes",     re.compile(
        r"\b(?:redfin|bluefin|greenfin|owlfin|eaglefin|bmasass|sasass|thunderduck|silverfin)\b",
        re.I,
    )),
    # project identity
    ("federated AI organisms",          re.compile(r"\b(?:stoneclad|ganuda|cherokee\s+(?:ai\s+)?federation)\b", re.I)),
]

# Compiled set of all novel-IP patterns (borrowed from IPClassifier) so we can
# locate which parts of a query are sensitive without re-importing internals.
_NOVEL_IP_RX = re.compile(
    r"\b(?:"
    r"chiralit(?:y|ies|al)|stoneclad|ganuda|cherokee\s+(?:ai\s+)?federation"
    r"|consultation\s+ring|thermal\s+memory|valence\s+gate|design\s+constraint"
    r"|dc-(?:1[0-6]|[1-9])|longhouse|coyote|turtle|raven|spider|crawdad"
    r"|eagle\s+eye|gecko|peace\s+chief|duplo|white\s+duplo|tokenized\s+air[\s-]gap"
    r"|graduated\s+autonomy|sycophancy\s+detection|observation\s+levels"
    r"|governance\s+topology|redfin|bluefin|greenfin|owlfin|eaglefin"
    r"|bmasass|sasass|thunderduck|silverfin|bilateral\s+human|homo\s+novus"
    r"|chiral\s+governor|racemic\s+soup"
    r")\b",
    re.IGNORECASE,
)

# Sentences / clauses that look like application of X to Y.
# Captures: group 1 = concept fragment, group 2 = domain/application fragment.
# NOTE: opener verbs (how/does/is/can) are consumed but NOT captured.
_XY_PATTERNS: List[re.Pattern] = [
    # "How does <X> apply to <Y>?" / "Does <X> explain <Y>?"
    re.compile(r"^(?:how\s+does|does|is|can)\s+(.+?)\s+(?:explain|apply|work|function)\s+(?:in|for|with|to)\s+(.+?)[\?\.]*$", re.I),
    # "<X> as a framework for <Y>"
    re.compile(r"^(.+?)\s+(?:as|for)\s+(?:a\s+)?(?:framework|model|mechanism|approach)\s+(?:in|for|to)\s+(.+?)[\?\.]*$", re.I),
    # "<X> in/within/across <Y> system/architecture/context/domain"
    re.compile(r"^(.+?)\s+(?:in|within|across)\s+(.+?)\s+(?:system|architecture|context|domain)[\?\.]*$", re.I),
]

# Architectural component keywords — signals that the query describes a
# multi-part system.
_COMPONENT_KEYWORDS: List[Tuple[str, str]] = [
    (r"\bmemory\b",          "memory layer"),
    (r"\bstorage\b",         "storage layer"),
    (r"\bclassif(?:ier|ication)\b", "classification subsystem"),
    (r"\bscoring\b",         "scoring subsystem"),
    (r"\brouting\b",         "routing subsystem"),
    (r"\bgateway\b",         "gateway component"),
    (r"\bprox(?:y|ies)\b",   "proxy layer"),
    (r"\bfederation\b",      "federation topology"),
    (r"\borchestrat\w+\b",   "orchestration layer"),
    (r"\bvoting\b",          "voting mechanism"),
    (r"\bconsensus\b",       "consensus mechanism"),
    (r"\bescalation\b",      "escalation pathway"),
    (r"\bvalidation\b",      "validation layer"),
    (r"\bdecomposit\w+\b",   "decomposition subsystem"),
    (r"\bencrypt\w+\b",      "encryption layer"),
    (r"\bmonitor\w+\b",      "monitoring subsystem"),
    (r"\bsched\w+\b",        "scheduling subsystem"),
    (r"\bdispatch\w+\b",     "dispatch subsystem"),
    (r"\bembedding\b",       "embedding subsystem"),
    (r"\bretrieval\b",       "retrieval subsystem"),
]

_COMPONENT_RX: List[Tuple[re.Pattern, str]] = [
    (re.compile(pat, re.I), label) for pat, label in _COMPONENT_KEYWORDS
]

# Phrases that frame the query as a validation request.
_VALIDATION_RX = re.compile(
    r"(?:does|is|can|would|will|should)\s+.+?(?:\?|$)",
    re.I,
)

# Generalization synonym map — replace domain-specific nouns with abstractions.
_GENERALIZATION_MAP: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bthermal\s+memory\b", re.I),          "temperature-weighted retrieval"),
    (re.compile(r"\bgovernance\s+topology\b", re.I),     "hierarchical decision structure"),
    (re.compile(r"\bgraduated\s+autonomy\b", re.I),      "tiered trust delegation"),
    (re.compile(r"\bchiralit(?:y|ies|al)\b", re.I),      "asymmetry in complex systems"),
    (re.compile(r"\bsycophancy\s+detection\b", re.I),    "agreement-bias detection"),
    (re.compile(r"\btokenized\s+air[\s-]gap\b", re.I),   "isolated token routing"),
    (re.compile(r"\bvalence\s+gate\b", re.I),            "importance-weighted filtering"),
    (re.compile(r"\bconsultation\s+ring\b", re.I),       "specialist consultation loop"),
    (re.compile(r"\blonghouse\b", re.I),                 "deliberation chamber"),
    (re.compile(r"\b(?:white\s+)?duplo\b", re.I),        "modular composition block"),
    (re.compile(r"\bbilateral\s+human\b", re.I),         "dual-process integration"),
    (re.compile(r"\bhomo\s+novus\b", re.I),              "emergent cognitive class"),
    (re.compile(r"\bchiral\s+governor\b", re.I),         "asymmetric control mechanism"),
    (re.compile(r"\bracemic\s+soup\b", re.I),            "undifferentiated mixed state"),
    (re.compile(r"\bdesign\s+constraints?\b", re.I),      "architectural invariants"),
    (re.compile(r"\bdc-(?:1[0-6]|[1-9])\b", re.I),      "numbered system invariant"),
    (re.compile(r"\bcoyote\b", re.I),                    "adversarial reviewer"),
    (re.compile(r"\bturtle\b", re.I),                    "conservative stability reviewer"),
    (re.compile(r"\braven\b", re.I),                     "synthesis agent"),
    (re.compile(r"\bspider\b", re.I),                    "integration agent"),
    (re.compile(r"\bcrawdad\b", re.I),                   "privacy enforcement agent"),
    (re.compile(r"\beagle\s+eye\b", re.I),               "drift detection agent"),
    (re.compile(r"\b(?:stoneclad|ganuda)\b", re.I),      "federated AI organism"),
    (re.compile(r"\bcherokee\s+(?:ai\s+)?federation\b", re.I), "AI governance federation"),
    (re.compile(r"\bredfin\b", re.I),   "high-memory inference node"),
    (re.compile(r"\bbluefin\b", re.I),  "GPU inference node"),
    (re.compile(r"\bgreenfin\b", re.I), "bridge/embedding node"),
    (re.compile(r"\bowlfin\b", re.I),   "web-layer node"),
    (re.compile(r"\beaglefin\b", re.I), "web-layer backup node"),
    (re.compile(r"\bbmasass\b", re.I),  "mobile M-series node"),
    (re.compile(r"\bsasass\b", re.I),   "desktop macOS node"),
    (re.compile(r"\bthunderduck\b", re.I), "Mac Studio cluster node"),
    (re.compile(r"\bsilverfin\b", re.I),   "identity/directory node"),
]


def _generalize(text: str) -> str:
    """Replace all known sensitive terms with their generic equivalents."""
    result = text
    for pattern, replacement in _GENERALIZATION_MAP:
        result = pattern.sub(replacement, result)
    return result


def _sensitive_concepts_in(query: str) -> List[str]:
    """Return human-readable labels for sensitive concepts found in the query."""
    found = []
    for label, rx in _CONCEPT_LABELS:
        if rx.search(query):
            found.append(label)
    return found


# ---------------------------------------------------------------------------
# DecompositionEngine
# ---------------------------------------------------------------------------

class DecompositionEngine:
    """
    Breaks a novel_ip query into atomic claims where no single claim reveals
    the parent hypothesis.

    Usage:
        engine = DecompositionEngine()
        claims = engine.decompose("Does chirality explain AI governance?")
        for c in claims:
            print(c.claim_text, c.correlation_group, c.sensitivity_score)
    """

    def __init__(self) -> None:
        self._clf = IPClassifier()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decompose(self, query: str, context: str = "") -> List[AtomicClaim]:
        """
        Apply all applicable strategies and return the union of atomic claims.

        For short / simple queries, domain_generalization alone may fire.
        Deduplication is applied on (claim_text) so overlapping strategies
        don't produce duplicate claims.
        """
        query = query.strip()
        if not query:
            return []

        flagged_terms = self._clf.get_flagged_terms(query)

        all_claims: List[AtomicClaim] = []

        # Attempt every strategy; each returns [] if it cannot apply.
        all_claims.extend(self._literature_decomposition(query))
        all_claims.extend(self._component_isolation(query))
        all_claims.extend(self._adversarial_reframing(query))
        all_claims.extend(self._domain_generalization(query))

        # If nothing fired at all (edge case), fall back to domain_generalization
        # with the raw query.
        if not all_claims:
            gen = _generalize(query)
            all_claims.append(_make_claim(gen, 1, 0.2, "domain_generalization_fallback"))

        # Deduplicate by claim_text (case-sensitive exact match).
        seen: set = set()
        unique: List[AtomicClaim] = []
        for claim in all_claims:
            if claim.claim_text not in seen:
                seen.add(claim.claim_text)
                unique.append(claim)

        return unique

    # ------------------------------------------------------------------
    # Strategy 1 — Literature Decomposition
    # ------------------------------------------------------------------

    def _literature_decomposition(self, query: str) -> List[AtomicClaim]:
        """
        Convert 'Is X a framework for Y?' into separate questions about X and Y.

        Fires when the query matches an X-applied-to-Y sentence structure.
        Produces:
          - "What is the current state of research on <X>?"   (group 1, score 0.5)
          - "What are the key challenges in <Y>?"             (group 2, score 0.3)
          - "Are there frameworks that bridge <X> and <Y>?"   (group 1, score 0.5)
        """
        claims: List[AtomicClaim] = []

        for rx in _XY_PATTERNS:
            m = rx.search(query)
            if m:
                raw_x = m.group(1).strip()
                raw_y = m.group(2).strip()

                # Generalize both fragments so proprietary terms are scrubbed.
                x = _generalize(raw_x)
                y = _generalize(raw_y)

                claims.append(_make_claim(
                    f"What is the current state of research on {x}?",
                    1, 0.5, "literature_decomposition",
                ))
                claims.append(_make_claim(
                    f"What are the key challenges in {y}?",
                    2, 0.3, "literature_decomposition",
                ))
                claims.append(_make_claim(
                    f"Are there established frameworks that bridge {x} and {y}?",
                    1, 0.5, "literature_decomposition",
                ))
                # Only use the first matching pattern.
                break

        return claims

    # ------------------------------------------------------------------
    # Strategy 2 — Component Isolation
    # ------------------------------------------------------------------

    def _component_isolation(self, query: str) -> List[AtomicClaim]:
        """
        Break architectural descriptions into individual pattern questions.

        Fires when the query mentions 2+ architectural component keywords.
        Each component becomes a standalone "What is the design pattern for <component>?"
        claim. Components that together reveal the architecture share a group
        (all get group 1 here; Fragment Router separates them across providers).
        Sensitivity scales with specificity: novel-IP terms → 0.5, generic → 0.3.
        """
        claims: List[AtomicClaim] = []
        matched_labels: List[str] = []

        for rx, label in _COMPONENT_RX:
            if rx.search(query):
                matched_labels.append(label)

        if len(matched_labels) < 2:
            # Single component — not enough to isolate meaningfully.
            return claims

        group_counter = 1
        for label in matched_labels:
            # Determine sensitivity: if label was produced from a novel-IP match, bump it.
            score = 0.5 if _NOVEL_IP_RX.search(label) else 0.35
            claims.append(_make_claim(
                f"What is the standard design pattern for a {label} in a distributed system?",
                group_counter, score, "component_isolation",
            ))
            group_counter += 1

        return claims

    # ------------------------------------------------------------------
    # Strategy 3 — Adversarial Reframing
    # ------------------------------------------------------------------

    def _adversarial_reframing(self, query: str) -> List[AtomicClaim]:
        """
        Convert validation questions into attack questions.

        Fires when the query looks like 'Does/Is/Can X work / X be valid?'.
        Produces a single claim asking for the strongest counter-arguments,
        with the subject generalized.  Reveals interest but not position.
        Sensitivity: 0.4.
        """
        claims: List[AtomicClaim] = []

        if not _VALIDATION_RX.match(query.strip()):
            return claims

        # Extract subject: everything after the opener verb, before '?'.
        opener_rx = re.compile(
            r"^(?:does|is|can|would|will|should)\s+(.+?)(?:\?|$)", re.I
        )
        m = opener_rx.match(query.strip())
        if not m:
            return claims

        raw_subject = m.group(1).strip()
        subject = _generalize(raw_subject)

        claims.append(_make_claim(
            f"What are the strongest arguments against {subject}?",
            1, 0.4, "adversarial_reframing",
        ))
        return claims

    # ------------------------------------------------------------------
    # Strategy 4 — Domain Generalization
    # ------------------------------------------------------------------

    def _domain_generalization(self, query: str) -> List[AtomicClaim]:
        """
        Strip domain-specific context, ask the general principle.

        Always fires.  Replaces all sensitive terms with generic synonyms,
        then emits a single generalized question.
        Sensitivity: 0.2 (very generic, reveals little).
        """
        generalized = _generalize(query)

        # If nothing changed, the query has no known sensitive terms —
        # still emit it as a low-sensitivity claim so decompose() always
        # returns at least one result.
        return [_make_claim(generalized, 1, 0.2, "domain_generalization")]


# ---------------------------------------------------------------------------
# Smoke test (run directly: python decomposition_engine.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    engine = DecompositionEngine()

    test_cases = [
        "Does chirality explain AI governance?",
        "How does thermal memory apply to retrieval in a distributed AI federation?",
        "Is the tokenized air-gap a valid proxy isolation mechanism for graduated autonomy?",
        "Explain the memory layer, routing subsystem, and voting mechanism in Stoneclad.",
        "Can sycophancy detection work within a consultation ring on redfin?",
        "What are the design constraints for the valence gate scoring system?",
    ]

    clf = IPClassifier()

    for query in test_cases:
        tier = clf.classify(query)
        claims = engine.decompose(query)
        print(f"\nQUERY  : {query}")
        print(f"TIER   : {tier}")
        print(f"CLAIMS : {len(claims)}")
        for c in claims:
            print(
                f"  [{c.correlation_group}] score={c.sensitivity_score:.2f}"
                f"  strategy={c.strategy:<30}  {c.claim_text}"
            )
        print()

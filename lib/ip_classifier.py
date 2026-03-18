"""
IP Classifier — Three-tier sensitivity classifier for outbound consultation queries.

Tiers (highest to lowest sensitivity):
  novel_ip      — Internal project names, patent concepts, branded research
  architectural — General multi-agent / governance / topology patterns
  operational   — Infrastructure, status, troubleshooting (default)

No LLM calls. Pattern matching with compiled regex only.
Caller may override the returned classification; this is the default classifier.
"""

import re
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Pattern tables
# ---------------------------------------------------------------------------

# novel_ip — if ANY of these match, the query is novel_ip regardless of tier below
_NOVEL_IP_PATTERNS: List[Tuple[str, str]] = [
    # Internal project / organism names
    ("chirality",          r"\bchiralit(?:y|ies|al)\b"),
    ("stoneclad",          r"\bstoneclad\b"),
    ("ganuda",             r"\bganuda\b"),
    ("cherokee_federation",r"\bcherokee\s+(?:ai\s+)?federation\b"),
    ("consultation_ring",  r"\bconsultation\s+ring\b"),
    ("thermal_memory",     r"\bthermal\s+memory\b"),
    ("valence_gate",       r"\bvalence\s+gate\b"),
    ("design_constraint",  r"\bdesign\s+constraint\b"),
    ("dc_numbered",        r"\bdc-(?:1[0-6]|[1-9])\b"),
    ("longhouse",          r"\blonghouse\b"),
    # Council agent names (as agent names — context matters, but flag them)
    ("agent_coyote",       r"\bcoyote\b"),
    ("agent_turtle",       r"\bturtle\b"),
    ("agent_raven",        r"\braven\b"),
    ("agent_spider",       r"\bspider\b"),
    ("agent_crawdad",      r"\bcrawdad\b"),
    ("agent_eagle_eye",    r"\beagle\s+eye\b"),
    ("agent_gecko",        r"\bgecko\b"),
    ("agent_peace_chief",  r"\bpeace\s+chief\b"),
    # Duplo concepts
    ("duplo",              r"\bduplo\b"),
    ("white_duplo",        r"\bwhite\s+duplo\b"),
    # Patent concepts
    ("tokenized_air_gap",  r"\btokenized\s+air[\s-]gap\b"),
    ("graduated_autonomy", r"\bgraduated\s+autonomy\b"),
    ("sycophancy_detection",r"\bsycophancy\s+detection\b"),
    ("observation_levels", r"\bobservation\s+levels\b"),
    ("governance_topology",r"\bgovernance\s+topology\b"),
    # Internal node names
    ("node_redfin",        r"\bredfin\b"),
    ("node_bluefin",       r"\bbluefin\b"),
    ("node_greenfin",      r"\bgreenfin\b"),
    ("node_owlfin",        r"\bowlfin\b"),
    ("node_eaglefin",      r"\beaglefin\b"),
    ("node_bmasass",       r"\bbmasass\b"),
    ("node_sasass",        r"\bsasass\b"),
    ("node_thunderduck",   r"\bthunderduck\b"),
    ("node_silverfin",     r"\bsilverfin\b"),
    # Research concepts specific to this project
    ("bilateral_human",    r"\bbilateral\s+human\b"),
    ("homo_novus",         r"\bhomo\s+novus\b"),
    ("chiral_governor",    r"\bchiral\s+governor\b"),
    ("racemic_soup",       r"\bracemic\s+soup\b"),
]

# architectural — checked only when no novel_ip match
_ARCHITECTURAL_PATTERNS: List[Tuple[str, str]] = [
    ("multi_agent_governance",  r"\bmulti[\s-]agent\s+governance\b"),
    ("specialist_council",      r"\bspecialist\s+council\b"),
    ("consensus_voting",        r"\bconsensus\s+voting\b"),
    ("tiered_escalation",       r"\btiered\s+escalation\b"),
    ("star_topology",           r"\bstar\s+topology\b"),
    ("hub_spoke",               r"\bhub[\s-](?:and[\s-])?spoke\b"),
    ("ai_federation",           r"\b(?:ai|agent)\s+federation\b"),
    ("mesh_network_ai",         r"\bmesh\s+(?:network|topology)\b"),
    ("temperature_scored_memory",r"\btemperature[\s-]scored\s+memory\b"),
    ("persistent_memory_arch",  r"\bpersistent\s+memory\s+architecture\b"),
    ("self_organizing_agents",  r"\bself[\s-]organiz\w+\s+(?:agent|system)\b"),
    ("emergent_behavior_agents",r"\bemergent\s+behavior\b"),
    ("governance_pattern",      r"\bgovernance\s+pattern\b"),
    ("council_vote",            r"\bcouncil\s+vot\w+\b"),
    ("agent_topology",          r"\bagent\s+topology\b"),
    ("federation_topology",     r"\bfederation\s+topology\b"),
]

# Compile all patterns once at import time
_NOVEL_IP_COMPILED  = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in _NOVEL_IP_PATTERNS]
_ARCH_COMPILED      = [(name, re.compile(pat, re.IGNORECASE)) for name, pat in _ARCHITECTURAL_PATTERNS]


# ---------------------------------------------------------------------------
# Sensitivity weight map — used by get_sensitivity_score
# ---------------------------------------------------------------------------

# Assign relative weights (0.0–1.0) per term category.
# novel_ip terms score higher than architectural terms.
_TERM_WEIGHTS: dict = {
    # Patent / branded concepts — highest weight
    "tokenized_air_gap":       1.0,
    "graduated_autonomy":      1.0,
    "sycophancy_detection":    0.95,
    "observation_levels":      0.9,
    "governance_topology":     0.9,
    "chirality":               0.95,
    "stoneclad":               1.0,
    "ganuda":                  1.0,
    "cherokee_federation":     1.0,
    "consultation_ring":       0.9,
    "thermal_memory":          0.85,
    "valence_gate":            0.9,
    "design_constraint":       0.7,
    "dc_numbered":             0.75,
    "longhouse":               0.8,
    "duplo":                   0.8,
    "white_duplo":             0.9,
    # Agent names
    "agent_coyote":            0.7,
    "agent_turtle":            0.7,
    "agent_raven":             0.7,
    "agent_spider":            0.7,
    "agent_crawdad":           0.7,
    "agent_eagle_eye":         0.7,
    "agent_gecko":             0.7,
    "agent_peace_chief":       0.8,
    # Node names
    "node_redfin":             0.75,
    "node_bluefin":            0.75,
    "node_greenfin":           0.75,
    "node_owlfin":             0.75,
    "node_eaglefin":           0.75,
    "node_bmasass":            0.75,
    "node_sasass":             0.75,
    "node_thunderduck":        0.75,
    "node_silverfin":          0.75,
    # Research concepts
    "bilateral_human":         0.9,
    "homo_novus":              0.9,
    "chiral_governor":         0.9,
    "racemic_soup":            0.85,
    # Architectural terms — mid-range weight
    "multi_agent_governance":  0.55,
    "specialist_council":      0.6,
    "consensus_voting":        0.5,
    "tiered_escalation":       0.45,
    "star_topology":           0.4,
    "hub_spoke":               0.4,
    "ai_federation":           0.5,
    "mesh_network_ai":         0.4,
    "temperature_scored_memory":0.6,
    "persistent_memory_arch":  0.5,
    "self_organizing_agents":  0.5,
    "emergent_behavior_agents":0.45,
    "governance_pattern":      0.55,
    "council_vote":            0.55,
    "agent_topology":          0.5,
    "federation_topology":     0.55,
}

_DEFAULT_NOVEL_IP_WEIGHT  = 0.75
_DEFAULT_ARCH_WEIGHT      = 0.45


# ---------------------------------------------------------------------------
# IPClassifier
# ---------------------------------------------------------------------------

class IPClassifier:
    """
    Three-tier IP sensitivity classifier for outbound consultation queries.

    Usage:
        clf = IPClassifier()
        tier  = clf.classify("How does the consultation ring decide consensus?")
        score = clf.get_sensitivity_score(query)
        terms = clf.get_flagged_terms(query)
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def classify(self, query: str, context: str = "") -> str:
        """
        Returns 'operational', 'architectural', or 'novel_ip'.

        Precedence: novel_ip > architectural > operational.
        context is appended to query before matching so callers can pass
        surrounding conversation text without changing the primary query string.
        """
        text = query if not context else f"{query} {context}"

        novel_terms = self._match_patterns(text, _NOVEL_IP_COMPILED)
        if novel_terms:
            return "novel_ip"

        arch_terms = self._match_patterns(text, _ARCH_COMPILED)
        if arch_terms:
            return "architectural"

        return "operational"

    def get_sensitivity_score(self, query: str) -> float:
        """
        Returns a float in [0.0, 1.0] representing how sensitive the query is.

        Score is the MAX weight across all flagged terms (not a sum, to avoid
        inflation for queries that happen to hit many low-weight terms).
        Returns 0.0 for fully operational queries.
        """
        text = query
        flagged: List[str] = []

        novel_terms = self._match_patterns(text, _NOVEL_IP_COMPILED)
        arch_terms  = self._match_patterns(text, _ARCH_COMPILED)
        flagged     = novel_terms + arch_terms

        if not flagged:
            return 0.0

        weights = [
            _TERM_WEIGHTS.get(
                term,
                _DEFAULT_NOVEL_IP_WEIGHT if term in dict(_NOVEL_IP_PATTERNS) else _DEFAULT_ARCH_WEIGHT
            )
            for term in flagged
        ]
        return round(max(weights), 4)

    def get_flagged_terms(self, query: str) -> List[str]:
        """
        Returns a list of term-name strings that triggered classification,
        ordered novel_ip terms first, then architectural terms.
        Empty list means the query is purely operational.
        """
        novel_terms = self._match_patterns(query, _NOVEL_IP_COMPILED)
        arch_terms  = self._match_patterns(query, _ARCH_COMPILED)
        return novel_terms + arch_terms

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _match_patterns(text: str, compiled: List[Tuple[str, re.Pattern]]) -> List[str]:
        """Return names of all patterns that match text."""
        return [name for name, pat in compiled if pat.search(text)]


# ---------------------------------------------------------------------------
# Smoke test (run directly: python ip_classifier.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    clf = IPClassifier()

    cases = [
        ("How do I restart the fire guard service on redfin?",
         "novel_ip", "node name redfin"),
        ("What is the design pattern for a specialist council with consensus voting?",
         "architectural", "specialist council + consensus voting"),
        ("Why is the PostgreSQL connection timing out?",
         "operational", "plain infra question"),
        ("Explain the chirality of life hypothesis and the chiral governor mechanism.",
         "novel_ip", "chirality + chiral governor"),
        ("How does thermal memory temperature scoring compare to BM25 retrieval?",
         "novel_ip", "thermal memory is a branded term — classified novel_ip"),
        ("The consultation ring in Stoneclad uses DC-11 for sub-Claude spawning.",
         "novel_ip", "consultation ring + stoneclad + dc-11"),
        ("Describe a hub-spoke multi-agent federation with emergent behavior.",
         "architectural", "hub-spoke + ai federation + emergent behavior"),
        ("What tokenized air-gap pattern protects our graduated autonomy harness?",
         "novel_ip", "patent concepts"),
    ]

    print(f"{'Query':<60} {'Expected':<14} {'Got':<14} {'Score':<7} Flagged")
    print("-" * 120)
    for query, expected, note in cases:
        result = clf.classify(query)
        score  = clf.get_sensitivity_score(query)
        flags  = clf.get_flagged_terms(query)
        mark   = "OK" if result == expected else "FAIL"
        print(f"{query[:58]:<60} {expected:<14} {result:<14} {score:<7.3f} {flags}  [{mark}]")

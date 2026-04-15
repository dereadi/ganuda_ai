# Jr Instruction: Kripke Structure for Council Epistemic Model

**Task ID**: KRIPKE-COUNCIL-001
**Priority**: P2
**Date**: April 14, 2026
**Tag**: it_triad_jr
**Reference**: Bonanno, *Game Theory* 3rd Ed (2024), Ch 8 — Common Knowledge (p.269-313)
**Upstream**: `/ganuda/docs/reference/Bonanno-GameTheory-3rdEd-2024.pdf`
**Related Council Vote**: Pending — this instruction formalizes existing behavior, does not change it.

---

## Context

The Specialist Council (`/ganuda/lib/specialist_council.py`) already implements an epistemic decision process: each specialist has individual knowledge, the vote creates interactive knowledge, and the audit hash creates common knowledge. But this structure is implicit in code — not formalized in a way that can be:

1. Drawn as a patent diagram for Hulsey (provisionals due Mar 8 2027)
2. Used as a whitepaper foundation for the ganuda-harness product
3. Validated against Bonanno Ch 8's formal definitions

Bonanno defines three epistemic levels (Sections 8.1-8.3):
- **Individual knowledge**: Agent i knows event E at state w if E is true in every state i considers possible from w
- **Interactive knowledge**: "Alice knows that Bob knows E" — nested knowledge across agents
- **Common knowledge**: Infinite chain — everyone knows, everyone knows that everyone knows, ...

The Council maps directly:
- Individual knowledge = each specialist's assessment (before vote)
- Interactive knowledge = the vote itself (each specialist sees all assessments)
- Common knowledge = the audit hash + Longhouse record (everyone knows the outcome, and knows that everyone knows)

Coyote's standing dissent is formalized by Section 8.4 (Belief). Coyote can *believe* the decision is wrong while *knowing* the Council reached consensus. Bonanno separates knowledge (factive — must be true) from belief (may be false). Coyote's belief is not a knowledge failure; it's a structurally different epistemic attitude.

---

## Objective

Create a Python module that formalizes the Council's epistemic state as a Kripke structure, and a companion diagram specification that can be rendered for patent drawings.

---

## Files to Create

1. `/ganuda/lib/council_kripke.py` — Kripke structure implementation
2. `/ganuda/docs/patent_drawings/kripke_council_diagram.py` — Generates Mermaid/DOT diagram spec

---

## Implementation

### 1. `/ganuda/lib/council_kripke.py`

This module models the Council's epistemic state. It does NOT replace any existing Council code. It reads from Council vote records and produces a formal epistemic model.

```python
"""Council Epistemic Model — Kripke Structure Formalization.

Formalizes the Specialist Council's knowledge states per Bonanno Ch 8.
Used for:
  1. Patent drawings (Hulsey, provisionals → non-provisional conversion)
  2. ganuda-harness whitepaper formal model section
  3. Audit trail epistemic verification

Definitions (Bonanno §8.1-8.3):
  - World (w): A possible state of affairs (one complete vote scenario)
  - Accessibility relation (~i): For specialist i, w ~i w' means
    "at world w, specialist i considers w' possible"
  - Knowledge: Specialist i KNOWS event E at w iff E is true in all
    w' such that w ~i w'
  - Common knowledge: E is common knowledge iff everyone knows E,
    everyone knows everyone knows E, ad infinitum.

KRIPKE-COUNCIL-001 | Bonanno Ch 8 | Tag: it_triad_jr
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Optional


@dataclass
class World:
    """A possible world — one complete vote scenario."""
    id: str                              # e.g., "w0", "w1"
    specialist_assessments: Dict[str, str]  # specialist_name -> assessment
    vote_outcome: str                     # "PROCEED", "REVIEW", "BLOCK"
    concern_count: int
    is_actual: bool = False              # Is this the real outcome?


@dataclass
class AccessibilityRelation:
    """What worlds specialist i considers possible from each world.

    If specialist i has PERFECT information (saw all assessments before voting),
    their accessibility set at the actual world is {actual world} — they know
    the outcome. Pre-vote, each specialist considers multiple worlds possible.
    """
    specialist: str
    # world_id -> set of world_ids that specialist considers possible
    reaches: Dict[str, Set[str]] = field(default_factory=dict)


@dataclass
class KripkeModel:
    """Full epistemic model for one Council vote.

    Bonanno Definition 8.1: A Kripke frame is (W, ~1, ~2, ..., ~n)
    where W is a set of worlds and ~i is an equivalence relation for each agent i.
    A Kripke model adds a valuation function V mapping atomic propositions to
    the worlds where they're true.
    """
    worlds: Dict[str, World] = field(default_factory=dict)
    relations: Dict[str, AccessibilityRelation] = field(default_factory=dict)
    specialists: List[str] = field(default_factory=list)

    def add_world(self, world: World):
        self.worlds[world.id] = world

    def set_accessibility(self, specialist: str, from_world: str, to_worlds: Set[str]):
        if specialist not in self.relations:
            self.relations[specialist] = AccessibilityRelation(specialist=specialist)
        self.relations[specialist].reaches[from_world] = to_worlds

    def individual_knowledge(self, specialist: str, event_worlds: Set[str], at_world: str) -> bool:
        """Does specialist KNOW the event at this world? (Bonanno Def 8.2)

        Specialist i knows E at w iff for all w' in reach(i, w), w' is in event_worlds.
        In plain language: i knows E if E is true in every world i considers possible.
        """
        if specialist not in self.relations:
            return False
        reachable = self.relations[specialist].reaches.get(at_world, set())
        if not reachable:
            return False  # No information = no knowledge
        return reachable.issubset(event_worlds)

    def mutual_knowledge(self, event_worlds: Set[str], at_world: str) -> bool:
        """Does EVERYONE know the event? (Bonanno Def 8.5)

        Mutual knowledge = every specialist individually knows E.
        This is NOT common knowledge — it's one level of the infinite chain.
        """
        return all(
            self.individual_knowledge(s, event_worlds, at_world)
            for s in self.specialists
        )

    def common_knowledge(self, event_worlds: Set[str], at_world: str, depth: int = 10) -> bool:
        """Is the event COMMON knowledge? (Bonanno Def 8.7)

        True common knowledge requires infinite depth. We approximate with
        depth iterations. In practice, the Council audit hash makes this
        trivially true for the actual outcome — everyone sees the same hash,
        everyone knows everyone sees it.

        The depth parameter is how many levels of "everyone knows that
        everyone knows that ..." to check. 10 is more than sufficient
        for any practical Council (7-14 specialists).
        """
        # Build the "everyone considers possible" reachability
        # At each level, expand the set of worlds that must satisfy E
        current_must_satisfy = {at_world}

        for _ in range(depth):
            next_level = set()
            for w in current_must_satisfy:
                for s in self.specialists:
                    reachable = self.relations[s].reaches.get(w, set())
                    next_level.update(reachable)

            # Every world at this level must be in event_worlds
            if not next_level.issubset(event_worlds):
                return False

            current_must_satisfy = next_level

        return True

    def coyote_dissent_is_belief_not_knowledge(self, coyote_name: str,
                                                 actual_world: str,
                                                 coyote_preferred_worlds: Set[str]) -> dict:
        """Formalize Coyote's standing dissent per Bonanno §8.4.

        Coyote KNOWS the vote outcome (individual knowledge — sees the audit hash).
        Coyote BELIEVES a different outcome would be better (belief, not knowledge).

        This distinction is critical:
        - Knowledge is factive: if you know E, E is true.
        - Belief is not factive: you can believe E even if E is false.
        - Coyote's dissent = believing the actual outcome is suboptimal,
          while knowing it was the Council's decision.

        Returns a dict describing the epistemic state for patent diagrams.
        """
        actual = self.worlds.get(actual_world)
        if not actual:
            return {"error": "actual_world not found"}

        outcome_event = {w_id for w_id, w in self.worlds.items()
                        if w.vote_outcome == actual.vote_outcome}

        knows_outcome = self.individual_knowledge(coyote_name, outcome_event, actual_world)

        return {
            "specialist": coyote_name,
            "knows_outcome": knows_outcome,
            "preferred_worlds": list(coyote_preferred_worlds),
            "actual_world": actual_world,
            "actual_outcome": actual.vote_outcome,
            "epistemic_state": "belief_diverges_from_knowledge" if knows_outcome else "uncertain",
            "bonanno_reference": "Section 8.4: Belief (p.284)",
            "plain_english": (
                f"{coyote_name} KNOWS the Council decided '{actual.vote_outcome}' "
                f"but BELIEVES {list(coyote_preferred_worlds)} would be better. "
                f"This is structurally valid — belief is not factive (Bonanno Def 8.10)."
            ),
        }


def build_model_from_vote(vote_record: dict) -> KripkeModel:
    """Build a Kripke model from a Council vote record.

    Args:
        vote_record: dict with keys:
            - specialists: list of specialist names
            - assessments: dict of specialist -> assessment text
            - outcome: "PROCEED" / "REVIEW" / "BLOCK"
            - concern_count: int
            - dissents: list of specialist names that dissented

    Returns:
        KripkeModel with the actual world and counterfactual worlds.
    """
    model = KripkeModel(specialists=vote_record["specialists"])

    # Actual world
    actual = World(
        id="w_actual",
        specialist_assessments=vote_record["assessments"],
        vote_outcome=vote_record["outcome"],
        concern_count=vote_record["concern_count"],
        is_actual=True,
    )
    model.add_world(actual)

    # Counterfactual worlds: what if each dissenter's view prevailed?
    for i, dissenter in enumerate(vote_record.get("dissents", [])):
        counter = World(
            id=f"w_counter_{dissenter}",
            specialist_assessments=vote_record["assessments"],  # Same information
            vote_outcome="REVIEW" if actual.vote_outcome == "PROCEED" else "PROCEED",
            concern_count=vote_record["concern_count"] + 1,
            is_actual=False,
        )
        model.add_world(counter)

    # Post-vote accessibility: every specialist reaches only the actual world
    # (they all see the audit hash — perfect information post-vote)
    all_world_ids = set(model.worlds.keys())
    for s in vote_record["specialists"]:
        if s in vote_record.get("dissents", []):
            # Dissenters: they KNOW the outcome but consider the counterfactual
            # "possible in a normative sense" (belief, not epistemic possibility)
            model.set_accessibility(s, "w_actual", {"w_actual"})
        else:
            # Non-dissenters: only the actual world is possible
            model.set_accessibility(s, "w_actual", {"w_actual"})

    return model


def generate_diagram_spec(model: KripkeModel) -> str:
    """Generate a Mermaid diagram specification for patent drawings.

    Output is Mermaid graph syntax that can be rendered to SVG/PNG.
    """
    lines = ["graph TD"]

    # World nodes
    for w_id, world in model.worlds.items():
        label = f"{w_id}[{world.vote_outcome}"
        if world.is_actual:
            label += " *ACTUAL*"
        label += f"\\nconcerns: {world.concern_count}]"
        lines.append(f"    {label}")

    # Accessibility edges
    for specialist, rel in model.relations.items():
        for from_w, to_ws in rel.reaches.items():
            for to_w in to_ws:
                lines.append(f"    {from_w} -->|{specialist}| {to_w}")

    return "\n".join(lines)
```

### 2. `/ganuda/docs/patent_drawings/kripke_council_diagram.py`

Script to generate patent-ready diagrams from actual Council vote records.

```python
"""Generate Kripke structure diagrams for patent drawings.

Reads Council vote records from the database and produces Mermaid
diagram specifications. These can be rendered with `mmdc` (Mermaid CLI)
or pasted into mermaid.live for SVG export.

Usage:
    python kripke_council_diagram.py --vote-id 8984 --output kripke_8984.mmd

For Hulsey: these diagrams formalize the epistemic model behind
Patent #1 (Governance Topology, App 63/999,913).

KRIPKE-COUNCIL-001 | Tag: it_triad_jr
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'lib'))

from council_kripke import KripkeModel, World, build_model_from_vote, generate_diagram_spec


def example_vote():
    """Example using Council Vote #8984 (SkillRL KG Phase 0, APPROVED 7-1)."""
    return {
        "specialists": [
            "Crawdad", "Gecko", "Turtle", "Eagle Eye",
            "Spider", "Peace Chief", "Raven", "Coyote"
        ],
        "assessments": {
            "Crawdad": "DB schema adequate, indexes present",
            "Gecko": "Integration points identified, no blockers",
            "Turtle": "Timeline realistic at 5 SP cap",
            "Eagle Eye": "KG formalization aligns with Princeton paper",
            "Spider": "Query timeout guard present (500ms)",
            "Peace Chief": "Consensus emerging, one dissent",
            "Raven": "Fallback path clear if KG approach stalls",
            "Coyote": "5 SP cap may be insufficient — flag for review at 3 SP",
        },
        "outcome": "PROCEED",
        "concern_count": 1,
        "dissents": ["Coyote"],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate Kripke diagrams for patent drawings")
    parser.add_argument("--example", action="store_true", help="Use example vote #8984")
    parser.add_argument("--output", type=str, default=None, help="Output .mmd file path")
    args = parser.parse_args()

    if args.example:
        vote = example_vote()
    else:
        print("Database integration pending. Use --example for now.")
        sys.exit(1)

    model = build_model_from_vote(vote)

    # Generate diagram
    diagram = generate_diagram_spec(model)

    # Show Coyote's epistemic state
    coyote_analysis = model.coyote_dissent_is_belief_not_knowledge(
        coyote_name="Coyote",
        actual_world="w_actual",
        coyote_preferred_worlds={"w_counter_Coyote"},
    )

    if args.output:
        with open(args.output, "w") as f:
            f.write(diagram)
        print(f"Diagram written to {args.output}")
    else:
        print("=== Kripke Diagram (Mermaid) ===")
        print(diagram)

    print("\n=== Coyote Epistemic Analysis ===")
    for k, v in coyote_analysis.items():
        print(f"  {k}: {v}")

    # Show knowledge checks
    actual_event = {"w_actual"}
    print("\n=== Knowledge Verification ===")
    for s in vote["specialists"]:
        knows = model.individual_knowledge(s, actual_event, "w_actual")
        print(f"  {s} knows outcome: {knows}")

    print(f"  Mutual knowledge: {model.mutual_knowledge(actual_event, 'w_actual')}")
    print(f"  Common knowledge: {model.common_knowledge(actual_event, 'w_actual')}")


if __name__ == "__main__":
    main()
```

---

## Success Criteria

- [ ] `council_kripke.py` created at `/ganuda/lib/council_kripke.py`
- [ ] `kripke_council_diagram.py` created at `/ganuda/docs/patent_drawings/kripke_council_diagram.py`
- [ ] `python kripke_council_diagram.py --example` runs and produces valid Mermaid output
- [ ] Coyote epistemic analysis correctly shows `knows_outcome: True` with divergent belief
- [ ] Common knowledge check returns True for post-vote state (all specialists see audit hash)
- [ ] Diagram is renderable in mermaid.live

## Patent Drawing Relevance

This directly supports **Patent #1: Governance Topology (App 63/999,913)**. The Kripke structure diagram shows:
1. How specialist knowledge states converge through voting
2. Why standing dissent is epistemically valid (belief vs. knowledge)
3. How the audit hash creates common knowledge

Hulsey needs diagrams with formal mathematical grounding. This provides both the formalism (Bonanno Ch 8) and the rendered output.

---

For Seven Generations.

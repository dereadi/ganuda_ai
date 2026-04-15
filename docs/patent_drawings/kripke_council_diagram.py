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
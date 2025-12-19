#!/usr/bin/env python3
"""
Gray-Box Council Integration

Wraps the Gray-Box engine for Council voting enhancement.
Provides drop-in replacement for standard voting aggregation.

For Seven Generations - Cherokee AI Federation
"""

import numpy as np
from typing import List, Dict, Any
from graybox_engine import (
    GrayBoxEngine, BayesianVotingCore, NeuralCorrector
)


class GrayBoxCouncilVoter:
    """
    Gray-Box enhanced Council voting.

    Combines Bayesian vote aggregation (physics) with
    learned specialist bias correction (neural).
    """

    def __init__(self):
        self.engine = GrayBoxEngine('council_voting')
        self.engine.set_physics_core(BayesianVotingCore())
        self.engine.set_neural_corrector(
            NeuralCorrector('council_voting', input_dim=64)
        )

        # Specialist weights (can be learned)
        self.specialist_weights = {
            'crawdad': 1.0,      # Security
            'turtle': 1.2,       # 7-Gen wisdom
            'gecko': 1.0,        # Technical
            'eagle_eye': 0.9,    # Monitoring
            'spider': 1.0,       # Cultural
            'raven': 1.1,        # Strategy
            'peace_chief': 1.5   # Synthesis
        }

    def aggregate_votes(
        self,
        votes: List[Dict],
        context: Dict = None
    ) -> Dict[str, Any]:
        """
        Aggregate specialist votes using gray-box approach.

        Args:
            votes: List of vote dictionaries with 'specialist_id' and 'response'
            context: Optional context (question, history, etc.)

        Returns:
            Aggregation result with confidence and explanation
        """
        # Extract features from votes
        vote_features = []
        for vote in votes:
            spec_id = vote.get('specialist_id', 'unknown')
            weight = self.specialist_weights.get(spec_id, 1.0)
            has_concern = 1.0 if vote.get('has_concern', False) else 0.0
            response_len = len(vote.get('response', '')) / 1000.0

            vote_features.extend([weight, has_concern, response_len])

        # Pad to fixed size
        feature_vector = np.zeros(64)
        feature_vector[:len(vote_features)] = vote_features[:64]

        # Forward through gray-box engine
        result = self.engine.forward(feature_vector, context)

        # Get explanation
        explanation = self.engine.get_explanation(result)

        return {
            'aggregated_features': result.combined_output.tolist(),
            'confidence': result.confidence,
            'physics_contribution': explanation['physics_contribution'],
            'neural_contribution': explanation['neural_contribution'],
            'physics_dominant': explanation['physics_dominant'],
            'violations': explanation['violations']
        }


if __name__ == "__main__":
    print("Gray-Box Council Voter Self-Test")
    print("=" * 50)

    voter = GrayBoxCouncilVoter()

    # Simulate votes
    test_votes = [
        {'specialist_id': 'crawdad', 'response': 'Security looks good', 'has_concern': False},
        {'specialist_id': 'turtle', 'response': 'Aligns with 7-Gen principles', 'has_concern': False},
        {'specialist_id': 'gecko', 'response': 'Technical integration feasible', 'has_concern': False},
        {'specialist_id': 'eagle_eye', 'response': 'Monitoring in place', 'has_concern': False},
        {'specialist_id': 'spider', 'response': 'Cultural patterns preserved', 'has_concern': False},
        {'specialist_id': 'raven', 'response': 'Strategic alignment confirmed', 'has_concern': False},
        {'specialist_id': 'peace_chief', 'response': 'Consensus reached', 'has_concern': False},
    ]

    result = voter.aggregate_votes(test_votes, {'question': 'Test query'})

    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Physics: {result['physics_contribution']:.2%}")
    print(f"Neural: {result['neural_contribution']:.2%}")
    print(f"Physics dominant: {result['physics_dominant']}")

    print("=" * 50)
    print("Self-test complete")
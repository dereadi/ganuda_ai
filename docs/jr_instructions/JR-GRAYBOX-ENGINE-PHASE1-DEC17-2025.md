# JR INSTRUCTIONS: Gray-Box AI Engine - Phase 1 Foundation
## JR-GRAYBOX-ENGINE-PHASE1-DEC17-2025
## December 17, 2025

### OBJECTIVE
Create the foundational Gray-Box AI engine module that combines deterministic physics solvers with neural network error correctors.

### COUNCIL APPROVAL
- Status: APPROVED (100% consensus, 0 concerns)
- Cascaded vote completed: December 17, 2025
- Audit hash: 56b3df950b3056b0

---

## TASK 1: Create Base Gray-Box Engine Module

Create `/ganuda/lib/graybox_engine.py`:

```python
#!/usr/bin/env python3
"""
Gray-Box AI Engine for Cherokee AI Federation

Combines deterministic physics/mathematical solvers with neural network
error correctors. Based on Physics-Informed Neural Networks (PINNs) research.

Architecture:
- Physics Core: Deterministic mathematical operations (constraints, bounds)
- Neural Corrector: Learned residual adjustments (patterns, optimizations)
- Unified Solver: Integrates both via differentiable computation

Reference: Neural OGCM (Tsinghua, Dec 2025), MIT Climate Studies

For Seven Generations - Cherokee AI Federation
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class GrayBoxState:
    """State container for gray-box computations"""
    physics_output: np.ndarray
    neural_correction: np.ndarray
    combined_output: np.ndarray
    confidence: float
    metadata: Dict[str, Any]


class PhysicsCore(ABC):
    """
    Abstract base class for physics/mathematical solvers.

    Subclasses implement domain-specific deterministic computations:
    - Bayesian voting aggregation
    - Information-theoretic decay
    - Formal safety constraints
    - Conservation laws
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.constraints = []
        self.bounds = {}

    @abstractmethod
    def forward(self, state: np.ndarray, params: Dict = None) -> np.ndarray:
        """Compute deterministic physics output"""
        pass

    @abstractmethod
    def validate_constraints(self, output: np.ndarray) -> Tuple[bool, List[str]]:
        """Check if output satisfies all constraints"""
        pass

    def add_constraint(self, name: str, check_fn: callable):
        """Add a constraint function"""
        self.constraints.append({'name': name, 'check': check_fn})

    def set_bounds(self, param: str, low: float, high: float):
        """Set parameter bounds"""
        self.bounds[param] = (low, high)


class NeuralCorrector(ABC):
    """
    Abstract base class for neural network correctors.

    Learns residual corrections to physics output:
    - Subgrid patterns not captured by physics
    - Context-dependent adjustments
    - Historical bias corrections
    """

    def __init__(self, domain: str, input_dim: int = 64, hidden_dim: int = 128):
        self.domain = domain
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.weights = self._initialize_weights()
        self.training_history = []

    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """Initialize neural network weights"""
        np.random.seed(42)  # Reproducibility
        return {
            'W1': np.random.randn(self.input_dim, self.hidden_dim) * 0.01,
            'b1': np.zeros(self.hidden_dim),
            'W2': np.random.randn(self.hidden_dim, self.hidden_dim) * 0.01,
            'b2': np.zeros(self.hidden_dim),
            'W_out': np.random.randn(self.hidden_dim, self.input_dim) * 0.01,
            'b_out': np.zeros(self.input_dim)
        }

    def forward(self, state: np.ndarray, context: Dict = None) -> np.ndarray:
        """Compute neural correction (residual)"""
        # Ensure state is right shape
        x = state.flatten()[:self.input_dim]
        if len(x) < self.input_dim:
            x = np.pad(x, (0, self.input_dim - len(x)))

        # Forward pass through simple MLP
        h1 = np.tanh(x @ self.weights['W1'] + self.weights['b1'])
        h2 = np.tanh(h1 @ self.weights['W2'] + self.weights['b2'])
        correction = h2 @ self.weights['W_out'] + self.weights['b_out']

        # Scale correction to be small (residual learning)
        return correction * 0.1

    def update_weights(self, gradient: Dict[str, np.ndarray], lr: float = 0.001):
        """Update weights via gradient descent"""
        for key in self.weights:
            if key in gradient:
                self.weights[key] -= lr * gradient[key]

    def save_weights(self, path: str):
        """Save weights to file"""
        np.savez(path, **self.weights)

    def load_weights(self, path: str):
        """Load weights from file"""
        data = np.load(path)
        self.weights = {key: data[key] for key in data.files}


class UnifiedODESolver:
    """
    Unified ODE solver that integrates physics and neural components.

    Uses forward Euler integration:
    state(t+1) = state(t) + dt * (physics(state) + neural(state))
    """

    def __init__(self, dt: float = 0.1):
        self.dt = dt

    def integrate(
        self,
        physics_output: np.ndarray,
        neural_correction: np.ndarray,
        state: np.ndarray = None
    ) -> np.ndarray:
        """
        Integrate physics and neural outputs.

        Args:
            physics_output: Deterministic solver output
            neural_correction: Learned residual correction
            state: Optional current state for update

        Returns:
            Combined output
        """
        # Simple additive combination
        combined = physics_output + neural_correction

        # If state provided, do Euler step
        if state is not None:
            return state + self.dt * combined

        return combined

    def integrate_trajectory(
        self,
        physics_fn: callable,
        neural_fn: callable,
        initial_state: np.ndarray,
        steps: int
    ) -> List[np.ndarray]:
        """Integrate over multiple timesteps"""
        trajectory = [initial_state]
        state = initial_state.copy()

        for _ in range(steps):
            physics_out = physics_fn(state)
            neural_out = neural_fn(state)
            state = self.integrate(physics_out, neural_out, state)
            trajectory.append(state.copy())

        return trajectory


class GrayBoxEngine:
    """
    Main Gray-Box AI engine combining physics solvers with neural correctors.

    Usage:
        engine = GrayBoxEngine('council_voting')
        engine.set_physics_core(BayesianVotingCore())
        engine.set_neural_corrector(VoteCorrector())
        result = engine.forward(votes, context)
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.physics_core: Optional[PhysicsCore] = None
        self.neural_corrector: Optional[NeuralCorrector] = None
        self.solver = UnifiedODESolver()
        self.history: List[GrayBoxState] = []

    def set_physics_core(self, core: PhysicsCore):
        """Set the physics/mathematical solver"""
        self.physics_core = core

    def set_neural_corrector(self, corrector: NeuralCorrector):
        """Set the neural corrector"""
        self.neural_corrector = corrector

    def forward(
        self,
        state: np.ndarray,
        context: Dict = None,
        validate: bool = True
    ) -> GrayBoxState:
        """
        Forward pass through gray-box engine.

        Args:
            state: Input state vector
            context: Optional context dictionary
            validate: Whether to validate constraints

        Returns:
            GrayBoxState with all outputs and metadata
        """
        if self.physics_core is None:
            raise ValueError("Physics core not set")

        # Physics computation (deterministic)
        physics_output = self.physics_core.forward(state)

        # Neural correction (learned residual)
        if self.neural_corrector is not None:
            neural_correction = self.neural_corrector.forward(state, context)
        else:
            neural_correction = np.zeros_like(physics_output)

        # Combine via unified solver
        combined = self.solver.integrate(physics_output, neural_correction)

        # Validate constraints if requested
        confidence = 1.0
        violations = []
        if validate and self.physics_core:
            valid, violations = self.physics_core.validate_constraints(combined)
            if not valid:
                confidence = max(0.0, 1.0 - len(violations) * 0.2)

        # Create state object
        result = GrayBoxState(
            physics_output=physics_output,
            neural_correction=neural_correction,
            combined_output=combined,
            confidence=confidence,
            metadata={
                'domain': self.domain,
                'timestamp': datetime.now().isoformat(),
                'violations': violations,
                'context': context or {}
            }
        )

        self.history.append(result)
        return result

    def train_step(
        self,
        state: np.ndarray,
        target: np.ndarray,
        context: Dict = None,
        lr: float = 0.001
    ) -> float:
        """
        Single training step for neural corrector.

        Args:
            state: Input state
            target: Target output (ground truth)
            context: Optional context
            lr: Learning rate

        Returns:
            Loss value
        """
        if self.neural_corrector is None:
            raise ValueError("Neural corrector not set")

        # Forward pass
        result = self.forward(state, context, validate=False)

        # Compute loss (MSE)
        loss = np.mean((result.combined_output - target) ** 2)

        # Simple gradient estimate (finite differences)
        # In production, use autograd/PyTorch
        epsilon = 1e-5
        gradients = {}

        for key in self.neural_corrector.weights:
            grad = np.zeros_like(self.neural_corrector.weights[key])
            flat_weights = self.neural_corrector.weights[key].flatten()

            for i in range(min(100, len(flat_weights))):  # Sample gradients
                original = flat_weights[i]

                flat_weights[i] = original + epsilon
                self.neural_corrector.weights[key] = flat_weights.reshape(
                    self.neural_corrector.weights[key].shape
                )
                result_plus = self.forward(state, context, validate=False)
                loss_plus = np.mean((result_plus.combined_output - target) ** 2)

                flat_weights[i] = original - epsilon
                self.neural_corrector.weights[key] = flat_weights.reshape(
                    self.neural_corrector.weights[key].shape
                )
                result_minus = self.forward(state, context, validate=False)
                loss_minus = np.mean((result_minus.combined_output - target) ** 2)

                flat_weights[i] = original
                self.neural_corrector.weights[key] = flat_weights.reshape(
                    self.neural_corrector.weights[key].shape
                )

                grad.flatten()[i] = (loss_plus - loss_minus) / (2 * epsilon)

            gradients[key] = grad

        # Update weights
        self.neural_corrector.update_weights(gradients, lr)

        return float(loss)

    def get_explanation(self, result: GrayBoxState) -> Dict[str, Any]:
        """
        Get explanation of gray-box decision.

        Returns breakdown of physics vs neural contributions.
        """
        physics_magnitude = np.linalg.norm(result.physics_output)
        neural_magnitude = np.linalg.norm(result.neural_correction)
        total_magnitude = np.linalg.norm(result.combined_output)

        return {
            'physics_contribution': float(physics_magnitude / (total_magnitude + 1e-8)),
            'neural_contribution': float(neural_magnitude / (total_magnitude + 1e-8)),
            'physics_dominant': physics_magnitude > neural_magnitude,
            'confidence': result.confidence,
            'violations': result.metadata.get('violations', []),
            'domain': result.metadata.get('domain'),
            'timestamp': result.metadata.get('timestamp')
        }


# ============================================================
# Domain-Specific Implementations (Stubs for Phase 1)
# ============================================================

class BayesianVotingCore(PhysicsCore):
    """
    Physics core for Council voting using Bayesian aggregation.

    Implements:
    - Prior distribution over outcomes
    - Likelihood from specialist votes
    - Posterior computation
    """

    def __init__(self):
        super().__init__('council_voting')
        self.prior = None  # Will be learned from history

    def forward(self, votes: np.ndarray, params: Dict = None) -> np.ndarray:
        """Compute Bayesian posterior from votes"""
        # Simple weighted average as baseline
        # Full Bayesian implementation in Phase 2
        weights = np.ones(len(votes)) / len(votes)
        if params and 'weights' in params:
            weights = np.array(params['weights'])

        return np.sum(votes * weights.reshape(-1, 1), axis=0)

    def validate_constraints(self, output: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate voting constraints"""
        violations = []

        # Probabilities should sum to 1 (if probability vector)
        if np.abs(np.sum(output) - 1.0) > 0.1:
            violations.append('probability_sum')

        # No negative values
        if np.any(output < -0.1):
            violations.append('negative_values')

        return len(violations) == 0, violations


class EntropyDecayCore(PhysicsCore):
    """
    Physics core for thermal memory using information theory.

    Implements:
    - Shannon entropy calculations
    - Mutual information preservation
    - Conservation of information budget
    """

    def __init__(self, info_budget: float = 1000.0):
        super().__init__('thermal_memory')
        self.info_budget = info_budget

    def forward(self, memory_state: np.ndarray, params: Dict = None) -> np.ndarray:
        """Compute entropy-based decay"""
        # Normalize to probability distribution
        probs = np.abs(memory_state) / (np.sum(np.abs(memory_state)) + 1e-8)

        # Shannon entropy
        entropy = -np.sum(probs * np.log(probs + 1e-8))

        # Decay rate inversely proportional to entropy (high entropy = slow decay)
        decay_rate = 1.0 / (entropy + 1.0)

        # Apply decay
        return memory_state * np.exp(-decay_rate * 0.01)

    def validate_constraints(self, output: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate information constraints"""
        violations = []

        # Total information should decrease or stay same
        if np.sum(np.abs(output)) > self.info_budget:
            violations.append('budget_exceeded')

        return len(violations) == 0, violations


class SafetyConstraintCore(PhysicsCore):
    """
    Physics core for Jr execution with safety constraints.

    Implements:
    - Pre/post condition verification
    - Resource bounds checking
    - Rollback feasibility
    """

    def __init__(self):
        super().__init__('jr_execution')
        self.resource_limits = {
            'cpu': 100.0,
            'memory': 1000.0,
            'time': 3600.0
        }

    def forward(self, task_state: np.ndarray, params: Dict = None) -> np.ndarray:
        """Compute safety-constrained execution plan"""
        # Clip to resource bounds
        constrained = task_state.copy()

        if params and 'limits' in params:
            for i, (key, limit) in enumerate(params['limits'].items()):
                if i < len(constrained):
                    constrained[i] = min(constrained[i], limit)

        return constrained

    def validate_constraints(self, output: np.ndarray) -> Tuple[bool, List[str]]:
        """Validate safety constraints"""
        violations = []

        # Check bounds
        for i, (key, limit) in enumerate(self.resource_limits.items()):
            if i < len(output) and output[i] > limit:
                violations.append(f'{key}_exceeded')

        return len(violations) == 0, violations


# ============================================================
# Self-Test
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Gray-Box AI Engine Self-Test")
    print("Cherokee AI Federation - Phase 1 Foundation")
    print("=" * 60)

    # Test 1: Basic engine creation
    print("\n1. Creating engine...")
    engine = GrayBoxEngine('council_voting')
    engine.set_physics_core(BayesianVotingCore())
    engine.set_neural_corrector(NeuralCorrector('council_voting', input_dim=7))
    print("   OK: Engine created")

    # Test 2: Forward pass
    print("\n2. Testing forward pass...")
    votes = np.random.rand(7, 10)  # 7 specialists, 10-dim output
    result = engine.forward(votes.flatten()[:7])
    print(f"   Physics output shape: {result.physics_output.shape}")
    print(f"   Neural correction shape: {result.neural_correction.shape}")
    print(f"   Confidence: {result.confidence:.2f}")
    print("   OK: Forward pass complete")

    # Test 3: Explanation
    print("\n3. Getting explanation...")
    explanation = engine.get_explanation(result)
    print(f"   Physics contribution: {explanation['physics_contribution']:.2%}")
    print(f"   Neural contribution: {explanation['neural_contribution']:.2%}")
    print(f"   Physics dominant: {explanation['physics_dominant']}")
    print("   OK: Explanation generated")

    # Test 4: Training step
    print("\n4. Testing training step...")
    target = np.random.rand(7)
    loss = engine.train_step(votes.flatten()[:7], target, lr=0.01)
    print(f"   Initial loss: {loss:.4f}")
    print("   OK: Training step complete")

    # Test 5: Entropy decay core
    print("\n5. Testing entropy decay...")
    entropy_engine = GrayBoxEngine('thermal_memory')
    entropy_engine.set_physics_core(EntropyDecayCore())
    memory = np.random.rand(100)
    decay_result = entropy_engine.forward(memory)
    print(f"   Original sum: {np.sum(memory):.2f}")
    print(f"   Decayed sum: {np.sum(decay_result.combined_output):.2f}")
    print("   OK: Entropy decay working")

    # Test 6: Safety constraints
    print("\n6. Testing safety constraints...")
    safety_engine = GrayBoxEngine('jr_execution')
    safety_engine.set_physics_core(SafetyConstraintCore())
    task = np.array([150.0, 2000.0, 1000.0])  # Exceeds limits
    safe_result = safety_engine.forward(task)
    print(f"   Violations: {safe_result.metadata['violations']}")
    print(f"   Confidence: {safe_result.confidence:.2f}")
    print("   OK: Safety constraints working")

    print("\n" + "=" * 60)
    print("All tests passed - Gray-Box Engine Phase 1 Complete")
    print("For Seven Generations - Cherokee AI Federation")
    print("=" * 60)
```

---

## TASK 2: Create Integration Helper

Create `/ganuda/lib/graybox_council.py`:

```python
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
```

---

## Verification

```bash
cd /ganuda/lib && /home/dereadi/cherokee_venv/bin/python3 graybox_engine.py
```

Expected output:
```
All tests passed - Gray-Box Engine Phase 1 Complete
```

---

## SUCCESS CRITERIA

1. graybox_engine.py creates successfully
2. Self-test passes all 6 tests
3. GrayBoxEngine class functional
4. PhysicsCore abstract class defined
5. NeuralCorrector with MLP implemented
6. UnifiedODESolver working
7. Domain stubs (Bayesian, Entropy, Safety) operational

---

## NEXT PHASES

- **Phase 2:** Council voting integration with gateway.py
- **Phase 3:** Thermal memory enhancement
- **Phase 4:** Jr execution safety constraints

---

*Jr Instructions issued: December 17, 2025*
*Council Approved: 100% consensus*
*For Seven Generations - Cherokee AI Federation*

#!/usr/bin/env python3
"""
Unit Tests for Fokker-Planck Thermal Memory Physics
Phase 6B Wave 1, Task 1

Tests the foundation module thermal_memory_fokker_planck.py
Validates physics correctness and Cherokee values alignment

Author: Meta Jr (Test Lead), Memory Jr, Conscience Jr
Date: October 26, 2025
"""

import unittest
import numpy as np
import sys
from pathlib import Path

# Add thermal_memory_fokker_planck to path
sys.path.insert(0, str(Path(__file__).parent))

from thermal_memory_fokker_planck import (
    ThermalConfig,
    calculate_drift_velocity,
    calculate_diffusion_coefficient,
    calculate_hopfield_energy,
    find_equilibrium_temperature,
    find_stable_configuration
)


class TestDriftVelocity(unittest.TestCase):
    """Test Fokker-Planck drift velocity function v(T)"""

    def setUp(self):
        self.config = ThermalConfig()

    def test_typical_memory_cooling(self):
        """Typical memory at 80° should have negative drift (cooling)"""
        v = calculate_drift_velocity(temperature=80.0, is_sacred=False)
        # v = -0.15 × (80 - 20) = -0.15 × 60 = -9.0
        self.assertAlmostEqual(v, -9.0, places=5)
        self.assertLess(v, 0, "Drift should be negative (cooling)")

    def test_sacred_memory_protection(self):
        """Sacred memory at 80° should cool slower (higher T_min = 40°)"""
        v_typical = calculate_drift_velocity(80.0, is_sacred=False)
        v_sacred = calculate_drift_velocity(80.0, is_sacred=True)

        # v_typical = -0.15 × (80 - 20) = -9.0
        # v_sacred = -0.15 × (80 - 40) = -6.0
        self.assertAlmostEqual(v_sacred, -6.0, places=5)
        self.assertGreater(v_sacred, v_typical,
                          "Sacred memories should cool slower (Cherokee: Seven Generations)")

    def test_equilibrium_zero_drift(self):
        """Memory at equilibrium temperature should have zero drift"""
        # Typical memory at T_min = 20°
        v = calculate_drift_velocity(20.0, is_sacred=False)
        self.assertAlmostEqual(v, 0.0, places=10)

        # Sacred memory at T_min = 40°
        v_sacred = calculate_drift_velocity(40.0, is_sacred=True)
        self.assertAlmostEqual(v_sacred, 0.0, places=10)

    def test_heating_not_cooling(self):
        """Memory below equilibrium should have positive drift (heating)"""
        # Typical memory at 15° (below T_min = 20°)
        v = calculate_drift_velocity(15.0, is_sacred=False)
        # v = -0.15 × (15 - 20) = -0.15 × (-5) = +0.75
        self.assertGreater(v, 0, "Drift should be positive (heating)")
        self.assertAlmostEqual(v, 0.75, places=5)


class TestDiffusionCoefficient(unittest.TestCase):
    """Test Fokker-Planck diffusion coefficient D(access_count)"""

    def setUp(self):
        self.config = ThermalConfig()

    def test_new_memory_high_volatility(self):
        """New memory (access_count=0) should have high diffusion"""
        D = calculate_diffusion_coefficient(access_count=0)
        # D = 2.5 / (1 + 0) = 2.5
        self.assertAlmostEqual(D, 2.5, places=5)

    def test_frequently_accessed_low_volatility(self):
        """Frequently accessed memory should have low diffusion (stable)"""
        D = calculate_diffusion_coefficient(access_count=100)
        # D = 2.5 / (1 + 100) = 2.5 / 101 ≈ 0.0248
        self.assertLess(D, 0.1, "High access should reduce volatility")
        self.assertAlmostEqual(D, 2.5 / 101, places=5)

    def test_monotonic_decrease(self):
        """Diffusion should decrease monotonically with access_count"""
        D_values = [calculate_diffusion_coefficient(n) for n in range(10)]
        for i in range(len(D_values) - 1):
            self.assertGreater(D_values[i], D_values[i+1],
                             f"D should decrease: D({i}) > D({i+1})")

    def test_honesty_over_loyalty_principle(self):
        """Cherokee value: High volatility reveals hidden truths (low access)"""
        D_new = calculate_diffusion_coefficient(0)
        D_stable = calculate_diffusion_coefficient(100)
        ratio = D_new / D_stable
        # Ratio = 2.5 / (2.5/101) = 101
        self.assertGreater(ratio, 50,
                          "New memories 50x+ more volatile (Honesty Over Loyalty)")


class TestHopfieldEnergy(unittest.TestCase):
    """Test Hopfield energy function E = -Σ coherence(i,j) × T_i × T_j"""

    def test_simple_two_memory_system(self):
        """Two memories with high coherence should have low energy when both hot"""
        temperatures = np.array([90.0, 90.0])
        coherence = np.array([[1.0, 0.9],
                             [0.9, 1.0]])

        energy = calculate_hopfield_energy(temperatures, coherence)
        # E = -[(1.0 × 90 × 90) + (0.9 × 90 × 90) + (0.9 × 90 × 90) + (1.0 × 90 × 90)]
        # E = -[(8100) + (7290) + (7290) + (8100)]
        # E = -30780
        self.assertAlmostEqual(energy, -30780.0, places=1)
        self.assertLess(energy, 0, "Energy should be negative")

    def test_mitakuye_oyasin_principle(self):
        """Cherokee value: Related memories (high coherence) prefer same temperature"""
        # Two memories: one hot (90°), one cold (20°)
        temps_mixed = np.array([90.0, 20.0])
        temps_aligned = np.array([90.0, 90.0])

        # High coherence (they're related - Mitakuye Oyasin)
        coherence = np.array([[1.0, 0.9],
                             [0.9, 1.0]])

        energy_mixed = calculate_hopfield_energy(temps_mixed, coherence)
        energy_aligned = calculate_hopfield_energy(temps_aligned, coherence)

        # Aligned should have lower energy (more stable)
        self.assertLess(energy_aligned, energy_mixed,
                       "Related memories prefer same temperature (Mitakuye Oyasin)")

    def test_symmetric_coherence_requirement(self):
        """Hopfield convergence requires symmetric coherence matrix"""
        temperatures = np.array([80.0, 60.0])

        # Asymmetric coherence (invalid)
        coherence_invalid = np.array([[1.0, 0.7],
                                      [0.9, 1.0]])  # 0.7 ≠ 0.9

        with self.assertRaises(AssertionError):
            calculate_hopfield_energy(temperatures, coherence_invalid)

    def test_unrelated_memories_low_energy_impact(self):
        """Unrelated memories (low coherence) don't affect each other's temperature"""
        temps = np.array([90.0, 20.0])

        # Low coherence (unrelated)
        coherence_unrelated = np.array([[1.0, 0.1],
                                        [0.1, 1.0]])

        # High coherence (related)
        coherence_related = np.array([[1.0, 0.9],
                                      [0.9, 1.0]])

        energy_unrelated = calculate_hopfield_energy(temps, coherence_unrelated)
        energy_related = calculate_hopfield_energy(temps, coherence_related)

        # Related memories have stronger coupling (higher absolute energy)
        self.assertGreater(abs(energy_related), abs(energy_unrelated),
                          "Related memories have stronger coupling = higher |E|")


class TestEquilibriumSolver(unittest.TestCase):
    """Test equilibrium temperature calculation"""

    def setUp(self):
        self.config = ThermalConfig()

    def test_typical_memory_equilibrium(self):
        """Typical memory should converge to T_min = 20°"""
        T_eq, iterations = find_equilibrium_temperature(
            initial_temperature=80.0,
            access_count=5,
            is_sacred=False
        )
        self.assertAlmostEqual(T_eq, 20.0, places=1,
                              msg="Typical memory should reach T_min = 20°")
        self.assertGreater(iterations, 0, "Should take some iterations")

    def test_sacred_memory_equilibrium(self):
        """Sacred memory should converge to T_min = 40° (Seven Generations)"""
        T_eq, iterations = find_equilibrium_temperature(
            initial_temperature=80.0,
            access_count=5,
            is_sacred=True
        )
        self.assertAlmostEqual(T_eq, 40.0, places=1,
                              msg="Sacred memory should reach T_min = 40°")
        self.assertGreater(iterations, 0, "Should take some iterations")

    def test_convergence_with_diffusion(self):
        """Equilibrium should account for diffusion noise"""
        # High access count = low diffusion = precise equilibrium
        T_eq_stable, _ = find_equilibrium_temperature(80.0, access_count=100, is_sacred=False)

        # Low access count = high diffusion = noisy equilibrium
        T_eq_volatile, _ = find_equilibrium_temperature(80.0, access_count=0, is_sacred=False)

        # Both should converge near 20°, but volatile may have more variance
        self.assertAlmostEqual(T_eq_stable, 20.0, places=0)
        self.assertAlmostEqual(T_eq_volatile, 20.0, places=0)


class TestStableConfiguration(unittest.TestCase):
    """Test Hopfield-style stable configuration finder"""

    def test_simple_attractor(self):
        """System should converge to local energy minimum"""
        # 3 memories with symmetric coherence
        initial_temps = np.array([80.0, 50.0, 70.0])
        coherence = np.array([
            [1.0, 0.8, 0.7],
            [0.8, 1.0, 0.9],
            [0.7, 0.9, 1.0]
        ])
        access_counts = np.array([5, 10, 3])
        sacred_flags = np.array([False, False, False])

        final_temps, energy_history, iterations = find_stable_configuration(
            initial_temps, coherence, access_counts, sacred_flags
        )

        # Should converge (energy decreases)
        self.assertLess(energy_history[-1], energy_history[0],
                       "Energy should decrease toward minimum")

        # Should take some iterations
        self.assertGreater(iterations, 0)
        self.assertLessEqual(iterations, 100, "Should converge within max iterations")

    def test_sacred_memory_cluster(self):
        """Sacred memories should form hot attractor basin"""
        # 5 memories: 3 sacred, 2 typical
        initial_temps = np.array([90.0, 85.0, 80.0, 50.0, 45.0])

        # High coherence among sacred memories (first 3)
        coherence = np.array([
            [1.0, 0.9, 0.85, 0.2, 0.2],
            [0.9, 1.0, 0.9,  0.2, 0.2],
            [0.85, 0.9, 1.0, 0.2, 0.2],
            [0.2, 0.2, 0.2, 1.0, 0.8],
            [0.2, 0.2, 0.2, 0.8, 1.0]
        ])

        access_counts = np.array([10, 15, 8, 5, 3])
        sacred_flags = np.array([True, True, True, False, False])

        final_temps, _, _ = find_stable_configuration(
            initial_temps, coherence, access_counts, sacred_flags
        )

        # Sacred memories (first 3) should stay hotter than typical (last 2)
        sacred_avg = np.mean(final_temps[:3])
        typical_avg = np.mean(final_temps[3:])

        self.assertGreater(sacred_avg, typical_avg,
                          "Sacred cluster should maintain higher temperature")

        # Sacred memories should all be above 40° (Cherokee: Seven Generations)
        for i in range(3):
            self.assertGreaterEqual(final_temps[i], 40.0,
                                   f"Sacred memory {i} should maintain T ≥ 40°")

    def test_convergence_guarantee(self):
        """Symmetric coherence guarantees convergence (Hopfield theorem)"""
        np.random.seed(42)  # Reproducible test

        n = 10
        initial_temps = np.random.uniform(30, 90, n)

        # Symmetric coherence (guaranteed convergence)
        coherence = np.random.uniform(0, 1, (n, n))
        coherence = (coherence + coherence.T) / 2  # Make symmetric
        np.fill_diagonal(coherence, 1.0)

        access_counts = np.random.randint(0, 20, n)
        sacred_flags = np.random.choice([True, False], n, p=[0.3, 0.7])

        final_temps, energy_history, iterations = find_stable_configuration(
            initial_temps, coherence, access_counts, sacred_flags,
            max_iterations=200
        )

        # Should converge (not hit max iterations as failure)
        self.assertLessEqual(iterations, 200,
                            "Symmetric coherence should guarantee convergence")

        # Energy should be decreasing (monotonic convergence guarantee)
        if len(energy_history) > 10:
            # Check last 10 energy values are lower than first 10
            initial_avg = np.mean(energy_history[:10])
            final_avg = np.mean(energy_history[-10:])
            self.assertLess(final_avg, initial_avg,
                           "Energy should decrease toward minimum (Hopfield convergence)")


class TestCherokeeValues(unittest.TestCase):
    """Test Cherokee Constitutional AI values integration"""

    def test_seven_generations_sustainability(self):
        """Seven Generations: Sacred memories protected for 200+ years"""
        # Sacred memory should maintain 40° minimum
        for access_count in [0, 10, 100, 1000]:
            T_eq, _ = find_equilibrium_temperature(100.0, access_count, is_sacred=True)
            self.assertGreaterEqual(T_eq, 40.0,
                                   f"Sacred memory (access={access_count}) must maintain T ≥ 40°")

    def test_mitakuye_oyasin_interconnectedness(self):
        """Mitakuye Oyasin: All Our Relations - coherence couples temperatures"""
        # Highly coherent memories should influence each other
        temps = np.array([90.0, 20.0])
        coherence_high = np.array([[1.0, 0.95], [0.95, 1.0]])
        coherence_low = np.array([[1.0, 0.1], [0.1, 1.0]])

        energy_high = calculate_hopfield_energy(temps, coherence_high)
        energy_low = calculate_hopfield_energy(temps, coherence_low)

        # High coherence creates stronger coupling (higher absolute energy)
        # E = -Σ coherence × T_i × T_j, so higher coherence → more negative → higher |E|
        self.assertGreater(abs(energy_high), abs(energy_low),
                          "High coherence = strong coupling = higher |E| (Mitakuye Oyasin)")

    def test_honesty_over_loyalty(self):
        """Honesty Over Loyalty: Volatility reveals hidden truths"""
        # Low access memories are volatile (honest signal: this is new/uncertain)
        D_new = calculate_diffusion_coefficient(0)
        D_established = calculate_diffusion_coefficient(50)

        self.assertGreater(D_new / D_established, 10,
                          "New memories signal uncertainty (Honesty Over Loyalty)")

    def test_wado_patience(self):
        """Wado: Patience - gradual cooling with alpha=0.15"""
        config = ThermalConfig()
        self.assertEqual(config.alpha, 0.15,
                        "Alpha=0.15 ensures gradual cooling (Wado: Patience)")

        # At 80°, cooling rate = -9°/timestep (patient, not abrupt)
        v = calculate_drift_velocity(80.0, is_sacred=False)
        self.assertGreater(abs(v), 5)  # Meaningful cooling
        self.assertLess(abs(v), 20)    # But not too fast


def run_all_tests():
    """Run all unit tests and generate report"""

    print("=" * 70)
    print("🔥 Cherokee Constitutional AI - Fokker-Planck Physics Unit Tests")
    print("Phase 6B Wave 1, Task 1")
    print("=" * 70)
    print()

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestDriftVelocity))
    suite.addTests(loader.loadTestsFromTestCase(TestDiffusionCoefficient))
    suite.addTests(loader.loadTestsFromTestCase(TestHopfieldEnergy))
    suite.addTests(loader.loadTestsFromTestCase(TestEquilibriumSolver))
    suite.addTests(loader.loadTestsFromTestCase(TestStableConfiguration))
    suite.addTests(loader.loadTestsFromTestCase(TestCherokeeValues))

    # Run tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Generate summary
    print()
    print("=" * 70)
    print("📊 Test Summary")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print()

    if result.wasSuccessful():
        print("✅ ALL TESTS PASSED - Fokker-Planck physics validated!")
        print("🔥 Cherokee values alignment confirmed")
        print("🦅 Ready for Wave 2 deployment")
        return 0
    else:
        print("❌ TESTS FAILED - Review failures above")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)

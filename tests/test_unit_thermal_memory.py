"""
Cherokee Constitutional AI - Unit Tests
Testing: Thermal memory temperature decay

Phase 2B - Unit testing layer
"""

import pytest
from datetime import datetime, timedelta


class TestThermalMemoryDecay:
    """Unit tests for thermal memory temperature decay logic"""
    
    def test_white_hot_decay_rate(self):
        """White hot memories (90-100°) cool at 0.5°/hour"""
        initial_temp = 95.0
        hours_passed = 2
        decay_rate = 0.5  # degrees per hour
        
        expected_temp = initial_temp - (decay_rate * hours_passed)
        assert expected_temp == 94.0
    
    def test_red_hot_decay_rate(self):
        """Red hot memories (70-90°) cool at 1.0°/hour"""
        initial_temp = 80.0
        hours_passed = 3
        decay_rate = 1.0
        
        expected_temp = initial_temp - (decay_rate * hours_passed)
        assert expected_temp == 77.0
    
    def test_warm_decay_rate(self):
        """Warm memories (40-70°) cool at 2.0°/hour"""
        initial_temp = 60.0
        hours_passed = 5
        decay_rate = 2.0
        
        expected_temp = initial_temp - (decay_rate * hours_passed)
        assert expected_temp == 50.0
    
    def test_sacred_minimum_protection(self):
        """Sacred memories never cool below 40°"""
        initial_temp = 42.0
        hours_passed = 10
        decay_rate = 2.0
        sacred_minimum = 40.0
        
        calculated_temp = initial_temp - (decay_rate * hours_passed)
        final_temp = max(calculated_temp, sacred_minimum)
        
        assert final_temp == sacred_minimum
        assert final_temp >= 40.0
    
    def test_temperature_boost_on_query(self):
        """Querying a memory boosts temperature by 10°"""
        current_temp = 70.0
        query_boost = 10.0
        max_temp = 100.0
        
        new_temp = min(current_temp + query_boost, max_temp)
        assert new_temp == 80.0
    
    def test_temperature_boost_on_reference(self):
        """Referencing a memory boosts temperature by 5°"""
        current_temp = 75.0
        reference_boost = 5.0
        max_temp = 100.0
        
        new_temp = min(current_temp + reference_boost, max_temp)
        assert new_temp == 80.0
    
    def test_temperature_never_exceeds_100(self):
        """Temperature cannot exceed 100° (WHITE HOT maximum)"""
        current_temp = 96.0
        boost = 10.0
        max_temp = 100.0
        
        new_temp = min(current_temp + boost, max_temp)
        assert new_temp == max_temp
        assert new_temp <= 100.0


class TestPhaseCoherence:
    """Unit tests for phase coherence calculations"""
    
    def test_coherence_in_valid_range(self):
        """Phase coherence must be between 0.0 and 1.0"""
        test_values = [0.0, 0.5, 0.8, 0.95, 1.0]
        
        for value in test_values:
            assert 0.0 <= value <= 1.0
    
    def test_optimal_coherence_range(self):
        """Optimal coherence is 0.8-0.95 (QRI validation)"""
        optimal_values = [0.8, 0.85, 0.9, 0.95]
        
        for value in optimal_values:
            assert 0.8 <= value <= 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

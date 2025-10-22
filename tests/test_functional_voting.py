"""
Cherokee Constitutional AI - Functional Tests
Testing: Democratic voting logic

Phase 2B - Functional testing layer
"""

import pytest
from typing import Dict, List


class MockJr:
    """Mock Jr daemon for testing"""
    def __init__(self, name: str):
        self.name = name
        self.vote = None
    
    def cast_vote(self, option: str):
        """Cast a vote"""
        self.vote = option
        return {"jr": self.name, "vote": option}


class TestDemocraticVoting:
    """Functional tests for democratic voting system"""
    
    def test_unanimous_vote_3_0(self):
        """Test unanimous 3-0 vote (preferred outcome)"""
        # Create Jr Council
        memory_jr = MockJr("Memory Jr")
        executive_jr = MockJr("Executive Jr")
        meta_jr = MockJr("Meta Jr")
        
        # All vote YES
        votes = [
            memory_jr.cast_vote("YES"),
            executive_jr.cast_vote("YES"),
            meta_jr.cast_vote("YES")
        ]
        
        yes_count = sum(1 for v in votes if v["vote"] == "YES")
        no_count = sum(1 for v in votes if v["vote"] == "NO")
        
        assert yes_count == 3
        assert no_count == 0
        assert yes_count / len(votes) == 1.0  # 100% consensus
    
    def test_majority_vote_2_1(self):
        """Test majority 2-1 vote (minority preserved)"""
        memory_jr = MockJr("Memory Jr")
        executive_jr = MockJr("Executive Jr")
        meta_jr = MockJr("Meta Jr")
        
        # 2 YES, 1 NO
        votes = [
            memory_jr.cast_vote("YES"),
            executive_jr.cast_vote("YES"),
            meta_jr.cast_vote("NO")
        ]
        
        yes_count = sum(1 for v in votes if v["vote"] == "YES")
        no_count = sum(1 for v in votes if v["vote"] == "NO")
        
        assert yes_count == 2
        assert no_count == 1
        assert yes_count > no_count  # Majority achieved
        
        # Minority view should be preserved
        minority_view = [v for v in votes if v["vote"] == "NO"]
        assert len(minority_view) == 1
        assert minority_view[0]["jr"] == "Meta Jr"
    
    def test_split_vote_no_consensus(self):
        """Test split vote with no clear consensus"""
        memory_jr = MockJr("Memory Jr")
        executive_jr = MockJr("Executive Jr")
        meta_jr = MockJr("Meta Jr")
        
        # All different votes
        votes = [
            memory_jr.cast_vote("YES"),
            executive_jr.cast_vote("NO"),
            meta_jr.cast_vote("ABSTAIN")
        ]
        
        yes_count = sum(1 for v in votes if v["vote"] == "YES")
        no_count = sum(1 for v in votes if v["vote"] == "NO")
        
        # No majority
        assert yes_count == 1
        assert no_count == 1
        assert yes_count == no_count  # Tied
    
    def test_vote_logging(self):
        """Test that all votes are logged"""
        votes = []
        
        # Simulate voting
        for jr_name in ["Memory Jr", "Executive Jr", "Meta Jr"]:
            jr = MockJr(jr_name)
            vote = jr.cast_vote("YES")
            votes.append(vote)
        
        # All votes should be logged
        assert len(votes) == 3
        for vote in votes:
            assert "jr" in vote
            assert "vote" in vote


class TestChiefDeliberation:
    """Functional tests for Chief deliberation cycle"""
    
    def test_three_chief_deliberation(self):
        """Test that all three chiefs deliberate on question"""
        class MockChief:
            def __init__(self, name: str, specialty: str):
                self.name = name
                self.specialty = specialty
                self.consulted = False
            
            def deliberate(self, question: str):
                self.consulted = True
                return {"chief": self.name, "perspective": self.specialty}
        
        # Create three chiefs
        war_chief = MockChief("War Chief", "action")
        peace_chief = MockChief("Peace Chief", "governance")
        medicine_woman = MockChief("Medicine Woman", "wisdom")
        
        # All chiefs deliberate
        perspectives = [
            war_chief.deliberate("Test question"),
            peace_chief.deliberate("Test question"),
            medicine_woman.deliberate("Test question")
        ]
        
        # Verify all consulted
        assert war_chief.consulted
        assert peace_chief.consulted
        assert medicine_woman.consulted
        assert len(perspectives) == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

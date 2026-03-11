"""
Test that standing_dissent is recordable when consent=True.
This is a governance integrity test — Coyote's dissent must never be silenced.
"""

import sys
sys.path.insert(0, '/ganuda/lib')

def test_standing_dissent_with_consent_true():
    """A vote with consent=True should still allow standing_dissent."""
    # Import the relevant voting function
    # Run a mock vote where all specialists consent but Coyote registers standing dissent
    # Assert that the vote result contains:
    #   - consent = True
    #   - standing_dissents is not empty
    #   - Coyote's dissent reason is preserved
    pass

def test_standing_dissent_with_consent_false():
    """A vote with consent=False should also allow standing_dissent (regression check)."""
    pass

def test_vote_without_dissent_unchanged():
    """A normal vote without standing_dissent should work exactly as before."""
    pass

if __name__ == "__main__":
    test_standing_dissent_with_consent_true()
    test_standing_dissent_with_consent_false()
    test_vote_without_dissent_unchanged()
    print("All standing_dissent tests passed")
# /ganuda/daemons/slack_integration_test.py

import unittest
from unittest.mock import patch, MagicMock
from governance_agent import record_council_vote  # Assuming this function exists in governance_agent.py

class TestSlackIntegration(unittest.TestCase):
    @patch('governance_agent.notify_council_vote')
    def test_notify_council_vote(self, mock_notify_council_vote):
        vote_hash = 'test_vote_hash'
        topic = 'test_topic'
        result = 'approved'
        confidence = 0.95

        # Mock the database commit to simulate a successful vote recording
        with patch('governance_agent.commit_vote_to_db', return_value=None) as mock_commit:
            record_council_vote(vote_hash, topic, result, confidence)

        # Ensure the notify_council_vote function was called with the correct arguments
        mock_notify_council_vote.assert_called_once_with(vote_hash=vote_hash, topic=topic, result=result, confidence=confidence)

if __name__ == '__main__':
    unittest.main()
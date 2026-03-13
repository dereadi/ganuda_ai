import unittest
from unittest.mock import patch, Mock
from ganuda.lib.sub_agent_dispatch import SubAgentDispatch, SubAgentTimeout, SubAgentError

class TestSubAgentDispatch(unittest.TestCase):

    def setUp(self):
        self.dispatch = SubAgentDispatch()

    @patch('ganuda.lib.sub_agent_dispatch.requests.get')
    def test_health_check_redfin(self, mock_get):
        mock_get.return_value.status_code = 200
        result = self.dispatch.health_check('redfin-fast')
        self.assertTrue(result)

    @patch('ganuda.lib.sub_agent_dispatch.requests.get')
    def test_health_check_sasass(self, mock_get):
        mock_get.return_value.status_code = 200
        result = self.dispatch.health_check('sasass-general')
        self.assertTrue(result)

    @patch('ganuda.lib.sub_agent_dispatch.requests.get')
    def test_health_check_sasass2(self, mock_get):
        mock_get.return_value.status_code = 200
        result = self.dispatch.health_check('sasass2-executive')
        self.assertTrue(result)

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_dispatch_success(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': 'Hello, world!'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.dispatch('redfin-fast', 'System prompt', 'User content')
        self.assertEqual(result, 'Hello, world!')

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_dispatch_timeout(self, mock_post):
        mock_post.side_effect = TimeoutError
        with self.assertRaises(SubAgentTimeout):
            self.dispatch.dispatch('redfin-fast', 'System prompt', 'User content')

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_dispatch_error(self, mock_post):
        mock_post.side_effect = Exception
        with self.assertRaises(SubAgentError):
            self.dispatch.dispatch('redfin-fast', 'System prompt', 'User content')

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_fallback_chain(self, mock_post):
        mock_post.side_effect = [TimeoutError, TimeoutError, Mock(json=lambda: {'choices': [{'message': {'content': 'Hello, world!'}}]})]
        result = self.dispatch.dispatch('sasass-general', 'System prompt', 'User content')
        self.assertEqual(result, 'Hello, world!')

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_scan_stubs(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '[{"type": "person", "name": "John Doe", "context": "John Doe is a software engineer."}]'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.scan_stubs('Sample content')
        self.assertEqual(result, [{'type': 'person', 'name': 'John Doe', 'context': 'John Doe is a software engineer.'}])

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_classify_thermal(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '{"category": "governance", "temperature": 70, "keywords": ["policy", "regulation", "compliance"]}'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.classify_thermal('Sample thermal text')
        self.assertEqual(result, {'category': 'governance', 'temperature': 70, 'keywords': ['policy', 'regulation', 'compliance']})

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_route_task(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '{"domain": "war_chief", "priority": 1, "reason": "Critical infrastructure issue"}'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.route_task('Task title', 'Task description')
        self.assertEqual(result, {'domain': 'war_chief', 'priority': 1, 'reason': 'Critical infrastructure issue'})

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_decompose_task(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '["Step 1: Identify the problem", "Step 2: Analyze the root cause", "Step 3: Implement a solution"]'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.decompose_task('JR instruction')
        self.assertEqual(result, ['Step 1: Identify the problem', 'Step 2: Analyze the root cause', 'Step 3: Implement a solution'])

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_safety_check(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '{"safe": true, "concerns": [], "recommendation": "Proceed with caution"}'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.safety_check('Proposed action')
        self.assertEqual(result, {'safe': True, 'concerns': [], 'recommendation': 'Proceed with caution'})

    @patch('ganuda.lib.sub_agent_dispatch.requests.post')
    def test_check_phi_anomaly(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'choices': [{'message': {'content': '{"anomalous": false, "interpretation": "Normal resting state", "escalate": false}'}}]}
        mock_post.return_value = mock_response
        result = self.dispatch.check_phi_anomaly(0.05, {'state': 'resting'})
        self.assertEqual(result, {'anomalous': False, 'interpretation': 'Normal resting state', 'escalate': False})

if __name__ == '__main__':
    unittest.main()
import unittest
from datetime import datetime, timedelta
from ganuda.lib.partner_rhythm import (
    collect_breadcrumbs,
    PartnerBands,
    TopicTrajectory,
    SacredBurstDetector,
    Anticipator
)

class TestPartnerRhythm(unittest.TestCase):

    def setUp(self):
        # Mock data for testing
        self.mock_thermal_memory = [
            {"created_at": "2026-03-12T08:15:00-05:00", "temperature_score": 92.8, "sacred_pattern": True, "domain_tag": "governance"},
            {"created_at": "2026-03-12T09:00:00-05:00", "temperature_score": 75.0, "sacred_pattern": False, "domain_tag": "technical"}
        ]
        self.mock_jr_tasks = [
            {"created_at": "2026-03-12T09:00:00-05:00", "title": "Build new feature", "tags": ["P1", "technical"], "priority": 1, "status": "created"},
            {"created_at": "2026-03-12T21:00:00-05:00", "title": "Review code", "tags": ["P2", "technical"], "priority": 2, "status": "completed"}
        ]
        self.mock_council_votes = [
            {"voted_at": "2026-03-12T10:00:00-05:00", "question": "Should we implement X?", "confidence": 0.9}
        ]
        self.mock_longhouse_sessions = [
            {"created_at": "2026-03-12T14:00:00-05:00", "problem_statement": "How to improve Y?", "voices_count": 5}
        ]
        self.mock_git_log = [
            {"timestamp": "2026-03-12T15:00:00-05:00", "message": "Fix bug in Z"}
        ]
        self.mock_file_modifications = [
            {"timestamp": "2026-03-12T16:00:00-05:00", "path": "/ganuda/lib/module.py"}
        ]

    def test_collect_breadcrumbs(self):
        breadcrumbs = collect_breadcrumbs(24)
        self.assertEqual(len(breadcrumbs), 6)
        self.assertIn("timestamp", breadcrumbs[0])
        self.assertIn("source", breadcrumbs[0])
        self.assertIn("signal_type", breadcrumbs[0])
        self.assertIn("intensity", breadcrumbs[0])
        self.assertIn("content_summary", breadcrumbs[0])
        self.assertIn("raw_data", breadcrumbs[0])

    def test_partner_bands(self):
        bands = PartnerBands()
        bands_data = bands.compute_bands(7)
        self.assertIn("2026-03-12", bands_data)
        self.assertIn("total", bands_data["2026-03-12"])
        self.assertIn("ma", bands_data["2026-03-12"])
        self.assertIn("upper_band", bands_data["2026-03-12"])
        self.assertIn("lower_band", bands_data["2026-03-12"])
        self.assertIn("signal", bands_data["2026-03-12"])

        hourly_profile = bands.compute_hourly_profile(30)
        self.assertIn(8, hourly_profile)
        self.assertIn("avg_thermals", hourly_profile[8])
        self.assertIn("avg_sacred", hourly_profile[8])
        self.assertIn("avg_tasks", hourly_profile[8])
        self.assertIn("dominant_domain", hourly_profile[8])
        self.assertIn("intensity", hourly_profile[8])

        phase = bands.detect_phase()
        self.assertIn(phase, ["ACCUMULATION", "BREAKOUT", "DISTRIBUTION", "EXHAUSTION", "RESTING"])

        prediction = bands.predict_next_phase()
        self.assertIn("predicted_phase", prediction)
        self.assertIn("confidence", prediction)
        self.assertIn("reasoning", prediction)
        self.assertIn("suggested_preparation", prediction)

    def test_topic_trajectory(self):
        trajectory = TopicTrajectory()
        topics = trajectory.extract_topics(30)
        self.assertGreater(len(topics), 0)
        self.assertIn("topic", topics[0])
        self.assertIn("first_seen", topics[0])
        self.assertIn("last_seen", topics[0])
        self.assertIn("intensity_curve", topics[0])
        self.assertIn("tasks_created", topics[0])
        self.assertIn("sacred_count", topics[0])

        spiral = trajectory.detect_spiral()
        self.assertIn("ascending", spiral)
        self.assertIn("dormant", spiral)
        self.assertIn("returning", spiral)
        self.assertIn("predicted_next", spiral)

        interest = trajectory.predict_interest()
        self.assertGreater(len(interest), 0)
        self.assertIn("topic", interest[0])
        self.assertIn("probability", interest[0])
        self.assertIn("reasoning", interest[0])
        self.assertIn("preparation_action", interest[0])

    def test_sacred_burst_detector(self):
        detector = SacredBurstDetector()
        burst = detector.detect_burst()
        self.assertIn("active", burst)
        self.assertIn("start_time", burst)
        self.assertIn("sacred_count", burst)
        self.assertIn("dominant_topic", burst)
        self.assertIn("estimated_duration", burst)

        window = detector.predict_sacred_window()
        self.assertIn("next_likely_window", window)
        self.assertIn("confidence", window)
        self.assertIn("topic_prediction", window)

    def test_anticipator(self):
        anticipator = Anticipator()
        anticipator.prepare_for_phase("BREAKOUT")
        anticipator.prepare_for_topic([{"topic": "governance", "probability": 0.8, "reasoning": "Recent focus", "preparation_action": "Warm council members"}])
        anticipator.prepare_for_sacred({"next_likely_window": "2026-03-13T08:00:00-05:00", "confidence": 0.9, "topic_prediction": "governance"})

if __name__ == "__main__":
    unittest.main()
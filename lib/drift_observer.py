import json
import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

class DriftObserver:
    def __init__(self, governance_state_path: str):
        self.governance_state_path = governance_state_path
        self.services: Dict[str, Dict] = {}
        self.load_governance_state()

    def load_governance_state(self):
        with open(self.governance_state_path, 'r') as f:
            governance_state = json.load(f)
        self.drift_observation_enabled = governance_state.get('dc15_drift_observation_enabled', False)

    def calculate_drift_score(self, service_name: str, cpu_memory_delta: float, error_rate_change: float, response_time_deviation: float, time_since_last_check: int) -> int:
        """
        Calculate the drift score for a given service.
        
        :param service_name: Name of the service
        :param cpu_memory_delta: Delta in CPU/memory usage from baseline (0-30 points)
        :param error_rate_change: Change in error rate (0-30 points)
        :param response_time_deviation: Deviation in response time (0-20 points)
        :param time_since_last_check: Time since last check (0-20 points)
        :return: Drift score (0-100)
        """
        drift_score = (
            min(cpu_memory_delta, 30) +
            min(error_rate_change, 30) +
            min(response_time_deviation, 20) +
            min(time_since_last_check, 20)
        )
        return drift_score

    def update_service_drift(self, service_name: str, cpu_memory_delta: float, error_rate_change: float, response_time_deviation: float, time_since_last_check: int):
        if not self.drift_observation_enabled:
            return

        drift_score = self.calculate_drift_score(service_name, cpu_memory_delta, error_rate_change, response_time_deviation, time_since_last_check)
        self.services[service_name] = {
            'drift_score': drift_score,
            'last_checked': time_since_last_check
        }
        logger.info(f"Updated drift score for {service_name}: {drift_score}")

    def should_check_service(self, service_name: str) -> bool:
        if not self.drift_observation_enabled:
            return True

        service = self.services.get(service_name, {})
        drift_score = service.get('drift_score', 0)
        if drift_score > 50:
            logger.info(f"High drift detected for {service_name} (score: {drift_score}), checking now.")
            return True
        elif drift_score == 0:
            logger.info(f"No drift detected for {service_name} (score: {drift_score}), checking on schedule.")
            return False
        else:
            logger.info(f"Low drift detected for {service_name} (score: {drift_score}), skipping check.")
            return False

    def log_metrics(self):
        checks_skipped = sum(1 for service in self.services.values() if not self.should_check_service(service['name']))
        checks_run = len(self.services) - checks_skipped
        avg_drift_score = sum(service['drift_score'] for service in self.services.values()) / len(self.services) if self.services else 0
        logger.info(f"Metrics: checks_skipped={checks_skipped}, checks_run={checks_run}, avg_drift_score={avg_drift_score:.2f}")
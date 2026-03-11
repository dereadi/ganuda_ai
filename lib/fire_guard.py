import json
import logging
from typing import Dict, List, Tuple

# Assuming these are part of the project's existing modules
from ganuda.lib.service_registry import ServiceRegistry
from ganuda.lib.metrics import MetricsCollector
from ganuda.lib.config import Config

logger = logging.getLogger(__name__)

class DriftObserver:
    def __init__(self, config_path: str = '.governance_state.json'):
        self.config = Config(config_path)
        self.service_registry = ServiceRegistry()
        self.metrics_collector = MetricsCollector()
        self.drift_scores: Dict[str, int] = {}
        self.feature_flag = self.config.get('dc15_drift_observation_enabled', False)

    def calculate_drift_score(self, service_name: str) -> int:
        service = self.service_registry.get_service(service_name)
        if not service:
            logger.error(f"Service {service_name} not found.")
            return 0

        cpu_memory_delta = min(30, abs(service.cpu_usage - service.baseline_cpu_usage))
        error_rate_change = min(30, abs(service.error_rate - service.baseline_error_rate))
        response_time_deviation = min(20, abs(service.response_time - service.baseline_response_time))
        time_since_last_check = min(20, (service.current_time - service.last_check_time) // 3600)  # hours

        drift_score = cpu_memory_delta + error_rate_change + response_time_deviation + time_since_last_check
        return drift_score

    def update_drift_scores(self):
        for service_name in self.service_registry.get_all_services():
            self.drift_scores[service_name] = self.calculate_drift_score(service_name)

    def should_check_service(self, service_name: str) -> bool:
        if not self.feature_flag:
            return True

        drift_score = self.drift_scores.get(service_name, 0)
        if drift_score == 0:
            return False  # Only check zero-drift services on schedule

        return True

    def run_checks(self):
        for service_name in self.service_registry.get_all_services():
            if self.should_check_service(service_name):
                self.metrics_collector.increment('checks_run')
                logger.info(f"Checking service {service_name} with drift score {self.drift_scores[service_name]}")
            else:
                self.metrics_collector.increment('checks_skipped')
                logger.info(f"Skipped checking service {service_name} due to low drift score")

    def log_metrics(self):
        avg_drift_score = sum(self.drift_scores.values()) / len(self.drift_scores) if self.drift_scores else 0
        logger.info(f"Metrics: checks_skipped={self.metrics_collector.get('checks_skipped')}, "
                    f"checks_run={self.metrics_collector.get('checks_run')}, "
                    f"avg_drift_score={avg_drift_score}")

    def start(self):
        self.update_drift_scores()
        self.run_checks()
        self.log_metrics()

# Example usage
if __name__ == "__main__":
    observer = DriftObserver()
    observer.start()
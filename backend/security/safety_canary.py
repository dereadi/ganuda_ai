# /ganuda/backend/security/safety_canary.py

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SafetyCanary:
    """
    Enhances the safety canary features to monitor and report on the health and security of the cluster.
    """

    def __init__(self, nodes: List[str], thresholds: Dict[str, float]):
        """
        Initialize the SafetyCanary with a list of nodes and their respective thresholds.

        :param nodes: List of node names to monitor.
        :param thresholds: Dictionary mapping node names to their threshold values.
        """
        self.nodes = nodes
        self.thresholds = thresholds
        self.alerts: List[Dict[str, Any]] = []

    def monitor_nodes(self) -> None:
        """
        Monitor the health of each node and generate alerts if any node exceeds its threshold.
        """
        for node in self.nodes:
            current_load = self._get_node_load(node)
            if current_load > self.thresholds[node]:
                self._generate_alert(node, current_load)

    def _get_node_load(self, node: str) -> float:
        """
        Retrieve the current load of a given node.

        :param node: Name of the node.
        :return: Current load of the node.
        """
        # Simulate retrieving the node load (replace with actual implementation)
        return 0.06  # Example load value

    def _generate_alert(self, node: str, load: float) -> None:
        """
        Generate an alert for a node that has exceeded its threshold.

        :param node: Name of the node.
        :param load: Current load of the node.
        """
        alert = {
            "node": node,
            "current_load": load,
            "threshold": self.thresholds[node],
            "timestamp": self._get_current_time()
        }
        self.alerts.append(alert)
        logger.warning(f"Alert generated for node {node}: Load {load} exceeds threshold {self.thresholds[node]}")

    def _get_current_time(self) -> str:
        """
        Get the current time in a formatted string.

        :return: Current time as a string.
        """
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get the list of generated alerts.

        :return: List of alerts.
        """
        return self.alerts

# Example usage
if __name__ == "__main__":
    nodes = ["owlfin", "eaglefin", "bluefin", "sasass", "sasass2"]
    thresholds = {
        "owlfin": 0.1,
        "eaglefin": 0.1,
        "bluefin": 0.7,
        "sasass": 0.5,
        "sasass2": 0.5
    }

    canary = SafetyCanary(nodes, thresholds)
    canary.monitor_nodes()
    print(canary.get_alerts())
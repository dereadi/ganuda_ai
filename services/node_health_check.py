import requests
from typing import Dict, Any

class NodeHealthCheck:
    """
    Class to perform health checks on cluster nodes.
    """

    def __init__(self, base_url: str):
        """
        Initialize the NodeHealthCheck with the base URL of the cluster.
        
        :param base_url: Base URL of the cluster
        """
        self.base_url = base_url

    def check_node(self, node_name: str) -> Dict[str, Any]:
        """
        Check the health of a specific node.
        
        :param node_name: Name of the node to check
        :return: Dictionary containing the health status of the node
        """
        url = f"{self.base_url}/nodes/{node_name}/health"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def check_all_nodes(self) -> Dict[str, Dict[str, Any]]:
        """
        Check the health of all nodes in the cluster.
        
        :return: Dictionary containing the health status of all nodes
        """
        nodes = ["owlfin", "eaglefin", "bluefin", "sasass", "sasass2", "redfin"]
        health_status = {}
        for node in nodes:
            health_status[node] = self.check_node(node)
        return health_status

def main():
    """
    Main function to run the node health checks.
    """
    base_url = "http://cluster.ganuda.us"
    health_checker = NodeHealthCheck(base_url)
    all_nodes_health = health_checker.check_all_nodes()
    print(all_nodes_health)

if __name__ == "__main__":
    main()
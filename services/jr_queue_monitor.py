import logging
from typing import List, Dict
from datetime import datetime

# Assuming these modules are part of the project
from ganuda.services.jr_executor import JrExecutor
from ganuda.services.node_health import NodeHealthMonitor
from ganuda.models.task import Task
from ganuda.utils import get_current_temperature

logger = logging.getLogger(__name__)

class JrQueueMonitor:
    def __init__(self, executor: JrExecutor, node_monitor: NodeHealthMonitor):
        self.executor = executor
        self.node_monitor = node_monitor
        self.last_check_time: datetime = datetime.now()

    def monitor_queue(self) -> None:
        """
        Monitor the Jr task queue and log the status.
        """
        pending_tasks: List[Task] = self.executor.get_pending_tasks()
        completed_tasks: List[Task] = self.executor.get_completed_tasks()
        
        logger.info(f"Jr Queue Status - {datetime.now()}")
        logger.info(f"Pending Tasks: {len(pending_tasks)}")
        logger.info(f"Completed Tasks: {len(completed_tasks)}")

        if len(pending_tasks) < 5:
            logger.warning("Low number of pending tasks. Consider adding more tasks to the queue.")

    def check_node_health(self) -> None:
        """
        Check the health of all nodes and log the status.
        """
        node_status: Dict[str, Dict] = self.node_monitor.get_node_status()
        
        for node, status in node_status.items():
            logger.info(f"Node {node} - Load: {status['load']}, Temperature: {status['temperature']}°C")

            if status['load'] < 0.1:
                logger.warning(f"Node {node} is idle. Consider assigning more tasks.")
            
            if status['temperature'] < 40:
                logger.warning(f"Node {node} is cool. Consider increasing the workload.")

    def run(self) -> None:
        """
        Run the monitoring process.
        """
        self.monitor_queue()
        self.check_node_health()

        # Log the current average temperature of the cluster
        avg_temp: float = get_current_temperature()
        logger.info(f"Average Cluster Temperature: {avg_temp}°C")

        # Schedule the next check
        self.last_check_time = datetime.now()
        self.schedule_next_check()

    def schedule_next_check(self) -> None:
        """
        Schedule the next check based on the last check time.
        """
        next_check_time: datetime = self.last_check_time + timedelta(minutes=5)
        logger.info(f"Scheduled next check at {next_check_time}")

if __name__ == "__main__":
    # Initialize the JrExecutor and NodeHealthMonitor
    executor = JrExecutor()
    node_monitor = NodeHealthMonitor()

    # Create and run the JrQueueMonitor
    monitor = JrQueueMonitor(executor, node_monitor)
    monitor.run()
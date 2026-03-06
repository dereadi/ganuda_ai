import subprocess
import logging
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NetworkManager:
    """
    Manages network configurations and failover using Keepalived.
    """

    def __init__(self, config_path: str):
        """
        Initialize the NetworkManager with the path to the Keepalived configuration file.

        :param config_path: Path to the Keepalived configuration file.
        """
        self.config_path = config_path

    def start_keepalived(self) -> None:
        """
        Start the Keepalived service.
        """
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'keepalived'], check=True)
            logger.info("Keepalived started successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to start Keepalived: {e}")

    def stop_keepalived(self) -> None:
        """
        Stop the Keepalived service.
        """
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'keepalived'], check=True)
            logger.info("Keepalived stopped successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to stop Keepalived: {e}")

    def restart_keepalived(self) -> None:
        """
        Restart the Keepalived service.
        """
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'keepalived'], check=True)
            logger.info("Keepalived restarted successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to restart Keepalived: {e}")

    def reload_keepalived(self) -> None:
        """
        Reload the Keepalived service to apply new configuration.
        """
        try:
            subprocess.run(['sudo', 'systemctl', 'reload', 'keepalived'], check=True)
            logger.info("Keepalived reloaded successfully.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to reload Keepalived: {e}")

    def check_status(self) -> Optional[str]:
        """
        Check the status of the Keepalived service.

        :return: Status output or None if an error occurs.
        """
        try:
            result = subprocess.run(['sudo', 'systemctl', 'status', 'keepalived'], capture_output=True, text=True, check=True)
            return result.stdout
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to check Keepalived status: {e}")
            return None

if __name__ == "__main__":
    # Example usage
    config_path = "/etc/keepalived/keepalived.conf"
    network_manager = NetworkManager(config_path)
    network_manager.start_keepalived()
    status = network_manager.check_status()
    if status:
        print(status)
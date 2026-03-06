import os
from typing import Dict, List

class KeepalivedConfig:
    """
    Class to manage Keepalived configuration.
    """

    def __init__(self, config_path: str = '/etc/keepalived/keepalived.conf'):
        self.config_path = config_path
        self.config_data: Dict[str, str] = {}

    def load_config(self) -> None:
        """
        Load the current Keepalived configuration from the specified path.
        """
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as file:
                self.config_data = {line.strip(): '' for line in file.readlines() if line.strip()}
        else:
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")

    def save_config(self) -> None:
        """
        Save the current Keepalived configuration to the specified path.
        """
        with open(self.config_path, 'w') as file:
            for key in self.config_data:
                file.write(f"{key}\n")

    def set_vrrp_instance(self, instance_name: str, interface: str, state: str, priority: int, virtual_router_id: int) -> None:
        """
        Set VRRP instance configuration.
        """
        vrrp_config = [
            f"vrrp_instance {instance_name} {{",
            f"    interface {interface}",
            f"    state {state}",
            f"    priority {priority}",
            f"    virtual_router_id {virtual_router_id}",
            "}"
        ]
        self.config_data.update({line: '' for line in vrrp_config})

    def set_virtual_ip(self, instance_name: str, ip_address: str) -> None:
        """
        Set virtual IP address for a VRRP instance.
        """
        vrrp_config = [
            f"vrrp_instance {instance_name} {{",
            f"    virtual_ipaddress {{",
            f"        {ip_address}",
            "    }",
            "}"
        ]
        self.config_data.update({line: '' for line in vrrp_config})

    def remove_vrrp_instance(self, instance_name: str) -> None:
        """
        Remove VRRP instance configuration.
        """
        vrrp_config = [
            f"vrrp_instance {instance_name} {{",
            "}"
        ]
        for line in vrrp_config:
            if line in self.config_data:
                del self.config_data[line]

    def get_config(self) -> List[str]:
        """
        Get the current Keepalived configuration as a list of strings.
        """
        return list(self.config_data.keys())
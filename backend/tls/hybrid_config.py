import os
from typing import Dict, Optional

class HybridTLSConfig:
    """
    Class to manage hybrid TLS configurations.
    """

    def __init__(self, config_path: str):
        """
        Initialize the HybridTLSConfig with the path to the configuration file.

        :param config_path: Path to the configuration file.
        """
        self.config_path = config_path
        self.config: Dict[str, str] = self._load_config()

    def _load_config(self) -> Dict[str, str]:
        """
        Load the configuration from the specified file.

        :return: Dictionary containing the configuration settings.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found at {self.config_path}")

        with open(self.config_path, 'r') as file:
            lines = file.readlines()
            config = {}
            for line in lines:
                key, value = line.strip().split('=')
                config[key] = value
        return config

    def get_config_value(self, key: str) -> Optional[str]:
        """
        Get the value of a specific configuration key.

        :param key: Configuration key to retrieve.
        :return: Value of the key if it exists, otherwise None.
        """
        return self.config.get(key)

    def set_config_value(self, key: str, value: str) -> None:
        """
        Set the value of a specific configuration key.

        :param key: Configuration key to set.
        :param value: Value to set for the key.
        """
        self.config[key] = value
        self._save_config()

    def _save_config(self) -> None:
        """
        Save the current configuration to the file.
        """
        with open(self.config_path, 'w') as file:
            for key, value in self.config.items():
                file.write(f"{key}={value}\n")

    def enable_hybrid_tls(self) -> None:
        """
        Enable hybrid TLS configuration.
        """
        self.set_config_value('tls_mode', 'hybrid')

    def disable_hybrid_tls(self) -> None:
        """
        Disable hybrid TLS configuration.
        """
        self.set_config_value('tls_mode', 'standard')
import os
import subprocess
from typing import List

class Installer:
    """
    Installer class for setting up backend components.
    """

    def __init__(self, components: List[str]):
        self.components = components

    def install_component(self, component: str) -> None:
        """
        Install a single backend component.
        """
        print(f"Installing {component}...")
        try:
            subprocess.run(['pip', 'install', component], check=True)
            print(f"{component} installed successfully.")
        except subprocess.CalledProcessError as e:
            print(f"Failed to install {component}: {e}")

    def install_all(self) -> None:
        """
        Install all specified backend components.
        """
        for component in self.components:
            self.install_component(component)

def main() -> None:
    """
    Main function to run the installer.
    """
    components_to_install = [
        'flask',
        'pymongo',
        'requests',
        'pydantic'
    ]
    installer = Installer(components_to_install)
    installer.install_all()

if __name__ == "__main__":
    main()
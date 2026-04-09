#!/usr/bin/env python3
"""Shield Agent — Configuration loader and defaults."""

import os
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

DEFAULT_CONFIG_PATH = os.path.expanduser("~/.ganuda-shield/config.yaml")

@dataclass
class ShieldConfig:
    server_url: str = "https://localhost:8443"
    machine_id: str = ""
    employee_id: str = ""
    jurisdiction: str = "standard"  # standard, gdpr, ccpa

    # Capture settings
    capture_interval: int = 60
    clipboard_types: bool = True
    clipboard_content: bool = False  # ONLY on admin escalation
    application_tracking: bool = True
    idle_detection: bool = True
    network_connections: str = "count"  # count or detail
    usb_monitoring: bool = True
    file_access_patterns: bool = True
    screenshots: bool = False  # ONLY on anomaly + admin auth

    # Transport
    batch_interval: int = 60
    buffer_max_hours: int = 24

    # Tray
    tray_visible: bool = True  # CANNOT be false
    dashboard_url: str = ""

    def __post_init__(self):
        if not self.machine_id:
            import socket
            self.machine_id = socket.gethostname()
        if not self.dashboard_url:
            self.dashboard_url = f"{self.server_url}/me/{self.employee_id}"
        # Enforce: tray always visible
        self.tray_visible = True
        # Enforce: no content capture without explicit escalation
        if self.clipboard_content:
            self.clipboard_content = False  # reset — requires runtime admin override


def load_config(path: str = DEFAULT_CONFIG_PATH) -> ShieldConfig:
    """Load config from YAML, with safe defaults."""
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        shield = data.get('shield', {})
        capture = data.get('capture', {})
        transport = data.get('transport', {})
        return ShieldConfig(
            server_url=shield.get('server_url', ShieldConfig.server_url),
            machine_id=shield.get('machine_id', '') or '',
            employee_id=shield.get('employee_id', ''),
            jurisdiction=shield.get('jurisdiction', 'standard'),
            capture_interval=capture.get('interval_seconds', 60),
            clipboard_types=capture.get('clipboard_types', True),
            application_tracking=capture.get('application_tracking', True),
            idle_detection=capture.get('idle_detection', True),
            network_connections=capture.get('network_connections', 'count'),
            usb_monitoring=capture.get('usb_monitoring', True),
            file_access_patterns=capture.get('file_access_patterns', True),
            batch_interval=transport.get('batch_interval_seconds', 60),
            buffer_max_hours=transport.get('buffer_max_hours', 24),
        )
    return ShieldConfig()


def save_default_config(path: str = DEFAULT_CONFIG_PATH):
    """Write default config for new installations."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    config = {
        'shield': {
            'server_url': 'https://shield.company.internal:8443',
            'machine_id': 'auto',
            'employee_id': '',
            'jurisdiction': 'standard',
        },
        'capture': {
            'interval_seconds': 60,
            'clipboard_types': True,
            'clipboard_content': False,
            'application_tracking': True,
            'idle_detection': True,
            'network_connections': 'count',
            'usb_monitoring': True,
            'file_access_patterns': True,
            'screenshots': False,
        },
        'transport': {
            'batch_interval_seconds': 60,
            'buffer_max_hours': 24,
        },
    }
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    return path

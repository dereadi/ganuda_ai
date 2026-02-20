#!/usr/bin/env python3
"""
Discover cameras on network via common methods:
1. ONVIF discovery (professional cameras)
2. RTSP port scan (port 554)
3. Known vendor APIs (Ring, Nest, Wyze, Arlo)
"""

import socket
import subprocess
from typing import List, Dict

def scan_rtsp_ports(subnet: str = "192.168.132") -> List[Dict]:
    """Scan for devices with RTSP port 554 open."""
    cameras = []

    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        result = sock.connect_ex((ip, 554))
        if result == 0:
            cameras.append({
                'ip': ip,
                'port': 554,
                'protocol': 'rtsp',
                'url': f'rtsp://{ip}:554/stream1'
            })
        sock.close()

    return cameras

def scan_onvif(subnet: str = "192.168.132") -> List[Dict]:
    """Scan for ONVIF cameras on port 80/8080."""
    # ONVIF uses WS-Discovery multicast
    # For now, scan common ports
    cameras = []

    for i in range(1, 255):
        ip = f"{subnet}.{i}"
        for port in [80, 8080, 8000]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            result = sock.connect_ex((ip, port))
            if result == 0:
                # Try to detect if it's a camera by checking for ONVIF path
                cameras.append({
                    'ip': ip,
                    'port': port,
                    'protocol': 'onvif',
                    'url': f'http://{ip}:{port}/onvif/device_service'
                })
            sock.close()

    return cameras

if __name__ == '__main__':
    print("Scanning for RTSP cameras...")
    rtsp = scan_rtsp_ports()
    print(f"Found {len(rtsp)} RTSP endpoints")
    for cam in rtsp:
        print(f"  {cam['ip']}:{cam['port']}")
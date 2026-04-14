#!/usr/bin/env python3
"""Port Scanner — finds all listening ports and identifies risky services."""

import socket
import subprocess
import re
from typing import List, Dict

RISKY_PORTS = {
    21: ("FTP", "critical", "Unencrypted file transfer. Credentials sent in plain text."),
    23: ("Telnet", "critical", "Unencrypted remote shell. Replace with SSH immediately."),
    25: ("SMTP", "warning", "Mail server. Ensure authentication is required."),
    53: ("DNS", "info", "DNS resolver. Verify it's intentional."),
    80: ("HTTP", "warning", "Unencrypted web server. Use HTTPS (443) instead."),
    110: ("POP3", "warning", "Unencrypted mail retrieval. Use POP3S (995)."),
    135: ("RPC", "critical", "Windows RPC. Common attack vector."),
    139: ("NetBIOS", "critical", "Windows file sharing. Should not be exposed."),
    143: ("IMAP", "warning", "Unencrypted mail. Use IMAPS (993)."),
    445: ("SMB", "critical", "Windows file sharing. WannaCry attack vector."),
    1433: ("MSSQL", "critical", "Database exposed to network. Should be localhost only."),
    1521: ("Oracle", "critical", "Database exposed to network."),
    3306: ("MySQL", "critical", "Database exposed to network. Should be localhost only."),
    3389: ("RDP", "critical", "Remote desktop. Major attack surface."),
    5432: ("PostgreSQL", "warning", "Database. Verify access controls."),
    5900: ("VNC", "critical", "Remote desktop. Often unencrypted."),
    6379: ("Redis", "critical", "In-memory database. Often no authentication by default."),
    8080: ("HTTP-Alt", "info", "Alternative HTTP. Verify intentional."),
    27017: ("MongoDB", "critical", "Database. Frequently misconfigured with no auth."),
}


def scan_listening_ports() -> List[Dict]:
    """Find all listening TCP/UDP ports using ss."""
    findings = []
    try:
        result = subprocess.run(
            ["ss", "-tlnp"], capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.strip().split('\n')[1:]:  # skip header
            parts = line.split()
            if len(parts) < 5:
                continue

            local_addr = parts[3]
            # Parse address and port
            if ']:' in local_addr:  # IPv6
                addr, port = local_addr.rsplit(':', 1)
            elif local_addr.count(':') == 1:
                addr, port = local_addr.rsplit(':', 1)
            else:
                continue

            try:
                port = int(port)
            except ValueError:
                continue

            # Extract process info
            process_info = parts[-1] if 'users:' in parts[-1] else ''
            pid_match = re.search(r'pid=(\d+)', process_info)
            name_match = re.search(r'"([^"]+)"', process_info)
            pid = pid_match.group(1) if pid_match else "unknown"
            process_name = name_match.group(1) if name_match else "unknown"

            # Determine exposure
            exposed = addr in ('0.0.0.0', '*', '[::]', '::')

            # Check if risky
            severity = "info"
            service = ""
            risk_note = ""
            if port in RISKY_PORTS:
                service, severity, risk_note = RISKY_PORTS[port]
                if exposed and severity == "warning":
                    severity = "critical"  # exposed risky port escalates
            elif exposed:
                severity = "warning"

            findings.append({
                "port": port,
                "address": addr,
                "exposed": exposed,
                "process": process_name,
                "pid": pid,
                "service": service or f"port-{port}",
                "severity": severity,
                "risk": risk_note or ("Exposed to network" if exposed else "Local only"),
            })
    except FileNotFoundError:
        # macOS fallback
        try:
            result = subprocess.run(
                ["lsof", "-iTCP", "-sTCP:LISTEN", "-P", "-n"],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.strip().split('\n')[1:]:
                parts = line.split()
                if len(parts) < 9:
                    continue
                process_name = parts[0]
                pid = parts[1]
                addr_port = parts[8]
                if ':' in addr_port:
                    addr, port_str = addr_port.rsplit(':', 1)
                    try:
                        port = int(port_str)
                    except ValueError:
                        continue
                    exposed = addr in ('*', '0.0.0.0')
                    severity = "info"
                    service = ""
                    risk_note = ""
                    if port in RISKY_PORTS:
                        service, severity, risk_note = RISKY_PORTS[port]
                    findings.append({
                        "port": port, "address": addr, "exposed": exposed,
                        "process": process_name, "pid": pid,
                        "service": service or f"port-{port}",
                        "severity": severity,
                        "risk": risk_note or ("Exposed" if exposed else "Local only"),
                    })
        except Exception:
            pass
    except Exception as e:
        findings.append({"error": str(e), "severity": "warning"})

    return sorted(findings, key=lambda x: (
        {"critical": 0, "warning": 1, "info": 2}.get(x.get("severity", "info"), 3),
        x.get("port", 0)
    ))


if __name__ == '__main__':
    import json
    results = scan_listening_ports()
    print(f"Found {len(results)} listening ports")
    for r in results:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🟢"}.get(r.get("severity"), "⚪")
        exposed = "EXPOSED" if r.get("exposed") else "local"
        print(f"  {icon} :{r['port']:>5} | {r['service']:15} | {r['process']:20} | {exposed:8} | {r.get('risk','')[:50]}")

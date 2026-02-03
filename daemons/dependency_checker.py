#!/usr/bin/env python3
"""
Phase 7 Supply Chain: Dependency vulnerability checker daemon.

Reads config from /ganuda/config/dependency-check.yaml.
Runs pip-audit on each configured virtualenv.
Compares against previous scan to alert only on NEW vulnerabilities.
Stores results in /ganuda/security/dependency_audit/.
Designed to run as systemd timer (weekly).

Cherokee AI Federation
"""

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("ERROR: PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)


CONFIG_PATH = "/ganuda/config/dependency-check.yaml"
SECRETS_PATH = "/ganuda/secrets/secrets.env"


def load_config():
    """Load dependency check configuration."""
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)


def load_secrets():
    """Load Telegram credentials from secrets.env."""
    secrets = {}
    if os.path.exists(SECRETS_PATH):
        with open(SECRETS_PATH, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    secrets[key.strip()] = value.strip().strip("\"'")
    return secrets


def send_telegram_alert(message, secrets):
    """Send alert via Telegram bot."""
    token = secrets.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = secrets.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print("WARN: Telegram credentials not configured. Skipping alert.")
        return

    try:
        import urllib.request
        import urllib.parse

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        print("Telegram alert sent.")
    except Exception as e:
        print(f"WARN: Failed to send Telegram alert: {e}")


def run_pip_audit(venv_path):
    """Run pip-audit against a virtualenv and return results dict."""
    python_bin = os.path.join(venv_path, "bin", "python")
    pip_bin = os.path.join(venv_path, "bin", "pip")

    if not os.path.exists(python_bin):
        print(f"  SKIP: {venv_path} not found")
        return None

    # Ensure pip-audit is installed
    try:
        subprocess.run(
            [python_bin, "-m", "pip_audit", "--help"],
            capture_output=True, check=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  Installing pip-audit in {venv_path}...")
        subprocess.run(
            [pip_bin, "install", "pip-audit", "--quiet"],
            capture_output=True
        )

    # Run pip-audit
    result = subprocess.run(
        [python_bin, "-m", "pip_audit", "--format", "json"],
        capture_output=True, text=True
    )

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  WARN: Could not parse pip-audit output for {venv_path}")
        return None


def extract_vuln_ids(scan_data):
    """Extract set of vulnerability IDs from scan data."""
    vuln_ids = set()
    deps = scan_data if isinstance(scan_data, list) else scan_data.get("dependencies", [])
    for dep in deps:
        for vuln in dep.get("vulns", []):
            vuln_id = vuln.get("id", vuln.get("aliases", ["unknown"])[0] if vuln.get("aliases") else "unknown")
            vuln_ids.add(vuln_id)
    return vuln_ids


def load_previous_vulns(previous_dir, venv_name):
    """Load vulnerability IDs from previous scan."""
    if not os.path.exists(previous_dir):
        return set()

    previous_files = sorted(Path(previous_dir).glob(f"scan_{venv_name}_*.json"), reverse=True)
    if not previous_files:
        return set()

    try:
        with open(previous_files[0], "r") as f:
            data = json.load(f)
        return extract_vuln_ids(data)
    except (json.JSONDecodeError, IOError):
        return set()


def main():
    print("=== Dependency Vulnerability Checker ===")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
    print()

    config = load_config()
    secrets = load_secrets()

    results_dir = config.get("results_dir", "/ganuda/security/dependency_audit")
    previous_dir = config.get("previous_scan_dir", os.path.join(results_dir, "previous"))
    ignored_cves = set(config.get("ignore", []))
    severity_threshold = config.get("severity_threshold", "high")
    auto_alert = config.get("auto_alert", True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(previous_dir, exist_ok=True)

    all_new_vulns = []

    for venv_path in config.get("virtualenvs", []):
        venv_name = os.path.basename(os.path.dirname(venv_path))
        print(f"--- Scanning: {venv_path} ---")

        scan_data = run_pip_audit(venv_path)
        if scan_data is None:
            continue

        # Save current scan
        scan_file = os.path.join(results_dir, f"scan_{venv_name}_{timestamp}.json")
        with open(scan_file, "w") as f:
            json.dump(scan_data, f, indent=2)
        print(f"  Scan saved: {scan_file}")

        # Compare with previous
        current_vulns = extract_vuln_ids(scan_data)
        previous_vulns = load_previous_vulns(previous_dir, venv_name)
        new_vulns = current_vulns - previous_vulns - ignored_cves

        if new_vulns:
            print(f"  NEW vulnerabilities: {len(new_vulns)}")
            for v in sorted(new_vulns):
                print(f"    - {v}")
                all_new_vulns.append(f"{venv_name}: {v}")
        else:
            print("  No new vulnerabilities.")

        # Archive current as previous for next run
        archive_file = os.path.join(previous_dir, f"scan_{venv_name}_{timestamp}.json")
        shutil.copy2(scan_file, archive_file)

        print()

    # Alert on new vulnerabilities
    if all_new_vulns and auto_alert:
        alert_msg = (
            f"*Dependency Alert* ({len(all_new_vulns)} new)\n"
            f"Node: {os.uname().nodename}\n\n"
            + "\n".join(f"- {v}" for v in all_new_vulns[:20])
        )
        if len(all_new_vulns) > 20:
            alert_msg += f"\n... and {len(all_new_vulns) - 20} more"

        if config.get("alert_channel") == "telegram":
            send_telegram_alert(alert_msg, secrets)

    print("=== Dependency check complete ===")
    return 1 if all_new_vulns else 0


if __name__ == "__main__":
    sys.exit(main())

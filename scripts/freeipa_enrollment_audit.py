#!/usr/bin/env python3
"""
FreeIPA Enrollment Audit — Cherokee AI Federation

Checks all linux nodes for:
1. ipa-client installation and enrollment
2. HBAC rule coverage
3. Sudo rule deployment via FreeIPA
4. Kerberos ticket status

Run from redfin (has SSH access to all nodes).

Council Vote: (pending)
Kanban: #1812

For Seven Generations - Cherokee AI Federation
"""

import subprocess
import json
import sys
from datetime import datetime

NODES = {
    'redfin': '192.168.132.223',
    'bluefin': '192.168.132.222',
    'greenfin': '192.168.132.224',
}

# macOS nodes use different identity management
MAC_NODES = {
    'sasass': '192.168.132.241',
    'sasass2': '192.168.132.242',
    'bmasass': '192.168.132.21',
}

def run_local(cmd):
    """Run command locally, return (stdout, returncode)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', -1

def run_remote(node_ip, cmd):
    """Run command on remote node via SSH, return (stdout, returncode)."""
    ssh_cmd = f"ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no dereadi@{node_ip} '{cmd}'"
    return run_local(ssh_cmd)

def check_node(name, ip, is_local=False):
    """Audit a single node for FreeIPA enrollment."""
    runner = run_local if is_local else lambda cmd: run_remote(ip, cmd)
    result = {'node': name, 'ip': ip, 'timestamp': datetime.now().isoformat()}

    # 1. Check ipa-client installed
    out, rc = runner('ipa-client-install --version 2>/dev/null || echo NOT_INSTALLED')
    result['ipa_client_version'] = out if rc == 0 and 'NOT_INSTALLED' not in out else None
    result['ipa_client_installed'] = result['ipa_client_version'] is not None

    # 2. Check enrollment (presence of /etc/ipa/default.conf)
    out, rc = runner('cat /etc/ipa/default.conf 2>/dev/null | grep -i realm || echo NOT_ENROLLED')
    result['enrolled'] = 'NOT_ENROLLED' not in out
    if result['enrolled']:
        result['realm'] = out.split('=')[-1].strip() if '=' in out else 'unknown'

    # 3. Check SSSD running (means FreeIPA identity is active)
    out, rc = runner('systemctl is-active sssd 2>/dev/null || echo INACTIVE')
    result['sssd_active'] = out == 'active'

    # 4. Check Kerberos keytab exists
    out, rc = runner('test -f /etc/krb5.keytab && echo EXISTS || echo MISSING')
    result['keytab_exists'] = out == 'EXISTS'

    # 5. Check HBAC rules (if enrolled)
    if result['enrolled']:
        out, rc = runner('ipa hbacrule-find --sizelimit=100 2>/dev/null | grep -c "Rule name:" || echo 0')
        try:
            result['hbac_rule_count'] = int(out)
        except ValueError:
            result['hbac_rule_count'] = 0

    # 6. Check sudo rules via FreeIPA
    if result['enrolled']:
        out, rc = runner('ipa sudorule-find --sizelimit=100 2>/dev/null | grep -c "Rule name:" || echo 0')
        try:
            result['sudo_rule_count'] = int(out)
        except ValueError:
            result['sudo_rule_count'] = 0

    # 7. Check if node can resolve IPA server
    out, rc = runner('dig +short _kerberos._udp.cherokee.local SRV 2>/dev/null || echo NO_DNS')
    result['kerberos_dns'] = 'NO_DNS' not in out and len(out) > 0

    return result

def main():
    print(f"=== FreeIPA Enrollment Audit — {datetime.now().isoformat()} ===\n")

    results = []

    # Audit linux nodes
    for name, ip in NODES.items():
        print(f"Checking {name} ({ip})...")
        is_local = (name == 'redfin')
        result = check_node(name, ip, is_local=is_local)
        results.append(result)

        status = 'ENROLLED' if result.get('enrolled') else 'NOT ENROLLED'
        sssd = 'SSSD active' if result.get('sssd_active') else 'SSSD inactive'
        hbac = f"{result.get('hbac_rule_count', '?')} HBAC rules"
        sudo = f"{result.get('sudo_rule_count', '?')} sudo rules"
        print(f"  {status} | {sssd} | {hbac} | {sudo}")
        print()

    # Summary
    print("=== SUMMARY ===")
    enrolled = sum(1 for r in results if r.get('enrolled'))
    total = len(results)
    print(f"Enrolled: {enrolled}/{total} linux nodes")

    for r in results:
        icon = '✅' if r.get('enrolled') and r.get('sssd_active') else '❌'
        print(f"  {icon} {r['node']}: enrolled={r.get('enrolled')}, sssd={r.get('sssd_active')}, "
              f"hbac={r.get('hbac_rule_count', 'N/A')}, sudo={r.get('sudo_rule_count', 'N/A')}")

    # Save JSON report
    report_path = '/ganuda/reports/freeipa_audit.json'
    with open(report_path, 'w') as f:
        json.dump({'audit_date': datetime.now().isoformat(), 'nodes': results}, f, indent=2)
    print(f"\nJSON report saved to {report_path}")

if __name__ == '__main__':
    main()
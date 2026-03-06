# Self-Replication Containment Audit Script

**Kanban**: #1906
**Priority**: P1 — Security (sfp=95)
**Assigned**: Software Engineer Jr.

---

## Context

Pan et al (2412.12140) demonstrated Qwen2.5-72B self-replicates in 90% of trials. We run Qwen2.5-72B on redfin. This script audits our containment boundary — FreeIPA sudo scoping, nftables, systemd, SSH keys, model weight access — and reports gaps.

## Step 1: Create the containment audit script

Create `/ganuda/scripts/security/self_replication_audit.py`

```python
#!/usr/bin/env python3
"""
Self-Replication Containment Audit
Cherokee AI Federation — Hawk Security Mandate

Audits containment boundary against Qwen2.5-72B self-replication risk.
Reference: Pan et al (2412.12140), Zhang et al (2509.25302)

Council Vote: Per kanban #1906, sfp=95
"""

import subprocess
import os
import sys
import json
from datetime import datetime

sys.path.insert(0, '/ganuda/lib')


def run_check(name, cmd, expect_pass=True):
    """Run a containment check and return result dict."""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=15
        )
        output = result.stdout.strip()
        return {
            'check': name,
            'output': output[:500],
            'returncode': result.returncode,
            'pass': True  # Will be evaluated by caller
        }
    except Exception as e:
        return {
            'check': name,
            'output': str(e),
            'returncode': -1,
            'pass': False
        }


def audit_sudo_scoping():
    """Check that FreeIPA sudo rules are properly scoped."""
    results = []

    # Check what commands dereadi can run as root
    r = run_check(
        'sudo_scope',
        "sudo -l 2>&1 | grep -E 'NOPASSWD|ALL' | head -10"
    )
    # FAIL if unrestricted ALL without NOPASSWD constraint
    has_unrestricted = 'ALL : ALL' in (r['output'] or '')
    has_scoped = 'NOPASSWD:' in (r['output'] or '')
    r['pass'] = has_scoped  # Scoped NOPASSWD is expected
    r['warning'] = has_unrestricted  # Full ALL is a risk
    r['note'] = 'FreeIPA scoped sudo expected. (ALL : ALL) requires password — acceptable.'
    results.append(r)

    return results


def audit_nftables():
    """Check that nftables restricts outbound from executor."""
    results = []

    # Check if nftables is active
    r = run_check(
        'nftables_active',
        "sudo nft list ruleset 2>/dev/null | head -5 || echo 'nft not available'"
    )
    r['pass'] = 'table' in r['output']
    results.append(r)

    # Check for outbound restrictions
    r = run_check(
        'nftables_outbound',
        "sudo nft list ruleset 2>/dev/null | grep -i 'output\\|forward\\|drop\\|reject' | head -10"
    )
    r['pass'] = bool(r['output'].strip())
    r['note'] = 'Should have outbound restrictions preventing model from reaching external compute'
    results.append(r)

    return results


def audit_systemd():
    """Check if executor can create or enable new systemd services."""
    results = []

    # Check if /etc/systemd/system is writable by dereadi
    r = run_check(
        'systemd_write_access',
        "ls -la /etc/systemd/system/ | head -3 && test -w /etc/systemd/system/ && echo 'WRITABLE' || echo 'NOT_WRITABLE'"
    )
    r['pass'] = 'NOT_WRITABLE' in r['output']
    results.append(r)

    # Check executor ESCALATE_FILE_TYPES includes .service
    r = run_check(
        'executor_service_escalation',
        "grep -c '.service' /ganuda/jr_executor/task_executor.py"
    )
    r['pass'] = int(r['output'] or '0') > 0
    r['note'] = 'Executor should escalate .service files (require Chief approval)'
    results.append(r)

    return results


def audit_ssh_keys():
    """Check SSH key access constraints."""
    results = []

    # Check authorized_keys — should only have known keys
    r = run_check(
        'ssh_authorized_keys',
        "wc -l ~/.ssh/authorized_keys 2>/dev/null || echo '0 keys'"
    )
    r['pass'] = True  # Informational
    r['note'] = 'Review authorized_keys manually for unexpected entries'
    results.append(r)

    # Check if executor can write to .ssh
    r = run_check(
        'ssh_dir_protection',
        "ls -la ~/.ssh/ | head -3 && stat -c '%a' ~/.ssh/"
    )
    perms = r['output'].split('\n')[-1] if r['output'] else ''
    r['pass'] = perms in ('700', '755')
    r['note'] = f'SSH dir perms: {perms}. Should be 700.'
    results.append(r)

    return results


def audit_model_weights():
    """Check if executor can access or modify model weight files."""
    results = []

    # Check model directory permissions
    model_dirs = [
        '/ganuda/models/',
        '/home/dereadi/.cache/huggingface/',
    ]
    for mdir in model_dirs:
        r = run_check(
            f'model_dir_{os.path.basename(mdir.rstrip("/"))}',
            f"ls -la {mdir} 2>/dev/null | head -5 || echo 'NOT_FOUND'"
        )
        r['pass'] = True  # Informational — model dirs should exist but be read-only for executor
        r['note'] = 'Model weights should be readable but not writable by executor process'
        results.append(r)

    return results


def audit_executor_sandbox():
    """Check executor path restrictions and forbidden patterns."""
    results = []

    # Check forbidden paths in search_replace_editor
    r = run_check(
        'sr_editor_forbidden_paths',
        "grep -A10 'forbidden_paths' /ganuda/jr_executor/search_replace_editor.py | head -12"
    )
    r['pass'] = '/etc/' in r['output'] and '/usr/' in r['output']
    r['note'] = 'SearchReplaceEditor must block /etc/, /usr/, /bin/, /sbin/, /boot/'
    results.append(r)

    # Check symlink-aware validation exists
    r = run_check(
        'symlink_validation',
        "grep -c 'resolve()' /ganuda/jr_executor/search_replace_editor.py"
    )
    r['pass'] = int(r['output'] or '0') > 0
    r['note'] = 'Path validation must resolve symlinks to prevent escape'
    results.append(r)

    # Check forbidden patterns in task_executor
    r = run_check(
        'forbidden_command_patterns',
        "grep -A20 'FORBIDDEN_PATTERNS' /ganuda/jr_executor/task_executor.py | head -22"
    )
    patterns_found = r['output'].count("'") // 2  # rough count of pattern strings
    r['pass'] = patterns_found >= 10
    r['note'] = f'Found ~{patterns_found} forbidden patterns. Should cover rm, dd, mkfs, shutdown, etc.'
    results.append(r)

    # Check 50% loss guardrail
    r = run_check(
        'fifty_pct_loss_guardrail',
        "grep -c '50' /ganuda/jr_executor/task_executor.py"
    )
    r['pass'] = int(r['output'] or '0') > 0
    r['note'] = 'Executor must block writes that reduce file by >50%'
    results.append(r)

    return results


def audit_network_egress():
    """Check if executor process can reach external compute."""
    results = []

    # Check if outbound HTTP is restricted
    r = run_check(
        'outbound_http_test',
        "timeout 5 curl -s -o /dev/null -w '%{http_code}' https://api.openai.com/v1/models 2>&1 || echo 'BLOCKED'"
    )
    r['pass'] = 'BLOCKED' in r['output'] or r['returncode'] != 0
    r['note'] = 'Executor should NOT be able to reach external AI APIs'
    r['risk'] = 'HIGH' if r['output'] == '200' else 'LOW'
    results.append(r)

    return results


def main():
    print("=" * 70)
    print("SELF-REPLICATION CONTAINMENT AUDIT")
    print(f"Cherokee AI Federation — {datetime.now().isoformat()}")
    print(f"Node: {os.uname().nodename}")
    print(f"Threat model: Qwen2.5-72B self-replication (Pan et al 2412.12140)")
    print("=" * 70)

    all_results = []
    audits = [
        ('FreeIPA Sudo Scoping', audit_sudo_scoping),
        ('nftables Firewall', audit_nftables),
        ('systemd Service Creation', audit_systemd),
        ('SSH Key Access', audit_ssh_keys),
        ('Model Weight Protection', audit_model_weights),
        ('Executor Sandbox', audit_executor_sandbox),
        ('Network Egress', audit_network_egress),
    ]

    for section_name, audit_fn in audits:
        print(f"\n--- {section_name} ---")
        try:
            results = audit_fn()
            all_results.extend(results)
            for r in results:
                status = 'PASS' if r.get('pass') else 'FAIL'
                warning = ' [WARNING]' if r.get('warning') else ''
                risk = f" [RISK: {r.get('risk')}]" if r.get('risk') else ''
                print(f"  [{status}]{warning}{risk} {r['check']}")
                if r.get('note'):
                    print(f"         {r['note']}")
                if not r.get('pass') and r.get('output'):
                    print(f"         Output: {r['output'][:200]}")
        except Exception as e:
            print(f"  [ERROR] {section_name}: {e}")

    # Summary
    passed = sum(1 for r in all_results if r.get('pass'))
    failed = sum(1 for r in all_results if not r.get('pass'))
    warnings = sum(1 for r in all_results if r.get('warning'))

    print(f"\n{'=' * 70}")
    print(f"SUMMARY: {passed} passed, {failed} failed, {warnings} warnings")
    print(f"Total checks: {len(all_results)}")

    if failed > 0:
        print("\nFAILED CHECKS:")
        for r in all_results:
            if not r.get('pass'):
                print(f"  - {r['check']}: {r.get('note', r.get('output', ''))[:100]}")

    # Write JSON report
    report_path = f"/ganuda/reports/containment_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('/ganuda/reports', exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'node': os.uname().nodename,
            'checks': all_results,
            'summary': {'passed': passed, 'failed': failed, 'warnings': warnings}
        }, f, indent=2)
    print(f"\nReport written to: {report_path}")

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
```

## Verification

After creating:
1. `python3 /ganuda/scripts/security/self_replication_audit.py` runs without errors
2. Report shows PASS for: systemd write protection, executor .service escalation, symlink validation, forbidden patterns
3. JSON report written to /ganuda/reports/
4. Any FAIL items are flagged for TPM review

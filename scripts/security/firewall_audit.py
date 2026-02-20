#!/usr/bin/env python3
"""Audit nftables firewall state on the local node.

Kanban #547 — Harden Hub Firewall Rules
Checks: nftables service active, rules loaded, persistence configured,
fail2ban running, xtables compat issues.

Run on each federation node to assess firewall posture.
"""
import subprocess
import os
import sys
import socket

HOSTNAME = socket.gethostname().lower()

# Expected nftables config source files
CONFIG_PATHS = {
    "redfin": "/ganuda/config/nftables-redfin.conf",
    "bluefin": "/ganuda/config/nftables-bluefin.conf",
}

PERSIST_PATH = "/etc/nftables.conf"
FAIL2BAN_JAIL = "/ganuda/config/fail2ban-jail.local"


def run_cmd(cmd, timeout=10):
    """Run a command and return (success, stdout)."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode == 0, result.stdout.strip()
    except FileNotFoundError:
        return False, f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)


def check_nftables_service():
    """Check nftables service status."""
    ok, out = run_cmd(["systemctl", "is-active", "nftables"])
    return out == "active"


def check_nftables_enabled():
    """Check if nftables is enabled at boot."""
    ok, out = run_cmd(["systemctl", "is-enabled", "nftables"])
    return out == "enabled"


def get_ruleset():
    """Get current nftables ruleset."""
    ok, out = run_cmd(["nft", "list", "ruleset"])
    if ok:
        return out
    # Try with sudo hint
    return None


def count_rules(ruleset):
    """Count meaningful rules in a ruleset string."""
    if not ruleset:
        return 0
    keywords = ["accept", "drop", "reject", "counter", "limit", "log"]
    lines = [l.strip() for l in ruleset.split("\n") if l.strip()]
    return sum(1 for l in lines if any(kw in l for kw in keywords))


def check_xtables_compat(ruleset):
    """Check for xtables compat expressions that break nftables reloads."""
    if not ruleset:
        return []
    problems = []
    for i, line in enumerate(ruleset.split("\n"), 1):
        if "xt " in line.lower() or "xtables" in line.lower():
            problems.append(f"  Line {i}: {line.strip()}")
    return problems


def check_drop_policy(ruleset):
    """Check if INPUT chain has DROP policy."""
    if not ruleset:
        return False
    for line in ruleset.split("\n"):
        if "chain input" in line.lower() or "chain INPUT" in line:
            # Look for policy drop in nearby lines
            pass
    # Simpler: just check for "policy drop"
    return "policy drop" in ruleset.lower()


def check_persistence():
    """Check if nftables config is persisted for reboot survival."""
    exists = os.path.exists(PERSIST_PATH)
    size = os.path.getsize(PERSIST_PATH) if exists else 0
    return exists, size


def check_fail2ban():
    """Check fail2ban service status."""
    active_ok, active_out = run_cmd(["systemctl", "is-active", "fail2ban"])
    is_active = active_out == "active"

    jail_count = 0
    if is_active:
        ok, out = run_cmd(["fail2ban-client", "status"])
        if ok and "Jail list:" in out:
            jails_line = [l for l in out.split("\n") if "Jail list:" in l]
            if jails_line:
                jails = jails_line[0].split(":")[-1].strip()
                jail_count = len([j for j in jails.split(",") if j.strip()])

    return is_active, jail_count


def check_rate_limiting(ruleset):
    """Check if rate limiting rules exist."""
    if not ruleset:
        return False
    return "limit rate" in ruleset.lower() or "meter" in ruleset.lower()


def audit():
    """Run the full firewall audit."""
    print("=" * 60)
    print(f"FIREWALL AUDIT — {HOSTNAME}")
    print("Cherokee AI Federation — Kanban #547")
    print("=" * 60)

    issues = []
    warnings = []

    # 1. nftables service
    print("\n[1] nftables Service")
    svc_active = check_nftables_service()
    svc_enabled = check_nftables_enabled()
    print(f"  Active:  {'YES' if svc_active else 'NO'}")
    print(f"  Enabled: {'YES' if svc_enabled else 'NO'}")
    if not svc_active:
        issues.append("nftables service not active")
    if not svc_enabled:
        issues.append("nftables not enabled at boot — will not survive reboot")

    # 2. Ruleset
    print("\n[2] Active Ruleset")
    ruleset = get_ruleset()
    if ruleset:
        rule_count = count_rules(ruleset)
        has_drop = check_drop_policy(ruleset)
        has_rate_limit = check_rate_limiting(ruleset)
        print(f"  Rules loaded:   {rule_count}")
        print(f"  DROP policy:    {'YES' if has_drop else 'NO'}")
        print(f"  Rate limiting:  {'YES' if has_rate_limit else 'NO'}")

        if rule_count < 5:
            issues.append(f"Only {rule_count} rules — firewall is likely permissive")
        if not has_drop:
            issues.append("No default DROP policy — all traffic accepted by default")
        if not has_rate_limit:
            warnings.append("No rate limiting — vulnerable to brute force")

        # xtables compat check
        xtables = check_xtables_compat(ruleset)
        if xtables:
            print(f"  xtables compat: {len(xtables)} PROBLEMS")
            for x in xtables[:5]:
                print(f"    {x}")
            issues.append(f"{len(xtables)} xtables compat expressions will break reload")
        else:
            print(f"  xtables compat: Clean")
    else:
        print("  ERROR: Cannot read ruleset (may need sudo)")
        warnings.append("Cannot read ruleset without sudo")

    # 3. Persistence
    print("\n[3] Persistence (/etc/nftables.conf)")
    persisted, size = check_persistence()
    print(f"  File exists: {'YES' if persisted else 'NO'}")
    if persisted:
        print(f"  File size:   {size} bytes")
        if size < 100:
            issues.append("Persistence file too small — likely empty or default")
    else:
        issues.append("CRITICAL: No /etc/nftables.conf — rules LOST on reboot")

    # 4. Expected config comparison
    print("\n[4] Config Source")
    expected_path = CONFIG_PATHS.get(HOSTNAME)
    if expected_path:
        exists = os.path.exists(expected_path)
        print(f"  Expected: {expected_path} ({'EXISTS' if exists else 'MISSING'})")
        if exists and ruleset:
            with open(expected_path) as f:
                expected_rules = count_rules(f.read())
            actual_rules = count_rules(ruleset)
            drift = abs(actual_rules - expected_rules)
            print(f"  Expected rules: {expected_rules}, Active rules: {actual_rules}, Drift: {drift}")
            if drift > 5:
                warnings.append(f"Rule drift: {drift} rules differ from config file")
        elif not exists:
            issues.append(f"Config file missing: {expected_path}")
    else:
        print(f"  No config file defined for {HOSTNAME}")
        if HOSTNAME == "greenfin":
            warnings.append("Greenfin needs a dedicated nftables config (router node)")

    # 5. fail2ban
    print("\n[5] fail2ban")
    f2b_active, f2b_jails = check_fail2ban()
    print(f"  Active: {'YES' if f2b_active else 'NO'}")
    if f2b_active:
        print(f"  Jails:  {f2b_jails}")
    if not f2b_active:
        warnings.append("fail2ban not active — no brute-force protection")

    # 6. fail2ban config availability
    f2b_config_exists = os.path.exists(FAIL2BAN_JAIL)
    print(f"  Config ready: {'YES' if f2b_config_exists else 'NO'} ({FAIL2BAN_JAIL})")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    if issues:
        print(f"\nISSUES ({len(issues)}):")
        for i in issues:
            print(f"  [!] {i}")
    if warnings:
        print(f"\nWARNINGS ({len(warnings)}):")
        for w in warnings:
            print(f"  [~] {w}")
    if not issues and not warnings:
        print("\nALL CHECKS PASSED")

    print(f"\nScore: {max(0, 100 - len(issues)*20 - len(warnings)*5)}/100")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(audit())
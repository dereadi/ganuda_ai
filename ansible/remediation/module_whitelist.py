"""
Cherokee AI Federation — Ansible Module Whitelist

Turtle's 7GEN Constraint: LLM-generated playbooks may ONLY use modules
from this approved list. No raw, no script, no arbitrary execution.
Crawdad's Security Gate: Any module not on this list triggers rejection.
"""

# Approved Ansible modules for LLM-generated remediation playbooks
APPROVED_MODULES = {
    # Service management
    "ansible.builtin.systemd",
    "ansible.builtin.service",
    "ansible.builtin.systemd_service",
    # File operations
    "ansible.builtin.copy",
    "ansible.builtin.template",
    "ansible.builtin.file",
    "ansible.builtin.lineinfile",
    "ansible.builtin.stat",
    # Package management
    "ansible.builtin.apt",
    "ansible.builtin.pip",
    # Commands (limited)
    "ansible.builtin.command",
    "ansible.builtin.shell",
    # Networking
    "ansible.builtin.uri",
    "ansible.builtin.wait_for",
    # Info gathering
    "ansible.builtin.debug",
    "ansible.builtin.assert",
    "ansible.builtin.set_fact",
    "ansible.builtin.pause",
    # PostgreSQL (community)
    "community.postgresql.postgresql_query",
    # POSIX
    "ansible.posix.sysctl",
}

# Explicitly BANNED modules — LLM must never emit these
BANNED_MODULES = {
    "ansible.builtin.raw",       # Uncontrolled remote execution
    "ansible.builtin.script",    # Arbitrary script upload + execute
    "ansible.builtin.expect",    # Interactive session automation
    "community.general.proxmox", # Infrastructure destruction risk
    "ansible.builtin.reboot",    # Node-level disruption
}


def validate_playbook_modules(playbook_content: str) -> dict:
    """
    Scan a generated playbook for module usage.
    Returns dict with 'approved', 'unapproved', and 'banned' lists.
    """
    import yaml
    import re

    results = {"approved": [], "unapproved": [], "banned": [], "valid": True}

    try:
        plays = yaml.safe_load(playbook_content)
        if not isinstance(plays, list):
            plays = [plays]
    except yaml.YAMLError:
        results["valid"] = False
        return results

    for play in plays:
        if not isinstance(play, dict):
            continue
        tasks = play.get("tasks", [])
        for task in tasks:
            if not isinstance(task, dict):
                continue
            for key in task:
                # Skip Ansible meta-keys
                if key in ("name", "register", "when", "loop", "notify",
                           "ignore_errors", "changed_when", "failed_when",
                           "become", "become_user", "vars", "tags",
                           "block", "rescue", "always", "environment"):
                    continue
                # Check if it's a module reference
                module_name = key
                # Normalize short names to FQCN
                if "." not in module_name:
                    module_name = f"ansible.builtin.{module_name}"

                if module_name in BANNED_MODULES:
                    results["banned"].append(module_name)
                    results["valid"] = False
                elif module_name in APPROVED_MODULES:
                    results["approved"].append(module_name)
                else:
                    results["unapproved"].append(module_name)
                    results["valid"] = False

    return results
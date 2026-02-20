"""
Cherokee AI Federation — Crawdad Security Review Prompt

Builds the council vote question that Crawdad (and all 7 specialists)
evaluate when reviewing a generated remediation playbook.
"""


def build_crawdad_review_prompt(playbook_content: str) -> str:
    """Build a council vote question for security review of a generated playbook."""
    return f"""SECURITY REVIEW REQUEST: Auto-generated remediation playbook

The self-healing remediation engine has generated the following Ansible playbook
in response to a detected anomaly. This playbook has already passed:
- ansible-lint syntax validation
- Module whitelist check (all modules are approved)

Review this playbook for security concerns:

1. Does it access or modify sensitive files (credentials, keys, secrets)?
2. Could it cause data loss or service disruption beyond the target?
3. Are the shell/command tasks safe and scoped appropriately?
4. Does it follow least-privilege principles?
5. Could an attacker use this playbook template to escalate privileges?

PLAYBOOK CONTENT:
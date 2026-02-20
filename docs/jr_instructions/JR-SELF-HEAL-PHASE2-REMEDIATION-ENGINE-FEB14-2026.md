# Jr Instruction: Self-Healing Phase 2 — Remediation Engine + Templates

**Kanban**: #1781 (Phase 2 of 4)
**Story Points**: 5
**Council Vote**: #1872d8f580eaec28 (PROCEED WITH CAUTION, 0.874)
**Priority**: 15 (RC-2026-02B)
**Dependencies**: Phase 1 (Alert Bridge) must be complete
**Risk**: LOW — new files only, no modifications to existing code

## Objective

Build the core remediation engine that receives alerts from the EDA triage playbook,
classifies them, searches thermal memory for similar past remediations (RAG), selects
a Jinja2 playbook template, and calls Qwen 72B to fill template variables.

Turtle's 7GEN constraint: ALL generated playbooks MUST be human-readable and
maintainable without AI. The LLM fills TEMPLATES, it does NOT write free-form YAML.

## Step 1: Create Module Whitelist

Create `/ganuda/ansible/remediation/module_whitelist.py`

```python
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
```

## Step 2: Create Prompt Templates

Create `/ganuda/ansible/remediation/prompt_templates.py`

```python
"""
Cherokee AI Federation — LLM Prompt Templates for Remediation

These prompts constrain Qwen 72B to generate ONLY template variable
values, NOT free-form YAML. The playbook structure comes from our
Jinja2 templates — the LLM just fills in the blanks.
"""

CLASSIFY_ALERT_PROMPT = """You are Eagle Eye, the monitoring specialist for the Cherokee AI Federation.
Classify this alert into exactly ONE category.

Alert content: {alert_content}
Alert severity: {severity}

Categories:
- service_down: A systemd service has stopped or is failing
- config_drift: A configuration file has changed unexpectedly
- resource_exhaustion: Disk, memory, or CPU is critically high
- database_issue: PostgreSQL connection or query failure
- network_issue: Connectivity between federation nodes is broken
- unknown: Cannot determine the issue

Respond with ONLY a JSON object:
{{"category": "<category>", "target_node": "<hostname or 'unknown'>", "target_service": "<service name or 'unknown'>", "summary": "<one line description>"}}
"""

FILL_TEMPLATE_PROMPT = """You are a remediation engine for the Cherokee AI Federation.
Given the alert classification below, provide ONLY the template variables needed
to fill the remediation playbook template.

Classification:
- Category: {category}
- Target node: {target_node}
- Target service: {target_service}
- Summary: {summary}

Similar past remediations from thermal memory:
{rag_context}

The playbook template expects these variables:
{template_variables}

CONSTRAINTS (Turtle's 7GEN Rule):
- Every value must be a simple string, list, or boolean
- No embedded Jinja2 or YAML in values
- No shell commands longer than 80 characters
- Service names must match known federation services
- File paths must start with /ganuda/ or /etc/

Respond with ONLY a JSON object containing the template variable values.
"""

# Known federation services for validation
KNOWN_SERVICES = {
    "redfin": [
        "vllm.service", "llm-gateway.service", "sag.service",
        "jr-queue-worker.service", "jr-bidding.service",
        "vetassist-frontend.service", "vetassist-backend.service",
        "telegram-chief.service",
    ],
    "bluefin": [
        "vlm-bluefin.service", "vlm-adapter.service",
        "yolo-world.service", "optic-nerve.service",
        "tribal-vision.service", "speed-detector.service",
    ],
    "greenfin": [
        "cherokee-embedding.service", "cherokee-thermal-purge.service",
        "promtail.service",
    ],
}
```

## Step 3: Create Service Restart Playbook Template

Create `/ganuda/ansible/templates/remediation/restart_service.yml.j2`

```yaml
---
# Cherokee AI Federation — Auto-Generated Service Restart Playbook
# Generated by remediation engine for alert {{ alert_id }}
# Category: service_down
# Target: {{ target_node }} / {{ target_service }}
#
# HUMAN-READABLE (Turtle's 7GEN): This playbook restarts a crashed
# service after verifying the node is reachable and checking disk space.
- name: "Remediate service_down: {{ target_service }} on {{ target_node }}"
  hosts: "{{ target_node }}"
  become: yes
  gather_facts: yes

  tasks:
    - name: Check disk space is not critically low
      assert:
        that:
          - ansible_mounts | selectattr('mount', 'equalto', '/') | map(attribute='size_available') | first > 1073741824
        fail_msg: "Root filesystem has less than 1GB free — manual intervention required"
        success_msg: "Disk space OK"

    - name: Check if service unit file exists
      stat:
        path: "/etc/systemd/system/{{ target_service }}"
      register: unit_file

    - name: Fail if service unit not found
      assert:
        that: unit_file.stat.exists
        fail_msg: "Service unit {{ target_service }} not found on {{ target_node }}"

    - name: Restart the failed service
      systemd:
        name: "{{ target_service }}"
        state: restarted
        daemon_reload: yes

    - name: Wait for service to stabilize (10 seconds)
      pause:
        seconds: 10

    - name: Verify service is running
      systemd:
        name: "{{ target_service }}"
      register: service_status

    - name: Report service status
      debug:
        msg: >-
          {{ target_service }} on {{ target_node }}:
          {{ 'RUNNING' if service_status.status.ActiveState == 'active' else 'FAILED — escalate to TPM' }}

    - name: Fail if service did not recover
      assert:
        that: service_status.status.ActiveState == 'active'
        fail_msg: "Service {{ target_service }} failed to restart — requires TPM intervention"
```

## Step 4: Create Config Drift Playbook Template

Create `/ganuda/ansible/templates/remediation/config_drift.yml.j2`

```yaml
---
# Cherokee AI Federation — Auto-Generated Config Drift Remediation
# Generated by remediation engine for alert {{ alert_id }}
# Category: config_drift
# Target: {{ target_node }} / {{ config_path }}
#
# HUMAN-READABLE (Turtle's 7GEN): This playbook restores a drifted
# config file from the git-tracked version in /ganuda/config/.
- name: "Remediate config_drift: {{ config_path }} on {{ target_node }}"
  hosts: "{{ target_node }}"
  become: yes
  gather_facts: no

  tasks:
    - name: Backup current (drifted) config
      copy:
        src: "{{ config_path }}"
        dest: "{{ config_path }}.drift_backup_{{ ansible_date_time.iso8601_basic_short | default('unknown') }}"
        remote_src: yes
      ignore_errors: yes

    - name: Restore config from ganuda source
      copy:
        src: "{{ ganuda_source_path }}"
        dest: "{{ config_path }}"
        owner: "{{ config_owner | default('root') }}"
        group: "{{ config_group | default('root') }}"
        mode: "{{ config_mode | default('0644') }}"
      notify: "reload {{ affected_service | default('nothing') }}"

    - name: Verify restored config syntax
      command: "{{ validation_command }}"
      register: syntax_check
      changed_when: false
      when: validation_command is defined

    - name: Report restoration result
      debug:
        msg: "Config {{ config_path }} restored from {{ ganuda_source_path }} — syntax check: {{ syntax_check.stdout | default('skipped') }}"

  handlers:
    - name: "reload {{ affected_service | default('nothing') }}"
      systemd:
        name: "{{ affected_service }}"
        state: reloaded
      when: affected_service is defined
```

## Step 5: Create Resource Cleanup Playbook Template

Create `/ganuda/ansible/templates/remediation/resource_cleanup.yml.j2`

```yaml
---
# Cherokee AI Federation — Auto-Generated Resource Cleanup Playbook
# Generated by remediation engine for alert {{ alert_id }}
# Category: resource_exhaustion
# Target: {{ target_node }}
#
# HUMAN-READABLE (Turtle's 7GEN): This playbook cleans up common
# space consumers (logs, pycache, temp files) when disk usage is critical.
- name: "Remediate resource_exhaustion on {{ target_node }}"
  hosts: "{{ target_node }}"
  become: yes
  gather_facts: yes

  tasks:
    - name: Report current disk usage
      debug:
        msg: >-
          Root filesystem: {{ (ansible_mounts | selectattr('mount', 'equalto', '/') | first).size_available | human_readable }}
          available of {{ (ansible_mounts | selectattr('mount', 'equalto', '/') | first).size_total | human_readable }}

    - name: Clean systemd journal (older than 3 days)
      command: journalctl --vacuum-time=3d
      changed_when: true

    - name: Remove Python __pycache__ directories under /ganuda
      command: find /ganuda -type d -name __pycache__ -exec rm -rf {} +
      changed_when: true
      ignore_errors: yes

    - name: Clean apt cache
      apt:
        autoclean: yes
        autoremove: yes
      when: ansible_os_family == 'Debian'

    - name: Report disk usage after cleanup
      command: df -h /
      register: df_result
      changed_when: false

    - name: Show cleanup result
      debug:
        msg: "{{ df_result.stdout }}"
```

## Step 6: Create the Remediation Engine

Create `/ganuda/ansible/remediation/engine.py`

```python
#!/usr/bin/env python3
"""
Cherokee AI Federation — Self-Healing Remediation Engine

Receives alerts from EDA triage playbook, classifies them via Qwen 72B,
searches thermal memory for similar past remediations, selects a playbook
template, and generates a candidate remediation playbook.

Turtle's 7GEN: LLM fills TEMPLATES, never writes free-form YAML.
Crawdad's Gate: Generated playbooks go to validation pipeline before execution.

Usage:
    python engine.py --alert-id <id> --severity <level> --content <text>
"""

import argparse
import json
import os
import sys
import hashlib
from datetime import datetime
from pathlib import Path

import requests
import psycopg2
import yaml

# Import sibling modules
sys.path.insert(0, str(Path(__file__).parent))
from module_whitelist import validate_playbook_modules, KNOWN_SERVICES
from prompt_templates import CLASSIFY_ALERT_PROMPT, FILL_TEMPLATE_PROMPT

# Configuration
VLLM_URL = "http://192.168.132.223:8000/v1/chat/completions"
GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = os.environ.get("CHEROKEE_API_KEY", "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5")
DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"

TEMPLATE_DIR = Path("/ganuda/ansible/templates/remediation")
STAGING_DIR = Path("/ganuda/ansible/staging")
EMBEDDING_URL = "http://192.168.132.224:8003"

# Template mapping by alert category
CATEGORY_TEMPLATES = {
    "service_down": "restart_service.yml.j2",
    "config_drift": "config_drift.yml.j2",
    "resource_exhaustion": "resource_cleanup.yml.j2",
}


def get_db_password():
    """Load DB password from secrets_loader or environment."""
    try:
        sys.path.insert(0, "/ganuda/lib")
        from secrets_loader import get_secret
        return get_secret("DB_PASSWORD")
    except Exception:
        return os.environ.get("DB_PASSWORD", "")


def classify_alert(alert_content: str, severity: str) -> dict:
    """Use Qwen 72B to classify the alert into a remediation category."""
    prompt = CLASSIFY_ALERT_PROMPT.format(
        alert_content=alert_content,
        severity=severity,
    )

    try:
        resp = requests.post(
            VLLM_URL,
            json={
                "model": "Qwen/Qwen2.5-72B-Instruct-AWQ",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 256,
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Extract JSON from response
        # Handle markdown code blocks if present
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        return json.loads(content.strip())
    except Exception as e:
        print(f"Classification failed: {e}", file=sys.stderr)
        return {
            "category": "unknown",
            "target_node": "unknown",
            "target_service": "unknown",
            "summary": str(e),
        }


def search_similar_remediations(alert_content: str, limit: int = 3) -> str:
    """RAG search thermal memory for similar past remediations."""
    db_password = get_db_password()
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=db_password
        )
        cur = conn.cursor()

        # Try semantic search first (if embeddings available)
        try:
            # Get embedding for alert content
            embed_resp = requests.post(
                f"{EMBEDDING_URL}/embed",
                json={"text": alert_content[:500]},
                timeout=10,
            )
            if embed_resp.status_code == 200:
                embedding = embed_resp.json().get("embedding")
                if embedding:
                    cur.execute(
                        """SELECT original_content, temperature_score
                        FROM thermal_memory_archive
                        WHERE embedding IS NOT NULL
                        ORDER BY embedding <-> %s::vector
                        LIMIT %s""",
                        (str(embedding), limit),
                    )
                    rows = cur.fetchall()
                    if rows:
                        return "\n---\n".join(
                            f"[temp={r[1]:.2f}] {r[0][:300]}" for r in rows
                        )
        except Exception:
            pass  # Fall through to ILIKE search

        # Fallback: keyword search
        keywords = alert_content.split()[:5]
        pattern = "%".join(keywords)
        cur.execute(
            """SELECT original_content, temperature_score
            FROM thermal_memory_archive
            WHERE original_content ILIKE %s
            ORDER BY temperature_score DESC
            LIMIT %s""",
            (f"%{pattern}%", limit),
        )
        rows = cur.fetchall()
        conn.close()

        if rows:
            return "\n---\n".join(
                f"[temp={r[1]:.2f}] {r[0][:300]}" for r in rows
            )
        return "No similar remediations found in thermal memory."
    except Exception as e:
        return f"Thermal memory search failed: {e}"


def fill_template(classification: dict, rag_context: str) -> str:
    """Use Qwen 72B to fill template variables, then render the Jinja2 template."""
    category = classification.get("category", "unknown")
    template_name = CATEGORY_TEMPLATES.get(category)

    if not template_name:
        return f"No template available for category: {category}"

    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        return f"Template not found: {template_path}"

    template_content = template_path.read_text()

    # Extract variable names from template
    import re
    variables = set(re.findall(r'\{\{\s*(\w+)\s*\}\}', template_content))
    # Remove Ansible built-in variables
    variables -= {"ansible_date_time", "ansible_mounts", "ansible_os_family",
                  "inventory_hostname"}

    prompt = FILL_TEMPLATE_PROMPT.format(
        category=category,
        target_node=classification.get("target_node", "unknown"),
        target_service=classification.get("target_service", "unknown"),
        summary=classification.get("summary", ""),
        rag_context=rag_context[:1000],
        template_variables=", ".join(sorted(variables)),
    )

    try:
        resp = requests.post(
            VLLM_URL,
            json={
                "model": "Qwen/Qwen2.5-72B-Instruct-AWQ",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 512,
                "temperature": 0.1,
            },
            headers={"Authorization": f"Bearer {API_KEY}"},
            timeout=30,
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]

        # Extract JSON
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        variables_dict = json.loads(content.strip())

        # Validate target_service against known services
        target_node = variables_dict.get("target_node", classification.get("target_node"))
        target_service = variables_dict.get("target_service", classification.get("target_service"))
        if target_node in KNOWN_SERVICES:
            if target_service not in KNOWN_SERVICES[target_node]:
                print(f"WARNING: {target_service} not in known services for {target_node}", file=sys.stderr)

        # Render template with Jinja2
        from jinja2 import Template
        tmpl = Template(template_content)
        rendered = tmpl.render(**variables_dict, alert_id=classification.get("alert_id", "unknown"))

        return rendered
    except Exception as e:
        return f"Template fill failed: {e}"


def validate_and_stage(playbook_content: str, alert_id: str) -> str:
    """Validate generated playbook and write to staging directory."""
    # Module whitelist check
    validation = validate_playbook_modules(playbook_content)
    if not validation["valid"]:
        banned = validation.get("banned", [])
        unapproved = validation.get("unapproved", [])
        return f"REJECTED — banned modules: {banned}, unapproved: {unapproved}"

    # Write to staging
    STAGING_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    staging_file = STAGING_DIR / f"remediation_{alert_id}_{timestamp}.yml"
    staging_file.write_text(playbook_content)

    return f"STAGED at {staging_file} — awaiting validation pipeline + TPM approval"


def main():
    parser = argparse.ArgumentParser(description="Cherokee Self-Healing Remediation Engine")
    parser.add_argument("--alert-id", required=True, help="Thermal memory alert ID")
    parser.add_argument("--severity", required=True, help="Alert severity (critical/elevated)")
    parser.add_argument("--content", required=True, help="Alert content text")
    args = parser.parse_args()

    print(f"[{datetime.now().isoformat()}] Remediation engine processing alert {args.alert_id}")

    # Step 1: Classify
    print("Step 1: Classifying alert...")
    classification = classify_alert(args.content, args.severity)
    classification["alert_id"] = args.alert_id
    print(f"  Category: {classification.get('category')}")
    print(f"  Target: {classification.get('target_node')}/{classification.get('target_service')}")

    # Step 2: RAG search
    print("Step 2: Searching thermal memory for similar remediations...")
    rag_context = search_similar_remediations(args.content)
    print(f"  Found context: {len(rag_context)} chars")

    # Step 3: Fill template
    print("Step 3: Generating remediation playbook from template...")
    playbook = fill_template(classification, rag_context)

    if playbook.startswith("No template") or playbook.startswith("Template"):
        print(f"  {playbook}")
        sys.exit(1)

    # Step 4: Validate and stage
    print("Step 4: Validating and staging...")
    result = validate_and_stage(playbook, args.alert_id)
    print(f"  {result}")

    if "REJECTED" in result:
        sys.exit(1)

    print(f"\nRemediation playbook staged. Next: validation pipeline + TPM approval.")


if __name__ == "__main__":
    main()
```

## Manual Steps

On redfin:
```text
mkdir -p /ganuda/ansible/remediation
mkdir -p /ganuda/ansible/templates/remediation
mkdir -p /ganuda/ansible/staging
pip install jinja2  # likely already installed
```

# Jr Instruction: FreeIPA Audit Ansible Playbook

**Task ID:** FREEIPA-AUDIT
**Kanban:** #1812
**Priority:** 13
**Assigned:** Software Engineer Jr.

---

## Overview

Create an Ansible playbook that audits FreeIPA enrollment, HBAC rules, and sudo policies across all Linux nodes. Server: silverfin (CHEROKEE.LOCAL realm). Redfin confirmed enrolled. owlfin + eaglefin recently enrolled. Output per-host audit reports.

---

## Step 1: Create the FreeIPA audit playbook

Create `/ganuda/ansible/playbooks/freeipa-audit.yml`

```yaml
---
# Cherokee AI Federation — FreeIPA Audit
# Kanban #1812 | Enrollment, HBAC, Sudo verification
#
# Run: ansible-playbook playbooks/freeipa-audit.yml
# Output: /ganuda/reports/freeipa_audit/

- name: FreeIPA Audit
  hosts: all
  become: yes
  gather_facts: yes

  vars:
    audit_dir: "/ganuda/reports/freeipa_audit"
    ipa_realm: "CHEROKEE.LOCAL"

  tasks:
    - name: Ensure audit directory exists
      file:
        path: "{{ audit_dir }}"
        state: directory
        mode: "0755"
      delegate_to: localhost
      run_once: true

    # === IPA Client Enrollment ===

    - name: Check ipa-client-install status
      shell: ipa-client-install --unattended 2>&1 | head -1 || echo "ipa-client not installed"
      register: ipa_client_status
      changed_when: false
      ignore_errors: yes
      when: ansible_system == 'Linux'

    - name: Check SSSD status
      shell: systemctl is-active sssd 2>/dev/null || echo "not active"
      register: sssd_status
      changed_when: false
      when: ansible_system == 'Linux'

    - name: Check SSSD config
      shell: grep -E 'ipa_domain|ipa_server|krb5_realm' /etc/sssd/sssd.conf 2>/dev/null || echo "No SSSD config"
      register: sssd_config
      changed_when: false
      when: ansible_system == 'Linux'

    - name: Check Kerberos realm
      shell: grep default_realm /etc/krb5.conf 2>/dev/null || echo "No krb5.conf"
      register: krb5_realm
      changed_when: false
      when: ansible_system == 'Linux'

    - name: Check ipa command availability
      command: which ipa
      register: ipa_cmd
      changed_when: false
      ignore_errors: yes
      when: ansible_system == 'Linux'

    # === HBAC Rules ===

    - name: List HBAC rules (if ipa available)
      shell: |
        echo "REDACTED_USE_ENV_VAR" | kinit admin 2>/dev/null
        ipa hbacrule-find --all 2>/dev/null || echo "Cannot query HBAC rules (kinit may have failed)"
      register: hbac_rules
      changed_when: false
      when: ipa_cmd is defined and ipa_cmd.rc == 0

    - name: Test HBAC for current host
      shell: |
        ipa hbactest --user=admin --host={{ inventory_hostname }}.cherokee.local --service=sshd 2>/dev/null || echo "HBAC test failed"
      register: hbac_test
      changed_when: false
      when: ipa_cmd is defined and ipa_cmd.rc == 0

    # === Sudo Rules ===

    - name: List sudo rules (if ipa available)
      shell: ipa sudorule-find 2>/dev/null || echo "Cannot query sudo rules"
      register: sudo_rules
      changed_when: false
      when: ipa_cmd is defined and ipa_cmd.rc == 0

    - name: Check local sudoers (fallback)
      shell: |
        echo "=== /etc/sudoers.d/ ==="
        ls -la /etc/sudoers.d/ 2>/dev/null || echo "No sudoers.d"
        echo "=== sudoers entries ==="
        grep -v '^#' /etc/sudoers 2>/dev/null | grep -v '^$' | head -20
      register: local_sudoers
      changed_when: false
      when: ansible_system == 'Linux'

    # === DNS resolution ===

    - name: Check IPA server DNS
      shell: dig +short _kerberos._tcp.cherokee.local SRV 2>/dev/null || echo "DNS lookup failed"
      register: ipa_dns
      changed_when: false
      when: ansible_system == 'Linux'

    # === Certificate status ===

    - name: Check IPA certificate
      shell: |
        certutil -L -d /etc/ipa/nssdb 2>/dev/null || echo "No IPA NSS DB"
        ls -la /etc/ipa/ca.crt 2>/dev/null || echo "No IPA CA cert"
      register: ipa_certs
      changed_when: false
      ignore_errors: yes
      when: ansible_system == 'Linux'

    # === Write audit report ===

    - name: Write per-host audit report
      copy:
        dest: "{{ audit_dir }}/{{ inventory_hostname }}.txt"
        content: |
          # FreeIPA Audit: {{ inventory_hostname }}
          # Generated: {{ ansible_date_time.iso8601 }}
          # Realm: {{ ipa_realm }}

          ## IPA Client Status
          {{ ipa_client_status.stdout | default('Skipped (not Linux)') }}

          ## SSSD
          Status: {{ sssd_status.stdout | default('N/A') }}
          Config: {{ sssd_config.stdout | default('N/A') }}

          ## Kerberos
          {{ krb5_realm.stdout | default('N/A') }}

          ## HBAC Rules
          {{ hbac_rules.stdout | default('Not queried (ipa cmd not available)') }}

          ## HBAC Test (sshd)
          {{ hbac_test.stdout | default('Not tested') }}

          ## Sudo Rules (IPA)
          {{ sudo_rules.stdout | default('Not queried') }}

          ## Local Sudoers
          {{ local_sudoers.stdout | default('N/A') }}

          ## DNS
          {{ ipa_dns.stdout | default('N/A') }}

          ## IPA Certificates
          {{ ipa_certs.stdout | default('N/A') }}
      delegate_to: localhost
      when: ansible_system == 'Linux'

    - name: Report summary
      debug:
        msg: >-
          {{ inventory_hostname }} |
          SSSD: {{ sssd_status.stdout | default('N/A') }} |
          Realm: {{ krb5_realm.stdout | default('N/A') | trim }} |
          IPA cmd: {{ 'YES' if (ipa_cmd is defined and ipa_cmd.rc == 0) else 'NO' }}
```

---

## Verification

```text
cd /ganuda/ansible
ansible-playbook playbooks/freeipa-audit.yml -l redfin
```

Then review:
```text
cat /ganuda/reports/freeipa_audit/redfin.txt
```

---

## Notes

- Non-destructive read-only audit
- kinit admin attempt for HBAC/sudo queries — may fail if no admin credentials cached
- Falls back to local sudoers inspection if ipa command unavailable
- CHEROKEE.LOCAL realm, silverfin is IPA server
- macOS hosts skipped (no SSSD/IPA enrollment)
- Per-host .txt reports for TPM consolidation

# JR Instruction: SSH PQC Hardening Ansible Playbook

**Task**: PQC-SSH-001
**Priority**: P1
**Kanban**: #1874 (5 SP)
**use_rlm**: false
**assigned_jr**: Software Engineer Jr.
**Council Vote**: PROCEED WITH CAUTION (0.846 confidence, 1.0 agreement)
**Long Man Phase**: BUILD — Quantum/PQC Hardening Sprint

## Context

Council deliberation on Google's quantum error correction breakthrough (Willow chip, below-threshold QEC) identified that OpenSSH 9.6 on all federation nodes ALREADY supports `sntrup761x25519-sha512@openssh.com` — a hybrid post-quantum key exchange using Streamlined NTRU Prime. This means we can enable PQC SSH key exchange TODAY without upgrading OpenSSH.

Wolf (Technical): "Ed25519 signatures are quantum-safe, but Curve25519 ECDH key exchange is NOT. sntrup761 hybrid KEX protects the key exchange against quantum attacks."

This playbook hardens SSH configuration fleet-wide with PQC KEX and modern defaults. Crypto-agile group_vars per Turtle's recommendation.

## Changes

### Change 1: Create crypto-agile SSH group variables

Create `/ganuda/ansible/group_vars/linux.yml`

```yaml
<<<<<<< SEARCH
=======
# SSH Cryptographic Configuration — Cherokee AI Federation
# Council mandate: Quantum/PQC Hardening Sprint (Feb 21, 2026)
# Crypto-agile: change these variables to update fleet-wide SSH crypto
#
# sntrup761x25519 is a HYBRID post-quantum KEX:
#   - sntrup761 (Streamlined NTRU Prime, post-quantum)
#   - x25519 (classical ECDH)
#   An attacker must break BOTH to compromise the session.

ssh_kex_algorithms:
  - "sntrup761x25519-sha512@openssh.com"
  - "curve25519-sha256"
  - "curve25519-sha256@libssh.org"

ssh_ciphers:
  - "chacha20-poly1305@openssh.com"
  - "aes256-gcm@openssh.com"
  - "aes128-gcm@openssh.com"

ssh_macs:
  - "hmac-sha2-512-etm@openssh.com"
  - "hmac-sha2-256-etm@openssh.com"

ssh_host_key_algorithms:
  - "ssh-ed25519"

ssh_host_key_files:
  - "/etc/ssh/ssh_host_ed25519_key"

ssh_permit_root_login: "no"
ssh_password_authentication: "no"
ssh_pubkey_authentication: "yes"
ssh_x11_forwarding: "no"
ssh_max_auth_tries: 3
ssh_permit_empty_passwords: "no"
ssh_client_alive_interval: 300
ssh_client_alive_count_max: 3
>>>>>>> REPLACE
```

### Change 2: Create the SSH PQC hardening playbook

Create `/ganuda/ansible/playbooks/ssh-pqc-hardening.yml`

```yaml
<<<<<<< SEARCH
=======
---
# SSH PQC Hardening Playbook — Cherokee AI Federation
# Council mandate: Quantum/PQC Sprint, Wolf + Bear P1
#
# Enables sntrup761x25519 post-quantum hybrid KEX,
# disables RSA host keys, enforces Ed25519-only.
#
# Usage:
#   ansible-playbook -i /ganuda/ansible/inventory playbooks/ssh-pqc-hardening.yml
#   ansible-playbook -i /ganuda/ansible/inventory playbooks/ssh-pqc-hardening.yml --limit greenfin
#   ansible-playbook -i /ganuda/ansible/inventory playbooks/ssh-pqc-hardening.yml --check  # dry run
#
# IMPORTANT: Test on one node first (--limit owlfin) before fleet-wide deploy.

- name: SSH PQC Hardening
  hosts: linux
  become: yes
  vars_files:
    - ../group_vars/linux.yml

  tasks:
    - name: Verify sntrup761 KEX is available
      command: ssh -Q kex
      register: kex_list
      changed_when: false

    - name: Assert sntrup761 is supported
      assert:
        that: "'sntrup761x25519-sha512@openssh.com' in kex_list.stdout"
        fail_msg: "sntrup761 not available on {{ inventory_hostname }}. OpenSSH may be too old."

    - name: Backup current sshd_config
      copy:
        src: /etc/ssh/sshd_config
        dest: "/etc/ssh/sshd_config.bak.{{ ansible_date_time.iso8601_basic_short }}"
        remote_src: yes

    - name: Set KexAlgorithms
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?KexAlgorithms'
        line: "KexAlgorithms {{ ssh_kex_algorithms | join(',') }}"
        state: present
      notify: restart sshd

    - name: Set Ciphers
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?Ciphers'
        line: "Ciphers {{ ssh_ciphers | join(',') }}"
        state: present
      notify: restart sshd

    - name: Set MACs
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?MACs'
        line: "MACs {{ ssh_macs | join(',') }}"
        state: present
      notify: restart sshd

    - name: Set HostKey to Ed25519 only
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?HostKey\s+/etc/ssh/ssh_host_{{ item }}_key'
        line: "#HostKey /etc/ssh/ssh_host_{{ item }}_key"
        state: present
      loop:
        - rsa
        - ecdsa
      notify: restart sshd

    - name: Ensure Ed25519 HostKey is active
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?HostKey\s+/etc/ssh/ssh_host_ed25519_key'
        line: "HostKey /etc/ssh/ssh_host_ed25519_key"
        state: present
      notify: restart sshd

    - name: Set HostKeyAlgorithms
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?HostKeyAlgorithms'
        line: "HostKeyAlgorithms {{ ssh_host_key_algorithms | join(',') }}"
        state: present
      notify: restart sshd

    - name: Set PermitRootLogin
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?PermitRootLogin'
        line: "PermitRootLogin {{ ssh_permit_root_login }}"
      notify: restart sshd

    - name: Set PasswordAuthentication
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?PasswordAuthentication'
        line: "PasswordAuthentication {{ ssh_password_authentication }}"
      notify: restart sshd

    - name: Set PubkeyAuthentication
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?PubkeyAuthentication'
        line: "PubkeyAuthentication {{ ssh_pubkey_authentication }}"
      notify: restart sshd

    - name: Set X11Forwarding
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?X11Forwarding'
        line: "X11Forwarding {{ ssh_x11_forwarding }}"
      notify: restart sshd

    - name: Set MaxAuthTries
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?MaxAuthTries'
        line: "MaxAuthTries {{ ssh_max_auth_tries }}"
      notify: restart sshd

    - name: Set ClientAliveInterval
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?ClientAliveInterval'
        line: "ClientAliveInterval {{ ssh_client_alive_interval }}"
      notify: restart sshd

    - name: Set ClientAliveCountMax
      lineinfile:
        path: /etc/ssh/sshd_config
        regexp: '^#?ClientAliveCountMax'
        line: "ClientAliveCountMax {{ ssh_client_alive_count_max }}"
      notify: restart sshd

    - name: Validate sshd config
      command: sshd -t
      register: sshd_test
      changed_when: false

    - name: Show validation result
      debug:
        msg: "sshd config validation: {{ 'PASSED' if sshd_test.rc == 0 else 'FAILED' }}"

  handlers:
    - name: restart sshd
      systemd:
        name: sshd
        state: restarted
      when: sshd_test.rc == 0
>>>>>>> REPLACE
```

## Verification

```text
# Dry run on one node first
cd /ganuda/ansible
ansible-playbook -i inventory playbooks/ssh-pqc-hardening.yml --limit greenfin --check

# Apply to one node
ansible-playbook -i inventory playbooks/ssh-pqc-hardening.yml --limit greenfin

# Verify PQC KEX is negotiated
ssh -v greenfin 2>&1 | grep -i kex

# Expected: "kex: algorithm: sntrup761x25519-sha512@openssh.com"

# Then fleet-wide
ansible-playbook -i inventory playbooks/ssh-pqc-hardening.yml
```

## Notes

- MUST test on one non-critical node before fleet-wide. Ansible backs up sshd_config before changes.
- sshd_config validation (`sshd -t`) runs before restart — if validation fails, sshd is NOT restarted.
- sntrup761 is available in OpenSSH 9.6 (confirmed on redfin + greenfin). No upgrade needed.
- The playbook comments out RSA and ECDSA host keys but does not delete the key files.
- bmasass (macOS) is NOT in the linux group — requires separate macOS playbook if needed.
- DMZ nodes (owlfin/eaglefin) require SSSD/Kerberos fix before Ansible can reach them.

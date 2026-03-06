# Jr Instruction: VetAssist P0 — PII Vault + FreeIPA Integration

**Task ID:** VETASSIST-P0-PII
**Kanban:** #1825
**Priority:** 1
**Assigned:** Software Engineer Jr.

---

## Overview

Create field-level PII encryption module for VetAssist and FreeIPA access control playbook.

---

## Step 1: Create PII vault encryption module

Create `/ganuda/services/vetassist/pii_vault.py`

```python
"""PII Vault: Field-level encryption for VetAssist sensitive data.
Encrypts SSN, DOB, full name before database storage.
Key loaded from env var VETASSIST_PII_KEY."""

import os
import logging
from cryptography.fernet import Fernet

logger = logging.getLogger(__name__)

_KEY = os.environ.get("VETASSIST_PII_KEY", "")
_fernet = None

def _get_fernet():
    global _fernet
    if _fernet is None:
        if not _KEY:
            raise ValueError("VETASSIST_PII_KEY environment variable not set")
        _fernet = Fernet(_KEY.encode() if isinstance(_KEY, str) else _KEY)
    return _fernet

def encrypt_pii(plaintext):
    """Encrypt a PII field value. Returns base64 ciphertext string."""
    if not plaintext:
        return plaintext
    f = _get_fernet()
    ciphertext = f.encrypt(plaintext.encode("utf-8"))
    logger.info("PII field encrypted (audit)")
    return ciphertext.decode("utf-8")

def decrypt_pii(ciphertext):
    """Decrypt a PII field value. Returns plaintext string."""
    if not ciphertext:
        return ciphertext
    f = _get_fernet()
    plaintext = f.decrypt(ciphertext.encode("utf-8"))
    logger.info("PII field decrypted (audit)")
    return plaintext.decode("utf-8")

def generate_key():
    """Generate a new Fernet key. Run once, store in env."""
    return Fernet.generate_key().decode("utf-8")
```

---

## Step 2: Create FreeIPA access control playbook

Create `/ganuda/ansible/playbooks/vetassist-freeipa-access.yml`

```yaml
---
- name: VetAssist FreeIPA Access Control
  hosts: goldfin
  become: true
  tasks:
    - name: Ensure FreeIPA client is installed
      ansible.builtin.package:
        name: freeipa-client
        state: present

    - name: Check FreeIPA enrollment
      ansible.builtin.command: ipa-client-install --check
      register: ipa_check
      changed_when: false
      failed_when: false

    - name: Create vetassist-admins HBAC rule
      ansible.builtin.command: >
        ipa hbacrule-add vetassist_goldfin_access
        --desc="VetAssist admin access to goldfin"
      register: hbac_add
      changed_when: "'Added' in hbac_add.stdout"
      failed_when: false

    - name: Add vetassist-admins group to HBAC rule
      ansible.builtin.command: >
        ipa hbacrule-add-user vetassist_goldfin_access
        --groups=vetassist-admins
      failed_when: false
      changed_when: false

    - name: Add goldfin host to HBAC rule
      ansible.builtin.command: >
        ipa hbacrule-add-host vetassist_goldfin_access
        --hosts=goldfin.cherokee.local
      failed_when: false
      changed_when: false

    - name: Create sudo rule for vetassist service management
      ansible.builtin.command: >
        ipa sudorule-add vetassist_service_mgmt
        --desc="Allow vetassist-admins to restart vetassist services"
      failed_when: false
      changed_when: false
```

---

## Verification

```text
python3 -c "from pii_vault import generate_key, encrypt_pii, decrypt_pii; import os; os.environ['VETASSIST_PII_KEY']=generate_key(); enc=encrypt_pii('123-45-6789'); print(f'Encrypted: {enc[:20]}...'); print(f'Decrypted: {decrypt_pii(enc)}')"
```

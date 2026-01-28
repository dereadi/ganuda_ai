# JR Instruction: Implement Dependency Tracking System

**JR ID:** JR-DEPENDENCY-TRACKING-SYSTEM
**Priority:** P0 (Security/Operations)
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Assigned To:** All Infrastructure Jrs
**Effort:** Medium (ongoing maintenance)

---

## Security Context: CIA Triad

| Principle | Dependency Risk | Mitigation |
|-----------|-----------------|------------|
| **Confidentiality** | Vulnerable packages expose data | Track CVEs, pin versions |
| **Integrity** | ABI mismatches corrupt behavior | Version lock compile-time deps |
| **Availability** | Broken deps = service down | Test before upgrade, rollback plan |

**Incident Example:** 2026-01-27 vLLM outage - PyTorch nightly broke ABI compatibility, 517 restart attempts before fix.

---

## Objective

Create and maintain dependency manifests for all Cherokee AI Federation nodes to prevent untracked changes from breaking services.

---

## Phase 1: Create Dependency Manifest Structure

### 1.1 Directory Structure

```bash
/ganuda/config/dependencies/
├── redfin.yaml
├── bluefin.yaml
├── greenfin.yaml
├── goldfin.yaml
├── silverfin.yaml
├── sasass.yaml
├── sasass2.yaml
└── CHANGELOG.md
```

### 1.2 Manifest Schema

```yaml
# /ganuda/config/dependencies/<node>.yaml
---
node: <hostname>
updated: YYYY-MM-DD
updated_by: <who>
change_reason: <why>

system:
  os: <distro> <version>
  kernel: <version>

gpu_stack:  # If applicable
  cuda_driver: <version>
  cuda_toolkit: <version>
  torch: <version>
  vllm: <version>

services:
  <service_name>:
    version: <version>
    python: <version>
    venv: <path>
    requirements_hash: <sha256>
    dependencies:
      - name: <package>
        version: <version>
        pinned: true|false
        compile_time: true|false  # ABI-sensitive

databases:
  - name: <db_name>
    host: <host>
    version: <postgres version>
    extensions:
      - pgcrypto
      - etc

security:
  last_audit: YYYY-MM-DD
  cve_check: YYYY-MM-DD
  known_vulnerabilities: []
```

---

## Phase 2: Create Initial Manifests

### 2.1 Redfin (GPU Inference Node)

```yaml
# /ganuda/config/dependencies/redfin.yaml
---
node: redfin
updated: 2026-01-27
updated_by: TPM
change_reason: Post-vLLM incident - baseline established

system:
  os: Ubuntu 24.04.3 LTS
  kernel: 6.14.0-37-generic

gpu_stack:
  cuda_driver: "570.195.03"
  torch: "2.9.0"           # PINNED - do not upgrade without testing vLLM
  torchvision: "0.24.0"
  torchaudio: "2.9.0"
  vllm: "0.11.2"           # PINNED - ABI-sensitive
  xformers: "0.0.33.post1"
  triton: "3.5.0"

services:
  vllm:
    version: "0.11.2"
    python: "3.12"
    venv: /home/dereadi/cherokee_venv
    systemd_unit: vllm.service
    dependencies:
      - name: torch
        version: "2.9.0"
        pinned: true
        compile_time: true   # ABI-sensitive!
      - name: cuda-python
        version: "13.1.1"
        pinned: true
        compile_time: true

  llm_gateway:
    version: "1.5.0"
    python: "3.12"
    venv: /home/dereadi/cherokee_venv
    port: 8080

  vetassist_backend:
    version: "1.0.0"
    python: "3.12"
    venv: /ganuda/vetassist/backend/venv
    port: 8001

  vetassist_frontend:
    version: "1.0.0"
    runtime: node
    node_version: "20.x"
    port: 3000

databases:
  - name: zammad_production
    host: bluefin
    purpose: operational data
  - name: triad_federation
    host: bluefin
    purpose: auth/sessions
  - name: vetassist_pii
    host: goldfin
    purpose: PII vault (planned)

security:
  last_audit: 2026-01-27
  cve_check: 2026-01-27
  known_vulnerabilities: []

notes: |
  CRITICAL: torch and vllm are ABI-coupled.
  Never upgrade torch without rebuilding vllm.
  Use stable PyTorch releases only (no nightly/dev).
```

### 2.2 Generate Requirements Hash

```bash
# For each venv, generate hash of pinned requirements
cd /home/dereadi/cherokee_venv
pip freeze > requirements.lock
sha256sum requirements.lock
```

---

## Phase 3: Automation Scripts

### 3.1 Dependency Audit Script

```bash
#!/bin/bash
# /ganuda/scripts/audit_dependencies.sh
# Run weekly via cron

NODE=$(hostname)
MANIFEST="/ganuda/config/dependencies/${NODE}.yaml"
ALERT_EMAIL="admin@cherokee.local"

echo "=== Dependency Audit for ${NODE} ==="
echo "Date: $(date)"

# Check for security updates
echo "Checking for security updates..."
apt list --upgradable 2>/dev/null | grep -i security

# Check pip packages for known vulnerabilities
echo "Checking Python packages..."
source /home/dereadi/cherokee_venv/bin/activate
pip-audit 2>/dev/null || echo "pip-audit not installed"

# Compare current versions to manifest
echo "Comparing to manifest..."
# TODO: Parse YAML and compare

echo "=== Audit Complete ==="
```

### 3.2 Pre-Upgrade Checklist Script

```bash
#!/bin/bash
# /ganuda/scripts/pre_upgrade_check.sh
# Run BEFORE any pip install/upgrade

echo "=== PRE-UPGRADE CHECKLIST ==="
echo "1. Is this change documented in a JR instruction? [y/n]"
echo "2. Has this been tested in isolation? [y/n]"
echo "3. Is there a rollback plan? [y/n]"
echo "4. Are ABI-sensitive packages affected? (torch, cuda, vllm)"
echo ""
echo "Current ABI-sensitive versions:"
pip show torch vllm xformers 2>/dev/null | grep -E "^(Name|Version)"
echo ""
echo "Proceed with caution. Update manifest after successful change."
```

---

## Phase 4: Change Control Process

### Before ANY Dependency Change:

1. **Check manifest** for ABI-sensitive packages
2. **Create JR instruction** documenting the change
3. **Test in isolation** (separate venv or container)
4. **Backup current state**: `pip freeze > requirements.backup`
5. **Make change**
6. **Verify services**: `systemctl status <service>`
7. **Update manifest** with new versions
8. **Commit to git**: `git commit -m "deps: update <package> to <version>"`

### ABI-Sensitive Packages (NEVER auto-upgrade):

| Package | Depends On | Risk |
|---------|------------|------|
| torch | CUDA toolkit | Breaks all GPU code |
| vllm | torch ABI | Undefined symbols |
| xformers | torch ABI | Undefined symbols |
| triton | CUDA | Kernel compilation fails |
| flash-attention | torch + CUDA | Silent failures |

---

## Phase 5: CMDB Integration

Store dependency snapshots in thermal_memory_archive:

```sql
INSERT INTO thermal_memory_archive (
    memory_hash,
    original_content,
    metadata
) VALUES (
    md5('dependency_snapshot_redfin_20260127'),
    '<full manifest YAML>',
    '{"type": "cmdb_dependency", "node": "redfin", "date": "2026-01-27"}'
);
```

---

## Success Criteria

- [ ] Manifest files created for all 7 nodes
- [ ] Requirements.lock generated for each Python venv
- [ ] audit_dependencies.sh script deployed
- [ ] Cron job for weekly audits
- [ ] CHANGELOG.md tracking all dependency changes
- [ ] Team trained on change control process

---

## Schedule

| Task | Frequency | Owner |
|------|-----------|-------|
| Manifest updates | On every change | Whoever makes change |
| Security audit | Weekly | Infrastructure Jr |
| CVE check | Weekly (automated) | Cron job |
| Full review | Quarterly | TPM |

---

## References

- KB-DEPENDENCY-MANAGEMENT-POLICY-JAN27-2026.md
- JR-VLLM-PYTORCH-STABLE-JAN27-2026.md (incident that prompted this)
- OWASP Dependency Check guidelines

---

FOR SEVEN GENERATIONS

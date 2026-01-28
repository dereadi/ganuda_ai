# KB Article: Dependency Management Policy

**KB ID:** KB-DEPENDENCY-MANAGEMENT-POLICY
**Created:** 2026-01-27
**Author:** TPM via Claude Code
**Category:** Operations / Configuration Management

---

## Problem Statement

PyTorch nightly build broke vLLM due to ABI mismatch. We need to track all dependencies for production stability.

---

## Policy: Dependency Tracking Requirements

### 1. Version Pinning

All production services MUST have pinned dependencies:

```bash
# Example: /ganuda/services/llm_gateway/requirements.txt
torch==2.5.1
vllm==0.11.2
transformers==4.47.0
# etc.
```

### 2. Dependency Manifest per Node

Each node maintains a manifest in `/ganuda/config/dependencies/`:

| Node | Manifest File |
|------|---------------|
| redfin | `/ganuda/config/dependencies/redfin.yaml` |
| bluefin | `/ganuda/config/dependencies/bluefin.yaml` |
| greenfin | `/ganuda/config/dependencies/greenfin.yaml` |
| goldfin | `/ganuda/config/dependencies/goldfin.yaml` |

### 3. Manifest Format

```yaml
# /ganuda/config/dependencies/redfin.yaml
node: redfin
updated: 2026-01-27
updated_by: TPM

system:
  os: Ubuntu 24.04.3 LTS
  kernel: 6.14.0-37-generic
  cuda_driver: 570.195.03

gpu_stack:
  torch: 2.5.1
  torchvision: 0.20.1
  torchaudio: 2.5.1
  cuda_toolkit: 12.4
  vllm: 0.11.2
  xformers: 0.0.28

services:
  llm_gateway:
    version: 1.5.0
    python: 3.12
    venv: /home/dereadi/cherokee_venv
    requirements: /ganuda/services/llm_gateway/requirements.txt

  vetassist_backend:
    version: 1.0.0
    python: 3.12
    venv: /ganuda/vetassist/backend/venv
    requirements: /ganuda/vetassist/backend/requirements.txt

databases:
  - host: bluefin
    name: zammad_production
    purpose: operational data
  - host: bluefin
    name: triad_federation
    purpose: auth/users
  - host: goldfin
    name: vetassist_pii
    purpose: PII vault
```

### 4. Update Process

Before ANY dependency upgrade:

1. **Check CMDB manifest** for current versions
2. **Test in isolation** (separate venv or container)
3. **Update manifest** with new versions
4. **Commit to git** with change description
5. **Update Ansible playbook** if applicable

### 5. Quarterly Review Cycle

- **Q1, Q2, Q3, Q4:** Review and update dependencies
- **Exception:** Security patches applied immediately
- **No nightly/dev builds** in production

---

## Sync Points

| Component | Depends On | Must Match |
|-----------|------------|------------|
| vLLM | PyTorch | ABI compatible |
| xformers | PyTorch + CUDA | Exact version |
| flash-attention | PyTorch + CUDA | Compiled version |
| transformers | tokenizers | Major version |

---

## CMDB Integration

Dependencies tracked in thermal_memory_archive with:
- `memory_type: 'cmdb_dependency'`
- `metadata: {node, component, version, updated_at}`

---

## References

- JR-VLLM-PYTORCH-STABLE-JAN27-2026.md (incident that prompted this)
- Ansible playbooks in `/ganuda/ansible/`

---

FOR SEVEN GENERATIONS

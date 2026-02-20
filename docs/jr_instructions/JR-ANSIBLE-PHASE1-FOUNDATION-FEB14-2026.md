# Jr Instruction: Ansible Phase 1 — Foundation Framework

**Kanban**: #1755 (Phase 1 of 3)
**Story Points**: 8
**Council Vote**: #1bcd4a66217c3a21 (PROCEED, 0.89, unanimous)
**Priority**: 13 (RC-2026-02B, TOP PRIORITY)
**Dependencies**: None
**Risk**: LOW — new files only, no existing code modified

## Objective

Establish the Ansible framework for the Cherokee AI Federation's 5-node infrastructure.
Creates ansible.cfg, requirements.yml, group_vars, and host_vars for all nodes.

## Step 1: Create ansible.cfg

Create `/ganuda/ansible/ansible.cfg`

```ini
[defaults]
inventory = ./inventory
roles_path = ./roles
collections_paths = ./collections
host_key_checking = False
retry_files_enabled = False
gathering = smart
fact_caching = jsonfile
fact_caching_connection = /tmp/ansible_facts_cache
fact_caching_timeout = 86400
stdout_callback = yaml
interpreter_python = auto_silent
forks = 5

[privilege_escalation]
become = True
become_method = sudo
become_user = root
become_ask_pass = False

[ssh_connection]
pipelining = True
ssh_args = -o ControlMaster=auto -o ControlPersist=60s

[colors]
changed = yellow
ok = green
error = red
```

## Step 2: Create Galaxy requirements

Create `/ganuda/ansible/requirements.yml`

```yaml
---
# Cherokee AI Federation — Ansible Galaxy Dependencies
# Install: ansible-galaxy install -r requirements.yml
collections:
  - name: ansible.posix
    version: ">=1.5.0"
  - name: community.general
    version: ">=8.0.0"

roles: []
```

## Step 3: Create Linux group vars

Create `/ganuda/ansible/group_vars/linux.yml`

```yaml
---
# Cherokee AI Federation — Linux Node Group Variables
ganuda_base_path: /ganuda
ganuda_config_path: /ganuda/config
ganuda_scripts_path: /ganuda/scripts
ganuda_services_path: /ganuda/scripts/systemd
ganuda_venv_path: /ganuda/amem_venv

# Package management
package_manager: apt
common_packages:
  - python3
  - python3-pip
  - python3-venv
  - git
  - curl
  - jq
  - htop
  - nftables
  - fail2ban
  - postgresql-client
  - rsync
  - tmux

# Service management
service_manager: systemd

# Security
ssh_allowed_network: 192.168.132.0/24
fail2ban_enabled: true

# Database
db_host: 192.168.132.222
db_name: zammad_production
db_user: claude

# Embedding service
embedding_host: 192.168.132.224
embedding_port: 8003
```

## Step 4: Create macOS group vars

Create `/ganuda/ansible/group_vars/macos.yml`

```yaml
---
# Cherokee AI Federation — macOS Node Group Variables
ganuda_base_path: /Users/Shared/ganuda
ganuda_config_path: /Users/Shared/ganuda/config
ganuda_scripts_path: /Users/Shared/ganuda/scripts

# Package management
package_manager: homebrew
common_packages:
  - python3
  - git
  - curl
  - jq
  - htop
  - postgresql@16
  - rsync

# Service management
service_manager: launchd
launchd_plist_path: /Library/LaunchDaemons

# Munki
munki_client_enabled: true
munki_repo_url: "http://192.168.132.242:8080"
```

## Step 5: Create GPU nodes group vars

Create `/ganuda/ansible/group_vars/gpu_nodes.yml`

```yaml
---
# Cherokee AI Federation — GPU Node Group Variables
# ABI-sensitive: Pin exact versions from dependency manifests

nvidia_driver_version: "570"
cuda_version: "12.8"

# Python GPU stack (pinned for ABI compatibility)
gpu_python_packages:
  - torch==2.9.1+cu128
  - vllm>=0.8.0
  - xformers
  - triton
  - flash-attn

# GPU monitoring
gpu_power_monitor_enabled: true
gpu_power_monitor_interval_idle: 300
gpu_power_monitor_interval_active: 15
gpu_utilization_threshold: 40
```

## Step 6: Create redfin host vars

Create `/ganuda/ansible/host_vars/redfin.yml`

```yaml
---
# Cherokee AI Federation — Redfin (GPU Inference Node)
# IP: 192.168.132.223 | RTX PRO 6000 96GB

hostname: redfin
node_role: gpu_inference

# vLLM Configuration
vllm_model: /ganuda/models/qwen2.5-72b-instruct-awq
vllm_port: 8000
vllm_gpu_memory_utilization: 0.95
vllm_quantization: awq_marlin

# LLM Gateway
gateway_port: 8080
gateway_version: "1.6.0"

# SAG Unified Interface
sag_port: 4000

# VetAssist
vetassist_backend_port: 8001
vetassist_frontend_port: 3000

# Services managed on this node
managed_services:
  - vllm
  - llm-gateway
  - sag
  - vetassist-backend
  - jr-executor
  - jr-bidding
  - jr-orchestrator
  - jr-queue-worker
  - jr-se
  - jr-research
  - jr-infra
  - jr-it-triad
  - ganudabot
  - research-worker
  - ritual-review

# Firewall
nftables_config: nftables-redfin.conf
firewall_open_ports:
  public:
    - { port: 80, proto: tcp }
    - { port: 443, proto: tcp }
  internal:
    - { port: 8080, proto: tcp, comment: "LLM Gateway" }
    - { port: 8000, proto: tcp, comment: "vLLM" }
    - { port: 4000, proto: tcp, comment: "SAG" }
    - { port: 3000, proto: tcp, comment: "Kanban" }
    - { port: 8001, proto: tcp, comment: "VetAssist Backend" }
```

## Step 7: Create bluefin host vars

Create `/ganuda/ansible/host_vars/bluefin.yml`

```yaml
---
# Cherokee AI Federation — Bluefin (Database + Vision Node)
# IP: 192.168.132.222 | RTX 5070

hostname: bluefin
node_role: database

# PostgreSQL
postgresql_version: 17
postgresql_port: 5432
postgresql_ssl_enabled: true

# Vision services
vlm_port: 8090
vlm_model: "Qwen/Qwen2-VL-7B-Instruct-AWQ"
vlm_adapter_port: 8092
yolo_world_port: 8091

# Services managed on this node
managed_services:
  - vlm-bluefin
  - vlm-adapter
  - yolo-world
  - optic-nerve
  - tribal-vision
  - speed-detector
  - gpu-power-monitor

# Firewall
nftables_config: nftables-bluefin.conf
firewall_open_ports:
  internal:
    - { port: 5432, proto: tcp, comment: "PostgreSQL" }
    - { port: 3000, proto: tcp, comment: "Grafana" }
    - { port: 8090, proto: tcp, comment: "VLM vLLM" }
    - { port: 8091, proto: tcp, comment: "YOLO World" }
    - { port: 8092, proto: tcp, comment: "VLM Adapter" }
```

## Step 8: Create greenfin host vars

Create `/ganuda/ansible/host_vars/greenfin.yml`

```yaml
---
# Cherokee AI Federation — Greenfin (Edge LB / Monitoring)
# IP: 192.168.132.224

hostname: greenfin
node_role: edge_monitoring

# Monitoring stack
openobserve_port: 5080
openobserve_grpc_port: 5081
promtail_port: 9080

# Embedding service
embedding_service_port: 8003
embedding_model: "BAAI/bge-large-en-v1.5"
embedding_dimensions: 1024

# Camera tunnel (garage cam NAT)
camera_tunnel_enabled: true
camera_nat_rules:
  - { external_port: 18080, internal_ip: "10.0.0.123", internal_port: 80, comment: "Garage cam HTTP" }
  - { external_port: 10554, internal_ip: "10.0.0.123", internal_port: 554, comment: "Garage cam RTSP" }

# Services managed on this node
managed_services:
  - cherokee-embedding
  - cherokee-thermal-purge
  - promtail
  - openobserve

# Firewall
nftables_config: nftables-greenfin.conf
firewall_open_ports:
  internal:
    - { port: 5080, proto: tcp, comment: "OpenObserve UI" }
    - { port: 5081, proto: tcp, comment: "OpenObserve gRPC" }
    - { port: 9080, proto: tcp, comment: "Promtail" }
    - { port: 8003, proto: tcp, comment: "Embedding Server" }
    - { port: 18080, proto: tcp, comment: "Camera HTTP tunnel" }
    - { port: 10554, proto: tcp, comment: "Camera RTSP tunnel" }
```

## Step 9: Create sasass host vars

Create `/ganuda/ansible/host_vars/sasass.yml`

```yaml
---
# Cherokee AI Federation — sasass (M4 Max 128GB, bmasass)
# IP: 192.168.132.241 (also known as bmasass)

hostname: sasass
node_role: mobile_edge
ansible_become_method: sudo

# MLX Services
mlx_deepseek_port: 8800
mlx_deepseek_model: "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit"
mlx_qwen_port: 8801
mlx_qwen_model: "mlx-community/Qwen2.5-1.5B-Instruct-4bit"

# launchd services
managed_launchd_services:
  - com.cherokee.mlx-deepseek-r1

# Munki
munki_client_enabled: true
```

## Step 10: Create sasass2 host vars

Create `/ganuda/ansible/host_vars/sasass2.yml`

```yaml
---
# Cherokee AI Federation — sasass2 (Mac Studio, Munki Server)
# IP: 192.168.132.242

hostname: sasass2
node_role: package_server
ansible_become_method: sudo

# Munki server
munki_server_enabled: true
munki_repo_path: /Users/Shared/munki_repo
munki_server_port: 8080

# Services
managed_launchd_services: []
```

## Manual Steps

None — all new files. Run `ansible-galaxy install -r requirements.yml` after Jr execution.

# Jr Build Instructions: Ganuda Single Configuration File
## Priority: CRITICAL - Blocks v1.0 Release

---

## Objective

Create a single `ganuda.yaml` configuration file that controls all Ganuda Gateway settings. Users should only need to edit ONE file to configure the entire system.

---

## Current State

Configuration is scattered across:
- `/ganuda/services/llm_gateway/gateway.py` (hardcoded)
- Environment variables
- Database settings
- Multiple Python config dicts
- systemd service files

**Problem**: No single source of truth. Users cannot easily configure the system.

---

## Target State

```
/etc/ganuda/ganuda.yaml     <- Single config file
     │
     ├── Gateway settings
     ├── Inference settings
     ├── Database connection
     ├── Authentication
     ├── Logging
     └── Module enable/disable flags
```

---

## Implementation Tasks

### Task 1: Create Config Schema

Location: `/ganuda/lib/config_schema.py`

```python
"""
Ganuda Configuration Schema
Defines all configurable options with defaults
"""

from dataclasses import dataclass, field
from typing import Optional, List
import yaml

@dataclass
class GatewayConfig:
    host: str = "0.0.0.0"
    port: int = 8080
    workers: int = 4
    api_key_required: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    request_timeout_sec: int = 300

@dataclass
class InferenceConfig:
    backend: str = "vllm"  # vllm, ollama, openai
    base_url: str = "http://localhost:8000"
    model: str = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
    max_concurrent: int = 4
    max_tokens_default: int = 2048
    temperature_default: float = 0.7

@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "ganuda"
    user: str = "ganuda"
    password: str = ""  # Required, no default
    pool_size: int = 10

@dataclass
class LoggingConfig:
    level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR
    format: str = "json"  # json, text
    file: Optional[str] = "/var/log/ganuda/gateway.log"
    audit_enabled: bool = True
    audit_retention_days: int = 90

@dataclass
class ModulesConfig:
    """Intelligence modules - all disabled by default"""
    council_enabled: bool = False
    council_specialists: int = 7
    memory_enabled: bool = False
    memory_thermal_decay: bool = True
    breadcrumbs_enabled: bool = False
    fse_enabled: bool = False
    triad_enabled: bool = False
    multi_tenant_enabled: bool = False

@dataclass
class GanudaConfig:
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    modules: ModulesConfig = field(default_factory=ModulesConfig)

    @classmethod
    def from_yaml(cls, path: str) -> 'GanudaConfig':
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> 'GanudaConfig':
        # Recursive dataclass instantiation
        ...

    def to_yaml(self, path: str):
        with open(path, 'w') as f:
            yaml.dump(self._to_dict(), f, default_flow_style=False)
```

### Task 2: Create Default Config File

Location: `/ganuda/config/ganuda.yaml.default`

```yaml
# Ganuda Gateway Configuration
# Copy to /etc/ganuda/ganuda.yaml and customize

# ============================================================
# GATEWAY SETTINGS
# ============================================================
gateway:
  host: 0.0.0.0
  port: 8080
  workers: 4
  api_key_required: true
  cors_origins:
    - "*"
  request_timeout_sec: 300

# ============================================================
# INFERENCE BACKEND
# ============================================================
inference:
  backend: vllm          # vllm, ollama, or openai
  base_url: http://localhost:8000
  model: nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
  max_concurrent: 4
  max_tokens_default: 2048
  temperature_default: 0.7

# ============================================================
# DATABASE CONNECTION
# ============================================================
database:
  host: localhost
  port: 5432
  database: ganuda
  user: ganuda
  password: CHANGE_ME    # REQUIRED: Set your password
  pool_size: 10

# ============================================================
# LOGGING
# ============================================================
logging:
  level: INFO            # DEBUG, INFO, WARNING, ERROR
  format: json           # json or text
  file: /var/log/ganuda/gateway.log
  audit_enabled: true
  audit_retention_days: 90

# ============================================================
# INTELLIGENCE MODULES (Advanced - disabled by default)
# ============================================================
# These modules provide advanced AI capabilities but add complexity.
# Enable only if you need them and understand their implications.

modules:
  # 7-Specialist Council for multi-perspective decisions
  council_enabled: false
  council_specialists: 7

  # Thermal Memory for persistent context
  memory_enabled: false
  memory_thermal_decay: true

  # Breadcrumb trails for decision tracking
  breadcrumbs_enabled: false

  # Fractal Stigmergic Encryption for key evolution
  fse_enabled: false

  # Query Triad (Two Wolves) for privacy/security
  triad_enabled: false

  # Multi-tenant namespace isolation
  multi_tenant_enabled: false
```

### Task 3: Update Gateway to Load Config

Modify: `/ganuda/services/llm_gateway/gateway.py`

```python
import os
from ganuda.lib.config_schema import GanudaConfig

# Load configuration
CONFIG_PATH = os.environ.get('GANUDA_CONFIG', '/etc/ganuda/ganuda.yaml')

try:
    config = GanudaConfig.from_yaml(CONFIG_PATH)
    logger.info(f"Loaded configuration from {CONFIG_PATH}")
except FileNotFoundError:
    logger.warning(f"No config at {CONFIG_PATH}, using defaults")
    config = GanudaConfig()

# Use config throughout
app = Flask(__name__)
app.config['HOST'] = config.gateway.host
app.config['PORT'] = config.gateway.port
# ... etc
```

### Task 4: Add Config Validation Endpoint

Add to gateway.py:

```python
@app.route('/v1/config/validate', methods=['POST'])
def validate_config():
    """Validate a configuration file without applying it"""
    try:
        yaml_content = request.get_data(as_text=True)
        data = yaml.safe_load(yaml_content)
        config = GanudaConfig._from_dict(data)
        return jsonify({
            'valid': True,
            'modules_enabled': [
                k for k, v in vars(config.modules).items()
                if k.endswith('_enabled') and v
            ]
        })
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': str(e)
        }), 400

@app.route('/v1/config/current')
def current_config():
    """Show current running configuration (passwords redacted)"""
    safe_config = config._to_dict()
    safe_config['database']['password'] = '***REDACTED***'
    return jsonify(safe_config)
```

### Task 5: Create Config CLI Tool

Location: `/ganuda/bin/ganuda-config`

```bash
#!/bin/bash
# Ganuda Configuration Helper

case "$1" in
  init)
    cp /ganuda/config/ganuda.yaml.default /etc/ganuda/ganuda.yaml
    echo "Created /etc/ganuda/ganuda.yaml - edit and set your database password"
    ;;
  validate)
    curl -s -X POST http://localhost:8080/v1/config/validate \
      -d @/etc/ganuda/ganuda.yaml
    ;;
  show)
    curl -s http://localhost:8080/v1/config/current | jq '.'
    ;;
  *)
    echo "Usage: ganuda-config {init|validate|show}"
    ;;
esac
```

---

## File Locations

| File | Purpose |
|------|---------|
| `/ganuda/lib/config_schema.py` | Python config dataclasses |
| `/ganuda/config/ganuda.yaml.default` | Default config template |
| `/etc/ganuda/ganuda.yaml` | Active configuration (deployed) |
| `/ganuda/bin/ganuda-config` | CLI helper tool |

---

## Testing

1. Copy default config:
   ```bash
   sudo mkdir -p /etc/ganuda
   sudo cp /ganuda/config/ganuda.yaml.default /etc/ganuda/ganuda.yaml
   ```

2. Edit password:
   ```bash
   sudo nano /etc/ganuda/ganuda.yaml
   # Set database.password
   ```

3. Restart gateway:
   ```bash
   sudo systemctl restart llm-gateway
   ```

4. Verify config loaded:
   ```bash
   curl http://localhost:8080/v1/config/current | jq '.gateway'
   ```

---

## Success Criteria

- [ ] Single YAML file controls all settings
- [ ] Gateway loads config on startup
- [ ] Missing config uses sensible defaults
- [ ] `/v1/config/current` shows running config
- [ ] `/v1/config/validate` validates without applying
- [ ] All modules disabled by default
- [ ] Documentation updated

---

## Dependencies

- PyYAML library
- Python dataclasses (stdlib)

---

*For Seven Generations*

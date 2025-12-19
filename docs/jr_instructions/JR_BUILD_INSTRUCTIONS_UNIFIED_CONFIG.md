# Jr Build Instructions: Unified Configuration (ganuda.yaml)
## Priority: CRITICAL - Foundation for Everything

---

## Objective

Consolidate all configuration across the Cherokee AI Federation into a single `/ganuda/config/ganuda.yaml` file. Every service (Gateway, SAG, daemons) should read from this one source of truth.

**Current State**: Gateway uses `ganuda.yaml`, but SAG and other services have hardcoded `DB_CONFIG` dictionaries scattered across 7+ files.

**Target State**: One config file to rule them all.

---

## Architecture

```
/ganuda/config/ganuda.yaml  ◄──── SINGLE SOURCE OF TRUTH
         │
         ├──► LLM Gateway (port 8080) ✅ Already uses it
         │
         ├──► SAG UI (port 4000) ❌ Needs migration
         │
         ├──► Public Site (ganuda.us) ❌ Needs migration
         │
         ├──► Daemons (pheromone decay, etc.) ❌ Needs migration
         │
         └──► Future services...
```

---

## Current Config Locations (Problems)

| File | Hardcoded Config | Should Use |
|------|-----------------|------------|
| `/ganuda/services/llm_gateway/gateway.py` | ✅ Uses ganuda.yaml | Already correct |
| `/home/dereadi/sag_unified_interface/action_integrations.py` | ❌ `DB_CONFIG = {...}` | `ganuda.yaml` |
| `/home/dereadi/sag_unified_interface/event_manager.py` | ❌ `DB_CONFIG = {...}` | `ganuda.yaml` |
| `/home/dereadi/sag_unified_interface/email_intelligence.py` | ❌ `DB_CONFIG = {...}` | `ganuda.yaml` |
| `/home/dereadi/sag_unified_interface/kanban_integration.py` | ❌ `DB_CONFIG = {...}` | `ganuda.yaml` |
| `/home/dereadi/sag_unified_interface/create_database.py` | ❌ `DB_CONFIG = {...}` | `ganuda.yaml` |
| `/home/dereadi/sag_unified_interface/messaging.py` | ❌ Hardcoded Redis | `ganuda.yaml` |

---

## Expanded ganuda.yaml Schema

Update `/ganuda/config/ganuda.yaml` to include all services:

```yaml
# ============================================================
# GANUDA FEDERATION CONFIGURATION
# Single source of truth for ALL Cherokee AI services
# Version: 2.0
# ============================================================

# ------------------------------------------------------------
# INFRASTRUCTURE
# ------------------------------------------------------------

# Node topology
nodes:
  redfin:
    ip: 192.168.132.223
    role: gpu-inference
    services: [gateway, sag, vllm]
  bluefin:
    ip: 192.168.132.222
    role: database
    services: [postgresql, grafana]
  greenfin:
    ip: 192.168.132.224
    role: daemons
    services: [promtail, monitoring]
  sasass:
    ip: 192.168.132.241
    role: edge
    services: []
  sasass2:
    ip: 192.168.132.242
    role: edge
    services: []

# ------------------------------------------------------------
# LLM GATEWAY (port 8080)
# ------------------------------------------------------------

gateway:
  host: 0.0.0.0
  port: 8080
  workers: 4
  api_key_required: true
  cors_origins:
    - "*"
  request_timeout_sec: 300

inference:
  backend: vllm
  base_url: http://localhost:8000
  model: nvidia/Llama-3.1-Nemotron-70B-Instruct-HF
  max_concurrent: 4
  max_tokens_default: 2048
  temperature_default: 0.7

# ------------------------------------------------------------
# SAG UNIFIED INTERFACE (port 4000)
# ------------------------------------------------------------

sag:
  host: 0.0.0.0
  port: 4000
  debug: false
  secret_key: ${SAG_SECRET_KEY}  # Set via environment
  session_lifetime_hours: 24

  # Features
  features:
    calendar_enabled: true
    messages_enabled: true
    email_enabled: true
    kanban_enabled: true
    iot_enabled: true

  # External integrations
  kanban_url: http://localhost:3001
  grafana_url: http://192.168.132.222:3000
  cherokee_monitor_url: http://localhost:5555

# ------------------------------------------------------------
# PUBLIC SITE (ganuda.us)
# ------------------------------------------------------------

public_site:
  host: 0.0.0.0
  port: 80
  ssl_port: 443
  domain: ganuda.us
  ssl_cert: /etc/letsencrypt/live/ganuda.us/fullchain.pem
  ssl_key: /etc/letsencrypt/live/ganuda.us/privkey.pem

  # What stats to expose publicly
  expose_stats:
    - uptime
    - throughput
    - model_name
    - node_count

  # Never expose these
  hide_stats:
    - ip_addresses
    - api_keys
    - user_data

# ------------------------------------------------------------
# DATABASE
# ------------------------------------------------------------

database:
  host: 192.168.132.222
  port: 5432
  database: zammad_production
  user: claude
  password: ${DB_PASSWORD}  # Set via environment or use default
  pool_size: 10

  # Connection aliases for different purposes
  # All point to same DB but could be split later
  aliases:
    thermal_memory: zammad_production
    audit_log: zammad_production
    sag_data: zammad_production

# ------------------------------------------------------------
# REDIS
# ------------------------------------------------------------

redis:
  host: 192.168.132.223
  port: 6379
  password: ""  # No password currently
  db: 0

  # Key prefixes for namespacing
  prefixes:
    messages: "sag:messages"
    calendar: "sag:calendar"
    config: "sag:config"
    sessions: "sag:sessions"

# ------------------------------------------------------------
# LOGGING
# ------------------------------------------------------------

logging:
  level: INFO
  format: text  # text or json

  # Per-service log files
  files:
    gateway: /ganuda/logs/gateway.log
    sag: /ganuda/logs/sag.log
    public: /ganuda/logs/public.log
    daemons: /ganuda/logs/daemons.log

  # Audit logging
  audit:
    enabled: true
    retention_days: 90
    log_requests: true
    log_responses: false  # Don't log response bodies

# ------------------------------------------------------------
# INTELLIGENCE MODULES
# All disabled by default (Gateway v1 = boring)
# ------------------------------------------------------------

modules:
  # 7-Specialist Council
  council:
    enabled: true  # Currently enabled for our use
    specialists: 7
    timeout_sec: 60

  # Thermal Memory
  memory:
    enabled: true
    thermal_decay: true
    decay_rate: 0.01  # 1% per day

  # Breadcrumb trails
  breadcrumbs:
    enabled: true
    retention_days: 365

  # Fractal Stigmergic Encryption
  fse:
    enabled: false
    decay_coefficient: 0.01
    reinforcement_coefficient: 0.1

  # Query Triad (Two Wolves)
  triad:
    enabled: true
    log_full_reasoning: true

  # Multi-tenant isolation
  multi_tenant:
    enabled: false
    default_namespace: "default"

# ------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------

security:
  # API key settings
  api_keys:
    min_length: 32
    rotation_days: 90
    require_prefix: "ck-"

  # Session settings
  sessions:
    secure_cookies: true  # Set false for HTTP development
    httponly: true
    samesite: "Lax"

  # Network restrictions
  allowed_networks:
    - 192.168.132.0/24
    - 10.0.0.0/8
    - 127.0.0.1/32

# ------------------------------------------------------------
# AUTHENTICATION
# ------------------------------------------------------------

auth:
  # SAG authentication
  sag:
    enabled: true
    method: session  # session, api_key, or both
    session_timeout_hours: 24

  # Gateway authentication
  gateway:
    enabled: true
    method: api_key

  # Public site (no auth)
  public:
    enabled: false

# ------------------------------------------------------------
# IOT DEVICES
# ------------------------------------------------------------

iot:
  scan_interval_minutes: 5
  alert_on_new_device: true

  # Known device types
  device_types:
    - router
    - switch
    - camera
    - sensor
    - thermostat
    - light

# ------------------------------------------------------------
# EXTERNAL INTEGRATIONS
# ------------------------------------------------------------

integrations:
  # iCloud Calendar
  icloud:
    enabled: false
    apple_id: ${ICLOUD_APPLE_ID}
    app_password: ${ICLOUD_APP_PASSWORD}

  # Telegram
  telegram:
    enabled: true
    bot_token: ${TELEGRAM_BOT_TOKEN}

  # Slack
  slack:
    enabled: false
    bot_token: ${SLACK_BOT_TOKEN}
    signing_secret: ${SLACK_SIGNING_SECRET}

# ------------------------------------------------------------
# MAINTENANCE
# ------------------------------------------------------------

maintenance:
  # Pheromone decay schedule
  pheromone_decay:
    enabled: true
    cron: "33 3 * * *"  # 3:33 AM daily

  # Session cleanup
  session_cleanup:
    enabled: true
    cron: "0 * * * *"  # Hourly

  # Backup schedule
  backup:
    enabled: true
    cron: "0 2 * * *"  # 2 AM daily
    retention_days: 30
```

---

## Updated Config Schema

Update `/ganuda/lib/config_schema.py`:

```python
#!/usr/bin/env python3
"""
Ganuda Configuration Schema v2.0
Single source of truth for ALL Cherokee AI services
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import yaml
import os
import re

# ============================================================
# CONFIG DATACLASSES
# ============================================================

@dataclass
class NodeConfig:
    ip: str = ""
    role: str = ""
    services: List[str] = field(default_factory=list)

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
    backend: str = "vllm"
    base_url: str = "http://localhost:8000"
    model: str = "nvidia/Llama-3.1-Nemotron-70B-Instruct-HF"
    max_concurrent: int = 4
    max_tokens_default: int = 2048
    temperature_default: float = 0.7

@dataclass
class SAGFeaturesConfig:
    calendar_enabled: bool = True
    messages_enabled: bool = True
    email_enabled: bool = True
    kanban_enabled: bool = True
    iot_enabled: bool = True

@dataclass
class SAGConfig:
    host: str = "0.0.0.0"
    port: int = 4000
    debug: bool = False
    secret_key: str = ""
    session_lifetime_hours: int = 24
    features: SAGFeaturesConfig = field(default_factory=SAGFeaturesConfig)
    kanban_url: str = "http://localhost:3001"
    grafana_url: str = "http://192.168.132.222:3000"
    cherokee_monitor_url: str = "http://localhost:5555"

@dataclass
class PublicSiteConfig:
    host: str = "0.0.0.0"
    port: int = 80
    ssl_port: int = 443
    domain: str = "ganuda.us"
    ssl_cert: str = ""
    ssl_key: str = ""
    expose_stats: List[str] = field(default_factory=lambda: ["uptime", "throughput"])
    hide_stats: List[str] = field(default_factory=lambda: ["ip_addresses", "api_keys"])

@dataclass
class DatabaseConfig:
    host: str = "192.168.132.222"
    port: int = 5432
    database: str = "zammad_production"
    user: str = "claude"
    password: str = ""
    pool_size: int = 10
    aliases: Dict[str, str] = field(default_factory=dict)

@dataclass
class RedisConfig:
    host: str = "192.168.132.223"
    port: int = 6379
    password: str = ""
    db: int = 0
    prefixes: Dict[str, str] = field(default_factory=dict)

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "text"
    files: Dict[str, str] = field(default_factory=dict)
    audit: Dict[str, Any] = field(default_factory=dict)

@dataclass
class CouncilConfig:
    enabled: bool = False
    specialists: int = 7
    timeout_sec: int = 60

@dataclass
class MemoryConfig:
    enabled: bool = False
    thermal_decay: bool = True
    decay_rate: float = 0.01

@dataclass
class BreadcrumbsConfig:
    enabled: bool = False
    retention_days: int = 365

@dataclass
class FSEConfig:
    enabled: bool = False
    decay_coefficient: float = 0.01
    reinforcement_coefficient: float = 0.1

@dataclass
class TriadConfig:
    enabled: bool = False
    log_full_reasoning: bool = True

@dataclass
class MultiTenantConfig:
    enabled: bool = False
    default_namespace: str = "default"

@dataclass
class ModulesConfig:
    council: CouncilConfig = field(default_factory=CouncilConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    breadcrumbs: BreadcrumbsConfig = field(default_factory=BreadcrumbsConfig)
    fse: FSEConfig = field(default_factory=FSEConfig)
    triad: TriadConfig = field(default_factory=TriadConfig)
    multi_tenant: MultiTenantConfig = field(default_factory=MultiTenantConfig)

    # Legacy flat access for backward compatibility
    @property
    def council_enabled(self) -> bool:
        return self.council.enabled

    @property
    def council_specialists(self) -> int:
        return self.council.specialists

    @property
    def memory_enabled(self) -> bool:
        return self.memory.enabled

    @property
    def memory_thermal_decay(self) -> bool:
        return self.memory.thermal_decay

    @property
    def breadcrumbs_enabled(self) -> bool:
        return self.breadcrumbs.enabled

    @property
    def fse_enabled(self) -> bool:
        return self.fse.enabled

    @property
    def triad_enabled(self) -> bool:
        return self.triad.enabled

    @property
    def multi_tenant_enabled(self) -> bool:
        return self.multi_tenant.enabled

@dataclass
class SecurityConfig:
    api_keys: Dict[str, Any] = field(default_factory=dict)
    sessions: Dict[str, Any] = field(default_factory=dict)
    allowed_networks: List[str] = field(default_factory=list)

@dataclass
class AuthConfig:
    sag: Dict[str, Any] = field(default_factory=dict)
    gateway: Dict[str, Any] = field(default_factory=dict)
    public: Dict[str, Any] = field(default_factory=dict)

@dataclass
class IntegrationsConfig:
    icloud: Dict[str, Any] = field(default_factory=dict)
    telegram: Dict[str, Any] = field(default_factory=dict)
    slack: Dict[str, Any] = field(default_factory=dict)

@dataclass
class MaintenanceConfig:
    pheromone_decay: Dict[str, Any] = field(default_factory=dict)
    session_cleanup: Dict[str, Any] = field(default_factory=dict)
    backup: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GanudaConfig:
    """Master configuration for all Cherokee AI services"""
    nodes: Dict[str, NodeConfig] = field(default_factory=dict)
    gateway: GatewayConfig = field(default_factory=GatewayConfig)
    inference: InferenceConfig = field(default_factory=InferenceConfig)
    sag: SAGConfig = field(default_factory=SAGConfig)
    public_site: PublicSiteConfig = field(default_factory=PublicSiteConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    modules: ModulesConfig = field(default_factory=ModulesConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    maintenance: MaintenanceConfig = field(default_factory=MaintenanceConfig)

# ============================================================
# CONFIG LOADING
# ============================================================

def expand_env_vars(value: Any) -> Any:
    """Expand ${VAR} and ${VAR:-default} patterns in strings"""
    if isinstance(value, str):
        # Match ${VAR} or ${VAR:-default}
        pattern = r'\$\{([^}:]+)(?::-([^}]*))?\}'

        def replacer(match):
            var_name = match.group(1)
            default = match.group(2)
            return os.environ.get(var_name, default if default else '')

        return re.sub(pattern, replacer, value)
    elif isinstance(value, dict):
        return {k: expand_env_vars(v) for k, v in value.items()}
    elif isinstance(value, list):
        return [expand_env_vars(v) for v in value]
    return value


def load_config(path: str = '/ganuda/config/ganuda.yaml') -> GanudaConfig:
    """
    Load configuration from YAML file.
    Environment variables in ${VAR} or ${VAR:-default} format are expanded.
    """
    # Check if file exists
    if not os.path.exists(path):
        print(f"Warning: Config file not found at {path}, using defaults")
        return GanudaConfig()

    with open(path) as f:
        raw_data = yaml.safe_load(f) or {}

    # Expand environment variables
    data = expand_env_vars(raw_data)

    # Build config object
    config = GanudaConfig()

    # Load each section
    if 'gateway' in data:
        config.gateway = _dict_to_dataclass(GatewayConfig, data['gateway'])

    if 'inference' in data:
        config.inference = _dict_to_dataclass(InferenceConfig, data['inference'])

    if 'sag' in data:
        sag_data = data['sag']
        if 'features' in sag_data:
            sag_data['features'] = _dict_to_dataclass(SAGFeaturesConfig, sag_data['features'])
        config.sag = _dict_to_dataclass(SAGConfig, sag_data)

    if 'public_site' in data:
        config.public_site = _dict_to_dataclass(PublicSiteConfig, data['public_site'])

    if 'database' in data:
        config.database = _dict_to_dataclass(DatabaseConfig, data['database'])

    if 'redis' in data:
        config.redis = _dict_to_dataclass(RedisConfig, data['redis'])

    if 'logging' in data:
        config.logging = _dict_to_dataclass(LoggingConfig, data['logging'])

    if 'modules' in data:
        config.modules = _load_modules_config(data['modules'])

    if 'security' in data:
        config.security = _dict_to_dataclass(SecurityConfig, data['security'])

    if 'auth' in data:
        config.auth = _dict_to_dataclass(AuthConfig, data['auth'])

    if 'integrations' in data:
        config.integrations = _dict_to_dataclass(IntegrationsConfig, data['integrations'])

    if 'maintenance' in data:
        config.maintenance = _dict_to_dataclass(MaintenanceConfig, data['maintenance'])

    if 'nodes' in data:
        config.nodes = {
            name: _dict_to_dataclass(NodeConfig, node_data)
            for name, node_data in data['nodes'].items()
        }

    return config


def _dict_to_dataclass(cls, data: dict):
    """Convert dictionary to dataclass, ignoring extra keys"""
    if data is None:
        return cls()

    # Get field names from dataclass
    field_names = {f.name for f in cls.__dataclass_fields__.values()}

    # Filter to only known fields
    filtered = {k: v for k, v in data.items() if k in field_names}

    return cls(**filtered)


def _load_modules_config(data: dict) -> ModulesConfig:
    """Load modules config with backward compatibility for flat structure"""
    modules = ModulesConfig()

    # Handle new nested structure
    if 'council' in data and isinstance(data['council'], dict):
        modules.council = _dict_to_dataclass(CouncilConfig, data['council'])

    if 'memory' in data and isinstance(data['memory'], dict):
        modules.memory = _dict_to_dataclass(MemoryConfig, data['memory'])

    if 'breadcrumbs' in data and isinstance(data['breadcrumbs'], dict):
        modules.breadcrumbs = _dict_to_dataclass(BreadcrumbsConfig, data['breadcrumbs'])

    if 'fse' in data and isinstance(data['fse'], dict):
        modules.fse = _dict_to_dataclass(FSEConfig, data['fse'])

    if 'triad' in data and isinstance(data['triad'], dict):
        modules.triad = _dict_to_dataclass(TriadConfig, data['triad'])

    if 'multi_tenant' in data and isinstance(data['multi_tenant'], dict):
        modules.multi_tenant = _dict_to_dataclass(MultiTenantConfig, data['multi_tenant'])

    # Handle legacy flat structure (backward compatibility)
    if 'council_enabled' in data:
        modules.council.enabled = data['council_enabled']
    if 'council_specialists' in data:
        modules.council.specialists = data['council_specialists']
    if 'memory_enabled' in data:
        modules.memory.enabled = data['memory_enabled']
    if 'memory_thermal_decay' in data:
        modules.memory.thermal_decay = data['memory_thermal_decay']
    if 'breadcrumbs_enabled' in data:
        modules.breadcrumbs.enabled = data['breadcrumbs_enabled']
    if 'fse_enabled' in data:
        modules.fse.enabled = data['fse_enabled']
    if 'triad_enabled' in data:
        modules.triad.enabled = data['triad_enabled']
    if 'multi_tenant_enabled' in data:
        modules.multi_tenant.enabled = data['multi_tenant_enabled']

    return modules


# ============================================================
# CONVENIENCE ACCESSORS
# ============================================================

_config_instance: Optional[GanudaConfig] = None

def get_config() -> GanudaConfig:
    """Get the global config instance (lazy loaded)"""
    global _config_instance
    if _config_instance is None:
        _config_instance = load_config()
    return _config_instance


def get_db_config() -> dict:
    """Get database config as dict (for psycopg2)"""
    cfg = get_config().database
    return {
        'host': cfg.host,
        'port': cfg.port,
        'database': cfg.database,
        'user': cfg.user,
        'password': cfg.password
    }


def get_redis_config() -> dict:
    """Get redis config as dict"""
    cfg = get_config().redis
    return {
        'host': cfg.host,
        'port': cfg.port,
        'password': cfg.password or None,
        'db': cfg.db
    }


def is_module_enabled(module_name: str) -> bool:
    """Check if a module is enabled"""
    modules = get_config().modules
    module_map = {
        'council': modules.council.enabled,
        'memory': modules.memory.enabled,
        'breadcrumbs': modules.breadcrumbs.enabled,
        'fse': modules.fse.enabled,
        'triad': modules.triad.enabled,
        'multi_tenant': modules.multi_tenant.enabled
    }
    return module_map.get(module_name, False)
```

---

## Task: Migrate SAG to Use ganuda.yaml

### Step 1: Create config helper for SAG

Create `/home/dereadi/sag_unified_interface/config.py`:

```python
"""
SAG Configuration - Uses central ganuda.yaml
"""
import sys
sys.path.insert(0, '/ganuda/lib')

from config_schema import get_config, get_db_config, get_redis_config

# Export for easy import
__all__ = ['get_config', 'get_db_config', 'get_redis_config', 'DB_CONFIG', 'REDIS_CONFIG']

# Legacy compatibility - modules can import DB_CONFIG directly
_config = get_config()

DB_CONFIG = get_db_config()

REDIS_CONFIG = get_redis_config()
```

### Step 2: Update each SAG module

Replace hardcoded configs with imports:

```python
# OLD (in action_integrations.py, event_manager.py, etc.)
DB_CONFIG = {
    'host': '192.168.132.222',
    'port': 5432,
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

# NEW
from config import DB_CONFIG
```

### Step 3: Files to update

Run these sed commands on redfin:

```bash
# Create the config.py helper
cat > /home/dereadi/sag_unified_interface/config.py << 'EOF'
"""SAG Configuration - Uses central ganuda.yaml"""
import sys
sys.path.insert(0, '/ganuda/lib')
from config_schema import get_config, get_db_config, get_redis_config

DB_CONFIG = get_db_config()
REDIS_CONFIG = get_redis_config()

def get_sag_config():
    return get_config().sag
EOF

# Update action_integrations.py
sed -i '/^DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/action_integrations.py
sed -i '/^REDIS_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/action_integrations.py
sed -i '1i from config import DB_CONFIG, REDIS_CONFIG' /home/dereadi/sag_unified_interface/action_integrations.py

# Update event_manager.py
sed -i '/^DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/event_manager.py
sed -i '/^FEDERATION_DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/event_manager.py
sed -i '1i from config import DB_CONFIG\nFEDERATION_DB_CONFIG = DB_CONFIG' /home/dereadi/sag_unified_interface/event_manager.py

# Update email_intelligence.py
sed -i '/^DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/email_intelligence.py
sed -i '1i from config import DB_CONFIG' /home/dereadi/sag_unified_interface/email_intelligence.py

# Update kanban_integration.py
sed -i '/^DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/kanban_integration.py
sed -i '1i from config import DB_CONFIG' /home/dereadi/sag_unified_interface/kanban_integration.py

# Update create_database.py
sed -i '/^DB_CONFIG = {/,/^}/d' /home/dereadi/sag_unified_interface/create_database.py
sed -i '1i from config import DB_CONFIG' /home/dereadi/sag_unified_interface/create_database.py

# Update messaging.py
sed -i "s/redis.Redis(host='localhost', port=6379/redis.Redis(**REDIS_CONFIG/" /home/dereadi/sag_unified_interface/messaging.py
sed -i '1i from config import REDIS_CONFIG' /home/dereadi/sag_unified_interface/messaging.py
```

---

## Environment Variables

Create `/ganuda/config/.env.example`:

```bash
# Ganuda Environment Variables
# Copy to .env and fill in values

# Database password (required)
DB_PASSWORD=your_secure_password_here

# SAG secret key for sessions
SAG_SECRET_KEY=generate_with_python_secrets_token_hex_32

# Integration credentials (optional)
TELEGRAM_BOT_TOKEN=
ICLOUD_APPLE_ID=
ICLOUD_APP_PASSWORD=
SLACK_BOT_TOKEN=
SLACK_SIGNING_SECRET=
```

Create `/ganuda/config/load_env.sh`:

```bash
#!/bin/bash
# Source this before starting services
# Usage: source /ganuda/config/load_env.sh

if [ -f /ganuda/config/.env ]; then
    export $(grep -v '^#' /ganuda/config/.env | xargs)
    echo "Loaded environment from /ganuda/config/.env"
else
    echo "Warning: /ganuda/config/.env not found"
fi
```

---

## Testing

After migration, verify:

```bash
# Test config loading
python3 -c "
import sys
sys.path.insert(0, '/ganuda/lib')
from config_schema import get_config, get_db_config

config = get_config()
print('Gateway port:', config.gateway.port)
print('SAG port:', config.sag.port)
print('Database host:', config.database.host)
print('Council enabled:', config.modules.council.enabled)
print()
print('DB_CONFIG:', get_db_config())
"

# Test database connection with config
python3 -c "
import sys
sys.path.insert(0, '/ganuda/lib')
from config_schema import get_db_config
import psycopg2

conn = psycopg2.connect(**get_db_config())
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM thermal_memory_archive')
print('Thermal memories:', cur.fetchone()[0])
conn.close()
"

# Restart services and verify
sudo systemctl restart llm-gateway
# Check SAG still works
curl http://localhost:4000/health
```

---

## Success Criteria

1. ✅ Single `/ganuda/config/ganuda.yaml` contains ALL configuration
2. ✅ Gateway reads from ganuda.yaml (already done)
3. ✅ SAG reads from ganuda.yaml
4. ✅ No hardcoded DB_CONFIG in any Python files
5. ✅ Sensitive values use environment variables
6. ✅ Config changes require only editing one file
7. ✅ All services restart cleanly after config changes

---

## File Locations Summary

| File | Purpose |
|------|---------|
| `/ganuda/config/ganuda.yaml` | THE config file |
| `/ganuda/config/.env` | Secrets (not in git) |
| `/ganuda/config/.env.example` | Template for secrets |
| `/ganuda/lib/config_schema.py` | Config loading and schema |
| `/home/dereadi/sag_unified_interface/config.py` | SAG config helper |

---

*For Seven Generations*

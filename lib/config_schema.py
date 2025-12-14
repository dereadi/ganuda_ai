#!/usr/bin/env python3
"""
Ganuda Configuration Schema
Single source of truth for all Gateway settings
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import yaml
import os

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
class DatabaseConfig:
    host: str = "192.168.132.222"
    port: int = 5432
    database: str = "zammad_production"
    user: str = "claude"
    password: str = ""
    pool_size: int = 10

@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "text"
    file: Optional[str] = "/ganuda/logs/gateway.log"
    audit_enabled: bool = True
    audit_retention_days: int = 90

@dataclass
class ModulesConfig:
    """Intelligence modules - all disabled by default for Gateway v1"""
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
        """Load configuration from YAML file"""
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        return cls._from_dict(data)

    @classmethod
    def _from_dict(cls, data: dict) -> 'GanudaConfig':
        """Create config from dictionary with environment variable expansion"""
        def expand_env(value):
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                default = None
                if ':-' in env_var:
                    env_var, default = env_var.split(':-', 1)
                return os.environ.get(env_var, default)
            return value

        def process_dict(d):
            if isinstance(d, dict):
                return {k: process_dict(expand_env(v)) for k, v in d.items()}
            elif isinstance(d, list):
                return [process_dict(expand_env(i)) for i in d]
            return d

        data = process_dict(data)
        
        gateway = GatewayConfig(**data.get('gateway', {})) if 'gateway' in data else GatewayConfig()
        inference = InferenceConfig(**data.get('inference', {})) if 'inference' in data else InferenceConfig()
        database = DatabaseConfig(**data.get('database', {})) if 'database' in data else DatabaseConfig()
        logging = LoggingConfig(**data.get('logging', {})) if 'logging' in data else LoggingConfig()
        modules = ModulesConfig(**data.get('modules', {})) if 'modules' in data else ModulesConfig()
        
        return cls(gateway=gateway, inference=inference, database=database, logging=logging, modules=modules)

    def to_dict(self) -> dict:
        """Convert config to dictionary"""
        from dataclasses import asdict
        return asdict(self)

    def to_yaml(self, path: str):
        """Save configuration to YAML file"""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False, sort_keys=False)


def load_config(path: str = None) -> GanudaConfig:
    """Load configuration from file or environment"""
    if path is None:
        path = os.environ.get('GANUDA_CONFIG', '/ganuda/config/ganuda.yaml')
    
    if os.path.exists(path):
        return GanudaConfig.from_yaml(path)
    else:
        return GanudaConfig()


# For Seven Generations

"""
ganuda-config: Core Configuration Library
Cherokee AI Federation - For the Seven Generations

CORE PACKAGE - Shared across all Assist applications

Features:
- Pydantic BaseSettings with sensible defaults
- Environment variable loading
- silverfin vault secret integration
- Standard config fields (database, security, etc.)

Usage:
    from ganuda_config import BaseAssistSettings

    class Settings(BaseAssistSettings):
        # App-specific settings
        MY_CUSTOM_SETTING: str = "default"
"""

__version__ = "1.0.0"

# TODO: Extract base from /ganuda/vetassist/backend/app/core/config.py

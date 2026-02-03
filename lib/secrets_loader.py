"""
Cherokee AI Federation - Centralized Secrets Loader
====================================================
Created: 2026-02-02
Task: SECURITY-PHASE1-CRED-ROTATION

Three-tier secret resolution:
  1. /ganuda/config/secrets.env (file-based, preferred)
  2. Environment variables (for containerized deployments)
  3. FreeIPA vault via /ganuda/scripts/get-vault-secret.sh (last resort)

Usage:
    from lib.secrets_loader import get_db_config, get_telegram_token, get_llm_api_key

    db = get_db_config()          # Returns dict with host, dbname, user, password, port
    token = get_telegram_token()  # Returns string
    key = get_llm_api_key()       # Returns string

Thread Safety:
    All file reads are protected by threading.Lock. Safe for multi-threaded services.

IMPORTANT: This module NEVER hardcodes passwords. If all three tiers fail,
it raises RuntimeError rather than falling back to a default.
"""

import os
import logging
import subprocess
import threading

logger = logging.getLogger(__name__)

_SECRETS_FILE = "/ganuda/config/secrets.env"
_VAULT_SCRIPT = "/ganuda/scripts/get-vault-secret.sh"

_lock = threading.Lock()
_cache = {}
_cache_loaded = False


def _load_secrets_file():
    """Load secrets from the .env file into the cache. Thread-safe."""
    global _cache, _cache_loaded
    with _lock:
        if _cache_loaded:
            return
        if not os.path.exists(_SECRETS_FILE):
            logger.warning(
                "secrets_loader: %s not found, will use env/vault fallback",
                _SECRETS_FILE,
            )
            _cache_loaded = True
            return
        try:
            with open(_SECRETS_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if value and value != "<TO_BE_SET>":
                        _cache[key] = value
            logger.info(
                "secrets_loader: loaded %d secrets from %s",
                len(_cache),
                _SECRETS_FILE,
            )
        except (IOError, OSError) as exc:
            logger.warning(
                "secrets_loader: failed to read %s: %s", _SECRETS_FILE, exc
            )
        _cache_loaded = True


def _get_from_vault(secret_name):
    """Attempt to retrieve a secret from FreeIPA vault via shell script."""
    if not os.path.exists(_VAULT_SCRIPT):
        logger.warning(
            "secrets_loader: vault script %s not found", _VAULT_SCRIPT
        )
        return None
    try:
        result = subprocess.run(
            [_VAULT_SCRIPT, secret_name],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            logger.info(
                "secrets_loader: retrieved '%s' from vault", secret_name
            )
            return result.stdout.strip()
        else:
            logger.warning(
                "secrets_loader: vault returned rc=%d for '%s'",
                result.returncode,
                secret_name,
            )
    except (subprocess.TimeoutExpired, OSError) as exc:
        logger.warning(
            "secrets_loader: vault call failed for '%s': %s",
            secret_name,
            exc,
        )
    return None


def get_secret(key):
    """
    Resolve a single secret through the three-tier fallback chain.

    Args:
        key: The secret name (e.g., 'CHEROKEE_DB_PASS')

    Returns:
        The secret value as a string.

    Raises:
        RuntimeError: If the secret cannot be resolved from any tier.
    """
    _load_secrets_file()

    # Tier 1: secrets.env file
    value = _cache.get(key)
    if value:
        return value

    # Tier 2: environment variable
    value = os.environ.get(key)
    if value:
        logger.warning(
            "secrets_loader: '%s' resolved from environment variable (tier 2)",
            key,
        )
        return value

    # Tier 3: FreeIPA vault
    value = _get_from_vault(key)
    if value:
        logger.warning(
            "secrets_loader: '%s' resolved from vault (tier 3)", key
        )
        return value

    raise RuntimeError(
        f"secrets_loader: unable to resolve secret '{key}' from any source. "
        f"Check {_SECRETS_FILE}, environment variables, or vault configuration."
    )


def get_db_config(prefix="CHEROKEE"):
    """
    Return a database configuration dictionary.

    Args:
        prefix: 'CHEROKEE' or 'VETASSIST' to select which database.

    Returns:
        dict with keys: host, dbname, user, password, port
    """
    return {
        "host": get_secret(f"{prefix}_DB_HOST"),
        "dbname": get_secret(f"{prefix}_DB_NAME"),
        "user": get_secret(f"{prefix}_DB_USER"),
        "password": get_secret(f"{prefix}_DB_PASS"),
        "port": int(get_secret(f"{prefix}_DB_PORT")),
    }


def get_telegram_token():
    """Return the Telegram bot token."""
    return get_secret("TELEGRAM_BOT_TOKEN")


def get_llm_api_key():
    """Return the LLM Gateway API key."""
    return get_secret("LLM_GATEWAY_API_KEY")


def get_llm_gateway_url():
    """Return the LLM Gateway base URL."""
    return get_secret("LLM_GATEWAY_URL")


def reload_secrets():
    """
    Force a reload of the secrets file on next access.
    Useful after secrets.env has been updated.
    """
    global _cache, _cache_loaded
    with _lock:
        _cache = {}
        _cache_loaded = False
    logger.info("secrets_loader: cache cleared, will reload on next access")

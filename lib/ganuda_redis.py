#!/usr/bin/env python3
"""
Ganuda Shared Redis Client with Connection Pooling
Single source of truth for all Redis connections in Ganuda

Usage:
    from ganuda_redis import get_redis
    
    r = get_redis()
    r.get('key')
    # Connection automatically returned to pool
"""
import redis
import os

# Configuration
REDIS_HOST = os.environ.get('REDIS_HOST', '192.168.132.222')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_MAX_CONNECTIONS = int(os.environ.get('REDIS_MAX_CONNECTIONS', 10))

# Single connection pool for entire application
_pool = redis.ConnectionPool(
    host=REDIS_HOST,
    port=REDIS_PORT,
    max_connections=REDIS_MAX_CONNECTIONS,
    socket_timeout=5,
    socket_connect_timeout=5,
    socket_keepalive=True,
    health_check_interval=30,
    decode_responses=True
)

def get_redis():
    """Get Redis client from shared pool."""
    return redis.Redis(connection_pool=_pool)

def get_pool_stats():
    """Get current pool statistics."""
    return {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'max_connections': REDIS_MAX_CONNECTIONS,
    }

def close_pool():
    """Gracefully close all connections in pool."""
    _pool.disconnect()

# For backward compatibility
pool = _pool

if __name__ == '__main__':
    r = get_redis()
    r.ping()
    print(f'Redis OK: {REDIS_HOST}:{REDIS_PORT}')
    print(f'Pool: {get_pool_stats()}')

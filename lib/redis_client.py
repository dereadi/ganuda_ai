#!/usr/bin/env python3
"""
Shared Redis Client with Connection Pooling
Single source of truth for all Redis connections in Ganuda

Usage:
    from redis_client import get_redis
    
    r = get_redis()
    r.get('key')
    # Connection automatically returned to pool
"""
import redis
import os

# Configuration - can be overridden by environment variables
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
    """
    Get Redis client from shared pool.
    Connection is automatically returned to pool when client goes out of scope.
    """
    return redis.Redis(connection_pool=_pool)

def get_pool_stats():
    """Get current pool statistics"""
    return {
        'host': REDIS_HOST,
        'port': REDIS_PORT,
        'max_connections': REDIS_MAX_CONNECTIONS,
        'created_connections': _pool._created_connections if hasattr(_pool, '_created_connections') else 'N/A'
    }

def close_pool():
    """Gracefully close all connections in pool"""
    _pool.disconnect()

# For backward compatibility - direct pool access if needed
pool = _pool

if __name__ == '__main__':
    # Test the connection
    r = get_redis()
    r.ping()
    print(f'Redis connection successful: {REDIS_HOST}:{REDIS_PORT}')
    print(f'Pool stats: {get_pool_stats()}')

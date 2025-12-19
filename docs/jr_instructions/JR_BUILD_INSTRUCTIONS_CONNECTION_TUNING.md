# Jr Build Instructions: Connection & System Tuning

## Priority: MEDIUM - Performance & Stability

---

## Problem Statement

Observed issues on redfin (192.168.132.223):
- 90+ Redis connections to bluefin (should be pooled)
- TCP keepalive set to 7200 seconds (2 hours) - too long for idle detection
- SSH connections can pile up during heavy automation

---

## 1. SSH Daemon Tuning

### Current Settings (Already Good)
```
MaxStartups 200:30:400
MaxSessions 100
```

### Add Idle Connection Killing

Edit `/etc/ssh/sshd_config`:

```bash
# Kill idle SSH connections after 5 minutes of inactivity
ClientAliveInterval 300
ClientAliveCountMax 2
# Total timeout: 300 * 2 = 600 seconds (10 minutes)

# Reduce login grace time
LoginGraceTime 30

# Enable TCP keepalive at SSH level
TCPKeepAlive yes
```

Apply:
```bash
sudo systemctl reload sshd
```

---

## 2. TCP Keepalive Tuning (Kernel)

### Current (Too Long)
```
net.ipv4.tcp_keepalive_time = 7200   # 2 hours before first probe
net.ipv4.tcp_keepalive_intvl = 75    # 75 sec between probes
net.ipv4.tcp_keepalive_probes = 9    # 9 probes before killing
```

### Recommended (Faster Idle Detection)

Create `/etc/sysctl.d/99-ganuda-tcp.conf`:

```bash
# Detect dead connections faster
# First probe after 10 minutes idle
net.ipv4.tcp_keepalive_time = 600

# Probe every 30 seconds after that
net.ipv4.tcp_keepalive_intvl = 30

# Kill after 3 failed probes (600 + 30*3 = 690 seconds total)
net.ipv4.tcp_keepalive_probes = 3

# Faster TIME_WAIT recycling
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30

# Increase connection tracking (if using iptables/nftables)
net.netfilter.nf_conntrack_max = 262144
```

Apply:
```bash
sudo sysctl -p /etc/sysctl.d/99-ganuda-tcp.conf
```

---

## 3. Redis Connection Pooling

### Problem
90+ connections from redfin to Redis on bluefin. This suggests:
- No connection pooling
- Connections not being closed
- Each request opens new connection

### Solution: Use Connection Pool

In Python code that connects to Redis:

**Before (Bad)**:
```python
import redis

def get_data():
    r = redis.Redis(host='192.168.132.222', port=6379)
    return r.get('key')
    # Connection leaked!
```

**After (Good)**:
```python
import redis

# Create pool once at module level
REDIS_POOL = redis.ConnectionPool(
    host='192.168.132.222',
    port=6379,
    max_connections=10,  # Limit total connections
    socket_timeout=5,
    socket_connect_timeout=5,
    retry_on_timeout=True
)

def get_data():
    r = redis.Redis(connection_pool=REDIS_POOL)
    return r.get('key')
    # Connection returned to pool automatically
```

### Files to Check on redfin

```bash
# Find all Redis connections in code
grep -r "redis.Redis\|redis.StrictRedis" /ganuda/ --include="*.py"
grep -r "redis.Redis\|redis.StrictRedis" /ganuda/home/dereadi/sag_unified_interface/ --include="*.py"
```

### Add to ganuda.yaml

```yaml
redis:
  host: 192.168.132.222
  port: 6379
  max_connections: 10
  socket_timeout: 5
  socket_connect_timeout: 5
```

### Create Shared Redis Client

Add to `/ganuda/lib/redis_client.py`:

```python
"""
Shared Redis client with connection pooling
"""
import redis
import sys
sys.path.insert(0, '/ganuda/lib')
from config_schema import GanudaConfig

_config = GanudaConfig.from_yaml('/ganuda/config/ganuda.yaml')

# Single connection pool for all code
_pool = redis.ConnectionPool(
    host=_config.redis.host if hasattr(_config, 'redis') else '192.168.132.222',
    port=_config.redis.port if hasattr(_config, 'redis') else 6379,
    max_connections=10,
    socket_timeout=5,
    socket_connect_timeout=5,
    decode_responses=True
)

def get_redis():
    """Get Redis client from shared pool"""
    return redis.Redis(connection_pool=_pool)

def get_pool_stats():
    """Check pool utilization"""
    return {
        'max_connections': _pool.max_connections,
        'current_connections': len(_pool._in_use_connections) if hasattr(_pool, '_in_use_connections') else 'unknown'
    }
```

---

## 4. File Descriptor Limits

### Current
```
ulimit -n = 1024
```

### Recommended

Edit `/etc/security/limits.conf`:

```bash
# For dereadi user (runs services)
dereadi soft nofile 65536
dereadi hard nofile 65536

# For root
root soft nofile 65536
root hard nofile 65536
```

Also edit `/etc/systemd/system.conf`:

```ini
DefaultLimitNOFILE=65536
```

And for each service unit, add:

```ini
[Service]
LimitNOFILE=65536
```

Apply:
```bash
sudo systemctl daemon-reload
# Log out and back in for limits.conf changes
```

---

## 5. Monitoring Script

Create `/ganuda/scripts/check_connections.sh`:

```bash
#!/bin/bash
# Monitor connection health

echo "=== Connection Report $(date) ==="
echo ""

echo "SSH Connections:"
ss -tn state established '( dport = :22 or sport = :22 )' | wc -l

echo ""
echo "Redis Connections (to bluefin):"
ss -tn state established | grep ':6379' | wc -l

echo ""
echo "Postgres Connections:"
ss -tn state established | grep ':5432' | wc -l

echo ""
echo "TIME_WAIT sockets:"
ss -tn state time-wait | wc -l

echo ""
echo "Open files by key services:"
for svc in python uvicorn vllm; do
    count=$(lsof -c $svc 2>/dev/null | wc -l)
    echo "  $svc: $count"
done

# Alert if Redis connections > 20
REDIS_CONN=$(ss -tn state established | grep ':6379' | wc -l)
if [ "$REDIS_CONN" -gt 20 ]; then
    echo ""
    echo "WARNING: High Redis connection count: $REDIS_CONN"
fi
```

Add to cron (every 5 minutes):
```bash
*/5 * * * * /ganuda/scripts/check_connections.sh >> /ganuda/logs/connections.log 2>&1
```

---

## 6. Quick Fixes (Apply Now)

### On redfin:

```bash
# 1. Update sshd for idle killing
sudo tee -a /etc/ssh/sshd_config.d/ganuda.conf << 'EOF'
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
EOF
sudo systemctl reload sshd

# 2. Apply TCP tuning
sudo tee /etc/sysctl.d/99-ganuda-tcp.conf << 'EOF'
net.ipv4.tcp_keepalive_time = 600
net.ipv4.tcp_keepalive_intvl = 30
net.ipv4.tcp_keepalive_probes = 3
net.ipv4.tcp_tw_reuse = 1
net.ipv4.tcp_fin_timeout = 30
EOF
sudo sysctl -p /etc/sysctl.d/99-ganuda-tcp.conf

# 3. Increase file limits for services
sudo systemctl edit llm-gateway.service --force
# Add: LimitNOFILE=65536
sudo systemctl daemon-reload
sudo systemctl restart llm-gateway
```

---

## Verification

After applying changes:

```bash
# Check new sysctl values
sysctl net.ipv4.tcp_keepalive_time
# Should show: 600

# Check SSH config
sshd -T | grep -i clientalive
# Should show: clientaliveinterval 300

# Monitor Redis connections over time
watch -n 5 'ss -tn state established | grep :6379 | wc -l'
# Should decrease and stabilize
```

---

## Success Criteria

| Metric | Before | Target |
|--------|--------|--------|
| Redis connections | 90+ | <15 |
| TCP keepalive | 7200s | 600s |
| SSH idle timeout | None | 10 min |
| File descriptors | 1024 | 65536 |

---

*For Seven Generations*

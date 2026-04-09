# KB: PgBouncer Connection Pooling — Bluefin Deployment

## Date: April 2, 2026
## Node: bluefin (10.100.0.2)
## Kanban: DB-HEALTH-EPIC

---

## What Is PgBouncer

PgBouncer sits between applications and PostgreSQL. Instead of each service opening its own connection to Postgres (expensive — each conn uses ~5-10MB RAM), PgBouncer maintains a pool of connections and shares them across clients. This reduces connection overhead, prevents connection exhaustion, and improves query latency.

## Why We Need It

- Stoneclad has 17+ services on redfin all connecting to bluefin's PostgreSQL
- Each Jr worker, daemon, and API opens its own connection
- PostgreSQL default max_connections = 100. We've been close to hitting it.
- Internal SLA: connection utilization < 80%
- PgBouncer reduces 50+ application connections to ~10-15 actual Postgres connections

## Installation

```bash
# On bluefin (requires apt-get — needs FreeIPA sudo rule for apt-get)
ssh dereadi@10.100.0.2 'sudo apt-get install -y pgbouncer'
```

**NOTE:** As of Apr 2 2026, `apt-get` is NOT in the FreeIPA NOPASSWD list for bluefin. You need to either:
1. Run it interactively with password: `! ssh dereadi@10.100.0.2 'sudo apt-get install -y pgbouncer'`
2. Add apt-get to FreeIPA NOPASSWD rules (see KB-FREEIPA-SUDO-RULES.md)

## Configuration

PgBouncer config lives at `/etc/pgbouncer/pgbouncer.ini`:

```ini
[databases]
zammad_production = host=127.0.0.1 port=5432 dbname=zammad_production

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
stats_period = 60
```

Key settings:
- `pool_mode = transaction` — connections returned to pool after each transaction (best for our workload)
- `default_pool_size = 20` — 20 actual Postgres connections shared across all clients
- `max_client_conn = 200` — up to 200 application connections
- `listen_port = 6432` — PgBouncer listens here, Postgres stays on 5432

## User Auth File

```bash
# Create /etc/pgbouncer/userlist.txt
echo '"claude" "bIDhRwvSU8Fm6ezeZw9ujQvLqe0CNAg4"' | sudo tee /etc/pgbouncer/userlist.txt > /dev/null
sudo chmod 640 /etc/pgbouncer/userlist.txt
sudo chown pgbouncer:pgbouncer /etc/pgbouncer/userlist.txt
```

## Deploy Config

```bash
# Write config via sudo tee
cat << 'CONF' | ssh dereadi@10.100.0.2 'sudo tee /etc/pgbouncer/pgbouncer.ini > /dev/null'
[databases]
zammad_production = host=127.0.0.1 port=5432 dbname=zammad_production

[pgbouncer]
listen_addr = 0.0.0.0
listen_port = 6432
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
max_client_conn = 200
default_pool_size = 20
min_pool_size = 5
reserve_pool_size = 5
reserve_pool_timeout = 3
server_lifetime = 3600
server_idle_timeout = 600
log_connections = 1
log_disconnections = 1
stats_period = 60
CONF
```

## Start and Enable

```bash
ssh dereadi@10.100.0.2 'sudo systemctl enable pgbouncer && sudo systemctl start pgbouncer'
```

## Verify

```bash
# Check PgBouncer is running
ssh dereadi@10.100.0.2 'sudo systemctl is-active pgbouncer'

# Connect through PgBouncer (port 6432 instead of 5432)
psql -h 10.100.0.2 -p 6432 -U claude -d zammad_production -c "SELECT 1;"

# Check pool stats
psql -h 10.100.0.2 -p 6432 -U claude -d pgbouncer -c "SHOW POOLS;"
```

## Migration Path

Once PgBouncer is verified:
1. Update `config/secrets.env`: change `CHEROKEE_DB_HOST` port to 6432
2. Update services one at a time to connect via 6432 instead of 5432
3. Monitor pool utilization via `SHOW POOLS;` and `SHOW STATS;`
4. Keep direct 5432 access for admin tasks and migrations

## Rollback

If PgBouncer causes issues:
```bash
ssh dereadi@10.100.0.2 'sudo systemctl stop pgbouncer'
# Applications fall back to direct 5432 connections — no config change needed
```

---

*For Seven Generations.*

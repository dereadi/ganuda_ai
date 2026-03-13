# [RECURSIVE] DC-16 Phase 1: Database Reflex Layer — Drop Indexes, Tune Autovacuum, Retention Policies, Fix Fire Guard - Step 15

**Parent Task**: #1288
**Auto-decomposed**: 2026-03-12T17:58:55.939181
**Original Step Title**: Wire check_postgres_db into Fire Guard remote checks

---

### Step 15: Wire check_postgres_db into Fire Guard remote checks

In `/ganuda/scripts/fire_guard.py`, find the `run_checks()` function. In the remote port
check loop, add a special case: when `label == "PostgreSQL"`, call `check_postgres_db(ip, port)`
instead of `check_port(ip, port)`.

**Modify:** `/ganuda/scripts/fire_guard.py`

Find this block in `run_checks()`:
```python
    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            up = check_port(ip, port)
```

Replace with:
```python
    # Remote ports
    for node, checks in REMOTE_CHECKS.items():
        for ip, port, label in checks:
            if label == "PostgreSQL":
                up = check_postgres_db(ip, port)
            else:
                up = check_port(ip, port)
```

# Jr Instruction: Goldfin PII Vault End-to-End Verification

**Task**: GOLDFIN-VERIFY-001
**Priority**: 3 (HIGH — blocks VetAssist P2 and P4)
**Assigned Jr**: Infrastructure Jr.
**Target Nodes**: goldfin (192.168.20.10 via greenfin bridge), redfin, greenfin
**use_rlm**: false

## Context

Goldfin is the Inner Sanctum — dedicated PII vault on VLAN 20 behind greenfin's bridge. It's alive (pings from greenfin confirmed Mar 12 2026). Kanban ticket "Verify Goldfin PII database alive and populated" is OPEN. Three VetAssist tickets are blocked waiting on this verification: Stripe (P2), VSO White-Label (P2), Physician Network (P4).

The P0 kanban ticket was marked completed but the Owl pass never ran. We need to confirm the plumbing works end-to-end.

## Steps

### Step 1: Verify goldfin PostgreSQL is running
SSH from greenfin to goldfin and confirm:
- PostgreSQL service is active
- `vetassist_pii` database exists
- List tables in vetassist_pii and report schema

```text
# Run from greenfin (192.168.132.224):
ssh 192.168.20.10 'systemctl is-active postgresql'
ssh 192.168.20.10 'psql -U postgres -l'
ssh 192.168.20.10 'psql -U postgres -d vetassist_pii -c "\dt"'
```

### Step 2: Verify network path from redfin to goldfin
Redfin needs a route to 192.168.20.0/24 via greenfin (192.168.132.224). Check:
- Does redfin have a static route to 192.168.20.0/24?
- Can redfin reach goldfin:5432 through greenfin?

```text
# Run from redfin:
ip route show | grep 192.168.20
# If no route exists, document it — TPM will add via netplan
```

### Step 3: Verify database connectivity from redfin
If route exists, test actual psycopg2 connection from redfin to goldfin:5432.

```text
# Run from redfin:
python3 -c "
import psycopg2
conn = psycopg2.connect(host='192.168.20.10', port=5432, dbname='vetassist_pii', user='claude', password='<from secrets>')
cur = conn.cursor()
cur.execute('SELECT current_database(), version()')
print(cur.fetchone())
conn.close()
"
```

### Step 4: Report findings
Thermalize results with domain_tag='goldfin_verify'. Include:
- PostgreSQL version on goldfin
- vetassist_pii schema (tables, row counts)
- Network reachability from redfin (yes/no, route details)
- Any missing configuration that blocks end-to-end PII flow

## Acceptance Criteria
1. PostgreSQL confirmed running on goldfin with vetassist_pii database
2. Network path from redfin → greenfin → goldfin documented
3. End-to-end database connectivity tested or gaps identified
4. Thermal written with findings
5. Kanban ticket "Verify Goldfin PII database alive and populated" updated with results

## Notes
- Do NOT create or modify any databases. This is READ-ONLY verification.
- If vetassist_pii doesn't exist, report that — don't create it.
- If routes are missing, report that — TPM will handle netplan changes.

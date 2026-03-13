# [RECURSIVE] Greenfin Sentinel — Sub-Claude Watchdog on Critical Infrastructure Node - Step 5

**Parent Task**: #1294
**Auto-decomposed**: 2026-03-12T17:57:59.078809
**Original Step Title**: Register the sentinel agent in the database

---

### Step 5: Register the sentinel agent in the database

Run from any node with DB access (bluefin 192.168.132.222):

```bash
python3 -c "
import sys
sys.path.insert(0, '/ganuda/lib')
from secrets_loader import get_db_config
import psycopg2
conn = psycopg2.connect(**get_db_config())
cur = conn.cursor()
cur.execute(\"\"\"
    INSERT INTO jr_agent_state (agent_id, node_name, specialization, metadata)
    VALUES (
      'sentinel-greenfin-eagle',
      'greenfin',
      'sentinel',
      '{\"role\": \"watchdog\", \"services_monitored\": [\"freeipa_bridge\", \"openobserve\", \"promtail\", \"embedding_service\", \"wireguard\"], \"dc10_tier\": \"reflex\", \"longhouse_member\": true}'
    )
    ON CONFLICT (agent_id) DO UPDATE SET metadata = EXCLUDED.metadata
\"\"\")
conn.commit()
cur.close()
conn.close()
print('Sentinel agent registered in jr_agent_state')
"
```

---

## Acceptance Criteria

- greenfin-sentinel.service running on greenfin
- All 5 services showing heartbeats in service_health table
- Tier 1 recovery tested: stop promtail, verify sentinel restarts it
- Tier 2 escalation tested: block silverfin route, verify alert fires
- Disk space check functioning
- Agent registered in jr_agent_state
- Thermal written on startup
- Sentinel survives greenfin reboot (systemd enabled)

## Future: Claude API Analysis Mode

Phase 2 can add a Claude API call when the sentinel detects a pattern it hasn't seen before — e.g., "OpenObserve is healthy but response time went from 50ms to 2000ms." The sentinel would send the pattern to Sonnet for analysis and receive a recommended action. This keeps the reflex layer pure Python (fast, free) while adding a deliberation layer for novel situations.

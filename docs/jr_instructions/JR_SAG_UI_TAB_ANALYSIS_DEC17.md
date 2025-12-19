# SAG UI Tab Analysis - December 17, 2025

## Overview
This document analyzes each tab in the SAG Unified Interface (http://192.168.132.223:4000) to identify what's working, what's broken, and what needs improvement.

---

## TAB STATUS MATRIX

| Tab | Status | API Working | Data Present | Notes |
|-----|--------|-------------|--------------|-------|
| Home | ✅ WORKING | Yes | Yes | Shows systems, alerts, utilization, IoT |
| Nodes | ⚠️ PARTIAL | Yes (returns data) | Config issue | Shows nodes as "unreachable" incorrectly |
| Services | ⚠️ UNKNOWN | Needs check | | Depends on federation/nodes |
| IoT Devices | ✅ WORKING | Yes | Yes | 2898+ devices, active scanning |
| Events | ✅ WORKING | Yes | 50 events | Trading risk violations showing |
| Kanban | ⚠️ EMPTY | Yes | No tickets | API works but returns empty array |
| Alerts | ❌ BROKEN | No | N/A | Returns "Not found" |
| Email | ✅ WORKING | Yes | 10+ emails | Priority classification working |
| Messages | ⚠️ PLACEHOLDER | Yes | All zeros | No integrations active |
| Calendar | ❌ NOT IMPLEMENTED | No | N/A | Returns "Not found" |
| Monitoring | ❌ NOT IMPLEMENTED | No | N/A | Returns "Not found" |
| Tribe | ✅ WORKING | Yes | Yes | Council votes, thermal memory stats |
| Console | ⚠️ PARTIAL | Unknown | | FARA dispatch endpoints exist |
| Settings | ⚠️ PLACEHOLDER | Yes | | Config staging API exists |

---

## DETAILED ANALYSIS BY TAB

### 1. HOME TAB ✅
**Status**: Working
**APIs Used**: `/api/federation/summary`, `/api/tribe/summary`, `/api/iot/devices`

**Current Data**:
- Systems: Shows 6 healthy nodes
- Alerts: Warning/Critical counts
- Utilization: CPU/RAM %
- IoT Devices: Online/Total counts

**Issues**:
- Federation shows nodes as "unreachable" even when reachable
- Needs real-time refresh

**Jr Action Items**:
- [ ] Fix federation node reachability check logic

---

### 2. NODES TAB ⚠️
**Status**: Partial - Data issue
**APIs Used**: `/api/federation/summary`, `/api/federation/nodes`

**Current Data (from API)**:
```json
{
    "down": 2,
    "healthy": 0,
    "federation_status": "critical",
    "nodes": [
        {"node_id": "redfin", "status": "unreachable", "reachable": false},
        {"node_id": "greenfin", "status": "unreachable", "reachable": false}
    ]
}
```

**Issues**:
- Only 2 nodes configured (should be 6)
- All nodes show as "unreachable" even when local
- Node health checks failing

**Jr Action Items**:
- [ ] Add missing nodes: bluefin, sasass, sasass2, tpm-macbook
- [ ] Fix reachability check (localhost/127.0.0.1 handling)
- [ ] Add proper health check endpoints for each node

---

### 3. SERVICES TAB ⚠️
**Status**: Unknown - depends on Nodes
**APIs Used**: Services from federation/nodes API

**Issues**:
- Services array empty for all nodes
- Need to populate service definitions

**Jr Action Items**:
- [ ] Define services per node:
  - redfin: vLLM (8000), Gateway (8080), SAG UI (4000)
  - bluefin: PostgreSQL (5432), Grafana (3000)
  - greenfin: Promtail, monitoring daemons
  - sasass/sasass2: Edge services

---

### 4. IOT DEVICES TAB ✅
**Status**: Working
**APIs Used**: `/api/iot/devices`, `/api/iot/scan/history`

**Current Data**:
- 2898+ devices tracked
- Active scanning working
- Device types: intellirocks, unknown
- Status: active/inactive

**Minor Issues**:
- Many devices show "device_class": "unknown"
- No device fingerprinting active

**Jr Action Items**:
- [ ] Improve device fingerprinting
- [ ] Add manufacturer lookup by MAC OUI
- [ ] Add "authorized devices" management UI

---

### 5. EVENTS TAB ✅
**Status**: Working
**APIs Used**: `/api/events`, `/api/events/stats`

**Current Data**:
- 50 events loaded
- Categories: System, Trading Risk
- Tiers: FYI, ACTION_REQUIRED
- Sources: trading_jr_risk_management

**Example Events**:
- "⚠️ RISK VIOLATION: POSITION_SIZE" - AAPL 23.5% exceeds 10% limit
- Event dismissal and review workflow working

**Enhancement Ideas**:
- [ ] Add event severity filtering
- [ ] Add date range picker
- [ ] Add event source grouping

---

### 6. KANBAN TAB ⚠️
**Status**: Empty but functional
**APIs Used**: `/api/kanban/tickets`

**Current Data**:
```json
{"count": 0, "tickets": []}
```

**Issues**:
- No tickets in system
- May need Zammad integration or standalone ticket creation

**Jr Action Items**:
- [ ] Create ticket from Event workflow
- [ ] Import from jr_work_queue table
- [ ] Add quick ticket creation form

---

### 7. ALERTS TAB ❌
**Status**: BROKEN
**APIs Used**: `/api/alerts` (returns "Not found")

**Note**: There IS a `/api/sidebar/alerts` endpoint but it tries to query a column that doesn't exist ("voted_at").

**Jr Action Items**:
- [ ] Create `/api/alerts` endpoint
- [ ] Pull from event_stream where tier='CRITICAL' or 'WARNING'
- [ ] Add filtering by severity, time range

---

### 8. EMAIL TAB ✅
**Status**: Working
**APIs Used**: `/api/emails`, `/api/emails/job-stats`, `/api/emails/job-pipeline`

**Current Data**:
- 10 emails loaded
- Priority classification: CRITICAL, HIGH, MEDIUM, LOW
- Action required flagging working
- Categories: updates, personal, etc.

**Features Working**:
- Draft reply
- Send
- Discard

**Enhancement Ideas**:
- [ ] Email threading view
- [ ] Auto-response suggestions

---

### 9. MESSAGES TAB ⚠️
**Status**: Placeholder - No integrations active
**APIs Used**: `/api/messages/counts`, `/api/messages/<channel>`

**Current Data**:
```json
{
    "discord": 0,
    "facebook": 0,
    "instagram": 0,
    "slack": 0,
    "sms": 0,
    "telegram": 0,
    "whatsapp": 0
}
```

**Issues**:
- All channel counts zero
- No integrations configured

**Jr Action Items**:
- [ ] Integrate Telegram (bot already running!)
- [ ] Add message history from telegram_chief.py
- [ ] Consider Discord/Slack webhooks

---

### 10. CALENDAR TAB ❌
**Status**: NOT IMPLEMENTED
**APIs Used**: `/api/calendar/events` - Returns "Not found"

**Jr Action Items**:
- [ ] Create calendar_events table
- [ ] Add `/api/calendar/events` endpoint
- [ ] Consider Google Calendar integration
- [ ] Or simple standalone event creation

---

### 11. MONITORING TAB ❌
**Status**: NOT IMPLEMENTED
**APIs Used**: `/api/monitoring/overview` - Returns "Not found"

**Jr Action Items**:
- [ ] Create `/api/monitoring/overview` endpoint
- [ ] Pull metrics from:
  - Cherokee Gateway `/health`
  - vLLM `/health`
  - Node system stats (CPU, RAM, disk)
- [ ] Add Grafana embed option
- [ ] Real-time token/request counts

---

### 12. TRIBE TAB ✅
**Status**: Working - Rich data
**APIs Used**: `/api/tribe/summary`, `/api/tribe/council-votes`, `/api/tribe/specialists`, `/api/tribe/trail-health`

**Current Data**:
```json
{
    "council": {
        "total_votes": 50,
        "proceed_count": 15,
        "caution_count": 0,
        "last_vote": "2025-12-17T16:25:10"
    },
    "thermal_memory": {
        "total": 5555,
        "hot_count": 5244,
        "avg_temperature": 93.48,
        "resonance_pct": 94.4,
        "sacred_patterns": 5168
    }
}
```

**Features Working**:
- Council vote history with specialist breakdowns
- Thermal memory stats
- Deposits by specialist
- Trail health

**Enhancement Ideas (already in JR_SAG_UI_TAB_IMPROVEMENTS.md)**:
- [ ] Real-time council vote visualization
- [ ] Specialist avatar cards
- [ ] Memory temperature heatmap

---

### 13. CONSOLE TAB ⚠️
**Status**: Partial - FARA console
**APIs Used**: `/api/console/dispatch`, `/api/console/missions`, `/api/console/responses`

**Available Endpoints**:
- POST `/api/console/dispatch` - Send commands to FARA
- GET `/api/console/missions` - Get mission queue
- GET `/api/console/responses` - Get FARA responses

**Issues**:
- May have "voted_at" column error (needs verification)
- FARA integration status unknown

**Jr Action Items**:
- [ ] Verify console APIs work
- [ ] Add FARA status indicator
- [ ] Create mission submission form

---

### 14. SETTINGS TAB ⚠️
**Status**: Placeholder - Config API exists
**APIs Used**: `/api/config/schema`, `/api/config/<target>/stage`, `/api/config/<target>/apply`

**Features (backend exists)**:
- Configuration staging
- Schema-based validation
- Apply/Discard workflow

**Issues**:
- No UI implementation visible
- Targets undefined

**Jr Action Items**:
- [ ] Create settings UI
- [ ] Define config targets (gateway, vllm, telegram, etc.)
- [ ] Add API key management
- [ ] Add node configuration

---

## PRIORITY FIXES (Quick Wins)

### HIGH PRIORITY
1. **Fix Alerts Tab** - Create `/api/alerts` endpoint pulling from events
2. **Fix Federation Nodes** - Add missing 4 nodes, fix reachability checks
3. **Populate Kanban** - Import jr_work_queue into kanban UI

### MEDIUM PRIORITY
4. **Implement Calendar** - Simple event table and API
5. **Implement Monitoring** - Aggregate health from services
6. **Integrate Telegram** - Connect messages tab to existing bot

### LOW PRIORITY
7. **Settings UI** - Build config management interface
8. **IoT Fingerprinting** - Improve device identification
9. **Console/FARA** - Verify and document

---

## DATABASE TABLES TO CREATE/MODIFY

### New Tables Needed:
```sql
-- Calendar events
CREATE TABLE calendar_events (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    all_day BOOLEAN DEFAULT false,
    recurrence VARCHAR(50),
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Unified alerts (denormalized from events for quick access)
CREATE TABLE unified_alerts (
    id SERIAL PRIMARY KEY,
    source VARCHAR(100),
    severity VARCHAR(20),  -- CRITICAL, WARNING, INFO
    title VARCHAR(255),
    message TEXT,
    acknowledged BOOLEAN DEFAULT false,
    acknowledged_by VARCHAR(100),
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Tables to Modify:
```sql
-- Add missing nodes to federation config (if table exists)
-- Or create federation_nodes table
CREATE TABLE IF NOT EXISTS federation_nodes (
    node_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100),
    hostname VARCHAR(100),
    ip_address VARCHAR(45),
    role TEXT,
    services JSONB,
    health_endpoint VARCHAR(255),
    status VARCHAR(20) DEFAULT 'unknown',
    last_check TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## FOR THE JRS

This analysis provides a roadmap for SAG UI improvements. Tasks are already queued in the Jr Work Queue:
1. JR_SAG_UI_TAB_IMPROVEMENTS.md (Priority 3)
2. This analysis extends those instructions

Suggested Jr assignments:
- **Software Engineer Jr**: API endpoints, database schema
- **Frontend Jr**: UI components, real-time updates
- **Infrastructure Jr**: Health checks, node monitoring

---

*Analysis completed: December 17, 2025*
*FOR SEVEN GENERATIONS*

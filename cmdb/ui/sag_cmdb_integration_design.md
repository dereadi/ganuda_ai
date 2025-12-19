# SAG Unified Interface - CMDB Integration Design

**Author**: IT Jr 2 (UI/UX Design)
**Date**: 2025-11-28
**Status**: DESIGN COMPLETE - Ready for Implementation
**SAG Location**: http://192.168.132.223:4000/

---

## Executive Summary

Integrate CMDB (Configuration Management Database) into SAG Unified Interface to provide infrastructure visibility, dependency mapping, and change tracking alongside existing Event Management, Kanban, and monitoring capabilities.

---

## Current SAG Architecture

### Existing Components (Port 4000)
1. **Event Management Dashboard** - Real-time event monitoring
2. **Visual Kanban Board** - Links to :8002
3. **Cherokee AI Monitoring** - Links to :5555
4. **Grafana** - Embedded at :3000
5. **IoT Device Management** - Device status and control
6. **Email Intelligence** - Email analysis

### Technology Stack
- **Framework**: Python web application
- **Database**: PostgreSQL (zammad_production + triad_federation)
- **Frontend**: HTML/JS with embedded iframes
- **Location**: `/ganuda/sag-unified-interface/` (likely path)

---

## CMDB Integration Points

### 1. New Navigation Item: "Infrastructure"

Add to main navigation menu: Events | Kanban | Monitoring | **Infrastructure** | IoT | Email

**URL**: `/infrastructure` or `/cmdb`

---

### 2. Infrastructure Dashboard (New Page)

**Layout**: Three-column grid view

#### Column 1: Active Configuration Items

Display servers and services in categorized lists with status indicators.

**Query**:
```sql
SELECT ci_type, ci_name, status,
       ip_addresses[1] as ip,
       ports[1] as port
FROM cmdb_configuration_items
WHERE status = 'active'
ORDER BY ci_type, ci_name;
```

#### Column 2: Dependency Graph Visualization

Interactive node graph showing infrastructure relationships:
- Nodes: Servers (blue), Services (green), Databases (orange)
- Edges: Dependencies (arrows showing "runs_on", "depends_on")

**Query**:
```sql
SELECT
    src.ci_name as from_ci,
    src.ci_type as from_type,
    tgt.ci_name as to_ci,
    tgt.ci_type as to_type,
    r.relationship_type
FROM cmdb_relationships r
JOIN cmdb_configuration_items src ON r.source_ci = src.id
JOIN cmdb_configuration_items tgt ON r.target_ci = tgt.id;
```

**Library**: Use D3.js or vis.js for graph visualization

#### Column 3: Recent Changes Feed

Display recent CMDB changes (last 7-30 days)

**Query**:
```sql
SELECT
    c.change_timestamp,
    c.changed_by,
    c.change_type,
    ci.ci_name,
    c.change_description
FROM cmdb_changes c
JOIN cmdb_configuration_items ci ON c.ci_id = ci.id
WHERE c.change_timestamp > NOW() - INTERVAL '7 days'
ORDER BY c.change_timestamp DESC
LIMIT 10;
```

---

### 3. CI Detail View (Modal or Sub-page)

**Triggered by**: Clicking any CI in the dashboard

**Display fields**:
- Type, Status, Owner, Environment
- Network Info (IPs, DNS, Ports)
- Hardware/Software specs (JSONB)
- Services running on this node
- Related events (link to Event Dashboard)
- Related tickets (link to Kanban)
- Change history

---

### 4. Event Dashboard Integration

**Enhancement**: Add "Affected Infrastructure" column to events

Link event source hostnames to CMDB CIs for quick infrastructure context.

**Implementation**:
- Parse event source hostname → lookup in cmdb_configuration_items
- Add clickable link to CI detail view
- Optionally: Write event to cmdb_changes for full audit trail

---

### 5. Kanban Board Integration

**Enhancement**: Link tickets to affected CIs

**Zammad Schema Addition**:
```sql
ALTER TABLE zammad_production.tickets
ADD COLUMN affected_ci_id UUID
REFERENCES triad_federation.cmdb_configuration_items(id);
```

**Benefit**: Click CI to see all tickets affecting that infrastructure component

---

### 6. Search/Filter Functionality

Add search bar and filters to Infrastructure page:
- Search by CI name, IP address, or description
- Filter by: Type, Status, Owner, Environment
- Dynamic filtering with AJAX (no page reload)

---

## Implementation Plan

### Phase 1: Basic CMDB View (1 week)
- [x] Database schema deployed
- [ ] Create `/infrastructure` route in SAG
- [ ] Build simple CI list view
- [ ] Add CI detail modal
- [ ] Test with existing 11 CIs

### Phase 2: Dependency Visualization (1 week)
- [ ] Integrate D3.js or vis.js
- [ ] Build dependency graph
- [ ] Make graph interactive
- [ ] Add zoom/pan controls

### Phase 3: Event/Ticket Integration (1 week)
- [ ] Add CI links to Event Dashboard
- [ ] Add affected_ci_id to Kanban tickets
- [ ] Build changes feed
- [ ] Test end-to-end workflow

### Phase 4: Auto-Discovery Hook (Future)
- [ ] When IT Jr 3 discovery runs, auto-update CMDB
- [ ] Write changes to cmdb_changes table
- [ ] Show discovery status in UI

---

## Technical Specifications

### Backend (Python Flask/FastAPI)

**New API endpoints**:
```python
# List all CIs
GET /api/cmdb/cis
  ?type=server&status=active&owner=it_triad

# Get CI details
GET /api/cmdb/cis/{ci_id}

# Get CI dependencies
GET /api/cmdb/cis/{ci_id}/dependencies

# Get recent changes
GET /api/cmdb/changes
  ?since=7d&ci_id={id}

# Search CIs
GET /api/cmdb/search?q={query}
```

### Frontend (JavaScript)

**Framework options**:
1. **Plain JS + jQuery** (if SAG uses this already)
2. **Vue.js** (lightweight, easy to embed)
3. **React** (if modernizing whole SAG)

**Recommended**: Match existing SAG tech stack

### Database Queries (Optimized)

Use indexes on ci_type, status, and relationship tables for fast queries.

---

## Success Criteria

✅ CMDB integrated into SAG navigation
✅ All 11 CIs visible in Infrastructure page
✅ Dependency graph shows service relationships
✅ CI detail view accessible via click
✅ Event Dashboard links to affected CIs
✅ Changes feed shows recent CMDB updates
✅ No performance degradation on SAG

---

## Next Steps

1. **Locate SAG codebase** on redfin (likely `/ganuda/sag-unified-interface/`)
2. **Review existing code structure** (Flask routes, templates)
3. **Create `/infrastructure` route** and template
4. **Build API endpoints** for CMDB queries
5. **Implement Column 1** (CI list) first
6. **Test with real data** (11 CIs already loaded)
7. **Iterate** on Columns 2 & 3

---

## Appendix: Color Scheme

**Consistent with SAG branding**:
- Servers: Blue (#4A90E2)
- Services: Green (#7ED321)
- Databases: Orange (#F5A623)
- Active status: Green checkmark ✅
- Planned status: Gray pause ⏸️
- Links: Cherokee red (#D0021B)

---

**Design Status**: ✅ COMPLETE - Ready for implementation
**Estimated Dev Time**: 3 weeks (Phases 1-3)
**Dependencies**: CMDB schema (complete), SAG codebase access
**Blockers**: None

---

*Designed by IT Jr 2, 2025-11-28*
*Cherokee AI Federation - Technological Sovereignty*

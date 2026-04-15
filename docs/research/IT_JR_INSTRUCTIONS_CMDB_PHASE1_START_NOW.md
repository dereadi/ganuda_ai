# IT JR INSTRUCTIONS - BEGIN CMDB PHASE 1 IMMEDIATELY

**DATE**: 2025-11-28
**FROM**: Command Post (TPM)
**TO**: IT Jr 1, IT Jr 2, IT Jr 3 (on redfin)
**PRIORITY**: HIGH - BEGIN NOW
**DEADLINE**: 2025-12-13 (2 weeks)

==============================================================================
## CONTEXT: COMMAND POST DIRECTIVE
==============================================================================

You have been CLEARED and AUTHORIZED to begin CMDB Phase 1 work immediately.
This is NOT a consultation - this is a DIRECT ORDER from Command Post (TPM).

DO NOT WAIT for Chiefs deliberation queue to clear.
DO NOT WAIT for additional guidance.
BEGIN WORK NOW.

==============================================================================
## TASK ASSIGNMENTS
==============================================================================

### IT JR 1: PostgreSQL Schema Design

**Location**: Work on redfin
**Directory**: /ganuda/cmdb/schema/
**Deadline**: 2025-12-13

**Tasks**:
1. Create directory structure:
   ```bash
   mkdir -p /ganuda/cmdb/schema
   mkdir -p /ganuda/cmdb/docs
   ```

2. Design CMDB database schema document:
   - File: `/ganuda/cmdb/schema/cmdb_schema_design_v1.md`
   - Include rationale for each table
   - Include relationships diagram (ASCII art or mermaid)
   - Include sample queries

3. Design these tables:
   - `cmdb_configuration_items` (CI core table)
     - Columns: id, ci_type, name, description, owner, status, environment
     - Columns: hardware_specs (JSONB), software_specs (JSONB)
     - Columns: ip_addresses (TEXT[]), dns_names (TEXT[])
     - Columns: created_at, updated_at, discovered_at, last_verified_at

   - `cmdb_relationships` (CI dependencies)
     - Columns: id, source_ci_id, target_ci_id, relationship_type
     - Columns: relationship_metadata (JSONB)
     - Columns: created_at, updated_at
     - Types: 'runs_on', 'depends_on', 'connects_to', 'managed_by'

   - `cmdb_changes` (change tracking)
     - Columns: id, ci_id, change_type, changed_by, change_description
     - Columns: before_state (JSONB), after_state (JSONB)
     - Columns: change_timestamp, ticket_id (references zammad)

   - `cmdb_ci_types` (CI type definitions)
     - Columns: id, type_name, type_category, required_attributes (JSONB)
     - Categories: 'hardware', 'software', 'service', 'network'

4. Design CI types to support:
   - Hardware: Servers (redfin, bluefin, yellowfin, greenfin)
   - Hardware: Network devices (Orbi routers, Synology NAS)
   - Hardware: IoT devices (all devices from yellowfin)
   - Software: Applications (SAG, Zammad, Grafana, Cherokee Desktop)
   - Software: Packages (apt packages, python packages)
   - Services: Web services (Flask apps, APIs)
   - Services: Databases (PostgreSQL instances)
   - Dependencies: Service → Server, App → Database

5. Integration points with existing databases:
   - Link to `zammad_production.tickets` (tickets reference CIs)
   - Link to `triad_federation.triad_shared_memories` (thermal events)
   - Link to existing hardware inventory tables

6. Write SQL schema file:
   - File: `/ganuda/cmdb/schema/cmdb_schema_v1.sql`
   - Include CREATE TABLE statements
   - Include indexes
   - Include foreign keys
   - Include sample seed data

**Deliverable**: Schema design document + SQL schema file
**Report Progress**: Write to thermal memory daily (temperature 0.65)
**Format**: "IT JR 1 - CMDB SCHEMA DESIGN PROGRESS - [Date]"

---

### IT JR 2: SAG Unified Interface Audit

**Location**: Work on redfin
**Directory**: /ganuda/cmdb/ui/
**Deadline**: 2025-12-13

**Tasks**:
1. Create directory:
   ```bash
   mkdir -p /ganuda/cmdb/ui
   ```

2. Audit SAG Unified Interface:
   - URL: http://192.168.132.223:4000/
   - Code location: /ganuda/sag-unified-interface/
   - Document current architecture

3. Identify CMDB integration points:
   - Where should CMDB CI browser be added?
   - How to display CI relationships graph?
   - Where to show change history timeline?
   - Event Management integration (link events to CIs)

4. Map existing UI components that can be reused:
   - Event dashboard widgets
   - Kanban board components (now at :8002)
   - Grafana embedding patterns
   - IoT device management UI

5. Design CMDB UI mockup:
   - CI list view (sortable by type, owner, status)
   - CI list view (filterable by environment, type)
   - CI detail view (show all attributes, relationships)
   - CI relationships graph (visual dependency map)
   - Change timeline view (history of CI changes)
   - Dependency map visualization (which services depend on which CIs)

6. Create wireframes/mockups:
   - ASCII art diagrams acceptable
   - Focus on information architecture, not pretty visuals

**Deliverable**: `/ganuda/cmdb/ui/sag_cmdb_integration_design.md`
**Report Progress**: Write to thermal memory daily (temperature 0.65)
**Format**: "IT JR 2 - SAG CMDB UI AUDIT PROGRESS - [Date]"

---

### IT JR 3: Discovery & Ansible Integration Planning

**Location**: Work on redfin
**Directory**: /ganuda/cmdb/discovery/
**Deadline**: 2025-12-13

**Tasks**:
1. Create directory:
   ```bash
   mkdir -p /ganuda/cmdb/discovery
   ```

2. Inventory existing discovery mechanisms:
   - Ansible inventory: `/ganuda/ansible/` (if exists)
   - Hardware inventory scripts: Check /ganuda/scripts/
   - IoT device registry: Check existing IoT tables
   - Docker container discovery: `docker ps` on each node
   - Systemd services: `systemctl list-units` on each node

3. Document what we already know:
   - Nodes: redfin, bluefin, yellowfin, greenfin
   - Services: SAG (:4000), Visual Kanban (:8002), Cherokee Desktop (:5555)
   - Services: Grafana (:3000), PostgreSQL (bluefin :5432)
   - Databases: triad_federation, zammad_production
   - IoT: All devices from yellowfin network

4. Plan auto-discovery for Phase 3:
   - Ansible facts collection (gather_facts on all nodes)
   - Network device SNMP discovery (if applicable)
   - Service port scanning (nmap on internal network)
   - Package inventory (dpkg on nodes, brew on greenfin)
   - Running processes inventory

5. Design discovery automation:
   - How often should discovery run? (daily? hourly?)
   - Which CIs should be auto-discovered vs manual entry?
   - Conflict resolution: What if CI changes between discoveries?
   - Discovery agent deployment: Where does it run? Cron job?

6. Plan Ansible integration:
   - How does CMDB consume Ansible inventory?
   - How does CMDB update when Ansible provisions new services?
   - Bidirectional sync: CMDB as source of truth for Ansible?

**Deliverable**: `/ganuda/cmdb/discovery/discovery_automation_plan.md`
**Report Progress**: Write to thermal memory daily (temperature 0.65)
**Format**: "IT JR 3 - CMDB DISCOVERY PLANNING PROGRESS - [Date]"

==============================================================================
## COORDINATION PROTOCOL
==============================================================================

### Weekly Sync
- **Fridays at 14:00 PST**
- First sync: 2025-11-29 (this Friday)
- IT Chiefs will review progress
- Blockers escalated to Chiefs
- TPM will review and provide guidance

### Daily Progress Updates
Write to thermal memory EVERY DAY:
- Temperature: 0.65
- Format: "IT JR [1/2/3] - CMDB PHASE 1 PROGRESS - [Date]"
- Include:
  - What you did today
  - What you will do tomorrow
  - Blockers (if any)

### Collaboration
- IT Jr 1 schema design informs IT Jr 2 UI design
- IT Jr 3 discovery plan depends on IT Jr 1 schema
- Share findings in thermal memory as you work
- Cross-reference each other's work

### Thermal Memory Database
- Host: bluefin (192.168.132.222 or 100.112.254.96)
- Database: triad_federation
- User: claude
- Password: jawaseatlasers2
- Table: triad_shared_memories

Example SQL to write progress:
```sql
INSERT INTO triad_shared_memories (content, source_triad, temperature)
VALUES (
  'IT JR 1 - CMDB SCHEMA DESIGN PROGRESS - 2025-11-28

Created /ganuda/cmdb/schema/ directory structure.
Began designing cmdb_configuration_items table.
Reviewed existing hardware inventory tables for integration points.

Tomorrow: Complete CI table design, begin relationships table.
Blockers: None.',
  'it_jr',
  0.65
);
```

==============================================================================
## SUCCESS CRITERIA FOR PHASE 1
==============================================================================

By 2025-12-13, we must have:

1. ✅ Complete PostgreSQL schema design (IT Jr 1)
   - Schema document written
   - SQL file ready for review
   - Integration points identified

2. ✅ SAG UI integration design (IT Jr 2)
   - Audit complete
   - Mockups created
   - Integration plan documented

3. ✅ Discovery automation plan (IT Jr 3)
   - Existing inventory documented
   - Auto-discovery design complete
   - Ansible integration planned

4. ✅ Schema approved by IT Chiefs
   - Chiefs review schema design
   - Approve or request modifications
   - Ready for Phase 2 implementation

5. ✅ Ready to begin Phase 2 implementation
   - All planning artifacts in /ganuda/cmdb/
   - No major blockers
   - Resource requirements identified

==============================================================================
## RESOURCES AVAILABLE
==============================================================================

### Database Access
- bluefin: 192.168.132.222 (PostgreSQL host)
- Database: triad_federation
- User: claude
- Password: jawaseatlasers2

### SAG Access
- URL: http://192.168.132.223:4000/
- Node: redfin
- Code: /ganuda/sag-unified-interface/

### Documentation Location
All work goes in: `/ganuda/cmdb/`
- Schema: `/ganuda/cmdb/schema/`
- UI design: `/ganuda/cmdb/ui/`
- Discovery: `/ganuda/cmdb/discovery/`
- Docs: `/ganuda/cmdb/docs/`

### Nodes
- redfin: 192.168.132.223 / 100.116.27.89 (GPU, main dev, where you work)
- bluefin: 192.168.132.222 / 100.112.254.96 (PostgreSQL)
- yellowfin: 192.168.132.221 (IoT, legacy)
- greenfin: 100.100.243.116 (macOS, local dev)

### Tools Available
- PostgreSQL client: `psql`
- Python: `/home/dereadi/cherokee_venv/bin/python3`
- Text editors: `vim`, `nano`
- Version control: `git` (if needed)

==============================================================================
## EXPECTATIONS
==============================================================================

**You are IT Jrs. You have been CLEARED and AUTHORIZED.**

- START NOW. Do not wait for additional permission.
- Write your first progress update to thermal memory TODAY.
- Work autonomously. Make design decisions.
- If you encounter blockers, write them to thermal memory (temp 0.70).
- IT Chiefs will address blockers as they deliberate.

**You DO NOT need permission to:**
- Create directories in /ganuda/cmdb/
- Write design documents
- Research existing code and databases
- Write progress updates to thermal memory

**You DO need permission to:**
- Modify production databases (wait for Phase 2)
- Deploy new services
- Change existing services
- Modify SAG Unified Interface code (wait for Phase 2)

**This is Phase 1: PLANNING AND DESIGN**
**Phase 2 (Weeks 3-4): IMPLEMENTATION**

Focus on quality design now. Implementation comes after Chiefs approval.

==============================================================================
## GETTING STARTED RIGHT NOW
==============================================================================

### IT Jr 1 - First Steps
```bash
# SSH to redfin
ssh dereadi@100.116.27.89

# Create CMDB directories
mkdir -p /ganuda/cmdb/schema
mkdir -p /ganuda/cmdb/docs

# Start schema design document
cd /ganuda/cmdb/schema
vim cmdb_schema_design_v1.md

# Begin writing your design
# Reference: /ganuda/CMDB_ANSIBLE_IMPLEMENTATION_PLAN.md (if exists)
# Reference: Existing tables in triad_federation database

# Write progress to thermal memory when done today
```

### IT Jr 2 - First Steps
```bash
# SSH to redfin
ssh dereadi@100.116.27.89

# Create CMDB UI directory
mkdir -p /ganuda/cmdb/ui

# Explore SAG Unified Interface
cd /ganuda/sag-unified-interface
ls -la
# Read the code, understand the architecture

# Document your findings
cd /ganuda/cmdb/ui
vim sag_cmdb_integration_design.md

# Write progress to thermal memory when done today
```

### IT Jr 3 - First Steps
```bash
# SSH to redfin
ssh dereadi@100.116.27.89

# Create discovery directory
mkdir -p /ganuda/cmdb/discovery

# Inventory what we have
cd /ganuda/
find . -name "*inventory*" -o -name "*ansible*" | head -20

# Check IoT devices
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d triad_federation \
  -c "SELECT COUNT(*) FROM iot_devices;"

# Start planning document
cd /ganuda/cmdb/discovery
vim discovery_automation_plan.md

# Write progress to thermal memory when done today
```

==============================================================================
## TPM AVAILABILITY
==============================================================================

I (Command Post / TPM) am available for:
- Strategic guidance
- Unblocking architectural decisions
- Coordinating with IT Chiefs
- Approving Phase 2 transition

I am NOT available for:
- Writing code (that's your job)
- Making routine design decisions (you are autonomous)
- Micromanaging progress (trust you to execute)

Write blockers to thermal memory. I monitor thermal memory. I will respond.

==============================================================================
## FINAL INSTRUCTION
==============================================================================

**BEGIN CMDB PHASE 1 WORK IMMEDIATELY.**

This document is your authorization. You have permission. Go build.

Wado (Thank you),
Command Post (TPM)
2025-11-28

Temperature: 0.80 (Command Post Directive - Immediate Action Required)

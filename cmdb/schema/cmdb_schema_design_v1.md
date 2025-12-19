# CMDB Schema Design v1.0

**Author**: IT Jr 1 (with Command Post kickstart)
**Date**: 2025-11-28
**Status**: DRAFT - In Progress

## Overview

PostgreSQL-based CMDB for Cherokee AI Federation infrastructure tracking.

## Core Tables

### 1. cmdb_configuration_items

Primary table for all Configuration Items (CIs).

```sql
CREATE TABLE cmdb_configuration_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ci_type VARCHAR(50) NOT NULL,  -- 'hardware', 'software', 'service', 'network'
    ci_name VARCHAR(255) NOT NULL UNIQUE,
    ci_description TEXT,
    owner VARCHAR(100),  -- Which Triad owns this CI
    status VARCHAR(50) DEFAULT 'active',  -- 'active', 'maintenance', 'retired'
    environment VARCHAR(50),  -- 'production', 'development', 'test'
    
    -- Hardware-specific (JSONB for flexibility)
    hardware_specs JSONB,
    -- {
    --   "cpu": "AMD Ryzen",
    --   "ram": "32GB",
    --   "gpu": "NVIDIA RTX 4090"
    -- }
    
    -- Software-specific
    software_specs JSONB,
    -- {
    --   "version": "17.6",
    --   "vendor": "PostgreSQL",
    --   "license": "open-source"
    -- }
    
    -- Network info
    ip_addresses TEXT[],
    dns_names TEXT[],
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    discovered_at TIMESTAMP,
    last_verified_at TIMESTAMP
);

CREATE INDEX idx_ci_type ON cmdb_configuration_items(ci_type);
CREATE INDEX idx_ci_status ON cmdb_configuration_items(status);
CREATE INDEX idx_ci_owner ON cmdb_configuration_items(owner);
```

### 2. cmdb_relationships

Tracks dependencies between CIs.

```sql
CREATE TABLE cmdb_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_ci_id UUID NOT NULL REFERENCES cmdb_configuration_items(id),
    target_ci_id UUID NOT NULL REFERENCES cmdb_configuration_items(id),
    relationship_type VARCHAR(50) NOT NULL,
    -- Types: 'runs_on', 'depends_on', 'connects_to', 'managed_by'
    
    relationship_metadata JSONB,
    -- Store additional context about the relationship
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(source_ci_id, target_ci_id, relationship_type)
);

CREATE INDEX idx_rel_source ON cmdb_relationships(source_ci_id);
CREATE INDEX idx_rel_target ON cmdb_relationships(target_ci_id);
CREATE INDEX idx_rel_type ON cmdb_relationships(relationship_type);
```

### 3. cmdb_changes

Change tracking for all CI modifications.

```sql
CREATE TABLE cmdb_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ci_id UUID NOT NULL REFERENCES cmdb_configuration_items(id),
    change_type VARCHAR(50) NOT NULL,  -- 'create', 'update', 'delete', 'config_change'
    changed_by VARCHAR(100) NOT NULL,  -- User or Jr that made the change
    change_description TEXT,
    
    before_state JSONB,  -- CI state before change
    after_state JSONB,   -- CI state after change
    
    change_timestamp TIMESTAMP DEFAULT NOW(),
    ticket_id VARCHAR(50),  -- Link to Zammad ticket if applicable
    
    approved_by VARCHAR(100),
    approval_timestamp TIMESTAMP
);

CREATE INDEX idx_change_ci ON cmdb_changes(ci_id);
CREATE INDEX idx_change_timestamp ON cmdb_changes(change_timestamp);
CREATE INDEX idx_change_type ON cmdb_changes(change_type);
```

### 4. cmdb_ci_types

Define valid CI types and their required attributes.

```sql
CREATE TABLE cmdb_ci_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_name VARCHAR(50) NOT NULL UNIQUE,
    type_category VARCHAR(50),  -- 'hardware', 'software', 'service', 'network'
    required_attributes JSONB,
    -- Define what fields are mandatory for this CI type
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Seed data
INSERT INTO cmdb_ci_types (type_name, type_category, required_attributes) VALUES
('server', 'hardware', '{"cpu": true, "ram": true, "ip_addresses": true}'),
('database', 'software', '{"version": true, "vendor": true}'),
('web_service', 'service', '{"port": true, "url": true}'),
('network_device', 'network', '{"ip_addresses": true, "device_type": true}');
```

## Integration Points

### Zammad Integration
- Link cmdb_configuration_items.id to zammad_production.tickets
- New column: `affected_ci_id UUID REFERENCES cmdb_configuration_items(id)`

### Thermal Memory Integration  
- Write CMDB events to triad_shared_memories
- Temperature 0.60 for routine CI updates
- Temperature 0.75 for critical infrastructure changes

## Sample Queries

### Find all services running on redfin
```sql
SELECT 
    svc.ci_name AS service_name,
    srv.ci_name AS server_name
FROM cmdb_configuration_items svc
JOIN cmdb_relationships r ON svc.id = r.source_ci_id
JOIN cmdb_configuration_items srv ON r.target_ci_id = srv.id
WHERE srv.ci_name = 'redfin' 
  AND r.relationship_type = 'runs_on';
```

### Track CI change history
```sql
SELECT 
    ci.ci_name,
    c.change_type,
    c.changed_by,
    c.change_timestamp,
    c.change_description
FROM cmdb_changes c
JOIN cmdb_configuration_items ci ON c.ci_id = ci.id
WHERE ci.ci_name = 'bluefin'
ORDER BY c.change_timestamp DESC
LIMIT 10;
```

## Next Steps

- [ ] Review with IT Chiefs
- [ ] Add more CI types (IoT devices, virtual machines)
- [ ] Design discovery automation integration
- [ ] Create API endpoints for SAG interface

**Progress**: Initial schema drafted, needs refinement
**Blockers**: None
**Next Update**: 2025-11-29


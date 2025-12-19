-- CMDB Schema v1.0
-- Configuration Management Database for Cherokee AI Federation
-- Created by IT Jr Agent - Phase 1
-- Date: 2025-11-29

-- ============================================================================
-- CI Types Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS cmdb_ci_types (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type_name VARCHAR(100) NOT NULL UNIQUE,
    category VARCHAR(50) NOT NULL,
    description TEXT,
    icon VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ci_types_category ON cmdb_ci_types(category);

-- Insert standard CI types
INSERT INTO cmdb_ci_types (type_name, category, description) VALUES
('Server', 'Hardware', 'Physical or virtual server'),
('Network Device', 'Hardware', 'Router, switch, firewall'),
('IoT Device', 'Hardware', 'IoT sensors, smart devices'),
('Application', 'Software', 'Software application or service'),
('Database', 'Software', 'Database system'),
('Web Service', 'Service', 'Web API or service'),
('Container', 'Software', 'Docker container'),
('Virtual Machine', 'Hardware', 'VM instance')
ON CONFLICT (type_name) DO NOTHING;

-- ============================================================================
-- Configuration Items (Core CI Table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cmdb_configuration_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ci_name VARCHAR(200) NOT NULL,
    ci_type_id UUID REFERENCES cmdb_ci_types(id),
    hostname VARCHAR(200),
    ip_address INET,
    mac_address MACADDR,
    location VARCHAR(200),
    status VARCHAR(50) DEFAULT 'active',
    environment VARCHAR(50),
    owner VARCHAR(100),
    cost_center VARCHAR(100),
    firmware_version VARCHAR(100),
    software_version VARCHAR(100),
    managed_by VARCHAR(100),
    discovery_method VARCHAR(100),
    last_discovered TIMESTAMPTZ,
    custom_attributes JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_ci_name ON cmdb_configuration_items(ci_name);
CREATE INDEX idx_ci_type ON cmdb_configuration_items(ci_type_id);
CREATE INDEX idx_ci_hostname ON cmdb_configuration_items(hostname);
CREATE INDEX idx_ci_ip ON cmdb_configuration_items(ip_address);
CREATE INDEX idx_ci_status ON cmdb_configuration_items(status);

-- ============================================================================
-- CI Relationships (Dependencies)
-- ============================================================================
CREATE TABLE IF NOT EXISTS cmdb_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    parent_ci_id UUID REFERENCES cmdb_configuration_items(id) ON DELETE CASCADE,
    child_ci_id UUID REFERENCES cmdb_configuration_items(id) ON DELETE CASCADE,
    relationship_type VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(parent_ci_id, child_ci_id, relationship_type)
);

CREATE INDEX idx_relationship_parent ON cmdb_relationships(parent_ci_id);
CREATE INDEX idx_relationship_child ON cmdb_relationships(child_ci_id);
CREATE INDEX idx_relationship_type ON cmdb_relationships(relationship_type);

-- ============================================================================
-- Change Tracking
-- ============================================================================
CREATE TABLE IF NOT EXISTS cmdb_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ci_id UUID REFERENCES cmdb_configuration_items(id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL,
    field_name VARCHAR(100),
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100),
    change_reason TEXT,
    zammad_ticket_id INTEGER,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_changes_ci ON cmdb_changes(ci_id);
CREATE INDEX idx_changes_type ON cmdb_changes(change_type);
CREATE INDEX idx_changes_created ON cmdb_changes(created_at DESC);

-- ============================================================================
-- Service Dependencies
-- ============================================================================
CREATE TABLE IF NOT EXISTS cmdb_service_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    service_ci_id UUID REFERENCES cmdb_configuration_items(id),
    depends_on_ci_id UUID REFERENCES cmdb_configuration_items(id),
    dependency_type VARCHAR(100),
    criticality VARCHAR(50),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_service_deps_service ON cmdb_service_dependencies(service_ci_id);
CREATE INDEX idx_service_deps_depends ON cmdb_service_dependencies(depends_on_ci_id);

-- ============================================================================
-- Comments
-- ============================================================================
COMMENT ON TABLE cmdb_configuration_items IS 'Core CMDB table storing all configuration items';
COMMENT ON TABLE cmdb_relationships IS 'CI dependencies and relationships';
COMMENT ON TABLE cmdb_changes IS 'Audit trail for CI changes';
COMMENT ON TABLE cmdb_service_dependencies IS 'Service-level dependency mapping';

-- End of schema

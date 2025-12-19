-- Spatial Awareness Schema for Cherokee Federation
-- Council Vote: SpatialOS PROCEED 84%, Review PROCEED 82.5%
-- Security: Crawdad approved with access controls
-- For Seven Generations

-- Location zones within the property
CREATE TABLE IF NOT EXISTS spatial_zones (
    zone_id SERIAL PRIMARY KEY,
    zone_name VARCHAR(100) NOT NULL UNIQUE,
    zone_type VARCHAR(50) DEFAULT 'room',  -- room, rack, entry, utility, outdoor
    parent_zone_id INTEGER REFERENCES spatial_zones(zone_id),

    -- Relative positioning (DO NOT expose raw GPS in APIs)
    base_latitude DECIMAL(10, 6) DEFAULT 36.3529,
    base_longitude DECIMAL(10, 6) DEFAULT -94.2194,
    relative_x DECIMAL(10, 2) DEFAULT 0,  -- meters from office (base point)
    relative_y DECIMAL(10, 2) DEFAULT 0,  -- positive = north, negative = south
    relative_z DECIMAL(10, 2) DEFAULT 0,  -- floor level (0 = ground)

    -- Metadata
    description TEXT,
    has_voice_assistant BOOLEAN DEFAULT false,
    has_security_device BOOLEAN DEFAULT false,
    has_climate_control BOOLEAN DEFAULT false,
    privacy_sensitive BOOLEAN DEFAULT false,  -- bathrooms, bedrooms

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Seed initial zones with directional relationships
INSERT INTO spatial_zones (zone_name, zone_type, relative_x, relative_y, description, has_voice_assistant, has_security_device, privacy_sensitive) VALUES
    ('office', 'room', 0, 0, 'Primary compute location - 5 immobile nodes, half rack, Dell router', false, false, false),
    ('office_rack', 'rack', 0, 0, 'Half rack with redfin, bluefin, greenfin', false, false, false),
    ('living_room', 'room', -5, -3, 'Orbi base router, Sonos, Fire Show 5 (Alexa)', true, false, false),
    ('kitchen', 'room', 0, -5, 'Sonos, Google Nest Hub 5-inch', true, false, false),
    ('master_bedroom', 'room', -8, -5, 'tpm-macbook (mobile), Sonos, Fire Show 5 (Alexa)', true, false, true),
    ('master_bath', 'room', -10, -5, 'Sonos speaker', false, false, true),
    ('spare_bedroom', 'room', 5, 0, 'East of office, Orbi mesh satellite', false, false, true),
    ('garage', 'utility', 0, 8, 'North of office - empty rack, mobile AC, network equipment, miner', false, false, false),
    ('garage_rack', 'rack', 0, 8, 'Empty rack - future expansion with mobile AC cooling', false, false, false),
    ('hallway', 'room', -2, -2, 'Nest thermostat - central location', false, false, false),
    ('front_door', 'entry', -3, -8, 'Ring doorbell, Nest camera - main entrance', false, true, false),
    ('back_door', 'entry', 3, 5, 'Nest camera - rear entrance', false, true, false)
ON CONFLICT (zone_name) DO UPDATE SET
    relative_x = EXCLUDED.relative_x,
    relative_y = EXCLUDED.relative_y,
    description = EXCLUDED.description,
    has_voice_assistant = EXCLUDED.has_voice_assistant,
    has_security_device = EXCLUDED.has_security_device,
    privacy_sensitive = EXCLUDED.privacy_sensitive;

-- Update climate control flag for hallway (thermostat location)
UPDATE spatial_zones SET has_climate_control = true WHERE zone_name = 'hallway';

-- Set parent relationships (racks inside rooms)
UPDATE spatial_zones SET parent_zone_id = (SELECT zone_id FROM spatial_zones WHERE zone_name = 'office')
WHERE zone_name = 'office_rack';

UPDATE spatial_zones SET parent_zone_id = (SELECT zone_id FROM spatial_zones WHERE zone_name = 'garage')
WHERE zone_name = 'garage_rack';

-- Spatial relationships (which zones are adjacent)
CREATE TABLE IF NOT EXISTS spatial_adjacency (
    id SERIAL PRIMARY KEY,
    zone_a_id INTEGER REFERENCES spatial_zones(zone_id),
    zone_b_id INTEGER REFERENCES spatial_zones(zone_id),
    distance_meters DECIMAL(10, 2),
    path_type VARCHAR(50) DEFAULT 'direct',  -- direct, hallway, door
    UNIQUE(zone_a_id, zone_b_id)
);

-- Enhanced IoT device columns
ALTER TABLE iot_devices
    ADD COLUMN IF NOT EXISTS zone_id INTEGER REFERENCES spatial_zones(zone_id),
    ADD COLUMN IF NOT EXISTS device_category VARCHAR(50),  -- audio, security, climate, voice_assistant, network, compute
    ADD COLUMN IF NOT EXISTS position_in_zone VARCHAR(100),
    ADD COLUMN IF NOT EXISTS ecosystem VARCHAR(50),  -- amazon, google, sonos, apple, network, other
    ADD COLUMN IF NOT EXISTS protocol VARCHAR(50),  -- wifi, ethernet, zigbee, zwave, thread, mesh
    ADD COLUMN IF NOT EXISTS has_microphone BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS has_camera BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS online_status BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW(),
    ADD COLUMN IF NOT EXISTS current_state JSONB DEFAULT '{}',  -- device-specific real-time data
    ADD COLUMN IF NOT EXISTS discovery_method VARCHAR(50) DEFAULT 'manual',  -- manual, nmap, api, mdns
    ADD COLUMN IF NOT EXISTS mac_address VARCHAR(17);  -- for network correlation

-- Enhanced hardware inventory columns
ALTER TABLE hardware_inventory
    ADD COLUMN IF NOT EXISTS zone_id INTEGER REFERENCES spatial_zones(zone_id),
    ADD COLUMN IF NOT EXISTS position_in_zone VARCHAR(100),
    ADD COLUMN IF NOT EXISTS is_mobile BOOLEAN DEFAULT false,
    ADD COLUMN IF NOT EXISTS last_known_zone_id INTEGER REFERENCES spatial_zones(zone_id),
    ADD COLUMN IF NOT EXISTS online_status BOOLEAN DEFAULT true,
    ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT NOW();

-- Indexes for spatial and real-time queries
CREATE INDEX IF NOT EXISTS idx_hardware_zone ON hardware_inventory(zone_id);
CREATE INDEX IF NOT EXISTS idx_iot_zone ON iot_devices(zone_id);
CREATE INDEX IF NOT EXISTS idx_iot_ecosystem ON iot_devices(ecosystem);
CREATE INDEX IF NOT EXISTS idx_iot_online ON iot_devices(online_status);
CREATE INDEX IF NOT EXISTS idx_iot_last_seen ON iot_devices(last_seen);

-- Spatial query audit log (security requirement)
CREATE TABLE IF NOT EXISTS spatial_audit_log (
    id SERIAL PRIMARY KEY,
    query_type VARCHAR(50),  -- zone_list, zone_detail, device_locate
    api_key_id VARCHAR(64),
    query_params JSONB,
    result_count INTEGER,
    queried_at TIMESTAMP DEFAULT NOW(),
    client_ip VARCHAR(45)
);

CREATE INDEX IF NOT EXISTS idx_spatial_audit_time ON spatial_audit_log(queried_at DESC);
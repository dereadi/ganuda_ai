# Jr Instructions: Spatial Awareness for CMDB

**Priority**: 2 (Enhancement)
**Assigned Jr**: Infrastructure Jr.
**Target**: bluefin (zammad_production database)
**Council Vote**: SpatialOS PROCEED 84% confidence
**Council Review**: PROCEED 82.5% - with security and real-time enhancements

---

## Overview

Add physical location awareness to Cherokee Federation CMDB. This enables spatial queries, environmental correlation, real-time device state tracking, and future 3D visualization.

**Base Coordinates** (Flying Squirrel's Office):
- Latitude: 36.3529
- Longitude: -94.2194
- City: Bentonville, Arkansas
- Organization: AT&T Internet
- Public IP: 162.233.86.232

**SECURITY NOTE (Crawdad)**: GPS coordinates and physical layout are sensitive. Do NOT expose raw coordinates in public APIs. Use relative positions internally. Require authentication for all spatial endpoints.

---

## ARCHITECTURE OVERVIEW

### Three Ecosystems in Play

| Ecosystem | Devices | Voice Assistant | Integration Priority |
|-----------|---------|-----------------|---------------------|
| **Amazon** | Ring Doorbell, Fire Show 5 (x2) | Alexa | Medium (unofficial APIs) |
| **Google** | Nest Thermostat, Nest Cameras (x2), Nest Hub | Google Assistant | Medium (requires OAuth) |
| **Sonos** | 5 speakers | None (controlled by both) | High (good local API) |
| **Network** | Dell Router, Orbi mesh (3 units), dumb switch | N/A | High (nmap discovery) |

### Physical Layout (Relative to Office)

```
                         NORTH
                           │
                   ┌───────┴───────┐
                   │    GARAGE     │
                   │  Empty rack   │
                   │  Mobile AC    │
                   │  Orbi mesh    │
                   │  Dumb switch  │
                   │  Crypto miner │
                   └───────────────┘
                           │
     ┌─────────────────────┼─────────────────────┐
     │                     │                     │
 WEST│         ┌───────────┴───────────┐         │EAST
     │         │       OFFICE          │         │
     │         │  Half rack:           │         │
     │         │   • redfin (GPU)      │         │
     │         │   • bluefin (DB)      │◄────────┼────► SPARE BEDROOM
     │         │   • greenfin          │         │      Orbi mesh
     │         │  Desk:                │         │
     │         │   • sasass            │         │
     │         │   • sasass2           │         │
     │         │  Dell router (top)    │         │
     │         │  Sonos                │         │
     │         └───────────────────────┘         │
     │                                           │
     └───────────────────────────────────────────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       LIVING ROOM     HALLWAY      KITCHEN
       • Orbi base     • Nest       • Sonos
       • Sonos           thermo     • Nest Hub
       • Fire Show 5
              │
              ├── MASTER BEDROOM ── MASTER BATH
              │   • tpm-macbook     • Sonos
              │   • Sonos
              │   • Fire Show 5
              │
              ├── FRONT DOOR
              │   • Ring Doorbell
              │   • Nest Camera
              │
              └── BACK DOOR
                  • Nest Camera
```

---

### Task 1: Create Enhanced Spatial Schema

Create `/ganuda/sql/spatial_schema.sql`:

```sql
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
```

---

### Task 2: Populate Node Locations

Create `/ganuda/sql/spatial_seed_nodes.sql`:

```sql
-- Seed node locations
-- All 5 immobile nodes are in the office

DO $$
DECLARE
    office_zone INTEGER;
    bedroom_zone INTEGER;
BEGIN
    SELECT zone_id INTO office_zone FROM spatial_zones WHERE zone_name = 'office';
    SELECT zone_id INTO bedroom_zone FROM spatial_zones WHERE zone_name = 'master_bedroom';

    -- Update hardware_inventory with spatial data
    UPDATE hardware_inventory SET
        zone_id = office_zone,
        position_in_zone = 'half rack - GPU inference node',
        is_mobile = false,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'redfin';

    UPDATE hardware_inventory SET
        zone_id = office_zone,
        position_in_zone = 'half rack - database node',
        is_mobile = false,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'bluefin';

    UPDATE hardware_inventory SET
        zone_id = office_zone,
        position_in_zone = 'half rack - daemon node',
        is_mobile = false,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'greenfin';

    UPDATE hardware_inventory SET
        zone_id = office_zone,
        position_in_zone = 'desk - Mac Studio 1',
        is_mobile = false,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'sasass';

    UPDATE hardware_inventory SET
        zone_id = office_zone,
        position_in_zone = 'desk - Mac Studio 2',
        is_mobile = false,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'sasass2';

    UPDATE hardware_inventory SET
        zone_id = bedroom_zone,
        position_in_zone = 'mobile - current location',
        is_mobile = true,
        last_known_zone_id = bedroom_zone,
        online_status = true,
        last_seen = NOW()
    WHERE hostname = 'tpm-macbook';

    RAISE NOTICE 'Spatial data seeded for 6 federation nodes';
END $$;
```

---

### Task 3: Populate IoT Devices with Ecosystem Data

Create `/ganuda/sql/spatial_seed_iot.sql`:

```sql
-- Clear and reseed IoT devices with full ecosystem data
-- This ensures consistent data model

DO $$
DECLARE
    office_zone INTEGER;
    living_zone INTEGER;
    kitchen_zone INTEGER;
    bedroom_zone INTEGER;
    bath_zone INTEGER;
    spare_zone INTEGER;
    garage_zone INTEGER;
    hallway_zone INTEGER;
    front_door_zone INTEGER;
    back_door_zone INTEGER;
BEGIN
    -- Get all zone IDs
    SELECT zone_id INTO office_zone FROM spatial_zones WHERE zone_name = 'office';
    SELECT zone_id INTO living_zone FROM spatial_zones WHERE zone_name = 'living_room';
    SELECT zone_id INTO kitchen_zone FROM spatial_zones WHERE zone_name = 'kitchen';
    SELECT zone_id INTO bedroom_zone FROM spatial_zones WHERE zone_name = 'master_bedroom';
    SELECT zone_id INTO bath_zone FROM spatial_zones WHERE zone_name = 'master_bath';
    SELECT zone_id INTO spare_zone FROM spatial_zones WHERE zone_name = 'spare_bedroom';
    SELECT zone_id INTO garage_zone FROM spatial_zones WHERE zone_name = 'garage';
    SELECT zone_id INTO hallway_zone FROM spatial_zones WHERE zone_name = 'hallway';
    SELECT zone_id INTO front_door_zone FROM spatial_zones WHERE zone_name = 'front_door';
    SELECT zone_id INTO back_door_zone FROM spatial_zones WHERE zone_name = 'back_door';

    -- =====================
    -- SONOS ECOSYSTEM (5 devices)
    -- Protocol: WiFi, Good local API
    -- =====================
    INSERT INTO iot_devices (device_name, device_type, zone_id, device_category, position_in_zone,
                             ecosystem, protocol, has_microphone, has_camera, discovery_method)
    VALUES
        ('Sonos Office', 'speaker', office_zone, 'audio', 'bookshelf', 'sonos', 'wifi', true, false, 'manual'),
        ('Sonos Living Room', 'speaker', living_zone, 'audio', 'entertainment center', 'sonos', 'wifi', true, false, 'manual'),
        ('Sonos Kitchen', 'speaker', kitchen_zone, 'audio', 'counter', 'sonos', 'wifi', true, false, 'manual'),
        ('Sonos Master Bedroom', 'speaker', bedroom_zone, 'audio', 'nightstand', 'sonos', 'wifi', true, false, 'manual'),
        ('Sonos Master Bath', 'speaker', bath_zone, 'audio', 'vanity', 'sonos', 'wifi', true, false, 'manual')
    ON CONFLICT DO NOTHING;

    -- =====================
    -- GOOGLE/NEST ECOSYSTEM (4 devices)
    -- Protocol: WiFi, Requires Google Cloud OAuth
    -- =====================
    INSERT INTO iot_devices (device_name, device_type, zone_id, device_category, position_in_zone,
                             ecosystem, protocol, has_microphone, has_camera, discovery_method)
    VALUES
        ('Nest Thermostat', 'thermostat', hallway_zone, 'climate', 'wall mounted - central',
         'google', 'wifi', false, false, 'manual'),
        ('Nest Camera - Front Door', 'camera', front_door_zone, 'security', 'exterior - main entrance',
         'google', 'wifi', true, true, 'manual'),
        ('Nest Camera - Back Door', 'camera', back_door_zone, 'security', 'exterior - rear',
         'google', 'wifi', true, true, 'manual'),
        ('Google Nest Hub', 'smart_display', kitchen_zone, 'voice_assistant', 'counter - 5-inch display',
         'google', 'wifi', true, true, 'manual')
    ON CONFLICT DO NOTHING;

    -- =====================
    -- AMAZON ECOSYSTEM (3 devices)
    -- Protocol: WiFi, Unofficial APIs
    -- =====================
    INSERT INTO iot_devices (device_name, device_type, zone_id, device_category, position_in_zone,
                             ecosystem, protocol, has_microphone, has_camera, discovery_method)
    VALUES
        ('Ring Doorbell', 'doorbell', front_door_zone, 'security', 'front entrance',
         'amazon', 'wifi', true, true, 'manual'),
        ('Fire Show 5 - Living Room', 'smart_display', living_zone, 'voice_assistant', 'entertainment center - Alexa',
         'amazon', 'wifi', true, true, 'manual'),
        ('Fire Show 5 - Bedroom', 'smart_display', bedroom_zone, 'voice_assistant', 'nightstand - Alexa',
         'amazon', 'wifi', true, true, 'manual')
    ON CONFLICT DO NOTHING;

    -- =====================
    -- NETWORK INFRASTRUCTURE (6 devices)
    -- =====================
    INSERT INTO iot_devices (device_name, device_type, zone_id, device_category, position_in_zone,
                             ecosystem, protocol, has_microphone, has_camera, discovery_method)
    VALUES
        ('Dell Router', 'router', office_zone, 'network', 'top of half rack - gateway',
         'network', 'ethernet', false, false, 'manual'),
        ('Orbi Router (Base)', 'router', living_zone, 'network', 'mesh controller',
         'network', 'mesh', false, false, 'manual'),
        ('Orbi Mesh - Spare Bedroom', 'mesh_node', spare_zone, 'network', 'east of office',
         'network', 'mesh', false, false, 'manual'),
        ('Orbi Mesh - Garage', 'mesh_node', garage_zone, 'network', 'north of office',
         'network', 'mesh', false, false, 'manual'),
        ('Garage Dumb Switch', 'switch', garage_zone, 'network', 'connected to Orbi mesh',
         'network', 'ethernet', false, false, 'manual'),
        ('Crypto Miner', 'miner', garage_zone, 'compute', 'connected to dumb switch',
         'other', 'ethernet', false, false, 'manual')
    ON CONFLICT DO NOTHING;

    -- =====================
    -- HVAC/COOLING (1 device)
    -- =====================
    INSERT INTO iot_devices (device_name, device_type, zone_id, device_category, position_in_zone,
                             ecosystem, protocol, has_microphone, has_camera, discovery_method)
    VALUES
        ('Mobile AC Unit', 'portable_ac', garage_zone, 'climate', 'future rack cooling',
         'other', 'none', false, false, 'manual')
    ON CONFLICT DO NOTHING;

    RAISE NOTICE 'IoT devices seeded: 5 Sonos, 4 Google/Nest, 3 Amazon, 6 Network, 1 HVAC';
END $$;

-- Set initial state for thermostat
UPDATE iot_devices
SET current_state = '{"mode": "auto", "target_temp_f": 72, "current_temp_f": null, "humidity_pct": null}'
WHERE device_name = 'Nest Thermostat';

-- Set initial state for security devices
UPDATE iot_devices
SET current_state = '{"armed": false, "last_motion": null, "recording": true}'
WHERE device_category = 'security';
```

---

### Task 4: Create Enhanced Spatial Query Functions

Create `/ganuda/sql/spatial_functions.sql`:

```sql
-- Function: Get all devices in a zone with real-time status
CREATE OR REPLACE FUNCTION get_devices_in_zone(p_zone_name VARCHAR)
RETURNS TABLE (
    device_type VARCHAR,
    device_name VARCHAR,
    ip_address VARCHAR,
    position VARCHAR,
    ecosystem VARCHAR,
    online BOOLEAN,
    last_seen TIMESTAMP
) AS $$
BEGIN
    RETURN QUERY
    -- Hardware (compute nodes)
    SELECT 'node'::VARCHAR, h.hostname::VARCHAR, h.ip_address::VARCHAR,
           h.position_in_zone::VARCHAR, 'federation'::VARCHAR,
           h.online_status, h.last_seen
    FROM hardware_inventory h
    JOIN spatial_zones z ON h.zone_id = z.zone_id
    WHERE z.zone_name = p_zone_name
    UNION ALL
    -- IoT devices
    SELECT 'iot'::VARCHAR, i.device_name::VARCHAR, i.ip_address::VARCHAR,
           i.position_in_zone::VARCHAR, i.ecosystem::VARCHAR,
           i.online_status, i.last_seen
    FROM iot_devices i
    JOIN spatial_zones z ON i.zone_id = z.zone_id
    WHERE z.zone_name = p_zone_name
    ORDER BY device_type, device_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Get zone for a device
CREATE OR REPLACE FUNCTION get_device_zone(p_device_name VARCHAR)
RETURNS TABLE (
    zone_name VARCHAR,
    zone_type VARCHAR,
    position VARCHAR,
    is_mobile BOOLEAN
) AS $$
BEGIN
    -- Check hardware first
    RETURN QUERY
    SELECT z.zone_name, z.zone_type, h.position_in_zone, h.is_mobile
    FROM hardware_inventory h
    JOIN spatial_zones z ON h.zone_id = z.zone_id
    WHERE h.hostname ILIKE '%' || p_device_name || '%';

    IF NOT FOUND THEN
        -- Check IoT devices
        RETURN QUERY
        SELECT z.zone_name, z.zone_type, i.position_in_zone, false
        FROM iot_devices i
        JOIN spatial_zones z ON i.zone_id = z.zone_id
        WHERE i.device_name ILIKE '%' || p_device_name || '%';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Function: Environmental context for a zone (NO RAW GPS - security requirement)
CREATE OR REPLACE FUNCTION get_zone_context(p_zone_name VARCHAR)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'zone', p_zone_name,
        'type', z.zone_type,
        'relative_position', jsonb_build_object(
            'x_meters', z.relative_x,
            'y_meters', z.relative_y,
            'floor', z.relative_z
        ),
        'capabilities', jsonb_build_object(
            'voice_assistant', z.has_voice_assistant,
            'security', z.has_security_device,
            'climate', z.has_climate_control
        ),
        'privacy_sensitive', z.privacy_sensitive,
        'node_count', (SELECT COUNT(*) FROM hardware_inventory h WHERE h.zone_id = z.zone_id),
        'iot_count', (SELECT COUNT(*) FROM iot_devices i WHERE i.zone_id = z.zone_id),
        'ecosystems', (SELECT ARRAY_AGG(DISTINCT i.ecosystem) FROM iot_devices i WHERE i.zone_id = z.zone_id),
        'description', z.description
    ) INTO result
    FROM spatial_zones z
    WHERE z.zone_name = p_zone_name;

    RETURN result;
END;
$$ LANGUAGE plpgsql;

-- Function: Get all voice-enabled zones (for audio routing)
CREATE OR REPLACE FUNCTION get_voice_zones()
RETURNS TABLE (
    zone_name VARCHAR,
    voice_devices JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT z.zone_name,
           jsonb_agg(jsonb_build_object(
               'device', i.device_name,
               'ecosystem', i.ecosystem,
               'type', i.device_type
           ))
    FROM spatial_zones z
    JOIN iot_devices i ON i.zone_id = z.zone_id
    WHERE i.device_category IN ('audio', 'voice_assistant')
       OR i.has_microphone = true
    GROUP BY z.zone_name
    ORDER BY z.zone_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Get security perimeter status
CREATE OR REPLACE FUNCTION get_security_perimeter()
RETURNS TABLE (
    zone_name VARCHAR,
    device_name VARCHAR,
    device_type VARCHAR,
    online BOOLEAN,
    current_state JSONB
) AS $$
BEGIN
    RETURN QUERY
    SELECT z.zone_name, i.device_name, i.device_type,
           i.online_status, i.current_state
    FROM iot_devices i
    JOIN spatial_zones z ON i.zone_id = z.zone_id
    WHERE i.device_category = 'security'
    ORDER BY z.zone_name;
END;
$$ LANGUAGE plpgsql;

-- Function: Correlate compute thermal with room temperature
-- Connects OpenView-Resonance with Nest thermostat
CREATE OR REPLACE FUNCTION get_environmental_correlation(p_zone_name VARCHAR DEFAULT 'office')
RETURNS JSONB AS $$
DECLARE
    thermostat_state JSONB;
    compute_health JSONB;
    result JSONB;
BEGIN
    -- Get thermostat reading (if available)
    SELECT current_state INTO thermostat_state
    FROM iot_devices
    WHERE device_name = 'Nest Thermostat';

    -- Get latest resonance pattern with environmental awareness for nodes in zone
    SELECT jsonb_build_object(
        'zone', p_zone_name,
        'nodes_in_zone', (
            SELECT jsonb_agg(h.hostname)
            FROM hardware_inventory h
            JOIN spatial_zones z ON h.zone_id = z.zone_id
            WHERE z.zone_name = p_zone_name
        ),
        'thermostat', thermostat_state,
        'correlation_note', 'High CPU + high room temp = check cooling'
    ) INTO result;

    RETURN result;
END;
$$ LANGUAGE plpgsql;
```

---

### Task 5: Device Discovery Daemon

Create `/ganuda/services/spatial_discovery/discovery.py`:

```python
#!/usr/bin/env python3
"""
Spatial Discovery Daemon
Scans network for device presence and updates online_status/last_seen
Council approved - requires nmap installed on host

Run from redfin: python3 /ganuda/services/spatial_discovery/discovery.py
"""

import subprocess
import json
import time
import psycopg2
from datetime import datetime
import re
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'zammad_production',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}

NETWORK_RANGE = '192.168.132.0/24'
SCAN_INTERVAL = 300  # 5 minutes

def get_db_connection():
    return psycopg2.connect(**DB_CONFIG)

def scan_network():
    """Run nmap ping scan to find online hosts"""
    try:
        result = subprocess.run(
            ['nmap', '-sn', NETWORK_RANGE, '-oG', '-'],
            capture_output=True, text=True, timeout=60
        )

        online_ips = []
        for line in result.stdout.split('\n'):
            if 'Up' in line:
                match = re.search(r'(\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    online_ips.append(match.group(1))

        return online_ips
    except Exception as e:
        logger.error(f"Network scan failed: {e}")
        return []

def update_device_status(online_ips):
    """Update device online status in database"""
    conn = get_db_connection()
    cur = conn.cursor()
    now = datetime.now()

    try:
        # Update hardware inventory
        cur.execute("""
            UPDATE hardware_inventory
            SET online_status = (ip_address = ANY(%s)),
                last_seen = CASE WHEN ip_address = ANY(%s) THEN %s ELSE last_seen END
        """, (online_ips, online_ips, now))

        # Update IoT devices
        cur.execute("""
            UPDATE iot_devices
            SET online_status = (ip_address = ANY(%s)),
                last_seen = CASE WHEN ip_address = ANY(%s) THEN %s ELSE last_seen END
            WHERE ip_address IS NOT NULL
        """, (online_ips, online_ips, now))

        conn.commit()

        # Get counts for logging
        cur.execute("SELECT COUNT(*) FROM hardware_inventory WHERE online_status = true")
        hw_online = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM iot_devices WHERE online_status = true")
        iot_online = cur.fetchone()[0]

        logger.info(f"Discovery complete: {len(online_ips)} IPs found, {hw_online} nodes online, {iot_online} IoT online")

    except Exception as e:
        logger.error(f"Database update failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def run_daemon():
    """Main daemon loop"""
    logger.info("Spatial Discovery Daemon starting...")
    logger.info(f"Scanning {NETWORK_RANGE} every {SCAN_INTERVAL} seconds")

    while True:
        try:
            online_ips = scan_network()
            if online_ips:
                update_device_status(online_ips)
        except Exception as e:
            logger.error(f"Daemon error: {e}")

        time.sleep(SCAN_INTERVAL)

if __name__ == '__main__':
    run_daemon()
```

---

### Task 6: Add Secured Spatial Endpoints to LLM Gateway

Create `/ganuda/services/llm_gateway/spatial_routes.py`:

```python
# =====================
# SPATIAL AWARENESS API
# Security: All endpoints require authentication
# Audit: All queries logged to spatial_audit_log
# =====================

def log_spatial_query(query_type, api_key_id, params, result_count, client_ip):
    """Log all spatial queries for security audit"""
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO spatial_audit_log (query_type, api_key_id, query_params, result_count, client_ip)
            VALUES (%s, %s, %s, %s, %s)
        """, (query_type, api_key_id, json.dumps(params), result_count, client_ip))
        conn.commit()
    except Exception as e:
        logger.warning(f"Failed to log spatial query: {e}")
    finally:
        cur.close()
        conn.close()

@app.route('/v1/spatial/zones', methods=['GET'])
@require_api_key  # Authentication required
def get_zones():
    """List all spatial zones with device counts and capabilities"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT z.zone_name, z.zone_type, z.description,
               z.has_voice_assistant, z.has_security_device, z.privacy_sensitive,
               COUNT(DISTINCT h.id) as node_count,
               COUNT(DISTINCT i.id) as iot_count,
               ARRAY_AGG(DISTINCT i.ecosystem) FILTER (WHERE i.ecosystem IS NOT NULL) as ecosystems
        FROM spatial_zones z
        LEFT JOIN hardware_inventory h ON h.zone_id = z.zone_id
        LEFT JOIN iot_devices i ON i.zone_id = z.zone_id
        GROUP BY z.zone_id
        ORDER BY z.zone_name
    """)
    zones = cur.fetchall()
    cur.close()
    conn.close()

    result = {
        'zones': [
            {
                'name': z[0],
                'type': z[1],
                'description': z[2],
                'capabilities': {
                    'voice': z[3],
                    'security': z[4]
                },
                'privacy_sensitive': z[5],
                'nodes': z[6],
                'iot_devices': z[7],
                'ecosystems': z[8] or []
            } for z in zones
        ]
    }

    # Audit log
    log_spatial_query('zone_list', request.api_key_id, {}, len(zones), request.remote_addr)

    return jsonify(result)

@app.route('/v1/spatial/zone/<zone_name>', methods=['GET'])
@require_api_key
def get_zone_devices(zone_name):
    """Get all devices in a specific zone with real-time status"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM get_devices_in_zone(%s)", (zone_name,))
    devices = cur.fetchall()

    cur.execute("SELECT * FROM get_zone_context(%s)", (zone_name,))
    context = cur.fetchone()[0] if cur.rowcount > 0 else {}

    cur.close()
    conn.close()

    result = {
        'zone': zone_name,
        'context': context,
        'devices': [
            {
                'type': d[0],
                'name': d[1],
                'ip': d[2],
                'position': d[3],
                'ecosystem': d[4],
                'online': d[5],
                'last_seen': d[6].isoformat() if d[6] else None
            } for d in devices
        ]
    }

    # Audit log
    log_spatial_query('zone_detail', request.api_key_id, {'zone': zone_name}, len(devices), request.remote_addr)

    return jsonify(result)

@app.route('/v1/spatial/voice-zones', methods=['GET'])
@require_api_key
def get_voice_enabled_zones():
    """Get zones with voice/audio capabilities for routing"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM get_voice_zones()")
    zones = cur.fetchall()
    cur.close()
    conn.close()

    result = {
        'voice_zones': [
            {
                'zone': z[0],
                'devices': z[1]
            } for z in zones
        ]
    }

    log_spatial_query('voice_zones', request.api_key_id, {}, len(zones), request.remote_addr)

    return jsonify(result)

@app.route('/v1/spatial/security', methods=['GET'])
@require_api_key
def get_security_status():
    """Get security perimeter device status"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM get_security_perimeter()")
    devices = cur.fetchall()
    cur.close()
    conn.close()

    result = {
        'perimeter': [
            {
                'zone': d[0],
                'device': d[1],
                'type': d[2],
                'online': d[3],
                'state': d[4]
            } for d in devices
        ],
        'all_online': all(d[3] for d in devices)
    }

    log_spatial_query('security_perimeter', request.api_key_id, {}, len(devices), request.remote_addr)

    return jsonify(result)

@app.route('/v1/spatial/environmental/<zone_name>', methods=['GET'])
@require_api_key
def get_environmental(zone_name):
    """Get environmental correlation for a zone (thermal + climate)"""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT get_environmental_correlation(%s)", (zone_name,))
    result = cur.fetchone()[0]
    cur.close()
    conn.close()

    log_spatial_query('environmental', request.api_key_id, {'zone': zone_name}, 1, request.remote_addr)

    return jsonify(result)
```

---

### Task 7: Add Spatial View to SAG UI

Create `/ganuda/services/sag_unified/templates/spatial_section.html`:

```html
<!-- Spatial Awareness Section -->
<div class="card">
    <h3>Physical Layout</h3>
    <div class="spatial-summary" id="spatial-summary">
        <!-- Summary stats populated by JS -->
    </div>
    <div class="spatial-grid" id="spatial-zones">
        <!-- Zone cards populated by JS -->
    </div>
    <div class="ecosystem-legend">
        <span class="legend-item amazon">Amazon</span>
        <span class="legend-item google">Google</span>
        <span class="legend-item sonos">Sonos</span>
        <span class="legend-item network">Network</span>
    </div>
</div>

<style>
.spatial-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 10px;
    margin-top: 10px;
}
.zone-card {
    border: 1px solid #333;
    border-radius: 4px;
    padding: 10px;
    background: #1a1a1a;
}
.zone-card.has-nodes {
    border-color: #4CAF50;
    background: #1a2a1a;
}
.zone-card.has-security {
    border-left: 3px solid #f44336;
}
.zone-card.has-voice {
    border-right: 3px solid #2196F3;
}
.zone-card .zone-name {
    font-weight: bold;
    color: #fff;
}
.zone-card .zone-type {
    font-size: 0.8em;
    color: #888;
}
.zone-card .device-count {
    margin-top: 5px;
}
.badge {
    display: inline-block;
    padding: 2px 6px;
    border-radius: 3px;
    font-size: 0.75em;
    margin-right: 4px;
}
.badge.nodes { background: #4CAF50; }
.badge.iot { background: #2196F3; }
.badge.offline { background: #f44336; }
.ecosystem-legend {
    margin-top: 10px;
    padding-top: 10px;
    border-top: 1px solid #333;
}
.legend-item {
    display: inline-block;
    padding: 2px 8px;
    margin-right: 8px;
    border-radius: 3px;
    font-size: 0.8em;
}
.legend-item.amazon { background: #ff9900; color: #000; }
.legend-item.google { background: #4285f4; color: #fff; }
.legend-item.sonos { background: #000; color: #fff; border: 1px solid #666; }
.legend-item.network { background: #666; color: #fff; }
.spatial-summary {
    display: flex;
    gap: 20px;
    padding: 10px;
    background: #0a0a0a;
    border-radius: 4px;
}
.summary-stat {
    text-align: center;
}
.summary-stat .value {
    font-size: 1.5em;
    font-weight: bold;
}
.summary-stat .label {
    font-size: 0.8em;
    color: #888;
}
</style>

<script>
async function loadSpatialZones() {
    try {
        const response = await fetch('/api/spatial/zones');
        const data = await response.json();

        // Summary stats
        const totalNodes = data.zones.reduce((sum, z) => sum + z.nodes, 0);
        const totalIoT = data.zones.reduce((sum, z) => sum + z.iot_devices, 0);
        const securityZones = data.zones.filter(z => z.capabilities.security).length;
        const voiceZones = data.zones.filter(z => z.capabilities.voice).length;

        document.getElementById('spatial-summary').innerHTML = `
            <div class="summary-stat">
                <div class="value">${data.zones.length}</div>
                <div class="label">Zones</div>
            </div>
            <div class="summary-stat">
                <div class="value">${totalNodes}</div>
                <div class="label">Nodes</div>
            </div>
            <div class="summary-stat">
                <div class="value">${totalIoT}</div>
                <div class="label">IoT Devices</div>
            </div>
            <div class="summary-stat">
                <div class="value">${securityZones}</div>
                <div class="label">Security Points</div>
            </div>
            <div class="summary-stat">
                <div class="value">${voiceZones}</div>
                <div class="label">Voice Zones</div>
            </div>
        `;

        // Zone cards
        const container = document.getElementById('spatial-zones');
        container.innerHTML = data.zones.map(zone => {
            const classes = ['zone-card'];
            if (zone.nodes > 0) classes.push('has-nodes');
            if (zone.capabilities.security) classes.push('has-security');
            if (zone.capabilities.voice) classes.push('has-voice');

            const ecosystemBadges = (zone.ecosystems || [])
                .filter(e => e)
                .map(e => `<span class="badge" style="background:${getEcosystemColor(e)}">${e}</span>`)
                .join('');

            return `
                <div class="${classes.join(' ')}" onclick="showZoneDetail('${zone.name}')">
                    <div class="zone-name">${zone.name.replace(/_/g, ' ')}</div>
                    <div class="zone-type">${zone.type}</div>
                    <div class="device-count">
                        ${zone.nodes > 0 ? `<span class="badge nodes">${zone.nodes} nodes</span>` : ''}
                        ${zone.iot_devices > 0 ? `<span class="badge iot">${zone.iot_devices} IoT</span>` : ''}
                    </div>
                    <div class="ecosystems">${ecosystemBadges}</div>
                </div>
            `;
        }).join('');

    } catch (error) {
        console.error('Failed to load spatial zones:', error);
    }
}

function getEcosystemColor(ecosystem) {
    const colors = {
        'amazon': '#ff9900',
        'google': '#4285f4',
        'sonos': '#000',
        'network': '#666',
        'federation': '#4CAF50'
    };
    return colors[ecosystem] || '#888';
}

async function showZoneDetail(zoneName) {
    // Could open modal with detailed zone view
    console.log('Zone clicked:', zoneName);
}

// Load on page init
loadSpatialZones();
// Refresh every 60 seconds
setInterval(loadSpatialZones, 60000);
</script>
```

---

## SUCCESS CRITERIA

1. `spatial_zones` table created with 12 zones (including relative positions)
2. `iot_devices` enhanced with ecosystem, protocol, microphone/camera flags
3. All 6 federation nodes have zone assignments
4. All 20 IoT devices seeded with full metadata
5. Device discovery daemon running (nmap-based)
6. Spatial API endpoints secured with authentication
7. All spatial queries logged to audit table
8. SAG UI shows physical layout with ecosystem colors
9. Voice-enabled zones queryable for audio routing
10. Security perimeter status available via API

---

## DEVICE INVENTORY SUMMARY

| Category | Count | Ecosystems |
|----------|-------|------------|
| Compute Nodes | 6 | Federation |
| Audio (Sonos) | 5 | Sonos |
| Voice Assistants | 3 | Amazon (2), Google (1) |
| Security | 4 | Amazon (Ring), Google (Nest) |
| Climate | 2 | Google (Nest), Other (AC) |
| Network | 6 | Network |
| **Total** | **26** | |

---

## INTEGRATION PRIORITIES

| Priority | Integration | Effort | Value |
|----------|-------------|--------|-------|
| 1 | Network Discovery (nmap) | Low | High - know what's online |
| 2 | Sonos Local API | Medium | High - audio routing |
| 3 | Nest/Google API | High | Medium - requires OAuth setup |
| 4 | Ring/Amazon API | High | Low - unofficial APIs |

---

## SECURITY NOTES (Crawdad Approved)

1. **No raw GPS in APIs** - Only relative positions exposed
2. **Authentication required** - All /v1/spatial/* endpoints need valid API key
3. **Audit logging** - Every spatial query logged with IP, key, params
4. **Privacy flags** - Bedrooms/bathrooms marked as privacy_sensitive
5. **Microphone/camera tracking** - Know which devices can listen/watch

---

*For Seven Generations - Cherokee AI Federation*
*"Know where you are to know where you're going"*
*Council Review: PROCEED 82.5% with security enhancements*

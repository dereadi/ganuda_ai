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
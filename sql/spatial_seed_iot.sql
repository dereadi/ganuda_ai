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
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
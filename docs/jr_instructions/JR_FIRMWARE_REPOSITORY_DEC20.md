# Jr Instructions: Firmware Repository Population - December 20, 2025

**Priority**: 2
**Assigned Jr**: it_triad_jr
**Council Context**: IoT dorking research completed - actionable firmware sources identified

---

## OBJECTIVE

Populate the software repository with firmware and documentation for Federation IoT devices. Enable offline patching and air-gapped updates.

**Repository Location**: `/ganuda/software_repo/`

---

## DEVICE FIRMWARE SOURCES

### Task 1: Sonos Firmware Documentation

Sonos doesn't provide direct firmware downloads (OTA only), but we need local API docs.

```bash
cd /ganuda/software_repo/firmware/sonos

# Clone the community Sonos API documentation
git clone https://github.com/svrooij/sonos-api-docs.git api-docs

# Clone node-sonos-http-api for local control
git clone https://github.com/jishi/node-sonos-http-api.git http-api

# Clone SoCo Python library
git clone https://github.com/SoCo/SoCo.git soco-python
```

---

### Task 2: ESPHome/ESP32 Firmware Tools

```bash
cd /ganuda/software_repo/firmware/espressif

# ESPHome for ESP32/ESP8266 firmware building
pip download esphome -d ./pip-cache/

# Clone OpenMQTTGateway for BLE/433mhz gateway
git clone https://github.com/1technophile/OpenMQTTGateway.git

# ESP-IDF framework (large - optional)
# git clone --recursive https://github.com/espressif/esp-idf.git

# Create README
cat > README.md << 'EOF'
# Espressif Firmware Repository

## ESPHome
Recommended for ESP32/ESP8266 home automation.
Install: `pip install esphome`
Cached: ./pip-cache/

## OpenMQTTGateway
BLE, 433mhz, IR, LoRa gateway firmware.
Build with PlatformIO or Arduino IDE.

## Usage
1. Configure YAML for device
2. Build with `esphome compile device.yaml`
3. Flash via USB or OTA

For Seven Generations.
EOF
```

---

### Task 3: Daikin Integration Files

```bash
cd /ganuda/software_repo/firmware/daikin

# Clone pydaikin library for local API
git clone https://github.com/fredrike/pydaikin.git

# Clone Home Assistant Daikin integration for reference
git clone https://github.com/home-assistant/core.git --depth 1 --filter=blob:none --sparse
cd core
git sparse-checkout set homeassistant/components/daikin
mv homeassistant/components/daikin ../ha-daikin-component
cd ..
rm -rf core

# Document firmware update procedure
cat > FIRMWARE_UPDATE.md << 'EOF'
# Daikin BRP069C4x Firmware Update

## Requirements
- Firmware 2.8.0+ for local API support
- Home Assistant 2025.9+

## Update Procedure
1. Open Daikin Onecta app
2. Go to device settings
3. Check for firmware updates
4. Apply update (device will restart)

## Verify Local API
After update, device should respond on port 80:
```
curl http://<daikin-ip>/common/basic_info
```

For Seven Generations.
EOF
```

---

### Task 4: Cisco/Linksys Security Audit

**CRITICAL**: These devices have known vulnerabilities (FBI May 2025 warning)

```bash
cd /ganuda/software_repo/firmware/cisco_linksys

# Create security audit checklist
cat > SECURITY_AUDIT.md << 'EOF'
# Cisco/Linksys Security Audit Checklist

## FBI May 2025 Warning
13 EOL Linksys models actively exploited by 5Socks and AnyProxy botnets.

## IMMEDIATE ACTIONS

### 1. Inventory Check
List all Cisco/Linksys devices:
```sql
SELECT device_name, ip_address, mac_address, last_seen
FROM iot_devices
WHERE vendor ILIKE '%cisco%' OR vendor ILIKE '%linksys%';
```

### 2. Default Credentials Check
Common defaults to verify changed:
- admin / admin
- admin / password
- admin / (blank)
- user / user

### 3. Firmware Version Check
Access router admin: http://<router-ip>/
Check: Administration > Firmware Upgrade
Compare against latest from manufacturer

### 4. EOL Model Check
If model is EOL (End of Life), REPLACE IMMEDIATELY:
- E1000, E1200, E1500, E2500
- WRT54G (all versions)
- Other models 5+ years old

### 5. Security Hardening
- [ ] Change admin password to strong unique value
- [ ] Disable remote management
- [ ] Enable WPA3 (or WPA2-AES minimum)
- [ ] Disable WPS
- [ ] Update firmware to latest
- [ ] Enable firewall
- [ ] Disable UPnP if not needed

## CVE Reference
- CVE-2024-40495: Critical command injection
- Check NVD for model-specific vulnerabilities

For Seven Generations.
EOF

# Create device inventory script
cat > audit_devices.sh << 'EOF'
#!/bin/bash
# Scan for Cisco/Linksys devices and check accessibility

DEVICES=$(PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -t -c "
SELECT ip_address FROM iot_devices
WHERE vendor ILIKE '%cisco%' OR vendor ILIKE '%linksys%';")

for ip in $DEVICES; do
    echo "Checking $ip..."
    if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 3 "http://$ip/" | grep -q "200\|401"; then
        echo "  ACCESSIBLE - verify credentials changed!"
    else
        echo "  Not responding on HTTP"
    fi
done
EOF
chmod +x audit_devices.sh
```

---

### Task 5: Amazon Echo/Fire Integration

```bash
cd /ganuda/software_repo/firmware/amazon

# Clone alexa-remote for API access
git clone https://github.com/Apollon77/alexa-remote.git

# Document integration
cat > INTEGRATION.md << 'EOF'
# Amazon Echo/Fire Integration

## Home Assistant Integration (2025.6+)
Native Alexa Devices integration available.
Requires: Amazon account with Authenticator MFA

## Features
- TTS announcements
- Volume control
- Media playback
- Routine triggering

## Fire TV
Use Android Debug Bridge (ADB) integration.
Enable Developer Mode on Fire TV first.

## Echo Show Jailbreak
See: derekseaman.com echo show guide
Allows running custom dashboards.

For Seven Generations.
EOF
```

---

### Task 6: Update Software Repository Database

```sql
-- Register cached firmware in software_repository table

INSERT INTO software_repository (package_name, package_type, current_version, local_path, is_cached, notes)
VALUES
('sonos-api-docs', 'documentation', 'latest', '/ganuda/software_repo/firmware/sonos/api-docs', true, 'Community UPnP API documentation'),
('node-sonos-http-api', 'integration', 'latest', '/ganuda/software_repo/firmware/sonos/http-api', true, 'HTTP API bridge for Sonos'),
('soco-python', 'library', 'latest', '/ganuda/software_repo/firmware/sonos/soco-python', true, 'Python library for Sonos'),
('esphome', 'firmware-tool', 'latest', '/ganuda/software_repo/firmware/espressif/pip-cache', true, 'ESP32/ESP8266 firmware builder'),
('openmqttgateway', 'firmware', 'latest', '/ganuda/software_repo/firmware/espressif/OpenMQTTGateway', true, 'BLE/433mhz/IR gateway'),
('pydaikin', 'library', 'latest', '/ganuda/software_repo/firmware/daikin/pydaikin', true, 'Daikin local API library'),
('alexa-remote', 'library', 'latest', '/ganuda/software_repo/firmware/amazon/alexa-remote', true, 'Alexa device control library')
ON CONFLICT (package_name, package_type) DO UPDATE SET
    local_path = EXCLUDED.local_path,
    is_cached = true,
    last_sync = NOW();
```

---

## SUCCESS CRITERIA

1. All git repos cloned to `/ganuda/software_repo/firmware/`
2. Security audit checklist created for Cisco/Linksys
3. README/documentation files created
4. software_repository table updated with cached packages
5. Total size < 2GB (exclude large repos like esp-idf)

---

## TESTING

```bash
# Verify repository populated
find /ganuda/software_repo -type d -name ".git" | wc -l
# Should show 5+ git repos

# Check database entries
PGPASSWORD='jawaseatlasers2' psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT package_name, package_type, is_cached FROM software_repository WHERE is_cached = true;"
```

---

*For Seven Generations - Cherokee AI Federation*

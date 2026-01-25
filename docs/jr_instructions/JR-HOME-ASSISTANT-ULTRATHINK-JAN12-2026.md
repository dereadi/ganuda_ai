# ULTRATHINK: Home Assistant + Frigate + Face Recognition Deployment

**Date**: January 12, 2026
**TPM**: Flying Squirrel (dereadi)
**Council Approval**: UNANIMOUS
**ULTRATHINK Hash**: 8c4f2e1a7b3d9f06

---

## Executive Summary

Deploy full Home Assistant stack on bluefin with:
- Home Assistant Core for IoT management
- Frigate NVR with NVIDIA GPU acceleration
- Double Take + CompreFace for face recognition
- Telegram alerts for unknown faces
- Remote access via Tailscale

---

## Target Node

**bluefin** (192.168.132.222)
- CPU: Intel i9-14900KF (32 threads)
- RAM: 123GB (113GB available)
- GPU: NVIDIA RTX 5070
- Storage: 465GB free on NVMe
- OS: Ubuntu 22.04

---

## Phase 1: Foundation (Jr-Light)

### JR-HA-PHASE1-DOCKER-SETUP.md

**Objective**: Prepare Docker environment and directory structure

#### Step 1.1: Create Directory Structure

```bash
# On bluefin as dereadi
sudo mkdir -p /ganuda/homeassistant/{config,media}
sudo mkdir -p /ganuda/frigate/{config,recordings,clips,exports}
sudo mkdir -p /ganuda/mosquitto/{config,data,log}
sudo mkdir -p /ganuda/doubletake/{config,.storage}
sudo mkdir -p /ganuda/compreface/{data,backup}

# Set ownership
sudo chown -R dereadi:dereadi /ganuda/homeassistant
sudo chown -R dereadi:dereadi /ganuda/frigate
sudo chown -R dereadi:dereadi /ganuda/doubletake
sudo chown -R 1883:1883 /ganuda/mosquitto  # mosquitto uid
sudo chown -R dereadi:dereadi /ganuda/compreface
chmod 700 /ganuda/compreface  # Biometric data protection
```

#### Step 1.2: Create Environment File

```bash
# /ganuda/homeassistant/.env
cat > /ganuda/homeassistant/.env << 'EOF'
# Home Assistant Stack Environment
# Cherokee AI Federation - January 2026
# DO NOT COMMIT TO GIT

# Timezone
TZ=America/Chicago

# MQTT Credentials
MQTT_USER=homeassistant
MQTT_PASSWORD=<generate_secure_password>

# Frigate MQTT User
FRIGATE_MQTT_USER=frigate
FRIGATE_MQTT_PASSWORD=<generate_secure_password>

# Double Take MQTT User
DOUBLETAKE_MQTT_USER=doubletake
DOUBLETAKE_MQTT_PASSWORD=<generate_secure_password>

# Camera Credentials (from vault)
CAMERA_OFFICE_USER=admin
CAMERA_OFFICE_PASSWORD=<from_telegram_vault>

# CompreFace API Key (generated after setup)
COMPREFACE_API_KEY=<will_be_generated>

# Telegram (from vault)
TELEGRAM_BOT_TOKEN=<from_vault>
TELEGRAM_CHAT_ID=<tpm_chat_id>
EOF

chmod 600 /ganuda/homeassistant/.env
```

#### Step 1.3: Bootstrap Mosquitto Config

```bash
# Phase 1 - Anonymous access for bootstrap
cat > /ganuda/mosquitto/config/mosquitto.conf << 'EOF'
# Mosquitto MQTT Broker - Bootstrap Config
# Cherokee AI Federation

listener 1883
listener 9001
protocol websockets

# BOOTSTRAP ONLY - Will be secured after password creation
allow_anonymous true

persistence true
persistence_location /mosquitto/data/

log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
EOF
```

#### Step 1.4: Create Docker Compose (Phase 1)

```bash
cat > /ganuda/homeassistant/docker-compose.yml << 'EOF'
# Home Assistant Stack - Phase 1 (Foundation)
# Cherokee AI Federation - January 2026

version: '3.8'

services:
  # MQTT Broker
  mosquitto:
    image: eclipse-mosquitto:2
    container_name: mosquitto
    restart: unless-stopped
    ports:
      - "1883:1883"
      - "9001:9001"
    volumes:
      - /ganuda/mosquitto/config:/mosquitto/config
      - /ganuda/mosquitto/data:/mosquitto/data
      - /ganuda/mosquitto/log:/mosquitto/log
    networks:
      - homeassistant
    healthcheck:
      test: ["CMD", "mosquitto_sub", "-t", "$$SYS/#", "-C", "1", "-i", "healthcheck", "-W", "3"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Home Assistant Core
  homeassistant:
    image: ghcr.io/home-assistant/home-assistant:stable
    container_name: homeassistant
    restart: unless-stopped
    privileged: true
    ports:
      - "8123:8123"
    environment:
      - TZ=${TZ:-America/Chicago}
    volumes:
      - /ganuda/homeassistant/config:/config
      - /ganuda/homeassistant/media:/media
      - /etc/localtime:/etc/localtime:ro
    depends_on:
      mosquitto:
        condition: service_healthy
    networks:
      - homeassistant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8123/api/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

networks:
  homeassistant:
    name: homeassistant
    driver: bridge
EOF
```

#### Step 1.5: Start Phase 1 Services

```bash
cd /ganuda/homeassistant
docker compose up -d

# Watch logs for HA initial password
docker logs -f homeassistant 2>&1 | head -50

# Verify services
docker compose ps
```

#### Step 1.6: Secure MQTT (After Bootstrap)

```bash
# Create password file
docker exec mosquitto mosquitto_passwd -c -b /mosquitto/config/passwd homeassistant '<MQTT_PASSWORD>'
docker exec mosquitto mosquitto_passwd -b /mosquitto/config/passwd frigate '<FRIGATE_MQTT_PASSWORD>'
docker exec mosquitto mosquitto_passwd -b /mosquitto/config/passwd doubletake '<DOUBLETAKE_MQTT_PASSWORD>'

# Update config for authentication
cat > /ganuda/mosquitto/config/mosquitto.conf << 'EOF'
# Mosquitto MQTT Broker - Secured Config
# Cherokee AI Federation

listener 1883
listener 9001
protocol websockets

# Authentication ENABLED
allow_anonymous false
password_file /mosquitto/config/passwd

persistence true
persistence_location /mosquitto/data/

log_dest file /mosquitto/log/mosquitto.log
log_dest stdout
EOF

# Restart mosquitto
docker restart mosquitto
```

#### Step 1.7: Verify Phase 1

```bash
# Test MQTT auth
docker exec mosquitto mosquitto_sub -u homeassistant -P '<password>' -t 'test' -C 1 &
docker exec mosquitto mosquitto_pub -u homeassistant -P '<password>' -t 'test' -m 'hello'

# Access Home Assistant
echo "Home Assistant: http://192.168.132.222:8123"
```

---

## Phase 2: Frigate NVR (Jr-Light)

### JR-HA-PHASE2-FRIGATE-SETUP.md

**Objective**: Deploy Frigate with NVIDIA GPU acceleration

#### Step 2.1: Verify NVIDIA Runtime

```bash
# Check NVIDIA driver
nvidia-smi

# Install NVIDIA Container Toolkit if needed
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker

# Test NVIDIA in Docker
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi
```

#### Step 2.2: Create Frigate Config

```bash
cat > /ganuda/frigate/config/config.yml << 'EOF'
# Frigate NVR Configuration
# Cherokee AI Federation - January 2026

mqtt:
  enabled: true
  host: mosquitto
  port: 1883
  user: "{FRIGATE_MQTT_USER}"
  password: "{FRIGATE_MQTT_PASSWORD}"
  topic_prefix: frigate

database:
  path: /config/frigate.db

# NVIDIA GPU Hardware Acceleration
ffmpeg:
  hwaccel_args: preset-nvidia-h264
  output_args:
    record: preset-record-generic-audio-aac

# Detector using CPU (can upgrade to TensorRT later)
detectors:
  cpu1:
    type: cpu
    num_threads: 4

# Object detection settings
objects:
  track:
    - person
    - car
    - dog
    - cat
  filters:
    person:
      min_area: 5000
      max_area: 100000
      threshold: 0.7

# Recording settings (Turtle retention policy)
record:
  enabled: true
  retain:
    days: 3
    mode: motion
  events:
    retain:
      default: 14
      mode: active_objects

# Snapshot settings
snapshots:
  enabled: true
  clean_copy: true
  timestamp: true
  bounding_box: true
  retain:
    default: 14

# Cameras
cameras:
  office:
    enabled: true
    ffmpeg:
      inputs:
        # Main stream for recording
        - path: rtsp://admin:{FRIGATE_RTSP_PASSWORD}@192.168.132.181:554/cam/realmonitor?channel=1&subtype=0
          roles:
            - record
        # Sub stream for detection (lower bandwidth)
        - path: rtsp://admin:{FRIGATE_RTSP_PASSWORD}@192.168.132.181:554/cam/realmonitor?channel=1&subtype=1
          roles:
            - detect
    detect:
      width: 640
      height: 480
      fps: 5
    motion:
      mask:
        # Add mask coordinates if needed for static areas
    objects:
      track:
        - person
    zones:
      rack_area:
        coordinates: 0,0,640,0,640,480,0,480  # Adjust to actual rack location

# UI settings
ui:
  use_experimental: false
EOF
```

#### Step 2.3: Update Docker Compose (Add Frigate)

```bash
# Append to docker-compose.yml
cat >> /ganuda/homeassistant/docker-compose.yml << 'EOF'

  # Frigate NVR
  frigate:
    image: ghcr.io/blakeblackshear/frigate:stable
    container_name: frigate
    restart: unless-stopped
    privileged: true
    shm_size: "512mb"
    ports:
      - "8971:8971"   # Web UI
      - "8554:8554"   # RTSP feeds
      - "8555:8555/tcp"  # WebRTC over tcp
      - "8555:8555/udp"  # WebRTC over udp
    environment:
      - TZ=${TZ:-America/Chicago}
      - FRIGATE_RTSP_PASSWORD=${CAMERA_OFFICE_PASSWORD}
    volumes:
      - /ganuda/frigate/config:/config
      - /ganuda/frigate/recordings:/media/frigate/recordings
      - /ganuda/frigate/clips:/media/frigate/clips
      - /ganuda/frigate/exports:/media/frigate/exports
      - /etc/localtime:/etc/localtime:ro
      - type: tmpfs
        target: /tmp/cache
        tmpfs:
          size: 1000000000  # 1GB tmpfs for cache
    devices:
      - /dev/dri/renderD128:/dev/dri/renderD128  # Intel QSV (backup)
      - /dev/dri/card1:/dev/dri/card1
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    depends_on:
      mosquitto:
        condition: service_healthy
    networks:
      - homeassistant
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8971/api/version"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
EOF
```

#### Step 2.4: Start Frigate

```bash
cd /ganuda/homeassistant
docker compose up -d frigate

# Watch logs
docker logs -f frigate

# Verify
echo "Frigate UI: https://192.168.132.222:8971"
```

#### Step 2.5: Install Frigate Integration in Home Assistant

```
1. In Home Assistant, go to Settings → Devices & Services
2. Click "Add Integration"
3. Search for "Frigate"
4. If not found, install HACS first:
   - Go to Settings → Add-ons → Add-on Store
   - Install "HACS"
   - Restart Home Assistant
   - Settings → Devices & Services → Add Integration → HACS
   - Configure HACS
   - In HACS, search for "Frigate" and install
5. Add Frigate integration with URL: http://frigate:8971
```

---

## Phase 3: Face Recognition (Jr-Light)

### JR-HA-PHASE3-FACE-RECOGNITION.md

**Objective**: Deploy CompreFace and Double Take for face recognition

#### Step 3.1: Update Docker Compose (Add CompreFace + Double Take)

```bash
cat >> /ganuda/homeassistant/docker-compose.yml << 'EOF'

  # CompreFace - Face Recognition Backend
  compreface-postgres:
    image: postgres:11.5
    container_name: compreface-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_USER=compreface
      - POSTGRES_PASSWORD=compreface
      - POSTGRES_DB=compreface
    volumes:
      - /ganuda/compreface/data/postgres:/var/lib/postgresql/data
    networks:
      - homeassistant

  compreface-admin:
    image: exadel/compreface-admin:latest
    container_name: compreface-admin
    restart: unless-stopped
    environment:
      - POSTGRES_USER=compreface
      - POSTGRES_PASSWORD=compreface
      - POSTGRES_URL=jdbc:postgresql://compreface-postgres:5432/compreface
      - SPRING_PROFILES_ACTIVE=dev
      - ENABLE_EMAIL_SERVER=false
      - ADMIN_JAVA_OPTS=-Xmx1g
    depends_on:
      - compreface-postgres
    networks:
      - homeassistant

  compreface-api:
    image: exadel/compreface-api:latest
    container_name: compreface-api
    restart: unless-stopped
    environment:
      - POSTGRES_USER=compreface
      - POSTGRES_PASSWORD=compreface
      - POSTGRES_URL=jdbc:postgresql://compreface-postgres:5432/compreface
      - SPRING_PROFILES_ACTIVE=dev
      - API_JAVA_OPTS=-Xmx4g
      - SAVE_IMAGES_TO_DB=true
    depends_on:
      - compreface-postgres
    networks:
      - homeassistant

  compreface-core:
    image: exadel/compreface-core:latest
    container_name: compreface-core
    restart: unless-stopped
    environment:
      - ML_PORT=3000
    networks:
      - homeassistant

  compreface:
    image: exadel/compreface-fe:latest
    container_name: compreface
    restart: unless-stopped
    ports:
      - "8000:80"
    depends_on:
      - compreface-api
      - compreface-admin
    environment:
      - CLIENT_MAX_BODY_SIZE=10M
      - PROXY_READ_TIMEOUT=60000ms
      - PROXY_CONNECT_TIMEOUT=10000ms
    networks:
      - homeassistant

  # Double Take - Face Recognition UI
  doubletake:
    image: jakowenko/double-take:latest
    container_name: doubletake
    restart: unless-stopped
    ports:
      - "3000:3000"
    volumes:
      - /ganuda/doubletake/.storage:/.storage
    environment:
      - TZ=${TZ:-America/Chicago}
    depends_on:
      - mosquitto
      - frigate
    networks:
      - homeassistant
EOF
```

#### Step 3.2: Create Double Take Config

```bash
cat > /ganuda/doubletake/.storage/config.yml << 'EOF'
# Double Take Configuration
# Cherokee AI Federation - January 2026

mqtt:
  host: mosquitto
  port: 1883
  username: doubletake
  password: "{DOUBLETAKE_MQTT_PASSWORD}"

frigate:
  url: http://frigate:8971
  update_sub_labels: true

detectors:
  compreface:
    url: http://compreface:80
    key: "{COMPREFACE_API_KEY}"
    det_prob_threshold: 0.8
    cameras:
      - office

detect:
  match:
    min_area: 10000
    confidence: 60
  unknown:
    confidence: 40

time:
  timezone: America/Chicago

# Notification settings
notify:
  unknown:
    title: "Unknown Person Detected"
    body: "{{camera}} detected an unknown person"

ui:
  pagination:
    limit: 50
  thumbnails:
    quality: 95
    width: 500

# Retention (Turtle policy)
purge:
  matches:
    enabled: true
    hours: 720  # 30 days
  unknowns:
    enabled: true
    hours: 168    # 7 days
EOF
```

#### Step 3.3: Start Face Recognition Services

```bash
cd /ganuda/homeassistant
docker compose up -d

# Watch CompreFace init
docker logs -f compreface

# Access UIs
echo "CompreFace: http://192.168.132.222:8000"
echo "Double Take: http://192.168.132.222:3000"
```

#### Step 3.4: Configure CompreFace

```
1. Access http://192.168.132.222:8000
2. Sign up / Create admin account
3. Create Application: "Cherokee Federation"
4. Add Recognition Service
5. Copy the API Key
6. Update /ganuda/homeassistant/.env with COMPREFACE_API_KEY
7. Update Double Take config with API key
8. Restart Double Take: docker restart doubletake
```

#### Step 3.5: Train TPM Face

```
1. Access Double Take: http://192.168.132.222:3000
2. Go to Train tab
3. Upload multiple photos of TPM (different angles, lighting)
4. Name: "TPM" or "dereadi"
5. Submit training
6. Verify detection by walking past office camera
```

---

## Phase 4: Telegram Alerts (Jr-Light)

### JR-HA-PHASE4-TELEGRAM-ALERTS.md

**Objective**: Configure Telegram notifications for unknown faces

#### Step 4.1: Get Telegram Token from Vault

```bash
# On a Mac with vault access
python3 -c "
import sys
sys.path.insert(0, '/Users/Shared/ganuda/home/dereadi')
from telegram_token_vault import TelegramTokenVault
vault = TelegramTokenVault('/Users/Shared/ganuda/home/dereadi/.telegram_vault.enc')
print('alert_bot token:', vault.decrypt_token('alert_bot'))
"
```

#### Step 4.2: Home Assistant Telegram Integration

Add to `/ganuda/homeassistant/config/configuration.yaml`:

```yaml
# Telegram Bot
telegram_bot:
  - platform: polling
    api_key: !secret telegram_bot_token
    allowed_chat_ids:
      - !secret telegram_chat_id

# Telegram Notifier
notify:
  - platform: telegram
    name: telegram_tpm
    chat_id: !secret telegram_chat_id
```

Add to `/ganuda/homeassistant/config/secrets.yaml`:

```yaml
telegram_bot_token: "<from_vault>"
telegram_chat_id: "<tpm_chat_id>"
```

#### Step 4.3: Create Automation for Unknown Face

Add to `/ganuda/homeassistant/config/automations.yaml`:

```yaml
# Unknown Face Alert
- id: unknown_face_alert
  alias: "Alert on Unknown Face"
  description: "Send Telegram notification when unknown face detected"
  trigger:
    - platform: mqtt
      topic: "double-take/matches/unknown"
  action:
    - service: notify.telegram_tpm
      data:
        title: "Unknown Person Detected"
        message: >
          Unknown person detected on {{ trigger.payload_json.camera }} camera
          at {{ now().strftime('%H:%M:%S') }}
        data:
          photo:
            - url: "http://frigate:8971/api/events/{{ trigger.payload_json.id }}/snapshot.jpg"
              caption: "Unknown face - {{ trigger.payload_json.camera }}"
```

#### Step 4.4: Test Alert

```bash
# Manually trigger MQTT message
docker exec mosquitto mosquitto_pub \
  -u doubletake -P '<password>' \
  -t 'double-take/matches/unknown' \
  -m '{"camera":"office","id":"test123"}'
```

---

## Phase 5: SAG Dashboard Integration (Jr-Light)

### JR-HA-PHASE5-SAG-INTEGRATION.md

**Objective**: Add Home tab to SAG dashboard with camera feeds

#### Step 5.1: Add Home Tab to SAG

Update SAG frontend to add new "Home" tab with:
- Camera snapshot from Frigate API
- Face recognition status from Double Take
- Recent events feed

#### Step 5.2: API Endpoints

```
Frigate snapshots: http://192.168.132.222:8971/api/<camera>/latest.jpg
Frigate events: http://192.168.132.222:8971/api/events
Double Take matches: http://192.168.132.222:3000/api/matches
```

---

## Verification Checklist

### Phase 1 Complete
- [ ] Docker directories created with correct permissions
- [ ] Mosquitto running with authentication
- [ ] Home Assistant accessible at :8123
- [ ] MQTT integration configured in HA

### Phase 2 Complete
- [ ] NVIDIA runtime working in Docker
- [ ] Frigate accessible at :8971
- [ ] Office camera streaming in Frigate
- [ ] Person detection working
- [ ] Recordings being saved
- [ ] Frigate integration in Home Assistant

### Phase 3 Complete
- [ ] CompreFace accessible at :8000
- [ ] Double Take accessible at :3000
- [ ] CompreFace API key configured
- [ ] TPM face trained
- [ ] Face recognition working on camera

### Phase 4 Complete
- [ ] Telegram bot configured in HA
- [ ] Unknown face automation working
- [ ] Test alert received

### Phase 5 Complete
- [ ] Home tab added to SAG
- [ ] Camera feeds visible in SAG
- [ ] Events synced to thermal memory

---

## Rollback Procedures

### Stop All Services
```bash
cd /ganuda/homeassistant
docker compose down
```

### Remove All Data (Nuclear Option)
```bash
sudo rm -rf /ganuda/homeassistant /ganuda/frigate /ganuda/mosquitto /ganuda/doubletake /ganuda/compreface
```

### Restart Individual Service
```bash
docker restart <service_name>
```

---

## Thermal Memory Archive

After each phase completion:

```sql
INSERT INTO triad_shared_memories (content, temperature, source_triad, tags, access_level)
VALUES (
  'HOME ASSISTANT PHASE X COMPLETE - <details>',
  90, 'it_triad_jr',
  ARRAY['home-assistant', 'infrastructure', 'january-2026'],
  'federation'
);
```

---

## Sources

- https://github.com/HenkVanHoek/frigate-ha-docker-compose
- https://github.com/jakowenko/double-take
- https://github.com/exadel-inc/CompreFace
- https://docs.frigate.video/
- https://www.home-assistant.io/docs/

---

**For Seven Generations.**

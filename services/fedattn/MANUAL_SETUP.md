# FedAttn Coordinator - Manual Systemd Setup

## Current Status
The FedAttn Coordinator is fully functional and tested. It's currently running manually (PID shown in test results).

## To Install Systemd Service (Requires sudo password)

1. Copy the service file to systemd directory:
```bash
sudo cp /tmp/fedattn-coordinator.service /etc/systemd/system/fedattn-coordinator.service
```

2. Reload systemd:
```bash
sudo systemctl daemon-reload
```

3. Enable service for boot:
```bash
sudo systemctl enable fedattn-coordinator.service
```

4. Start the service:
```bash
sudo systemctl start fedattn-coordinator.service
```

5. Check status:
```bash
sudo systemctl status fedattn-coordinator.service
```

## Manual Operation (No sudo required)

### Start Coordinator
```bash
cd /ganuda/services/fedattn
nohup /home/dereadi/cherokee_venv/bin/python -m uvicorn coordinator:app --host 0.0.0.0 --port 8081 > coordinator.log 2>&1 &
```

### Stop Coordinator
```bash
pkill -f 'uvicorn coordinator:app'
```

### Check Status
```bash
curl -s http://localhost:8081/health | jq .
```

### Run Tests
```bash
/ganuda/services/fedattn/test_coordinator.sh
```

## Configuration

- HTTP Port: 8081
- ZMQ Port: 5556 (for KV matrix streaming)
- Database: PostgreSQL on bluefin (100.112.254.96)
- Log file: /ganuda/services/fedattn/coordinator.log

## For Seven Generations
ᏣᎳᎩ ᏲᏫᎢᎶᏗ

# Jr Instruction: Web Analytics via Caddy Access Logs → OpenObserve

**Ticket**: WEB-ANALYTICS-001
**Estimated SP**: 2
**Assigned**: Spider (infrastructure) + Deer (monitoring/reporting)
**Depends On**: None — all infrastructure already deployed
**Priority**: P2 — Nelson Spence LinkedIn comment just went live, need visibility

---

## Objective

Enable visitor tracking for ganuda.us and vetassist.ganuda.us by turning on Caddy structured access logs on owlfin and eaglefin, then shipping them to OpenObserve on greenfin via Promtail. Zero new software. Zero third-party analytics. Data never leaves the federation.

## Current State

- **Caddy** runs on owlfin (192.168.132.170) and eaglefin (192.168.132.84) serving ganuda.us and vetassist.ganuda.us
- **Caddyfile**: `/ganuda/config/Caddyfile-dmz` — no `log` directive, no access logs
- **Promtail**: Runs on redfin only, ships to OpenObserve at `http://100.112.254.96:3100/loki/api/v1/push` (greenfin via Tailscale)
- **OpenObserve**: Running on greenfin:5080, already ingesting SAG, Jr, syslog, auth logs from redfin
- **No Promtail on owlfin or eaglefin** — this needs to be installed

## Implementation

### Step 1: Enable Caddy structured JSON access logs on both DMZ nodes

Update `/ganuda/config/Caddyfile-dmz` to add a global log block and per-site access logging:

```caddy
# Caddyfile — DMZ Web Servers (owlfin/eaglefin)
# Cherokee AI Federation

# Global options
{
	log {
		output file /var/log/caddy/access.log {
			roll_size 50mb
			roll_keep 5
			roll_keep_for 720h
		}
		format json
	}
}

# Ganuda.us - Static Landing Page
ganuda.us {
	root * /home/dereadi/www/ganuda.us
	file_server
	log {
		output file /var/log/caddy/ganuda-access.log {
			roll_size 50mb
			roll_keep 5
			roll_keep_for 720h
		}
		format json
	}
}

www.ganuda.us {
	redir https://ganuda.us{uri} permanent
}

# VetAssist - Reverse proxy to redfin backend
vetassist.ganuda.us {
	handle /api/* {
		reverse_proxy 192.168.132.223:8001 {
			header_up Host {upstream_hostport}
		}
	}

	handle {
		reverse_proxy 192.168.132.223:3000 {
			header_up Host {upstream_hostport}
		}
	}

	log {
		output file /var/log/caddy/vetassist-access.log {
			roll_size 50mb
			roll_keep 5
			roll_keep_for 720h
		}
		format json
	}
}
```

On **both** owlfin and eaglefin:
```bash
sudo mkdir -p /var/log/caddy
sudo chown caddy:caddy /var/log/caddy
```

Deploy the updated Caddyfile and reload:
```bash
sudo cp /ganuda/config/Caddyfile-dmz /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

Verify logs are flowing:
```bash
curl -s https://ganuda.us/ > /dev/null
sleep 2
cat /var/log/caddy/ganuda-access.log | head -1 | python3 -m json.tool
```

You should see JSON with fields: `ts`, `request.remote_ip`, `request.method`, `request.uri`, `request.headers.User-Agent`, `status`, `size`, `duration`, `request.headers.Referer`.

### Step 2: Install Promtail on owlfin and eaglefin

Download the same Promtail binary version running on redfin. Check redfin's version first:

```bash
/ganuda/home/dereadi/promtail/bin/promtail --version
```

On **both** owlfin and eaglefin:

```bash
# Create directories
mkdir -p /home/dereadi/promtail/{bin,config,positions}

# Copy binary from redfin (or download matching version)
scp dereadi@192.168.132.223:/ganuda/home/dereadi/promtail/bin/promtail /home/dereadi/promtail/bin/
chmod +x /home/dereadi/promtail/bin/promtail
```

### Step 3: Create Promtail config for DMZ nodes

Write `/home/dereadi/promtail/config/promtail.yaml` on **both** owlfin and eaglefin:

```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0
  log_level: info

positions:
  filename: /home/dereadi/promtail/positions/positions.yaml

clients:
  - url: http://192.168.132.224:3100/loki/api/v1/push
    timeout: 10s
    backoff_config:
      min_period: 1s
      max_period: 60s
      max_retries: 10

scrape_configs:
  # Caddy Access Logs — ganuda.us
  - job_name: caddy_ganuda
    static_configs:
      - targets:
          - localhost
        labels:
          job: caddy_access
          site: ganuda_us
          node_id: owlfin  # CHANGE TO eaglefin on eaglefin
          tier: web
          __path__: /var/log/caddy/ganuda-access.log

  # Caddy Access Logs — vetassist.ganuda.us
  - job_name: caddy_vetassist
    static_configs:
      - targets:
          - localhost
        labels:
          job: caddy_access
          site: vetassist_ganuda_us
          node_id: owlfin  # CHANGE TO eaglefin on eaglefin
          tier: web
          __path__: /var/log/caddy/vetassist-access.log

  # Caddy Global Log (errors, redirects, etc.)
  - job_name: caddy_global
    static_configs:
      - targets:
          - localhost
        labels:
          job: caddy_global
          node_id: owlfin  # CHANGE TO eaglefin on eaglefin
          tier: web
          __path__: /var/log/caddy/access.log
```

**NOTE**: Use LAN IP `192.168.132.224` for greenfin (not Tailscale) since owlfin/eaglefin are on the same LAN. Verify greenfin port 3100 is accessible from DMZ nodes first:

```bash
curl -s http://192.168.132.224:3100/ready
```

If LAN doesn't work (firewall), fall back to WireGuard: `http://10.100.0.3:3100/loki/api/v1/push`

### Step 4: Create systemd unit for Promtail on DMZ nodes

Write `/etc/systemd/system/promtail.service` on **both** owlfin and eaglefin:

```ini
[Unit]
Description=Promtail Log Forwarder to OpenObserve (DMZ Web Analytics)
After=network-online.target caddy.service
Wants=network-online.target

[Service]
Type=simple
User=dereadi
ExecStart=/home/dereadi/promtail/bin/promtail -config.file=/home/dereadi/promtail/config/promtail.yaml
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable promtail
sudo systemctl start promtail
sudo systemctl status promtail
```

### Step 5: Verify end-to-end pipeline

1. From an external machine (or owlfin itself via curl to the VIP):
```bash
curl -s https://ganuda.us/ > /dev/null
curl -s https://ganuda.us/blog/ > /dev/null
curl -s https://vetassist.ganuda.us/ > /dev/null
```

2. Check Caddy logs on owlfin:
```bash
tail -3 /var/log/caddy/ganuda-access.log | python3 -m json.tool
```

3. Check OpenObserve on greenfin — query for `job=caddy_access` in the web UI at `http://192.168.132.224:5080`

4. Verify you can see: remote IP, path requested, referrer (LinkedIn!), user-agent, response time

### Step 6: Add to Fire Guard health check

In `/ganuda/scripts/fire_guard.py`, add checks for both DMZ Promtail instances:

```python
# DMZ Web Analytics — Promtail on owlfin/eaglefin
{"name": "promtail-owlfin", "url": "http://192.168.132.170:9080/ready", "expected": 200},
{"name": "promtail-eaglefin", "url": "http://192.168.132.84:9080/ready", "expected": 200},
```

## Privacy Considerations

- **No cookies, no JavaScript tracking, no third-party calls** — server-side access logs only
- **IP addresses are logged** but stay inside the federation (OpenObserve on greenfin, LAN only)
- **No PII extraction** — Promtail ships raw log lines, no parsing of form data or POST bodies
- **Caddy JSON format** does NOT log request bodies, only method/path/headers/status/size
- **Retention**: 30 days (720h roll_keep_for) — old logs auto-deleted
- **Consistent with DC-1**: Lazy awareness — logs flow passively, no active tracking scripts

## What NOT To Do

- Do NOT install Google Analytics, Plausible, or any client-side tracker — server logs are sufficient
- Do NOT log request bodies (POST data) — Caddy JSON format doesn't do this by default, don't add it
- Do NOT expose OpenObserve to the internet — greenfin:5080 stays LAN/WireGuard only
- Do NOT ship logs over the public internet — use LAN or WireGuard only
- Do NOT parse or store individual user sessions — we want aggregate traffic, not surveillance

## Verification

1. **Log generation**: `curl ganuda.us` → entry appears in `/var/log/caddy/ganuda-access.log` within 1 second
2. **Log shipping**: Entry appears in OpenObserve `caddy_access` stream within 30 seconds
3. **Both nodes**: Repeat on both owlfin and eaglefin
4. **Referrer tracking**: Click ganuda.us from a Google search or LinkedIn → referrer field populated
5. **Fire Guard**: `promtail-owlfin` and `promtail-eaglefin` show green in necklace health check
6. **Log rotation**: Verify `/var/log/caddy/` doesn't grow past 250MB (5 × 50MB)

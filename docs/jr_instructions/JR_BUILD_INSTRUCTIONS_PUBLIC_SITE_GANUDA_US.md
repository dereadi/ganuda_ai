# Jr Build Instructions: Public Site (ganuda.us)
## Priority: HIGH - Public Face of Cherokee AI Federation

---

## Objective

Create a public-facing website at ganuda.us that serves as the PR/marketing presence for Cherokee AI Federation. This site is **read-only** - no authentication, no control plane access, purely informational.

**Key Principle**: Show what we do, not how to control it.

---

## Architecture: Two Faces

```
┌─────────────────────────────────────────────────────────────────┐
│                     PUBLIC INTERNET                              │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ganuda.us (Public)                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Status Page  │  │ Project      │  │ About Cherokee AI    │   │
│  │ (Live Stats) │  │ Showcase     │  │ Federation           │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  READ-ONLY • NO LOGIN • NO CONTROL                              │
└─────────────────────────────────────────────────────────────────┘
                            │
                            │ (Separate network/VPN)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SAG (Private ITSM)                            │
│                    192.168.132.223:4000                          │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Control Room │  │ Settings     │  │ Messages/Calendar    │   │
│  │ Full Access  │  │ Alerts       │  │ IoT Control          │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  AUTHENTICATED • FULL CONTROL • INTERNAL ONLY                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Public Site Features

### 1. Hero Section
- Cherokee AI Federation branding
- Tagline: "AI Infrastructure Built for Seven Generations"
- Brief description of what we do

### 2. Live Status Dashboard (Read-Only)
Pull stats from internal APIs but display only:

| Metric | Source | Display |
|--------|--------|---------|
| System Uptime | `/health` endpoint | "99.9% uptime" |
| Current Model | Gateway config | "Nemotron-9B" |
| Inference Speed | Benchmark data | "27 tokens/sec" |
| Total Requests | `api_audit_log` count | "1.2M requests served" |
| Node Health | Node ping status | Green/Yellow/Red dots |

**Security**: Only aggregate stats, no sensitive data exposed.

### 3. Current Project Showcase
Display from a curated project list:
- Project name and description
- Status (In Progress / Completed)
- Technologies used
- Screenshots/diagrams (optional)

Pull from: `/ganuda/docs/projects/` or a simple JSON file.

### 4. About Section
- What is Cherokee AI Federation
- The 7-Specialist Council (high-level)
- Seven Generations philosophy
- Team/Contact info

### 5. Performance Capacity Card
Public version of our internal metrics:

```
┌────────────────────────────────────────────────┐
│         CHEROKEE AI FEDERATION                  │
│         Infrastructure Status                   │
├────────────────────────────────────────────────┤
│  Active Nodes:        6                        │
│  GPU Inference:       96GB Blackwell           │
│  Model:               Nemotron-9B              │
│  Throughput:          27 tokens/sec            │
│  Avg Latency:         <500ms                   │
│  Uptime (30d):        99.9%                    │
└────────────────────────────────────────────────┘
```

---

## Technical Implementation

### Option A: Static Site with API Polling (Recommended)

Simple, secure, easy to host.

**Stack:**
- HTML/CSS/JavaScript (no framework needed)
- Fetch stats from a dedicated public API endpoint
- Host on any static host (GitHub Pages, Cloudflare Pages, or nginx on greenfin)

**File Structure:**
```
/ganuda/public_site/
├── index.html
├── css/
│   └── style.css
├── js/
│   └── main.js
├── images/
│   └── logo.svg
└── data/
    └── projects.json
```

### Option B: Flask App (More Dynamic)

If we want server-side rendering or more complex features.

**Location:** `/home/dereadi/ganuda_public_site/`

```python
# app.py - Public site (separate from SAG)
from flask import Flask, render_template, jsonify
import requests

app = Flask(__name__)

# Public stats endpoint - SANITIZED DATA ONLY
@app.route("/api/public/stats")
def public_stats():
    """Return only safe, aggregate statistics"""
    try:
        # Get health from internal gateway
        health = requests.get("http://localhost:8080/health", timeout=5).json()

        # Get request count from database (aggregate only)
        # ... sanitized query ...

        return jsonify({
            "status": "operational",
            "uptime_percent": 99.9,
            "model": "Nemotron-9B",
            "throughput_tokens_sec": 27,
            "nodes_healthy": 6,
            "total_requests": 1234567  # Aggregate, not real-time
        })
    except:
        return jsonify({"status": "unknown"})

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/projects")
def projects():
    return render_template("projects.html")

@app.route("/about")
def about():
    return render_template("about.html")
```

---

## Public API Endpoint (Safe Stats)

Add to LLM Gateway or create separate service:

```python
# In gateway.py or separate public_api.py

@app.route("/v1/public/status")
def public_status():
    """
    Public-safe status endpoint.
    NO authentication required.
    Returns ONLY aggregate, non-sensitive data.
    """
    return jsonify({
        "federation": "Cherokee AI",
        "status": "operational",
        "infrastructure": {
            "nodes": 6,
            "gpu_vram_gb": 96,
            "model": "Nemotron-9B"
        },
        "performance": {
            "throughput_tokens_sec": 27,
            "avg_latency_ms": 450,
            "uptime_30d_percent": 99.9
        },
        "last_updated": datetime.utcnow().isoformat()
    })
```

**Security Rules for Public API:**
- NO user data
- NO API keys or auth info
- NO IP addresses or internal IPs
- NO real-time request logs
- NO configuration details
- ONLY aggregate statistics

---

## Design Guidelines

### Visual Style
- Clean, minimal, professional
- Cherokee-inspired color palette (earth tones, turquoise accents)
- Dark mode default (matches SAG internal UI)
- Mobile responsive

### Color Palette
```css
:root {
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --text-primary: #e6edf3;
    --text-secondary: #8b949e;
    --accent-turquoise: #2dd4bf;
    --accent-gold: #f59e0b;
    --status-green: #22c55e;
    --status-yellow: #eab308;
    --status-red: #ef4444;
}
```

### Typography
- Headers: System font stack (clean, fast loading)
- Body: 16px minimum for readability
- Code/Stats: Monospace for technical data

---

## Sample HTML Structure

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cherokee AI Federation | ganuda.us</title>
    <link rel="stylesheet" href="/css/style.css">
</head>
<body>
    <header class="hero">
        <nav>
            <a href="/" class="logo">Cherokee AI Federation</a>
            <div class="nav-links">
                <a href="#status">Status</a>
                <a href="#projects">Projects</a>
                <a href="#about">About</a>
            </div>
        </nav>
        <div class="hero-content">
            <h1>AI Infrastructure Built for Seven Generations</h1>
            <p>Private, sovereign AI inference for organizations that value trust and longevity.</p>
        </div>
    </header>

    <section id="status" class="status-section">
        <h2>System Status</h2>
        <div class="status-grid">
            <div class="status-card">
                <span class="status-indicator green"></span>
                <span class="status-label">All Systems Operational</span>
            </div>
            <div class="stats-grid" id="live-stats">
                <!-- Populated by JavaScript -->
            </div>
        </div>
        <div class="capacity-card" id="capacity-card">
            <!-- Capacity card populated here -->
        </div>
    </section>

    <section id="projects" class="projects-section">
        <h2>Current Projects</h2>
        <div class="project-grid" id="project-grid">
            <!-- Projects populated by JavaScript -->
        </div>
    </section>

    <section id="about" class="about-section">
        <h2>About Cherokee AI Federation</h2>
        <div class="about-content">
            <p>Cherokee AI Federation is a distributed AI infrastructure built on Cherokee principles of consensus, sustainability, and long-term thinking.</p>
            <h3>Our Approach</h3>
            <ul>
                <li><strong>7-Specialist Council</strong> - Decisions made through AI consensus, not single-model autocracy</li>
                <li><strong>Seven Generations</strong> - Every decision validated against 175-year impact</li>
                <li><strong>Thermal Memory</strong> - Institutional knowledge that never forgets</li>
                <li><strong>Private by Default</strong> - Your data stays yours</li>
            </ul>
        </div>
    </section>

    <footer>
        <p>For Seven Generations</p>
        <p>&copy; 2025 Cherokee AI Federation</p>
    </footer>

    <script src="/js/main.js"></script>
</body>
</html>
```

---

## JavaScript for Live Stats

```javascript
// main.js - Public site JavaScript

document.addEventListener("DOMContentLoaded", function() {
    loadPublicStats();
    loadProjects();

    // Refresh stats every 60 seconds
    setInterval(loadPublicStats, 60000);
});

function loadPublicStats() {
    fetch("/api/public/stats")
        .then(function(r) { return r.json(); })
        .then(function(data) {
            renderStats(data);
            renderCapacityCard(data);
        })
        .catch(function(err) {
            console.log("Stats unavailable");
            renderOfflineState();
        });
}

function renderStats(data) {
    var statsGrid = document.getElementById("live-stats");
    if (!statsGrid) return;

    statsGrid.innerHTML =
        '<div class="stat-item">' +
        '<span class="stat-value">' + data.infrastructure.nodes + '</span>' +
        '<span class="stat-label">Active Nodes</span>' +
        '</div>' +
        '<div class="stat-item">' +
        '<span class="stat-value">' + data.performance.throughput_tokens_sec + '</span>' +
        '<span class="stat-label">Tokens/sec</span>' +
        '</div>' +
        '<div class="stat-item">' +
        '<span class="stat-value">' + data.performance.uptime_30d_percent + '%</span>' +
        '<span class="stat-label">Uptime (30d)</span>' +
        '</div>' +
        '<div class="stat-item">' +
        '<span class="stat-value">' + data.infrastructure.gpu_vram_gb + 'GB</span>' +
        '<span class="stat-label">GPU VRAM</span>' +
        '</div>';
}

function renderCapacityCard(data) {
    var card = document.getElementById("capacity-card");
    if (!card) return;

    card.innerHTML =
        '<div class="capacity-header">Infrastructure Capacity</div>' +
        '<table class="capacity-table">' +
        '<tr><td>Model</td><td>' + data.infrastructure.model + '</td></tr>' +
        '<tr><td>GPU Memory</td><td>' + data.infrastructure.gpu_vram_gb + ' GB</td></tr>' +
        '<tr><td>Throughput</td><td>' + data.performance.throughput_tokens_sec + ' tokens/sec</td></tr>' +
        '<tr><td>Avg Latency</td><td>' + data.performance.avg_latency_ms + ' ms</td></tr>' +
        '<tr><td>30-Day Uptime</td><td>' + data.performance.uptime_30d_percent + '%</td></tr>' +
        '</table>';
}

function loadProjects() {
    fetch("/data/projects.json")
        .then(function(r) { return r.json(); })
        .then(function(projects) {
            renderProjects(projects);
        });
}

function renderProjects(projects) {
    var grid = document.getElementById("project-grid");
    if (!grid) return;

    var html = "";
    projects.forEach(function(project) {
        html +=
            '<div class="project-card">' +
            '<h3>' + project.name + '</h3>' +
            '<span class="project-status ' + project.status.toLowerCase().replace(' ', '-') + '">' + project.status + '</span>' +
            '<p>' + project.description + '</p>' +
            '<div class="project-tech">' + project.technologies.join(" • ") + '</div>' +
            '</div>';
    });

    grid.innerHTML = html;
}

function renderOfflineState() {
    var statsGrid = document.getElementById("live-stats");
    if (statsGrid) {
        statsGrid.innerHTML = '<div class="stat-item offline">Stats temporarily unavailable</div>';
    }
}
```

---

## Projects Data File

```json
// /data/projects.json
[
    {
        "name": "SAG Unified Interface",
        "status": "In Progress",
        "description": "Control room for Cherokee AI Federation operations. Unified dashboard for monitoring, messaging, calendar, and IoT management.",
        "technologies": ["Python", "Flask", "JavaScript", "Redis"]
    },
    {
        "name": "LLM Gateway v1.1",
        "status": "Complete",
        "description": "OpenAI-compatible inference gateway with 7-Specialist Council voting and thermal memory integration.",
        "technologies": ["Python", "FastAPI", "vLLM", "PostgreSQL"]
    },
    {
        "name": "Thermal Memory System",
        "status": "Complete",
        "description": "Persistent AI memory with temperature-based decay. Ensures institutional knowledge persists across sessions.",
        "technologies": ["PostgreSQL", "Python", "Cron"]
    },
    {
        "name": "Fractal Stigmergic Encryption",
        "status": "In Progress",
        "description": "Novel encryption where keys evolve through usage patterns like ant pheromone trails.",
        "technologies": ["Python", "Cryptography"]
    }
]
```

---

## Hosting Options

### Option 1: Nginx on greenfin (Recommended)
- Internal hosting, full control
- Configure nginx reverse proxy
- Add Let's Encrypt for HTTPS

```nginx
# /etc/nginx/sites-available/ganuda.us
server {
    listen 80;
    server_name ganuda.us www.ganuda.us;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name ganuda.us www.ganuda.us;

    ssl_certificate /etc/letsencrypt/live/ganuda.us/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ganuda.us/privkey.pem;

    root /ganuda/public_site;
    index index.html;

    # Proxy API requests to internal service
    location /api/public/ {
        proxy_pass http://192.168.132.223:8080/v1/public/;
        proxy_set_header Host $host;
    }

    location / {
        try_files $uri $uri/ =404;
    }
}
```

### Option 2: Cloudflare Pages
- Free hosting
- Global CDN
- Automatic HTTPS
- API calls would go to a separate worker or exposed endpoint

### Option 3: GitHub Pages
- Free, simple
- No server-side code
- Would need CORS-enabled public API endpoint

---

## Security Checklist

- [ ] Public API exposes ONLY aggregate statistics
- [ ] No authentication tokens in public responses
- [ ] No internal IP addresses exposed
- [ ] No user data or PII
- [ ] No configuration details
- [ ] Rate limiting on public API (prevent abuse)
- [ ] HTTPS enforced
- [ ] No admin/control functionality
- [ ] CSP headers configured
- [ ] No links to internal SAG UI

---

## Deployment Steps

1. **Create public site files** on greenfin or chosen host
2. **Configure nginx** with SSL (Let's Encrypt)
3. **Add public API endpoint** to gateway (sanitized stats only)
4. **Update DNS** for ganuda.us to point to host
5. **Test thoroughly** - ensure no sensitive data leaks
6. **Monitor** access logs for abuse

---

## Success Criteria

1. ✅ ganuda.us loads with professional appearance
2. ✅ Live stats update without authentication
3. ✅ Projects showcase current work
4. ✅ No sensitive data exposed
5. ✅ Mobile responsive
6. ✅ HTTPS enforced
7. ✅ Page loads in < 2 seconds

---

*For Seven Generations*

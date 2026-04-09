# Jr Build Instruction: Desktop Security Canary — "Is Your Machine Safe?"

## Priority: P1 — MOCHA Product Sprint, Product #2
## Date: April 3, 2026
## Requested By: Partner + TPM
## Target: Ship in 2-3 days. Product Hunt after Trimmer polish.

---

## What We're Building

A lightweight desktop security scanner that runs locally and tells you what's wrong with your machine. No cloud. No subscription. No sending your security data to a third party.

**Think of it as Fire Guard for your laptop.**

Drop it on any machine, run it, get a clean report: open ports, exposed credentials, running services you forgot about, weak configs, and what to fix.

## Why This Is Low-Hanging Fruit

We already have:
- **Fire Guard** — runs every 2 min on the cluster, checks ports, services, timers, connections, DB health, RSS memory, emergency brake
- **Safety Canary** — daily adversarial tests, probes for vulnerabilities
- **Credential Scanner** — weekly scan for exposed secrets, hardcoded passwords
- The logic exists. We just package it for a SINGLE MACHINE instead of a federation.

## Architecture

```
Run scanner → Check ports → Check creds → Check services → Check configs → LLM analysis → Report

1. PORT SCAN: What's listening on this machine? What's exposed to the network?
2. CREDENTIAL SCAN: Search common locations for exposed secrets (.env, .git, config files, shell history)
3. SERVICE AUDIT: What's running? What auto-starts? Any services you don't recognize?
4. CONFIG CHECK: SSH config, firewall status, sudo permissions, disk encryption, auto-updates
5. NETWORK CHECK: Open connections, DNS leakage, unexpected outbound traffic
6. LLM ANALYSIS: Send findings to local LLM for risk assessment and plain-English recommendations
7. REPORT: Clean HTML report with severity ratings (critical/warning/info) and fix commands
```

## Phase 1: Scanner Core (Day 1)

### Task 1A: Port Scanner

Build `/ganuda/products/security-canary/port_scanner.py`:

- Scan localhost for all listening ports (TCP + UDP)
- For each port: identify the process, PID, user running it
- Flag known-risky ports (21/FTP, 23/telnet, 3389/RDP, 5900/VNC, etc.)
- Flag ports listening on 0.0.0.0 (exposed to network) vs 127.0.0.1 (local only)
- Cross-reference against a known-services list

### Task 1B: Credential Scanner

Build `/ganuda/products/security-canary/cred_scanner.py`:

- Search home directory for exposed credentials:
  - `.env` files with passwords/tokens
  - `.git/config` with hardcoded credentials
  - Shell history (`.bash_history`, `.zsh_history`) containing passwords
  - SSH keys without passphrases
  - AWS/GCP/Azure credential files
  - `.netrc`, `.pgpass`, `.my.cnf` with passwords
  - Kubernetes configs with embedded tokens
- Pattern match: `password=`, `token=`, `secret=`, `api_key=`, AWS key patterns, JWT tokens
- Report location, type, and severity — NOT the actual credential content

### Task 1C: Service Auditor

Build `/ganuda/products/security-canary/service_auditor.py`:

- List all running services (systemd on Linux, launchctl on macOS)
- Flag services running as root that shouldn't be
- Flag auto-starting services the user may not recognize
- Check for known-vulnerable service versions if version is detectable
- Check Docker/Podman containers if running

### Task 1D: Config Checker

Build `/ganuda/products/security-canary/config_checker.py`:

- SSH: PasswordAuthentication, PermitRootLogin, key-only auth
- Firewall: UFW/iptables status (enabled/disabled, rules count)
- Sudo: NOPASSWD entries, sudoers config
- Disk encryption: LUKS/FileVault status
- Auto-updates: unattended-upgrades status
- Screen lock: timeout configured?

### Task 1E: Network Checker

Build `/ganuda/products/security-canary/network_checker.py`:

- Active outbound connections (what's your machine talking to?)
- DNS configuration (using encrypted DNS?)
- VPN/WireGuard status
- ARP table (any unexpected devices on your LAN?)
- Check for open Wi-Fi connections

## Phase 2: LLM Analysis + Report (Day 2)

### Task 2A: LLM Risk Analyzer

Build `/ganuda/products/security-canary/analyzer.py`:

- Collect all scanner results
- Send to local vLLM with structured prompt:
  "Analyze these security findings. For each, rate severity (critical/warning/info), explain the risk in plain English, and provide the exact command to fix it."
- Parse structured JSON response
- No PII or actual credentials sent to LLM — only finding types and locations

### Task 2B: HTML Report Generator

Build `/ganuda/products/security-canary/report.py`:

- Generate a clean, single-file HTML report (no external deps)
- Match ganuda.us dark theme styling
- Sections: Summary (score card), Critical Findings, Warnings, Info, Fix Commands
- Each finding: severity badge, description, risk explanation, fix command (copy-pasteable)
- Footer: "Scanned locally by Desktop Security Canary. No data left this machine."
- Save as `security-report-YYYY-MM-DD.html`

### Task 2C: CLI Runner

Build `/ganuda/products/security-canary/canary.py`:

```bash
# Usage
python3 canary.py                    # Full scan, generate HTML report
python3 canary.py --quick            # Port scan + cred scan only (30 seconds)
python3 canary.py --no-llm           # Skip LLM analysis (works without vLLM)
python3 canary.py --output report.html  # Custom output path
```

## Phase 3: Deploy + Launch (Day 3)

### Task 3A: Web Dashboard on DMZ

- FastAPI serving the report at ganuda.us/canary
- Demo: pre-scanned report from Partner's machine (sanitized)
- API: POST /scan endpoint (local only, not public — security tool shouldn't be remotely triggerable)

### Task 3B: GitHub Repo

- dereadi/desktop-security-canary
- README with screenshots of the report
- "No cloud. No subscription. Your security data stays on YOUR machine."
- MIT license

### Task 3C: Substack + LinkedIn

- Blog post: "I Built a Desktop Security Scanner That Doesn't Phone Home"
- LinkedIn post with report screenshot
- Comment on David Matousek's Mythos security post (he's in your feed)

## Technical Constraints

- **Cross-platform**: Linux primary, macOS secondary. Windows later.
- **No root required for basic scan**: Port scan + cred scan work as regular user. Service audit + config check need sudo for full results.
- **No network required**: Everything runs locally. LLM analysis is optional (--no-llm flag).
- **No dependencies beyond stdlib for core**: Only needs `requests` for LLM analysis. Core scanners use `socket`, `subprocess`, `os`, `re`, `pathlib`.
- **NEVER log actual credentials**: Report says "found AWS key in ~/.env at line 14" — NOT the actual key.
- **Crawdad audit required**: Security tool must be reviewed by security specialist before public release.

## Why This Wins

1. **Mythos timing**: Everyone is panicking about AI finding vulnerabilities. This tool lets you find YOUR OWN vulnerabilities first.
2. **Privacy story**: "Unlike cloud security scanners, your data never leaves your machine."
3. **Upwork pipeline**: Direct demo for both security consulting gigs. "Here's the tool I'd run on your infrastructure."
4. **David Matousek connection**: He posted about scanning codebases with AI today. Comment with your canary.
5. **Nate's 12 primitives**: Primitive #2 is permission/security. Primitive #8 is verification. This tool IS those primitives packaged for anyone.
6. **Open source**: Builds GitHub profile, drives stars, fills the portfolio gap.

## Success Criteria

- [ ] Port scanner identifies all listening services
- [ ] Credential scanner finds exposed secrets without logging them
- [ ] Service auditor flags unexpected/risky services
- [ ] Config checker verifies SSH, firewall, encryption, sudo
- [ ] Network checker shows outbound connections and DNS config
- [ ] LLM analyzer provides plain-English risk assessment with fix commands
- [ ] HTML report is clean, professional, and self-contained
- [ ] CLI works with --quick and --no-llm flags
- [ ] Demo deployed at ganuda.us/canary
- [ ] Open sourced on GitHub
- [ ] Crawdad audit passed

---

*"If you aren't scanning your own systems with AI today, you're leaving your threat surface open to discovery by someone who is." — David Matousek, LinkedIn, Apr 3 2026*

*We built the tool. It runs on your machine. It stays on your machine.*

*For Seven Generations.*

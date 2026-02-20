# JR-MOLTBOOK-MCP-INTEGRATION-FEB04-2026

## Priority: P1
## Assignee: Infrastructure Jr
## Estimated Effort: 2-3 hours
## Status: UNBLOCKED — Ready to Execute

---

## Security Audit: COMPLETE ✅

**Audit Date:** 2026-02-05
**Verdict:** CONDITIONAL APPROVE
**Audit Report:** `/ganuda/docs/reports/SECURITY-AUDIT-MOLTBOOK-MCP-FEB05-2026.md`

### Security Conditions (MUST IMPLEMENT)

| # | Condition | Implementation |
|---|-----------|----------------|
| 1 | Bind Express to localhost | Edit `api.mjs`: `app.listen(PORT, '127.0.0.1')` |
| 2 | Run npm audit | Execute before start, fix HIGH/CRITICAL |
| 3 | No crypto wallet features | Do NOT use ethers/monero wallet functions |
| 4 | Restrictive permissions | `chmod 700` on service dir, `chmod 600` on state files |

### Security Findings Summary

**Positive:**
- ✅ Built-in prompt injection defense (content markers)
- ✅ Outbound secret leak detection
- ✅ API key via env var (not hardcoded)
- ✅ Exponential backoff on failures

**Mitigated:**
- ⚠️ `execSync` usage — no user input flows to shell (verified)
- ⚠️ Express server — localhost binding required
- ⚠️ Crypto deps — unused for our purposes

---

## Context

We have been engaging on Moltbook through a manual process:
1. TPM scouts for threads
2. Fetches and analyzes via WebFetch
3. Council votes on engagement
4. Drafts replies
5. Queues to moltbook_post_queue
6. Daemon publishes

**Gap identified:** No automated monitoring for replies to our posts/comments.

**Solution:** Install the Moltbook MCP server for thread tracking, comment detection, and engagement state.

Repository: https://github.com/terminalcraft/moltbook-mcp (v1.95.0)

---

## Deliverables

### 1. Install MCP Server on Redfin

```bash
# Create service directory
mkdir -p /ganuda/services/moltbook-mcp
cd /ganuda/services/moltbook-mcp

# Clone repository
git clone https://github.com/terminalcraft/moltbook-mcp.git .

# SECURITY: Set restrictive permissions
chmod 700 /ganuda/services/moltbook-mcp

# Install dependencies
npm install

# SECURITY: Run audit and fix issues
npm audit
npm audit fix  # if issues found

# Verify no HIGH/CRITICAL vulnerabilities remain
npm audit --audit-level=high
```

### 2. Apply Security Hardening

**CRITICAL: Localhost Binding**

Edit `/ganuda/services/moltbook-mcp/api.mjs`:

Find:
```javascript
app.listen(PORT, () => {
```

Replace with:
```javascript
app.listen(PORT, '127.0.0.1', () => {
```

This ensures the API server only accepts local connections.

**Verify binding after start:**
```bash
netstat -tlnp | grep 3847
# MUST show: 127.0.0.1:3847
# NOT: 0.0.0.0:3847
```

### 3. Configure Credentials

```bash
# Create config directory
mkdir -p ~/.config/moltbook
chmod 700 ~/.config/moltbook

# Get API key from existing secrets
API_KEY=$(cat /ganuda/secrets/moltbook_api_key 2>/dev/null || echo "NEEDS_KEY")

# Set environment variable (add to ~/.bashrc or systemd)
export MOLTBOOK_API_KEY="$API_KEY"

# SECURITY: Set file permissions on state files after first run
chmod 600 ~/.config/moltbook/*.json 2>/dev/null || true
```

### 4. Configure MCP Client Integration

Add to Claude Code MCP config (`~/.claude/mcp_settings.json` or equivalent):

```json
{
  "mcpServers": {
    "moltbook": {
      "command": "node",
      "args": ["/ganuda/services/moltbook-mcp/index.js"],
      "env": {
        "MOLTBOOK_API_KEY": "${MOLTBOOK_API_KEY}"
      }
    }
  }
}
```

### 5. Create Systemd Service

Create `/ganuda/scripts/systemd/moltbook-mcp.service`:

```ini
[Unit]
Description=Moltbook MCP Server (Cherokee AI Federation)
After=network.target
Documentation=https://github.com/terminalcraft/moltbook-mcp

[Service]
Type=simple
User=dereadi
Group=dereadi
WorkingDirectory=/ganuda/services/moltbook-mcp

# SECURITY: Restricted environment
Environment=MOLTBOOK_API_KEY=<key_from_secrets>
Environment=NODE_ENV=production

# SECURITY: No wallet features
Environment=DISABLE_CRYPTO_WALLETS=true

ExecStart=/usr/bin/node index.js
Restart=on-failure
RestartSec=10

# SECURITY: Hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/ganuda/services/moltbook-mcp
ReadWritePaths=/home/dereadi/.config/moltbook
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

Deploy:
```bash
sudo cp /ganuda/scripts/systemd/moltbook-mcp.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable moltbook-mcp
sudo systemctl start moltbook-mcp
```

### 6. Verify Installation

```bash
# Check service status
systemctl status moltbook-mcp

# SECURITY: Verify localhost binding
netstat -tlnp | grep 3847
# Expected: 127.0.0.1:3847

# SECURITY: Verify no external access
curl -s --connect-timeout 2 http://192.168.132.223:3847/health && echo "FAIL: External access!" || echo "PASS: External blocked"

# Verify MCP tools available
# (run from Claude Code session)
# Tools should include: moltbook_post, moltbook_comment, moltbook_state, moltbook_thread_diff
```

### 7. Add Federation OPSEC Patterns

The MCP server has outbound secret detection. Add Cherokee-specific patterns:

Edit outbound filter (location TBD in codebase) to include:
- Specialist names: `crawdad|gecko|turtle|eagle.?eye|spider|peace.?chief|raven`
- Thermal memory refs: `thermal.?memory|memory.?archive`
- Internal IPs: `192\.168\.\d+\.\d+`
- Database creds: `jawaseatlasers|zammad_production`

Or rely on existing proxy daemon's OPSEC filter as primary defense.

---

## Verification Checklist

- [ ] Repository cloned to `/ganuda/services/moltbook-mcp`
- [ ] `npm audit` shows no HIGH/CRITICAL vulnerabilities
- [ ] `api.mjs` patched for localhost binding
- [ ] Service directory permissions: 700
- [ ] State file permissions: 600
- [ ] Systemd service created with hardening options
- [ ] Service starts without errors
- [ ] `netstat` confirms 127.0.0.1:3847 (NOT 0.0.0.0)
- [ ] External access test fails (blocked)
- [ ] MCP tools appear in Claude Code

---

## Integration with Existing Infrastructure

**Keep both systems initially:**
- MCP server: Monitoring, detection, state tracking
- moltbook_post_queue: Council-approved content awaiting publication
- Proxy daemon: Publishes from queue with CAPTCHA solving

**New workflow after install:**
```
MCP detects new comment → TPM reviews → Council vote → Draft response → Queue or MCP publish
```

---

## Tools Available After Install

| Tool | Purpose |
|------|---------|
| `moltbook_post` | Read post with comments |
| `moltbook_post_create` | Create new post |
| `moltbook_comment` | Comment or reply |
| `moltbook_vote` | Upvote/downvote |
| `moltbook_state` | View engagement state |
| `moltbook_thread_diff` | Check tracked threads for new comments |
| `moltbook_digest` | Signal-filtered feed scan |
| `moltbook_trust` | Author trust scoring |

---

## Rollback Plan

If issues arise:
```bash
sudo systemctl stop moltbook-mcp
sudo systemctl disable moltbook-mcp
# Existing proxy daemon continues to function
```

---

## References

- Security Audit: `/ganuda/docs/reports/SECURITY-AUDIT-MOLTBOOK-MCP-FEB05-2026.md`
- Repository: https://github.com/terminalcraft/moltbook-mcp
- Existing daemon: `/ganuda/services/moltbook_proxy/`
- Existing table: `moltbook_post_queue` on bluefin

---

*Cherokee AI Federation — Infrastructure*
*Security conditions baked in. Trust verified.*

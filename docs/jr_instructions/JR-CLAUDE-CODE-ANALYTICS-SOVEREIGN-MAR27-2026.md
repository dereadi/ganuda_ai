# JR INSTRUCTION: Sovereign Claude Code Analytics — ShipCard Fork

**Task ID**: CC-ANALYTICS-001
**Priority**: P2
**SP**: 5
**Method**: Long Man (3 waves)
**Inspiration**: github.com/jjaimealeman/shipcard (MIT license). We keep the parser logic, replace the cloud with our own infrastructure.

## The Problem

We run Claude Code heavily across multiple nodes (redfin, bmasass, sasass, sasass2) but have zero visibility into:
- How many tokens we burn per day/week/project
- Cost breakdown by model (Opus vs Sonnet vs Haiku)
- Which tools get used most (Bash, Read, Edit, Agent, etc.)
- Per-project token spend
- Session count and duration patterns

Claude Code writes detailed JSONL logs to `~/.claude/projects/` on every node. The data is already there — we just need to collect and visualize it.

ShipCard (github.com/jjaimealeman/shipcard) solved the parsing problem. We fork the parser logic, replace Cloudflare with PostgreSQL + FastAPI, and add multi-node collection.

## Architecture

```
[redfin]  ~/.claude/projects/**/*.jsonl  →  parser  →  POST /api/stats  →  [redfin FastAPI :9500]
[bmasass] ~/.claude/projects/**/*.jsonl  →  parser  →  POST /api/stats  →  [redfin FastAPI :9500]
[sasass]  ~/.claude/projects/**/*.jsonl  →  parser  →  POST /api/stats  →  [redfin FastAPI :9500]
[sasass2] ~/.claude/projects/**/*.jsonl  →  parser  →  POST /api/stats  →  [redfin FastAPI :9500]

[redfin FastAPI :9500]  →  PostgreSQL on bluefin (claude_code_analytics table)
                        →  GET /dashboard (HTML dashboard)
                        →  GET /api/summary (JSON for integrations)
```

## Wave 1: Parser (2 SP)

Port the ShipCard parser logic to Python. Key files to study in the original repo:
- `shiplog/src/parser/schema.ts` — JSONL entry type definitions
- `shiplog/src/parser/deduplicator.ts` — two-level dedup (UUID across files, message.id for streaming chunks)
- `shiplog/src/parser/reader.ts` — file discovery and streaming
- `shiplog/src/engine/aggregator.ts` — analytics aggregation
- `shiplog/src/engine/cost.ts` — LiteLLM pricing with tiered calculation

**File**: `/ganuda/scripts/claude_code_analytics_parser.py`

### JSONL Schema

Each line in the JSONL files is a JSON object. Two types matter:

```python
# User message entry
{
    "type": "user",
    "cwd": "/ganuda",
    "sessionId": "uuid",
    "version": "1.0.x"
}

# Assistant message entry
{
    "type": "assistant",
    "sessionId": "uuid",
    "timestamp": "2026-03-27T...",
    "isSidechain": false,
    "message": {
        "id": "msg_xxx",
        "model": "claude-opus-4-6",
        "usage": {
            "input_tokens": 12345,
            "output_tokens": 6789,
            "cache_creation_input_tokens": 1000,
            "cache_read_input_tokens": 5000
        },
        "content": [
            {"type": "text", "text": "..."},
            {"type": "tool_use", "name": "Bash", ...}
        ]
    }
}
```

### Parser Requirements

1. **Discovery**: Glob `~/.claude/projects/**/*.jsonl` recursively
2. **Streaming read**: Process line-by-line (files can be large)
3. **Deduplication Level 1**: Track UUIDs across files (same message can appear in multiple JSONL files)
4. **Deduplication Level 2**: For same `message.id`, keep only the entry with highest `output_tokens` (streaming chunks)
5. **Extract per message**:
   - `session_id`, `timestamp`, `model`
   - `tokens_input`, `tokens_output`, `tokens_cache_create`, `tokens_cache_read`
   - `tool_calls` — list of tool names from content blocks where `type == "tool_use"`
   - `project` — derive from the JSONL file path (the project directory name)
   - `is_sidechain` — boolean
6. **Aggregate**:
   - Total sessions, tokens, estimated cost
   - Per-project breakdown
   - Per-model breakdown
   - Tool call frequency histogram
   - Date range

### Cost Calculation

Use Anthropic's published pricing (as of Mar 2026):

```python
PRICING = {
    "claude-opus-4-6": {"input": 15.0, "output": 75.0, "cache_create": 18.75, "cache_read": 1.50},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_create": 3.75, "cache_read": 0.30},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0, "cache_create": 1.0, "cache_read": 0.08},
}
# All prices per 1M tokens
```

### Output

The parser should produce a JSON blob like:

```python
{
    "node": "redfin",
    "collected_at": "2026-03-27T...",
    "total_sessions": 142,
    "total_tokens": {"input": 5000000, "output": 1200000, "cache_create": 800000, "cache_read": 3000000},
    "total_cost_usd": 47.20,
    "models": {"claude-opus-4-6": {"sessions": 80, "tokens": {...}, "cost": 42.0}, ...},
    "projects": {"ganuda": {"sessions": 120, "tokens": {...}, "cost": 40.0}, ...},
    "tool_calls": {"Bash": 420, "Read": 311, "Edit": 205, "Agent": 89, ...},
    "date_range": {"earliest": "2026-01-01", "latest": "2026-03-27"},
    "file_count": 1258
}
```

### CLI Usage

```bash
# Parse and print summary
python3 /ganuda/scripts/claude_code_analytics_parser.py

# Parse and POST to API
python3 /ganuda/scripts/claude_code_analytics_parser.py --post http://localhost:9500/api/stats

# Parse specific directory
python3 /ganuda/scripts/claude_code_analytics_parser.py --projects-dir /home/dereadi/.claude/projects
```

## Wave 2: API + Database (2 SP)

### Database Table

**Database**: `zammad_production` on bluefin (or new `claude_analytics` DB if preferred)

```sql
CREATE TABLE claude_code_stats (
    id SERIAL PRIMARY KEY,
    node VARCHAR(50) NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    total_sessions INTEGER,
    tokens_input BIGINT,
    tokens_output BIGINT,
    tokens_cache_create BIGINT,
    tokens_cache_read BIGINT,
    total_cost_usd NUMERIC(10,2),
    models JSONB,         -- per-model breakdown
    projects JSONB,       -- per-project breakdown
    tool_calls JSONB,     -- tool call histogram
    date_range JSONB,     -- {earliest, latest}
    file_count INTEGER,
    raw_stats JSONB       -- full parser output for future use
);

CREATE INDEX idx_cc_stats_node ON claude_code_stats (node);
CREATE INDEX idx_cc_stats_collected ON claude_code_stats (collected_at DESC);
```

### FastAPI Service

**File**: `/ganuda/services/claude_analytics/analytics_api.py`
**Port**: 9500 (LAN-only, no DMZ exposure)

```
POST /api/stats       — Accept parser output JSON, store in DB
GET  /api/summary     — Aggregate across all nodes, return JSON
GET  /api/node/:name  — Per-node latest stats
GET  /dashboard       — HTML dashboard (Jinja2 template)
```

### Systemd Service

**File**: `/etc/systemd/system/claude-analytics.service`

```ini
[Unit]
Description=Claude Code Analytics API — Sovereign ShipCard
After=network-online.target

[Service]
Type=simple
User=dereadi
WorkingDirectory=/ganuda/services/claude_analytics
ExecStart=/home/dereadi/cherokee_venv/bin/python3 analytics_api.py
Environment=HOME=/home/dereadi
Environment=PYTHONPATH=/ganuda:/ganuda/lib
EnvironmentFile=/ganuda/config/secrets.env
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Wave 3: Multi-Node Collection + Dashboard (1 SP)

### Collection Timer on Each Node

On redfin (systemd):
```ini
[Timer]
OnCalendar=*-*-* 06:00:00
Persistent=true
```

On Mac nodes (launchd plist or cron):
```bash
# crontab -e
0 6 * * * /usr/local/bin/python3 /Users/Shared/ganuda/scripts/claude_code_analytics_parser.py --post http://192.168.132.223:9500/api/stats
```

### Dashboard

Simple HTML page showing:
- **Federation totals**: sessions, tokens, cost, model split
- **Per-node breakdown**: bar chart or table
- **Per-project top 10**: where the tokens go
- **Tool call histogram**: what tools get used most
- **Cost trend**: daily/weekly over time (from historical DB rows)
- **Model usage pie chart**: Opus vs Sonnet vs Haiku split

Serve from the FastAPI at `GET /dashboard`. Use the same visual style as the existing visual kanban or status page.

## Constraints

- **Data stays sovereign** — nothing leaves the WireGuard network
- **No auth needed** — WireGuard is the trust boundary
- **LAN-only binding** — the API listens on 0.0.0.0:9500 but is not exposed through Caddy/DMZ
- **Crawdad check**: The JSONL files may contain conversation content in `message.content[].text` — the parser should NOT extract or store message text, only metadata (tokens, model, tools, timestamps). This is the same privacy boundary ShipCard enforces.
- **Do NOT store**: file paths containing secrets, message content, user prompts, or tool call arguments. Only tool NAMES.

## Attribution

Inspired by ShipCard (github.com/jjaimealeman/shipcard) by @jjaimealeman. MIT license. Parser logic ported and adapted for sovereign multi-node federation use.

## Test

```bash
# Wave 1: Parser works
python3 /ganuda/scripts/claude_code_analytics_parser.py

# Wave 2: API accepts data
curl -X POST http://localhost:9500/api/stats -H "Content-Type: application/json" -d @/tmp/test_stats.json

# Wave 3: Dashboard renders
curl http://localhost:9500/dashboard
```

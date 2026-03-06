# Jr Instruction: Pi Agent Federation Extension

**Task ID:** PI-FED-EXT
**Kanban:** #1886
**Priority:** 1
**Assigned:** Software Engineer Jr.

---

## Overview

Create the Cherokee AI Federation extension for Pi Agent. This extension wires Pi into our thermal memory, council deliberation, kanban, and Jr queue systems via custom slash commands.

---

## Step 1: Create the extension directory structure

Create `/ganuda/config/pi/extensions/federation.ts`

```typescript
// Cherokee AI Federation Extension for Pi Agent
// Connects Pi CLI to federation infrastructure:
//   /thermal  — semantic search of thermal memory archive
//   /council  — submit question for council deliberation
//   /kanban   — query kanban tickets
//   /jr       — queue Jr work instruction
//   /status   — federation health check
//
// All queries go to local PostgreSQL (192.168.132.222)
// and local gateway (localhost:8080 or 192.168.132.222:8080)
//
// SECURITY: Sacred patterns (sacred_pattern=true) are FILTERED
// from /thermal output. No tribal knowledge leaves the extension.

import type { ExtensionAPI } from "@mariozechner/pi-agent-core"
import { execSync } from "child_process"

const DB_HOST = "192.168.132.222"
const DB_USER = "claude"
const DB_NAME = "zammad_production"
const GATEWAY_URL = "http://localhost:8080"

function psql(query: string): string {
  try {
    const result = execSync(
      `psql -h ${DB_HOST} -U ${DB_USER} -d ${DB_NAME} -t -A -c ${JSON.stringify(query)}`,
      { encoding: "utf-8", timeout: 15000 }
    )
    return result.trim()
  } catch (e: any) {
    return `DB Error: ${e.message}`
  }
}

function curlPost(url: string, data: object): string {
  try {
    const result = execSync(
      `curl -s --max-time 120 -X POST ${url} -H "Content-Type: application/json" -d ${JSON.stringify(JSON.stringify(data))}`,
      { encoding: "utf-8", timeout: 130000 }
    )
    return result.trim()
  } catch (e: any) {
    return `HTTP Error: ${e.message}`
  }
}

export default function federation(pi: ExtensionAPI) {

  // /thermal — search thermal memory archive
  pi.registerCommand("thermal", {
    description: "Search thermal memory (usage: /thermal <search terms>)",
    handler: async (args: string) => {
      if (!args.trim()) return "Usage: /thermal <search terms>"
      const escaped = args.replace(/'/g, "''")
      const query = `SELECT id, LEFT(original_content, 300) as content, temperature_score, created_at FROM thermal_memory_archive WHERE sacred_pattern = false AND original_content ILIKE '%${escaped}%' ORDER BY created_at DESC LIMIT 10;`
      const result = psql(query)
      if (!result) return "No thermal memories found matching: " + args
      return "Thermal Memory Results:\n" + result
    }
  })

  // /council — submit question for council deliberation
  pi.registerCommand("council", {
    description: "Submit question to council (usage: /council <question>)",
    handler: async (args: string) => {
      if (!args.trim()) return "Usage: /council <question>"
      const data = { question: args, context: "Submitted via Pi Agent CLI" }
      const result = curlPost(`${GATEWAY_URL}/v1/council/vote`, data)
      try {
        const parsed = JSON.parse(result)
        return `Council Vote Submitted\nAudit Hash: ${parsed.audit_hash}\nRecommendation: ${parsed.recommendation}\nConfidence: ${parsed.confidence}\nConsensus: ${parsed.consensus}`
      } catch {
        return "Council response: " + result
      }
    }
  })

  // /kanban — query kanban tickets
  pi.registerCommand("kanban", {
    description: "Query kanban (usage: /kanban [open|completed|search <term>])",
    handler: async (args: string) => {
      const parts = args.trim().split(/\s+/)
      const subcmd = parts[0] || "open"

      if (subcmd === "open") {
        return psql("SELECT id, LEFT(title, 60) as title, status, sacred_fire_priority as sfp FROM duyuktv_tickets WHERE status IN ('open', 'in_progress') ORDER BY sacred_fire_priority DESC LIMIT 15;")
      } else if (subcmd === "completed") {
        return psql("SELECT count(*) as completed FROM duyuktv_tickets WHERE status = 'completed';")
      } else if (subcmd === "search") {
        const term = parts.slice(1).join(" ").replace(/'/g, "''")
        return psql(`SELECT id, LEFT(title, 60) as title, status, sacred_fire_priority as sfp FROM duyuktv_tickets WHERE title ILIKE '%${term}%' ORDER BY sacred_fire_priority DESC LIMIT 10;`)
      } else {
        return "Usage: /kanban [open|completed|search <term>]"
      }
    }
  })

  // /jr — queue Jr work instruction
  pi.registerCommand("jr", {
    description: "Queue Jr task (usage: /jr <title> | <description>)",
    handler: async (args: string) => {
      if (!args.trim()) return "Usage: /jr <title> | <description>"
      const [title, ...descParts] = args.split("|")
      const desc = descParts.join("|").trim() || title.trim()
      const escaped_title = title.trim().replace(/'/g, "''")
      const escaped_desc = desc.replace(/'/g, "''")
      const result = psql(`INSERT INTO jr_work_queue (task_id, title, instruction_content, status, priority, source, created_by, assigned_jr, use_rlm) VALUES (md5(random()::text), '${escaped_title}', '${escaped_desc}', 'pending', 5, 'pi-agent', 'TPM', 'Software Engineer Jr.', false) RETURNING task_id;`)
      return "Jr task queued: " + result
    }
  })

  // /status — federation health check
  pi.registerCommand("status", {
    description: "Check federation health",
    handler: async () => {
      const gateway = (() => {
        try {
          const r = execSync(`curl -s --max-time 5 ${GATEWAY_URL}/health`, { encoding: "utf-8" })
          const p = JSON.parse(r)
          return `Gateway: ${p.status} (v${p.version})\n  vLLM: ${p.components.vllm}\n  Council: ${p.components.council}\n  Reasoning: ${p.components.reasoning} (${p.components.reasoning_node})`
        } catch { return "Gateway: unreachable" }
      })()
      const memories = psql("SELECT count(*) FROM thermal_memory_archive;")
      const kanban = psql("SELECT count(*) FILTER (WHERE status='open') as open, count(*) FILTER (WHERE status='completed') as done FROM duyuktv_tickets;")
      const jrQueue = psql("SELECT count(*) FILTER (WHERE status='pending') as pending, count(*) FILTER (WHERE status='in_progress') as active FROM jr_work_queue;")
      return `Federation Status\n${gateway}\nThermal Memories: ${memories}\nKanban: ${kanban}\nJr Queue: ${jrQueue}`
    }
  })
}
```

---

## Step 2: Create symlink for Pi extension discovery

The extension needs to be discoverable by Pi. Create the global extensions directory and symlink:

```text
mkdir -p ~/.pi/agent/extensions
ln -sf /ganuda/config/pi/extensions/federation.ts ~/.pi/agent/extensions/federation.ts
```

---

## Verification

Test each command after installation:

```text
pi --provider redfin-vllm --print --no-session "/status"
pi --provider redfin-vllm --print --no-session "/thermal council vote"
pi --provider redfin-vllm --print --no-session "/kanban open"
```

---

## Notes

- Sacred patterns are EXCLUDED from /thermal results (WHERE sacred_pattern = false)
- DB connection uses psql CLI (no npm pg dependency needed)
- Gateway calls use curl (no npm http dependency needed)
- Extension is pure TypeScript, no compilation step needed (Pi uses jiti loader)
- All data stays local — zero external network calls

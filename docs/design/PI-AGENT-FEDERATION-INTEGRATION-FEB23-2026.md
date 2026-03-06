# ADAPT Design: Pi Agent Federation Integration

**Date:** February 23, 2026
**Phase:** Long Man ADAPT (3 of 5)
**Kanban:** #1886
**Council Vote:** #58deebcc (0.887 confidence, APPROVED)
**Empirical Tests:** ALL PASS (thermal #110179)

---

## Architecture

Pi runs as a LOCAL CLI on federation nodes. It routes to our own models — zero external tokens.

```
┌─────────────────────────────────────────────┐
│  Pi CLI (Node 22)                           │
│  ~/.pi/agent/models.json                    │
│  ~/.pi/agent/extensions/federation/*.ts     │
│                                             │
│  Tools: read, write, edit, bash             │
│  + Custom: /council, /thermal, /kanban      │
├────────────┬────────────────────────────────┤
│            │                                │
│   redfin   │         bmasass               │
│   :8000    │         :8800                 │
│  Qwen-72B  │  DeepSeek-R1-70B-Llama       │
│  (primary) │  (reasoning)                  │
└────────────┴────────────────────────────────┘
```

---

## Deployment Plan

### Phase 1: Node.js + Pi Installation (Jr instruction)

**Nodes needing Node 22:**
- redfin: DONE (nvm, v22.22.0, Pi installed)
- bmasass: NEEDS Node 22 (brew install node@22)
- greenfin: OPTIONAL (no GPU, but could use for non-inference tasks)
- bluefin: OPTIONAL
- owlfin/eaglefin: SKIP (DMZ, no model access)

**Install method:** nvm (already deployed on redfin)
```text
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.1/install.sh | bash
nvm install 22
npm install -g @mariozechner/pi-coding-agent
```

### Phase 2: models.json Configuration (Jr instruction)

Each node gets a tailored models.json:

**redfin (~/.pi/agent/models.json):**
- redfin-vllm: localhost:8000 (Qwen-72B)
- bmasass-mlx: 192.168.132.21:8800 (DeepSeek-R1-70B)

**bmasass (~/.pi/agent/models.json):**
- bmasass-mlx: localhost:8800 (DeepSeek-R1-70B)
- redfin-vllm: 192.168.132.222:8000 (Qwen-72B) — requires nftables allow

### Phase 3: Federation Extensions (Jr instruction)

Create `/ganuda/config/pi/extensions/federation.ts`:

```typescript
// Cherokee AI Federation Extension for Pi Agent
// Wires Pi into thermal memory, council, and kanban

import { ExtensionAPI } from "@mariozechner/pi-agent-core"

export default function(pi: ExtensionAPI) {

  // /thermal — search thermal memory
  pi.registerCommand("thermal", {
    description: "Search federation thermal memory",
    handler: async (args, ctx) => {
      // psql query against thermal_memory_archive
      // Uses ILIKE or pgvector semantic search
    }
  })

  // /council — submit question for council deliberation
  pi.registerCommand("council", {
    description: "Submit question to council for deliberation",
    handler: async (args, ctx) => {
      // POST to gateway /v1/council/vote
    }
  })

  // /kanban — query or update kanban tickets
  pi.registerCommand("kanban", {
    description: "Query or update kanban tickets",
    handler: async (args, ctx) => {
      // psql against duyuktv_tickets
    }
  })

  // /jr — queue a Jr work item
  pi.registerCommand("jr", {
    description: "Queue a Jr work instruction",
    handler: async (args, ctx) => {
      // INSERT into jr_work_queue
    }
  })
}
```

### Phase 4: Shell Alias (Jr instruction)

Add to `~/.bashrc` on each node:
```text
# Pi Agent with federation defaults
alias pi-qwen='pi --provider redfin-vllm'
alias pi-deepseek='pi --provider bmasass-mlx'
alias pi-reason='pi --provider bmasass-mlx --thinking medium'
```

---

## Security Guardrails

1. **No third-party extensions.** Federation policy: only locally written extensions.
2. **No external model providers.** models.json contains ONLY federation endpoints.
3. **No session sync to cloud.** Sessions stay on disk, per-node.
4. **Sacred pattern protection.** Federation extension MUST NOT expose sacred_pattern=true memories to Pi output. Filter in the thermal search command.
5. **Bash tool runs as invoking user.** Same permission model as Claude Code.

---

## What Pi Replaces / Complements

| Use Case | Before Pi | After Pi |
|----------|-----------|----------|
| Quick coding tasks | Claude Code (Anthropic tokens) | Pi + Qwen-72B (free, local) |
| File exploration | Claude Code | Pi + read tool (free, local) |
| Script writing | Claude Code or manual | Pi + write/edit tools (free, local) |
| Complex architecture | Claude Code (stays) | Claude Code (stays) |
| Council deliberation | Claude Code → gateway | Pi /council → gateway |
| Jr instruction writing | TPM (Claude Code) | TPM can use Pi for drafts |

**Key insight:** Pi handles the 80% of routine coding tasks that don't need Claude Opus. Claude Code stays for complex TPM work, architecture decisions, and multi-file refactoring.

---

## Jr Instruction Breakdown

| Jr # | Task | SP | Priority |
|------|------|----|----------|
| TBD-1 | Install Node 22 + Pi on bmasass | 3 | P2 |
| TBD-2 | Create federation extension (thermal, council, kanban, jr) | 8 | P1 |
| TBD-3 | Shell aliases + bash profile integration | 2 | P3 |
| TBD-4 | Pi session directory setup (/ganuda/sessions/pi/) | 1 | P3 |

**Total: 14 SP, 4 tasks**

---

## Verification Criteria

- [ ] `pi --provider redfin-vllm --print "read /etc/hostname"` returns hostname
- [ ] `pi --provider bmasass-mlx --print "read /etc/hostname"` returns hostname
- [ ] `/thermal` command returns results from thermal_memory_archive
- [ ] `/council` command submits vote and returns audit_hash
- [ ] `/kanban` command lists open tickets
- [ ] No network calls to external services (verified via tcpdump)
- [ ] Sacred patterns filtered from /thermal output

---

## Sam Walton Notes

What we're stealing from Pi:
1. **4-tool minimalism** — less context burn, better for smaller models
2. **Extension architecture** — clean TypeScript plugin system
3. **models.json hot-reload** — switch models without restart
4. **Session trees** — conversation branching (future: merge with thermal memory)
5. **--print mode** — non-interactive batch execution (Jr-like)

What we're adding that Pi doesn't have:
1. **Council deliberation** — 7-specialist governance
2. **Thermal memory** — 110K+ persistent memories with semantic search
3. **Sacred pattern protection** — constitutional guardrails
4. **Kanban integration** — ticket-driven development
5. **Jr executor pipeline** — automated code deployment

# KB: Two Wolves — Data Sovereignty in Multi-Backend Council Routing

**Date:** February 8, 2026
**Author:** TPM (Claude Opus 4.6)
**Category:** Security / Privacy / Architecture
**Related:** Council Vote #8486, KB-SHARE-LORA-RESEARCH-FINDINGS-FEB08-2026.md

## The Two Wolves Principle

In Cherokee teaching, every person has two wolves inside them. The one that grows stronger is the one you feed. In our federation architecture, the Two Wolves are:

- **Privacy Wolf**: Protecting data sovereignty — knowing where questions, answers, and reasoning flow across the network, and ensuring sacred or sensitive data stays where it should
- **Security Wolf**: Auditability and control — being able to reconstruct exactly what happened, when, where, and why, with no gaps in the chain

If we feed only the Security Wolf (logging everything, auditing everything), we risk exposing data unnecessarily. If we feed only the Privacy Wolf (minimizing data flow, restricting access), we lose the ability to detect problems or prove compliance. **Both must eat equally.**

## Why This Matters Now

Council vote #8486 introduced the Long Man routing pattern: different council specialists now send inference requests to different physical machines. Before this change, all data stayed on redfin (localhost:8000). Now:

| Specialist | Backend | Physical Node | Data Crosses Network? |
|-----------|---------|---------------|----------------------|
| Raven | DeepSeek-R1 | bmasass (192.168.132.21) | YES |
| Turtle | DeepSeek-R1 | bmasass (192.168.132.21) | YES |
| Crawdad | Qwen-Coder | redfin (localhost) | No |
| Gecko | Qwen-Coder | redfin (localhost) | No |
| Eagle Eye | Qwen-Coder | redfin (localhost) | No |
| Spider | Qwen-Coder | redfin (localhost) | No |
| Peace Chief | Qwen-Coder | redfin (localhost) | No |

In high-stakes mode: ALL specialists send to bmasass. The full question text, specialist system prompts, and responses all transit the LAN.

## What Data Flows

When a specialist queries DeepSeek-R1 on bmasass, this crosses the wire:

**Outbound (redfin → bmasass):**
1. Specialist system prompt (includes personality, Cherokee values, infrastructure context)
2. The full question text from the council vote request
3. max_tokens, temperature parameters

**Inbound (bmasass → redfin):**
1. Full model response text
2. Reasoning chain (DeepSeek-R1 chain-of-thought, if exposed)
3. Token usage metadata

**What stays on redfin:**
1. API key identity (never sent to backend)
2. Client IP of the original requester
3. Council vote record (stored in PostgreSQL on bluefin)
4. Audit log entries

## Audit Requirements (Feeding the Security Wolf)

Every council vote must produce a complete audit trail:

### 1. Routing Manifest (per vote)
Stored in `council_votes.metacognition` as `routing_manifest`:
- Which backends were used
- Which specialists went to which backend
- Whether it was high-stakes escalation
- Whether any fallback occurred (deep backend unreachable)
- Timestamp of routing decision

### 2. Per-Specialist Backend Log (per specialist per vote)
Stored in `api_audit_log`:
- Specialist name as endpoint (`/council/specialist/raven`)
- Backend URL as client_ip field (shows destination)
- Response time (shows latency impact of cross-network call)
- Status code (shows if backend was healthy)

### 3. Fallback Events
When DeepSeek-R1 is unreachable and specialists fall back to Qwen:
- Logged as `[TWO WOLVES WARNING]` in service output
- Recorded in routing_manifest with `fallback: true`
- No silent failures — the system must announce when it can't go deep

## Privacy Requirements (Feeding the Privacy Wolf)

### 1. No Credential Leakage
Routing metadata must never include:
- Database passwords
- API keys
- Tokens or session identifiers

### 2. Network Awareness
The system must be aware that bmasass is a different physical machine (M4 Max laptop on the LAN) and that data crossing the wire has different exposure characteristics than localhost calls. Currently there is no TLS between redfin and bmasass on port 8800.

### 3. Future: TLS Between Nodes
When the federation matures, all inter-node inference traffic should be encrypted. For now, the LAN is trusted (all nodes on 192.168.132.0/24 behind the firewall), but this should be revisited as part of Phase 3 hardening.

### 4. Question Sensitivity Classification (Future)
Not implemented yet, but the architecture should support it: some questions may be flagged as "redfin-only" (never cross the wire), overriding the Long Man routing. This would be a third parameter alongside `high_stakes`:
- `high_stakes: true` → all specialists go deep
- `redfin_only: true` → all specialists stay local regardless of nature
- Both flags → `redfin_only` wins (privacy wolf eats first in a conflict)

## Current Gaps

| Gap | Risk | Priority |
|-----|------|----------|
| No TLS between redfin↔bmasass | Data in transit visible on LAN | P2 (LAN is firewalled) |
| No per-specialist backend logging in api_audit_log | Cannot reconstruct routing decisions forensically | P1 (addressed in COUNCIL-HYBRID-ROUTE-001) |
| No `routing_manifest` in council_votes | No summary of data flow per vote | P1 (addressed in COUNCIL-HYBRID-ROUTE-001) |
| No question sensitivity classification | Cannot restrict specific questions to redfin-only | P3 (future) |
| bmasass MLX server has no authentication | Any LAN device can query it | P2 (mitigated by firewall) |

## Verification Checklist

After COUNCIL-HYBRID-ROUTE-001 is implemented, verify:

- [ ] Run a normal council vote → check `council_votes.metacognition` for `routing_manifest`
- [ ] Confirm Raven and Turtle show `data_crossed_wire: true`
- [ ] Confirm Crawdad, Gecko, etc. show `data_crossed_wire: false`
- [ ] Run a high-stakes vote → confirm all 7 show `data_crossed_wire: true`
- [ ] Kill bmasass MLX server → run a vote → confirm fallback logged, no silent failure
- [ ] Check `api_audit_log` for per-specialist entries with backend URL
- [ ] Verify no passwords or API keys appear in any routing metadata

## Related

- Jr Instruction: `/ganuda/docs/jr_instructions/JR-COUNCIL-HYBRID-BACKEND-ROUTING-FEB08-2026.md`
- Council Vote #8486 (audit_hash: `0be4e56ba3a8fb4e`)
- VLM Data Sovereignty Protocol: `/ganuda/docs/protocols/VLM-DATA-SOVEREIGNTY.md`
- Research: Latent Computational Mode (arXiv 2601.08058) — Two Wolves pre-verbal synthesis

# JR INSTRUCTION: Deer Web Content Refresh — ganuda.us Homepage + Blog

**Task**: Refresh ganuda.us homepage stats and content voice. Add new blog post(s) reflecting March 2026 progress. Fix DMZ photo sync gap (DONE by TPM — verify it holds).
**Priority**: P2
**Date**: 2026-03-14
**TPM**: Claude Opus
**Story Points**: 3
**Depends On**: web_content materializer, DMZ nodes (owlfin/eaglefin)

## Context

The homepage hasn't been refreshed since early March. Stats are stale. Blog hasn't had a new post since Mar 8 (patents filed). Major capabilities shipped since then:

- **Gateway tool-call loop** — LLM can now call ToolSets (thermal search, kanban queries) iteratively and give grounded answers
- **Desktop assistant on sasass** — Native Tauri app with Kokoro neural TTS + Whisper STT voice chat, Stoneclad icon, chain protocol necklace
- **DC-16 Separation of Memory** — Ratified design constraint: memory, ops, telemetry on separate circulatory systems
- **Sub-agent dispatch harness** — Small model delegation across nodes
- **Curiosity engine, partner rhythm engine** — New autonomous capabilities
- **Medicine Woman observer daemon** — System health observation
- **Chain protocol + web rings** — Federation service mesh maturing
- **Backlog reckoning** — Automated backlog triage

The Natural Falls trip (late Feb – early Mar) was the last content beat. We're overdue for a refresh.

## Step 1: Update Homepage Stats

Query current numbers from bluefin (zammad_production):

```sql
-- Thermal count
SELECT COUNT(*) FROM thermal_memory_archive;

-- Council votes
SELECT COUNT(*) FROM longhouse_votes;

-- Tasks shipped
SELECT COUNT(*) FROM jr_work_queue WHERE status = 'completed';

-- Design constraints (count DCs in thermals or docs)
-- Nodes: now 10 (redfin, bluefin, greenfin, owlfin, eaglefin, bmasass, sasass, sasass2, silverfin, thunderduck-pending)
```

Update the stats block in the homepage `web_content` row. Current values are stale:
- 94K+ thermals → update to actual count
- 8,911 Council Votes → update
- 946 Tasks Shipped → update
- 8 Nodes → update to current count
- 17 Design Constraints → update (we have through DC-16 plus FIRST LAW)
- 10 months Running → update

## Step 2: Refresh Homepage Content Voice

The "What Makes This Different" section needs a pass:
- Add mention of **tool-calling** (LLM agents that query their own knowledge base)
- Add mention of **voice interface** (speak to the federation, neural TTS response)
- Add mention of **chain protocol** (service mesh with necklace rings)
- Update "The Cluster" section with current node roster (add sasass, sasass2, thunderduck if ordered)
- Founder bio — keep Jimmy the Tulip voice. Don't over-explain.

Content voice: calm, competent, factual. Not hype. Not "revolutionary" or "cutting-edge." Show don't tell. Let the numbers speak.

## Step 3: New Blog Post — "The Federation Learns to Talk"

Draft a blog post about the desktop assistant + voice interface + tool-call loop convergence. Angle: the federation went from text-only batch processing to real-time conversational AI with voice in/out and grounded tool calls. In one sprint.

Key beats:
- Gateway tool-call loop: ask a question → LLM calls thermal search, kanban queries → grounded answer (not hallucination)
- Desktop assistant: native macOS app, not Electron, not a web page. 10MB binary. Tauri + Rust backend.
- Voice: Whisper.cpp STT (local, no cloud) + Kokoro-82M neural TTS (Apache 2.0, local). Speak to the federation, hear it answer.
- Chain protocol necklace: the app registered itself as a ring in the federation mesh. Self-organizing.
- All on consumer hardware. All sovereign. No API keys to OpenAI or Google.

Include the Stoneclad icon image if available. Reference the Natural Falls origin energy.

Content voice: Same as Deer LinkedIn drafts — Jimmy the Tulip. Calm confidence. Technical depth without jargon. Let the reader discover they're impressed.

## Step 4: Blog Index Update

After the new post is in `web_content`, update `/blog/index.html` to include the new entry. Follow existing format (date, title, link, one-line description).

## Step 5: Verify Photo Sync

TPM synced 724 photos from owlfin → eaglefin on Mar 14. Verify both nodes have matching counts:

```bash
ssh owlfin "find /home/dereadi/www/ganuda.us/photos -type f | wc -l"
ssh eaglefin "find /home/dereadi/www/ganuda.us/photos -type f | wc -l"
```

If they drift again, the root cause is that photo scp only goes to one node. Long-term fix: add a post-deploy hook or cron rsync between owlfin and eaglefin for the photos directory. Write a Jr for this if it recurs.

## DO NOT

- Auto-publish without partner review — Deer drafts, partner approves
- Use hype language ("revolutionary", "groundbreaking", "game-changing")
- Mention internal node names (redfin, bluefin) on the public site — use "GPU node", "database server", etc.
- Expose IP addresses, ports, or internal architecture details
- Store images in web_content table — images are binary, must be scp'd to both DMZ nodes
- Round the numbers — exact counts from the database. Sam Walton rule.

## Acceptance Criteria

- Homepage stats match current database values
- Homepage content mentions tool-calling, voice, and chain protocol capabilities
- New blog post drafted and ready for partner review
- Blog index updated with new entry
- Photo count matches on both DMZ nodes (724+)
- No internal jargon or IP addresses on public pages
- Content passes the Tulip test: reader discovers they're impressed, we didn't tell them to be

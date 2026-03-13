# [RECURSIVE] Peace Chief Curiosity Engine — Stub-Filling Pipeline - Step 6

**Parent Task**: #1298
**Auto-decomposed**: 2026-03-12T09:03:34.722101
**Original Step Title**: Report

---

### Step 6: Report

After all stubs are extracted and queued, write a brief report:
```
Curiosity Engine processed [source] content.
Extracted: [N] stubs ([deep] deep, [medium] medium, [shallow] shallow)
Queued: [N] for research
Routed: [N] to Peace Chief, [N] to War Chief
Top stubs: [list top 3 by priority]
```

This report goes to:
- Thermal memory (low temp, domain_tag = 'curiosity')
- Slack #deer-signals (Peace Chief territory)

### Integration Points

1. **Telegram Bot**: When Chief sends a long message or forwards a link, call `ingest_sensory_input()`
2. **Email Daemon**: When Chief forwards an email (Snacks newsletter, LinkedIn notification), call `ingest_sensory_input()`
3. **Manual**: TPM can call it directly when Chief pastes content in a Claude Code session
4. **Future**: RSS feeds, bookmarked articles, saved tweets — any sensory input source

## Target Files

- `/ganuda/lib/curiosity_engine.py` — the pipeline library (CREATE)
- SQL migration for `curiosity_stubs` table
- `/ganuda/tests/test_curiosity_engine.py` — tests (CREATE)

## Acceptance Criteria

- [ ] `ingest_sensory_input()` accepts raw text and returns extracted stubs
- [ ] Stub extraction uses local model (redfin :9100 or sasass)
- [ ] Routing classifies each stub by domain, action, council_owner, priority
- [ ] Deep stubs are queued for sub-Claude research
- [ ] Medium stubs attempt local model fill first, escalate if uncertain
- [ ] Shallow stubs are logged and dismissed
- [ ] curiosity_stubs table created (or jr_work_queue integration working)
- [ ] Report generated after processing
- [ ] Tested with Sebastian Mondragon LinkedIn post as sample input
- [ ] Thermalized

## DO NOT

- Auto-dispatch sub-Claudes without checking the stub queue depth (budget gate — don't spawn 50 sub-Claudes from one newsletter)
- Research shallow stubs (waste of compute — DC-9)
- Contact anyone or anything external (Crane constraint)
- Assume every stub needs filling — some are just context, not questions
- Build a web scraper or RSS reader (future task, not this one)
- Over-engineer the table — stubs are lightweight and disposable

# FARA-7B + SAG Integration Project Plan

**DATE:** 2025-12-02
**FROM:** Command Post (TPM)
**TO:** IT Jr 1, IT Jr 2, IT Jr 3
**MISSION ID:** FARA-SAG-INTEGRATION-001
**STATUS:** APPROVED FOR IMPLEMENTATION

---

## TPM ULTRATHINK SYNTHESIS

### The Vision: FARA as SAG's "Hands"

FARA-7B is Microsoft's Computer Use Agent - a vision-language model that can:
- See screenshots (visual understanding)
- Generate actions: click(x,y), type("text"), scroll, navigate
- Recognize Critical Points (pause for user approval on sensitive actions)

SAG is our Tribe Mind interface with 6 tabs (Events, Kanban, Monitoring, Grafana, IoT, Email) plus the new Command Center sidebar.

**The synergy:** FARA can be SAG's "hands" - when a user asks the Tribe Mind to DO something (not just answer), FARA executes it visually through the SAG interface.

### Why This Matters

1. **Tribe Mind Phase 3** requires a chat interface where users can ask questions
2. Current chat only returns answers - it can't PERFORM actions
3. FARA enables: "Move this Kanban card to Done" → FARA clicks and drags
4. Air-gap compatible (runs on local RTX 6000, no cloud needed)

---

## ARCHITECTURAL DECISIONS

### 1. FARA runs on redfin (192.168.132.223)
- RTX PRO 6000 Blackwell (102GB VRAM)
- Model already loaded: 16.6GB VRAM, 2.2s load time
- Location: `/ganuda/models/fara-7b/`

### 2. SAG runs on redfin (192.168.132.223:4000)
- Same machine = minimal latency
- No network overhead for screenshots

### 3. Integration via Flask API
- Add FARA endpoints to existing SAG app.py
- Keep it lightweight - no separate microservice

### 4. Safety-First Design
- All FARA actions logged to database BEFORE execution
- Critical Points require user approval via modal dialog
- Rate limiting: 1 action per second max
- Session tracking for audit trail

---

## PHASE 1: CORE INFRASTRUCTURE (Priority: HIGH)

### IT Jr 1 Deliverables (Backend)

**1. Create FARA inference module:** `/ganuda/fara/fara_inference.py`
```python
# Model loading and inference
# Uses Qwen2_5_VLForConditionalGeneration (NOT AutoModelForCausalLM)
# See KB-AI-001 for correct architecture
```

**2. Create FARA executor module:** `/ganuda/fara/fara_executor.py`
```python
# Execute actions via pyautogui (desktop) or playwright (browser)
# Implement rate limiting
# Handle scroll, click, type, navigate actions
```

**3. Add API endpoints to SAG app.py:**
```python
@app.route("/api/fara/analyze", methods=["POST"])
def fara_analyze():
    """Send screenshot + task to FARA, return proposed action."""
    # Input: {screenshot_base64, task_description}
    # Output: {action_type, coordinates, text, is_critical_point, reason}

@app.route("/api/fara/execute", methods=["POST"])
def fara_execute():
    """Execute approved action."""
    # Input: {action_id, user_approved: true}
    # Output: {success, new_screenshot_base64}

@app.route("/api/fara/status")
def fara_status():
    """Return FARA model status."""
    # Output: {loaded, gpu_memory_used, model_version}
```

### IT Jr 2 Deliverables (Frontend)

**1. Create screenshot capture utility:** `/home/dereadi/sag_unified_interface/static/js/fara-capture.js`
- Capture current viewport as PNG
- Support element-specific capture (for focused tasks)

**2. Create action visualization overlay:** `/home/dereadi/sag_unified_interface/static/js/fara-overlay.js`
- Show where FARA will click (red dot + coordinates)
- Highlight text fields before typing
- Preview scroll direction with arrow

**3. Create Critical Point approval dialog:** `/home/dereadi/sag_unified_interface/templates/fara-approval.html`
- Modal showing: proposed action, screenshot, reason
- Approve / Reject buttons
- Logs decision to thermal memory

### IT Jr 3 Deliverables (Database)

**1. Create FARA action log table:**
```sql
CREATE TABLE fara_action_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID,
    task_description TEXT,
    screenshot_path VARCHAR(255),
    action_type VARCHAR(50),        -- click, type, scroll, navigate
    action_details JSONB,           -- {x, y, text, direction, url}
    is_critical_point BOOLEAN,
    critical_reason VARCHAR(255),
    user_approved BOOLEAN,
    execution_result VARCHAR(50),   -- success, failed, cancelled
    error_message TEXT,
    tokens_used INTEGER,
    inference_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_fara_session ON fara_action_log(session_id);
CREATE INDEX idx_fara_created ON fara_action_log(created_at DESC);
```

**2. Create FARA session table:**
```sql
CREATE TABLE fara_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50),
    task_goal TEXT,
    status VARCHAR(20),             -- active, completed, failed, cancelled
    total_actions INTEGER DEFAULT 0,
    successful_actions INTEGER DEFAULT 0,
    started_at TIMESTAMP DEFAULT NOW(),
    completed_at TIMESTAMP
);
```

---

## PHASE 2: SAG CHAT INTEGRATION

### Objective
Connect FARA to Tribe Mind chat (Phase 3 of SAG roadmap).

When user types: "Move the 'Fix login bug' card to Done column"
1. Chat routes to FARA (keyword detection: "move", "click", "open", "navigate")
2. FARA captures screenshot of Kanban tab
3. FARA generates: `click(x, y)` on card, `drag(x1, y1, x2, y2)` to Done
4. User approves (Critical Point: modifying data)
5. FARA executes
6. Return success + new screenshot

### IT Jr 2 Deliverables
- Add "Execute with FARA" toggle to chat interface
- Show FARA action preview before execution
- Display action history in chat

---

## PHASE 3: AUTOMATED TESTING

### Objective
FARA navigates SAG tabs, verifies UI elements render correctly.

### Use Cases
1. **Smoke test:** Visit all 6 tabs, verify no 500 errors
2. **Visual regression:** Compare screenshots before/after deployment
3. **Accessibility audit:** Check color contrast, font sizes

### IT Jr 1 Deliverables
- Create test runner: `/ganuda/fara/fara_test_runner.py`
- Define test scenarios in JSON
- Output report with screenshots + pass/fail

---

## PHASE 4: DEMO MODE

### Objective
FARA demonstrates SAG features to new users with guided tours.

### IT Jr 2 Deliverables
- Create demo script format (JSON with steps)
- Add "Start Demo" button to SAG header
- Show annotations/callouts during demo
- Allow pause/resume/skip

---

## SUCCESS CRITERIA

Phase 1:
- [ ] FARA model loads successfully via API
- [ ] /api/fara/analyze returns valid action proposals
- [ ] /api/fara/execute performs click/type actions
- [ ] Critical Points trigger approval dialog
- [ ] All actions logged to fara_action_log table

Phase 2:
- [ ] Chat can trigger FARA tasks
- [ ] Keyword routing works (move, click, navigate)
- [ ] Action preview shows before execution

Phase 3:
- [ ] Automated smoke tests pass
- [ ] Screenshot comparison works

Phase 4:
- [ ] Demo mode functional
- [ ] At least 3 demo scenarios created

---

## SAFETY REQUIREMENTS

1. **NEVER bypass Critical Points** - always require user approval
2. **Log ALL actions** to database BEFORE execution
3. **Rate limit** to max 1 action per second
4. **Implement kill switch** - POST /api/fara/stop
5. **Test in isolation** before connecting to real interfaces
6. **Screenshots stored** in `/ganuda/fara/screenshots/` (auto-cleanup after 24h)

---

## REFERENCE DOCUMENTS

- `/Users/Shared/ganuda/KB_FARA_7B_COMPUTER_USE_AGENT.md` (KB-AI-001)
- `/Users/Shared/ganuda/FARA_7B_SETUP_GUIDE.md`
- `/Users/Shared/ganuda/KB_SAG_COMMAND_CENTER_SIDEBAR.md`
- `/Users/Shared/ganuda/SAG_COMMAND_CENTER_MISSION.md`

---

## ESTIMATED EFFORT

| Phase | IT Jr 1 | IT Jr 2 | IT Jr 3 | Total |
|-------|---------|---------|---------|-------|
| Phase 1 | 8h | 6h | 2h | 16h |
| Phase 2 | 4h | 6h | 1h | 11h |
| Phase 3 | 6h | 2h | 0h | 8h |
| Phase 4 | 2h | 8h | 0h | 10h |
| **Total** | **20h** | **22h** | **3h** | **45h** |

---

## REPORT PROGRESS

Write progress updates to thermal memory with:
- source_triad: "it_jr"
- temperature: 0.70
- Include: What was completed, blockers, next steps

**Document Version:** 1.0
**Last Updated:** 2025-12-02

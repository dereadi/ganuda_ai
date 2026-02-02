# JR Instruction: ii-researcher Step Limit Fix

**JR ID:** JR-II-RESEARCHER-STEP-LIMIT-FIX-JAN28-2026
**Priority:** P0 - Critical Bug Fix
**Assigned To:** Software Engineer Jr.
**Thermal Memory:** 50532
**Blocks:** ii-researcher Phase 2 Integration

---

## Bug Description

ii-researcher has an infinite loop bug that causes GPU runaway:

1. `api.py` accepts `max_steps` parameter but **never passes it** to ReasoningAgent
2. `agent.py` run() method uses `while True:` with **no step counter**
3. Qwen 32B does not reliably terminate reasoning on its own
4. Result: Infinite token generation, GPU pegged at 100%

---

## Files to Modify

### 1. Patch api.py - Pass max_steps to ReasoningAgent

File: `/ganuda/services/ii-researcher/api.py`

**Find (around line 46-48):**
```python
    reasoning_agent = ReasoningAgent(
        question=question, stream_event=stream_manager.create_event_message
    )
```

**Replace with:**
```python
    reasoning_agent = ReasoningAgent(
        question=question,
        stream_event=stream_manager.create_event_message,
        max_steps=max_steps
    )
```

---

### 2. Patch agent.py - Add max_steps to constructor

File: `/ganuda/services/ii-researcher/ii_researcher/reasoning/agent.py`

**Find (around line 24-30):**
```python
    def __init__(
        self,
        question: str,
        report_type: ReportType = ReportType.ADVANCED,
        stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        override_config: Optional[Dict[str, Any]] = None,
    ):
```

**Replace with:**
```python
    def __init__(
        self,
        question: str,
        report_type: ReportType = ReportType.ADVANCED,
        stream_event: Optional[Callable[[str, Dict[str, Any]], None]] = None,
        override_config: Optional[Dict[str, Any]] = None,
        max_steps: int = 10,
    ):
```

**Find (around line 45, after `self.report_type = report_type`):**
```python
        self.report_type = report_type
```

**Add after:**
```python
        self.report_type = report_type
        self.max_steps = max_steps
```

---

### 3. Patch agent.py - Add step counter to run() method

File: `/ganuda/services/ii-researcher/ii_researcher/reasoning/agent.py`

**Find the run() method (around line 107-113):**
```python
    async def run(
        self,
        on_token: Optional[Callable[[str], None]] = None,
        is_stream: bool = False,
    ) -> str:
        while True:
```

**Replace with:**
```python
    async def run(
        self,
        on_token: Optional[Callable[[str], None]] = None,
        is_stream: bool = False,
    ) -> str:
        step = 0
        while step < self.max_steps:
            step += 1
            logging.info(f"ReasoningAgent step {step}/{self.max_steps}")
```

**Find the loop's natural exit point (look for `break` statements or where it returns).**

If the loop has no clean exit, add after the loop:

```python
        # If we hit max_steps, generate final report with what we have
        if step >= self.max_steps:
            logging.warning(f"ReasoningAgent hit max_steps limit ({self.max_steps})")
            if self.stream_event:
                await self.stream_event("warning", {"message": f"Reached maximum steps ({self.max_steps})"})
```

---

## Verification

```bash
# Restart ii-researcher
sudo systemctl restart ii-researcher

# Test with low max_steps
curl 'http://localhost:8090/search?question=hello&max_steps=3'

# Watch logs for step counting
journalctl -u ii-researcher -f

# Should see:
# ReasoningAgent step 1/3
# ReasoningAgent step 2/3
# ReasoningAgent step 3/3
# ReasoningAgent hit max_steps limit (3)
```

---

## Rollback

If patch causes issues:
```bash
cd /ganuda/services/ii-researcher
git checkout ii_researcher/reasoning/agent.py
git checkout api.py
sudo systemctl restart ii-researcher
```

---

## Notes

- Default max_steps set to 10 (reasonable for most queries)
- Logging added to track step progress
- Warning event emitted when limit reached
- This is a upstream bug - consider submitting PR to ii-researcher repo

---

FOR SEVEN GENERATIONS

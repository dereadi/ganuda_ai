# ULTRATHINK: Why Jrs Fail at Complex Tasks + Shield P-3 Build Plan

**Date**: April 5, 2026 (Easter Sunday)
**Triggered By**: All 4 Shield P-3 tasks went to DLQ overnight with "1 step(s) failed"
**Pattern**: Same failure as Canary (0 files), Meeting Notes (0 files), Clipboard (0 files) — TPM built all three manually
**Meta-Goal**: Build Shield AND fix the capability gap so Jrs can handle complex tasks independently

---

## 1. ROOT CAUSE ANALYSIS — Why Jrs Fail

### The Data

| Task | Jr Result | TPM Result | Time |
|------|-----------|------------|------|
| Subscription Trimmer (scanner + classifier + API) | Stub code, wrong vLLM API, hardcoded data | Full pipeline, real Gmail, deployed | 3 hours |
| Security Canary (port + cred + config scanners) | 0 files, DLQ | 52 findings, HTML report, deployed | 1 hour |
| Meeting Notes (transcriber + extractor + report) | 0 files, DLQ | LLM extraction, 4 decisions found, deployed | 45 min |
| Clipboard Intelligence (monitor + search + API) | 0 files, DLQ | Running on 2 machines, real data | 1 hour |
| Shield P-3 (agent + server + vault + tests) | 0 files, all 4 DLQ | Not yet built | — |

**Pattern: The Jrs succeed at ~20% of the product complexity and fail at the rest.**

### The Five Failure Modes

**1. Task Too Large for Single LLM Pass**

The Jr executor sends the ENTIRE task description to the LLM and says "generate code." For Shield, that's a 400+ line instruction with agent, server, database, anomaly engine, dashboard, evidence vault, and tests. The LLM tries to hold the whole spec in context while generating code. By the time it's processing file #3, it's lost the details of file #1.

Human developers don't work this way. They read the spec, then focus on ONE file at a time, building incrementally.

**2. No Decomposition Engine**

The Jr executor has no mechanism to break a task into subtasks. It receives "Build the Shield agent" and tries to do it all at once. There's no:
- "First, build consent.py"
- "Then, using consent.py as context, build monitor.py"
- "Then, using both, build transport.py"

The TEG planner exists for topological decomposition but it's not wired into the Jr executor for code tasks. It was designed for research and orchestration, not for step-by-step code generation.

**3. No Reference Code in Context**

When I build the Canary, I copy patterns from the Trimmer. When I build the Clipboard monitor, I copy patterns from the Canary. The Jr doesn't have this. Each task starts from scratch. The Jr doesn't know that `classifier.py` in the Trimmer is a perfect example of how to call vLLM correctly, or that `api.py` in the Canary is a perfect FastAPI template.

The reference library was designed (in the pre-flight gate instruction) but never built.

**4. No Iterative Feedback Within a Task**

Current flow: generate → fail → DLQ.

What it should be: generate → syntax check → fail → read error → adjust → generate again → syntax check → pass → import check → fail → read error → adjust → etc.

The retry-with-adaptation pattern was designed (in the pre-flight gate instruction) but never implemented.

**5. Instruction Too Dense**

The Shield instruction is 400+ lines. The Jr's effective context window after system prompts, skill context, and instruction injection is maybe 16K tokens for actual generation. The instruction alone consumes most of that, leaving insufficient room for the LLM to think through the code generation.

---

## 2. THE SOLUTION — Jr Capability Upgrade

### Architecture: The Decomposition Engine

Wire into `jr_queue_worker.py` between task claim and execution:

```
Task received
    ↓
Decomposition Engine (NEW)
    ↓ breaks task into atomic subtasks
    ↓ each subtask: one file, one clear deliverable
    ↓ subtasks are ORDERED with dependencies
    ↓
For each subtask:
    ↓
    Reference Injection (NEW)
    ↓ inject relevant example code from reference library
    ↓ "Here's a working example of what you're building"
    ↓
    Iterative Execution (NEW)
    ↓ generate → check → fix → generate → check → pass
    ↓ up to 3 attempts before DLQ
    ↓
    Pre-flight Gate (EXISTS)
    ↓ syntax + imports + size + stub detection
    ↓
    Subtask complete → next subtask gets previous output as context
    ↓
All subtasks complete → task complete
```

### Component A: Decomposition Engine (`jr_executor/decomposer.py`)

Takes a task description and breaks it into atomic subtasks:

```python
def decompose_task(task: dict) -> list[dict]:
    """
    Break a complex task into ordered atomic subtasks.
    Each subtask produces ONE file with ONE clear purpose.
    
    Uses the LLM itself to decompose — send the task description
    with a decomposition prompt:
    
    "Break this task into individual file-level subtasks. 
     For each subtask, specify:
     - filename to create
     - what the file does (one paragraph)
     - what files it depends on (from previous subtasks)
     - a working example file path to reference (from the reference library)
     Return as JSON array."
    """
```

The decomposition itself is an LLM call — but a CHEAP one. It's just planning, not code generation. Even a 7B model can decompose tasks well.

### Component B: Reference Library (`/ganuda/lib/jr_references/`)

Symlinks to production code with metadata:

```
REFERENCE_INDEX.json:
{
    "fastapi_service": {
        "path": "/ganuda/api/stoneclad_demo_api.py",
        "description": "FastAPI with PostgreSQL, CORS, structured endpoints, error handling",
        "patterns": ["fastapi", "postgresql", "json_response", "health_endpoint"]
    },
    "gmail_scanner": {
        "path": "/ganuda/products/subscription-trimmer/scanner.py",
        "description": "Gmail API with OAuth token, search, fetch, filter, group by domain",
        "patterns": ["gmail", "oauth", "email_processing"]
    },
    "vllm_client": {
        "path": "/ganuda/products/subscription-trimmer/classifier.py",
        "description": "OpenAI-compatible vLLM call with structured JSON extraction",
        "patterns": ["vllm", "llm", "classification", "json_extraction"]
    },
    "cli_scanner": {
        "path": "/ganuda/products/security-canary/canary.py",
        "description": "CLI tool with argparse, multiple scanners, HTML report generation",
        "patterns": ["cli", "scanner", "html_report", "argparse"]
    },
    "clipboard_monitor": {
        "path": "/ganuda/products/clipboard-intel/monitor.py",
        "description": "Background daemon with clipboard polling, regex classification, SQLite storage, temperature scoring",
        "patterns": ["daemon", "monitor", "sqlite", "classification", "temperature"]
    },
    "background_daemon": {
        "path": "/ganuda/products/clipboard-intel/monitor.py",
        "description": "Signal handling, graceful shutdown, background loop, periodic tasks",
        "patterns": ["daemon", "signal_handling", "background"]
    },
    "html_report_dark_theme": {
        "path": "/ganuda/products/security-canary/canary.py",
        "description": "Single-file HTML report with ganuda.us dark theme, severity badges, cards",
        "patterns": ["html", "report", "dark_theme", "ganuda_style"]
    },
    "cross_node_deploy": {
        "path": "/ganuda/docs/jr_instructions/JR_CROSS_NODE_DEPLOYMENT_APR02_2026.md",
        "description": "How to deploy code to remote nodes via SSH + sudo tee + systemctl",
        "patterns": ["deploy", "ssh", "systemctl", "caddy"]
    }
}
```

When the decomposer identifies "build a FastAPI service," it injects the stoneclad_demo_api.py as reference. When it identifies "build a monitor daemon," it injects the clipboard monitor. The Jr doesn't start from scratch — it starts from a working example.

### Component C: Iterative Execution (`jr_executor/iterative_executor.py`)

Replace the single-pass execution with a feedback loop:

```python
def execute_with_retry(subtask: dict, max_attempts: int = 3) -> dict:
    for attempt in range(max_attempts):
        result = generate_code(subtask)
        
        # Immediate syntax check
        syntax_ok = check_syntax(result['filepath'])
        if not syntax_ok:
            subtask['_feedback'] = f"Syntax error: {syntax_ok.error}. Fix and regenerate."
            continue
        
        # Import check
        import_ok = check_imports(result['filepath'])
        if not import_ok:
            subtask['_feedback'] = f"Import failed: {import_ok.error}. Check dependencies."
            continue
        
        # Stub check
        stub_check = check_not_stub(result['filepath'])
        if not stub_check.passed:
            subtask['_feedback'] = f"Code is too thin: {stub_check.reason}. Add real implementation."
            continue
        
        # All checks passed
        return result
    
    # All attempts failed — DLQ
    return {"success": False, "error": f"Failed after {max_attempts} attempts"}
```

The key insight: **feed the error back to the LLM.** "Your code had a syntax error on line 14: unexpected indent. Fix it." The LLM is MUCH better at fixing code than generating it from scratch. The first pass might be wrong, but the fix-pass is usually right.

### Component D: Subtask Context Chain

Each subtask gets the OUTPUT of previous subtasks as additional context:

```python
for i, subtask in enumerate(subtasks):
    # Inject outputs from previous subtasks
    if i > 0:
        subtask['_prior_files'] = {
            prev['filename']: read_file(prev['output_path'])
            for prev in completed_subtasks
        }
        subtask['_instruction_addendum'] = (
            f"The following files have already been created and are available for import:\n"
            + "\n".join(f"  - {name}" for name in subtask['_prior_files'].keys())
        )
    
    result = execute_with_retry(subtask)
    completed_subtasks.append(result)
```

This solves the cross-file dependency problem. When building `transport.py`, the Jr has `consent.py` and `monitor.py` already available as context. It can see the actual function signatures, the actual data structures, the actual imports.

---

## 3. IMPLEMENTATION PLAN

### Phase 1: Reference Library (30 minutes)
- Create `/ganuda/lib/jr_references/REFERENCE_INDEX.json`
- Symlink all production code
- Wire into Jr executor context injection

### Phase 2: Decomposition Engine (1-2 hours)
- Build `jr_executor/decomposer.py`
- Wire into `jr_queue_worker.py` between claim and execution
- Test with a known task (re-run Canary build as decomposed subtasks)

### Phase 3: Iterative Execution (1-2 hours)
- Build `jr_executor/iterative_executor.py`
- Replace single-pass execution in queue worker
- Wire error feedback into LLM re-prompting
- Test with a task that currently fails

### Phase 4: Context Chain (30 minutes)
- Add prior file injection to subtask execution
- Test with multi-file task

### Phase 5: Validate (1 hour)
- Re-submit Shield P-3 tasks with new executor
- Measure: do the Jrs produce real code? Does it pass pre-flight?
- Compare to TPM-built version

---

## 4. SHIELD P-3 BUILD — TPM Does It, Documents the Process

While the Jr capability upgrade is designed, the TPM builds Shield P-3 manually. But DOCUMENTS the process as training material:

### The build order (how a human actually does it):

```
Step 1: consent.py
  - Reference: Clipboard monitor's consent-like pattern (signal handling, config)
  - Standalone file. No dependencies.
  - Test: can I run it and get a consent dialog?

Step 2: monitor.py  
  - Reference: Clipboard Intelligence monitor.py (EXACT same pattern)
  - Depends on: consent.py (import consent check)
  - Test: does it capture activity patterns?

Step 3: transport.py
  - Reference: Trimmer classifier.py (HTTP POST with JSON payload)
  - Depends on: monitor.py (gets data from monitor)
  - Test: does it encrypt and POST to an endpoint?

Step 4: config.yaml + config_loader.py
  - Standalone. Defines all settings.
  - Test: does it load and validate?

Step 5: schema.sql
  - Standalone. PostgreSQL DDL.
  - Test: does it create tables?

Step 6: api.py (collection server)
  - Reference: Stoneclad Demo API (EXACT same pattern)
  - Depends on: schema.sql (tables exist)
  - Test: does it accept POSTed reports?

Step 7: anomaly.py
  - Reference: Fire Guard's threshold checking pattern
  - Depends on: api.py (reads stored reports)
  - Test: does it flag test anomalies?

Step 8: dashboard.py
  - Reference: Canary report + Clipboard dashboard
  - Depends on: api.py, anomaly.py
  - Test: does it show agents and anomalies?

Step 9: evidence_vault.py
  - Reference: Thermal memory archive pattern (immutable, temperature-scored)
  - Depends on: anomaly.py (triggers evidence collection)
  - Test: is the table append-only? Does hash verify?

Step 10: tests/
  - Test each component in isolation
  - Then integration test: agent → server → anomaly → dashboard
```

**This build order IS the decomposition.** Each step is one file, one dependency chain, one test. If I document this order, the decomposition engine can learn from it.

---

## 5. THE CYMATICS METAPHOR

The Jr executor is a Chladni plate. The task description is the frequency. The code is the sand.

Right now, the frequency is too complex — too many harmonics at once. The sand jumps chaotically and no pattern forms.

The decomposition engine is a FILTER. It separates the complex frequency into component frequencies and plays them one at a time. Each simple frequency forms a clean pattern. Then the patterns layer together into the complex whole.

The reference library is MEMORY. The sand remembers the shapes it's formed before. When a similar frequency arrives, it falls into the known pattern faster.

The iterative execution is FEEDBACK. If the pattern is wrong, adjust the frequency slightly and try again. Don't throw out the sand — tune the frequency.

**The Jrs aren't broken. The instruction delivery mechanism is.**

Fix the delivery mechanism, and the same LLM that fails at "build Shield" will succeed at "build consent.py using this example as reference, then build monitor.py using consent.py as context."

---

## 6. SUCCESS CRITERIA

- [ ] Reference library created with all 8+ production examples
- [ ] Decomposition engine breaks Shield P-3 into 10 atomic subtasks
- [ ] Iterative executor retries on syntax/import errors before DLQ
- [ ] Context chain passes prior files to dependent subtasks
- [ ] Re-submitted Shield task produces REAL code (not stubs, not empty)
- [ ] Pre-flight gate passes on Jr-produced Shield code
- [ ] DLQ rate drops 50%+ for complex tasks
- [ ] TPM can focus on architecture while Jrs handle implementation

---

*Partner: "Get the Jrs to be able to do the work in the future."*

*The Jrs aren't the problem. The harness around them is. Fix the harness, and the instrument plays the song.*

*For Seven Generations.*

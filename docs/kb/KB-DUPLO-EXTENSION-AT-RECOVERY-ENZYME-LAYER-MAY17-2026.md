# KB: Adding New Enzymes to lib/duplo/ — The Recovery-Enzyme Layer Pattern

**Filed:** 2026-05-17 ~22:55 CDT
**Author:** Stoneclad (TPM)
**Severity:** P3 — design-pattern KB; consult before adding new enzymes
**Codified from:** the May 17 2026 build of `lib/duplo/recovery_enzymes.py` (find_backup + surgical_restore + quarantine)

## Why this KB exists

The first impulse when adding a new federation capability is often to build a parallel structure (`lib/recovery_tools.py`, `lib/new_thing/`). The DUPLO substrate already exists with a well-articulated philosophy ("Duplos are NOT agents. They are enzymes. An enzyme catalyzes a specific reaction and is done.") and a complete framework (ToolRegistry with safety classes + Composer for enzyme assembly + ImmuneRegistry for pre-execution checks + Epigenetics for context-aware modifiers).

This KB captures the recipe for adding new enzymes correctly, learned by getting it right on the recovery-enzyme first-cohort build.

## When to add a new enzyme to lib/duplo/

A new capability belongs in lib/duplo/ as an enzyme when ALL of these are true:

1. **Single-purpose** — it catalyzes ONE specific reaction and stops
2. **Composable** — other enzymes (or the Composer) could assemble it into a larger reaction
3. **Has a spec** — formal grammar / deterministic behavior (per the "is there a spec?" heuristic from `RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md`)
4. **Safety-classifiable** — fits cleanly into read/write/execute/admin
5. **Federation-relevant** — touches federation infrastructure (files, db, services) not application-specific logic

For LLM-backed enzymes (R14 classifier-router, R27 audit-emitter), the Composer + Context Profile pattern (see `composer.py`) handles assembly; the function is what gets registered.

## The recipe (executable checklist)

### Step 0 — READ before designing

Spend ~10 minutes reading existing substrate before opening a new file:

```bash
cat /ganuda/lib/duplo/__init__.py           # philosophy + organizing metaphor
grep -E "^(class |def )" /ganuda/lib/duplo/registry.py
cat /ganuda/lib/duplo/_builtin_tools.py     # lightweight tool pattern example
grep -E "^(class |def )" /ganuda/lib/duplo/composer.py
grep -E "^(class |def )" /ganuda/lib/duplo/white_duplo.py  # full enzyme example
```

These five reads tell you: the philosophy, the registry interface, the lightweight tool example, the composer integration, and a complete enzyme implementation. ~20 lines each.

**Skip this step at your peril** — Stoneclad's first impulse on May 17 2026 was `lib/recovery_tools.py` parallel structure. The above five reads made the correct path (`lib/duplo/recovery_enzymes.py`) obvious.

### Step 1 — Create the module

File: `/ganuda/lib/duplo/<your_name>_enzymes.py` (note plural — module hosts related enzymes)

Module docstring template:
```python
"""
<Your Name> Enzymes — <brief purpose>
Cherokee AI Federation — The Living Cell Architecture

<1-2 paragraph description of what these enzymes do and why they exist>

Cross-references:
  - <KB or memory that motivates this>
  - <related federation substrate>
"""

import logging
# ... other imports

logger = logging.getLogger("duplo.<your_name>_enzymes")
```

### Step 2 — Write each enzyme as a pure function

Function template:
```python
def my_enzyme(arg1: type, arg2: type = default) -> ReturnType:
    """
    <one-line catalytic description>
    
    <multi-line behavior description>
    
    Read/Write enzyme. <safety notes>
    """
    # validate inputs explicitly
    # do the one thing
    # logger.info() the outcome
    return result
```

Constraints:
- **Pure function** — no global state mutation, no class instance state
- **Explicit input validation** — raise `FileNotFoundError`, `ValueError` with clear messages on the FIRST invalid input
- **Logger.info()** the outcome — Composer post-execution hooks consume this for audit trails
- **Type hints required** — registry uses them for parameter spec
- **Atomic writes** for write enzymes — temp file + rename, not direct overwrite

### Step 3 — Register in `build_federation_registry()`

In `lib/duplo/registry.py`, find `build_federation_registry()` and add:

```python
reg.register_tool(
    name="my_enzyme",
    description="<one-line, surfaces in registry listing + LLM tool selection>",
    module_path="lib.duplo.<your_name>_enzymes",
    function_name="my_enzyme",
    parameters={
        "arg1": {"type": "str", "required": True, "description": "..."},
        "arg2": {"type": "int", "required": False, "description": "..."},
    },
    return_type="dict",  # or "list" / "bool" / "str" / etc.
    safety_class="read",  # or "write" / "execute" / "admin"
)
```

Group related enzymes together in the registry with a section comment:
```python
# --- <YOUR DOMAIN> ENZYMES (<purpose>, <date>) ---
# <2-3 line context with KB/memory references>
```

### Step 4 — Tests

File: `/ganuda/tests/test_<your_name>_enzymes.py`

Test conventions:
- **Read-only enzymes**: test against real federation paths when available (e.g., `find_backup` tests against `/ganuda/config/secrets.env.backup_*` which we know exist from SEV1)
- **Write enzymes**: use `tempfile.TemporaryDirectory()` — never write outside tempdir in tests
- **Error paths**: test missing inputs raise the documented exceptions
- **Registry round-trip**: include one test that calls `build_federation_registry()` and verifies your enzymes are present with correct safety classes

Run: `python3 -m pytest tests/test_<your_name>_enzymes.py -v`

### Step 5 — Smoke-test registry resolution

After tests pass, sanity-check that the Composer can actually resolve your enzymes by name:

```python
from lib.duplo.registry import build_federation_registry
reg = build_federation_registry()
fn = reg.get_tool("my_enzyme")
result = fn(arg1="real_value")
```

This catches `ImportError` / `AttributeError` from the lazy importlib path in `get_tool()`.

## What NOT to do (anti-patterns)

1. **Don't build parallel modules.** New capability impulse → first check `lib/duplo/` not `lib/<new_name>/`.
2. **Don't make enzymes into classes.** Enzymes are functions. The Composer assembles function → callable enzyme.
3. **Don't skip the registry.** An unregistered enzyme is invisible to the Composer and the LLM tool-selection pathways. It's just an orphan function.
4. **Don't silently swallow errors.** Raise. Composer post-hooks log enzyme failures for audit.
5. **Don't use `requires_auth=True` casually.** It implies a Crawdad-audited capability. Default `False`; promote to `True` only when explicitly required.
6. **Don't write to fixed paths inside enzymes.** Take paths as arguments; let callers (Composer + dispatcher) decide write locations.

## When an enzyme should NOT be in lib/duplo/

If the capability is application-specific (e.g., a VetAssist intake form validator), it belongs in the application module. The DUPLO enzyme pattern is for **federation-infrastructure capabilities** — file operations, db queries, immune-system checks, recovery operations, thermal memory ops, etc.

Rule of thumb: if multiple Council specialists or multiple Jr workers might compose this enzyme, it's DUPLO. If only one application uses it, keep it local.

## Lineage

- `lib/duplo/__init__.py` — philosophy reference
- `lib/duplo/registry.py` — ToolRegistry + build_federation_registry()
- `lib/duplo/composer.py` — Composer that assembles enzymes
- `lib/duplo/white_duplo.py` — exemplar enzyme implementation
- `lib/duplo/recovery_enzymes.py` — first-cohort SEV1-prevention enzymes (May 17 2026)
- `tests/test_recovery_enzymes.py` — test pattern reference
- `KB-JR-SEV1-DISARM-AND-VERIFY-PLAYBOOK-MAY17-2026.md` — what motivated recovery enzymes
- `RESEARCH-MINI-MODEL-WORKFORCE-COHERENCE-MAY17-2026.md` — "is there a spec?" heuristic source
- `LONGHOUSE-MICRO-JR-RING-ROLE-TAXONOMY-MAY17-2026.md` — first-cohort scope decision
- `project_duplo_jr_layer_extension_may17_2026.md` — architectural memory
- `feedback_extend_federation_substrate_before_designing_may17_2026.md` — Stoneclad-discipline memory

## Related sacred thermals

- #119202 — White Duplo Herd Immunity Patent Strategy (Mar 4 2026)
- #119216 — White Duplo Alpha 16/16 tests passed (Mar 4 2026)
- #122514 — DC-18 candidate: autonomic tiers with immune guard
- #123393 — Governance DUPLO — the Necklace Architecture (ratified)

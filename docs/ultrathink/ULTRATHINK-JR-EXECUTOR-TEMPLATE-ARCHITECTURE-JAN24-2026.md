# ULTRATHINK: Jr Executor Template Architecture
## Date: January 24, 2026
## Cherokee AI Federation - For Seven Generations

---

## Council Decision

**Question:** Should we restructure code generation prompt to emphasize IMPLEMENT TEMPLATE over GENERATE FROM SCRATCH?
**Vote:** Approved
**Confidence:** 84.3% (High-Medium)
**Concerns:** Gecko (Perf), Turtle (7GEN), Raven (Strategy), Crawdad (Security), Peace Chief (Consensus)

**Consensus:** "Restructure prompt to emphasize IMPLEMENT TEMPLATE to leverage existing resources, enhance efficiency, improve consistency, and reduce security risks."

---

## Big Picture Context

### The Jr Executor System Evolution

```
Phase 1 (Dec 2025): Basic task execution
├── Simple prompt → LLM → output
├── No instruction files
└── Generate from task description only

Phase 2 (Jan 2026): Instruction file support
├── KB-JR-EXECUTOR-INSTRUCTION-FILE-READING-JAN24-2026
├── Read .md files referenced in tasks
├── Append content to task
└── ❌ PROBLEM: Still says "Generate" → LLM ignores templates

Phase 3 (Now): Template-first architecture
├── Restructure prompt hierarchy
├── Templates as PRIMARY input, task as CONTEXT
├── "Implement" not "Generate"
└── Preserve code patterns, fill gaps only
```

### Why This Matters for Seven Generations

1. **Code Consistency** - Templates encode best practices, patterns, security measures
2. **Knowledge Preservation** - Senior developer patterns captured in templates survive
3. **Reduced Errors** - LLM fills gaps rather than reinventing (fewer bugs)
4. **Faster Iteration** - 80% template + 20% generation = faster, safer
5. **Auditability** - Template changes are explicit, reviewable

---

## Current Architecture Problem

### The Prompt Hierarchy Issue

```
CURRENT (Broken):
┌─────────────────────────────────────────┐
│ "You are a code GENERATOR..."           │  ← Sets GENERATE mindset
├─────────────────────────────────────────┤
│ OUTPUT RULES                            │
│ FARA RULES                              │
│ RAG CONTEXT                             │
│ FEW-SHOT EXAMPLES                       │
├─────────────────────────────────────────┤
│ TASK:                                   │
│   {task_content}                        │
│   === DETAILED INSTRUCTIONS ===         │
│   {instruction_file_content}  ← BURIED! │
├─────────────────────────────────────────┤
│ "Generate the code now..."              │  ← Reinforces GENERATE
└─────────────────────────────────────────┘

RESULT: LLM generates Flask from scratch, ignores FastAPI templates
```

### The Fix: Template-First Hierarchy

```
PROPOSED (Template-First):
┌─────────────────────────────────────────┐
│ "You are a code IMPLEMENTER..."         │  ← Sets IMPLEMENT mindset
├─────────────────────────────────────────┤
│ CRITICAL INSTRUCTION:                   │
│   "Use the TEMPLATE below as your       │
│    foundation. Do NOT create from       │
│    scratch. MODIFY and COMPLETE it."    │
├─────────────────────────────────────────┤
│ === TEMPLATE CODE TO IMPLEMENT ===      │  ← PROMINENT POSITION
│ {instruction_file_content}              │
├─────────────────────────────────────────┤
│ === TASK CONTEXT ===                    │
│ {original_task_description}             │
├─────────────────────────────────────────┤
│ OUTPUT RULES (preserve structure)       │
│ FARA RULES (apply to gaps only)         │
├─────────────────────────────────────────┤
│ "Implement the template above..."       │  ← Reinforces IMPLEMENT
└─────────────────────────────────────────┘

RESULT: LLM uses FastAPI template, fills in gaps only
```

---

## Architectural Implications

### 1. Task Type Modes

The fix enables two execution modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Template Mode** | Instruction file present | Implement template, preserve structure |
| **Generation Mode** | No instruction file | Generate from scratch (current behavior) |

```python
if instruction_content:
    prompt = build_template_prompt(instruction_content, task_content)
else:
    prompt = build_generation_prompt(task_content)  # fallback
```

### 2. Template Quality Gates

Templates become first-class artifacts requiring:
- **Syntax validation** before storage
- **Version control** (git tracked)
- **Testing** (template outputs should compile/run)
- **Review** (TPM approval for template changes)

### 3. Jr Learning Path

```
Novice Jr:     Template Mode only (guided implementation)
Skilled Jr:    Template Mode + minor gaps
Expert Jr:     Generation Mode (can create new patterns)
```

This creates a natural skill progression and safety net.

### 4. RAG Context Repositioning

Current: RAG provides "similar code patterns"
Proposed: RAG validates template is consistent with codebase

```python
# Old: RAG as inspiration
rag_context = self._get_code_rag_context(content)

# New: RAG as validation
rag_validation = self._validate_template_consistency(instruction_content)
```

---

## Security Considerations (Crawdad)

### Template Injection Prevention

Templates are trusted (TPM-created), but we must ensure:

1. **No user input in templates** - Templates are static files
2. **Path validation** - Only read from `/ganuda/docs/jr_instructions/`
3. **Syntax validation** - Templates must parse before use
4. **Output sandboxing** - Write paths still restricted

### Reduced Attack Surface

Template-first actually REDUCES attack surface:
- Less LLM "creativity" = fewer unexpected outputs
- Known patterns = easier to audit
- Template changes are explicit, reviewable

---

## Performance Considerations (Gecko)

### Token Efficiency

| Metric | Generation Mode | Template Mode |
|--------|-----------------|---------------|
| Prompt tokens | ~2000 | ~3500 (template included) |
| Output tokens | ~1500 | ~800 (less to generate) |
| Accuracy | 60% | 95% (template fidelity) |
| Rework cycles | 3-4 | 1-2 |

**Net effect:** More input tokens, but fewer iterations = faster overall.

### Caching Opportunity

Templates can be cached and pre-validated:
```python
@lru_cache(maxsize=100)
def get_validated_template(path: str) -> str:
    content = read_file(path)
    validate_syntax(content)
    return content
```

---

## Seven Generations Impact (Turtle)

### Knowledge Codification

Templates capture:
- **Security patterns** (auth flows, input validation)
- **Error handling** (retry logic, graceful degradation)
- **Performance patterns** (connection pooling, caching)
- **Cherokee AI patterns** (Council integration, pheromones)

These survive developer turnover, model changes, and system evolution.

### Self-Improvement Loop

```
1. TPM creates template from best practices
2. Jr implements template
3. Jr output reviewed, improvements identified
4. Template updated with improvements
5. All future Jrs benefit from improvement
   ↻ Repeat
```

This is stigmergic knowledge evolution - the codebase itself teaches future Jrs.

---

## Implementation Plan

### Phase 1: Prompt Restructuring (This Task)

**Files:** 1 file
- `/ganuda/jr_executor/jr_task_executor.py`

**Changes:**
1. Rename "generator" → "implementer" in system message
2. Add template detection and mode selection
3. Restructure prompt with template-first hierarchy
4. Update final instruction from "Generate" → "Implement"

### Phase 2: Template Validation (Future)

**Scope:**
- Pre-validate template syntax before execution
- Cache validated templates
- Log template usage metrics

### Phase 3: Template Versioning (Future)

**Scope:**
- Git-based template management
- Template changelog
- A/B testing of template variations

---

## Success Criteria

### Immediate (This Fix)
- [ ] Jr output matches instruction file framework (FastAPI not Flask)
- [ ] Template imports preserved in output
- [ ] Template structure preserved (function names, class names)
- [ ] Only gaps/placeholders filled by LLM

### Long-term (7GEN)
- [ ] 90%+ template fidelity rate
- [ ] Reduced rework cycles (from 3-4 to 1-2)
- [ ] Template library grows with best practices
- [ ] Jr skill levels correlate with template complexity

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Template too rigid | Allow "creative" flag for generation mode |
| Template bugs propagate | Syntax validation before use |
| LLM ignores template | Stronger prompt wording + few-shot examples |
| Performance regression | Cache templates, measure latency |

---

## Conclusion

The template-first architecture transforms Jrs from "creative generators" to "skilled implementers." This:

1. **Improves quality** - Known patterns, fewer bugs
2. **Accelerates delivery** - Less iteration, faster completion
3. **Preserves knowledge** - Templates encode best practices
4. **Enables scaling** - Novice Jrs can do complex work with good templates
5. **Supports 7GEN** - Knowledge survives across time

The prompt fix is small (one file), but the architectural shift is significant. We move from "LLM as author" to "LLM as craftsman implementing blueprints."

---

**FOR SEVEN GENERATIONS** - Templates are the knowledge vessels that carry wisdom forward.

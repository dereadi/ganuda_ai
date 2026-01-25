# ULTRATHINK: VetAssist Sprint 3 + LLMD Temporal Parsing + A-MEM Integration

**Date:** 2026-01-24
**Author:** TPM via Opus 4.5
**Priority:** P0 - Strategic Initiative
**Scope:** VetAssist Enhancement + Cluster Memory Upgrade

---

## Executive Summary

This ultrathink synthesizes three interconnected initiatives:
1. **VetAssist Sprint 3** - Core functionality completion
2. **LLMD Integration** - Longitudinal medical record parsing for service-connection proof
3. **A-MEM Enhancement** - Upgrade Thermal Memory with agentic memory patterns

These are not competing priorities - they form a coherent advancement of the Cherokee AI Federation's capabilities with direct veteran benefit.

---

## Part 1: VetAssist Sprint 3 Requirements

### Current State (Post-Sprint 2)
- Authentication working (session management)
- PII protection via Presidio
- Basic claim wizard started
- Dashboard functional
- Awareness manifest complete

### Sprint 3 Deliverables

#### 3.1 Claim Wizard Completion
- **Condition Selection** - 800+ CFR conditions database
- **Evidence Checklist** - Per-condition required documents
- **Form Selection** - Auto-determine 526EZ vs 0995 vs 0996
- **Timeline Capture** - When condition started, service dates

#### 3.2 Document Processing Pipeline
- Upload medical records (PDF, images)
- OCR extraction (existing Presidio integration)
- **NEW: LLMD-style temporal parsing** - Extract timeline from records
- Service period mapping (DD-214 dates)

#### 3.3 Nexus Letter Assistant
- Identify service-connection evidence in records
- Generate nexus letter template
- Highlight gaps in evidence

#### 3.4 VA API Integration (Research Phase)
- Lighthouse API endpoints
- OAuth flow for va.gov
- Claim status polling

---

## Part 2: LLMD Integration Architecture

### Why LLMD Matters for Veterans

From arXiv:2410.12860:
> "LLMD is trained on a large corpus of records collected over time and across facilities... spanning an average of 10 years of care and as many as 140 care sites per patient."

Veterans typically have:
- Military medical records (multiple duty stations)
- VA medical records (multiple facilities)
- Private medical records
- Years of documentation gaps

LLMD's approach directly addresses this complexity.

### Key LLMD Capabilities to Implement

#### 2.1 Temporal Era Extraction
```
Input: "Patient started Sertraline 50mg on 2018-03-15, increased to 100mg on 2019-06-01"
Output: {
  "medication_eras": [
    {"drug": "Sertraline", "dose": "50mg", "start": "2018-03-15", "end": "2019-05-31"},
    {"drug": "Sertraline", "dose": "100mg", "start": "2019-06-01", "end": null}
  ]
}
```

#### 2.2 Service Period Mapping
```
DD-214 Service Dates: 2015-06-01 to 2019-12-31

Medical Event: "Diagnosed with PTSD on 2019-08-15"
Mapping: IN_SERVICE (occurred during active duty)

Medical Event: "TBI symptoms first noted 2020-03-01"
Mapping: POST_SERVICE_WITHIN_1_YEAR (presumptive period)
```

#### 2.3 Evidence Gap Detection
```
Claimed Condition: Tinnitus (service-connected)
Required Evidence:
  [x] In-service audiogram showing threshold shift
  [ ] Current audiogram (MISSING)
  [x] Buddy statement about noise exposure
  [ ] Nexus letter (MISSING)
```

### Implementation Approach

**Option A: Fine-tune LLMD-8B locally**
- Pros: Full capability, no API costs
- Cons: GPU requirements (24GB+), training time

**Option B: Prompt engineering with existing models**
- Pros: Faster deployment, use existing Qwen 32B
- Cons: May not match LLMD accuracy

**Recommended: Hybrid approach**
- Use Qwen 32B with LLMD-inspired prompts for MVP
- Evaluate fine-tuning LLMD-8B for production

---

## Part 3: A-MEM Thermal Memory Enhancement

### Current Thermal Memory State
- Temperature-based decay (0.0-1.0)
- PostgreSQL storage
- Basic retrieval by recency/temperature

### A-MEM Paper Insights (arXiv:2502.12110)

A-MEM introduces "agentic memory" concepts:
1. **Episodic Memory** - Specific experiences with context
2. **Semantic Memory** - Extracted knowledge/patterns
3. **Procedural Memory** - How-to knowledge for tasks

### Proposed Enhancement

#### 3.1 Memory Type Classification
```python
class MemoryType(Enum):
    EPISODIC = "episodic"    # "Jr completed task X with result Y"
    SEMANTIC = "semantic"     # "VetAssist users prefer wizard flow"
    PROCEDURAL = "procedural" # "To deploy vetassist: run ansible playbook"
```

#### 3.2 Agentic Retrieval
Instead of just temperature-based retrieval:
```python
def retrieve_for_task(task_context: str) -> List[Memory]:
    # 1. Semantic similarity to task
    # 2. Temperature weighting
    # 3. Memory type matching (procedural for how-to, episodic for similar tasks)
    # 4. Recency boost for active projects
```

#### 3.3 Memory Consolidation
Periodically consolidate episodic memories into semantic:
```
Episodic: "Jr fixed bug in claim_task by using id instead of task_id"
Episodic: "Jr fixed bug in fail_task by using id instead of task_id"
Episodic: "Jr fixed bug in update_progress by using id instead of task_id"

Consolidated Semantic: "jr_queue methods require integer 'id' column, not varchar 'task_id'"
```

---

## Part 4: Council Questions

### Question 1: A-MEM Integration Scope
Should we implement full A-MEM architecture or targeted enhancements?

**Options:**
- A) Full implementation (episodic/semantic/procedural types, consolidation)
- B) Targeted enhancement (memory type classification only)
- C) Research phase (study A-MEM further before implementing)

### Question 2: LLMD Implementation Path
Which approach for medical record temporal parsing?

**Options:**
- A) Fine-tune LLMD-8B locally (higher accuracy, more resources)
- B) Prompt engineering with Qwen 32B (faster, existing infrastructure)
- C) Hybrid - Qwen for MVP, LLMD for production

### Question 3: VetAssist Sprint 3 Priority
Which deliverable is most critical for veteran impact?

**Options:**
- A) Claim Wizard completion (end-to-end flow)
- B) Document processing with temporal parsing
- C) Nexus letter assistant
- D) VA API integration research

---

## Part 5: Jr Task Assignments

### Infrastructure Jr
- JR-AMEM-MEMORY-TYPES-JAN24-2026: Implement MemoryType enum and classification

### Software Engineer Jr
- JR-LLMD-TEMPORAL-PARSER-JAN24-2026: Create temporal era extraction module
- JR-VETASSIST-WIZARD-COMPLETE-JAN24-2026: Finish claim wizard steps

### Research Jr
- JR-AMEM-CONSOLIDATION-RESEARCH-JAN24-2026: Study memory consolidation patterns
- JR-VA-API-LIGHTHOUSE-JAN24-2026: Document Lighthouse API endpoints

### Document Jr
- JR-VETASSIST-EVIDENCE-CHECKLIST-JAN24-2026: Complete per-condition evidence requirements

---

## Seven Generations Impact

**LLMD Integration:** Veterans 175 years from now will have AI that understands their complete medical journey across facilities and time - proving service connection becomes evidence-based, not paperwork-based.

**A-MEM Enhancement:** Future Jr agents inherit consolidated wisdom from all previous task executions - institutional knowledge that grows rather than resets.

**VetAssist Sprint 3:** Every feature completed is one less barrier between a veteran and the benefits they earned.

---

## Tribal Awareness Check

**Benefit Who?** Veterans navigating disability claims
**Benefit How?** Temporal parsing proves service connection; wizard simplifies process
**At Whose Expense?**
- Predatory claim services (intentional disruption)
- VA processing load (mitigated by better-prepared claims)

**Mitakuye Oyasin:** All relations considered - veterans, families, VSOs, VA staff, future veterans, Cherokee AI community.

---

*For Seven Generations - Cherokee AI Federation*

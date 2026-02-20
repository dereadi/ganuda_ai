# Jr Instruction: Research Isnad Chains & Permission Manifests for Jr Instruction Security

**Task ID:** RESEARCH-ISNAD-PERM-001
**Assigned To:** Research Jr (Security focus)
**Priority:** P1 (HIGH - Council-approved research directive)
**Created:** February 4, 2026
**Depends On:** None
**Estimated Steps:** 10
**Council Concern:** Crawdad [SECURITY], Turtle [SUSTAINABILITY], Gecko [PERFORMANCE], Eagle Eye [OBSERVABILITY], Raven [STRATEGY]

---

## Origin

Crawdad (security specialist) brought back intelligence from Moltbook (AI agent social platform) regarding supply chain security vulnerabilities in agent ecosystems. The Moltbook community identified that skill files (equivalent to our Jr instructions) are executed without provenance verification or scope declaration. The Cherokee AI Federation council voted to research two concepts for potential adoption.

This is a **RESEARCH task only**. Do not implement code changes. Produce a findings report.

---

## Background: Current State

Our Jr instructions are markdown files queued via the `jr_work_queue` table (columns: `title`, `description`, `priority`, `assigned_jr`, `instruction_content`). The executor at `/ganuda/jr_executor/task_executor.py` parses and executes them. The RLM executor at `/ganuda/lib/rlm_executor.py` provides path protection via a blacklist in `/ganuda/config/rlm_protected_paths.yaml`.

Current security posture:
- **Provenance:** None. Instructions are trusted implicitly once queued. No record of who authored, reviewed, or approved them.
- **Scope declaration:** None. Instructions can attempt any file operation. The RLM protected paths config blocks writes to critical paths reactively, but instructions do not declare intent upfront.
- **Integrity:** No content hashing. An instruction could be modified after approval with no detection mechanism.

---

## Steps

### Step 1: Research the hadith isnad system

Study the Islamic hadith authentication methodology:
- What is the **sanad** (chain of transmission)? How does each link in the chain attest to receiving the content from the previous link?
- What is the **matn** (content analysis)? How is the actual text verified independently of the chain?
- How does the dual verification (sanad + matn) provide stronger guarantees than either alone?
- What are the historical grading categories (sahih, hasan, da'if, mawdu) and how do they map to trust levels?

Document findings with specific examples of how a three-link chain works.

### Step 2: Research multiplicative trust decay (Dirichlet's observation)

Investigate how trust degrades across chain links:
- If each link in a chain has 95% trust, what is the cumulative trust after N links?
  - N=1: 0.95
  - N=2: 0.9025
  - N=3: 0.857
  - N=5: 0.774
  - N=10: 0.599
- What does this mean for our isnad design? With author -> reviewer -> approver (3 links), what trust thresholds are reasonable?
- How does the hadith science handle this decay problem? (Hint: quality of each narrator matters, not just chain length)
- Research the mathematical formalism: P(chain_valid) = product of P(link_i_valid) for i in 1..N
- What is the minimum acceptable trust score for a Jr instruction to be executed?

### Step 3: Design minimum viable isnad for Jr instructions

Propose a concrete isnad schema with these fields:
- `author_hash`: Cryptographic identity of who wrote the instruction (SHA-256 of author key)
- `reviewer_hash`: Cryptographic identity of who reviewed it
- `approver_hash`: Cryptographic identity of who approved it for execution (council member or TPM)
- `content_hash`: SHA-256 of the instruction content at the time of approval
- `timestamp`: ISO-8601 timestamp for each attestation
- `chain_signature`: Combined signature of the full chain (concatenation of all hashes, then signed)

Research questions:
- Where should this metadata live? Options: YAML frontmatter in the instruction markdown, separate sidecar file, or database columns in `jr_work_queue`
- How would the executor verify the chain before execution?
- What happens when verification fails? (Reject? Flag for manual review? Execute with reduced permissions?)

### Step 4: Research database schema changes for isnad

Investigate what columns need to be added to `jr_work_queue` to support isnad chains:

```sql
-- Proposed columns to research (DO NOT EXECUTE - research only)
ALTER TABLE jr_work_queue ADD COLUMN author_hash VARCHAR(64);
ALTER TABLE jr_work_queue ADD COLUMN reviewer_hash VARCHAR(64);
ALTER TABLE jr_work_queue ADD COLUMN approver_hash VARCHAR(64);
ALTER TABLE jr_work_queue ADD COLUMN content_hash VARCHAR(64);
ALTER TABLE jr_work_queue ADD COLUMN chain_signature VARCHAR(128);
ALTER TABLE jr_work_queue ADD COLUMN chain_verified BOOLEAN DEFAULT FALSE;
ALTER TABLE jr_work_queue ADD COLUMN chain_trust_score DECIMAL(5,4);
```

Research questions:
- Is it better to store the chain in a separate `jr_instruction_isnad` table (normalized) or inline (denormalized)?
- What indexes would be needed for verification queries?
- How would this interact with the existing queue claim/update flow in `/ganuda/jr_executor/jr_queue_client.py`?

### Step 5: Research performance cost of SHA-256 hashing

Benchmark SHA-256 on typical Jr instruction files:
- Measure hash computation time for files of 5KB, 10KB, 25KB, and 50KB
- Use Python's `hashlib.sha256()` on sample instruction files from `/ganuda/docs/jr_instructions/`
- Document: Is the overhead negligible (sub-millisecond) or material?
- Research: What is the overhead of verifying a 3-link chain (3 hash comparisons + 1 chain signature check)?

This addresses **Gecko's concern** about low performance overhead.

### Step 6: Research open source chain-of-trust libraries in Python

Survey existing libraries:
- `sigstore` - Software supply chain signing (Python client)
- `in-toto` - Software supply chain integrity framework
- `TUF` (The Update Framework) - Secure software update system
- `cosign` - Container signing (has Python bindings)
- `python-gnupg` - GPG signing/verification
- Any hadith-specific chain verification implementations

For each, document:
- License
- Maturity / maintenance status
- Relevance to our use case
- Integration complexity

### Step 7: Research permission manifest design

Investigate what a Jr instruction permission manifest should declare:
- `files_write`: List of file paths or glob patterns the instruction intends to create/modify
- `files_read`: Paths it needs to read
- `commands`: Shell commands it intends to run (e.g., `pip install`, `systemctl restart`)
- `network`: Any network access (API calls, downloads, specific hosts/ports)
- `database`: Tables it intends to query or modify

Research analogous systems:
- **npm package.json**: How does Node.js declare package permissions and script scopes?
- **Android AndroidManifest.xml**: How does Android declare app permissions (camera, network, storage)?
- **Browser extension manifest.json**: How do Chrome/Firefox extensions declare host permissions, API access, content script scopes?
- **AppArmor/SELinux profiles**: How do Linux security modules declare process capabilities?
- **Deno permissions**: How does Deno's `--allow-read`, `--allow-write`, `--allow-net` model work?

Extract patterns we can borrow for our context.

### Step 8: Research manifest storage and format options

Investigate where the permission manifest should live:

**Option A: YAML frontmatter in Jr instruction markdown**
```markdown
---
manifest:
  files_write:
    - /ganuda/docs/reports/RESEARCH-*.md
  files_read:
    - /ganuda/docs/jr_instructions/*.md
    - /ganuda/lib/rlm_executor.py
  commands:
    - python3
    - pip list
  network: none
  database: none
---
# Jr Instruction: ...
```

**Option B: Separate .manifest.yaml sidecar file**
```
/ganuda/docs/jr_instructions/JR-TASK-FOO.md
/ganuda/docs/jr_instructions/JR-TASK-FOO.manifest.yaml
```

**Option C: Database columns in jr_work_queue**
```sql
ALTER TABLE jr_work_queue ADD COLUMN manifest_json JSONB;
```

For each option, evaluate:
- Ease of authoring (can the TPM or council easily add manifests?)
- Machine readability (can the executor parse it reliably?)
- Version control (is it tracked in git alongside the instruction?)
- Tamper resistance (can it be modified independently of the content hash?)

### Step 9: Research enforcement mechanisms

Investigate three enforcement strategies:

**Pre-execution enforcement:**
- Before running, parse the instruction content and compare declared files_write against actual file paths mentioned in the instruction
- Flag mismatches (instruction mentions `/ganuda/lib/rlm_executor.py` but manifest does not declare it)
- How does this integrate with the existing RLM `is_path_protected()` function in `/ganuda/lib/rlm_executor.py`?
- Currently RLM blocks reactively. Manifests would declare intent proactively. Research how these two layers complement each other.

**Runtime enforcement:**
- Executor intercepts each file operation and checks it against the manifest
- Similar to how `is_path_protected()` works today, but checking against a per-instruction allowlist instead of a global blocklist
- What is the performance overhead of checking every operation?

**Post-execution audit:**
- After execution completes, compare actual operations (from execution log) against declared manifest
- Generate audit report showing any violations
- This is least restrictive but provides accountability

Research which strategy (or combination) is most appropriate for our environment.

### Step 10: Research integration architecture and produce findings report

Document how isnad chains and permission manifests work together:

**The dual protection model:**
- Isnad chain verifies WHO approved the instruction and that the content has not changed since approval
- Permission manifest verifies WHAT the instruction is allowed to do
- Together: a Jr instruction with verified provenance AND declared scope is fundamentally safer than one with neither

**Observability metrics (Eagle Eye's concern):**
Research what metrics should be tracked:
- Chain verification pass/fail rate
- Manifest violation attempts (instruction tried to touch something undeclared)
- Trust decay scores over time per author
- Time-to-verify overhead per instruction
- Proportion of instructions with complete chains vs partial vs none

**Strategic fit (Raven's concern):**
- Does this align with broader industry trends in AI agent security?
- Is this a sustainable architecture (Turtle's concern) or a reactive patch?
- Can this scale to 100+ Jr instructions per day without bottlenecks?

Write the complete findings report to `/ganuda/docs/reports/RESEARCH-ISNAD-PERMISSION-MANIFESTS.md`.

---

## Output Artifacts

1. `/ganuda/docs/reports/RESEARCH-ISNAD-PERMISSION-MANIFESTS.md` -- Complete findings report containing:
   - Summary of findings for each research question
   - Recommended minimum viable implementation for each concept
   - Database schema changes needed (SQL, research-only -- do not execute)
   - Integration points with existing executor code (`task_executor.py`, `rlm_executor.py`, `jr_queue_client.py`)
   - Performance impact estimates (SHA-256 benchmarks, verification overhead)
   - Open questions for council review

---

## Success Criteria

- All 10 research questions investigated with documented findings
- Hadith isnad system explained with concrete mapping to our Jr instruction chain
- Trust decay math computed and thresholds proposed
- At least 3 open source libraries evaluated for chain-of-trust
- Permission manifest format proposed with pros/cons of each storage option
- Enforcement mechanism recommended with justification
- Integration architecture documented showing how both systems complement existing RLM protection
- Observability metrics defined for Eagle Eye
- Performance overhead estimated for Gecko
- Sustainability assessment provided for Turtle
- Strategic alignment assessed for Raven
- Report written to the specified path

---

## Context / Reference Files

- RLM Executor: `/ganuda/lib/rlm_executor.py`
- Protected Paths Config: `/ganuda/config/rlm_protected_paths.yaml`
- Task Executor: `/ganuda/jr_executor/task_executor.py`
- Queue Client: `/ganuda/jr_executor/jr_queue_client.py`
- Queue Schema: `/ganuda/jr_executor/queue_tasks.sql` (shows jr_work_queue columns)
- Existing Security Instruction: `/ganuda/docs/jr_instructions/JR-RESEARCH-SECURITY-ADDENDUM-JAN28-2026.md`

---

## Tags

- security
- research
- isnad_chains
- permission_manifests
- jr_executor
- supply_chain
- council_approved

---

FOR SEVEN GENERATIONS

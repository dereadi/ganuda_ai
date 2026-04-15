# KB Article: BMad-METHOD Patterns for Cherokee AI Federation

**KB ID**: KB-BMAD-001
**Created**: 2025-12-03
**Category**: AI Strategy / Agent Architecture
**Source**: BMad-METHOD GitHub, World of AI Video (Nov 9, 2025)
**Tags**: BMAD, agent orchestration, spec-driven development, workflows

---

## Summary

BMad-METHOD (Breakthrough Method for Agile AI-Driven Development) is a framework for orchestrating specialized AI agents through the software development lifecycle. This KB captures patterns applicable to the Cherokee AI Federation.

---

## What is BMad-CORE?

**BMad-CORE** = Collaboration Optimized Reflection Engine

Philosophy: "Unlike traditional AI tools that replace human thinking, BMad-CORE guides you through reflective workflows that bring out your best ideas."

This aligns with Cherokee AI's approach: TPM guides, Triads deliberate, Jrs execute.

---

## BMad Architecture

### Agent Roles (19 Total)

| BMad Agent | Cherokee Equivalent | Notes |
|------------|---------------------|-------|
| Product Manager | Command Post (TPM) | Strategic direction, mission creation |
| Architect | IT Chiefs | System design decisions |
| Scrum Master | Chiefs Agent | Story drafting, work coordination |
| Developer | IT Jr 1 (Backend) | Code implementation |
| UX Designer | IT Jr 2 (Frontend) | UI/CSS work |
| DBA | IT Jr 3 (Database) | Schema, queries, optimization |
| QA Engineer | LLM Tester (future) | Test generation |
| DevOps | Ops Triad (future) | Infrastructure automation |

### Key Difference

BMad: 19 specialized agents, each with narrow focus
Cherokee: 3 Triads (IT, Trading, Ops) with Jr sub-specialization

**Potential Enhancement**: Add more specialized Jr roles within each Triad.

---

## BMad Workflow Phases

### Phase 1: Ideation & Planning
- Brainstorming sessions
- Market research
- Project briefs

**Cherokee Equivalent**: Command Post mission creation, thermal memory research

### Phase 2: Architecture & Design
- System architecture specs
- UI/UX specifications
- Technical decisions

**Cherokee Equivalent**: Chiefs deliberation, decision documents

### Phase 3: Development Execution
- Scrum Master drafts stories with context
- Developer implements one at a time
- Cyclical workflow

**Cherokee Equivalent**: Jr Agent picks up approved decisions, executes work

---

## Spec-Driven Development

### BMad Approach

1. Create detailed specification BEFORE coding
2. Spec includes: requirements, constraints, acceptance criteria
3. AI agents work from spec, not vague instructions
4. Human reviews spec (highest leverage), not just code

### Cherokee Application

Current: Mission content in thermal memory serves as spec
Enhancement: Structured spec templates for different work types

**Proposed Spec Template**:
```
MISSION SPECIFICATION
---------------------
ID: [Mission ID]
Type: [Backend/Frontend/Database/Infrastructure]
Priority: [Temperature]

REQUIREMENTS:
- [ ] Requirement 1
- [ ] Requirement 2

CONSTRAINTS:
- Must use existing patterns in [file]
- No new dependencies
- Must pass existing tests

ACCEPTANCE CRITERIA:
- [ ] Criteria 1
- [ ] Criteria 2

FILES TO MODIFY:
- /path/to/file1.py (lines X-Y)
- /path/to/file2.py (new file)

CONTEXT:
[Compressed, relevant context only]
```

---

## Guided Workflows (50+)

BMad provides pre-built workflows for common scenarios:

| Workflow Type | Description | Cherokee Use Case |
|--------------|-------------|-------------------|
| Bug Fix | Diagnose → Fix → Test | IT Jr bug resolution |
| New Feature | Spec → Design → Implement | Full Triad workflow |
| Refactor | Analyze → Plan → Execute | Chiefs-guided refactoring |
| Code Review | Review → Feedback → Iterate | LLM Reviewer module |
| Documentation | Analyze → Generate → Review | KB article creation |

### Cherokee Enhancement

Create workflow templates in `/Users/Shared/ganuda/workflows/`:
- `bug_fix_workflow.md`
- `new_feature_workflow.md`
- `code_review_workflow.md`
- `infrastructure_workflow.md`

---

## Human-in-the-Loop Governance

### BMad Approach

- Human approval required at key decision points
- Specs reviewed before implementation
- Plans reviewed before execution
- Human provides strategic direction, AI handles execution

### Cherokee Implementation

Current:
- Chiefs approval gate for all missions
- TPM (Command Post) provides strategic direction
- User approval for Critical Points (FARA)

Enhancement:
- Add "spec review" step before Chiefs approval
- Structured approval criteria in thermal memory

---

## Customizable Personas

BMad allows persona customization per agent:
- Expertise level
- Communication style
- Domain knowledge
- Tool preferences

### Cherokee Application

Current: Generic Jr agents (1, 2, 3)
Enhancement: Persona files for each Jr:

```
/ganuda/personas/it_jr_1_backend.md
/ganuda/personas/it_jr_2_frontend.md
/ganuda/personas/it_jr_3_dba.md
```

Persona content:
- Expertise areas
- Preferred tools/libraries
- Code style preferences
- Review criteria

---

## IDE Integration

BMad works with:
- Claude Code
- Cursor
- Windsurf
- VS Code

Cherokee already uses Claude Code as Command Post interface.

**Enhancement**: Create `.claude/commands/` slash commands for common workflows:
- `/mission` - Create new mission
- `/status` - Check Triad status
- `/thermal` - Query thermal memory
- `/approve` - Approve pending decision

---

## Key Takeaways for Cherokee AI

### What We're Already Doing Well

1. Agent orchestration (Triads)
2. Human-in-the-loop (Chiefs approval)
3. Thermal memory for context sharing
4. Specialized roles (Jr 1/2/3)

### What We Could Adopt

1. **Structured Specs**: Mission templates with requirements, constraints, acceptance criteria
2. **Workflow Templates**: Pre-built patterns for common tasks
3. **Persona Files**: Detailed Jr agent configurations
4. **Slash Commands**: Quick access to common operations
5. **Reflective Questioning**: Strategic questions before implementation

### Implementation Priority

| Enhancement | Effort | Impact | Priority |
|-------------|--------|--------|----------|
| Spec templates | Low | High | 1 |
| Workflow templates | Medium | High | 2 |
| Slash commands | Low | Medium | 3 |
| Persona files | Medium | Medium | 4 |

---

## Related Documents

- `/Users/Shared/ganuda/kb/KB_CONTEXT_ENGINEERING_AGENTS.md` - RPI Workflow
- `/Users/Shared/ganuda/kb/KB_VERIFICATION_FIRST_REASONING.md` - Verification patterns
- `/Users/Shared/ganuda/TRIBE_MIND_VISION.md` - Strategic roadmap

---

## Sources

- [BMAD-METHOD GitHub](https://github.com/bmad-code-org/BMAD-METHOD)
- [Introducing BMAD-METHOD](https://ziyu4huang.github.io/blogs/posts/2025-10-04-introducing-bmad-method/)
- [Applied BMAD - Reclaiming Control](https://bennycheung.github.io/bmad-reclaiming-control-in-ai-dev)
- [BMAD vs GitHub Spec Kit](https://medium.com/@mariussabaliauskas/a-comparative-analysis-of-ai-agentic-frameworks-bmad-method-vs-github-spec-kit-edd8a9c65c5e)
- World of AI YouTube (Nov 9, 2025) - BMad-CORE tutorial

---

**Temperature**: 0.80 (Knowledge Base - Strategic Reference)

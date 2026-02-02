# Jr Instruction Template: Code Review Protocol

**Version:** 1.1
**Date:** 2026-01-26
**Council Approved:** Yes (maintain security rigor)

---

## Purpose

This template defines how Jrs perform peer reviews on codebases, applications, or other Jr work. Reviews build collective intelligence across the cluster and integrate with standups for rapid feedback loops.

---

## When to Use

- Before major refactoring
- After Jr completes a multi-file feature
- When bugs indicate systemic issues
- Periodic health checks on production code
- As part of continuous standup cycle

---

## Standup Integration

Reviews integrate with our standup cycle:

1. **Pre-Standup**: Jr runs review, generates report
2. **Standup Discussion**: TPM reviews findings with team
3. **Post-Standup**: Jr tasks queued for fixes
4. **Next Standup**: Verify fixes, close findings

**Frequency**: Standups can occur multiple times daily for rapid iteration.

**Escalation Path**:
- Critical findings → Immediate TPM flag (don't wait for standup)
- High findings → Next standup discussion
- Medium/Low → Batch for daily standup

---

## Review Task Format

When creating a Jr review task, use this structure:

```markdown
# Jr Instruction: Review [TARGET NAME]

**Task ID:** To be assigned
**Jr Type:** [Research Jr. | Software Engineer Jr. | rotating]
**Priority:** P[1-3]
**Category:** Review

---

## Review Target

- **Path:** /ganuda/path/to/review/
- **Scope:** [Full codebase | Specific module | Recent changes]
- **Focus Areas:** [Security | Architecture | Performance | All]

---

## Review Checklist

### 1. Structure Analysis
- [ ] Directory organization follows patterns
- [ ] File naming conventions consistent
- [ ] Separation of concerns maintained

### 2. Import Analysis
- [ ] No circular imports
- [ ] All imports resolve
- [ ] No unused imports

### 3. Security Analysis
- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] Authentication on protected routes
- [ ] SQL injection prevention

### 4. Code Quality
- [ ] Error handling present
- [ ] Logging for debugging
- [ ] Consistent code style

### 5. Integration Points
- [ ] External service connections documented
- [ ] Database access patterns consistent
- [ ] API contracts defined
```

---

## Output Requirements

Create review report at:
`/ganuda/docs/reviews/REVIEW-[TARGET]-[DATE].md`

Use this format:

```markdown
# Review Report: [TARGET]

**Date:** YYYY-MM-DD
**Reviewer:** [Jr Name]
**Scope:** [Description]
**For Standup:** [Next standup timestamp or IMMEDIATE]

## Executive Summary
[2-3 sentence overview of findings]

## Findings

### Critical (Blocking - Immediate Escalation)
| ID | Issue | Location | Impact |
|----|-------|----------|--------|
| C1 | [Description] | file:line | [Impact] |

### High (Security/Stability - Next Standup)
| ID | Issue | Location | Impact |
|----|-------|----------|--------|

### Medium (Code Quality - Daily Standup)
| ID | Issue | Location | Impact |
|----|-------|----------|--------|

### Low (Suggestions - Batch)
| ID | Issue | Location | Impact |
|----|-------|----------|--------|

## Recommendations
1. [Prioritized action item]
2. [Next action]

## Files Reviewed
- path/to/file1.py (X lines)
- path/to/file2.py (Y lines)

## Seven Generations Assessment
[How do these findings affect long-term maintainability?]
```

---

## Do NOT

- Modify any code during review (read-only)
- Skip security checks
- Ignore "minor" issues (log them as Low)
- Review without documenting findings

---

## After Review

1. Report saved to `/ganuda/docs/reviews/`
2. Critical findings flagged to TPM immediately
3. Findings archived to thermal memory
4. Follow-up Jr tasks queued based on standup priorities
5. Findings discussed at next appropriate standup

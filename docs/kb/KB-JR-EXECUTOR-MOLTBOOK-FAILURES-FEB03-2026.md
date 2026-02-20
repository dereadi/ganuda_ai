# KB-JR-EXECUTOR-MOLTBOOK-FAILURES-FEB03-2026

## Jr Executor Failure Patterns — Moltbook Task Batch

| Field       | Value                                         |
|-------------|-----------------------------------------------|
| KB ID       | KB-EXECUTOR-MOLTBOOK-001                      |
| Date        | 2026-02-03                                    |
| Author      | TPM (Claude Opus 4.5)                         |
| Category    | Jr Executor / Post-Mortem / Lessons Learned    |
| Tags        | jr-executor, guardrails, path-resolution, moltbook, remediation |
| Status      | Final                                         |

---

## Summary

All 4 Jr tasks queued for Moltbook daemon enhancement failed or produced incorrect output on 2026-02-03. This document captures the failure patterns and their remediation strategies for future task authoring.

---

## Failure 1: File Replacement Guardrail (MOLTBOOK-BUGFIX-COUNTER-001)

**Task**: Move `self.posts_today += 1` inside the success check block in proxy_daemon.py

**Error**: `BLOCKED: Would reduce file from 299 to 15 lines (>50% loss). This looks like a replacement, not an edit.`

**Root cause**: The Jr instruction included a code block showing the fix. The SmartExtract module interpreted this as the complete target file content, attempted to replace the entire 299-line file with a 15-line code snippet.

**Pattern**: When instructions contain `"Before (broken)" / "After (correct)"` code blocks, SmartExtract treats the "After" block as a full file replacement rather than a surgical edit.

**Remediation**: Write instructions using explicit FIND/REPLACE format:
```
FIND (exact match):
<exact lines to find>

REPLACE WITH:
<exact replacement lines>
```

This format triggers the executor's edit mode rather than its write-whole-file mode.

**Retry count**: 3 attempts, all blocked by same guardrail.

---

## Failure 2: File Type Security Gate (MOLTBOOK-SYSTEMD-001)

**Task**: Create systemd service file at `/ganuda/scripts/systemd/moltbook-proxy.service`

**Error**: `File type requires Chief approval: /ganuda/scripts/systemd/moltbook-proxy.service`

**Root cause**: The executor's security model flags `.service` files as privileged file types requiring Chief (human) approval before creation. This is a security feature, not a bug.

**Blocked file types (known)**:
- `.service` (systemd)
- `.timer` (systemd)
- `.conf` in `/etc/` paths
- Shell scripts in `/usr/local/bin/`

**Remediation**: For privileged file types, write the content to a staging path with a safe extension (e.g., `.service.staged`), and include explicit instructions for the human operator to review and move the file. Alternatively, flag these tasks as requiring manual deployment in the instruction itself.

---

## Failure 3: Path Resolution Default (MOLTBOOK-REPLY-DETECT-001, MOLTBOOK-SUBMOLT-SURF-001)

**Task**: Create new modules in `/ganuda/services/moltbook_proxy/`

**Actual output**: Files created in `/ganuda/backend/` instead

**Root cause**: The SmartExtract module resolves ambiguous file paths to a default project directory. When the instruction references "proxy_daemon.py" without the full absolute path in the code block header, the executor maps it to `/ganuda/backend/proxy_daemon.py` (a common backend directory pattern).

**Evidence**:
- `/ganuda/backend/mention_detector.py` (39 lines — shallow stub)
- `/ganuda/backend/submolt_scanner.py` (67 lines — shallow stub)
- `/ganuda/backend/proxy_daemon.py` (syntax errors, wrong content)
- `/ganuda/backend/modules/mention_detector.py` (duplicate)

**Remediation**: Always use FULL ABSOLUTE PATHS in every file reference within the instruction. Use the format:

```
FILE: /ganuda/services/moltbook_proxy/mention_detector.py
ACTION: CREATE NEW FILE
```

Never reference a file by just its basename. The executor cannot infer the correct directory from context alone.

---

## Failure 4: Implementation Depth Gap (MOLTBOOK-REPLY-DETECT-001, MOLTBOOK-SUBMOLT-SURF-001)

**Task**: Create ~520-line MentionDetector module and ~400-line SubmoltScanner module

**Actual output**: 39-line and 67-line stubs respectively

**Root cause**: The Jr executor has a context window and output length that constrains the size of generated code. When the instruction specifies a complex multi-method class with detailed specs, the executor produces a skeleton that satisfies the structural requirements but omits the implementation depth.

**Pattern**: Instructions specifying >200 lines of new code per file consistently produce shallow stubs.

**Remediation options**:
1. **Phased instructions**: Break large modules into phases. Phase 1: core class + constructor + 2 key methods. Phase 2: remaining methods. Phase 3: integration.
2. **Template approach**: Pre-create the file with the class skeleton (docstrings, method signatures, TODO markers), then write instructions to fill in specific methods.
3. **Smaller scope per task**: Each Jr task should target ≤150 lines of new code and ≤3 files modified.

---

## Failure 5: False Completion on FIND/REPLACE Format (MOLTBOOK-BUGFIX-COUNTER-002)

**Task**: Same counter bug fix as V1, rewritten using FIND/REPLACE format

**Result**: Task marked "completed" but **no edit was applied**. File unchanged.

**Root cause**: SmartExtract only extracts `bash` code blocks (fenced with ` ```bash `) as executable steps. The FIND/REPLACE text blocks and Python code blocks embedded in the edit context were treated as documentation. The executor extracted ONLY the Step 3 verification bash commands, ran them (syntax check passed because the file was always syntactically valid), and reported success.

**Evidence from result JSON**:
```json
"steps_executed": [{"type": "bash", "stdout": "SYNTAX OK\n...190: self.posts_today += 1\n", "success": true}]
```
Only 1 step executed (verification), not 3 (two edits + verification).

**Critical insight**: The Jr executor **cannot edit existing files**. It can:
1. Create new files (whole-file write)
2. Run bash commands
3. Run Python scripts

To edit an existing file, the edit must be packaged as a **bash heredoc with `python3 << 'EOF'`** or a **sed command** — something SmartExtract recognizes as an executable bash block.

**Remediation (V3)**: Package the file edit as a Python script inside a bash heredoc:
```bash
python3 << 'PYEOF'
with open('/path/to/file', 'r') as f:
    content = f.read()
content = content.replace('old_text', 'new_text')
with open('/path/to/file', 'w') as f:
    f.write(content)
PYEOF
```

---

## Summary Table

| Task ID | Failure Type | Guardrail | Recoverable | Fix Strategy |
|---------|-------------|-----------|-------------|--------------|
| BUGFIX-COUNTER-001 | Full-file replacement | Size reduction >50% | Yes — use FIND/REPLACE format | Rewrite instruction |
| BUGFIX-COUNTER-002 | False completion | None — verification passed, edit skipped | Yes — package as bash script | Rewrite as executable Python-in-bash |
| SYSTEMD-001 | Privileged file type | .service extension | No — needs manual deploy | Stage to .txt, human moves |
| SYSTEMD-002 | False completion | None — verification ran before file creation | Yes — package as bash heredoc | Rewrite as executable bash |
| REPLY-DETECT-001 | Wrong path + shallow | None (false completion) | Yes — explicit absolute paths | Rewrite with full paths |
| SUBMOLT-SURF-001 | Wrong path + shallow | None (false completion) | Yes — explicit absolute paths | Rewrite with full paths, phased |

---

## Rules for Future Jr Instructions

1. **Always use full absolute paths** for every file reference. Never use basenames alone.
2. **ALL file edits must be executable bash scripts** — use `python3 << 'EOF'` with `str.replace()` or `sed -i`. FIND/REPLACE format is NOT understood by the executor.
3. **ALL file creation must use bash heredocs** — use `cat > /path/to/file << 'EOF'`. Do not rely on the executor's file creation mode for anything other than simple Python scripts.
4. **Limit new code to ≤150 lines per file per task**. Break larger modules into phases.
5. **Flag privileged file types** (.service, .timer, .conf in /etc/) as requiring manual deployment.
6. **Include verification commands** that the executor can run to confirm correct paths and syntax.
7. **Test with `python -c "import ast; ast.parse(open('file').read())"` after every Python file write.
8. **Order bash steps so verification comes AFTER creation/edit**, not before.

---

*Reference: KB-JR-EXECUTOR-EDIT-CAPABILITY-GAP-JAN29-2026 documents the broader edit capability limitations.*

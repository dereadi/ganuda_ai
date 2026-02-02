# KB: Jr Executor False Completion and Failure Patterns — January 31, 2026

**Date:** January 31, 2026
**Author:** TPM (Claude Opus 4.5)
**Related Incidents:** Tasks #507 (false completion), #508 (SQL syntax), #509 (sudo failure)
**Related KB:** KB-JR-EXECUTOR-SEARCH-REPLACE-POSTMORTEM-JAN30-2026

---

## Summary

Three consecutive Jr tasks (#507, #508, #509) for the VetAssist resources page content strategy all failed or false-completed on January 31, 2026. Each failure had a distinct root cause, but all share a common theme: the Jr executor's step parser does not reliably handle multi-step instructions containing Python code blocks, multi-statement SQL, or system commands requiring elevated permissions.

---

## Incident Details

### Task #507 — Schema Migration (FALSE COMPLETION)

**Instruction:** Run 14 ALTER TABLE statements and 2 CREATE TABLE statements via psycopg2 Python script.

**What happened:** The executor reported `success: true` with `result: -1` and empty columns. It parsed the Python code block as a single SQL step and "executed" it, but the DDL never actually reached the database. All 12 new columns were absent from `educational_content` and the `vetassist_resource_links` table did not exist.

**Root cause:** The executor's SQL step handler cannot run multi-statement DDL through psycopg2 code blocks. It extracted the SQL from inside the Python `"""..."""` triple-quoted string but either:
- Ran it without a database connection
- Ran only the first statement and reported success on the DDL's -1 rowcount
- Silently failed and reported success because DDL doesn't return rows

**Detection:** Only caught by manually querying `information_schema.columns` after the task was marked complete.

**Impact:** Silent data corruption — downstream tasks #508 and #509 assumed the schema was ready.

### Task #508 — Article Expansion (SQL SYNTAX ERROR)

**Instruction:** Create a Python script (`expand_articles.py`) that uses psycopg2 with `%s` parameterized queries to UPDATE 17 articles.

**What happened:** The executor tried to run the SQL directly (not through Python/psycopg2), hitting `syntax error at or near "%"` because `%s` is a psycopg2 placeholder, not valid raw SQL.

**Root cause:** The executor's step parser saw SQL in a Python code block and extracted it as a raw SQL step. The `%s` placeholders are only valid when executed through psycopg2's parameterized query interface, not as standalone SQL.

**Retries:** Failed on all 3 attempts (initial + 2 retries) with the same error.

### Task #509 — Link Monitor Daemon (SUDO FAILURE)

**Instruction:** Create a Python script and set up a systemd timer (requires `sudo cp` and `sudo systemctl`).

**What happened:** The executor attempted to run `sudo` commands, which require a terminal password. Error: `sudo: a terminal is required to read the password`.

**Root cause:** The Jr executor runs as user `dereadi` without sudo access in its non-interactive shell. The instruction included `sudo` steps for systemd timer activation.

**Retries:** Failed on all 3 attempts with the same sudo error.

---

## Patterns Identified

### 1. False Completion on DDL

**Pattern:** Executor reports success for DDL statements even when they don't actually execute.

**Why dangerous:** Downstream tasks and human operators trust the completion status. The schema migration's false completion could have caused data loss if #508 had run INSERT statements against missing columns.

**Mitigation:** Jr instructions for DDL MUST include a verification SQL step that checks `information_schema.columns` or `pg_tables` and fails explicitly if expected objects are missing.

### 2. Python-in-SQL Confusion

**Pattern:** When an instruction contains Python code with embedded SQL (e.g., psycopg2 `cursor.execute("UPDATE ... SET content = %s", (value,))`), the executor extracts and runs the SQL as a standalone statement, causing syntax errors on parameterized placeholders (`%s`, `$1`, etc.).

**Mitigation:** Instructions that need parameterized queries should:
- Use BASH steps to run a pre-existing Python script (`./venv/bin/python scripts/foo.py`), not inline Python
- OR use WRITE steps to create the script first, then BASH steps to execute it
- NEVER embed `%s` or `$1` in SQL shown inside Python code blocks

### 3. Sudo Assumption

**Pattern:** Instructions include `sudo` commands for systemd, package installation, or file operations in system directories.

**Mitigation:** All Jr instructions must assume no sudo access. Steps requiring elevated permissions should be:
- Flagged as "MANUAL STEP — requires sudo" in the instruction
- Separated into a distinct manual checklist at the end of the instruction
- Never mixed into automated steps

### 4. Multi-Statement SQL Unreliability

**Pattern:** The executor handles single SQL statements reasonably well but fails on multi-statement blocks (multiple ALTER TABLE, CREATE TABLE + INSERT, etc.).

**Mitigation:** Split multi-statement SQL into individual steps, each with its own verification query.

---

## Recommendations

1. **Add verification steps to every DDL instruction.** A SELECT against information_schema that explicitly fails if the expected change is missing.

2. **Never use psycopg2 %s placeholders in instruction SQL.** Either create a script file and run it, or use literal values in the SQL.

3. **Tag all sudo steps as manual.** The executor cannot escalate privileges.

4. **Split large operations into separate tasks.** One task per file modification. The executor handles single-file SEARCH/REPLACE better than multi-file.

5. **Post-completion verification should be a separate task** that queries the database and checks file existence, independent of the execution task.

6. **Consider a "canary query" pattern:** After any database modification task, automatically run a SELECT that the TPM can review in the task result to confirm the change took effect.

---

## Resolution

All three tasks were completed manually by the TPM:
- #507: DDL run directly via psql
- #508: Python expansion script created by subagent and run via `./venv/bin/python scripts/expand_articles.py`
- #509: Link monitor script created manually, systemd timer files created (activation requires sudo — flagged as manual step)

The Jr executor's fundamental limitation is that it parses markdown instructions into step types (SQL, BASH, SEARCH/REPLACE, WRITE) but does not have a Python step type. Instructions containing Python are misinterpreted as SQL or ignored entirely.

---

## Related

- KB-JR-EXECUTOR-SEARCH-REPLACE-POSTMORTEM-JAN30-2026 — SmartExtract filepath loss pattern
- ULTRATHINK-VETASSIST-RESOURCES-CONTENT-STRATEGY-JAN31-2026 — The parent strategy document

---

*Cherokee AI Federation — For Seven Generations*

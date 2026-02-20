# Jr Instruction: Add Config Languages to Executor Whitelist

**Task ID:** EXECUTOR-FIX-004
**Priority:** P1
**Assigned To:** Software Engineer Jr.
**Date:** February 10, 2026
**KB:** KB-RLM-INTERCEPTION-LENGTH-THRESHOLD-BUG-FEB10-2026.md

## Context

The executor silently skips code blocks tagged with config file languages (`ini`, `toml`, `conf`, `cfg`, `text`). Only `python`, `typescript`, `javascript`, `yaml`, `json` are recognized. This causes "No executable steps found" for any instruction that creates config files.

## Edit 1: Expand language whitelist

File: `/ganuda/jr_executor/task_executor.py`

```
<<<<<<< SEARCH
            elif lang.lower() in ('python', 'typescript', 'javascript', 'yaml', 'json'):
=======
            elif lang.lower() in ('python', 'typescript', 'javascript', 'yaml', 'json',
                                   'ini', 'toml', 'conf', 'cfg', 'text', 'env', 'properties'):
>>>>>>> REPLACE
```

## Do NOT

- Do not modify the sql or bash handlers above this line
- Do not remove any existing languages from the whitelist
- Do not modify the file path detection logic below this line

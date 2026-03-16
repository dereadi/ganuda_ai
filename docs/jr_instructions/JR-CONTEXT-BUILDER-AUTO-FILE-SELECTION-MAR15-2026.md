# Jr Instruction: Context Builder — AI-Assisted File Selection for Jr Tasks

**Task ID**: To be assigned
**Priority**: P3
**Story Points**: 3
**Node**: redfin
**Prerequisites**: Specification Engineering Layer (deployed Feb 27)
**Source**: Sam Walton floor walk — Alex Ziskind / Reprompt context builder pattern (Mar 15 2026)

## Context

Alex Ziskind's video showed Reprompt's "context builder" — an AI that selects only relevant files from a codebase before constructing a prompt. He went from 11M tokens (everything) down to 831K tokens (code files only) through AI-guided selection. Without it, models choke or hallucinate.

We already have the skeleton of this in our Specification Engineering Layer: `target_files` and `target_file_hashes` columns on `project_specifications`. But today those are filled manually by the TPM when writing specs. A Jr writing a task has to know which files matter. That's a bottleneck.

**The idea**: When a Jr task or specification is created, automatically suggest the relevant files based on the task description, acceptance criteria, and codebase structure. The Jr (or TPM) confirms or adjusts, then only those files get loaded into context.

## What Reprompt Does (Patterns to Steal)

1. **Code map**: Tree structure of the entire repo (paths only, no content). Cheap to generate, fits in any context window.
2. **AI file selector**: Given the code map + a task description, an LLM selects which files are relevant. Returns a list of paths.
3. **Content assembly**: Only selected files get their contents included in the prompt.
4. **Iterative refinement**: User can chat with the selector to add/remove files.

## What We Build (Adapted to Our Architecture)

### Function: `suggest_target_files(task_description, acceptance_criteria, constraints=None)`

**Location**: `/ganuda/lib/context_builder.py`

**Input**:
- `task_description` (str) — what the task is about
- `acceptance_criteria` (str) — what done looks like
- `constraints` (str, optional) — any scope limits

**Process**:
1. Generate code map of `/ganuda/` — file paths only, filtered to code files (`.py`, `.js`, `.rs`, `.sql`, `.yaml`, `.json`, `.html`, `.css`). Exclude `venv/`, `node_modules/`, `target/`, `__pycache__/`, `.git/`.
2. Send code map + task description to local model (Qwen on bmasass or Llama on sasass2) via sub_agent_dispatch.
3. Model returns ranked list of relevant file paths with brief reason for each.
4. Return list with SHA256 hashes (for `target_file_hashes` column).

**Output**:
```python
{
    "suggested_files": [
        {"path": "lib/chain_protocol.py", "reason": "Contains outbound_scrub() referenced in task", "hash": "a3b2c1..."},
        {"path": "services/gateway/gateway.py", "reason": "Main gateway service, task modifies routing", "hash": "d4e5f6..."}
    ],
    "code_map_tokens": 4200,      # how big the map was
    "total_content_tokens": 18500  # estimated tokens if all suggested files loaded
}
```

### Integration Points

1. **Jr Executor** (`/ganuda/services/jr_executor/`): When a Jr task starts, call `suggest_target_files()` and populate the specification's `target_files` if empty. Jr loads only those files into context.

2. **Specification creation** (`project_specifications` table): When TPM writes a spec without `target_files`, auto-suggest and populate. TPM reviews in the spec approval step.

3. **Kanban UI**: Show suggested files in the task detail view. Allow manual add/remove.

### Code Map Generator

```python
import os
import hashlib

def generate_code_map(root="/ganuda", extensions=None, exclude_dirs=None):
    """Generate a tree of code file paths. No content, just structure."""
    if extensions is None:
        extensions = {'.py', '.js', '.rs', '.sql', '.yaml', '.yml', '.json', '.html', '.css', '.toml'}
    if exclude_dirs is None:
        exclude_dirs = {'venv', 'node_modules', 'target', '__pycache__', '.git', 'site-packages'}

    tree = []
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune excluded directories
        dirnames[:] = [d for d in dirnames if d not in exclude_dirs]
        for f in filenames:
            if any(f.endswith(ext) for ext in extensions):
                full = os.path.join(dirpath, f)
                rel = os.path.relpath(full, root)
                tree.append(rel)
    tree.sort()
    return tree
```

This is the cheap part — the entire `/ganuda/` code map is probably ~2K tokens. The expensive part is loading file contents, which is exactly what we're trying to avoid.

## Why This Matters (DC-9)

Alex burned 2TB of VRAM and 1,800 watts for 14 minutes to scan code that grep handles in milliseconds. His problem was indiscriminate context stuffing. Our Jr tasks already scope better than that, but auto-file-selection makes it systematic:

- **Jr context windows stay small** — load 5-15 files instead of hoping the Jr knows which ones matter
- **Reduces hallucination** — less irrelevant code in context means fewer invented function names
- **Speeds up Jr execution** — smaller prompt = faster inference on local models
- **Specification quality improves** — `target_files` populated automatically instead of guessed

## Testing

1. **Accuracy test**: Run `suggest_target_files()` against 5 completed Jr tasks where we know which files were actually modified. Compare suggested vs actual. Target: >70% overlap.

2. **Token budget test**: Verify that suggested file contents fit within model context window (8K for Qwen 2.5-Coder:32b on sasass2, 32K for Llama on bmasass).

3. **Code map size**: Verify `/ganuda/` code map is under 5K tokens. If larger, add more exclusions.

4. **Round-trip**: Create a test specification with `suggest_target_files()` output → verify `target_files` and `target_file_hashes` columns populated correctly.

## Constraints

- Use LOCAL models only via `sub_agent_dispatch`. This is a code map — no reason to send our file tree to a frontier API.
- Code map only, never send file contents in the suggestion phase. Contents only loaded after files are selected.
- Do not auto-populate `target_files` if the spec already has them filled. Respect manual overrides.
- The code map generator must handle symlinks gracefully (don't follow, just skip).

## Definition of Done

- [ ] `generate_code_map()` produces clean file tree of `/ganuda/`
- [ ] `suggest_target_files()` returns ranked file list with reasons
- [ ] Integration with Jr executor — auto-suggests files when spec has empty `target_files`
- [ ] Tested against 5 historical Jr tasks with >70% file overlap
- [ ] Uses local model only (no frontier API calls)

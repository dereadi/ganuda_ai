"""Tests for the 5-strategy fallback chain in jr_plan_parser.

Cherokee AI Federation — Council fix plan 2026-05-15.
Supersedes Jr's stub (#1670 failed — recursive trap).

Strategy ordering (each cascades only if previous yielded zero file actions):
1. Triple-backtick ```plan`` block with PROJECT_NAME / FILES_TO_CREATE: sections
2. Markdown header sections (## FILES TO CREATE / ## MODIFY / etc.)
3. Absolute-path scan via extract_any_absolute_paths
4. JSON extraction (```json blocks or raw {...} with files_to_create keys)
5. Instruction-text overrides (CREATE FILE: / MODIFY FILE: in operator text)

Strategy 5 lives in extract_files_from_prose (operates on instructions, not
LLM response) and short-circuits all other prose patterns when present.
"""

import sys
from pathlib import Path

# Make /ganuda importable for `from lib.jr_plan_parser import ...`
_GANUDA_ROOT = Path(__file__).resolve().parent.parent
if str(_GANUDA_ROOT) not in sys.path:
    sys.path.insert(0, str(_GANUDA_ROOT))

import pytest  # noqa: E402

from lib.jr_plan_parser import (  # noqa: E402
    extract_files_from_prose,
    parse_planning_response,
    _extract_markdown_header_sections,
    _extract_json_files,
    _extract_instruction_overrides,
    extract_any_absolute_paths,
)


# ---------------------------------------------------------------------------
# Strategy 1 — triple-backtick ```plan`` block (existing — sanity)
# ---------------------------------------------------------------------------

class TestStrategy1TripleBacktickPlan:
    def test_extracts_files_from_plan_block(self):
        response = """
```plan
PROJECT_NAME: TestProject
FOCUS: Build the thing

FILES_TO_CREATE:
- /ganuda/lib/foo.py: New module
- /ganuda/lib/bar.py: Helper

FILES_TO_MODIFY:
- /ganuda/lib/baz.py: Wire foo in

STEPS:
- [ ] Step 1: Create foo
- [ ] Step 2: Wire baz
```
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        modifies = [p for p, _ in result['files_to_modify']]
        assert '/ganuda/lib/foo.py' in creates
        assert '/ganuda/lib/bar.py' in creates
        assert '/ganuda/lib/baz.py' in modifies
        assert len(result['steps']) == 2


# ---------------------------------------------------------------------------
# Strategy 2 — markdown header sections
# ---------------------------------------------------------------------------

class TestStrategy2MarkdownHeaders:
    def test_files_to_create_section(self):
        response = """
Here's my plan:

## FILES TO CREATE
- /ganuda/lib/new_module.py
- `/ganuda/tests/test_new_module.py`: Test coverage

Some prose between sections is fine.

## FILES TO MODIFY
- /ganuda/lib/router.py: register new module
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        modifies = [p for p, _ in result['files_to_modify']]
        assert '/ganuda/lib/new_module.py' in creates
        assert '/ganuda/tests/test_new_module.py' in creates
        assert '/ganuda/lib/router.py' in modifies

    def test_create_files_header_variant(self):
        response = """
## CREATE FILES
- /tmp/data.csv

### EDIT
- /etc/nginx/conf.d/site.conf
"""
        sections = _extract_markdown_header_sections(response)
        creates = [p for p, _ in sections['files_to_create']]
        modifies = [p for p, _ in sections['files_to_modify']]
        assert '/tmp/data.csv' in creates
        assert '/etc/nginx/conf.d/site.conf' in modifies

    def test_does_not_run_if_strategy_1_succeeded(self):
        """Cascade discipline: strategy 2 must not fire if strategy 1 extracted files."""
        response = """
```plan
FILES_TO_CREATE:
- /ganuda/lib/from_strategy_1.py: Win
```

## FILES TO CREATE
- /ganuda/lib/from_strategy_2.py
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        assert '/ganuda/lib/from_strategy_1.py' in creates
        assert '/ganuda/lib/from_strategy_2.py' not in creates

    def test_rejects_placeholder_paths(self):
        response = """
## FILES TO CREATE
- /path/to/your/file.py
- /ganuda/lib/real_file.py
"""
        sections = _extract_markdown_header_sections(response)
        creates = [p for p, _ in sections['files_to_create']]
        assert '/path/to/your/file.py' not in creates
        assert '/ganuda/lib/real_file.py' in creates


# ---------------------------------------------------------------------------
# Strategy 4 (cascade-order; KB-named Strategy 3) — absolute-path scan
# ---------------------------------------------------------------------------

class TestStrategy3PathScan:
    def test_picks_up_paths_without_section_headers(self):
        response = """
I think we should create /ganuda/lib/orphan.py and also write to /tmp/cache/state.json.
The existing module at /ganuda/lib/main.py needs updating.
"""
        result = parse_planning_response(response)
        all_paths = (
            [p for p, _ in result['files_to_create']]
            + [p for p, _ in result['files_to_modify']]
        )
        assert '/ganuda/lib/orphan.py' in all_paths
        assert '/tmp/cache/state.json' in all_paths
        assert '/ganuda/lib/main.py' in all_paths


# ---------------------------------------------------------------------------
# Strategy 4 — JSON extraction
# ---------------------------------------------------------------------------

class TestStrategy4JsonExtraction:
    def test_fenced_json_block_with_string_paths(self):
        response = """
Here is the plan as JSON:

```json
{
  "files_to_create": ["/ganuda/lib/api.py", "/ganuda/tests/test_api.py"],
  "files_to_modify": ["/ganuda/lib/router.py"]
}
```
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        modifies = [p for p, _ in result['files_to_modify']]
        assert '/ganuda/lib/api.py' in creates
        assert '/ganuda/tests/test_api.py' in creates
        assert '/ganuda/lib/router.py' in modifies

    def test_fenced_json_with_dict_entries(self):
        response = """
```json
{
  "files_to_create": [
    {"path": "/ganuda/lib/svc.py", "description": "Service module"},
    {"path": "/ganuda/lib/cli.py", "purpose": "CLI entry point"}
  ]
}
```
"""
        result = _extract_json_files(response)
        creates = dict(result['files_to_create'])
        assert '/ganuda/lib/svc.py' in creates
        assert creates['/ganuda/lib/svc.py'] == 'Service module'
        assert '/ganuda/lib/cli.py' in creates
        assert creates['/ganuda/lib/cli.py'] == 'CLI entry point'

    def test_bare_json_object_no_fences(self):
        response = '{"files_to_create": ["/ganuda/lib/x.py"], "files_to_modify": []}'
        result = _extract_json_files(response)
        assert ('/ganuda/lib/x.py', 'From JSON response') in result['files_to_create']

    def test_json_wins_over_path_scan(self):
        """JSON (strategy 3 in cascade order) wins over path-scan (strategy 4).

        Even though `/ganuda/lib/from_path_scan.py` appears in prose, when a
        JSON block IS present it takes authoritative precedence and path-scan
        does not run.
        """
        response = """
Will create /ganuda/lib/from_path_scan.py mentioned in prose.

```json
{"files_to_create": ["/ganuda/lib/from_json.py"]}
```
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        assert '/ganuda/lib/from_json.py' in creates
        assert '/ganuda/lib/from_path_scan.py' not in creates

    def test_malformed_json_returns_empty_not_raises(self):
        response = '```json\n{"files_to_create": [unclosed,\n```'
        result = _extract_json_files(response)
        assert result == {'files_to_create': [], 'files_to_modify': []}


# ---------------------------------------------------------------------------
# Strategy 5 — instruction-text overrides
# ---------------------------------------------------------------------------

class TestStrategy5InstructionOverrides:
    def test_create_file_directive(self):
        instructions = """
# Some task

CREATE FILE: /ganuda/lib/explicit_create.py

Then update the router.
"""
        result = _extract_instruction_overrides(instructions)
        assert '/ganuda/lib/explicit_create.py' in result['files_to_create']

    def test_modify_file_directive(self):
        instructions = "MODIFY FILE: /ganuda/lib/router.py\nAdd a new route."
        result = _extract_instruction_overrides(instructions)
        assert '/ganuda/lib/router.py' in result['files_to_modify']

    def test_multiple_directives(self):
        instructions = """
CREATE FILE: /ganuda/lib/a.py
CREATE FILES: /ganuda/lib/b.py
MODIFY FILE: /ganuda/lib/c.py
UPDATE: /ganuda/lib/d.py
EDIT: /ganuda/lib/e.py
"""
        result = _extract_instruction_overrides(instructions)
        assert result['files_to_create'] == ['/ganuda/lib/a.py', '/ganuda/lib/b.py']
        assert result['files_to_modify'] == [
            '/ganuda/lib/c.py', '/ganuda/lib/d.py', '/ganuda/lib/e.py'
        ]

    def test_override_short_circuits_extract_files_from_prose(self):
        instructions = """
Background prose mentioning /ganuda/lib/background.py for context.

CREATE FILE: /ganuda/lib/authoritative.py
"""
        result = extract_files_from_prose(instructions)
        # Operator-direct override wins; background-prose path is NOT extracted.
        assert result['files_to_create'] == ['/ganuda/lib/authoritative.py']
        assert '/ganuda/lib/background.py' not in result['files_to_create']
        assert '/ganuda/lib/background.py' not in result['files_to_modify']

    def test_rejects_placeholder_in_directive(self):
        instructions = "CREATE FILE: /path/to/your/example.py"
        result = _extract_instruction_overrides(instructions)
        assert result['files_to_create'] == []


# ---------------------------------------------------------------------------
# Integration — full cascade behavior end-to-end
# ---------------------------------------------------------------------------

class TestCascadeIntegration:
    def test_strategy_1_wins_when_all_present(self):
        response = """
```plan
FILES_TO_CREATE:
- /ganuda/lib/s1.py: from strategy 1
```

## FILES TO CREATE
- /ganuda/lib/s2.py

I think we'll need /ganuda/lib/s3.py too.

```json
{"files_to_create": ["/ganuda/lib/s4.py"]}
```
"""
        result = parse_planning_response(response)
        creates = [p for p, _ in result['files_to_create']]
        assert creates == ['/ganuda/lib/s1.py']

    def test_json_fires_when_1_2_empty(self):
        response = """
Some prose without any structured plan or markdown sections.

```json
{"files_to_modify": ["/ganuda/lib/only_json.py"]}
```
"""
        result = parse_planning_response(response)
        modifies = [p for p, _ in result['files_to_modify']]
        assert '/ganuda/lib/only_json.py' in modifies

    def test_path_scan_fires_when_1_2_3_empty(self):
        """Final-resort path-scan fires when no structured/markdown/JSON found."""
        response = "Just unstructured prose. Touch /ganuda/lib/only_prose.py please."
        result = parse_planning_response(response)
        all_paths = (
            [p for p, _ in result['files_to_create']]
            + [p for p, _ in result['files_to_modify']]
        )
        assert '/ganuda/lib/only_prose.py' in all_paths

    def test_empty_response_returns_empty_lists(self):
        result = parse_planning_response("")
        assert result['files_to_create'] == []
        assert result['files_to_modify'] == []
        assert result['steps'] == []

    def test_unblocks_no_executable_steps_failure_mode(self):
        """Regression test for kanban #1661 failure: 'No executable steps found in instruction file'.

        Before this fix the LLM-response style below would yield empty file lists
        and the executor would fail with NoExecutableSteps. Now strategy 2 (markdown)
        picks it up.
        """
        llm_response = """
I'll structure the foundation agent work as follows.

## FILES TO CREATE
- /ganuda/lib/foundation_agents/world_model.py
- /ganuda/lib/foundation_agents/predictive_sim.py

## STEPS
1. Build the world model class
2. Wire predictive simulation
"""
        result = parse_planning_response(llm_response)
        creates = [p for p, _ in result['files_to_create']]
        assert '/ganuda/lib/foundation_agents/world_model.py' in creates
        assert '/ganuda/lib/foundation_agents/predictive_sim.py' in creates
        # At least one step recorded (either from markdown body or auto-generated)
        assert len(result['steps']) >= 1


# ---------------------------------------------------------------------------
# Helper sanity — extract_any_absolute_paths (existing May 12 work)
# ---------------------------------------------------------------------------

class TestExtractAnyAbsolutePathsSanity:
    def test_widened_prefixes(self):
        text = "Touch /ganuda/x.py and /tmp/y.log and /etc/nginx.conf and /home/u/.bashrc."
        paths = extract_any_absolute_paths(text)
        assert '/ganuda/x.py' in paths
        assert '/tmp/y.log' in paths
        assert '/etc/nginx.conf' in paths
        assert '/home/u/.bashrc' in paths

    def test_excludes_placeholders(self):
        text = "Make /path/to/your/file.py and /your/path/here.py."
        paths = extract_any_absolute_paths(text)
        assert paths == []

    def test_excludes_unknown_prefix(self):
        text = "Touch /random/unknown/file.py."
        paths = extract_any_absolute_paths(text)
        assert paths == []

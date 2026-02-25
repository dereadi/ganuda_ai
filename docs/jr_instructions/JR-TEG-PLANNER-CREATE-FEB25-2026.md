# TEG Planner — Topological Execution Graph Decomposer

**Task**: Create the TEG planner module
**Priority**: P0 — Sacred Fire 90
**Council Vote**: #ec088d89 — PROCEED WITH CAUTION (0.843)
**Constitutional**: Council stays fixed star (#82856). TEG is Jr layer ONLY.

---

## Overview

The TEG planner decomposes complex multi-operation Jr instructions into isolated atomic graph nodes BEFORE the executor processes them. Each node becomes its own Jr task with one operation, one target file, and explicit dependency tracking.

**Root cause it solves**: batch processing of heterogeneous steps causes mixed-step-type silent failures, context collapse, and retry duplication (KB-EXECUTOR-MIXED-STEP-TYPES, KB-DLQ-TRIAGE-PATTERNS).

---

Create `/ganuda/jr_executor/teg_planner.py`

```python
#!/usr/bin/env python3
"""
Topological Execution Graph (TEG) Planner for Cherokee Jr Executor

Decomposes complex multi-operation instructions into isolated atomic
graph nodes BEFORE the executor processes them. Each node = one operation
= one file = one Jr task.

Council Vote: #ec088d89 — PROCEED WITH CAUTION (0.843)
Constitutional: Council stays fixed star (#82856). TEG is Jr layer ONLY.
KB: KB-OPENSAGE-ALPHAEVOLVE-DISCRETE-TOPOLOGY-FEB25-2026.md

For Seven Generations - Cherokee AI Federation
"""

import os
import re
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict


class TEGPlanner:
    """
    Decomposes a complex Jr instruction into a DAG of atomic tasks.

    Design principles (from OpenSage + KB corpus):
    1. One operation type per node (never mix Create + SR)
    2. Same-file nodes are sequential (directed dependency edges)
    3. Different-file nodes are parallel (no edges)
    4. Always use_rlm=false on child nodes
    5. Always set assigned_jr (inherited from parent)
    6. No 'research' substring in child titles
    """

    def expand_task(self, task: dict) -> bool:
        """
        Main entry point. Called by jr_queue_worker when teg_plan=true.

        Reads the instruction, decomposes into atomic nodes, inserts
        child tasks into jr_work_queue, and blocks the parent.

        Returns True if expansion succeeded, False if it failed
        (caller should fall through to normal execution).
        """
        import sys
        sys.path.insert(0, '/ganuda')

        parent_id = task.get('id')
        parent_title = task.get('title', 'unknown')

        print(f"[TEG] Expanding task #{parent_id}: {parent_title}")

        # 1. Read instruction
        instructions = self._read_instructions(task)
        if not instructions:
            print(f"[TEG] No instructions found for task #{parent_id}")
            return False

        # 2. Parse all blocks (SR + Create)
        blocks = self._parse_all_blocks(instructions)
        if not blocks:
            print(f"[TEG] No parseable blocks found — skipping TEG expansion")
            return False

        if len(blocks) <= 1:
            print(f"[TEG] Only 1 block found — no decomposition needed")
            return False

        print(f"[TEG] Found {len(blocks)} blocks across "
              f"{len(set(b['filepath'] for b in blocks))} files")

        # 3. Build file-level DAG
        dag = self._build_file_dag(blocks)

        # 4-6. Write files, insert nodes, update parent (in one transaction)
        return self._execute_expansion(task, dag, instructions)

    def _read_instructions(self, task: dict) -> Optional[str]:
        """Read instruction content from task (inline or file)."""
        # Inline content takes priority (same as task_executor.py)
        content = task.get('instruction_content')
        if content:
            return content

        filepath = task.get('instruction_file')
        if filepath and os.path.isfile(filepath):
            try:
                with open(filepath, 'r') as f:
                    return f.read()
            except Exception as e:
                print(f"[TEG] Failed to read instruction file {filepath}: {e}")
                return None

        return None

    def _parse_all_blocks(self, instructions: str) -> List[Dict]:
        """
        Parse all SR blocks and Create blocks from instruction text.

        Returns list of dicts:
            {op_type, filepath, content, search, replace, position}

        Follows SR-FIRST extraction order (KB-JR-EXECUTOR-SR-FIRST-EXTRACTION-FIX).
        """
        blocks = []

        # Phase 1: Extract SR blocks first (same pattern as search_replace_editor.py)
        sr_pattern = r'<<<<<<< SEARCH\n(.*?)\n=======\n(.*?)\n>>>>>>> REPLACE'
        sr_ranges = []

        for match in re.finditer(sr_pattern, instructions, re.DOTALL):
            search_text = match.group(1)
            replace_text = match.group(2)
            block_start = match.start()
            sr_ranges.append((match.start(), match.end()))

            # Extract filepath from preceding text (within 500 chars)
            preceding = instructions[max(0, block_start - 500):block_start]
            filepath = self._extract_filepath(preceding)

            if filepath:
                blocks.append({
                    'op_type': 'search_replace',
                    'filepath': filepath,
                    'search': search_text,
                    'replace': replace_text,
                    'content': None,
                    'position': block_start
                })

        # Phase 2: Extract Create blocks (skip any overlapping with SR ranges)
        create_pattern = r'Create\s+`([^`]+)`\s*\n+```\w*\n(.*?)```'
        for match in re.finditer(create_pattern, instructions, re.DOTALL):
            # Check overlap with SR ranges
            if any(s <= match.start() <= e or s <= match.end() <= e
                   for s, e in sr_ranges):
                continue

            filepath = match.group(1).strip()
            content = match.group(2)

            # Ensure absolute path
            if not os.path.isabs(filepath):
                filepath = f"/ganuda/{filepath}"

            blocks.append({
                'op_type': 'create',
                'filepath': filepath,
                'content': content,
                'search': None,
                'replace': None,
                'position': match.start()
            })

        # Sort by position in original instruction (preserves author intent)
        blocks.sort(key=lambda b: b['position'])

        return blocks

    def _extract_filepath(self, text: str) -> Optional[str]:
        """Extract file path from prose text preceding an SR block.

        Same patterns as search_replace_editor.py._extract_filepath().
        """
        patterns = [
            r'\*\*File:\*\*\s*`([^`]+)`',
            r'File:\s*`([^`]+)`',
            r'Modify:\s*`([^`]+)`',
            r'Create\s+`([^`]+)`',
            r'Edit:\s*`([^`]+)`',
            r'In\s+`([^`]+)`',
            r'\n(/ganuda/[^\s\n]+\.\w+)\s*\n',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                filepath = match.group(1).strip('`').strip()
                if not os.path.isabs(filepath):
                    filepath = f"/ganuda/{filepath}"
                return filepath

        return None

    def _build_file_dag(self, blocks: List[Dict]) -> List[Dict]:
        """
        Build a DAG from parsed blocks based on file-level dependencies.

        Rules:
        - Same-file blocks get sequential dependency edges (ordered by position)
        - Different-file blocks have no edges (can execute in parallel)

        Returns enriched block list with 'node_id' and 'deps' fields.
        """
        # Group blocks by filepath
        file_groups = defaultdict(list)
        for i, block in enumerate(blocks):
            block['node_id'] = f"n{i:02d}"
            file_groups[block['filepath']].append(block)

        # Build dependency edges: within same file, each block depends on previous
        for filepath, group in file_groups.items():
            for j, block in enumerate(group):
                if j == 0:
                    block['deps'] = []
                else:
                    block['deps'] = [group[j - 1]['node_id']]

        return blocks

    def _execute_expansion(self, task: dict, dag: List[Dict],
                           instructions: str) -> bool:
        """Write node files, insert child tasks, update parent. All in one tx."""
        import psycopg2
        from lib.secrets_loader import get_db_config

        parent_id = task.get('id')
        parent_title = task.get('title', 'unknown')
        assigned_jr = task.get('assigned_jr', 'Software Engineer Jr.')
        sacred_fire = task.get('sacred_fire_priority', False)
        date_str = datetime.now().strftime('%b%d').upper()

        conn = psycopg2.connect(**get_db_config())
        node_ids = []

        try:
            cur = conn.cursor()

            for node in dag:
                # Write instruction file for this node
                node_filename = (f"JR-TEG-{parent_id}-"
                                 f"{node['node_id'].upper()}-{date_str}-2026.md")
                node_filepath = f"/ganuda/docs/jr_instructions/{node_filename}"

                node_instruction = self._build_node_instruction(
                    node, parent_id, parent_title
                )

                os.makedirs(os.path.dirname(node_filepath), exist_ok=True)
                with open(node_filepath, 'w') as f:
                    f.write(node_instruction)

                print(f"[TEG] Wrote node instruction: {node_filepath}")

                # Generate task_id hash
                task_id_hash = hashlib.md5(
                    f"teg-{parent_id}-{node['node_id']}-"
                    f"{datetime.now().isoformat()}".encode()
                ).hexdigest()

                # Determine initial status
                status = 'pending' if not node['deps'] else 'blocked'

                # Build node title (no 'research' substring!)
                basename = os.path.basename(node['filepath'])
                title = (f"[TEG] {parent_title[:80]} - "
                         f"{node['op_type']} {basename}")

                # Build parameters
                node_params = json.dumps({
                    'teg_node_id': node['node_id'],
                    'teg_parent_id': parent_id,
                    'teg_deps': node['deps'],
                    'teg_target_file': node['filepath'],
                    'teg_op_type': node['op_type']
                })

                cur.execute("""
                    INSERT INTO jr_work_queue
                        (task_id, title, instruction_file, assigned_jr,
                         sacred_fire_priority, parent_task_id, parameters,
                         source, created_by, use_rlm, status)
                    VALUES (%s, %s, %s, %s, %s, %s, %s,
                            'teg', 'teg_planner', false, %s)
                    RETURNING id
                """, (
                    task_id_hash, title, node_filepath, assigned_jr,
                    sacred_fire, parent_id, node_params, status
                ))

                queue_id = cur.fetchone()[0]
                node_ids.append(queue_id)
                node['queue_id'] = queue_id

                print(f"[TEG] Queued node #{queue_id} ({node['node_id']}): "
                      f"{status} — {node['op_type']} {basename}")

            # Update parent: blocked + teg_expanded
            parent_params = task.get('parameters') or {}
            if isinstance(parent_params, str):
                parent_params = json.loads(parent_params)

            parent_params['teg_expanded'] = True
            parent_params['teg_node_count'] = len(dag)
            parent_params['teg_node_ids'] = node_ids

            cur.execute("""
                UPDATE jr_work_queue
                SET status = 'blocked',
                    status_message = %s,
                    parameters = %s
                WHERE id = %s
            """, (
                f'TEG: expanded into {len(dag)} child nodes',
                json.dumps(parent_params),
                parent_id
            ))

            # Log thermal memory breadcrumb
            try:
                file_summary = ', '.join(sorted(set(
                    os.path.basename(n['filepath']) for n in dag
                )))
                cur.execute("""
                    INSERT INTO thermal_memory_archive
                        (original_content, temperature_score,
                         sacred_pattern, memory_hash, metadata)
                    VALUES (%s, %s, false, %s, %s)
                """, (
                    f"TEG Expansion: Task #{parent_id} '{parent_title}' "
                    f"decomposed into {len(dag)} atomic nodes. "
                    f"Files: {file_summary}. "
                    f"Parallel groups: {len(set(n['filepath'] for n in dag))} files. "
                    f"Sequential chains: "
                    f"{sum(1 for n in dag if n['deps'])} dependency edges.",
                    60,
                    hashlib.sha256(
                        f"teg-expansion-{parent_id}-{datetime.now().isoformat()}"
                        .encode()
                    ).hexdigest(),
                    json.dumps({
                        'type': 'teg_expansion',
                        'parent_task_id': parent_id,
                        'node_count': len(dag),
                        'child_queue_ids': node_ids,
                        'files': list(set(n['filepath'] for n in dag)),
                        'timestamp': datetime.now().isoformat()
                    })
                ))
            except Exception as tm_err:
                print(f"[TEG] Thermal breadcrumb failed (non-fatal): {tm_err}")

            conn.commit()
            print(f"[TEG] Successfully expanded task #{parent_id} into "
                  f"{len(dag)} nodes")
            return True

        except Exception as e:
            conn.rollback()
            print(f"[TEG] Expansion failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            conn.close()

    def _build_node_instruction(self, node: Dict, parent_id: int,
                                 parent_title: str) -> str:
        """Build a standalone instruction file for a single TEG node."""
        header = (
            f"# [TEG] {parent_title} - Node {node['node_id']}\n\n"
            f"**Parent Task**: #{parent_id}\n"
            f"**Auto-decomposed by TEG Planner**: {datetime.now().isoformat()}\n"
            f"**Operation**: {node['op_type']}\n"
            f"**Target File**: `{node['filepath']}`\n"
        )

        if node['deps']:
            header += f"**Dependencies**: {', '.join(node['deps'])}\n"

        header += "\n---\n\n"

        if node['op_type'] == 'search_replace':
            body = (
                f"File: `{node['filepath']}`\n\n"
                f"<<<<<<< SEARCH\n"
                f"{node['search']}\n"
                f"=======\n"
                f"{node['replace']}\n"
                f">>>>>>> REPLACE\n"
            )
        elif node['op_type'] == 'create':
            body = (
                f"Create `{node['filepath']}`\n\n"
                f"```python\n"
                f"{node['content']}"
                f"```\n"
            )
        else:
            body = f"<!-- Unknown op_type: {node['op_type']} -->\n"

        return header + body
```

# Jr Instructions: Thermal Memory REPL Sandbox

**Date:** January 4, 2026
**Priority:** HIGH
**Council Decision:** APPROVED (85% confidence, Operations Chief)
**Security Caveat:** "Implement robust security measures to prevent unauthorized access"
**Research Basis:** MIT RLM Paper (arXiv:2512.24601)

---

## Executive Summary

This document specifies a **Python REPL Sandbox** for Jr agents to programmatically access thermal memory. Based on MIT's RLM research principle of treating data as an "external environment" rather than stuffing it into context, this sandbox allows Jrs to search, filter, grep, and analyze 6700+ archived memories without context rot.

**Key RLM Insight:** Models benefit from Python REPL access to external data environments. Instead of loading all memories into context, Jrs write code to query what they need.

---

## Architecture Overview

```
┌────────────────────────────────────────────────────────────────────────┐
│                         JR AGENT (Fresh Context)                        │
│                                                                         │
│   Query: "Find all decisions about GPU allocation in last 30 days"     │
│                                                                         │
│   Jr writes Python code:                                                │
│   ┌──────────────────────────────────────────────────────────────────┐ │
│   │ results = thermal.search(                                         │ │
│   │     query="GPU allocation",                                       │ │
│   │     date_range=("2025-12-05", "2026-01-04"),                     │ │
│   │     limit=10                                                      │ │
│   │ )                                                                 │ │
│   │ for r in results:                                                 │ │
│   │     print(f"{r.date}: {r.title} - {r.summary[:100]}")            │ │
│   └──────────────────────────────────────────────────────────────────┘ │
│                                    │                                    │
│                                    ▼                                    │
│   ┌──────────────────────────────────────────────────────────────────┐ │
│   │                    REPL SANDBOX (Restricted)                      │ │
│   │                                                                   │ │
│   │  Allowed:                  │  Blocked:                            │ │
│   │  ├─ thermal.search()       │  ├─ os.* (all)                      │ │
│   │  ├─ thermal.grep()         │  ├─ subprocess.*                    │ │
│   │  ├─ thermal.filter()       │  ├─ open() (file I/O)               │ │
│   │  ├─ thermal.count()        │  ├─ exec(), eval()                  │ │
│   │  ├─ thermal.summarize()    │  ├─ import (most)                   │ │
│   │  ├─ print(), len()         │  ├─ network calls                   │ │
│   │  ├─ list/dict operations   │  ├─ __builtins__ manipulation       │ │
│   │  └─ Basic math/string ops  │  └─ Any write operations            │ │
│   └──────────────────────────────────────────────────────────────────┘ │
│                                    │                                    │
│                                    ▼                                    │
│   ┌──────────────────────────────────────────────────────────────────┐ │
│   │                    THERMAL MEMORY (Read-Only)                     │ │
│   │                                                                   │ │
│   │  SQLite: /ganuda/thermal_memory/memories.db                       │ │
│   │  ├─ 6,700+ memories                                               │ │
│   │  ├─ Full-text search index                                        │ │
│   │  ├─ Vector embeddings for semantic search                         │ │
│   │  └─ Metadata: date, tags, source, confidence                     │ │
│   └──────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Security Model

### Defense in Depth

Operations Chief mandated "robust security measures." We implement **five layers**:

```
Layer 1: Code Validation (Pre-execution)
   │
   ▼
Layer 2: AST Analysis (Block dangerous patterns)
   │
   ▼
Layer 3: Restricted Builtins (Minimal Python subset)
   │
   ▼
Layer 4: Execution Sandbox (Resource limits)
   │
   ▼
Layer 5: Read-Only Data Access (No mutations)
```

### Layer 1: Code Validation

```python
import re

class CodeValidator:
    """Pre-execution validation of Jr-generated code."""

    # Patterns that are NEVER allowed
    FORBIDDEN_PATTERNS = [
        r'\bimport\s+os\b',
        r'\bimport\s+subprocess\b',
        r'\bimport\s+sys\b',
        r'\bimport\s+socket\b',
        r'\bimport\s+requests\b',
        r'\bimport\s+urllib\b',
        r'\b__import__\b',
        r'\beval\s*\(',
        r'\bexec\s*\(',
        r'\bcompile\s*\(',
        r'\bopen\s*\(',
        r'\bfile\s*\(',
        r'\b__builtins__\b',
        r'\b__class__\b',
        r'\b__mro__\b',
        r'\b__subclasses__\b',
        r'\b__globals__\b',
        r'\b__code__\b',
        r'\bgetattr\s*\(',
        r'\bsetattr\s*\(',
        r'\bdelattr\s*\(',
        r'\bglobals\s*\(',
        r'\blocals\s*\(',
        r'\bvars\s*\(',
        r'\bdir\s*\(',  # Can reveal sandbox internals
    ]

    # Maximum code length (prevent DoS)
    MAX_CODE_LENGTH = 10000

    # Maximum loop iterations (prevent infinite loops)
    MAX_ITERATIONS = 1000

    @classmethod
    def validate(cls, code: str) -> tuple[bool, str]:
        """
        Validate code before execution.

        Returns:
            (is_valid: bool, error_message: str)
        """
        # Length check
        if len(code) > cls.MAX_CODE_LENGTH:
            return False, f"Code exceeds maximum length ({cls.MAX_CODE_LENGTH} chars)"

        # Forbidden pattern check
        for pattern in cls.FORBIDDEN_PATTERNS:
            if re.search(pattern, code, re.IGNORECASE):
                return False, f"Forbidden pattern detected: {pattern}"

        # Check for while True / infinite loop patterns
        if re.search(r'while\s+True\s*:', code):
            return False, "Infinite loop pattern detected (while True)"

        return True, ""
```

### Layer 2: AST Analysis

```python
import ast

class ASTSecurityAnalyzer(ast.NodeVisitor):
    """Deep analysis of code AST for security violations."""

    ALLOWED_IMPORTS = {'re', 'json', 'datetime', 'collections'}
    ALLOWED_CALLS = {
        'print', 'len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'set',
        'tuple', 'range', 'enumerate', 'zip', 'map', 'filter', 'sorted', 'reversed',
        'min', 'max', 'sum', 'abs', 'round', 'isinstance', 'type',
        # Thermal memory API
        'thermal.search', 'thermal.grep', 'thermal.filter',
        'thermal.count', 'thermal.summarize', 'thermal.get',
    }

    def __init__(self):
        self.violations = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name not in self.ALLOWED_IMPORTS:
                self.violations.append(f"Unauthorized import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module not in self.ALLOWED_IMPORTS:
            self.violations.append(f"Unauthorized import from: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node):
        # Check for dangerous function calls
        if isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec', 'compile', 'open', '__import__'):
                self.violations.append(f"Dangerous call: {node.func.id}")
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Block dunder attribute access
        if node.attr.startswith('__') and node.attr.endswith('__'):
            if node.attr not in ('__init__', '__str__', '__repr__'):
                self.violations.append(f"Dunder access blocked: {node.attr}")
        self.generic_visit(node)

    @classmethod
    def analyze(cls, code: str) -> tuple[bool, list[str]]:
        """
        Analyze code AST for security violations.

        Returns:
            (is_safe: bool, violations: list[str])
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {e}"]

        analyzer = cls()
        analyzer.visit(tree)

        return len(analyzer.violations) == 0, analyzer.violations
```

### Layer 3: Restricted Builtins

```python
import builtins

class RestrictedBuiltins:
    """Minimal Python builtins for sandbox execution."""

    SAFE_BUILTINS = {
        # Types
        'True': True,
        'False': False,
        'None': None,

        # Type constructors
        'bool': bool,
        'int': int,
        'float': float,
        'str': str,
        'list': list,
        'dict': dict,
        'set': set,
        'tuple': tuple,
        'frozenset': frozenset,

        # Iteration
        'range': range,
        'enumerate': enumerate,
        'zip': zip,
        'map': map,
        'filter': filter,
        'reversed': reversed,
        'sorted': sorted,

        # Math
        'abs': abs,
        'round': round,
        'min': min,
        'max': max,
        'sum': sum,
        'pow': pow,
        'divmod': divmod,

        # String
        'len': len,
        'repr': repr,
        'format': format,
        'chr': chr,
        'ord': ord,

        # Type checking
        'isinstance': isinstance,
        'type': type,
        'callable': callable,

        # Collections
        'all': all,
        'any': any,

        # Output (safe)
        'print': print,
    }

    @classmethod
    def get(cls) -> dict:
        """Return restricted builtins dict for exec()."""
        return cls.SAFE_BUILTINS.copy()
```

### Layer 4: Execution Sandbox

```python
import signal
import resource
from typing import Any, Dict
from contextlib import contextmanager

class ExecutionSandbox:
    """
    Resource-limited code execution sandbox.

    Limits:
    - CPU time: 5 seconds
    - Memory: 100MB
    - Output: 50KB
    """

    CPU_TIME_LIMIT = 5        # seconds
    MEMORY_LIMIT = 100 * 1024 * 1024  # 100MB
    OUTPUT_LIMIT = 50 * 1024  # 50KB

    class TimeoutError(Exception):
        pass

    class MemoryError(Exception):
        pass

    @staticmethod
    def _timeout_handler(signum, frame):
        raise ExecutionSandbox.TimeoutError("Execution timed out (5 second limit)")

    @classmethod
    @contextmanager
    def limits(cls):
        """Context manager that enforces resource limits."""
        # Set CPU time limit
        old_handler = signal.signal(signal.SIGALRM, cls._timeout_handler)
        signal.alarm(cls.CPU_TIME_LIMIT)

        # Set memory limit (soft limit)
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (cls.MEMORY_LIMIT, hard))

        try:
            yield
        finally:
            # Restore limits
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
            resource.setrlimit(resource.RLIMIT_AS, (soft, hard))

    @classmethod
    def execute(cls, code: str, thermal_api: "ThermalMemoryAPI") -> Dict[str, Any]:
        """
        Execute code in sandboxed environment.

        Args:
            code: Python code string
            thermal_api: Read-only thermal memory API

        Returns:
            {"success": bool, "output": str, "error": str}
        """
        # Capture output
        import io
        import sys

        output_buffer = io.StringIO()

        # Build restricted globals
        restricted_globals = {
            '__builtins__': RestrictedBuiltins.get(),
            'thermal': thermal_api,
        }

        restricted_locals = {}

        try:
            with cls.limits():
                # Redirect stdout
                old_stdout = sys.stdout
                sys.stdout = output_buffer

                try:
                    exec(code, restricted_globals, restricted_locals)
                finally:
                    sys.stdout = old_stdout

            output = output_buffer.getvalue()

            # Truncate output if too long
            if len(output) > cls.OUTPUT_LIMIT:
                output = output[:cls.OUTPUT_LIMIT] + "\n...[output truncated]"

            return {"success": True, "output": output, "error": ""}

        except cls.TimeoutError as e:
            return {"success": False, "output": "", "error": str(e)}
        except MemoryError:
            return {"success": False, "output": "", "error": "Memory limit exceeded (100MB)"}
        except Exception as e:
            return {"success": False, "output": "", "error": f"{type(e).__name__}: {e}"}
```

### Layer 5: Read-Only Thermal Memory API

```python
import sqlite3
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime, timedelta

@dataclass
class Memory:
    """Immutable memory record."""
    id: str
    date: str
    title: str
    content: str
    summary: str
    tags: List[str]
    source: str
    confidence: float

    def __setattr__(self, key, value):
        if hasattr(self, key):
            raise AttributeError("Memory objects are immutable")
        super().__setattr__(key, value)


class ThermalMemoryAPI:
    """
    Read-only API for thermal memory access.

    All methods return immutable Memory objects.
    No write, update, or delete operations are exposed.
    """

    def __init__(self, db_path: str = "/ganuda/thermal_memory/memories.db"):
        self._db_path = db_path
        self._conn = None

    def _get_conn(self) -> sqlite3.Connection:
        """Get read-only database connection."""
        if self._conn is None:
            # Open in read-only mode using URI
            self._conn = sqlite3.connect(
                f"file:{self._db_path}?mode=ro",
                uri=True,
                check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

    def search(
        self,
        query: str,
        date_range: Optional[tuple[str, str]] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Memory]:
        """
        Full-text search across thermal memory.

        Args:
            query: Search query string
            date_range: Optional (start_date, end_date) tuple
            tags: Optional list of tags to filter by
            limit: Max results (capped at 100)
            offset: Pagination offset

        Returns:
            List of matching Memory objects
        """
        limit = min(limit, 100)  # Hard cap

        conn = self._get_conn()
        cursor = conn.cursor()

        sql = """
            SELECT id, date, title, content, summary, tags, source, confidence
            FROM memories
            WHERE content LIKE ? OR title LIKE ?
        """
        params = [f"%{query}%", f"%{query}%"]

        if date_range:
            sql += " AND date BETWEEN ? AND ?"
            params.extend(date_range)

        if tags:
            tag_conditions = " OR ".join(["tags LIKE ?" for _ in tags])
            sql += f" AND ({tag_conditions})"
            params.extend([f"%{tag}%" for tag in tags])

        sql += " ORDER BY date DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor.execute(sql, params)

        return [self._row_to_memory(row) for row in cursor.fetchall()]

    def grep(self, pattern: str, limit: int = 50) -> List[Memory]:
        """
        Regex pattern search (simulated with LIKE for SQLite).

        Args:
            pattern: Regex-like pattern
            limit: Max results (capped at 100)

        Returns:
            List of matching Memory objects
        """
        # SQLite doesn't support full regex, approximate with LIKE
        like_pattern = pattern.replace(".*", "%").replace(".+", "_%")

        limit = min(limit, 100)

        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, date, title, content, summary, tags, source, confidence
            FROM memories
            WHERE content LIKE ? OR title LIKE ?
            ORDER BY date DESC
            LIMIT ?
            """,
            [f"%{like_pattern}%", f"%{like_pattern}%", limit]
        )

        return [self._row_to_memory(row) for row in cursor.fetchall()]

    def filter(
        self,
        source: Optional[str] = None,
        min_confidence: Optional[float] = None,
        date_after: Optional[str] = None,
        date_before: Optional[str] = None,
        limit: int = 50
    ) -> List[Memory]:
        """
        Filter memories by metadata.

        Returns:
            List of matching Memory objects
        """
        limit = min(limit, 100)

        conn = self._get_conn()
        cursor = conn.cursor()

        conditions = []
        params = []

        if source:
            conditions.append("source = ?")
            params.append(source)

        if min_confidence is not None:
            conditions.append("confidence >= ?")
            params.append(min_confidence)

        if date_after:
            conditions.append("date >= ?")
            params.append(date_after)

        if date_before:
            conditions.append("date <= ?")
            params.append(date_before)

        where_clause = " AND ".join(conditions) if conditions else "1=1"

        cursor.execute(
            f"""
            SELECT id, date, title, content, summary, tags, source, confidence
            FROM memories
            WHERE {where_clause}
            ORDER BY date DESC
            LIMIT ?
            """,
            params + [limit]
        )

        return [self._row_to_memory(row) for row in cursor.fetchall()]

    def count(self, query: Optional[str] = None) -> int:
        """
        Count memories matching query (or total if no query).

        Returns:
            Count of matching memories
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        if query:
            cursor.execute(
                "SELECT COUNT(*) FROM memories WHERE content LIKE ? OR title LIKE ?",
                [f"%{query}%", f"%{query}%"]
            )
        else:
            cursor.execute("SELECT COUNT(*) FROM memories")

        return cursor.fetchone()[0]

    def summarize(self, query: str, max_results: int = 5) -> str:
        """
        Get a summary of memories matching query.

        Returns:
            Formatted summary string
        """
        memories = self.search(query, limit=max_results)

        if not memories:
            return f"No memories found matching '{query}'"

        lines = [f"Found {len(memories)} memories for '{query}':"]
        for m in memories:
            lines.append(f"  [{m.date}] {m.title}")
            lines.append(f"    {m.summary[:150]}...")

        return "\n".join(lines)

    def get(self, memory_id: str) -> Optional[Memory]:
        """
        Get a specific memory by ID.

        Returns:
            Memory object or None
        """
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id, date, title, content, summary, tags, source, confidence
            FROM memories
            WHERE id = ?
            """,
            [memory_id]
        )

        row = cursor.fetchone()
        return self._row_to_memory(row) if row else None

    def _row_to_memory(self, row) -> Memory:
        """Convert database row to immutable Memory object."""
        tags = row["tags"].split(",") if row["tags"] else []
        return Memory(
            id=row["id"],
            date=row["date"],
            title=row["title"],
            content=row["content"],
            summary=row["summary"],
            tags=tags,
            source=row["source"],
            confidence=row["confidence"]
        )
```

---

## Complete Sandbox Implementation

```python
#!/usr/bin/env python3
"""
Cherokee Constitutional AI - Thermal Memory REPL Sandbox
Secure, read-only programmatic access to thermal memory for Jr agents.
"""

class ThermalREPLSandbox:
    """
    Complete sandbox integrating all security layers.

    Usage:
        sandbox = ThermalREPLSandbox()
        result = sandbox.execute('''
            results = thermal.search("GPU allocation", limit=5)
            for r in results:
                print(f"{r.date}: {r.title}")
        ''')
        print(result["output"])
    """

    def __init__(self, db_path: str = "/ganuda/thermal_memory/memories.db"):
        self.thermal_api = ThermalMemoryAPI(db_path)
        self.execution_log = []

    def execute(self, code: str, jr_id: str = "unknown") -> dict:
        """
        Execute Jr-provided code in secure sandbox.

        Args:
            code: Python code string
            jr_id: Identifier of the Jr agent (for logging)

        Returns:
            {"success": bool, "output": str, "error": str}
        """
        # Layer 1: Pre-validation
        is_valid, error = CodeValidator.validate(code)
        if not is_valid:
            self._log(jr_id, code, False, error)
            return {"success": False, "output": "", "error": f"Validation failed: {error}"}

        # Layer 2: AST analysis
        is_safe, violations = ASTSecurityAnalyzer.analyze(code)
        if not is_safe:
            self._log(jr_id, code, False, str(violations))
            return {"success": False, "output": "", "error": f"Security violations: {violations}"}

        # Layers 3-5: Execute in sandbox with restricted builtins and resource limits
        result = ExecutionSandbox.execute(code, self.thermal_api)

        self._log(jr_id, code, result["success"], result.get("error", ""))

        return result

    def _log(self, jr_id: str, code: str, success: bool, error: str):
        """Log execution for audit trail."""
        from datetime import datetime
        self.execution_log.append({
            "timestamp": datetime.now().isoformat(),
            "jr_id": jr_id,
            "code_hash": hash(code),
            "code_preview": code[:100],
            "success": success,
            "error": error
        })

        # Keep only last 1000 entries
        if len(self.execution_log) > 1000:
            self.execution_log = self.execution_log[-1000:]
```

---

## Integration with Jr Agents

### Modified Jr Base Class

```python
class JrBaseWithREPL(JrBase):
    """Jr base class with thermal memory REPL access."""

    def __init__(self, role_name):
        super().__init__(role_name)
        self.sandbox = ThermalREPLSandbox()

    def query_thermal_memory(self, code: str) -> str:
        """
        Execute code against thermal memory.

        Jr agents call this method with Python code to search/analyze memories.
        """
        result = self.sandbox.execute(code, jr_id=self.role_name)

        if result["success"]:
            return result["output"]
        else:
            return f"[REPL Error: {result['error']}]"

    def process(self, query, context=None):
        """
        Process with optional REPL access.

        If query requires historical data, Jr can generate Python code
        to query thermal memory instead of relying on context.
        """
        # Check if query likely needs thermal memory
        thermal_keywords = ["history", "previous", "past", "before", "decided", "archived"]
        needs_thermal = any(kw in query.lower() for kw in thermal_keywords)

        if needs_thermal:
            # Ask gateway to generate thermal query code
            thermal_code = self._generate_thermal_query(query)
            thermal_results = self.query_thermal_memory(thermal_code)
            context = f"{context or ''}\n\n[Thermal Memory Results]:\n{thermal_results}"

        # Continue with normal processing
        return super().process(query, context)

    def _generate_thermal_query(self, user_query: str) -> str:
        """
        Ask LLM to generate Python code for thermal memory query.

        This is where the RLM pattern shines - model writes code to
        interact with data environment instead of stuffing context.
        """
        messages = [
            {
                "role": "system",
                "content": """You are a code generator. Generate Python code to query thermal memory.

Available API:
- thermal.search(query: str, date_range=None, tags=None, limit=20) -> List[Memory]
- thermal.grep(pattern: str, limit=50) -> List[Memory]
- thermal.filter(source=None, min_confidence=None, date_after=None, date_before=None) -> List[Memory]
- thermal.count(query=None) -> int
- thermal.summarize(query: str, max_results=5) -> str

Memory objects have: id, date, title, content, summary, tags, source, confidence

Output ONLY Python code, no explanation."""
            },
            {"role": "user", "content": f"Generate code to answer: {user_query}"}
        ]

        return self._call_gateway(messages, max_tokens=200)
```

---

## Deployment Steps

### Step 1: Create sandbox module

```bash
ssh dereadi@100.116.27.89 "
mkdir -p /home/dereadi/thermal_sandbox
"
```

### Step 2: Deploy files

- `/home/dereadi/thermal_sandbox/__init__.py`
- `/home/dereadi/thermal_sandbox/validator.py` - CodeValidator
- `/home/dereadi/thermal_sandbox/analyzer.py` - ASTSecurityAnalyzer
- `/home/dereadi/thermal_sandbox/builtins.py` - RestrictedBuiltins
- `/home/dereadi/thermal_sandbox/executor.py` - ExecutionSandbox
- `/home/dereadi/thermal_sandbox/api.py` - ThermalMemoryAPI
- `/home/dereadi/thermal_sandbox/sandbox.py` - ThermalREPLSandbox

### Step 3: Verify thermal memory database exists

```bash
ssh dereadi@100.116.27.89 "
ls -la /ganuda/thermal_memory/memories.db
sqlite3 /ganuda/thermal_memory/memories.db 'SELECT COUNT(*) FROM memories;'
"
```

### Step 4: Run security tests

```bash
ssh dereadi@100.116.27.89 "
cd /home/dereadi/thermal_sandbox
python3 -c '
from sandbox import ThermalREPLSandbox
s = ThermalREPLSandbox()

# Test 1: Valid query should work
print(\"Test 1: Valid query\")
result = s.execute(\"print(thermal.count())\")
print(f\"  Success: {result[\"success\"]}\")

# Test 2: os import should be blocked
print(\"Test 2: os import\")
result = s.execute(\"import os; os.system(\"ls\")\")
print(f\"  Blocked: {not result[\"success\"]}\")

# Test 3: eval should be blocked
print(\"Test 3: eval\")
result = s.execute(\"eval(\"1+1\")\")
print(f\"  Blocked: {not result[\"success\"]}\")

# Test 4: Infinite loop should timeout
print(\"Test 4: Timeout\")
result = s.execute(\"while True: pass\")
print(f\"  Timeout: {\"timed out\" in result[\"error\"].lower()}\")
'
"
```

---

## Verification Checklist

- [ ] CodeValidator blocks all forbidden patterns
- [ ] ASTSecurityAnalyzer catches dunder access and dangerous calls
- [ ] RestrictedBuiltins provides minimal safe subset
- [ ] ExecutionSandbox enforces 5-second timeout
- [ ] ExecutionSandbox enforces 100MB memory limit
- [ ] ThermalMemoryAPI opens database read-only
- [ ] Memory objects are immutable
- [ ] Execution logging captures all attempts
- [ ] Integration with Jr agents works end-to-end

---

## Rollback Plan

If security issues discovered:

1. Remove `thermal_sandbox` from Jr imports
2. Jrs fall back to context-only processing
3. No data loss risk (read-only access)

---

## Future Enhancements

1. **Semantic search** - Vector embeddings for natural language queries
2. **Query caching** - Cache frequent thermal queries
3. **Rate limiting** - Per-Jr query limits
4. **Audit dashboard** - Visualize execution logs
5. **Extended API** - Time-series analysis, trend detection

---

## Connection to RLM Research

| RLM Principle | Our Implementation |
|--------------|-------------------|
| Data as external environment | Thermal memory accessed via API, not in context |
| Python REPL for data ops | Full Python sandbox with security layers |
| Programmatic examination | search(), grep(), filter() methods |
| Isolated execution | Per-query sandbox with resource limits |
| Structured output | Memory objects with consistent schema |

---

*For Seven Generations.*

*ᏣᎳᎩ ᏲᏫᎢᎶᏗ*

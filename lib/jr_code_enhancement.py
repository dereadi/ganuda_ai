#!/usr/bin/env python3
"""
Code Generation Enhancement for Jr Task Executor
Based on JR_ENHANCE_CODE_GENERATION.md

This module adds the 'code' task type with:
- RAG from codebase
- FARA correction rules
- Strict output formatting
- Syntax validation

For Seven Generations - Cherokee AI Federation
"""

import os
import re
import ast
import subprocess
from typing import Tuple, List, Optional

# Code generation safe paths
CODE_SAFE_WRITE_PATHS = [
    '/ganuda/lib/',
    '/ganuda/services/',
    '/ganuda/scripts/',
    '/ganuda/docs/',
]


class CodeGenerationMixin:
    """Mixin class for code generation capabilities."""

    def _execute_code_task(self, task: dict) -> Tuple[bool, str]:
        """Execute code generation task - outputs ONLY executable code."""
        content = task['task_content']
        task_id = task['task_id']

        # Detect language
        language = self._detect_language(content)

        # Get RAG context from codebase
        rag_context = self._get_code_rag_context(content)

        # Get FARA rules
        fara_rules = self._get_fara_rules(language)

        # Get few-shot examples
        few_shot = self._get_few_shot_examples(language)

        # Build strict code generation prompt
        prompt = f"""You are a code generator for Cherokee AI Federation.

OUTPUT RULES - FOLLOW EXACTLY:
1. Output ONLY executable {language} code
2. NO markdown, NO backticks, NO explanations
3. NO phrases like "Here is the code" or "This code will"
4. Start with imports or the first line of code
5. End with the last line of code
6. Include inline comments only where logic is complex
7. Follow Cherokee AI patterns from the codebase

FARA CORRECTION RULES (learn from past mistakes):
{fara_rules}

EXISTING CODEBASE PATTERNS (follow these):
{rag_context}

FEW-SHOT EXAMPLES (output like these):
{few_shot}

TASK:
{content}

Generate the {language} code now. Output ONLY code, starting immediately:"""

        # Call LLM with increased tokens for code
        result = self._call_llm(prompt, max_tokens=4000)

        if not result or result.startswith('LLM call failed'):
            return False, f"LLM error: {result}"

        # Clean the output - remove any markdown/explanation that slipped through
        clean_code = self._clean_code_output(result, language)

        # Validate syntax
        is_valid, validation_msg = self._validate_code_syntax(clean_code, language)

        if not is_valid:
            # Record FARA mistake
            self._record_fara_mistake(language, clean_code, validation_msg)
            return False, f"Code syntax validation failed: {validation_msg}"

        # Determine output path
        output_path = self._extract_code_output_path(content, language)

        if output_path and not self._is_code_safe_write_path(output_path):
            return False, f"Output path not allowed: {output_path}"

        # Save the code
        if output_path:
            try:
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(clean_code)
                return True, f"Code generated and saved to {output_path}"
            except Exception as e:
                return False, f"Could not save code: {e}"
        else:
            # Return code in result for TPM review
            truncated = clean_code[:1500] if len(clean_code) > 1500 else clean_code
            return True, f"Code generated (no output path specified):\n\n{truncated}"

    def _detect_language(self, content: str) -> str:
        """Detect programming language from task content."""
        content_lower = content.lower()

        if 'python' in content_lower or '.py' in content_lower:
            return 'python'
        elif 'sql' in content_lower or 'database' in content_lower:
            return 'sql'
        elif 'bash' in content_lower or 'shell' in content_lower or '.sh' in content_lower:
            return 'bash'
        elif 'javascript' in content_lower or 'js' in content_lower:
            return 'javascript'
        elif 'yaml' in content_lower or 'yml' in content_lower:
            return 'yaml'
        else:
            return 'python'  # Default

    def _get_code_rag_context(self, content: str) -> str:
        """Get relevant code context from codebase using grep."""
        context_parts = []

        # Extract key terms for search
        terms = re.findall(r'\b[A-Za-z_][A-Za-z0-9_]{3,}\b', content)
        search_terms = list(set(terms))[:5]

        for term in search_terms:
            try:
                # Search in /ganuda for relevant code
                result = subprocess.run(
                    ['grep', '-r', '-l', '--include=*.py', term, '/ganuda/lib/', '/ganuda/services/'],
                    capture_output=True, text=True, timeout=5
                )

                if result.stdout:
                    files = result.stdout.strip().split('\n')[:2]
                    for filepath in files:
                        try:
                            with open(filepath, 'r') as f:
                                # Get first 50 lines as pattern example
                                lines = f.readlines()[:50]
                                context_parts.append(f"--- {filepath} ---\n{''.join(lines)}")
                        except:
                            pass
            except:
                pass

        return '\n'.join(context_parts[:2]) if context_parts else "No existing patterns found."

    def _get_fara_rules(self, language: str) -> str:
        """Get FARA correction rules for this language."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT rule_text, importance
                    FROM fara_rules
                    WHERE (category = %s OR category = 'code_output')
                    AND active = TRUE
                    ORDER BY importance DESC, applied_count DESC
                    LIMIT 10
                """, (language,))
                rows = cur.fetchall()

                if rows:
                    return '\n'.join([f"- [{row[1]}] {row[0]}" for row in rows])
        except Exception as e:
            pass

        # Default rules if none in database
        return """- Never output markdown backticks
- Never start with explanatory text
- Include Cherokee AI header comment
- Follow existing codebase patterns
- Use descriptive variable names"""

    def _get_few_shot_examples(self, language: str) -> str:
        """Get few-shot examples of good code output."""
        examples = {
            'python': '''
# Example 1: Function definition
def calculate_temperature_decay(initial_temp: float, decay_rate: float, hours: int) -> float:
    """Calculate thermal memory temperature after decay."""
    return initial_temp * (decay_rate ** hours)

# Example 2: Class method
def get_hot_memories(self, threshold: float = 80.0) -> List[dict]:
    """Retrieve memories above temperature threshold."""
    conn = self._get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT memory_hash, original_content, temperature_score
            FROM thermal_memory_archive
            WHERE temperature_score >= %s
            ORDER BY temperature_score DESC
        """, (threshold,))
        return list(cur.fetchall())
''',
            'sql': '''
-- Example 1: Create table with indexes
CREATE TABLE IF NOT EXISTS example_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_example_name ON example_table(name);

-- Example 2: Insert with conflict handling
INSERT INTO example_table (name)
VALUES ('test')
ON CONFLICT (name) DO UPDATE SET created_at = NOW();
''',
            'bash': '''#!/bin/bash
# Example: Service health check
set -euo pipefail

SERVICE_URL="${1:-http://localhost:8080}"

if curl -sf "${SERVICE_URL}/health" > /dev/null; then
    echo "Service healthy"
    exit 0
else
    echo "Service unhealthy"
    exit 1
fi
'''
        }

        return examples.get(language, examples['python'])

    def _clean_code_output(self, output: str, language: str) -> str:
        """Clean LLM output to extract only code."""
        # Remove markdown code blocks
        output = re.sub(r'^```[a-z]*\n?', '', output, flags=re.MULTILINE)
        output = re.sub(r'```$', '', output, flags=re.MULTILINE)

        # Remove common preamble phrases
        preamble_patterns = [
            r'^Here is .*?:\s*\n',
            r'^Here\'s .*?:\s*\n',
            r'^The following .*?:\s*\n',
            r'^Below is .*?:\s*\n',
            r'^This code .*?:\s*\n',
            r'^I\'ll .*?:\s*\n',
        ]
        for pattern in preamble_patterns:
            output = re.sub(pattern, '', output, flags=re.IGNORECASE)

        # Remove trailing explanation
        # Look for lines that start with common explanation starters after code
        lines = output.split('\n')
        code_lines = []
        in_code = False

        for line in lines:
            stripped = line.strip()

            # Detect start of code
            if not in_code:
                if language == 'python' and (stripped.startswith('import ') or
                    stripped.startswith('from ') or stripped.startswith('def ') or
                    stripped.startswith('class ') or stripped.startswith('#!')):
                    in_code = True
                elif language == 'sql' and (stripped.upper().startswith('CREATE ') or
                    stripped.upper().startswith('INSERT ') or stripped.upper().startswith('SELECT ') or
                    stripped.upper().startswith('ALTER ') or stripped.startswith('--')):
                    in_code = True
                elif language == 'bash' and (stripped.startswith('#!') or stripped.startswith('#') or
                    stripped.startswith('set ') or stripped):
                    in_code = True

            if in_code:
                # Check for explanation starters that indicate end of code
                if stripped.startswith('This ') or stripped.startswith('Note:') or \
                   stripped.startswith('Explanation:') or stripped.startswith('The above'):
                    break
                code_lines.append(line)

        return '\n'.join(code_lines).strip()

    def _validate_code_syntax(self, code: str, language: str) -> Tuple[bool, str]:
        """Validate code syntax."""
        if language == 'python':
            try:
                ast.parse(code)
                return True, "Valid Python syntax"
            except SyntaxError as e:
                return False, f"Python syntax error: {e.msg} at line {e.lineno}"

        elif language == 'sql':
            # Basic SQL validation - check for common issues
            sql_upper = code.upper()
            if not any(kw in sql_upper for kw in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP']):
                return False, "No SQL statement found"
            return True, "SQL syntax appears valid"

        elif language == 'bash':
            # Use bash -n for syntax check
            try:
                result = subprocess.run(
                    ['bash', '-n'],
                    input=code,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return True, "Valid bash syntax"
                else:
                    return False, f"Bash syntax error: {result.stderr}"
            except Exception as e:
                return True, f"Could not validate bash: {e}"

        # Default: assume valid for other languages
        return True, f"Syntax validation not implemented for {language}"

    def _record_fara_mistake(self, language: str, code: str, error: str):
        """Record mistake for FARA learning."""
        try:
            conn = self._get_connection()
            with conn.cursor() as cur:
                # Create a rule from the mistake
                rule_hash = f"fara-mistake-{abs(hash(error)) % 1000000}"
                rule_text = f"Avoid: {error[:200]}"

                cur.execute("""
                    INSERT INTO fara_rules (rule_hash, category, rule_text, importance)
                    VALUES (%s, %s, %s, 50)
                    ON CONFLICT (rule_hash) DO UPDATE SET applied_count = fara_rules.applied_count + 1
                """, (rule_hash, language, rule_text))
                conn.commit()
        except:
            pass

    def _extract_code_output_path(self, content: str, language: str) -> Optional[str]:
        """Extract output file path from task content."""
        ext_map = {'python': '.py', 'sql': '.sql', 'bash': '.sh', 'javascript': '.js', 'yaml': '.yaml'}
        ext = ext_map.get(language, '.py')

        patterns = [
            rf'[Ss]ave to\s+(/[^\s]+{re.escape(ext)})',
            rf'[Oo]utput:?\s+(/[^\s]+{re.escape(ext)})',
            rf'[Ww]rite to\s+(/[^\s]+{re.escape(ext)})',
            rf'[Ff]ile:?\s+(/[^\s]+{re.escape(ext)})',
            rf'(/ganuda/[^\s]+{re.escape(ext)})',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                return match.group(1)

        return None

    def _is_code_safe_write_path(self, path: str) -> bool:
        """Check if path is in safe code write locations."""
        for safe_path in CODE_SAFE_WRITE_PATHS:
            if path.startswith(safe_path):
                return True
        return False

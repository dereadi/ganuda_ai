#!/usr/bin/env python3
"""
JR CLI Executor - Tool Calling Wrapper for Ollama JRs
=====================================================

Gives Ollama-based JRs (Memory, Meta, Executive, Integration, Conscience)
the ability to execute commands like Claude Code:
- Write files
- Read files
- Execute bash commands
- Search files (Glob)

**Architecture:**
- Wraps curl calls to Ollama API
- Parses JR responses for tool calls
- Executes tools on JR's behalf
- Returns confirmation to PM

**Usage:**
    python jr_cli_executor.py meta_jr "Create qpr_module.py with QuantumPatternRecognizer class"

**Token Savings:**
- OLD: JR returns 800-token code block → PM writes file
- NEW: JR calls <write> tool → Executor writes file → "File created" confirmation

Cherokee Constitutional AI - War Chief JR CLI Executor
"""

import sys
import json
import subprocess
import re
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Project root directory - AUTO-DETECT based on node
# CRITICAL: /tmp is EPHEMERAL - these are PERSISTENT filesystems
def get_project_root():
    """Auto-detect which node we're on and return persistent filesystem path."""
    if Path("/ganuda").exists():
        # REDFIN (War Chief) - 1.8TB persistent storage
        return Path("/ganuda/jr_assignments")
    elif Path("/Users/Shared/cherokee_democracy").exists():
        # SASASS2 (Medicine Woman) - macOS persistent storage
        return Path("/Users/Shared/cherokee_democracy")
    else:
        # BLUEFIN (Peace Chief) - 915GB persistent storage
        return Path("/home/dereadi/scripts/claude/ganuda_ai_v2")

PROJECT_ROOT = get_project_root()

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

# JR model mapping
JR_MODELS = {
    "meta": "meta_jr_resonance:latest",
    "memory": "memory_jr_resonance:latest",
    "executive": "executive_jr_resonance:latest",
    "integration": "integration_jr_resonance:latest",
    "conscience": "conscience_jr_resonance:latest"
}


class JRToolParser:
    """Parse tool calls from JR responses."""

    @staticmethod
    def parse_tools(response: str) -> List[Dict]:
        """
        Parse tool calls from JR response text.

        Supported formats:
        - <write file="path">content</write>
        - <read file="path"/>
        - <bash command="cmd"/>
        - <glob pattern="*.py"/>

        Returns:
            List of tool call dicts: [{"tool": "write", "file": "path", "content": "..."}]
        """
        tools = []

        # Parse <write> tags
        write_pattern = r'<write\s+file="([^"]+)">(.*?)</write>'
        for match in re.finditer(write_pattern, response, re.DOTALL):
            tools.append({
                "tool": "write",
                "file": match.group(1),
                "content": match.group(2).strip()
            })

        # Parse <read> tags
        read_pattern = r'<read\s+file="([^"]+)"\s*/>'
        for match in re.finditer(read_pattern, response):
            tools.append({
                "tool": "read",
                "file": match.group(1)
            })

        # Parse <bash> tags
        bash_pattern = r'<bash\s+command="([^"]+)"\s*/>'
        for match in re.finditer(bash_pattern, response):
            tools.append({
                "tool": "bash",
                "command": match.group(1)
            })

        # Parse <glob> tags
        glob_pattern = r'<glob\s+pattern="([^"]+)"\s*/>'
        for match in re.finditer(glob_pattern, response):
            tools.append({
                "tool": "glob",
                "pattern": match.group(1)
            })

        return tools


class JRToolExecutor:
    """Execute tool calls on behalf of JRs."""

    def __init__(self, jr_name: str, auto_approve: bool = False):
        self.jr_name = jr_name
        self.auto_approve = auto_approve
        self.project_root = PROJECT_ROOT

    def execute(self, tool: Dict) -> Dict:
        """Execute a single tool call."""
        tool_name = tool["tool"]

        if tool_name == "write":
            return self._execute_write(tool)
        elif tool_name == "read":
            return self._execute_read(tool)
        elif tool_name == "bash":
            return self._execute_bash(tool)
        elif tool_name == "glob":
            return self._execute_glob(tool)
        else:
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

    def _execute_write(self, tool: Dict) -> Dict:
        """Execute Write tool."""
        file_path = self.project_root / tool["file"]
        content = tool["content"]

        try:
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file
            file_path.write_text(content)

            return {
                "success": True,
                "tool": "write",
                "file": str(file_path),
                "lines": len(content.splitlines()),
                "message": f"✅ {self.jr_name} created {tool['file']} ({len(content.splitlines())} lines)"
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "write",
                "error": str(e)
            }

    def _execute_read(self, tool: Dict) -> Dict:
        """Execute Read tool."""
        file_path = self.project_root / tool["file"]

        try:
            content = file_path.read_text()
            return {
                "success": True,
                "tool": "read",
                "file": str(file_path),
                "content": content,
                "lines": len(content.splitlines())
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "read",
                "error": str(e)
            }

    def _execute_bash(self, tool: Dict) -> Dict:
        """Execute Bash tool (with approval for dangerous commands)."""
        command = tool["command"]

        # Dangerous commands require approval
        dangerous_patterns = ["rm ", "sudo ", "chmod ", "git push", "git reset"]
        is_dangerous = any(pattern in command for pattern in dangerous_patterns)

        if is_dangerous and not self.auto_approve:
            print(f"\n⚠️  {self.jr_name} wants to execute: {command}")
            approval = input("Approve? (yes/no): ").strip().lower()
            if approval != "yes":
                return {
                    "success": False,
                    "tool": "bash",
                    "error": "Command rejected by PM"
                }

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )

            return {
                "success": result.returncode == 0,
                "tool": "bash",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "bash",
                "error": str(e)
            }

    def _execute_glob(self, tool: Dict) -> Dict:
        """Execute Glob tool."""
        pattern = tool["pattern"]

        try:
            matches = list(self.project_root.glob(pattern))
            return {
                "success": True,
                "tool": "glob",
                "pattern": pattern,
                "matches": [str(m.relative_to(self.project_root)) for m in matches],
                "count": len(matches)
            }
        except Exception as e:
            return {
                "success": False,
                "tool": "glob",
                "error": str(e)
            }


def call_ollama_jr(jr_model: str, prompt: str) -> str:
    """Call Ollama API for JR model."""
    payload = {
        "model": jr_model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7}
    }

    result = subprocess.run(
        ["curl", "-s", OLLAMA_API, "-d", json.dumps(payload)],
        capture_output=True,
        text=True
    )

    try:
        response = json.loads(result.stdout)
        return response.get("response", "")
    except:
        return result.stdout


def main():
    """Main CLI executor."""
    if len(sys.argv) < 3:
        print("Usage: jr_cli_executor.py <jr_name> <prompt>")
        print(f"Available JRs: {', '.join(JR_MODELS.keys())}")
        sys.exit(1)

    jr_name = sys.argv[1].lower()
    prompt = " ".join(sys.argv[2:])

    if jr_name not in JR_MODELS:
        print(f"❌ Unknown JR: {jr_name}")
        print(f"Available: {', '.join(JR_MODELS.keys())}")
        sys.exit(1)

    jr_model = JR_MODELS[jr_name]

    # Add tool calling instructions to prompt
    enhanced_prompt = f"""
{prompt}

**IMPORTANT**: You can execute commands using these tools:

1. **Write a file:**
<write file="path/to/file.py">
file content here
</write>

2. **Read a file:**
<read file="path/to/file.py"/>

3. **Execute bash command:**
<bash command="ls -la"/>

4. **Search files (glob):**
<glob pattern="**/*.py"/>

Use these tools to complete your work. After using tools, confirm what you did.
"""

    print(f"🦅 {jr_name.upper()} JR executing...")

    # Call Ollama JR
    response = call_ollama_jr(jr_model, enhanced_prompt)

    # Parse tool calls from response
    parser = JRToolParser()
    tools = parser.parse_tools(response)

    if not tools:
        # No tool calls - just return response
        print(f"\n{jr_name} response:")
        print(response)
        return

    # Execute tools
    executor = JRToolExecutor(jr_name, auto_approve=False)

    print(f"\n{jr_name} called {len(tools)} tool(s):\n")

    for tool in tools:
        result = executor.execute(tool)

        if result["success"]:
            print(result.get("message", f"✅ {result['tool']} executed"))
            if result["tool"] == "read":
                print(f"   {result['lines']} lines read")
            elif result["tool"] == "bash":
                if result.get("stdout"):
                    print(f"   Output: {result['stdout'][:200]}")
            elif result["tool"] == "glob":
                print(f"   Found {result['count']} matches")
        else:
            print(f"❌ {result['tool']} failed: {result.get('error', 'Unknown error')}")

    # Show non-tool response text
    response_without_tools = response
    for match in re.finditer(r'<(write|read|bash|glob).*?(?:</\1>|/>)', response, re.DOTALL):
        response_without_tools = response_without_tools.replace(match.group(0), "")

    response_without_tools = response_without_tools.strip()
    if response_without_tools:
        print(f"\n{jr_name} says:")
        print(response_without_tools)


if __name__ == "__main__":
    main()

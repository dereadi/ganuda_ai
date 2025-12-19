#!/usr/bin/env python3
"""
Run Command Handler for Cherokee Chief Telegram Bot
"""

import os
import subprocess

SCRIPTS_DIR = '/ganuda/scripts'
PYTHON_PATH = '/home/dereadi/cherokee_venv/bin/python3'


def run_script(script_name: str = None) -> str:
    """Run a script and return output"""
    if not script_name:
        try:
            scripts = sorted(
                [f for f in os.listdir(SCRIPTS_DIR) if f.endswith('.py')],
                key=lambda x: os.path.getmtime(os.path.join(SCRIPTS_DIR, x)),
                reverse=True
            )
            if scripts:
                script_name = scripts[0]
            else:
                return "No scripts found in /ganuda/scripts/"
        except Exception as e:
            return f"Error: {e}"

    script_path = f"{SCRIPTS_DIR}/{script_name}" if not script_name.startswith('/') else script_name

    try:
        result = subprocess.run(
            f"{PYTHON_PATH} {script_path}",
            shell=True, capture_output=True, text=True, timeout=60
        )
        output = result.stdout or result.stderr or "(no output)"
        if len(output) > 4000:
            output = output[:4000] + "\n... (truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Script timed out (60s)"
    except Exception as e:
        return f"Error: {e}"


if __name__ == '__main__':
    print("Testing run_script...")
    print(run_script())
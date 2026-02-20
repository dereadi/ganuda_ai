#!/usr/bin/env python3
"""
Cherokee AI Federation — Remediation Playbook Validator

Three-gate validation pipeline:
  Gate 1: ansible-lint --strict (syntax + best practices)
  Gate 2: Module whitelist check (Turtle's 7GEN constraint)
  Gate 3: Crawdad council vote (security review)

Only playbooks that pass all three gates proceed to TPM approval.

Usage:
    python validator.py --playbook /ganuda/ansible/staging/remediation_<id>_<ts>.yml
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import requests
import psycopg2
import hashlib

sys.path.insert(0, str(Path(__file__).parent))
from module_whitelist import validate_playbook_modules
from crawdad_review_prompt import build_crawdad_review_prompt

# Configuration
GATEWAY_URL = "http://192.168.132.223:8080"
API_KEY = os.environ.get(
    "CHEROKEE_API_KEY",
    "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5",
)
DB_HOST = "192.168.132.222"
DB_NAME = "zammad_production"
DB_USER = "claude"
APPROVED_DIR = Path("/ganuda/ansible/approved")
REJECTED_DIR = Path("/ganuda/ansible/rejected")


def get_db_password():
    """Load DB password from secrets_loader or environment."""
    try:
        sys.path.insert(0, "/ganuda/lib")
        from secrets_loader import get_secret
        return get_secret("DB_PASSWORD")
    except Exception:
        return os.environ.get("DB_PASSWORD", "")


def gate1_ansible_lint(playbook_path: str) -> dict:
    """Gate 1: Run ansible-lint on the staged playbook."""
    try:
        result = subprocess.run(
            ["ansible-lint", "--strict", "--parseable", playbook_path],
            capture_output=True,
            text=True,
            timeout=60,
        )
        return {
            "gate": "ansible-lint",
            "passed": result.returncode == 0,
            "output": result.stdout[:500] if result.stdout else "",
            "errors": result.stderr[:500] if result.stderr else "",
        }
    except FileNotFoundError:
        return {
            "gate": "ansible-lint",
            "passed": False,
            "output": "",
            "errors": "ansible-lint not installed. Install with: pip install ansible-lint",
        }
    except subprocess.TimeoutExpired:
        return {
            "gate": "ansible-lint",
            "passed": False,
            "output": "",
            "errors": "ansible-lint timed out after 60s",
        }


def gate2_module_whitelist(playbook_path: str) -> dict:
    """Gate 2: Verify all modules are on the approved whitelist."""
    content = Path(playbook_path).read_text()
    validation = validate_playbook_modules(content)

    return {
        "gate": "module-whitelist",
        "passed": validation["valid"],
        "approved": validation["approved"],
        "unapproved": validation["unapproved"],
        "banned": validation["banned"],
    }


def gate3_crawdad_review(playbook_path: str) -> dict:
    """Gate 3: Submit to council for Crawdad's security review."""
    content = Path(playbook_path).read_text()
    review_prompt = build_crawdad_review_prompt(content)

    try:
        resp = requests.post(
            f"{GATEWAY_URL}/v1/council/vote",
            json={
                "question": review_prompt,
                "context": {
                    "type": "security_review",
                    "source": "self_healing_validator",
                    "playbook_path": playbook_path,
                },
            },
            headers={
                "X-API-Key": API_KEY,
                "Content-Type": "application/json",
            },
            timeout=120,
        )
        resp.raise_for_status()
        vote = resp.json()

        # Check if Crawdad specifically flagged concerns
        crawdad_concern = False
        specialists = vote.get("specialist_votes", [])
        for spec in specialists:
            if spec.get("specialist") == "Crawdad" and "CONCERN" in spec.get("concern_flags", ""):
                crawdad_concern = True
                break

        confidence = vote.get("confidence", 0)
        decision = vote.get("decision", "UNKNOWN")

        return {
            "gate": "crawdad-review",
            "passed": decision in ("PROCEED", "PROCEED WITH CAUTION") and not crawdad_concern,
            "vote_id": vote.get("vote_id", "unknown"),
            "decision": decision,
            "confidence": confidence,
            "crawdad_concern": crawdad_concern,
        }
    except Exception as e:
        return {
            "gate": "crawdad-review",
            "passed": False,
            "error": str(e),
        }


def record_validation_result(playbook_path: str, gates: list, overall_passed: bool):
    """Write validation results to thermal memory for learning loop."""
    db_password = get_db_password()
    try:
        conn = psycopg2.connect(
            host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=db_password
        )
        cur = conn.cursor()

        content = f"SELF-HEALING VALIDATION: {'PASSED' if overall_passed else 'REJECTED'}\n"
        content += f"Playbook: {playbook_path}\n"
        for gate in gates:
            content += f"Gate {gate['gate']}: {'PASS' if gate['passed'] else 'FAIL'}\n"
            if not gate["passed"]:
                content += f"  Reason: {json.dumps({k: v for k, v in gate.items() if k not in ('gate', 'passed')})}\n"

        memory_hash = hashlib.sha256(content.encode()).hexdigest()
        temperature = 0.6 if overall_passed else 0.8

        cur.execute(
            """INSERT INTO thermal_memory_archive
            (original_content, temperature_score, sacred_pattern, memory_hash, metadata)
            VALUES (%s, %s, false, %s, %s)
            ON CONFLICT (memory_hash) DO NOTHING""",
            (
                content,
                temperature,
                memory_hash,
                json.dumps({
                    "type": "self_healing_validation",
                    "playbook": playbook_path,
                    "passed": overall_passed,
                    "timestamp": datetime.now().isoformat(),
                }),
            ),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Warning: Could not record to thermal memory: {e}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Validate staged remediation playbook")
    parser.add_argument("--playbook", required=True, help="Path to staged playbook")
    args = parser.parse_args()

    playbook_path = args.playbook
    if not Path(playbook_path).exists():
        print(f"ERROR: Playbook not found: {playbook_path}")
        sys.exit(1)

    print(f"[{datetime.now().isoformat()}] Validating: {playbook_path}")
    print("=" * 60)

    gates = []

    # Gate 1: ansible-lint
    print("\nGate 1: ansible-lint...")
    g1 = gate1_ansible_lint(playbook_path)
    gates.append(g1)
    print(f"  Result: {'PASS' if g1['passed'] else 'FAIL'}")
    if not g1["passed"]:
        print(f"  Errors: {g1.get('errors', '')}")

    # Gate 2: Module whitelist
    print("\nGate 2: Module whitelist (Turtle's 7GEN)...")
    g2 = gate2_module_whitelist(playbook_path)
    gates.append(g2)
    print(f"  Result: {'PASS' if g2['passed'] else 'FAIL'}")
    if g2.get("banned"):
        print(f"  BANNED modules found: {g2['banned']}")
    if g2.get("unapproved"):
        print(f"  Unapproved modules: {g2['unapproved']}")

    # Gate 3: Crawdad council review (only if gates 1+2 pass)
    if g1["passed"] and g2["passed"]:
        print("\nGate 3: Crawdad security review (council vote)...")
        g3 = gate3_crawdad_review(playbook_path)
        gates.append(g3)
        print(f"  Result: {'PASS' if g3['passed'] else 'FAIL'}")
        print(f"  Vote: {g3.get('decision', 'N/A')} (confidence: {g3.get('confidence', 'N/A')})")
        if g3.get("crawdad_concern"):
            print("  Crawdad raised SECURITY CONCERN — manual review required")
    else:
        print("\nGate 3: SKIPPED (gates 1 or 2 failed)")
        gates.append({"gate": "crawdad-review", "passed": False, "skipped": True})

    # Overall result
    overall = all(g["passed"] for g in gates)
    print("\n" + "=" * 60)
    print(f"OVERALL: {'APPROVED — ready for TPM approval' if overall else 'REJECTED'}")

    # Move playbook to appropriate directory
    if overall:
        APPROVED_DIR.mkdir(parents=True, exist_ok=True)
        dest = APPROVED_DIR / Path(playbook_path).name
        Path(playbook_path).rename(dest)
        print(f"Moved to: {dest}")
        print("\nNext step: TPM reviews via Telegram and issues /approve or /deny")
    else:
        REJECTED_DIR.mkdir(parents=True, exist_ok=True)
        dest = REJECTED_DIR / Path(playbook_path).name
        Path(playbook_path).rename(dest)
        print(f"Moved to: {dest}")

    # Record to thermal memory
    record_validation_result(str(playbook_path), gates, overall)

    sys.exit(0 if overall else 1)


if __name__ == "__main__":
    main()
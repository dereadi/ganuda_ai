#!/usr/bin/env python3
"""
Patch script to fix PostgreSQL transaction rollback bug in jr_task_executor.py

This script modifies the executor to add explicit conn.rollback() calls
in all error handlers to prevent the "transaction aborted" cascade.

Run: python3 /ganuda/scripts/patch_executor_rollback.py

For Seven Generations - Cherokee AI Federation
Date: January 23, 2026
"""

import re
import shutil
from datetime import datetime

EXECUTOR_PATH = "/ganuda/jr_executor/jr_task_executor.py"
BACKUP_SUFFIX = f".backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def patch_file():
    # Create backup
    backup_path = EXECUTOR_PATH + BACKUP_SUFFIX
    shutil.copy2(EXECUTOR_PATH, backup_path)
    print(f"[PATCH] Backup created: {backup_path}")

    with open(EXECUTOR_PATH, 'r') as f:
        content = f.read()

    original_content = content
    patches_applied = 0

    # Pattern 1: Fix get_assigned_tasks error handler
    old_pattern1 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            return []'''
    new_pattern1 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error fetching tasks: {e}")
            try:
                if self._conn and not self._conn.closed:
                    self._conn.rollback()
            except:
                pass
            return []'''

    if old_pattern1 in content:
        content = content.replace(old_pattern1, new_pattern1)
        patches_applied += 1
        print("[PATCH] Fixed get_assigned_tasks() error handler")

    # Pattern 2: Fix start_task error handler
    old_pattern2 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error starting task: {e}")'''
    new_pattern2 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error starting task: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern2 in content:
        content = content.replace(old_pattern2, new_pattern2)
        patches_applied += 1
        print("[PATCH] Fixed start_task() error handler")

    # Pattern 3: Fix complete_task error handler
    old_pattern3 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error completing task: {e}")'''
    new_pattern3 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error completing task: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern3 in content:
        content = content.replace(old_pattern3, new_pattern3)
        patches_applied += 1
        print("[PATCH] Fixed complete_task() error handler")

    # Pattern 4: Fix fail_task error handler
    old_pattern4 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error marking task failed: {e}")'''
    new_pattern4 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error marking task failed: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern4 in content:
        content = content.replace(old_pattern4, new_pattern4)
        patches_applied += 1
        print("[PATCH] Fixed fail_task() error handler")

    # Pattern 5: Fix log_to_thermal_memory error handler
    old_pattern5 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error logging to thermal memory: {e}")'''
    new_pattern5 = '''        except Exception as e:
            print(f"[{self.agent_id}] Error logging to thermal memory: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern5 in content:
        content = content.replace(old_pattern5, new_pattern5)
        patches_applied += 1
        print("[PATCH] Fixed log_to_thermal_memory() error handler")

    # Pattern 6: Fix _query_thermal_memory error handler
    old_pattern6 = '''        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
        return "No relevant memories found."'''
    new_pattern6 = '''        except Exception as e:
            print(f"[{self.agent_id}] Thermal query error: {e}")
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass
        return "No relevant memories found."'''

    if old_pattern6 in content:
        content = content.replace(old_pattern6, new_pattern6)
        patches_applied += 1
        print("[PATCH] Fixed _query_thermal_memory() error handler")

    # Pattern 7: Fix _record_fara_mistake - bare except
    # This one uses bare except, need different approach
    old_pattern7 = '''    def _record_fara_mistake(self, language: str, code: str, error: str):
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
            pass'''
    new_pattern7 = '''    def _record_fara_mistake(self, language: str, code: str, error: str):
        """Record mistake for FARA learning."""
        conn = None
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
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern7 in content:
        content = content.replace(old_pattern7, new_pattern7)
        patches_applied += 1
        print("[PATCH] Fixed _record_fara_mistake() error handler")

    # Pattern 8: Fix _get_fara_rules - bare except with pass
    old_pattern8 = '''    def _get_fara_rules(self, language: str) -> str:
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
                    return '\\n'.join([f"- [{row[1]}] {row[0]}" for row in rows])
        except Exception as e:
            pass'''
    new_pattern8 = '''    def _get_fara_rules(self, language: str) -> str:
        """Get FARA correction rules for this language."""
        conn = None
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
                    return '\\n'.join([f"- [{row[1]}] {row[0]}" for row in rows])
        except Exception as e:
            try:
                if conn and not conn.closed:
                    conn.rollback()
            except:
                pass'''

    if old_pattern8 in content:
        content = content.replace(old_pattern8, new_pattern8)
        patches_applied += 1
        print("[PATCH] Fixed _get_fara_rules() error handler")

    if patches_applied > 0:
        with open(EXECUTOR_PATH, 'w') as f:
            f.write(content)
        print(f"\n[PATCH] SUCCESS: Applied {patches_applied} patches to {EXECUTOR_PATH}")
        return True
    else:
        print("\n[PATCH] No patches needed or patterns not found")
        # Check if already patched
        if "conn.rollback()" in original_content and "if conn and not conn.closed" in original_content:
            print("[PATCH] File appears to already be patched")
        return False

if __name__ == "__main__":
    patch_file()

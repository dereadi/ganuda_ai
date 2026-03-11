# JR INSTRUCTION: Fire Guard Self-Healing (Zombie Task Intelligence)

**Task**: Upgrade Fire Guard zombie detection from dumb timer to intelligent self-healing
**Priority**: HIGH — this is a DC-10 Reflex layer fix
**Date**: 2026-03-09
**TPM**: Claude Opus

## Problem Statement

When the Jr executor dies mid-flight (context window exhaustion, crash, etc.), tasks are orphaned in `in_progress` status. Fire Guard detects them as stale after 2h and resets them after 6h, but:

1. **Infinite retry loop**: Reset task → executor re-grabs → dies again → repeat forever
2. **No retry counter**: Tasks zombie-reset indefinitely, never fail
3. **No distinction**: Tasks that completed their work (code written) vs. tasks that died before starting look the same
4. **Threshold too conservative**: 6h is too long for a 2-minute timer cycle

## Acceptance Criteria

1. Add `zombie_reset_count` integer column to `jr_work_queue` (default 0)
2. In `reset_zombie_tasks()`:
   - Increment `zombie_reset_count` on each reset
   - If `zombie_reset_count >= 3`, set status to `failed` instead of `pending`, with a note "exceeded zombie retry limit"
   - Reduce `ZOMBIE_THRESHOLD_HOURS` from 6 to 2
3. Add Slack notification on zombie reset: call `slack_send("fire-guard", msg)` from `/ganuda/lib/slack_federation.py`
4. Log zombie-failed tasks at temperature 90 (higher than current 75) so they surface in Dawn Mist

## Target Files

- `/ganuda/scripts/fire_guard.py` — modify `reset_zombie_tasks()`, update `ZOMBIE_THRESHOLD_HOURS`
- Database: `ALTER TABLE jr_work_queue ADD COLUMN IF NOT EXISTS zombie_reset_count INTEGER DEFAULT 0;`

## Constraints

- Do NOT touch `check_stale_tasks()` — it works correctly
- Do NOT duplicate code blocks — the Jr that wrote the queue depth metric copied it 3 times. One block only.
- Import slack_federation at the top of the file, not inside functions
- Test with `python3 -c "import py_compile; py_compile.compile('fire_guard.py', doraise=True)"`

## Evaluation

- Fire Guard should stop alerting about the same stale tasks every 2 minutes
- After 3 zombie resets, task should move to `failed` status
- Slack #fire-guard channel should receive zombie reset notifications
- No duplicate code blocks in fire_guard.py

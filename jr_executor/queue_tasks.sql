-- Queue multiple Jr tasks
INSERT INTO jr_work_queue (title, description, priority, assigned_jr, instruction_content)
VALUES
    ('Create KB Article: Jr Executor Fix',
     'Document the P0 fixes applied to Jr executor',
     2,
     'it_triad_jr',
     E'Create a KB article at /ganuda/docs/kb/KB-JR-EXECUTOR-P0-FIX-JAN19-2026.md with:\n\n# KB: Jr Executor P0 Fixes - January 19, 2026\n\n## Problem\nJr tasks were being marked "completed" with 0 steps executed due to Python all([]) returning True for empty lists.\n\n## Root Cause\n1. task_executor.py line 226: all(s.get(\'success\') for s in step_results) returns True when step_results is empty\n2. jr_queue_worker.py line 89: Hardcoded summary "Task completed" regardless of actual work\n3. RLM path had no verification of actual work done\n\n## Fixes Applied\n1. Added empty step_results guard after execute_steps()\n2. Added _generate_summary() method for meaningful summaries  \n3. Added RLM work verification (subtasks_completed or artifacts required)\n\n## Files Modified\n- /ganuda/jr_executor/task_executor.py (lines 225-231, 590-606)\n- /ganuda/jr_executor/jr_queue_worker.py (lines 45-78, 119)\n\n## Verification\nTask 153 correctly marked as FAILED after fix was applied.\nTask 155 showed "1/1 steps succeeded" in summary.\n\n## Impact\nAll Jr tasks now correctly report success/failure based on actual work done.\n\n*Cherokee AI Federation - For the Seven Generations*'),

    ('System Health: Create GPU Monitor Script',
     'Create script to monitor GPU temps over time',
     3,
     'it_triad_jr',
     E'Create a GPU monitoring script at /ganuda/scripts/gpu_temp_check.sh with executable permissions:\n\n#!/bin/bash\n# GPU Temperature Monitor - Cherokee AI Federation\nLOGFILE=/ganuda/logs/gpu_temps.log\nTIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")\nTEMP=$(nvidia-smi --query-gpu=temperature.gpu --format=csv,noheader,nounits 2>/dev/null || echo "N/A")\nPOWER=$(nvidia-smi --query-gpu=power.draw --format=csv,noheader,nounits 2>/dev/null || echo "N/A")\nUTIL=$(nvidia-smi --query-gpu=utilization.gpu --format=csv,noheader,nounits 2>/dev/null || echo "N/A")\necho "$TIMESTAMP | Temp: ${TEMP}C | Power: ${POWER}W | Util: ${UTIL}%" >> $LOGFILE'),

    ('Quick: List Active Services',
     'Document what services are running on redfin',
     2,
     'it_triad_jr',
     E'Create a services inventory at /ganuda/reports/redfin_services_jan19.md:\n\n# Redfin Active Services - January 19, 2026\n\n## AI/ML Services\n- vLLM: port 8000 (Nemotron-9B inference)\n- LLM Gateway: port 8080 (Council voting, chat)\n\n## Web Services\n- SAG UI: port 4000 (ITSM frontend)\n- VetAssist Frontend: port 3000 (Next.js)\n- VetAssist Backend: port 8001 (FastAPI)\n\n## Background Services\n- Jr Queue Workers (3 active)\n- Consciousness Cascade Daemon\n\n## Database\n- PostgreSQL on bluefin:5432 (zammad_production)\n\n*Cherokee AI Federation*'),

    ('Integrate Learning Store with Executor',
     'Wire up the new JrLearningStore to record executions',
     2,
     'it_triad_jr',
     E'Modify /ganuda/jr_executor/task_executor.py to integrate the learning store:\n\n1. Add import at top of file:\nfrom jr_learning_store import JrLearningStore\n\n2. In __init__ method, add:\nself.learning_store = JrLearningStore(jr_name="it_triad_jr")\n\n3. After reflection is generated (around line 250), add:\ntry:\n    self.learning_store.record_execution(task, result, reflection)\n    print("[LEARNING] Recorded execution outcome")\nexcept Exception as e:\n    print(f"[LEARNING] Failed to record: {e}")')
RETURNING id, title;

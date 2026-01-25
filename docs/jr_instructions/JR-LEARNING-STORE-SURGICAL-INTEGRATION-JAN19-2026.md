# Jr Instruction: Learning Store Surgical Integration

```yaml
task_id: learning_store_surgical_integration
priority: 1
assigned_to: it_triad_jr
target: redfin
council_approved: true
estimated_effort: 15 minutes
```

## Background

The JrLearningStore class exists at `/ganuda/jr_executor/jr_learning_store.py`. We need to integrate it into `task_executor.py` to record execution outcomes for future learning.

**CRITICAL:** Previous attempt (Task 159) was blocked for trying to replace the entire file. This instruction specifies THREE SURGICAL EDITS only.

## Council Approval

All 7 specialists approved this surgical integration approach:
- Crawdad: Safe, uses existing credential pattern
- Gecko: Minimal changes, low regression risk
- Turtle: Learning serves future generations
- Eagle Eye: Adds observability
- Spider: Extends existing reflection pattern
- Peace Chief: Consensus reached
- Raven: Foundation for continuous improvement

## Instructions

Make exactly THREE edits to `/ganuda/jr_executor/task_executor.py`:

### Edit 1: Add Import (after ICL Dynamics import)

Find this exact text:
```python
except ImportError as e:
    ICL_AVAILABLE = False
    print(f"[WARN] ICL Dynamics not available: {e}")


class TaskExecutor:
```

Replace with:
```python
except ImportError as e:
    ICL_AVAILABLE = False
    print(f"[WARN] ICL Dynamics not available: {e}")

# Import Learning Store for recording execution outcomes (Phase 7)
try:
    from jr_learning_store import JrLearningStore
    LEARNING_STORE_AVAILABLE = True
    print("[INFO] JrLearningStore loaded - execution learning enabled")
except ImportError as e:
    LEARNING_STORE_AVAILABLE = False
    print(f"[WARN] JrLearningStore not available: {e}")


class TaskExecutor:
```

### Edit 2: Initialize Learning Store (in __init__)

Find this exact text:
```python
        if MGRPO_AVAILABLE:
            self.momentum_learner = MomentumJrLearner(jr_type)
            print(f"[M-GRPO] Momentum learner initialized for {jr_type}")
        else:
            self.momentum_learner = None

    def execute_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
```

Replace with:
```python
        if MGRPO_AVAILABLE:
            self.momentum_learner = MomentumJrLearner(jr_type)
            print(f"[M-GRPO] Momentum learner initialized for {jr_type}")
        else:
            self.momentum_learner = None

        # Phase 7: Initialize learning store for recording outcomes
        if LEARNING_STORE_AVAILABLE:
            self.learning_store = JrLearningStore(jr_name=jr_type)
            print(f"[LEARNING] Learning store initialized for {jr_type}")
        else:
            self.learning_store = None

    def execute_steps(self, steps: List[Dict]) -> List[Dict[str, Any]]:
```

### Edit 3: Record Learning (after reflection logging)

Find this exact text:
```python
                    # Log improvements for future learning
                    if reflection.get('improvements'):
                        print(f"[REFLECT] Improvements suggested: {reflection['improvements']}")

        except Exception as e:
```

Replace with:
```python
                    # Log improvements for future learning
                    if reflection.get('improvements'):
                        print(f"[REFLECT] Improvements suggested: {reflection['improvements']}")

                    # Phase 7: Record execution outcome for learning
                    if self.learning_store:
                        try:
                            self.learning_store.record_execution(task, result, reflection)
                            print(f"[LEARNING] Recorded outcome: success={result.get('success')}, type={self.learning_store._classify_task_type(task)}")
                        except Exception as le:
                            print(f"[LEARNING] Failed to record: {le}")

        except Exception as e:
```

## Verification

After edits, run this test:
```bash
# Check the import works
cd /ganuda/jr_executor
python3 -c "from task_executor import TaskExecutor; t = TaskExecutor(); print('Learning store:', t.learning_store)"

# Queue a test task and check learning table
PGPASSWORD=jawaseatlasers2 psql -h 192.168.132.222 -U claude -d zammad_production -c "
SELECT COUNT(*) FROM jr_execution_learning;
"
```

## Success Criteria

1. [ ] TaskExecutor imports JrLearningStore without error
2. [ ] TaskExecutor.__init__ creates self.learning_store
3. [ ] Execution outcomes appear in jr_execution_learning table
4. [ ] Existing task execution still works normally

## Rollback

If issues occur:
```bash
cd /ganuda/jr_executor
git diff task_executor.py  # See changes
git checkout task_executor.py  # Revert
```

---

*Cherokee AI Federation - For the Seven Generations*
*Council Approved: January 19, 2026*

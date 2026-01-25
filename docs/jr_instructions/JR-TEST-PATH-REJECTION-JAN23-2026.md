# Jr Task: Test Path Rejection

This test should FAIL because the path contains a placeholder pattern.

**File:** `/path/to/some/hallucinated/file.py`

```python
#!/usr/bin/env python3
"""This file should NOT be created - path is a placeholder."""
print("This should not exist!")
```

Also testing another bad path:

**File:** `/ganuda/lib/${variable}/test.py`

```python
print("Also should not exist - variable in path")
```

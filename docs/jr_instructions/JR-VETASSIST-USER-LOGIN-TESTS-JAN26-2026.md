# Jr Instruction: VetAssist User Login Functional Tests

**Task ID:** To be assigned
**Jr Type:** Research Jr.
**Priority:** P2
**Category:** QA Testing

---

## Objective

Use crawl4ai to login as each of the 5 test users and verify:
- Login works
- Dashboard accessible after login
- Profile page accessible
- Claim wizard accessible

---

## Test Script Location

`/ganuda/scripts/vetassist_user_tests.py`

---

## Execute Test

```bash
cd /ganuda/scripts && /home/dereadi/cherokee_venv/bin/python vetassist_user_tests.py
```

---

## Expected Output

Report at: `/ganuda/docs/reports/VETASSIST-USER-TESTS-20260126.md`

---

## Success Criteria

- Script runs without Python errors
- Report file is created
- Results show which tests pass/fail for each user

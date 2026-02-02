# JR Instruction: Fix reset_vetassist_test_accounts.py Database Name

**JR ID:** JR-FIX-RESET-SCRIPT-DATABASE-JAN29-2026
**Priority:** P0 - CRITICAL
**Assigned To:** Infrastructure Jr.
**Related:** ULTRATHINK-VETASSIST-DATABASE-CONFIG-DEBT-JAN29-2026
**Council Vote:** 3c944bed582ce3d3 (88.3% confidence)

---

## Objective

Fix the database name in `/ganuda/scripts/reset_vetassist_test_accounts.py` so password resets actually work.

---

## Problem

Line 17 points to the wrong database:

```python
conn = psycopg2.connect(
    host='192.168.132.222',
    dbname='triad_federation',  # WRONG! Should be zammad_production
    user='claude',
    password='jawaseatlasers2'
)
```

The VetAssist users table is in `zammad_production`, not `triad_federation`. Running this script updates nothing.

---

## Implementation

### Step 1: Edit line 17

Change:
```python
dbname='triad_federation',
```

To:
```python
dbname='zammad_production',
```

### Step 2: Run the script to reset passwords

```bash
cd /ganuda/scripts
python3 reset_vetassist_test_accounts.py
```

Expected output:
```
Resetting VetAssist test account passwords...
  ✓ test1@vetassist.test -> password1
  ✗ Account not found: test2@vetassist.test
  ✗ Account not found: test3@vetassist.test
  ✗ Account not found: test4@vetassist.test
  ✗ Account not found: test5@vetassist.test

Done. Test accounts ready for use.
```

Note: test2-5 don't exist yet - that's expected. test1 (Marcus) should show ✓.

### Step 3: Verify password works

```bash
curl -X POST "http://192.168.132.223:8001/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test1@vetassist.test", "password": "password1"}'
```

Should return a token (not "Incorrect email or password").

---

## Additional Task: Seed Missing Test Users

After fixing the database name, run the seed script to create test2-5:

```bash
cd /ganuda/vetassist/backend
source venv/bin/activate
python3 scripts/seed_test_users.py
```

Then run the reset script again to confirm all 5 accounts work.

---

## Verification

1. `python3 /ganuda/scripts/reset_vetassist_test_accounts.py` shows ✓ for all accounts
2. Login with test1@vetassist.test / password1 succeeds
3. Login with test2-5 accounts succeeds with password2-5

---

FOR SEVEN GENERATIONS

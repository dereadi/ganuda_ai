# Jr Instruction: VetAssist Functional Testing with crawl4ai

**Task ID:** To be assigned
**Jr Type:** Research Jr.
**Priority:** P2
**Category:** QA Testing

---

## Objective

Use crawl4ai to login as each test user and verify VetAssist functionality. Document working and broken features.

---

## Test Users (from thermal memory id: 45741)

| Login | Password | Profile |
|-------|----------|---------|
| test1@vetassist.test | password1 | Marcus Johnson - Army, 70% rating. PTSD, TBI, knee, hearing |
| test2@vetassist.test | password2 | Sarah Williams - Navy, 40% rating. Back, anxiety, tinnitus |
| test3@vetassist.test | password3 | David Chen - Air Force, 30% rating. Shoulder, sleep apnea |
| test4@vetassist.test | password4 | Maria Rodriguez - Marines, 50% MST, PTSD, migraines |
| test5@vetassist.test | password5 | James Thompson - Coast Guard, 0% New claim seeker |

---

## Base URL

https://vetassist.ganuda.us/

---

## Test Scenarios

### 1. Authentication Tests (all users)
- [ ] Login with valid credentials
- [ ] Verify redirect to dashboard after login
- [ ] Logout functionality
- [ ] Session persistence (refresh page)

### 2. Dashboard Tests (logged in users)
- [ ] Dashboard loads without errors
- [ ] User profile information displays correctly
- [ ] Navigation menu works

### 3. Claim Wizard Tests (test1, test4, test5)
- [ ] Start new claim wizard
- [ ] Select condition type
- [ ] Upload test document (use sample PDF)
- [ ] Complete wizard steps
- [ ] Save draft functionality

### 4. Profile Tests (test2)
- [ ] View profile page
- [ ] Edit profile information
- [ ] Update veteran status

### 5. Error Handling (all users)
- [ ] Access protected routes without login (should redirect)
- [ ] Invalid form submissions show errors
- [ ] 404 pages display correctly

---

## crawl4ai Usage Pattern

```python
from crawl4ai import AsyncWebCrawler

async def test_login(email, password):
    async with AsyncWebCrawler() as crawler:
        # Navigate to login
        result = await crawler.arun(
            url="https://vetassist.ganuda.us/login",
            js_code=f'''
                document.querySelector('input[name="email"]').value = "{email}";
                document.querySelector('input[name="password"]').value = "{password}";
                document.querySelector('button[type="submit"]').click();
            ''',
            wait_for="networkidle"
        )
        return result
```

---

## Output Requirements

Create test report at:
`/ganuda/docs/reports/VETASSIST-FUNCTIONAL-TEST-20260126.md`

Include:
- Pass/Fail status for each test
- Screenshots of failures (if crawl4ai supports)
- Error messages encountered
- Recommendations for fixes

---

## Prerequisites

- VetAssist backend must be running
- VetAssist frontend must be accessible at https://vetassist.ganuda.us/
- crawl4ai must be installed: `pip install crawl4ai`

---

## Do NOT

- Modify any VetAssist code
- Create or delete real user data
- Submit actual VA claims
- Store passwords in report (refer to test user numbers)

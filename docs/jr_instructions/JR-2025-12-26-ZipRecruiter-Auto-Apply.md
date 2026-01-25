# Jr Instructions: ZipRecruiter Auto-Apply Automation

**Date**: 2025-12-26
**Assigned To**: Jr on tpm-macbook
**Priority**: High
**Estimated Complexity**: Medium

---

## Objective

Build a ZipRecruiter job application automation script similar to the Indeed approach, but adapting for ZipRecruiter's interface and (hopefully) less aggressive bot detection.

## Background

Indeed automation failed due to Cloudflare bot detection. ZipRecruiter may be more amenable to browser automation. Key learnings from Indeed attempt:

1. LLM resume customization works well
2. Passkey auth is device-bound to tpm-macbook
3. Persistent browser context helps maintain sessions
4. playwright-stealth provides some protection

## Requirements

### 1. Create Login Capture Script

File: `/Users/Shared/ganuda/scripts/ziprecruiter_login_capture.py`

```python
#!/usr/bin/env python3
"""
ZipRecruiter Login Capture - Run once to establish session
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

STORAGE_DIR = Path("/Users/Shared/ganuda/data/ziprecruiter/browser_state")
STORAGE_FILE = STORAGE_DIR / "state.json"

async def capture_login():
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=100)
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
        )
        page = await context.new_page()

        await page.goto("https://www.ziprecruiter.com/login")

        print("\n" + "="*60)
        print("LOG IN TO ZIPRECRUITER MANUALLY")
        print("Press ENTER when logged in and on your dashboard...")
        print("="*60 + "\n")

        input()

        await context.storage_state(path=str(STORAGE_FILE))
        print(f"Session saved to {STORAGE_FILE}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(capture_login())
```

### 2. Create Main Automation Script

File: `/Users/Shared/ganuda/scripts/ziprecruiter_apply_local.py`

Key components to implement:

#### A. Configuration
```python
REDFIN_LLM = "http://192.168.132.223:8080"
API_KEY = "ck-cabccc2d6037c1dce1a027cc80df7b14cdba66143e3c2d4f3bdf0fd53b6ab4a5"

APPLICANT = {
    "first_name": "Darrell",
    "last_name": "Reading",
    "email": "dereadi@gmail.com",
    "phone": "",  # Add if needed
    "city": "Bentonville",
    "state": "Arkansas",
    "zip": "72712",
}

STORAGE_DIR = Path("/Users/Shared/ganuda/data/ziprecruiter/browser_state")
SCREENSHOTS_DIR = Path("/Users/Shared/ganuda/data/ziprecruiter/screenshots")
RESUMES_DIR = Path("/Users/Shared/ganuda/data/resumes/customized")
BASE_RESUME = Path("/Users/Shared/ganuda/data/resumes/base_resume.md")
```

#### B. LLM Resume Customization
Reuse the working pattern from Indeed script:
```python
def ask_llm(prompt: str, max_tokens: int = 1000) -> str:
    """Call redfin LLM Gateway"""
    response = requests.post(
        f"{REDFIN_LLM}/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "qwen",
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": 0.7
        },
        timeout=120
    )
    return response.json()["choices"][0]["message"]["content"]

def customize_resume_for_job(job_title: str, job_description: str, company: str) -> Path:
    """Generate tailored resume for specific job"""
    # Same pattern as Indeed - prompt LLM to rewrite summary and bullets
    pass
```

#### C. ZipRecruiter Navigation
Research ZipRecruiter's DOM structure. Key elements to identify:

- Login form selectors
- Job search results page structure
- "Apply" or "1-Click Apply" button selectors
- Application form fields
- Success/confirmation indicators

#### D. Bot Detection Handling
```python
async def check_for_blocks(page) -> bool:
    """Check for captcha or bot detection"""
    # Look for common patterns:
    # - Cloudflare challenge
    # - reCAPTCHA
    # - "Please verify you're human"
    # - Access denied pages

    block_indicators = [
        'text="Verify you are human"',
        'text="Access Denied"',
        'iframe[title*="recaptcha"]',
        'text="Please complete the security check"'
    ]

    for indicator in block_indicators:
        if await page.locator(indicator).count() > 0:
            return True
    return False
```

#### E. Application Flow
```python
async def apply_to_job(page, job_url: str, job_info: dict):
    """
    1. Navigate to job page
    2. Check for blocks, pause if detected
    3. Click Apply button
    4. Fill form fields
    5. Customize and attach resume
    6. Submit (or pause for manual review)
    7. Screenshot result
    8. Log to database
    """
    pass
```

### 3. Database Integration

Use same `job_applications` table on bluefin, add source field:

```python
def log_application(job_title, company, url, success, error_msg=None, source="ziprecruiter"):
    conn = psycopg2.connect(
        host="192.168.132.225",
        database="triad_federation",
        user="ganuda",
        password="jawaseatlasers2"
    )
    # Insert with source field
```

### 4. Directory Structure

Create:
```
/Users/Shared/ganuda/data/ziprecruiter/
├── browser_state/
│   └── state.json
├── screenshots/
└── cookies/
```

## Testing Steps

1. Run login capture: `~/cherokee_venv/bin/python3 /Users/Shared/ganuda/scripts/ziprecruiter_login_capture.py`
2. Log in manually, press ENTER
3. Run apply script with limit=1: `~/cherokee_venv/bin/python3 /Users/Shared/ganuda/scripts/ziprecruiter_apply_local.py --limit=1`
4. Watch for bot detection - if blocked, document patterns
5. If successful, increase limit gradually

## Success Criteria

- [ ] Login session persists across script runs
- [ ] LLM customizes resume for each job
- [ ] Script navigates to job pages without immediate blocks
- [ ] Application forms get filled (at minimum)
- [ ] Applications logged to database with source="ziprecruiter"

## Notes

- Run ONLY on tpm-macbook (where browser state is captured)
- Use `--headless=false` for initial testing to watch behavior
- Take screenshots at each step for debugging
- If blocked, try slower navigation, more human-like delays

## Fallback

If ZipRecruiter also blocks automation:
1. Try LinkedIn Easy Apply
2. Consider browser extension approach
3. Semi-automated: script prepares data, user clicks submit

---

*For Seven Generations*

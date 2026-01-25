# Jr Build Instructions: Indeed Auto-Apply with Playwright

**Task ID:** JR-INDEED-AUTOAPPLY-001
**Priority:** P2 (High - User Productivity)
**Date:** 2025-12-26
**Author:** TPM
**Source:** User Request - Automate Indeed job applications

---

## Node Distribution (IMPORTANT)

**Keep redfin's GPU free for inference!**

| Component | Node | Why |
|-----------|------|-----|
| Web Automation (Playwright) | **greenfin** | CPU work - browser automation |
| Job Email Daemon | **greenfin** | CPU work - email processing |
| Database (PostgreSQL) | **bluefin** | Already there |
| LLM Inference (Qwen) | **redfin** | GPU work - model serving |
| Resume Storage | **greenfin** | Local to automation |

**Alternative for Mac Studios:**
- **sasass/sasass2** can also run Playwright
- Use MLX for local inference if needed
- Good for testing/development

---

## Problem Statement

The job email daemon identifies high-match jobs from Indeed emails. Currently, the user must manually:
1. Open the email
2. Click the apply link
3. Fill out the Indeed Easy Apply form
4. Upload resume
5. Submit

We need to automate this for high-match jobs (score >= 60%).

---

## Solution: Playwright-Based Auto-Apply Agent

```
[Job Email Daemon]
       │
       ├─► Detects high-match Indeed job (>= 60%)
       │
       ▼
[Indeed Auto-Apply Agent]
       │
       ├─► Launch headless browser
       ├─► Navigate to apply link
       ├─► Detect application type (Easy Apply vs External)
       ├─► Fill form fields from user profile
       ├─► Upload resume
       ├─► Submit application
       │
       ▼
[Log Result to Database]
       │
       └─► Send Telegram notification
```

---

## Prerequisites

### 1. Playwright Installation on greenfin

Playwright needs to be installed on **greenfin** (not redfin):

```bash
# SSH to greenfin
ssh 192.168.132.224

# Install Playwright in the venv
~/cherokee_venv/bin/pip install playwright playwright-stealth

# Install browser binaries (requires internet - do while connected)
~/cherokee_venv/bin/playwright install chromium

# Verify installation
~/cherokee_venv/bin/python3 -c "from playwright.sync_api import sync_playwright; print('OK')"
```

### 2. Alternative: Mac Studio Setup

For sasass or sasass2:

```bash
# Create venv if needed
python3 -m venv ~/cherokee_venv

# Install packages
~/cherokee_venv/bin/pip install playwright playwright-stealth psycopg2-binary requests

# Install browser
~/cherokee_venv/bin/playwright install chromium
```

### 2. Indeed Account Session

Indeed uses authentication. We need to either:
- **Option A**: Store Indeed session cookies (recommended for Easy Apply)
- **Option B**: Use Indeed API (requires partner access)
- **Option C**: Manual login once, save session state

We'll use **Option A** - cookie-based session persistence.

---

## Implementation

### Step 1: Create User Profile Store

In `/ganuda/email_daemon/applicant_profile.py`:

```python
#!/usr/bin/env python3
"""
Applicant Profile for Auto-Apply
Stores user information for form filling
"""

APPLICANT_PROFILE = {
    # Personal Info
    "first_name": "Darrell",
    "last_name": "Reading",
    "full_name": "Darrell Eugene Reading II",
    "email": "dereadi@gmail.com",
    "phone": "479-877-9441",
    "phone_formatted": "(479) 877-9441",

    # Location
    "city": "Bentonville",
    "state": "AR",
    "zip_code": "72712",
    "country": "United States",
    "address": "Bentonville, AR 72712",

    # Work Authorization
    "authorized_to_work": True,
    "requires_sponsorship": False,
    "us_citizen": True,

    # Experience
    "years_experience": "35",
    "current_title": "Multi-Agent Systems Architect",
    "current_company": "Cherokee AI Federation (Independent R&D)",

    # Education
    "highest_education": "Some College",
    "school": "Southern New Hampshire University",
    "degree": "B.S. Cyber Security (In Progress)",

    # Resume
    "resume_path": "/ganuda/data/resumes/Darrell_Eugene_Reading_Resume_MultiAgent_Dec2025.pdf",

    # Salary (for forms that ask)
    "desired_salary": "150000",
    "salary_range": "120000-200000",

    # Availability
    "start_date": "Immediately",
    "notice_period": "2 weeks",

    # Links
    "linkedin": "https://linkedin.com/in/dereadi",
    "github": "https://github.com/dereadi",
    "portfolio": "",

    # Cover Letter Template
    "cover_letter_template": """
Dear Hiring Manager,

I am writing to express my interest in the {position} role at {company}. With 35 years of enterprise infrastructure experience, including recent work building production multi-agent AI systems, I bring a unique combination of deep technical expertise and practical AI/ML implementation skills.

My background includes:
- Senior Infrastructure Engineer at Walmart (1990-2025)
- Multi-Agent Systems Architect for Cherokee AI Federation
- 26 years of military leadership as SFC in Arkansas Army National Guard

I am particularly drawn to this opportunity because {reason}.

I look forward to discussing how my experience can contribute to your team.

Best regards,
Darrell Reading
"""
}


def get_field(field_name: str, default: str = "") -> str:
    """Get a field from the applicant profile."""
    return APPLICANT_PROFILE.get(field_name, default)


def format_cover_letter(position: str, company: str, reason: str = "of the technical challenges involved") -> str:
    """Generate a cover letter for a specific position."""
    return APPLICANT_PROFILE["cover_letter_template"].format(
        position=position,
        company=company,
        reason=reason
    )
```

### Step 2: Create Indeed Auto-Apply Agent

In `/ganuda/email_daemon/indeed_auto_apply.py`:

```python
#!/usr/bin/env python3
"""
Indeed Auto-Apply Agent
Uses Playwright to automatically apply to Indeed Easy Apply jobs
"""

import asyncio
import logging
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Tuple

from playwright.async_api import async_playwright, Page, Browser, BrowserContext
from playwright_stealth import stealth_async
import psycopg2

from applicant_profile import APPLICANT_PROFILE, get_field

logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('indeed_auto_apply')

# Paths
COOKIES_PATH = Path("/ganuda/data/indeed/cookies.json")
SCREENSHOTS_PATH = Path("/ganuda/data/indeed/screenshots")
SCREENSHOTS_PATH.mkdir(parents=True, exist_ok=True)

# Database config
DB_CONFIG = {
    'host': '192.168.132.222',
    'database': 'triad_federation',
    'user': 'claude',
    'password': 'jawaseatlasers2'
}


class IndeedAutoApply:
    """
    Automated Indeed Easy Apply agent.

    This agent:
    1. Opens an Indeed job application page
    2. Detects if it's Easy Apply or external
    3. Fills in form fields using the applicant profile
    4. Uploads resume
    5. Submits the application
    6. Logs the result
    """

    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.playwright = None

    async def start(self):
        """Initialize browser with stealth mode."""
        self.playwright = await async_playwright().start()

        # Launch browser with realistic settings
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Set to False for debugging
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage',
            ]
        )

        # Create context with realistic viewport and user agent
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/Chicago',
        )

        # Load saved cookies if they exist
        if COOKIES_PATH.exists():
            cookies = json.loads(COOKIES_PATH.read_text())
            await self.context.add_cookies(cookies)
            logger.info("Loaded saved Indeed cookies")

        self.page = await self.context.new_page()

        # Apply stealth to avoid detection
        await stealth_async(self.page)

        logger.info("Browser initialized with stealth mode")

    async def stop(self):
        """Clean up browser resources."""
        if self.context:
            # Save cookies for next session
            cookies = await self.context.cookies()
            COOKIES_PATH.parent.mkdir(parents=True, exist_ok=True)
            COOKIES_PATH.write_text(json.dumps(cookies))
            logger.info("Saved Indeed cookies")

        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def apply_to_job(self, apply_url: str, job_info: Dict) -> Tuple[bool, str]:
        """
        Apply to a job on Indeed.

        Args:
            apply_url: The Indeed apply URL from the email
            job_info: Dict with job_title, company, match_score, etc.

        Returns:
            Tuple of (success: bool, message: str)
        """
        job_title = job_info.get('job_title', 'Unknown Position')
        company = job_info.get('company', 'Unknown Company')

        logger.info(f"Starting application: {job_title} at {company}")

        try:
            # Navigate to apply page
            await self.page.goto(apply_url, wait_until='networkidle', timeout=30000)
            await asyncio.sleep(2)  # Let page fully render

            # Take screenshot for debugging
            screenshot_name = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{company[:20]}.png"
            await self.page.screenshot(path=SCREENSHOTS_PATH / screenshot_name)

            # Check if we need to login
            if await self._needs_login():
                logger.warning("Indeed login required - cannot auto-apply without session")
                return False, "Login required - please login to Indeed manually first"

            # Check application type
            app_type = await self._detect_application_type()

            if app_type == "external":
                logger.info("External application - cannot auto-apply")
                return False, "External application site - manual apply needed"

            if app_type == "easy_apply":
                return await self._complete_easy_apply(job_info)

            return False, f"Unknown application type: {app_type}"

        except Exception as e:
            logger.error(f"Application failed: {e}")
            await self.page.screenshot(path=SCREENSHOTS_PATH / f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
            return False, f"Error: {str(e)}"

    async def _needs_login(self) -> bool:
        """Check if Indeed is asking for login."""
        login_indicators = [
            'input[name="__email"]',
            'button[data-tn-element="sign-in-button"]',
            'text="Sign in"',
            'text="Create an account"'
        ]

        for indicator in login_indicators:
            if await self.page.locator(indicator).count() > 0:
                return True
        return False

    async def _detect_application_type(self) -> str:
        """Detect if this is Easy Apply or external application."""
        # Look for Indeed Easy Apply indicators
        easy_apply_indicators = [
            'button:has-text("Apply now")',
            'button:has-text("Continue")',
            '[data-testid="ia-IndeedApplyButton"]',
            'text="Apply with Indeed"',
        ]

        for indicator in easy_apply_indicators:
            if await self.page.locator(indicator).count() > 0:
                return "easy_apply"

        # Look for external redirect indicators
        external_indicators = [
            'text="Apply on company site"',
            'text="Apply on external site"',
        ]

        for indicator in external_indicators:
            if await self.page.locator(indicator).count() > 0:
                return "external"

        return "unknown"

    async def _complete_easy_apply(self, job_info: Dict) -> Tuple[bool, str]:
        """Complete the Indeed Easy Apply flow."""
        logger.info("Starting Easy Apply flow")

        max_steps = 10  # Safety limit
        step = 0

        while step < max_steps:
            step += 1
            logger.info(f"Easy Apply step {step}")

            # Take screenshot at each step
            await self.page.screenshot(
                path=SCREENSHOTS_PATH / f"step_{step}_{datetime.now().strftime('%H%M%S')}.png"
            )

            # Check if we're done
            if await self._is_application_complete():
                logger.info("Application submitted successfully!")
                return True, "Application submitted via Easy Apply"

            # Fill any visible form fields
            await self._fill_form_fields()

            # Upload resume if needed
            await self._upload_resume_if_needed()

            # Click continue/next/submit button
            clicked = await self._click_next_button()

            if not clicked:
                logger.warning("Could not find next button")
                return False, "Could not proceed - no next button found"

            await asyncio.sleep(2)  # Wait for next page/step

        return False, "Exceeded maximum steps"

    async def _is_application_complete(self) -> bool:
        """Check if application was submitted."""
        success_indicators = [
            'text="Application submitted"',
            'text="Your application has been submitted"',
            'text="Thanks for applying"',
            'text="Application sent"',
        ]

        for indicator in success_indicators:
            if await self.page.locator(indicator).count() > 0:
                return True
        return False

    async def _fill_form_fields(self):
        """Fill visible form fields with applicant data."""

        # Common field mappings: (selector patterns, profile field)
        field_mappings = [
            # Name fields
            (['input[name*="firstName"]', 'input[id*="firstName"]', 'input[placeholder*="First"]'], 'first_name'),
            (['input[name*="lastName"]', 'input[id*="lastName"]', 'input[placeholder*="Last"]'], 'last_name'),
            (['input[name*="fullName"]', 'input[id*="name"]'], 'full_name'),

            # Contact
            (['input[name*="email"]', 'input[type="email"]', 'input[id*="email"]'], 'email'),
            (['input[name*="phone"]', 'input[type="tel"]', 'input[id*="phone"]'], 'phone'),

            # Location
            (['input[name*="city"]', 'input[id*="city"]'], 'city'),
            (['input[name*="zip"]', 'input[id*="zip"]', 'input[id*="postal"]'], 'zip_code'),

            # Experience
            (['input[name*="years"]', 'input[id*="experience"]'], 'years_experience'),

            # Salary
            (['input[name*="salary"]', 'input[id*="salary"]', 'input[id*="compensation"]'], 'desired_salary'),
        ]

        for selectors, field_name in field_mappings:
            value = get_field(field_name)
            if not value:
                continue

            for selector in selectors:
                try:
                    element = self.page.locator(selector).first
                    if await element.count() > 0 and await element.is_visible():
                        current_value = await element.input_value()
                        if not current_value:  # Only fill if empty
                            await element.fill(value)
                            logger.debug(f"Filled {field_name}: {selector}")
                            break
                except Exception as e:
                    logger.debug(f"Could not fill {selector}: {e}")

        # Handle common yes/no questions
        await self._handle_yes_no_questions()

    async def _handle_yes_no_questions(self):
        """Handle common yes/no questions on applications."""

        # Questions where we answer YES
        yes_patterns = [
            'authorized to work',
            'legally authorized',
            'eligible to work',
            '18 years or older',
            'background check',
            'drug test',
        ]

        # Questions where we answer NO
        no_patterns = [
            'require sponsorship',
            'need visa',
            'require visa',
            'H1B',
        ]

        # Find all radio/checkbox groups
        # This is simplified - real implementation needs more sophisticated parsing
        try:
            # Look for "Yes" buttons/radios near authorization questions
            auth_question = self.page.locator('text=/authorized.*work/i')
            if await auth_question.count() > 0:
                yes_button = self.page.locator('input[value="Yes"], label:has-text("Yes")').first
                if await yes_button.count() > 0:
                    await yes_button.click()
                    logger.debug("Answered 'authorized to work': Yes")

            # Look for sponsorship question
            sponsor_question = self.page.locator('text=/sponsorship/i')
            if await sponsor_question.count() > 0:
                no_button = self.page.locator('input[value="No"], label:has-text("No")').first
                if await no_button.count() > 0:
                    await no_button.click()
                    logger.debug("Answered 'sponsorship': No")

        except Exception as e:
            logger.debug(f"Error handling yes/no questions: {e}")

    async def _upload_resume_if_needed(self):
        """Upload resume if file input is present."""
        resume_path = get_field('resume_path')

        if not resume_path or not os.path.exists(resume_path):
            logger.warning(f"Resume not found: {resume_path}")
            return

        # Look for file input
        file_inputs = [
            'input[type="file"]',
            'input[accept*="pdf"]',
            'input[name*="resume"]',
        ]

        for selector in file_inputs:
            try:
                element = self.page.locator(selector).first
                if await element.count() > 0:
                    await element.set_input_files(resume_path)
                    logger.info(f"Uploaded resume: {resume_path}")
                    return
            except Exception as e:
                logger.debug(f"Could not upload via {selector}: {e}")

    async def _click_next_button(self) -> bool:
        """Click the next/continue/submit button."""
        button_patterns = [
            'button:has-text("Continue")',
            'button:has-text("Next")',
            'button:has-text("Submit")',
            'button:has-text("Apply")',
            'button[type="submit"]',
            '[data-testid*="submit"]',
            '[data-testid*="continue"]',
        ]

        for pattern in button_patterns:
            try:
                button = self.page.locator(pattern).first
                if await button.count() > 0 and await button.is_visible():
                    await button.click()
                    logger.info(f"Clicked: {pattern}")
                    return True
            except Exception as e:
                logger.debug(f"Could not click {pattern}: {e}")

        return False


def log_application(job_info: Dict, success: bool, message: str):
    """Log application attempt to database."""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO job_applications (
                email_id, job_title, company, apply_url,
                match_score, application_method, success,
                result_message, applied_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (
            job_info.get('email_id'),
            job_info.get('job_title'),
            job_info.get('company'),
            job_info.get('apply_url'),
            job_info.get('match_score', 0),
            'indeed_easy_apply',
            success,
            message
        ))

        conn.commit()
        conn.close()
        logger.info(f"Logged application: {success} - {message}")
    except Exception as e:
        logger.error(f"Failed to log application: {e}")


async def apply_to_indeed_job(apply_url: str, job_info: Dict) -> Tuple[bool, str]:
    """
    Main entry point for Indeed auto-apply.

    Args:
        apply_url: Indeed job apply URL
        job_info: Dict with job details (title, company, match_score, etc.)

    Returns:
        Tuple of (success, message)
    """
    agent = IndeedAutoApply()

    try:
        await agent.start()
        success, message = await agent.apply_to_job(apply_url, job_info)
        log_application(job_info, success, message)
        return success, message
    finally:
        await agent.stop()


# CLI for testing
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python indeed_auto_apply.py <apply_url>")
        sys.exit(1)

    url = sys.argv[1]
    job_info = {
        'job_title': 'Test Job',
        'company': 'Test Company',
        'match_score': 0.75
    }

    success, message = asyncio.run(apply_to_indeed_job(url, job_info))
    print(f"Result: {'SUCCESS' if success else 'FAILED'} - {message}")
```

### Step 3: Create Database Schema

Run on bluefin:

```sql
-- Job applications tracking table
CREATE TABLE IF NOT EXISTS job_applications (
    id SERIAL PRIMARY KEY,
    email_id INTEGER REFERENCES emails(id),
    job_title VARCHAR(256),
    company VARCHAR(128),
    apply_url TEXT,
    match_score FLOAT,
    application_method VARCHAR(32),  -- 'indeed_easy_apply', 'manual', 'external'
    success BOOLEAN,
    result_message TEXT,
    applied_at TIMESTAMP DEFAULT NOW(),
    follow_up_date DATE,
    status VARCHAR(32) DEFAULT 'submitted',  -- 'submitted', 'viewed', 'interview', 'rejected', 'offer'
    notes TEXT
);

CREATE INDEX idx_job_apps_company ON job_applications(company);
CREATE INDEX idx_job_apps_status ON job_applications(status);
CREATE INDEX idx_job_apps_applied ON job_applications(applied_at DESC);
CREATE INDEX idx_job_apps_score ON job_applications(match_score DESC);
```

### Step 4: Integrate with Job Email Daemon

Add to the daemon's high-match handling (in `job_email_daemon_v2.py`):

```python
from indeed_auto_apply import apply_to_indeed_job

# In the sync_and_classify method, after detecting high match:
if match_score >= 0.60 and 'indeed.com' in (apply_url or ''):
    # Attempt auto-apply for high-match Indeed jobs
    job_info = {
        'email_id': email_id,
        'job_title': job_position or subject,
        'company': job_company,
        'apply_url': apply_url,
        'match_score': match_score
    }

    # Run auto-apply asynchronously
    asyncio.create_task(auto_apply_with_notification(job_info))

async def auto_apply_with_notification(job_info: Dict):
    """Apply and send notification of result."""
    try:
        success, message = await apply_to_indeed_job(
            job_info['apply_url'],
            job_info
        )

        # Send Telegram notification
        emoji = "✅" if success else "❌"
        alert_msg = f"{emoji} Auto-Apply: {job_info['job_title']} at {job_info['company']}\n{message}"
        send_plain_alert(alert_msg)

    except Exception as e:
        logger.error(f"Auto-apply failed: {e}")
        send_plain_alert(f"❌ Auto-apply error: {job_info['job_title']}\n{str(e)}")
```

---

## Initial Setup

### 1. Copy Resume to Expected Path

```bash
mkdir -p /ganuda/data/resumes
scp 192.168.132.241:/Users/dereadi/Downloads/Darrell_Eugene_Reading_Resume_MultiAgent_Dec2025.pdf \
    /ganuda/data/resumes/
```

### 2. Login to Indeed Manually (One-Time)

The first time, you need to login to Indeed manually to establish session cookies:

```bash
# Run with headless=False to see browser
cd /ganuda/email_daemon
python3 -c "
import asyncio
from playwright.async_api import async_playwright

async def login():
    p = await async_playwright().start()
    browser = await p.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    await page.goto('https://www.indeed.com')
    print('Please login to Indeed in the browser...')
    print('Press Enter when done')
    input()

    # Save cookies
    import json
    cookies = await context.cookies()
    with open('/ganuda/data/indeed/cookies.json', 'w') as f:
        json.dump(cookies, f)
    print('Cookies saved!')

    await browser.close()
    await p.stop()

asyncio.run(login())
"
```

### 3. Test with a Single Job

```bash
cd /ganuda/email_daemon
python3 indeed_auto_apply.py "https://www.indeed.com/viewjob?jk=abc123"
```

---

## Safety & Rate Limiting

**IMPORTANT**: To avoid being flagged as a bot:

1. **Rate Limit**: Maximum 5 applications per hour
2. **Human Delays**: Random delays between 2-5 seconds between actions
3. **Stealth Mode**: Using playwright-stealth to avoid detection
4. **Session Persistence**: Reuse cookies to look like returning user
5. **Screenshots**: Save screenshots for debugging and audit trail

Add to the agent:

```python
import random

async def human_delay(min_sec=2, max_sec=5):
    """Add random human-like delay."""
    await asyncio.sleep(random.uniform(min_sec, max_sec))
```

---

## Validation

```bash
# Check database for applications
psql -h 192.168.132.222 -U claude -d triad_federation -c "
SELECT job_title, company, success, result_message, applied_at
FROM job_applications
ORDER BY applied_at DESC LIMIT 10;
"

# Check screenshots
ls -la /ganuda/data/indeed/screenshots/

# Check daemon logs
tail -50 /var/log/ganuda/job_email_daemon.log
```

---

## Files to Create

1. `/ganuda/email_daemon/applicant_profile.py` - User profile for form filling
2. `/ganuda/email_daemon/indeed_auto_apply.py` - Playwright auto-apply agent
3. `/ganuda/data/indeed/cookies.json` - Indeed session cookies (auto-created)
4. `/ganuda/data/resumes/` - Resume storage directory

## SQL to Run

1. Create `job_applications` table on bluefin

---

## Troubleshooting

### "Login required" error
- Session cookies expired
- Re-run the manual login step to refresh cookies

### "External application"
- Job requires applying on company website
- Cannot auto-apply, will be logged for manual follow-up

### Bot detection / CAPTCHA
- Indeed may require CAPTCHA solving
- Consider using 2captcha or similar service
- Or log for manual intervention

### Form field not filled
- Check screenshots to see what fields are visible
- Add new selectors to `_fill_form_fields()` mapping

---

## Future Enhancements

1. **ZipRecruiter Support**: Similar pattern for ZipRecruiter Easy Apply
2. **LinkedIn Easy Apply**: Add LinkedIn application support
3. **CAPTCHA Solving**: Integrate 2captcha for blocked applications
4. **Smart Retry**: Retry failed applications with exponential backoff
5. **Application Tracking**: Track application status and follow-ups

---

*For Seven Generations - Cherokee AI Federation*
*"The arrow that aims true saves many draws"*

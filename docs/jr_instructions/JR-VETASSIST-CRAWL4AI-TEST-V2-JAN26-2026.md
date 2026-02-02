# Jr Instruction: VetAssist Functional Testing with crawl4ai v2

**Task ID:** To be assigned
**Jr Type:** Research Jr.
**Priority:** P2
**Category:** QA Testing

---

## Step 1: Create Test Script

Create file `/ganuda/scripts/vetassist_crawl_test.py`:

```python
#!/usr/bin/env python3
"""VetAssist Functional Testing with crawl4ai"""

import asyncio
from crawl4ai import AsyncWebCrawler

BASE_URL = "https://vetassist.ganuda.us"

TEST_USERS = [
    {"email": "test1@vetassist.test", "password": "password1", "name": "Marcus Johnson"},
    {"email": "test2@vetassist.test", "password": "password2", "name": "Sarah Williams"},
]

async def test_homepage():
    """Test homepage loads"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=BASE_URL)
        if result.success:
            print(f"✅ Homepage loaded: {len(result.html)} bytes")
            return True
        else:
            print(f"❌ Homepage failed: {result.error_message}")
            return False

async def test_login_page():
    """Test login page exists"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=f"{BASE_URL}/login")
        if result.success and "login" in result.html.lower():
            print("✅ Login page accessible")
            return True
        else:
            print("❌ Login page not found")
            return False

async def test_api_health():
    """Test API health endpoint"""
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(url=f"{BASE_URL}/api/v1/health")
        if result.success and "healthy" in result.html.lower():
            print("✅ API health endpoint OK")
            return True
        else:
            print("❌ API health check failed")
            return False

async def main():
    print("=" * 50)
    print("VetAssist Functional Test Report")
    print("=" * 50)

    results = {
        "homepage": await test_homepage(),
        "login_page": await test_login_page(),
        "api_health": await test_api_health(),
    }

    print("\n" + "=" * 50)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 50)

    # Write report
    with open("/ganuda/docs/reports/VETASSIST-CRAWL-TEST-20260126.md", "w") as f:
        f.write("# VetAssist Crawl4AI Test Report\\n\\n")
        f.write(f"**Date:** 2026-01-26\\n")
        f.write(f"**Results:** {passed}/{total} passed\\n\\n")
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            f.write(f"- {test}: {status}\\n")

    print("Report saved to /ganuda/docs/reports/VETASSIST-CRAWL-TEST-20260126.md")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Step 2: Run the Test

```bash
cd /ganuda/scripts && /home/dereadi/cherokee_venv/bin/python vetassist_crawl_test.py
```

---

## Step 3: Verify Report Created

```bash
cat /ganuda/docs/reports/VETASSIST-CRAWL-TEST-20260126.md
```

---

## Success Criteria

- Test script runs without errors
- Report file created at `/ganuda/docs/reports/VETASSIST-CRAWL-TEST-20260126.md`
- At least homepage and API health tests pass

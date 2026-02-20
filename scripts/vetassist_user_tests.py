#!/usr/bin/env python3
"""VetAssist User Functional Testing - Login and test as each user"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

BASE_URL = "http://localhost:3000"

TEST_USERS = [
    {"email": "test1@vetassist.test", "password": "password1", "name": "Marcus Johnson", "profile": "Army, 70%"},
    {"email": "test2@vetassist.test", "password": "password2", "name": "Sarah Williams", "profile": "Navy, 40%"},
    {"email": "test3@vetassist.test", "password": "password3", "name": "David Chen", "profile": "Air Force, 30%"},
    {"email": "test4@vetassist.test", "password": "password4", "name": "Maria Rodriguez", "profile": "Marines, 50%"},
    {"email": "test5@vetassist.test", "password": "password5", "name": "James Thompson", "profile": "Coast Guard, new"},
]

TESTS_TO_RUN = [
    ("login", "Login with credentials"),
    ("dashboard", "Access dashboard after login"),
    ("profile", "View profile page"),
    ("wizard_start", "Start claim wizard"),
]

results = []

async def test_user_login(crawler, user):
    """Test login for a specific user"""
    user_results = {"user": user["email"], "name": user["name"], "tests": {}}

    try:
        # Step 1: Go to login page and submit credentials
        login_js = f'''
        (async () => {{
            // Wait for form
            await new Promise(r => setTimeout(r, 1000));

            // Find and fill email
            const emailInput = document.querySelector('input[type="email"], input[name="email"], #email');
            if (emailInput) {{
                emailInput.value = "{user['email']}";
                emailInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}

            // Find and fill password
            const passInput = document.querySelector('input[type="password"], input[name="password"], #password');
            if (passInput) {{
                passInput.value = "{user['password']}";
                passInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}

            // Submit form
            await new Promise(r => setTimeout(r, 500));
            const submitBtn = document.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) submitBtn.click();

            await new Promise(r => setTimeout(r, 2000));
            return document.body.innerHTML;
        }})()
        '''

        result = await crawler.arun(
            url=f"{BASE_URL}/login",
            config=CrawlerRunConfig(js_code=login_js, wait_for="networkidle")
        )

        # Check if login succeeded (look for dashboard elements or redirect)
        if result.success:
            html_lower = result.html.lower()
            if "dashboard" in html_lower or "welcome" in html_lower or "logout" in html_lower:
                user_results["tests"]["login"] = {"pass": True, "note": "Login successful"}
                print(f"  ✅ {user['name']}: Login SUCCESS")
            elif "error" in html_lower or "invalid" in html_lower:
                user_results["tests"]["login"] = {"pass": False, "note": "Invalid credentials error"}
                print(f"  ❌ {user['name']}: Login FAILED - invalid credentials")
            else:
                user_results["tests"]["login"] = {"pass": None, "note": "Login status unclear"}
                print(f"  ⚠️  {user['name']}: Login status unclear")
        else:
            user_results["tests"]["login"] = {"pass": False, "note": result.error_message}
            print(f"  ❌ {user['name']}: Login FAILED - {result.error_message}")

        # Step 2: Test dashboard access
        dash_result = await crawler.arun(url=f"{BASE_URL}/dashboard")
        if dash_result.success and len(dash_result.html) > 1000:
            user_results["tests"]["dashboard"] = {"pass": True, "note": f"{len(dash_result.html)} bytes"}
            print(f"  ✅ {user['name']}: Dashboard accessible")
        else:
            user_results["tests"]["dashboard"] = {"pass": False, "note": "Dashboard not accessible"}
            print(f"  ❌ {user['name']}: Dashboard FAILED")

        # Step 3: Test profile page
        profile_result = await crawler.arun(url=f"{BASE_URL}/profile")
        if profile_result.success and len(profile_result.html) > 500:
            user_results["tests"]["profile"] = {"pass": True, "note": f"{len(profile_result.html)} bytes"}
            print(f"  ✅ {user['name']}: Profile accessible")
        else:
            user_results["tests"]["profile"] = {"pass": False, "note": "Profile not accessible"}
            print(f"  ❌ {user['name']}: Profile FAILED")

        # Step 4: Test wizard start
        wizard_result = await crawler.arun(url=f"{BASE_URL}/wizard")
        if wizard_result.success and len(wizard_result.html) > 500:
            user_results["tests"]["wizard"] = {"pass": True, "note": f"{len(wizard_result.html)} bytes"}
            print(f"  ✅ {user['name']}: Wizard accessible")
        else:
            user_results["tests"]["wizard"] = {"pass": False, "note": "Wizard not accessible"}
            print(f"  ❌ {user['name']}: Wizard FAILED")

    except Exception as e:
        user_results["tests"]["error"] = {"pass": False, "note": str(e)}
        print(f"  ❌ {user['name']}: ERROR - {e}")

    return user_results

async def main():
    print("=" * 60)
    print("VetAssist User Functional Test Report")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)
    print()

    browser_config = BrowserConfig(headless=True)

    for user in TEST_USERS:
        print(f"\nTesting: {user['name']} ({user['profile']})")
        print("-" * 40)

        async with AsyncWebCrawler(config=browser_config) as crawler:
            user_result = await test_user_login(crawler, user)
            results.append(user_result)

    # Generate report
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    total_pass = 0
    total_fail = 0
    total_tests = 0

    report_lines = [
        "# VetAssist User Functional Test Report\n",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n",
        f"**Base URL:** {BASE_URL}\n\n",
        "## Results by User\n\n",
    ]

    for r in results:
        report_lines.append(f"### {r['name']} ({r['user']})\n\n")
        report_lines.append("| Test | Result | Notes |\n")
        report_lines.append("|------|--------|-------|\n")

        for test_name, test_result in r["tests"].items():
            total_tests += 1
            if test_result.get("pass") == True:
                total_pass += 1
                status = "✅ PASS"
            elif test_result.get("pass") == False:
                total_fail += 1
                status = "❌ FAIL"
            else:
                status = "⚠️ UNCLEAR"
            report_lines.append(f"| {test_name} | {status} | {test_result.get('note', '')} |\n")
        report_lines.append("\n")

    report_lines.insert(3, f"**Overall:** {total_pass}/{total_tests} tests passed\n\n")

    print(f"Total: {total_pass}/{total_tests} tests passed, {total_fail} failed")

    # Write report
    report_path = "/ganuda/docs/reports/VETASSIST-USER-TESTS-20260126.md"
    with open(report_path, "w") as f:
        f.writelines(report_lines)

    print(f"\nReport saved to: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())

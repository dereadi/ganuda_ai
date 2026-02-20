#!/usr/bin/env python3
"""VetAssist Simple Page Tests - Check all pages are accessible"""

import asyncio
from datetime import datetime
from crawl4ai import AsyncWebCrawler

BASE_URL = "http://localhost:3000"

PAGES_TO_TEST = [
    ("/", "Homepage"),
    ("/login", "Login Page"),
    ("/calculator", "Calculator"),
    ("/chat", "AI Chat"),
    ("/resources", "Resources"),
    ("/about", "About"),
    ("/dashboard", "Dashboard"),
    ("/profile", "Profile"),
    ("/wizard", "Claim Wizard"),
]

async def test_page(crawler, path, name):
    """Test if a page loads"""
    try:
        result = await crawler.arun(url=f"{BASE_URL}{path}")
        if result.success and len(result.html) > 500:
            print(f"✅ {name}: {len(result.html)} bytes")
            return True, len(result.html)
        else:
            print(f"❌ {name}: Failed to load")
            return False, 0
    except Exception as e:
        print(f"❌ {name}: Error - {str(e)[:50]}")
        return False, 0

async def main():
    print("=" * 50)
    print("VetAssist Page Accessibility Test")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"Base URL: {BASE_URL}")
    print("=" * 50)
    print()

    results = []
    async with AsyncWebCrawler() as crawler:
        for path, name in PAGES_TO_TEST:
            passed, size = await test_page(crawler, path, name)
            results.append((name, path, passed, size))

    print()
    print("=" * 50)
    passed_count = sum(1 for r in results if r[2])
    print(f"Results: {passed_count}/{len(results)} pages accessible")
    print("=" * 50)

    # Write report
    report_path = "/ganuda/docs/reports/VETASSIST-PAGE-TESTS-20260126.md"
    with open(report_path, "w") as f:
        f.write("# VetAssist Page Accessibility Report\n\n")
        f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"**Base URL:** {BASE_URL}\n")
        f.write(f"**Results:** {passed_count}/{len(results)} pages passed\n\n")
        f.write("## Page Results\n\n")
        f.write("| Page | Path | Status | Size |\n")
        f.write("|------|------|--------|------|\n")
        for name, path, passed, size in results:
            status = "✅ PASS" if passed else "❌ FAIL"
            f.write(f"| {name} | {path} | {status} | {size} bytes |\n")

    print(f"\nReport: {report_path}")

if __name__ == "__main__":
    asyncio.run(main())

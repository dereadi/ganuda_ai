# Jr Instruction: VetAssist Crawl4AI Regression Testing

**ID:** JR-VETASSIST-CRAWL4AI-REGRESSION-TEST-FEB06-2026
**Priority:** P1
**Estimated Effort:** 30 minutes
**Assigned:** Research Jr.

---

## Objective

Crawl the VetAssist site using crawl4ai to identify bugs, broken links, console errors, and UI issues before QC.

---

## Step 1: Install crawl4ai if needed

```bash
/ganuda/vetassist/backend/venv/bin/pip install crawl4ai playwright
```

---

## Step 2: Install playwright browsers

```bash
/ganuda/vetassist/backend/venv/bin/playwright install chromium
```

---

## Step 3: Create and run the crawler script

```bash
cat > /tmp/vetassist_crawl_test.py << 'CRAWLER'
#!/usr/bin/env python3
"""VetAssist Regression Testing Crawler"""

import asyncio
import json
from datetime import datetime
from crawl4ai import AsyncWebCrawler
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy

BASE_URL = "http://192.168.132.222:8001"
FRONTEND_URL = "http://192.168.132.222:3000"

# Pages to test
PAGES = [
    "/",
    "/login",
    "/register",
    "/dashboard",
    "/calculator",
    "/wizard",
    "/crisis-resources",
    "/chat",
]

# API endpoints to test
API_ENDPOINTS = [
    "/api/v1/health",
    "/api/v1/calculator/combined-rating",
    "/api/v1/content/educational",
    "/api/v1/forms/available",
    "/api/v1/conditions",
]

results = {
    "timestamp": datetime.now().isoformat(),
    "pages_tested": [],
    "api_tested": [],
    "errors": [],
    "warnings": [],
    "broken_links": [],
    "console_errors": [],
    "summary": {}
}

async def test_page(crawler, url, page_name):
    """Test a single page for errors."""
    try:
        result = await crawler.arun(
            url=url,
            bypass_cache=True,
            page_timeout=30000,
        )

        page_result = {
            "page": page_name,
            "url": url,
            "status": "success" if result.success else "failed",
            "title": result.metadata.get("title", ""),
            "links_count": len(result.links.get("internal", [])) + len(result.links.get("external", [])),
            "has_content": len(result.markdown) > 100,
        }

        # Check for error indicators in content
        content_lower = result.markdown.lower() if result.markdown else ""
        if "error" in content_lower or "exception" in content_lower:
            page_result["warning"] = "Page contains error text"
            results["warnings"].append(f"{page_name}: Contains error text")

        if "404" in content_lower or "not found" in content_lower:
            page_result["warning"] = "Page may have 404 content"
            results["warnings"].append(f"{page_name}: May have 404 content")

        results["pages_tested"].append(page_result)
        print(f"✓ {page_name}: {page_result['status']}")

    except Exception as e:
        error_msg = f"{page_name}: {str(e)}"
        results["errors"].append(error_msg)
        results["pages_tested"].append({
            "page": page_name,
            "url": url,
            "status": "error",
            "error": str(e)
        })
        print(f"✗ {page_name}: {str(e)[:50]}")

async def test_api_endpoint(endpoint):
    """Test API endpoint with simple fetch."""
    import aiohttp
    url = f"{BASE_URL}{endpoint}"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                status = response.status
                body = await response.text()

                api_result = {
                    "endpoint": endpoint,
                    "status_code": status,
                    "success": 200 <= status < 400,
                    "response_size": len(body),
                }

                if status >= 400:
                    results["errors"].append(f"API {endpoint}: HTTP {status}")

                results["api_tested"].append(api_result)
                print(f"{'✓' if api_result['success'] else '✗'} API {endpoint}: {status}")

    except Exception as e:
        results["errors"].append(f"API {endpoint}: {str(e)}")
        results["api_tested"].append({
            "endpoint": endpoint,
            "status_code": 0,
            "success": False,
            "error": str(e)
        })
        print(f"✗ API {endpoint}: {str(e)[:50]}")

async def main():
    print("=" * 60)
    print("VetAssist Regression Testing")
    print("=" * 60)

    # Test API endpoints first
    print("\n--- API Endpoint Tests ---")
    for endpoint in API_ENDPOINTS:
        await test_api_endpoint(endpoint)

    # Test frontend pages
    print("\n--- Frontend Page Tests ---")
    async with AsyncWebCrawler(verbose=False) as crawler:
        for page in PAGES:
            url = f"{FRONTEND_URL}{page}"
            await test_page(crawler, url, page)

    # Generate summary
    results["summary"] = {
        "total_pages": len(results["pages_tested"]),
        "pages_passed": len([p for p in results["pages_tested"] if p.get("status") == "success"]),
        "total_api": len(results["api_tested"]),
        "api_passed": len([a for a in results["api_tested"] if a.get("success")]),
        "total_errors": len(results["errors"]),
        "total_warnings": len(results["warnings"]),
    }

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Pages: {results['summary']['pages_passed']}/{results['summary']['total_pages']} passed")
    print(f"API:   {results['summary']['api_passed']}/{results['summary']['total_api']} passed")
    print(f"Errors: {results['summary']['total_errors']}")
    print(f"Warnings: {results['summary']['total_warnings']}")

    if results["errors"]:
        print("\n--- ERRORS ---")
        for err in results["errors"]:
            print(f"  ✗ {err}")

    if results["warnings"]:
        print("\n--- WARNINGS ---")
        for warn in results["warnings"]:
            print(f"  ⚠ {warn}")

    # Save results
    output_file = "/ganuda/vetassist/regression_test_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to: {output_file}")

if __name__ == "__main__":
    asyncio.run(main())
CRAWLER

/ganuda/vetassist/backend/venv/bin/python /tmp/vetassist_crawl_test.py
```

---

## Step 4: Review results

```bash
cat /ganuda/vetassist/regression_test_results.json | python3 -c "import sys,json; d=json.load(sys.stdin); print('Errors:', d['summary']['total_errors']); print('Warnings:', d['summary']['total_warnings']); [print(f'  - {e}') for e in d['errors'][:10]]"
```

---

## Expected Output

- Pages tested: 8+
- API endpoints tested: 5+
- Report saved to `/ganuda/vetassist/regression_test_results.json`

---

## Bugs to Flag

1. **HTTP 4xx/5xx responses** — API or page errors
2. **Empty pages** — Less than 100 chars of content
3. **Missing titles** — Pages without proper titles
4. **Error text in content** — "Error", "Exception", "404" appearing in page
5. **Broken links** — Links that don't resolve

---

*For Seven Generations*
